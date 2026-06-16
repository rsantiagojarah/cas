"""
Tablas Norma E.030 – Diseño Sismorresistente (actualización 2026 disponible en repo).
Constantes para zona, suelo, uso, R0 y distorsión máxima.
"""

from __future__ import annotations

from typing import Any, Optional

# Paso 1: Factor de Zona (Z). Clave = número de zona (1-4).
FACTOR_ZONA: dict[int, float] = {
    4: 0.45,
    3: 0.35,
    2: 0.25,
    1: 0.10,
}

# Tabla 4 – Factor de suelo S. En S2/S3 se almacena el mayor valor del intervalo,
# que es el valor normativo por defecto cuando no se dispone de Vs30.
FACTOR_SUELO_S: dict[int, dict[str, Optional[float]]] = {
    4: {"s0": 0.80, "s1": 1.00, "s2": 1.10, "s3": 1.20, "s4": None},
    3: {"s0": 0.80, "s1": 1.00, "s2": 1.15, "s3": 1.20, "s4": 1.30},
    2: {"s0": 0.80, "s1": 1.00, "s2": 1.30, "s3": 1.40, "s4": 1.70},
    1: {"s0": 0.80, "s1": 1.00, "s2": 1.30, "s3": 1.60, "s4": 2.40},
}

# Tabla 5 – Períodos Tp (s) y Tl (s) por perfil.
PERIODOS_TP_TL: dict[str, dict[str, Optional[float]]] = {
    "s0": {"tp": 0.30, "tl": 3.0},
    "s1": {"tp": 0.40, "tl": 2.5},
    "s2": {"tp": None, "tl": None},
    "s3": {"tp": None, "tl": None},
    "s4": {"tp": 1.20, "tl": 1.6},
    "s5": {"tp": None, "tl": None},
}

# Paso 5: Factor de uso U.
FACTOR_USO: dict[str, float] = {
    "A": 1.50,
    "B": 1.30,
    "C": 1.00,
}

# Paso 6: Factor de reducción R0 por sistema estructural.
FACTOR_R0: dict[str, float] = {
    "acero_smf": 8.0,
    "acero_imf": 5.0,
    "acero_omf": 4.0,
    "acero_scbf": 7.0,
    "acero_ocbf": 4.0,
    "acero_ebf": 8.0,
    "portico_concreto": 8.0,
    "dual": 7.0,
    "muros_estructurales": 6.0,
    "emdl": 3.5,
    "albanileria_confinada": 3.0,
    "madera": 7.0,
}

TABLA_ZONA = [
    {"Zona Sismica": "Zona 4", "Factor de Zona (Z)": 0.45},
    {"Zona Sismica": "Zona 3", "Factor de Zona (Z)": 0.35},
    {"Zona Sismica": "Zona 2", "Factor de Zona (Z)": 0.25},
    {"Zona Sismica": "Zona 1", "Factor de Zona (Z)": 0.10},
]

TABLA_PERFIL_DESC = [
    {"Perfil": "S0", "Descripcion": "Roca", "Vs (m/s)": ">= 800", "N60": "-", "Su (kPa)": "-"},
    {"Perfil": "S1", "Descripcion": "Suelos muy rigidos", "Vs (m/s)": "550 a <800", "N60": "> 50", "Su (kPa)": "-"},
    {"Perfil": "S2", "Descripcion": "Suelos rigidos", "Vs (m/s)": "350 a <550", "N60": "30 a 50", "Su (kPa)": "> 100"},
    {"Perfil": "S3", "Descripcion": "Suelos intermedios", "Vs (m/s)": "200 a <350", "N60": "15 a 30", "Su (kPa)": "50 a 100"},
    {"Perfil": "S4", "Descripcion": "Suelos blandos", "Vs (m/s)": "< 200", "N60": "< 15", "Su (kPa)": "< 50"},
    {"Perfil": "S5", "Descripcion": "Suelos excepcionales", "Vs (m/s)": "Especial", "N60": "Especial", "Su (kPa)": "Especial"},
]

TABLA_FACTOR_SUELO_S = [
    {"Zona / Suelo": "Z4", "S0": 0.80, "S1": 1.00, "S2": "1.00-1.10*", "S3": "1.10-1.20*", "S4": "Resp. sitio"},
    {"Zona / Suelo": "Z3", "S0": 0.80, "S1": 1.00, "S2": "1.00-1.15*", "S3": "1.15-1.20*", "S4": 1.30},
    {"Zona / Suelo": "Z2", "S0": 0.80, "S1": 1.00, "S2": "1.00-1.30*", "S3": "1.30-1.40*", "S4": 1.70},
    {"Zona / Suelo": "Z1", "S0": 0.80, "S1": 1.00, "S2": "1.00-1.30*", "S3": "1.30-1.60*", "S4": 2.40},
]

TABLA_PERIODOS_TP_TL = [
    {"Perfil de suelo": "S0", "Tp (s)": 0.30, "Tl (s)": 3.0},
    {"Perfil de suelo": "S1", "Tp (s)": 0.40, "Tl (s)": 2.5},
    {"Perfil de suelo": "S2", "Tp (s)": "0.40-0.60*", "Tl (s)": "2.5-2.0*"},
    {"Perfil de suelo": "S3", "Tp (s)": "0.60-0.90*", "Tl (s)": "2.0-1.6*"},
    {"Perfil de suelo": "S4", "Tp (s)": 1.20, "Tl (s)": 1.6},
    {"Perfil de suelo": "S5", "Tp (s)": "Especial", "Tl (s)": "Especial"},
]

TABLA_PERFIL_STPTL = [
    {"Perfil": "S0", "Factor de Suelo (S)": "por zona", "Tp (s)": 0.30, "Tl (s)": 3.0},
    {"Perfil": "S1", "Factor de Suelo (S)": "por zona", "Tp (s)": 0.40, "Tl (s)": 2.5},
    {"Perfil": "S2", "Factor de Suelo (S)": "intervalo por zona*", "Tp (s)": "0.40-0.60*", "Tl (s)": "2.5-2.0*"},
    {"Perfil": "S3", "Factor de Suelo (S)": "intervalo por zona*", "Tp (s)": "0.60-0.90*", "Tl (s)": "2.0-1.6*"},
    {"Perfil": "S4", "Factor de Suelo (S)": "por zona / estudio", "Tp (s)": 1.20, "Tl (s)": 1.6},
    {"Perfil": "S5", "Factor de Suelo (S)": "Estudio especial", "Tp (s)": "-", "Tl (s)": "-"},
]

TABLA_CATEGORIA = [
    {"Categoria": "A", "Tipo de Edificacion": "Edificaciones esenciales", "U": 1.50},
    {"Categoria": "B", "Tipo de Edificacion": "Edificaciones importantes", "U": 1.30},
    {"Categoria": "C", "Tipo de Edificacion": "Edificaciones comunes", "U": 1.00},
    {"Categoria": "D", "Tipo de Edificacion": "Edificaciones temporales", "U": "Pendiente"},
]

TABLA_SISTEMA = [
    {"Sistema Estructural": "Acero SMF", "R0": 8},
    {"Sistema Estructural": "Acero IMF", "R0": 5},
    {"Sistema Estructural": "Acero OMF", "R0": 4},
    {"Sistema Estructural": "Acero SCBF", "R0": 7},
    {"Sistema Estructural": "Acero OCBF", "R0": 4},
    {"Sistema Estructural": "Acero EBF", "R0": 8},
    {"Sistema Estructural": "Porticos de Concreto Armado", "R0": 8},
    {"Sistema Estructural": "Sistema Dual", "R0": 7},
    {"Sistema Estructural": "Muros Estructurales", "R0": 6},
    {"Sistema Estructural": "Muros de Ductilidad Limitada", "R0": 3.5},
    {"Sistema Estructural": "Albanileria armada o confinada", "R0": 3},
    {"Sistema Estructural": "Madera", "R0": 7},
]

TABLA_CLASIFICACION = [
    {"Sistema": "Portico", "% Cortante Muros": "< 20%", "% Cortante Porticos": ">= 80%"},
    {"Sistema": "Dual", "% Cortante Muros": "> 20% y < 70%", "% Cortante Porticos": "Complementario"},
    {"Sistema": "Muros estructurales", "% Cortante Muros": ">= 70%", "% Cortante Porticos": "<= 30%"},
]

TABLA_MATERIAL_DISTORSION = [
    {"Material": "Concreto Armado", "Distorsion Max (d/h)": 0.007},
    {"Material": "Acero", "Distorsion Max (d/h)": 0.010},
    {"Material": "Albanileria", "Distorsion Max (d/h)": 0.005},
    {"Material": "Madera", "Distorsion Max (d/h)": 0.010},
    {"Material": "Concreto Armado con Muros de Ductilidad Limitada", "Distorsion Max (d/h)": 0.004},
]

DISTORSION_MAXIMA: dict[str, float] = {
    "concreto_armado": 0.007,
    "acero": 0.010,
    "albanileria": 0.005,
    "madera": 0.010,
    "concreto_ductilidad_limitada": 0.004,
    "emdl": 0.004,
}


def obtener_z(zona: int) -> float:
    """Retorna el factor de zona Z para zona 1, 2, 3 o 4."""
    if zona not in FACTOR_ZONA:
        raise ValueError(f"Zona debe ser 1, 2, 3 o 4. Recibido: {zona}")
    return FACTOR_ZONA[zona]


def _interpolar(valor: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if valor <= min(x0, x1):
        return y0 if x0 <= x1 else y1
    if valor >= max(x0, x1):
        return y1 if x0 <= x1 else y0
    return y0 + (valor - x0) * (y1 - y0) / (x1 - x0)


def _obtener_parametros_interpolados(
    perfil: str,
    zona: int,
    vs: Optional[float],
) -> tuple[Optional[float], Optional[float], Optional[float], list[str]]:
    advertencias: list[str] = []
    if perfil == "s2":
        if vs is None:
            advertencias.append("Perfil S2 sin Vs30: se adopta S mayor del intervalo, Tp=0.60 y Tl=2.00.")
            return FACTOR_SUELO_S[zona]["s2"], 0.60, 2.00, advertencias
        s_val = _interpolar(vs, 550.0, 350.0, 1.00, float(FACTOR_SUELO_S[zona]["s2"]))
        tp = _interpolar(vs, 550.0, 350.0, 0.40, 0.60)
        tl = _interpolar(vs, 550.0, 350.0, 2.50, 2.00)
        return s_val, tp, tl, advertencias
    if perfil == "s3":
        if vs is None:
            advertencias.append("Perfil S3 sin Vs30: se adopta S mayor del intervalo, Tp=0.90 y Tl=1.60.")
            return FACTOR_SUELO_S[zona]["s3"], 0.90, 1.60, advertencias
        s_bajo = 1.10 if zona == 4 else float(FACTOR_SUELO_S[zona]["s2"])
        s_val = _interpolar(vs, 350.0, 200.0, s_bajo, float(FACTOR_SUELO_S[zona]["s3"]))
        tp = _interpolar(vs, 350.0, 200.0, 0.60, 0.90)
        tl = _interpolar(vs, 350.0, 200.0, 2.00, 1.60)
        return s_val, tp, tl, advertencias
    valores = PERIODOS_TP_TL[perfil]
    return FACTOR_SUELO_S[zona].get(perfil), valores["tp"], valores["tl"], advertencias


def obtener_parametros_sitio(
    perfil: str,
    zona: int,
    vs: Optional[float] = None,
) -> dict[str, Any]:
    """
    Retorna S, Tp, Tl y metadatos normativos.
    - S5 requiere estudio especial.
    - Z4 + S4 requiere análisis de respuesta de sitio.
    - S2 y S3 interpolan S, Tp y Tl si se dispone de Vs30.
    """
    clave = perfil.strip().lower()
    if clave not in PERIODOS_TP_TL:
        raise ValueError(f"Perfil debe ser s0, s1, s2, s3, s4 o s5. Recibido: {perfil}")
    if zona not in FACTOR_SUELO_S:
        raise ValueError(f"Zona debe ser 1, 2, 3 o 4. Recibido: {zona}")

    advertencias: list[str] = []
    requiere_estudio = False
    estado = "ok"

    if clave == "s5":
        requiere_estudio = True
        estado = "requiere_estudio_especial"
        advertencias.append("Perfil S5 requiere tratamiento especial; no se puede cerrar el cálculo con la información actual.")
        return {"s": None, "tp": None, "tl": None, "advertencias": advertencias, "requiere_estudio": True, "estado": estado}

    s_val, tp, tl, advert_interp = _obtener_parametros_interpolados(clave, zona, vs)
    advertencias.extend(advert_interp)

    if clave == "s4" and zona == 4:
        requiere_estudio = True
        estado = "requiere_respuesta_sitio"
        advertencias.append("Zona 4 + perfil S4 requiere análisis de respuesta de sitio; no se asigna S automáticamente.")
        s_val = None

    return {
        "s": s_val,
        "tp": tp,
        "tl": tl,
        "advertencias": advertencias,
        "requiere_estudio": requiere_estudio,
        "estado": estado,
    }


def obtener_u(categoria: str) -> float:
    """Retorna el factor de uso U para categoría A, B o C. D queda pendiente de verificación."""
    letra = categoria.strip().upper()
    if letra == "D":
        raise ValueError("Categoría D: valor normativo no verificable en la fuente disponible.")
    if letra not in FACTOR_USO:
        raise ValueError(f"Categoría debe ser A, B, C o D. Recibido: {categoria}")
    return FACTOR_USO[letra]


def obtener_r0(sistema: str) -> float:
    """Retorna R0 para el sistema estructural indicado."""
    clave = sistema.strip().lower()
    if clave not in FACTOR_R0:
        raise ValueError(f"Sistema debe ser uno de {list(FACTOR_R0)}. Recibido: {sistema}")
    return FACTOR_R0[clave]


def obtener_distorsion_maxima(material: str) -> float:
    """Retorna distorsión máxima (Δ/h) según material predominante."""
    clave = material.strip().lower()
    if clave == "albañileria":
        clave = "albanileria"
    if clave not in DISTORSION_MAXIMA:
        raise ValueError(f"Material debe ser uno de {list(DISTORSION_MAXIMA)}. Recibido: {material}")
    return DISTORSION_MAXIMA[clave]
