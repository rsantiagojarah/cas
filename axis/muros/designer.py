"""Motor de diseño de muros estructurales según RNE E.060 Art. 21.9.

Flujo completo:
  1. Verificación de espesor mínimo
  2-4. Refuerzo preliminar (cuantías mínimas ρh, ρv)
  5. Diseño a flexión  →  Mn, φMn ≥ Mua
  6. Verificación de agrietamiento  →  Mn ≥ 1.2 Mcr
  7. Diseño a corte (amplificación por capacidad)  →  φVn ≥ Vu_cap
  8. Elementos de borde (DEFORMACIÓN o ESFUERZO)
  9. Juntas de construcción (opcional)
"""

from __future__ import annotations

import math
from typing import Optional

from axis.muros.constants import RNE
from axis.muros.models import (
    WallGeometry,
    WallMaterials,
    WallLoads,
    Reinforcement,
    FlexureResult,
    ShearResult,
    BoundaryResult,
    JointResult,
    WallDesignResult,
    StoryData,
    StoryDesignResult,
    MultiStoryResult,
)


C = RNE  # alias corto


# ── 1. Espesor ──────────────────────────────────────────────────────────

def verify_thickness(geo: WallGeometry) -> tuple[bool, str]:
    """Verifica espesor mínimo (Art. 21.9.3)."""
    t_min = C.MIN_T_BASEMENT if geo.is_basement else C.MIN_T_GENERAL
    ok = geo.t >= t_min
    msg = (
        f"t={geo.t:.1f} cm {'>=' if ok else '<'} t_min={t_min:.1f} cm"
        f"  ->  {'CUMPLE' if ok else 'NO CUMPLE'}"
    )
    return ok, msg


# ── 2-4. Refuerzo preliminar ────────────────────────────────────────────

def preliminary_reinforcement(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
) -> Reinforcement:
    """Cuantías mínimas según Art. 11.10.7 / 11.10.8.

    Se parte siempre de las cuantías mínimas del CASO 1 (baja demanda de corte):
      ρh = 0.002   ; ρv = 0.0015

    Si la demanda de corte por capacidad requiere más acero, se ajustará luego
    en design_shear() manteniendo como piso estas cuantías mínimas o las del
    CASO 2 (ρh = 0.0025) según 0.27√f'c·Acw.
    """
    rho_h, rho_v = 0.0020, 0.0015
    return Reinforcement(rho_h=rho_h, rho_v=rho_v)


# ── 5. Flexión ──────────────────────────────────────────────────────────

def design_flexure(
    geo: WallGeometry,
    mat: WallMaterials,
    loads: WallLoads,
    reinf: Reinforcement,
) -> FlexureResult:
    """Diseño a flexión simplificado (Art. 21.9).

    Mn = As·fy·(d − a/2) + Pu·(lm/2 − t/2)
    a  = (As·fy + |Pu|) / (0.85·f'c·t)
    """
    Mua = abs(loads.Mu)

    if loads.Mn_manual is not None and loads.Mn_manual > 0:
        return FlexureResult(Mn=loads.Mn_manual, Mua=Mua, ok=True)

    As_total = reinf.rho_v * geo.Acw
    d = geo.lm - 5.0
    Pu_abs = abs(loads.Pu) if loads.Pu < 0 else loads.Pu

    a = (As_total * mat.fy + Pu_abs) / (0.85 * mat.fc * geo.t)
    a = min(a, geo.lm)

    Mn = As_total * mat.fy * (d - a / 2.0) + Pu_abs * (geo.lm / 2.0 - geo.t / 2.0)
    phi_Mn = C.PHI_FLEX * Mn
    ok = phi_Mn >= Mua

    return FlexureResult(Mn=Mn, Mua=Mua, ok=ok)


# ── 6. Agrietamiento ───────────────────────────────────────────────────

def check_cracking(
    geo: WallGeometry,
    mat: WallMaterials,
    flex: FlexureResult,
    Pu: float,
) -> FlexureResult:
    """Verifica Mn ≥ 1.2 Mcr (Art. 21.9.6.5).

    fr = 2√f'c − |Pu|/Ag
    Mcr = fr · Ig / y
    """
    Ag = geo.Acw
    fr = 2.0 * mat.sqrt_fc - abs(Pu) / Ag if Ag > 0 else 0.0
    fr = max(0.0, fr)

    y = geo.lm / 2.0
    Mcr = fr * geo.Ig / y if y > 0 else 0.0
    cracking_ok = flex.Mn >= C.CRACKING_FACTOR * Mcr

    flex.Mcr = Mcr
    flex.cracking_ok = cracking_ok
    return flex


# ── 7. Corte ────────────────────────────────────────────────────────────

def _alpha_c(hm: float, lm: float) -> float:
    """Coeficiente αc según Art. 11.10.5."""
    r = hm / lm if lm > 0 else 0.0
    if r <= 1.5:
        return 0.80
    if r >= 2.0:
        return 0.53
    return 0.80 + (r - 1.5) * (0.53 - 0.80) / 0.5


def _Vc(
    geo: WallGeometry, mat: WallMaterials, Pu: float,
    hm_for_alpha_c: Optional[float] = None,
) -> float:
    """Resistencia al corte del concreto Vc (Art. 11.10.5 / 11.10.6).

    Si hm_for_alpha_c está dado (altura desde el nivel hasta el tope), se usa para αc
    en lugar de geo.hm, de modo que TABLA 4 y TABLA 4A coincidan (E.060).
    """
    hm_alpha = hm_for_alpha_c if hm_for_alpha_c is not None else geo.hm
    ac = _alpha_c(hm_alpha, geo.lm)
    Vc = geo.Acw * ac * mat.sqrt_fc

    # Factor de reducción por tracción (11.10.6)
    if Pu > 0:
        factor = max(0.0, 1.0 - Pu / (35.0 * geo.Acw))
        Vc *= factor
    return Vc


def _Vs(geo: WallGeometry, mat: WallMaterials, reinf: Reinforcement) -> float:
    """Resistencia al corte del acero Vs = Acw · ρh · fyt."""
    return geo.Acw * reinf.rho_h * mat.fyt


def _capacity_shear(Vu: float, Mn: float, Mua: float, R: float | None = None) -> float:
    """Cortante amplificado por capacidad (Art. 21.9.5.3 E.060). Factor = min(Mn/Mua, R)."""
    if Mua <= 0:
        return Vu
    R_val = (R if R is not None else C.R)
    ratio = min(Mn / Mua, R_val)  # Mn/Mua ≤ R
    return Vu * ratio


def _required_rho_h(
    geo: WallGeometry,
    mat: WallMaterials,
    Vu_cap: float,
    Vc: float,
    rho_h_min: float,
) -> float:
    """Cuantía horizontal requerida cuando φVn < Vu_cap.

    Siempre respeta como mínimo rho_h_min (caso 1: 0.002 ; caso 2: 0.0025).
    """
    Vn_req = Vu_cap / C.PHI_SHEAR
    Vs_req = Vn_req - Vc
    if Vs_req <= 0:
        return rho_h_min
    rho = Vs_req / (geo.Acw * mat.fyt) if (geo.Acw * mat.fyt) > 0 else 0.0
    return max(rho, rho_h_min)


def design_shear(
    geo: WallGeometry,
    mat: WallMaterials,
    loads: WallLoads,
    reinf: Reinforcement,
    flex: FlexureResult,
    R: float | None = None,
    vu_cap_demand: float | None = None,
    hm_for_Vc: float | None = None,
) -> tuple[ShearResult, Reinforcement]:
    """Diseño completo a corte con amplificación por capacidad.

    Si φVn < Vu_cap, ajusta automáticamente ρh y recalcula.
    Factor = min(Mn/Mua, R); R por defecto desde constantes.
    Si vu_cap_demand está dado (kg), se usa como Vu_cap en vez de calcularlo.
    Si hm_for_Vc está dado (cm, altura desde nivel hasta tope), se usa para αc en Vc.
    """
    Vu = abs(loads.Vu)
    Mua = abs(loads.Mu)

    if vu_cap_demand is not None:
        Vu_cap = vu_cap_demand
    else:
        Vu_cap = _capacity_shear(Vu, flex.Mn, Mua, R=R)
    Vc = _Vc(geo, mat, loads.Pu, hm_for_alpha_c=hm_for_Vc)
    Vs = _Vs(geo, mat, reinf)
    Vn = Vc + Vs
    phi_Vn = C.PHI_SHEAR * Vn

    # Cuantía mínima de acuerdo con 11.10.7 / 11.10.8 (mismo criterio que TABLA 8C):
    #   Caso 1 (Vu_cap < 0.27√f'c·Acw)  ->  ρh mín = 0.002
    #   Caso 2 (Vu_cap ≥ 0.27√f'c·Acw) ->  ρh mín = 0.0025
    threshold = C.SHEAR_COEF_1 * mat.sqrt_fc * geo.Acw
    rho_h_min = 0.0025 if Vu_cap >= threshold else 0.002

    if phi_Vn < Vu_cap:
        rho_new = _required_rho_h(geo, mat, Vu_cap, Vc, rho_h_min)
        reinf = Reinforcement(rho_h=rho_new, rho_v=reinf.rho_v, n_capas=reinf.n_capas)
        Vs = _Vs(geo, mat, reinf)
        Vn = Vc + Vs
        phi_Vn = C.PHI_SHEAR * Vn

    # 11.10.7/11.10.8: ρh adoptado debe ser al menos el mínimo normativo
    reinf = Reinforcement(
        rho_h=max(reinf.rho_h, rho_h_min),
        rho_v=reinf.rho_v,
        n_capas=reinf.n_capas,
    )
    Vs = _Vs(geo, mat, reinf)
    Vn = Vc + Vs
    phi_Vn = C.PHI_SHEAR * Vn

    _tol = 1e-9
    ok = phi_Vn >= Vu_cap * (1.0 - _tol)  # tolerancia numérica para evitar falso NO CUMPLE
    vn_max = C.SHEAR_COEF_2 * mat.sqrt_fc * geo.Acw
    vn_ok = Vn <= vn_max * (1.0 + _tol)

    result = ShearResult(
        Vu_orig=Vu, Vu_cap=Vu_cap, Vc=Vc, Vs=Vs,
        Vn=Vn, phi_Vn=phi_Vn, ok=ok,
        vn_limit_ok=vn_ok,
    )
    return result, reinf


# ── 8. Elementos de borde ──────────────────────────────────────────────

def _c_approx(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads, reinf: Reinforcement,
) -> float:
    """Aproximación de c (profundidad eje neutro)."""
    As_total = reinf.rho_v * geo.Acw
    Pu_abs = abs(loads.Pu) if loads.Pu < 0 else loads.Pu
    a = (As_total * mat.fy + Pu_abs) / (0.85 * mat.fc * geo.t)
    c = max(0.0, a / 0.85)
    return min(c, geo.lm)


def boundary_deformation(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
    reinf: Reinforcement,
) -> BoundaryResult:
    """Elementos de borde por deformación (Art. 21.9.7.4).

    C_lim = lm / [600 · (δu / H_total)]
    Requiere borde si c_base ≥ C_lim
    """
    delta_u = loads.delta_u
    if delta_u is None or delta_u <= 0:
        return BoundaryResult(requires=False, method="DEFORMACION",
                              details={"nota": "δu no proporcionado"})

    H = geo.hm
    if H <= 0:
        return BoundaryResult(requires=False, method="DEFORMACION",
                              details={"nota": "hm inválido"})

    # Cociente de deriva δu/H, limitado inferiormente a DEFORM_RATIO_MIN
    ratio = delta_u / H
    ratio_eff = max(ratio, C.DEFORM_RATIO_MIN)
    denom = C.DEFORM_DENOM * ratio_eff
    C_lim = geo.lm / denom if denom > 0 else geo.lm * 1000.0

    c_base = loads.c if loads.c is not None else _c_approx(geo, mat, loads, reinf)
    requires = c_base >= C_lim

    Mua = abs(loads.Mu)
    Vu = abs(loads.Vu)
    L_ext = None
    if requires:
        term_m = Mua / (4.0 * Vu) if Vu > 0 else geo.lm
        L_ext = max(geo.lm, term_m)

    largo_borde = None
    if requires and c_base > 0:
        largo_borde = max(c_base / 2.0, c_base - 0.10 * geo.lm)

    return BoundaryResult(
        requires=requires, method="DEFORMACION",
        details={
            "c_base": round(c_base, 2),
            "C_lim": round(C_lim, 2),
            "delta_u": delta_u,
            "H_total": H,
            "ratio_du_H": round(ratio, 6),
            "ratio_min_ok": ratio >= C.DEFORM_RATIO_MIN,
            "L_ext": round(L_ext, 2) if L_ext else None,
            "largo_borde": round(largo_borde, 2) if largo_borde else None,
        },
    )


def boundary_stress(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
) -> BoundaryResult:
    """Elementos de borde por esfuerzos (Art. 21.9.7.5).

    σ_max = Pu/Ag + Mu·y/Ig
    Requiere borde si σ > 0.20 f'c
    No requiere si σ < 0.15 f'c
    """
    Ag = geo.Acw
    if Ag <= 0:
        return BoundaryResult(requires=False, method="ESFUERZO",
                              details={"nota": "Ag inválido"})

    stress_axial = loads.Pu / Ag
    y = geo.lm / 2.0
    Ig = geo.Ig
    stress_flex = abs(loads.Mu) * y / Ig if Ig > 0 else 0.0

    sigma_max = max(0.0, stress_axial + stress_flex, stress_axial - stress_flex)

    limit_on = C.STRESS_ON * mat.fc
    limit_off = C.STRESS_OFF * mat.fc

    if sigma_max > limit_on:
        requires = True
    elif sigma_max < limit_off:
        requires = False
    else:
        requires = False

    largo_borde = None
    if requires:
        c_base = loads.c if loads.c is not None else _c_approx(
            geo, mat, loads, Reinforcement())
        if c_base > 0:
            largo_borde = max(c_base / 2.0, c_base - 0.10 * geo.lm)

    return BoundaryResult(
        requires=requires, method="ESFUERZO",
        details={
            "sigma_max": round(sigma_max, 2),
            "limit_ON": round(limit_on, 2),
            "limit_OFF": round(limit_off, 2),
            "largo_borde": round(largo_borde, 2) if largo_borde else None,
        },
    )


def design_boundary(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
    reinf: Reinforcement, method: Optional[str] = None,
) -> BoundaryResult:
    """Selecciona método de elementos de borde.

    Si method es None, auto-detecta: DEFORMACION si hay δu, sino ESFUERZO.
    """
    if method is None:
        method = "DEFORMACION" if (loads.delta_u is not None and loads.delta_u > 0) else "ESFUERZO"

    if method == "DEFORMACION":
        return boundary_deformation(geo, mat, loads, reinf)
    return boundary_stress(geo, mat, loads)


# ── 9. Juntas de construcción ──────────────────────────────────────────

def verify_joint(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
    Vu_cap: float, Av: float, mu: float = 1.0,
) -> JointResult:
    """Verificación de juntas (Art. 11.7 / 21.9.8).

    φVn = φ · μ · (Nu + Av · fy)
    Con límites: Vn < 0.2 f'c·Ac  y  Vn < 55·Ac
    """
    Vn = mu * (abs(loads.Pu) + Av * mat.fy)
    lim1 = C.JOINT_COEF_1 * mat.fc * geo.Acw
    lim2 = C.JOINT_COEF_2 * geo.Acw
    Vn = min(Vn, lim1, lim2)
    phi_Vn = C.PHI_SHEAR * Vn
    ok = phi_Vn >= Vu_cap
    return JointResult(Vn_joint=Vn, phi_Vn_joint=phi_Vn, ok=ok, Av=Av, mu=mu)


# ── Compresión pura (14.5.2) ──────────────────────────────────────────

def compression_capacity(
    geo: WallGeometry, mat: WallMaterials, k: float = 1.0,
) -> float:
    """φPn = 0.55 · φ · f'c · Ag · [1 − (k·lc / (32·h))²]."""
    lc = geo.hm
    h = geo.t
    ratio = (k * lc) / (32.0 * h) if h > 0 else 0.0
    factor = max(0.0, 1.0 - ratio ** 2)
    return C.COMPRESSION_FACTOR * C.PHI_FLEX * mat.fc * geo.Acw * factor


# ── Acero mínimo distribuido ───────────────────────────────────────────

def minimum_reinforcement_check(
    geo: WallGeometry, mat: WallMaterials, loads: WallLoads,
) -> dict:
    """Verifica cuantías mínimas según Art. 11.10.7 / 11.10.8."""
    threshold = C.SHEAR_COEF_1 * mat.sqrt_fc * geo.Acw
    Vu = abs(loads.Vu)
    if Vu < threshold:
        rho_h_min, rho_v_min = 0.0020, 0.0015
    else:
        rho_h_min, rho_v_min = 0.0025, 0.0025
    return {
        "Vu": round(Vu, 2),
        "umbral": round(threshold, 2),
        "Vu_mayor": Vu >= threshold,
        "rho_h_min": rho_h_min,
        "rho_v_min": rho_v_min,
    }


# ══════════════════════════════════════════════════════════════════════
# ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def design_wall(
    nombre: str,
    geo: WallGeometry,
    mat: WallMaterials,
    loads: WallLoads,
    boundary_method: Optional[str] = None,
    joint_Av: Optional[float] = None,
    joint_mu: float = 1.0,
    R: float | None = None,
    vu_cap_demand: float | None = None,
    hm_for_Vc: float | None = None,
) -> WallDesignResult:
    """Ejecuta el flujo completo de diseño de un muro según RNE E.060.

    Pasos:
      1. Verificar espesor
      2-4. Determinar refuerzo preliminar
      5. Diseñar a flexión
      6. Verificar agrietamiento
      7. Diseñar a corte (amplificación por capacidad)
      8. Evaluar elementos de borde
      9. Verificar juntas (si Av se proporciona)
    """
    # 1. Espesor
    geom_ok, thick_msg = verify_thickness(geo)

    # 2-4. Refuerzo preliminar
    reinf = preliminary_reinforcement(geo, mat, loads)

    # 5. Flexión
    flex = design_flexure(geo, mat, loads, reinf)

    # 6. Agrietamiento
    flex = check_cracking(geo, mat, flex, loads.Pu)

    # 7. Corte (factor min(Mn/Mua, R) o vu_cap_demand si se proporciona; hm_for_Vc para αc)
    shear, reinf = design_shear(
        geo, mat, loads, reinf, flex, R=R,
        vu_cap_demand=vu_cap_demand, hm_for_Vc=hm_for_Vc,
    )

    # 8. Elementos de borde
    boundary = design_boundary(geo, mat, loads, reinf, boundary_method)

    # 9. Juntas (mismo criterio que TABLA 8D: si con Av actual no alcanza, se puede subir Av hasta cumplir)
    joint = None
    Av_eff = reinf.rho_v * geo.Acw
    if Av_eff > 0:
        joint = verify_joint(geo, mat, loads, shear.Vu_cap, Av_eff, joint_mu)
        if joint is not None and not joint.ok and geo.Acw > 0 and mat.fy > 0:
            # Calcular Av requerido para φVn ≥ Vu_cap (igual que TABLA 8D)
            Vn_req = shear.Vu_cap / C.PHI_SHEAR
            lim1 = C.JOINT_COEF_1 * mat.fc * geo.Acw
            lim2 = C.JOINT_COEF_2 * geo.Acw
            Vn_max = min(lim1, lim2)
            if Vn_req <= Vn_max:
                Av_req = (Vn_req / joint_mu - abs(loads.Pu)) / mat.fy
                Av_req = max(0.0, Av_req)
                Av_use = max(Av_eff, Av_req)
                Vn_j = joint_mu * (abs(loads.Pu) + Av_use * mat.fy)
                Vn_j = min(Vn_j, lim1, lim2)
                phi_Vn_j = C.PHI_SHEAR * Vn_j
                if phi_Vn_j >= shear.Vu_cap:
                    joint = JointResult(
                        Vn_joint=Vn_j, phi_Vn_joint=phi_Vn_j, ok=True,
                        Av=Av_use, mu=joint_mu,
                    )

    return WallDesignResult(
        nombre=nombre,
        geometry_ok=geom_ok,
        thickness_msg=thick_msg,
        flexure=flex,
        shear=shear,
        reinforcement=reinf,
        boundary=boundary,
        joint=joint,
    )


# ══════════════════════════════════════════════════════════════════════
# DISEÑO MULTIPISO
# ══════════════════════════════════════════════════════════════════════

def _boundary_deformation_global(
    lm: float, t: float, H_total: float,
    mat: WallMaterials, delta_u: float, c_base: float,
    Mua_base: float, Vu_base: float,
    height_2_floors: float,
    Pu_base_kg: float = 0.0,
) -> BoundaryResult:
    """Elementos de borde DEFORMACION global (Art. 21.9.7.4)."""
    if delta_u <= 0 or H_total <= 0:
        return BoundaryResult(requires=False, method="DEFORMACION",
                              details={"nota": "delta_u o H_total invalido"})

    # Cociente de deriva global δu/H_total, limitado inferiormente a DEFORM_RATIO_MIN
    ratio = delta_u / H_total
    ratio_eff = max(ratio, C.DEFORM_RATIO_MIN)
    denom = C.DEFORM_DENOM * ratio_eff
    C_lim = lm / denom if denom > 0 else lm * 1000.0
    requires = c_base >= C_lim

    L_ext = None
    largo_borde = None
    if requires:
        term_m = Mua_base / (4.0 * Vu_base) if Vu_base > 0 else lm
        L_ext = max(lm, term_m, height_2_floors)
        if c_base > 0:
            largo_borde = max(c_base / 2.0, c_base - 0.10 * lm)

    # Pu en Tn y deformación en acero de borde (εs ≈ 0.003*(lm - c)/c)
    Pu_tn = round(Pu_base_kg / 1000.0, 2) if Pu_base_kg else 0.0
    epsilon_s = round(0.003 * (lm - c_base) / c_base, 4) if c_base > 0 and c_base < lm else None

    return BoundaryResult(
        requires=requires, method="DEFORMACION",
        details={
            "c_base": round(c_base, 2), "C_lim": round(C_lim, 2),
            "delta_u": delta_u, "H_total": H_total,
            "ratio_du_H": round(ratio, 6),
            "ratio_min_ok": ratio >= C.DEFORM_RATIO_MIN,
            "L_ext": round(L_ext, 2) if L_ext else None,
            "z_end": round(min(H_total, L_ext), 2) if L_ext else None,
            "largo_borde": round(largo_borde, 2) if largo_borde else None,
            "Pu_tn": Pu_tn,
            "epsilon_s": epsilon_s,
        },
    )


def _boundary_stress_global(
    lm: float, t: float, H_total: float,
    mat: WallMaterials,
    stories_sorted: list[StoryData],
) -> BoundaryResult:
    """Elementos de borde ESFUERZO global (Art. 21.9.7.5)."""
    Ag = lm * t
    Ig = t * lm ** 3 / 12.0
    y = lm / 2.0
    limit_on = C.STRESS_ON * mat.fc
    limit_off = C.STRESS_OFF * mat.fc

    stress_report = []
    z_current = 0.0
    prev_state = False
    segments = []
    seg_start = None

    for story in stories_sorted:
        s_axial = story.Pu / Ag if Ag > 0 else 0.0
        s_flex = abs(story.Mu) * y / Ig if Ig > 0 else 0.0
        sigma_max = max(0.0, s_axial + s_flex, s_axial - s_flex)

        if sigma_max > limit_on:
            state_on = True
        elif sigma_max < limit_off:
            state_on = False
        else:
            state_on = prev_state

        stress_report.append({
            "piso": story.piso, "z": round(z_current, 2),
            "sigma_max": round(sigma_max, 2),
            "estado": "ON" if state_on else "OFF",
        })

        if state_on and seg_start is None:
            seg_start = z_current
        elif not state_on and seg_start is not None:
            segments.append((seg_start, z_current))
            seg_start = None

        prev_state = state_on
        z_current += story.hm

    if seg_start is not None:
        segments.append((seg_start, H_total))

    requires = len(segments) > 0
    return BoundaryResult(
        requires=requires, method="ESFUERZO",
        details={
            "stress_report": stress_report,
            "segments": segments,
            "limit_ON": round(limit_on, 2),
            "limit_OFF": round(limit_off, 2),
        },
    )


def design_wall_multi_story(
    nombre: str,
    lm: float, t: float,
    mat: WallMaterials,
    stories: list[StoryData],
    boundary_method: Optional[str] = None,
    delta_u: Optional[float] = None,
    joint_Av: Optional[float] = None,
    joint_mu: float = 1.0,
    k_buckling: float = 1.0,
    R: float | None = None,
) -> MultiStoryResult:
    """Diseño multipiso de un muro según RNE E.060.

    Para cada piso: flexion, agrietamiento, corte (sin borde individual).
    Luego calcula elementos de borde globalmente con H_total.
    """
    sorted_stories = sorted(stories, key=lambda s: s.piso)
    H_total = sum(s.hm for s in sorted_stories)

    story_results: list[StoryDesignResult] = []

    for story in sorted_stories:
        geo = WallGeometry(hm=story.hm, lm=lm, t=t)
        loads = WallLoads(
            Pu=story.Pu, Vu=story.Vu, Mu=story.Mu,
            Mn_manual=story.Mn_manual, c=story.c,
        )
        # hm desde este nivel hasta el tope (para αc en Vc; coherente con TABLA 4A)
        hm_desde_nivel_hasta_tope = sum(
            s.hm for s in sorted_stories if s.piso >= story.piso
        )
        result = design_wall(
            nombre=f"{nombre}_P{story.piso}",
            geo=geo, mat=mat, loads=loads,
            boundary_method=None,
            joint_Av=joint_Av, joint_mu=joint_mu,
            R=R,
            vu_cap_demand=story.Vu_cap_demand,
            hm_for_Vc=hm_desde_nivel_hasta_tope,
        )
        story_results.append(StoryDesignResult(
            piso=story.piso, result=result,
        ))

    # Auto-detectar metodo de borde
    if boundary_method is None:
        boundary_method = "DEFORMACION" if delta_u is not None else "ESFUERZO"

    # Calcular borde globalmente
    base_story = sorted_stories[0]
    base_result = story_results[0].result
    boundary_global = None

    if boundary_method == "DEFORMACION" and delta_u is not None:
        if base_story.c is not None:
            c_base = base_story.c
        else:
            c_base = _c_approx(
                WallGeometry(hm=base_story.hm, lm=lm, t=t),
                mat,
                WallLoads(Pu=base_story.Pu, Vu=base_story.Vu, Mu=base_story.Mu),
                base_result.reinforcement,
            )

        height_2 = sum(s.hm for s in sorted_stories[:2]) if len(sorted_stories) >= 2 else sorted_stories[0].hm

        boundary_global = _boundary_deformation_global(
            lm, t, H_total, mat, delta_u, c_base,
            abs(base_story.Mu), abs(base_story.Vu),
            height_2,
            Pu_base_kg=base_story.Pu,
        )

        z_end = boundary_global.details.get("z_end")
        largo = boundary_global.details.get("largo_borde")
        z_acc = 0.0
        for sr in story_results:
            st = next(s for s in sorted_stories if s.piso == sr.piso)
            z_start = z_acc
            z_acc += st.hm
            req = False
            if boundary_global.requires and z_end is not None:
                if z_start < z_end and z_acc > 0:
                    req = True
            sr.requires_boundary = req
            sr.largo_borde = largo if req else None
            sr.boundary_height = st.hm if req else None

    elif boundary_method == "ESFUERZO":
        boundary_global = _boundary_stress_global(
            lm, t, H_total, mat, sorted_stories)

        segs = boundary_global.details.get("segments", [])
        if base_story.c is not None:
            c_unique = base_story.c
        else:
            c_unique = _c_approx(
                WallGeometry(hm=base_story.hm, lm=lm, t=t),
                mat,
                WallLoads(Pu=base_story.Pu, Vu=base_story.Vu, Mu=base_story.Mu),
                base_result.reinforcement,
            )
        largo = max(c_unique / 2.0, c_unique - 0.10 * lm) if c_unique > 0 else None

        z_acc = 0.0
        for sr in story_results:
            st = next(s for s in sorted_stories if s.piso == sr.piso)
            z_start = z_acc
            z_end_story = z_acc + st.hm
            z_acc = z_end_story
            req = False
            for seg_s, seg_e in segs:
                if seg_s < z_end_story and seg_e > z_start:
                    req = True
                    break
            sr.requires_boundary = req
            sr.largo_borde = largo if req else None
            sr.boundary_height = st.hm if req else None

    # Compresion pura
    geo_total = WallGeometry(hm=H_total, lm=lm, t=t)
    phi_Pn = compression_capacity(geo_total, mat, k_buckling)

    return MultiStoryResult(
        nombre=nombre, lm=lm, t=t, H_total=H_total,
        stories=story_results,
        boundary_global=boundary_global,
        delta_u=delta_u, k_buckling=k_buckling,
        compression_phi_Pn=phi_Pn,
    )
