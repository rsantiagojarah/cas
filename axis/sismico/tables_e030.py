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

# Paso 2: Perfiles de suelo S0-S4 (clave en minúsculas).
# Paso 3: S (factor suelo), Tp (s), Tl (s). S4 requiere estudio específico.
PARAMETROS_SUELO: dict[str, dict[str, Optional[float]]] = {
    "s0": {"s": 0.80, "tp": 0.30, "tl": 3.0},
    "s1": {"s": 1.00, "tp": 0.40, "tl": 2.5},
    "s2": {"s": 1.20, "tp": 0.60, "tl": 2.0},
    "s3": {"s": 1.40, "tp": 0.90, "tl": 1.6},
    "s4": {"s": None, "tp": None, "tl": None},  # Según estudio específico
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


def obtener_parametros_sitio(perfil: str) -> dict[str, Optional[float]]:
    """Retorna S, Tp, Tl para perfil s0, s1, s2, s3 o s4."""
    clave = perfil.strip().lower()
    if clave not in PARAMETROS_SUELO:
        raise ValueError(
            f"Perfil debe ser s0, s1, s2, s3 o s4. Recibido: {perfil}"
        )
    return PARAMETROS_SUELO[clave].copy()


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
    if material not in DISTORSION_MAXIMA:
        raise ValueError(
            f"Material debe ser uno de {list(DISTORSION_MAXIMA)}. Recibido: {material}"
        )
    return DISTORSION_MAXIMA[material]
