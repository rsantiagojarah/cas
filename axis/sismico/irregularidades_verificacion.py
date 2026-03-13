"""
Verificacion de irregularidades E.030 (Tablas N° 8 y N° 9).
Calculos numericos a partir de datos ingresados manualmente.
Independiente del analisis sismico.
"""

from __future__ import annotations


# --- Tabla 9: Irregularidad torsional ---
# Existe si: Delta_max > 1.3 * Delta_prom (promedio de extremos)
# Extrema si: Delta_max > 1.5 * Delta_prom
# EXCEPCION (Tabla 9): El criterio solo se aplica si Delta_max > 50% del desplazamiento
# permisible (Tabla 11). El usuario indica si aplica o no (no se calcula).
def verificar_torsional(delta_a: float, delta_b: float) -> dict:
    """
    Tabla 9 - Irregularidad torsional.
    delta_a, delta_b: desplazamientos relativos en extremos (incl. excentricidad accidental).
    """
    da, db = abs(float(delta_a)), abs(float(delta_b))
    delta_max = max(da, db)
    delta_prom = (da + db) / 2.0
    if delta_prom <= 0:
        return {"existe": False, "extrema": False, "delta_max": delta_max,
                "delta_prom": delta_prom, "ratio": None}
    ratio = delta_max / delta_prom
    extrema = ratio > 1.5
    existe = ratio > 1.3
    return {"existe": existe, "extrema": extrema, "delta_max": delta_max,
            "delta_prom": delta_prom, "ratio": round(ratio, 4)}


# --- Tabla 8: Piso blando (rigidez) ---
# k_i < 0.70*k_sup O k_i < 0.80*prom(k_sup1,k_sup2,k_sup3)
def verificar_piso_blando(
    k_i: float,
    k_sup: float,
    k_sup2: float | None = None,
    k_sup3: float | None = None,
) -> dict:
    """
    Tabla 8 - Irregularidad de rigidez (piso blando).
    k_i: rigidez lateral del piso en analisis.
    k_sup: rigidez del piso inmediato superior.
    k_sup2, k_sup3: opcionales para promedio de 3 pisos superiores.
    """
    ki = float(k_i)
    ksup = float(k_sup)
    if ksup <= 0:
        return {"existe": False, "ratio_sup": None, "ratio_prom3": None}
    ratio_sup = ki / ksup
    crit1 = ratio_sup < 0.70
    crit2 = False
    ratio_prom3 = None
    if k_sup2 is not None and k_sup3 is not None:
        prom = (ksup + float(k_sup2) + float(k_sup3)) / 3.0
        if prom > 0:
            ratio_prom3 = ki / prom
            crit2 = ratio_prom3 < 0.80
    existe = crit1 or crit2
    return {"existe": existe, "ratio_sup": round(ratio_sup, 4),
            "ratio_prom3": round(ratio_prom3, 4) if ratio_prom3 is not None else None}


def verificar_piso_blando_todos(rigideces: list[float]) -> list[dict]:
    """
    Verifica piso blando para todos los entrepisos.
    rigideces: [k1, k2, ..., kn] de abajo hacia arriba (k1=base, kn=azotea).
    Retorna lista de dict por cada entrepiso (azotea no se verifica).
    """
    ks = [float(k) for k in rigideces]
    if len(ks) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(ks) - 1):
        k_sup2 = ks[i + 2] if i + 2 < len(ks) else None
        k_sup3 = ks[i + 3] if i + 3 < len(ks) else None
        r = verificar_piso_blando(ks[i], ks[i + 1], k_sup2, k_sup3)
        resultados.append({"piso": i + 1, "k_i": ks[i], "k_sup": ks[i + 1], **r})
    return resultados


# --- Tabla 8: Irregularidad extrema de rigidez ---
# k_i < 0.60*k_sup O k_i < 0.70*prom(k_sup1,k_sup2,k_sup3)
def verificar_extrema_rigidez(
    k_i: float,
    k_sup: float,
    k_sup2: float | None = None,
    k_sup3: float | None = None,
) -> dict:
    """Tabla 8 - Irregularidad extrema de rigidez."""
    ki = float(k_i)
    ksup = float(k_sup)
    if ksup <= 0:
        return {"existe": False, "ratio_sup": None, "ratio_prom3": None}
    ratio_sup = ki / ksup
    crit1 = ratio_sup < 0.60
    crit2 = False
    ratio_prom3 = None
    if k_sup2 is not None and k_sup3 is not None:
        prom = (ksup + float(k_sup2) + float(k_sup3)) / 3.0
        if prom > 0:
            ratio_prom3 = ki / prom
            crit2 = ratio_prom3 < 0.70
    existe = crit1 or crit2
    return {"existe": existe, "ratio_sup": round(ratio_sup, 4),
            "ratio_prom3": round(ratio_prom3, 4) if ratio_prom3 is not None else None}


def verificar_extrema_rigidez_todos(rigideces: list[float]) -> list[dict]:
    """Verifica irregularidad extrema de rigidez para todos los entrepisos."""
    ks = [float(k) for k in rigideces]
    if len(ks) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(ks) - 1):
        k_sup2 = ks[i + 2] if i + 2 < len(ks) else None
        k_sup3 = ks[i + 3] if i + 3 < len(ks) else None
        r = verificar_extrema_rigidez(ks[i], ks[i + 1], k_sup2, k_sup3)
        resultados.append({"piso": i + 1, "k_i": ks[i], "k_sup": ks[i + 1], **r})
    return resultados


def verificar_rigidez_unificado(rigideces: list[float]) -> list[dict]:
    """
    Verificacion unificada: piso blando y extrema rigidez en un solo calculo.
    Retorna por piso: clasificacion (Regular|Piso blando|Extrema), Ia.
    """
    ks = [float(k) for k in rigideces]
    if len(ks) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(ks) - 1):
        ki, ksup = ks[i], ks[i + 1]
        k_sup2 = ks[i + 2] if i + 2 < len(ks) else None
        k_sup3 = ks[i + 3] if i + 3 < len(ks) else None
        ratio_sup = ki / ksup if ksup > 0 else None
        ratio_prom3 = None
        if k_sup2 is not None and k_sup3 is not None:
            prom = (ksup + k_sup2 + k_sup3) / 3.0
            ratio_prom3 = ki / prom if prom > 0 else None
        extrema = (ratio_sup is not None and ratio_sup < 0.60) or (
            ratio_prom3 is not None and ratio_prom3 < 0.70
        )
        piso_blando = (ratio_sup is not None and ratio_sup < 0.70) or (
            ratio_prom3 is not None and ratio_prom3 < 0.80
        )
        if extrema:
            clasif, ia = "Extrema", 0.50
        elif piso_blando:
            clasif, ia = "Piso blando", 0.75
        else:
            clasif, ia = "Regular", 1.0
        resultados.append({
            "piso": i + 1, "k_i": ki, "k_sup": ksup,
            "ratio_sup": round(ratio_sup, 4) if ratio_sup is not None else None,
            "ratio_prom3": round(ratio_prom3, 4) if ratio_prom3 is not None else None,
            "clasificacion": clasif, "Ia": ia,
        })
    # Azotea: no tiene piso superior, no se verifica. Se agrega fila con k_sup=0 para mostrar 8 pisos.
    resultados.append({
        "piso": len(ks),
        "k_i": ks[-1],
        "k_sup": 0,
        "ratio_sup": None,
        "ratio_prom3": None,
        "clasificacion": "N/A",
        "Ia": 1.0,
    })
    return resultados


# --- Tabla 8: Piso debil (resistencia) ---
# V_res_i < 0.80 * V_res_sup
def verificar_piso_debil(v_res_i: float, v_res_sup: float) -> dict:
    """Tabla 8 - Irregularidad de resistencia (piso debil)."""
    vi, vsup = float(v_res_i), float(v_res_sup)
    if vsup <= 0:
        return {"existe": False, "ratio": None}
    ratio = vi / vsup
    return {"existe": ratio < 0.80, "ratio": round(ratio, 4)}


def verificar_piso_debil_todos(resistencias: list[float]) -> list[dict]:
    """Verifica piso debil para todos los entrepisos. resistencias: [V1 V2 ... Vn]."""
    vs = [float(v) for v in resistencias]
    if len(vs) < 2:
        return []
    return [
        {"piso": i + 1, "V_res_i": vs[i], "V_res_sup": vs[i + 1], **verificar_piso_debil(vs[i], vs[i + 1])}
        for i in range(len(vs) - 1)
    ]


# --- Tabla 8: Irregularidad extrema de resistencia ---
# V_res_i < 0.65 * V_res_sup
def verificar_extrema_resistencia(v_res_i: float, v_res_sup: float) -> dict:
    """Tabla 8 - Irregularidad extrema de resistencia."""
    vi, vsup = float(v_res_i), float(v_res_sup)
    if vsup <= 0:
        return {"existe": False, "ratio": None}
    ratio = vi / vsup
    return {"existe": ratio < 0.65, "ratio": round(ratio, 4)}


def verificar_extrema_resistencia_todos(resistencias: list[float]) -> list[dict]:
    """Verifica irregularidad extrema de resistencia para todos los entrepisos."""
    vs = [float(v) for v in resistencias]
    if len(vs) < 2:
        return []
    return [
        {"piso": i + 1, "V_res_i": vs[i], "V_res_sup": vs[i + 1], **verificar_extrema_resistencia(vs[i], vs[i + 1])}
        for i in range(len(vs) - 1)
    ]


def verificar_resistencia_unificado(resistencias: list[float]) -> list[dict]:
    """
    Verificacion unificada: piso debil y extrema resistencia en un solo calculo.
    Retorna por piso: clasificacion (Regular|Piso debil|Extrema), Ia.
    """
    vs = [float(v) for v in resistencias]
    if len(vs) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(vs) - 1):
        vi, vsup = vs[i], vs[i + 1]
        ratio = vi / vsup if vsup > 0 else None
        if ratio is None:
            clasif, ia = "Regular", 1.0
        elif ratio < 0.65:
            clasif, ia = "Extrema", 0.50
        elif ratio < 0.80:
            clasif, ia = "Piso debil", 0.75
        else:
            clasif, ia = "Regular", 1.0
        resultados.append({
            "piso": i + 1, "V_res_i": vi, "V_res_sup": vsup,
            "ratio": round(ratio, 4) if ratio is not None else None,
            "clasificacion": clasif, "Ia": ia,
        })
    # Azotea: no tiene piso superior, no se verifica. Se agrega fila para mostrar todos los pisos.
    resultados.append({
        "piso": len(vs),
        "V_res_i": vs[-1],
        "V_res_sup": 0,
        "ratio": None,
        "clasificacion": "N/A",
        "Ia": 1.0,
    })
    return resultados


# --- Tabla 8: Irregularidad de masa ---
# peso_i > 1.5 * peso_adyacente (no azotea/sotano)
def verificar_masa(peso_i: float, peso_adyacente: float) -> dict:
    """Tabla 8 - Irregularidad de masa o peso."""
    pi, pa = float(peso_i), float(peso_adyacente)
    if pa <= 0:
        return {"existe": False, "ratio": None}
    ratio = pi / pa
    return {"existe": ratio > 1.5, "ratio": round(ratio, 4)}


def verificar_masa_todos(pesos: list[float], hay_sotano: bool = False) -> list[dict]:
    """
    Verifica irregularidad de masa para todos los pisos. pesos: [P1 P2 ... Pn].
    Si hay_sotano=True, el primer piso (sótano) no aplica criterio (Tabla 8)
    y no se usa como adyacente para el piso superior.
    """
    ps = [float(p) for p in pesos]
    if len(ps) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(ps)):
        # Sótano (primer piso): no aplica criterio (Tabla 8).
        if hay_sotano and i == 0:
            resultados.append({
                "piso": i + 1,
                "peso": ps[i],
                "existe": False,
                "ratio": None,
                "aplica": False,
            })
            continue
        # Azotea: no aplica criterio de irregularidad de masa (Tabla 8).
        if i == len(ps) - 1:
            resultados.append({
                "piso": i + 1,
                "peso": ps[i],
                "existe": False,
                "ratio": None,
                "aplica": False,
            })
            continue
        existe = False
        ratio = None
        # Comparar con piso inferior (no usar sótano como adyacente).
        if i > 0 and ps[i - 1] > 0 and not (hay_sotano and i == 1):
            r = ps[i] / ps[i - 1]
            if r > 1.5:
                existe = True
            ratio = round(r, 4)
        # No comparar con azotea (ultimo piso).
        if i < len(ps) - 2 and ps[i + 1] > 0:
            r = ps[i] / ps[i + 1]
            if r > 1.5:
                existe = True
            ratio = round(r, 4)
        resultados.append({
            "piso": i + 1,
            "peso": ps[i],
            "existe": existe,
            "ratio": ratio,
            "aplica": True,
        })
    return resultados


# --- Tabla 8: Irregularidad geometrica vertical ---
# dim_planta_i > 1.3 * dim_planta_adyacente (no azotea/sotano)
def verificar_geometrica_vertical(dim_i: float, dim_adyacente: float) -> dict:
    """Tabla 8 - Irregularidad geometrica vertical."""
    di, da = float(dim_i), float(dim_adyacente)
    if da <= 0:
        return {"existe": False, "ratio": None}
    ratio = di / da
    return {"existe": ratio > 1.3, "ratio": round(ratio, 4)}


def verificar_geometrica_vertical_todos(dimensiones: list[float]) -> list[dict]:
    """Verifica irregularidad geometrica vertical. dimensiones: [D1 D2 ... Dn]."""
    ds = [float(d) for d in dimensiones]
    if len(ds) < 2:
        return []
    resultados: list[dict] = []
    for i in range(len(ds)):
        # Azotea: no aplica criterio de irregularidad geometrica vertical (Tabla 8).
        if i == len(ds) - 1:
            resultados.append({
                "piso": i + 1,
                "dim": ds[i],
                "existe": False,
                "ratio": None,
                "aplica": False,
            })
            continue
        existe = False
        ratio = None
        if i > 0 and ds[i - 1] > 0:
            r = ds[i] / ds[i - 1]
            if r > 1.3:
                existe = True
            ratio = round(r, 4)
        # No comparar con azotea (ultimo piso).
        if i < len(ds) - 2 and ds[i + 1] > 0:
            r = ds[i] / ds[i + 1]
            if r > 1.3:
                existe = True
            ratio = round(r, 4)
        resultados.append({
            "piso": i + 1,
            "dim": ds[i],
            "existe": existe,
            "ratio": ratio,
            "aplica": True,
        })
    return resultados


# --- Tabla 9: Esquinas entrantes ---
# dim_entrante > 20% dim_total en AMBAS direcciones
def verificar_esquinas_entrantes(
    dim_entrante_a: float,
    dim_entrante_b: float,
    dim_total_a: float,
    dim_total_b: float,
) -> dict:
    """
    Tabla 9 - Esquinas entrantes.
    dim_entrante_a/b: dimension del entrante en cada direccion.
    dim_total_a/b: dimension total en planta en cada direccion.
    """
    ea, eb = float(dim_entrante_a), float(dim_entrante_b)
    ta, tb = float(dim_total_a), float(dim_total_b)
    if ta <= 0 or tb <= 0:
        return {"existe": False, "pct_a": None, "pct_b": None}
    pct_a = (ea / ta) * 100
    pct_b = (eb / tb) * 100
    existe = pct_a > 20 and pct_b > 20
    return {"existe": existe, "pct_a": round(pct_a, 2), "pct_b": round(pct_b, 2)}


def verificar_esquinas_entrantes_todos(datos: list[tuple[float, float, float, float]]) -> list[dict]:
    """Verifica esquinas entrantes por piso. datos: [(ea,eb,ta,tb), ...] por piso."""
    resultados: list[dict] = []
    for i, (ea, eb, ta, tb) in enumerate(datos):
        r = verificar_esquinas_entrantes(ea, eb, ta, tb)
        resultados.append({"piso": i + 1, "pct_a": r["pct_a"], "pct_b": r["pct_b"], **r})
    return resultados


# --- Tabla 9: Discontinuidad del diafragma ---
# Abertura > 50% area bruta, O seccion neta < 25% seccion total
def verificar_diafragma(
    area_abertura: float,
    area_bruta: float,
    seccion_neta: float | None = None,
    seccion_total: float | None = None,
) -> dict:
    """
    Tabla 9 - Discontinuidad del diafragma.
    Criterio 1: area_abertura > 50% area_bruta.
    Criterio 2 (opcional): seccion_neta < 25% seccion_total.
    """
    ab, br = float(area_abertura), float(area_bruta)
    if br <= 0:
        return {"existe": False, "pct_abertura": None, "pct_seccion": None}
    pct_abertura = (ab / br) * 100
    crit1 = pct_abertura > 50
    crit2 = False
    pct_seccion = None
    if seccion_neta is not None and seccion_total is not None:
        sn, st = float(seccion_neta), float(seccion_total)
        if st > 0:
            pct_seccion = (sn / st) * 100
            crit2 = pct_seccion < 25
    existe = crit1 or crit2
    return {"existe": existe, "pct_abertura": round(pct_abertura, 2),
            "pct_seccion": round(pct_seccion, 2) if pct_seccion is not None else None}


def verificar_diafragma_todos(datos: list[tuple[float, float, float | None, float | None]]) -> list[dict]:
    """Verifica diafragma por piso. datos: [(ab,br,sn?,st?), ...]."""
    resultados: list[dict] = []
    for i, row in enumerate(datos):
        ab, br = row[0], row[1]
        sn = row[2] if len(row) > 2 else None
        st = row[3] if len(row) > 3 else None
        r = verificar_diafragma(ab, br, sn, st)
        resultados.append({"piso": i + 1, "pct_abertura": r["pct_abertura"], **r})
    return resultados


# --- Tabla 9: Sistemas no paralelos ---
# Angulo > 30° y elementos no paralelos resisten > 10% cortante
def verificar_sistemas_no_paralelos(
    angulo_grados: float,
    pct_cortante_no_paralelos: float,
) -> dict:
    """
    Tabla 9 - Sistemas no paralelos.
    angulo_grados: angulo entre ejes de marcos/muros.
    pct_cortante_no_paralelos: % del cortante de piso en elementos no paralelos.
    """
    ang = float(angulo_grados)
    pct = float(pct_cortante_no_paralelos)
    existe = ang > 30 and pct > 10
    return {"existe": existe, "angulo": ang, "pct_cortante": pct}


def verificar_sistemas_no_paralelos_todos(datos: list[tuple[float, float]]) -> list[dict]:
    """Verifica sistemas no paralelos por piso. datos: [(angulo,pct), ...]."""
    resultados: list[dict] = []
    for i, (ang, pct) in enumerate(datos):
        r = verificar_sistemas_no_paralelos(ang, pct)
        resultados.append({"piso": i + 1, **r})
    return resultados


# --- Tabla 8: Discontinuidad en sistemas resistentes ---
# Desalineamiento vertical: desplazamiento del eje > 25% de la dimension del elemento
def verificar_discontinuidad_sistemas(
    pct_cortante_discontinuos: float,
) -> dict:
    """
    Tabla 8 - Discontinuidad en sistemas resistentes.
    pct_cortante_discontinuos: % del cortante de piso en elementos con desalineamiento.
    """
    pct = float(pct_cortante_discontinuos)
    existe = pct > 10
    return {"existe": existe, "pct": round(pct, 2)}


def verificar_discontinuidad_sistemas_todos(pct_por_piso: list[float]) -> list[dict]:
    """Verifica discontinuidad por piso. pct_por_piso: [pct1, pct2, ...]."""
    return [
        {"piso": i + 1, **verificar_discontinuidad_sistemas(p)}
        for i, p in enumerate(pct_por_piso)
    ]


# --- Tabla 8: Discontinuidad extrema ---
# Cortante en elementos discontinuos > 25%
def verificar_discontinuidad_extrema(
    pct_cortante_discontinuos: float,
) -> dict:
    """Tabla 8 - Discontinuidad extrema en sistemas resistentes."""
    pct = float(pct_cortante_discontinuos)
    existe = pct > 25
    return {"existe": existe, "pct": round(pct, 2)}


def verificar_discontinuidad_extrema_todos(pct_por_piso: list[float]) -> list[dict]:
    """Verifica discontinuidad extrema por piso."""
    return [
        {"piso": i + 1, **verificar_discontinuidad_extrema(p)}
        for i, p in enumerate(pct_por_piso)
    ]


def verificar_discontinuidad_por_desalineamiento(
    desalineamiento_por_piso: list[float],
) -> list[dict]:
    """
    Verificacion por desalineamiento vertical (E.030 Tabla 8).
    desalineamiento_por_piso: [d1, d2, ...] = desalineamiento vertical (% de la
    dimension del elemento) en cada piso. Existe cuando desplazamiento del eje
    > 25% de la dimension. d>25% -> Discontinuidad (Ia=0.80); else Regular (Ia=1.0).
    Para extrema se requiere ademas el % de cortante en elementos discontinuos.
    """
    resultados: list[dict] = []
    for i, d in enumerate(desalineamiento_por_piso):
        val = float(d)
        if val > 25:
            clasif, ia = "Discontinuidad", 0.80
        else:
            clasif, ia = "Regular", 1.0
        resultados.append({
            "piso": i + 1,
            "Desalineamiento": round(val, 2),
            "clasificacion": clasif,
            "Ia": ia,
        })
    return resultados


def verificar_discontinuidad_por_longitud_desplazamiento(
    pares_longitud_desplazamiento: list[tuple[float, float]],
) -> list[dict]:
    """
    Verificacion por desalineamiento vertical (E.030 Tabla 8).
    Input: [(L1,d1), (L2,d2), ...] = (longitud del elemento, distancia de desalineamiento)
    por piso. Si no hay desalineamiento, d=0.
    Calcula pct = (d/L)*100. Si pct>25% -> Discontinuidad (Ia=0.80); else Regular (Ia=1.0).
    """
    resultados: list[dict] = []
    for i, (L, d) in enumerate(pares_longitud_desplazamiento):
        longitud = float(L)
        desplazamiento = float(d)
        if longitud <= 0:
            pct = 0.0
        else:
            pct = (desplazamiento / longitud) * 100.0
        if pct > 25:
            clasif, ia = "Discontinuidad", 0.80
        else:
            clasif, ia = "Regular", 1.0
        resultados.append({
            "piso": i + 1,
            "L": round(longitud, 2),
            "d": round(desplazamiento, 2),
            "d/L%": round(pct, 2),
            "clasificacion": clasif,
            "Ia": ia,
        })
    return resultados


def verificar_discontinuidad_unificado(pct_por_piso: list[float]) -> list[dict]:
    """
    Verificacion unificada (legacy): pct cortante en elementos discontinuos.
    pct>25% -> Extrema (Ia=0.60); pct>10% -> Discontinuidad (Ia=0.80); else Regular (Ia=1.0).
    """
    resultados: list[dict] = []
    for i, pct in enumerate(pct_por_piso):
        p = float(pct)
        if p > 25:
            clasif, ia = "Extrema", 0.60
        elif p > 10:
            clasif, ia = "Discontinuidad", 0.80
        else:
            clasif, ia = "Regular", 1.0
        resultados.append({"piso": i + 1, "pct": round(p, 2), "clasificacion": clasif, "Ia": ia})
    return resultados


def verificar_discontinuidad_unificado_desalineamiento(
    pares_longitud_desplazamiento: list[tuple[float, float]],
) -> list[dict]:
    """
    Verificacion por desalineamiento vertical (E.030 Tabla 8).
    Input: [(L1,d1), (L2,d2), ...] = (longitud elemento, distancia desalineamiento) por piso.
    Calcula pct=(d/L)*100. pct>25% -> Discontinuidad (Ia=0.80); else Regular (Ia=1.0).
    """
    return verificar_discontinuidad_por_longitud_desplazamiento(pares_longitud_desplazamiento)


def verificar_torsional_todos(pares: list[tuple[float, float]]) -> list[dict]:
    """Verifica torsional por piso. pares: [(da,db), ...] desplazamientos relativos por piso."""
    return [
        {"piso": i + 1, **verificar_torsional(da, db)}
        for i, (da, db) in enumerate(pares)
    ]


def calcular_relativos_desde_absolutos(
    abs_a: list[float], abs_b: list[float],
) -> list[tuple[float, float]]:
    """
    Calcula desplazamientos relativos (story drift) desde absolutos.
    abs_a, abs_b: desplazamientos absolutos en extremos por nivel (nivel 0 = base).
    Retorna [(da1,db1), (da2,db2), ...] donde da_i = abs_a[i] - abs_a[i-1].
    """
    pares = []
    u_a_ant, u_b_ant = 0.0, 0.0
    for i in range(len(abs_a)):
        da = abs_a[i] - u_a_ant
        db = abs_b[i] - u_b_ant
        pares.append((da, db))
        u_a_ant, u_b_ant = abs_a[i], abs_b[i]
    return pares
