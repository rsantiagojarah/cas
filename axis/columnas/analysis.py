"""
Análisis de columnas de concreto armado según E.060.

Procedimiento de diseño:

Fase 1 - Estabilidad global:
1. Índice de estabilidad Q por piso y dirección.

Fase 2 - Esbeltez y segundo orden:
2. Momentos extremos M1/M2.
3. Evaluación de segundo orden.
4. Factor Cm.
5. Factor delta de amplificación.

Fase 3 - Demanda amplificada:
6. Esfuerzos finales amplificados.

Fase 4 - Capacidad y verificación:
7. Momentos nominales Mn2/Mn3.
8. Estados sísmicos combinados.
9. Verificación P-M por flexocompresión.
"""

from __future__ import annotations

import math
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════
# PASO 1: ÍNDICE DE ESTABILIDAD Q
# ═══════════════════════════════════════════════════════════════════════

def compute_q_table(
    forces: list[dict],
    drifts: list[dict],
    heights: list[dict],
    r_x: float = 8.0,
    r_y: float = 8.0,
) -> list[dict]:
    """
    Calcula el índice Q por piso y dirección.
    Drift_R = Drift * 0.75 * R.
    """
    stories_forces = {r["Story"] for r in forces if "Story" in r}
    story_col = "Story" if any("Story" in h for h in heights) else "Name"
    stories_heights = {h[story_col] for h in heights if story_col in h}
    common = sorted(stories_forces & stories_heights)

    height_map = {}
    for h in heights:
        s = h.get(story_col, h.get("Story", ""))
        try:
            height_map[s] = float(h.get("Height", 0))
        except (ValueError, TypeError):
            pass

    drift_map = {}
    for d in drifts:
        key = (d.get("Story", ""), d.get("Output_Case", d.get("Output Case", "")))
        try:
            val = float(d.get("Drift", 0))
            if key not in drift_map or val > drift_map[key]:
                drift_map[key] = val
        except (ValueError, TypeError):
            pass

    results = []
    for story in common:
        he = height_map.get(story)
        if not he or he <= 0:
            continue

        drift_x_key = next(
            ((s, c) for (s, c) in drift_map if s == story and "SPX" in c.upper()),
            None,
        )
        drift_y_key = next(
            ((s, c) for (s, c) in drift_map if s == story and "SPY" in c.upper()),
            None,
        )

        drift_x_raw = drift_map.get(drift_x_key) if drift_x_key else None
        drift_y_raw = drift_map.get(drift_y_key) if drift_y_key else None

        drift_r_x = drift_x_raw * 0.75 * r_x if drift_x_raw is not None else None
        drift_r_y = drift_y_raw * 0.75 * r_y if drift_y_raw is not None else None

        for direction, drift_r, col_v in [("X", drift_r_x, "VX"), ("Y", drift_r_y, "VY")]:
            if drift_r is None:
                continue
            q_res = _calc_q_direction(forces, story, direction, drift_r, he, col_v)
            if q_res:
                results.append(q_res)

    return results


def _calc_q_direction(
    forces: list[dict], story: str, direction: str,
    drift_r: float, he: float, col_v: str,
) -> Optional[dict]:
    sx_filter = "SX" if direction == "X" else "SY"
    candidates = [
        r for r in forces
        if r.get("Story") == story
        and sx_filter in str(r.get("Output_Case", r.get("Output Case", ""))).upper()
    ]
    if not candidates:
        return None

    q_max = -math.inf
    best = None
    for row in candidates:
        try:
            pu = float(row["P"])
            vus = abs(float(row[col_v]))
        except (KeyError, ValueError, TypeError):
            continue
        if vus == 0:
            continue
        q = (pu * drift_r) / vus
        if q > q_max:
            q_max = q
            best = row

    if best is None:
        return None

    oc = str(best.get("Output_Case", best.get("Output Case", "")))
    st = best.get("Step_Type", best.get("Step Type", ""))
    label = f"{oc} ({st})" if st else oc

    return {
        "Story": story,
        "Direction": direction,
        "Selected_Case": label,
        "Pu": float(best["P"]),
        "Vus": abs(float(best[col_v])),
        "Drift_R": drift_r,
        "he": he,
        "Delta_o": drift_r * he,
        "Q": q_max,
        "Classification": "Arriostrado" if q_max <= 0.06 else "No arriostrado",
    }


# ═══════════════════════════════════════════════════════════════════════
# PASO 2: MOMENTOS EXTREMOS (ESBELTEZ)
# ═══════════════════════════════════════════════════════════════════════

def compute_slenderness(
    esfuerzos: list[dict],
    alturas: list[dict],
) -> list[dict]:
    """Calcula M1, M2 y curvatura por columna."""
    unique_names = list({r["Unique_Name"] for r in esfuerzos if "Unique_Name" in r})
    results = []

    for un in unique_names:
        rows = [r for r in esfuerzos if r.get("Unique_Name") == un]
        if not rows:
            continue
        story = rows[0].get("Story", "")
        m1_x, m2_x, curv_x = _calc_extreme_moments(rows, "M3")
        m1_y, m2_y, curv_y = _calc_extreme_moments(rows, "M2")

        results.append({
            "Story": story,
            "Unique_Name": un,
            "M1_X": m1_x or 0.0,
            "M2_X": m2_x or 0.0,
            "M1_Y": m1_y or 0.0,
            "M2_Y": m2_y or 0.0,
            "Curvatura_X": curv_x,
            "Curvatura_Y": curv_y,
        })

    return results


def _calc_extreme_moments(
    rows: list[dict], col_m: str,
) -> tuple[Optional[float], Optional[float], str]:
    """
    Calcula M1/M2 para la combinación crítica (34 - 12*M1/M2 máximo).
    Igual que Diseño_Columnas: solo stations extremas (mín y máx), M1 = menor |M| con signo,
    M2 = mayor |M| con signo; curvatura según la combinación crítica.
    """
    valid = []
    for r in rows:
        try:
            station = float(r.get("Station", 0))
            moment = float(r.get(col_m, 0))
            valid.append((station, moment, r))
        except (ValueError, TypeError):
            continue

    if not valid:
        return None, None, "N/A"

    stations = [v[0] for v in valid]
    s_min, s_max = min(stations), max(stations)
    extremes = [v for v in valid if v[0] == s_min or v[0] == s_max]

    if not extremes:
        return None, None, "N/A"

    combos = {}
    for s, m, r in extremes:
        oc = r.get("Output_Case", r.get("Output Case", ""))
        st = r.get("Step_Type", r.get("Step Type", ""))
        key = f"{oc}|{st}"
        combos.setdefault(key, []).append((m, r))

    best_val = -math.inf
    m1_final, m2_final = None, None
    best_key = None

    for key, items in combos.items():
        moments = [x[0] for x in items]
        if not moments:
            continue
        abs_moments = [abs(m) for m in moments]
        idx_min = abs_moments.index(min(abs_moments))
        idx_max = abs_moments.index(max(abs_moments))
        m1 = moments[idx_min]
        m2 = moments[idx_max]

        if abs(m2) > 1e-10:
            ratio = m1 / m2
            formula = min(34 - 12 * ratio, 40.0)
            if formula > best_val:
                best_val = formula
                m1_final, m2_final = m1, m2
                best_key = key

    if m1_final is None or m2_final is None:
        return None, None, "N/A"

    # Curvatura solo de la combinación crítica (como Diseño_Columnas)
    if best_key is not None:
        momentos_critico = [v[0] for v in combos[best_key]]
        has_pos = any(m > 0 for m in momentos_critico)
        has_neg = any(m < 0 for m in momentos_critico)
    else:
        momentos_critico = [v[1] for v in extremes]
        has_pos = any(m > 0 for m in momentos_critico)
        has_neg = any(m < 0 for m in momentos_critico)
    curvatura = "Doble" if has_pos and has_neg else "Simple"

    return m1_final, m2_final, curvatura


# ═══════════════════════════════════════════════════════════════════════
# PASO 3: EVALUACIÓN DE SEGUNDO ORDEN
# ═══════════════════════════════════════════════════════════════════════

def compute_second_order(
    esbeltez: list[dict],
    props: list[dict],
    q_results: list[dict],
) -> list[dict]:
    """
    Evalúa si se pueden ignorar efectos de segundo orden.
    Arriostrado: (k*lu)/r <= 34-12*(M1/M2) <= 40
    No arriostrado: (k*lu)/r < 22
    Análisis en dirección X usa inercia Iy; análisis en dirección Y usa inercia Ix.
    """
    props_map = {p["Unique_Name"]: p for p in props}
    q_map = {(r["Story"], r["Direction"]): r["Classification"] for r in q_results}

    results = []
    for row in esbeltez:
        un = row["Unique_Name"]
        story = row["Story"]
        prop = props_map.get(un)
        if not prop:
            continue

        k = float(prop.get("k", 1.0))
        lu = float(prop.get("lu", 0.0))
        Ag = float(prop.get("Ag", 0.0))

        I_fallback = float(prop.get("I", 0.0))
        Ix = float(prop.get("Ix", I_fallback))
        Iy = float(prop.get("Iy", I_fallback))
        # Dirección X → Iy; dirección Y → Ix (inercia que resiste la flexión en esa dirección)
        I_map = {"X": Iy, "Y": Ix}

        for direction in ["X", "Y"]:
            I_dir = I_map[direction]
            r_dir = math.sqrt(I_dir / Ag) if Ag > 0 and I_dir >= 0 else 0.0
            klu_r = (k * lu) / r_dir if r_dir > 1e-10 else 0.0

            m1 = float(row.get(f"M1_{direction}", 0))
            m2 = float(row.get(f"M2_{direction}", 0))
            ratio = m1 / m2 if abs(m2) > 1e-10 else 0.0
            formula = min(34 - 12 * ratio, 40.0)

            clasif = q_map.get((story, direction), "No arriostrado")
            es_arriostrado = clasif == "Arriostrado"

            if es_arriostrado:
                ignorar = klu_r <= formula
            else:
                ignorar = klu_r < 22

            results.append({
                "Story": story,
                "Unique_Name": un,
                "Direction": direction,
                "Arriostrado": "Si" if es_arriostrado else "No",
                "k": k,
                "I": round(I_dir, 4),
                "r": round(r_dir, 4),
                "lu": lu,
                "M1/M2": round(ratio, 4),
                "34-12(M1/M2)": round(formula, 2),
                "(k*lu)/r": round(klu_r, 2),
                "Ignorar_2do_Orden": "Si" if ignorar else "No",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════
# PASO 4: FACTOR Cm
# ═══════════════════════════════════════════════════════════════════════

def compute_cm(
    esfuerzos: list[dict],
    segundo_orden: list[dict],
) -> list[dict]:
    """
    Calcula Cm = 0.6 + 0.4*(M1/M2), limitado [0.4, 1.0].
    Si se ignora 2do orden -> Cm = 1.0.
    """
    ignorar_map = {}
    for r in segundo_orden:
        key = (r["Story"], r["Unique_Name"], r["Direction"])
        ignorar_map[key] = r.get("Ignorar_2do_Orden", "No") == "Si"

    unique_names = list({r["Unique_Name"] for r in esfuerzos if "Unique_Name" in r})
    results = []

    for un in unique_names:
        rows = [r for r in esfuerzos if r.get("Unique_Name") == un]
        if not rows:
            continue
        story = rows[0].get("Story", "")

        m1_x, m2_x, cm_x = _calc_cm_max(rows, "M3")
        m1_y, m2_y, cm_y = _calc_cm_max(rows, "M2")

        if ignorar_map.get((story, un, "X"), False):
            cm_x = 1.0
        if ignorar_map.get((story, un, "Y"), False):
            cm_y = 1.0

        results.append({
            "Story": story,
            "Unique_Name": un,
            "M1_X": m1_x or 0.0,
            "M2_X": m2_x or 0.0,
            "Cm_X": round(cm_x or 1.0, 4),
            "M1_Y": m1_y or 0.0,
            "M2_Y": m2_y or 0.0,
            "Cm_Y": round(cm_y or 1.0, 4),
        })

    return results


def _calc_cm_max(
    rows: list[dict], col_m: str,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calcula Cm máximo entre combinaciones."""
    valid = []
    for r in rows:
        try:
            station = float(r.get("Station", 0))
            moment = float(r.get(col_m, 0))
            valid.append((station, moment, r))
        except (ValueError, TypeError):
            continue

    if not valid:
        return None, None, None

    stations = [v[0] for v in valid]
    s_min, s_max = min(stations), max(stations)
    extremes = [v for v in valid if v[0] == s_min or v[0] == s_max]

    if not extremes:
        return None, None, None

    combos = {}
    for s, m, r in extremes:
        oc = r.get("Output_Case", r.get("Output Case", ""))
        st = r.get("Step_Type", r.get("Step Type", ""))
        key = f"{oc}|{st}"
        combos.setdefault(key, []).append(m)

    best_cm = -math.inf
    m1_final, m2_final = None, None

    for key, moments in combos.items():
        if not moments:
            continue
        abs_m = [abs(m) for m in moments]
        idx_min = abs_m.index(min(abs_m))
        idx_max = abs_m.index(max(abs_m))
        m1, m2 = moments[idx_min], moments[idx_max]

        if abs(m2) > 1e-10:
            cm = max(0.4, min(1.0, 0.6 + 0.4 * (m1 / m2)))
        else:
            cm = 0.6

        if cm > best_cm:
            best_cm = cm
            m1_final, m2_final = m1, m2

    return m1_final, m2_final, best_cm if best_cm > -math.inf else None


# ═══════════════════════════════════════════════════════════════════════
# PASO 5: FACTOR DELTA (AMPLIFICACIÓN)
# ═══════════════════════════════════════════════════════════════════════

def compute_delta(
    props: list[dict],
    cm_results: list[dict],
    esfuerzos: list[dict],
    segundo_orden: list[dict],
) -> list[dict]:
    """
    Calcula EI, Pc y delta por columna y dirección.
    EI = (0.4*Ec*I)/(1+Bd). Análisis en X usa Iy; análisis en Y usa Ix.
    Pc = pi²*EI/(k*lu)²
    delta = Cm/(1-0.75*Pu/Pc) >= 1.0
    """
    cm_map = {r["Unique_Name"]: r for r in cm_results}
    pu_map = _calc_pu_max(esfuerzos)

    ignorar_map = {}
    for r in segundo_orden:
        key = (r["Story"], r["Unique_Name"], r["Direction"])
        ignorar_map[key] = r.get("Ignorar_2do_Orden", "No") == "Si"

    results = []
    for prop in props:
        un = prop["Unique_Name"]
        story = prop.get("Story", "")
        ec = float(prop.get("Ec", 0))
        bd = float(prop.get("Bd", 0.5))
        k = float(prop.get("k", 1.0))
        lu = float(prop.get("lu", 0))

        I_fallback = float(prop.get("I", 0))
        Ix = float(prop.get("Ix", I_fallback))
        Iy = float(prop.get("Iy", I_fallback))

        pu = pu_map.get(un, 0.0)
        cm_row = cm_map.get(un, {})
        cm_x = float(cm_row.get("Cm_X", 1.0))
        cm_y = float(cm_row.get("Cm_Y", 1.0))

        # Dirección X → Iy; dirección Y → Ix (misma convención que paso 3)
        ei_x = _calc_ei(ec, Iy, bd)
        ei_y = _calc_ei(ec, Ix, bd)
        pc_x = _calc_pc(ei_x, k, lu)
        pc_y = _calc_pc(ei_y, k, lu)
        delta_x = _calc_delta(cm_x, pu, pc_x)
        delta_y = _calc_delta(cm_y, pu, pc_y)

        if ignorar_map.get((story, un, "X"), False):
            delta_x = 1.0
        if ignorar_map.get((story, un, "Y"), False):
            delta_y = 1.0

        results.append({
            "Story": story,
            "Unique_Name": un,
            "Pu": round(pu, 2),
            "EI_X": round(ei_x, 2),
            "Pc_X": round(pc_x, 2),
            "Cm_X": round(cm_x, 4),
            "Delta_X": round(delta_x, 4),
            "EI_Y": round(ei_y, 2),
            "Pc_Y": round(pc_y, 2),
            "Cm_Y": round(cm_y, 4),
            "Delta_Y": round(delta_y, 4),
        })

    return results


def _calc_pu_max(esfuerzos: list[dict]) -> dict[str, float]:
    """Pu máximo (absoluto) por unique_name, convertido a kg."""
    result = {}
    for r in esfuerzos:
        un = r.get("Unique_Name", "")
        try:
            p = abs(float(r.get("P", 0))) * 1000.0
        except (ValueError, TypeError):
            continue
        result[un] = max(result.get(un, 0.0), p)
    return result


def _calc_ei(ec: float, ig: float, bd: float) -> float:
    if bd < 0:
        bd = 0.5
    denom = 1.0 + bd
    if denom == 0:
        return 0.0
    return (0.4 * ec * ig) / denom


def _calc_pc(ei: float, k: float, lu: float) -> float:
    if ei <= 0 or k <= 0 or lu <= 0:
        return 0.0
    denom = (k * lu) ** 2
    if denom == 0:
        return 0.0
    return (math.pi ** 2 * ei) / denom


def _calc_delta(cm: float, pu: float, pc: float) -> float:
    if pu <= 0 or pc <= 0:
        return max(1.0, cm)
    denom = 1.0 - 0.75 * (pu / pc)
    if denom <= 0.001:
        return 1.0
    return max(1.0, cm / denom)


# ═══════════════════════════════════════════════════════════════════════
# PASO 6: ESFUERZOS FINALES AMPLIFICADOS
# ═══════════════════════════════════════════════════════════════════════

def compute_final_forces(
    esfuerzos: list[dict],
    delta_results: list[dict],
) -> list[dict]:
    """
    Amplifica momentos: M2_final = M2 * Delta_Y, M3_final = M3 * Delta_X.
    """
    delta_map = {}
    for r in delta_results:
        delta_map[r["Unique_Name"]] = {
            "Delta_X": float(r.get("Delta_X", 1.0)),
            "Delta_Y": float(r.get("Delta_Y", 1.0)),
        }

    results = []
    for row in esfuerzos:
        new_row = dict(row)
        un = row.get("Unique_Name", "")
        deltas = delta_map.get(un, {"Delta_X": 1.0, "Delta_Y": 1.0})

        try:
            m2 = float(row.get("M2", 0))
            new_row["M2"] = round(m2 * deltas["Delta_Y"], 6)
        except (ValueError, TypeError):
            pass

        try:
            m3 = float(row.get("M3", 0))
            new_row["M3"] = round(m3 * deltas["Delta_X"], 6)
        except (ValueError, TypeError):
            pass

        results.append(new_row)

    return results


# ═══════════════════════════════════════════════════════════════════════
# PASO 7: MOMENTOS NOMINALES (Mn2, Mn3)
# ═══════════════════════════════════════════════════════════════════════

class InteractionSurface:
    """Superficie de interacción para consultas P-M.
    Convención del ángulo (muros/columnas): θ = atan2(M2, M3), con 0° = eje M3 (sentido
    largo / mayor resistencia), 90° = eje M2. Si el diagrama solo tiene curvas en [0°, 180°],
    el ángulo se normaliza a ese rango por simetría.
    """

    def __init__(self, points: list[dict]):
        self.points = points
        self._angles = sorted({float(p["angle"]) for p in points})

    def p_bounds(self) -> tuple[float, float]:
        """Rango de P (Tn) cubierto por los puntos del diagrama."""
        if not self.points:
            return (0.0, 0.0)
        ps = [float(p["p"]) for p in self.points]
        return min(ps), max(ps)

    def pu_en_rango(self, pu: float, tol: float = 1e-4) -> bool:
        p_min, p_max = self.p_bounds()
        return (p_min - tol) <= pu <= (p_max + tol)

    def get_moment_nominal(self, pu: float, angle: float = 0.0, *, clamp_p: bool = True) -> float:
        angle = angle % 360.0
        # Si el diagrama solo tiene curvas en [0, 180°], mapear ángulo por simetría
        if self._angles and max(self._angles) <= 180.0 + 1e-6:
            angle = min(angle, 360.0 - angle)
        neighbors = self._find_neighbors(angle)

        if len(neighbors) == 1:
            return self._interp_p(pu, neighbors[0], clamp_p=clamp_p)

        a1, a2 = neighbors
        mn1 = self._interp_p(pu, a1, clamp_p=clamp_p)
        mn2 = self._interp_p(pu, a2, clamp_p=clamp_p)
        if a2 == a1:
            return mn1
        factor = (angle - a1) / (a2 - a1)
        return mn1 + factor * (mn2 - mn1)

    def _find_neighbors(self, angle: float) -> list[float]:
        if not self._angles:
            raise ValueError("Sin ángulos disponibles")
        if angle in self._angles:
            return [angle]
        smaller = [a for a in self._angles if a < angle]
        larger = [a for a in self._angles if a > angle]
        if not smaller:
            return [min(self._angles)]
        if not larger:
            return [max(self._angles)]
        return [max(smaller), min(larger)]

    def _interp_p(self, pu: float, angle: float, *, clamp_p: bool = True) -> float:
        pts = sorted(
            [p for p in self.points if float(p["angle"]) == angle],
            key=lambda x: float(x["p"]),
        )
        if not pts:
            raise ValueError(f"Sin puntos para ángulo {angle}")

        p_min = float(pts[0]["p"])
        p_max = float(pts[-1]["p"])
        if not clamp_p and (pu < p_min or pu > p_max):
            raise ValueError(f"P={pu} fuera de rango del diagrama [{p_min}, {p_max}]")
        if pu < p_min:
            pu = p_min
        elif pu > p_max:
            pu = p_max

        for i in range(len(pts) - 1):
            p1 = float(pts[i]["p"])
            p2 = float(pts[i + 1]["p"])
            if p1 <= pu <= p2:
                mn1 = math.sqrt(float(pts[i]["m2"]) ** 2 + float(pts[i]["m3"]) ** 2)
                mn2 = math.sqrt(float(pts[i + 1]["m2"]) ** 2 + float(pts[i + 1]["m3"]) ** 2)
                if p2 == p1:
                    return mn1
                f = (pu - p1) / (p2 - p1)
                return mn1 + f * (mn2 - mn1)

        closest = min(pts, key=lambda x: abs(float(x["p"]) - pu))
        return math.sqrt(float(closest["m2"]) ** 2 + float(closest["m3"]) ** 2)


def compute_nominal_moments(
    esfuerzos_finales: list[dict],
    asignaciones: list[dict],
    diagramas_nominales: dict[str, list[dict]],
) -> list[dict]:
    """
    Calcula Mn2 y Mn3 para cada combinación usando diagramas nominales.

    Args:
        esfuerzos_finales: Esfuerzos amplificados
        asignaciones: Mapeo Unique_Name -> nombre diagrama nominal
        diagramas_nominales: {nombre_diagrama: [InteractionPoint dicts]}
    """
    asig_map = {
        str(a["Unique_Name"]).strip().upper(): str(a.get("Diagrama_Nominal", "")).strip()
        for a in asignaciones
        if a.get("Diagrama_Nominal")
    }

    results = []

    for un_norm, diagrama_nombre in asig_map.items():
        puntos = diagramas_nominales.get(diagrama_nombre)
        if not puntos:
            continue
        surface = InteractionSurface(puntos)

        elem_rows = [
            r for r in esfuerzos_finales
            if str(r.get("Unique_Name", "")).strip().upper() == un_norm
        ]
        if not elem_rows:
            continue

        un_original = elem_rows[0].get("Unique_Name", un_norm)

        combos = {}
        for r in elem_rows:
            oc = r.get("Output_Case", r.get("Output Case", ""))
            st = r.get("Step_Type", r.get("Step Type", ""))
            key = f"{oc}|{st}"
            combos.setdefault(key, []).append(r)

        for combo_key, rows in combos.items():
            oc, st = combo_key.split("|", 1) if "|" in combo_key else (combo_key, "")
            inf, sup = _get_station_data(rows)
            if not inf or not sup:
                continue

            mn2_inf = _get_mn(surface, inf["pu"], inf.get("m2"), "m2")
            mn3_inf = _get_mn(surface, inf["pu"], inf.get("m3"), "m3")
            mn2_sup = _get_mn(surface, sup["pu"], sup.get("m2"), "m2")
            mn3_sup = _get_mn(surface, sup["pu"], sup.get("m3"), "m3")

            results.append({
                "Story": rows[0].get("Story", ""),
                "Unique_Name": un_original,
                "Load_Case": oc,
                "Step_Type": st.strip(),
                "Mn2_Inf": round(mn2_inf or 0.0, 4),
                "Mn3_Inf": round(mn3_inf or 0.0, 4),
                "Mn2_Sup": round(mn2_sup or 0.0, 4),
                "Mn3_Sup": round(mn3_sup or 0.0, 4),
            })

    return results


def _get_mn(surface: InteractionSurface, pu: float, m_val, axis: str) -> Optional[float]:
    if m_val is None or abs(float(m_val)) < 1e-6:
        return None
    m = float(m_val)
    if axis == "m2":
        angle = 0.0 if m >= 0 else 180.0
    else:
        angle = 90.0 if m >= 0 else 270.0
    try:
        mn = surface.get_moment_nominal(pu, angle)
        return abs(mn) if m >= 0 else -abs(mn)
    except Exception:
        return None


def _get_station_data(rows: list[dict]) -> tuple[Optional[dict], Optional[dict]]:
    """Obtiene datos de station inferior y superior."""
    valid = []
    for r in rows:
        try:
            s = float(r.get("Station", 0))
            valid.append((s, r))
        except (ValueError, TypeError):
            valid.append((0, r))

    if not valid:
        return None, None

    valid.sort(key=lambda x: x[0])
    r_inf = valid[0][1]
    r_sup = valid[-1][1]

    def extract(r):
        try:
            return {
                "pu": float(r.get("P", 0)),
                "m2": float(r.get("M2", 0)) if r.get("M2") is not None else None,
                "m3": float(r.get("M3", 0)) if r.get("M3") is not None else None,
            }
        except (ValueError, TypeError):
            return None

    return extract(r_inf), extract(r_sup)


# ═══════════════════════════════════════════════════════════════════════
# PASO 8: ESTADOS SÍSMICOS COMBINADOS
# ═══════════════════════════════════════════════════════════════════════

def compute_seismic_states(mn_results: list[dict]) -> list[dict]:
    """
    Sísmicos: Estado 1 (Mn Inf Max + Mn Sup Min), Estado 2 (Mn Inf Min + Mn Sup Max).
    No sísmicos: mantiene momentos en valor absoluto.
    """
    groups = {}
    for r in mn_results:
        key = (r["Story"], r["Unique_Name"], r["Load_Case"])
        groups.setdefault(key, []).append(r)

    results = []
    for (story, un, lc), group in groups.items():
        is_seismic = "SX" in lc.upper() or "SY" in lc.upper()

        if is_seismic:
            max_rows = [r for r in group if r.get("Step_Type", "").strip().upper() == "MAX"]
            min_rows = [r for r in group if r.get("Step_Type", "").strip().upper() == "MIN"]

            if max_rows and min_rows:
                mx = max_rows[0]
                mn = min_rows[0]
                results.append({
                    "Story": story, "Unique_Name": un, "Load_Case": lc,
                    "Mn2_Inf": abs(float(mx.get("Mn2_Inf", 0))),
                    "Mn2_Sup": abs(float(mn.get("Mn2_Sup", 0))),
                    "Mn3_Inf": abs(float(mx.get("Mn3_Inf", 0))),
                    "Mn3_Sup": abs(float(mn.get("Mn3_Sup", 0))),
                })
                results.append({
                    "Story": story, "Unique_Name": un, "Load_Case": lc,
                    "Mn2_Inf": abs(float(mn.get("Mn2_Inf", 0))),
                    "Mn2_Sup": abs(float(mx.get("Mn2_Sup", 0))),
                    "Mn3_Inf": abs(float(mn.get("Mn3_Inf", 0))),
                    "Mn3_Sup": abs(float(mx.get("Mn3_Sup", 0))),
                })
            else:
                r0 = group[0]
                results.append({
                    "Story": story, "Unique_Name": un, "Load_Case": lc,
                    "Mn2_Inf": abs(float(r0.get("Mn2_Inf", 0))),
                    "Mn2_Sup": abs(float(r0.get("Mn2_Sup", 0))),
                    "Mn3_Inf": abs(float(r0.get("Mn3_Inf", 0))),
                    "Mn3_Sup": abs(float(r0.get("Mn3_Sup", 0))),
                })
        else:
            r0 = group[0]
            results.append({
                "Story": story, "Unique_Name": un, "Load_Case": lc,
                "Mn2_Inf": abs(float(r0.get("Mn2_Inf", 0))),
                "Mn2_Sup": abs(float(r0.get("Mn2_Sup", 0))),
                "Mn3_Inf": abs(float(r0.get("Mn3_Inf", 0))),
                "Mn3_Sup": abs(float(r0.get("Mn3_Sup", 0))),
            })

    return results


# ═══════════════════════════════════════════════════════════════════════
# PASO 9: VERIFICACIÓN P-M (FLEXOCOMPRESIÓN)
# ═══════════════════════════════════════════════════════════════════════

def compute_pm_verification(
    esfuerzos_finales: list[dict],
    asignaciones: list[dict],
    diagramas_nominales: dict[str, list[dict]],
    diagramas_ultimos: dict[str, list[dict]],
) -> list[dict]:
    """Verificación P-M para todos los elementos con diagramas asignados."""
    asig_map = {}
    for a in asignaciones:
        un = str(a["Unique_Name"]).strip().upper()
        asig_map[un] = {
            "nominal": str(a.get("Diagrama_Nominal", "")).strip(),
            "ultimo": str(a.get("Diagrama_Ultimo", "")).strip(),
        }

    results = []

    for un_norm, diags in asig_map.items():
        nom_name = diags["nominal"]
        ult_name = diags["ultimo"] or nom_name
        pts_nom = diagramas_nominales.get(nom_name)
        pts_ult = diagramas_ultimos.get(ult_name) or diagramas_nominales.get(ult_name)

        if not pts_ult:
            continue
        if not pts_nom:
            pts_nom = pts_ult

        surface_ult = InteractionSurface(pts_ult)

        elem_rows = [
            r for r in esfuerzos_finales
            if str(r.get("Unique_Name", "")).strip().upper() == un_norm
        ]

        for row in elem_rows:
            try:
                story = str(row.get("Story", ""))
                oc = row.get("Output_Case", row.get("Output Case", "N/A"))
                pu = float(row.get("P", 0))
                m2 = float(row.get("M2", 0))
                m3_val = row.get("M3")
                m3 = float(m3_val) if m3_val is not None and str(m3_val).strip() else None

                is_biaxial = m3 is not None and abs(m3) > 1e-6

                if is_biaxial:
                    angle = math.degrees(math.atan2(m2, m3))
                    if angle < 0:
                        angle += 360.0
                    mu_equiv = math.sqrt(m2 ** 2 + m3 ** 2)
                else:
                    angle = 0.0 if m2 >= 0 else 180.0
                    mu_equiv = abs(m2)

                p_en_rango = surface_ult.pu_en_rango(pu)
                p_min, p_max = surface_ult.p_bounds()
                if p_en_rango:
                    cap = surface_ult.get_moment_nominal(pu, angle)
                else:
                    pu_ref = max(p_min, min(p_max, pu))
                    cap = surface_ult.get_moment_nominal(pu_ref, angle)
                ratio = mu_equiv / cap if cap > 0 else float("inf")
                if not p_en_rango:
                    ratio = float("inf")

                results.append({
                    "Story": story,
                    "Unique_Name": row.get("Unique_Name", ""),
                    "Load_Case": str(oc),
                    "Pu": round(pu, 4),
                    "M2": round(m2, 4),
                    "M3": round(m3, 4) if m3 is not None else 0.0,
                    "Mu_Equiv": round(mu_equiv, 4),
                    "Cap_Ultima": round(cap, 4),
                    "Ratio": round(ratio, 4) if ratio != float("inf") else "inf",
                    "P_En_Rango": "Si" if p_en_rango else "No",
                    "Cumple": "Si" if p_en_rango and ratio <= 1.0 else "No",
                })
            except Exception:
                continue

    return results


def _ratio_float(val) -> float:
    if val in ("inf", "Inf", "INF"):
        return float("inf")
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def compute_pm_summary(verificacion: list[dict]) -> list[dict]:
    """Resumen con el mayor ratio por Unique Name."""
    groups = {}
    for r in verificacion:
        key = (r["Story"], r["Unique_Name"])
        groups.setdefault(key, []).append(r)

    summary = []
    for (story, un), rows in groups.items():
        ratios = [_ratio_float(r.get("Ratio", 0)) for r in rows]
        max_ratio = max(ratios) if ratios else 0.0
        ratio_out = "inf" if max_ratio == float("inf") else round(max_ratio, 4)
        summary.append({
            "Story": story,
            "Unique_Name": un,
            "Ratio_Max": ratio_out,
            "Cumple": "Si" if max_ratio <= 1.0 else "No",
        })

    summary.sort(key=lambda x: -_ratio_float(x["Ratio_Max"]))
    return summary
