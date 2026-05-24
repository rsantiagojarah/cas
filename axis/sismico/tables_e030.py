"""
Tablas Norma E.030 – Diseño Sismorresistente (RNE).
Constantes para zona, suelo, uso, R0 y distorsión máxima.
"""

from __future__ import annotations

from typing import Optional

# Paso 1: Factor de Zona (Z). Clave = número de zona (1-4).
FACTOR_ZONA: dict[int, float] = {
    4: 0.45,
    3: 0.35,
    2: 0.25,
    1: 0.10,
}

# Paso 2: Perfiles de suelo S0–S4 (Tabla N° 2 E.030). Clave en minúsculas.
# Paso 3: Factor S por zona y perfil (Tabla N° 3); Tp y Tl por perfil (Tabla N° 4). S4 = estudio específico.

# Tabla N° 3 – Factor de Suelo S: S[zona][perfil]. Zona 1–4, perfil s0–s3.
FACTOR_SUELO_S: dict[int, dict[str, float]] = {
    4: {"s0": 0.80, "s1": 1.00, "s2": 1.05, "s3": 1.10},
    3: {"s0": 0.80, "s1": 1.00, "s2": 1.15, "s3": 1.20},
    2: {"s0": 0.80, "s1": 1.00, "s2": 1.20, "s3": 1.40},
    1: {"s0": 0.80, "s1": 1.00, "s2": 1.60, "s3": 2.00},
}

# Tabla N° 4 – Períodos Tp (s) y Tl (s) por perfil.
PERIODOS_TP_TL: dict[str, dict[str, Optional[float]]] = {
    "s0": {"tp": 0.30, "tl": 3.0},
    "s1": {"tp": 0.40, "tl": 2.5},
    "s2": {"tp": 0.60, "tl": 2.0},
    "s3": {"tp": 1.00, "tl": 1.6},
    "s4": {"tp": None, "tl": None},
}

# Paso 5: Factor de uso U. Categorías A, B, C, D.
FACTOR_USO: dict[str, float] = {
    "A": 1.50,
    "B": 1.30,
    "C": 1.00,
    "D": 0.80,
}

# Paso 6: Factor de reducción R0 por sistema estructural.
FACTOR_R0: dict[str, float] = {
    "portico_concreto": 8.0,
    "muros_estructurales": 6.0,
    "dual": 7.0,
    "albañileria_confinada": 3.0,
}

# Tablas para salida (list[dict] para format_table).
TABLA_ZONA = [
    {"Zona Sismica": "Zona 4", "Factor de Zona (Z)": 0.45},
    {"Zona Sismica": "Zona 3", "Factor de Zona (Z)": 0.35},
    {"Zona Sismica": "Zona 2", "Factor de Zona (Z)": 0.25},
    {"Zona Sismica": "Zona 1", "Factor de Zona (Z)": 0.10},
]
# Tabla N° 2 – Clasificación de perfiles de suelo (Vs, N60, Su).
TABLA_PERFIL_DESC = [
    {"Perfil": "S0", "Descripcion": "Roca muy dura", "Vs (m/s)": "> 1500", "N60": "-", "Su (kPa)": "-"},
    {"Perfil": "S1", "Descripcion": "Roca o suelo muy rigido", "Vs (m/s)": "500 a 1500", "N60": "> 50", "Su (kPa)": "> 100"},
    {"Perfil": "S2", "Descripcion": "Suelos intermedios (densos)", "Vs (m/s)": "180 a 500", "N60": "15 a 50", "Su (kPa)": "50 a 100"},
    {"Perfil": "S3", "Descripcion": "Suelos blandos", "Vs (m/s)": "< 180", "N60": "< 15", "Su (kPa)": "25 a 50"},
    {"Perfil": "S4", "Descripcion": "Suelos muy blandos / especiales", "Vs (m/s)": "Clasificacion basada en el EMS", "N60": "-", "Su (kPa)": "-"},
]
# Tabla N° 3 – Factor de Suelo S (Zona × Perfil).
TABLA_FACTOR_SUELO_S = [
    {"Zona / Suelo": "Z4", "S0": 0.80, "S1": 1.00, "S2": 1.05, "S3": 1.10},
    {"Zona / Suelo": "Z3", "S0": 0.80, "S1": 1.00, "S2": 1.15, "S3": 1.20},
    {"Zona / Suelo": "Z2", "S0": 0.80, "S1": 1.00, "S2": 1.20, "S3": 1.40},
    {"Zona / Suelo": "Z1", "S0": 0.80, "S1": 1.00, "S2": 1.60, "S3": 2.00},
]
# Tabla N° 4 – Períodos Tp y Tl (s) por perfil.
TABLA_PERIODOS_TP_TL = [
    {"Perfil de suelo": "S0", "Tp (s)": 0.30, "Tl (s)": 3.0},
    {"Perfil de suelo": "S1", "Tp (s)": 0.40, "Tl (s)": 2.5},
    {"Perfil de suelo": "S2", "Tp (s)": 0.60, "Tl (s)": 2.0},
    {"Perfil de suelo": "S3", "Tp (s)": 1.00, "Tl (s)": 1.6},
    {"Perfil de suelo": "S4", "Tp (s)": "Est. especifico", "Tl (s)": "-"},
]
# Compatibilidad: tabla única Perfil | S | Tp | Tl (S y Tp/Tl según zona y perfil; para listados genéricos).
TABLA_PERFIL_STPTL = [
    {"Perfil": "S0", "Factor de Suelo (S)": "por zona (Tabla 3)", "Tp (s)": 0.30, "Tl (s)": 3.0},
    {"Perfil": "S1", "Factor de Suelo (S)": "por zona (Tabla 3)", "Tp (s)": 0.40, "Tl (s)": 2.5},
    {"Perfil": "S2", "Factor de Suelo (S)": "por zona (Tabla 3)", "Tp (s)": 0.60, "Tl (s)": 2.0},
    {"Perfil": "S3", "Factor de Suelo (S)": "por zona (Tabla 3)", "Tp (s)": 1.00, "Tl (s)": 1.6},
    {"Perfil": "S4", "Factor de Suelo (S)": "Est. especifico", "Tp (s)": "-", "Tl (s)": "-"},
]
TABLA_CATEGORIA = [
    {
        "Categoria": "A",
        "Tipo de Edificacion": "Edificaciones esenciales (salud, emergencias,\ngobierno, refugio post-desastre)",
        "U": 1.50,
    },
    {
        "Categoria": "B",
        "Tipo de Edificacion": "Edificaciones importantes (gran concentracion de personas\no patrimonios valiosos)",
        "U": 1.30,
    },
    {
        "Categoria": "C",
        "Tipo de Edificacion": "Edificaciones comunes (vivienda, oficinas, hoteles,\nindustria sin riesgo adicional)",
        "U": 1.00,
    },
    {
        "Categoria": "D",
        "Tipo de Edificacion": "Edificaciones temporales (depósitos,\ncasetas y similares)",
        "U": 0.80,
    },
]
TABLA_SISTEMA = [
    {"Sistema Estructural": "Porticos de Concreto Armado", "R0": 8},
    {"Sistema Estructural": "Muros Estructurales de Concreto Armado", "R0": 6},
    {"Sistema Estructural": "Sistema Dual (Porticos + Muros)", "R0": 7},
    {"Sistema Estructural": "Albañileria Confinada", "R0": 3},
]
TABLA_CLASIFICACION = [
    {"Sistema": "Portico", "% Cortante Muros": "< 20%", "% Cortante Porticos": ">= 80%"},
    {"Sistema": "Dual", "% Cortante Muros": "> 20% y < 70%", "% Cortante Porticos": "Complementario"},
    {"Sistema": "Muros estructurales", "% Cortante Muros": ">= 70%", "% Cortante Porticos": "<= 30%"},
]
TABLA_MATERIAL_DISTORSION = [
    {"Material": "Concreto Armado", "Distorsion Max (d/h)": 0.007},
    {"Material": "Acero", "Distorsion Max (d/h)": 0.010},
    {"Material": "Albañileria", "Distorsion Max (d/h)": 0.005},
    {"Material": "Madera", "Distorsion Max (d/h)": 0.010},
    {
        "Material": "Concreto Armado con\nMuros de Ductilidad Limitada",
        "Distorsion Max (d/h)": 0.005,
    },
]

# Paso 14: Distorsión máxima admisible (Δ/h) por material.
DISTORSION_MAXIMA: dict[str, float] = {
    "concreto_armado": 0.007,
    "acero": 0.010,
    "albañileria": 0.005,
    "madera": 0.010,
    "concreto_ductilidad_limitada": 0.005,
}


def obtener_z(zona: int) -> float:
    """Retorna el factor de zona Z para zona 1, 2, 3 o 4."""
    if zona not in FACTOR_ZONA:
        raise ValueError(f"Zona debe ser 1, 2, 3 o 4. Recibido: {zona}")
    return FACTOR_ZONA[zona]


def obtener_parametros_sitio(perfil: str, zona: int) -> dict[str, Optional[float]]:
    """
    Retorna S, Tp, Tl según E.030: S de Tabla N° 3 (zona + perfil), Tp y Tl de Tabla N° 4 (perfil).
    Para perfil s4 retorna s, tp, tl = None (estudio específico).
    """
    clave = perfil.strip().lower()
    if clave not in PERIODOS_TP_TL:
        raise ValueError(
            f"Perfil debe ser s0, s1, s2, s3 o s4. Recibido: {perfil}"
        )
    if zona not in FACTOR_SUELO_S:
        raise ValueError(f"Zona debe ser 1, 2, 3 o 4. Recibido: {zona}")
    ptl = PERIODOS_TP_TL[clave]
    tp, tl = ptl["tp"], ptl["tl"]
    if clave == "s4":
        return {"s": None, "tp": None, "tl": None}
    s_val = FACTOR_SUELO_S[zona].get(clave)
    if s_val is None:
        return {"s": None, "tp": tp, "tl": tl}
    return {"s": s_val, "tp": tp, "tl": tl}


def obtener_u(categoria: str) -> float:
    """Retorna el factor de uso U para categoría A, B, C o D."""
    letra = categoria.strip().upper()
    if letra not in FACTOR_USO:
        raise ValueError(f"Categoría debe ser A, B, C o D. Recibido: {categoria}")
    return FACTOR_USO[letra]


def obtener_r0(sistema: str) -> float:
    """Retorna R0 para sistema: portico_concreto, muros_estructurales, dual, albañileria_confinada."""
    if sistema not in FACTOR_R0:
        raise ValueError(
            f"Sistema debe ser uno de {list(FACTOR_R0)}. Recibido: {sistema}"
        )
    return FACTOR_R0[sistema]


def obtener_distorsion_maxima(material: str) -> float:
    """Retorna distorsión máxima (Δ/h) según material predominante."""
    clave = material.strip().lower()
    if clave == "albanileria":
        clave = "albañileria"
    if clave not in DISTORSION_MAXIMA:
        raise ValueError(
            f"Material debe ser uno de {list(DISTORSION_MAXIMA)}. Recibido: {material}"
        )
    return DISTORSION_MAXIMA[clave]
