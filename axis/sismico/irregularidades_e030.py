"""
Reglas de irregularidades E.030 (Tablas N° 8 y N° 9).
Permite calcular Ia e Ip de forma rápida para CLI.
"""

from __future__ import annotations

from typing import Iterable


ALTURA_FACTORES: dict[str, dict[str, object]] = {
    "rb": {"nombre": "Irregularidad de rigidez - piso blando", "factor": 0.75},
    "resb": {"nombre": "Irregularidad de resistencia - piso debil", "factor": 0.75},
    "reb": {"nombre": "Irregularidad extrema de rigidez", "factor": 0.50},
    "rese": {"nombre": "Irregularidad extrema de resistencia", "factor": 0.50},
    "masa": {"nombre": "Irregularidad de masa o peso", "factor": 0.90},
    "geomv": {"nombre": "Irregularidad geometrica vertical", "factor": 0.90},
    "disc": {"nombre": "Discontinuidad en sistemas resistentes", "factor": 0.80},
    "disce": {"nombre": "Discontinuidad extrema en sistemas resistentes", "factor": 0.60},
}

PLANTA_FACTORES: dict[str, dict[str, object]] = {
    "tors": {"nombre": "Irregularidad torsional", "factor": 0.75},
    "torse": {"nombre": "Irregularidad torsional extrema", "factor": 0.60},
    "esq": {"nombre": "Esquinas entrantes", "factor": 0.90},
    "diaf": {"nombre": "Discontinuidad del diafragma", "factor": 0.85},
    "np": {"nombre": "Sistemas no paralelos", "factor": 0.90},
}

_TOKEN_VACIO = {"", "-", "0", "ninguna", "ninguno", "na", "n/a"}


def _normalizar_codigos(raw: str | Iterable[str]) -> list[str]:
    if isinstance(raw, str):
        tokens = [p.strip().lower() for p in raw.split(",")]
    else:
        tokens = [str(p).strip().lower() for p in raw]
    return [t for t in tokens if t and t not in _TOKEN_VACIO]


def _resolver_factor(
    codigos: list[str],
    catalogo: dict[str, dict[str, object]],
    nombre_factor: str,
) -> dict[str, object]:
    if not codigos:
        return {"factor": 1.0, "codigos": [], "detalles": []}
    invalidos = [c for c in codigos if c not in catalogo]
    if invalidos:
        validos = ", ".join(catalogo.keys())
        raise ValueError(f"{nombre_factor}: codigos invalidos {invalidos}. Use: {validos}")
    detalles = [
        {
            "codigo": c,
            "nombre": str(catalogo[c]["nombre"]),
            "factor": float(catalogo[c]["factor"]),
        }
        for c in codigos
    ]
    valor = min(float(d["factor"]) for d in detalles)
    return {"factor": valor, "codigos": codigos, "detalles": detalles}


def calcular_factores_irregularidad(
    altura: str | Iterable[str],
    planta: str | Iterable[str],
) -> dict[str, object]:
    """
    Calcula Ia e Ip con base en códigos de irregularidad.
    Regla: se toma el valor más desfavorable (mínimo) de los códigos elegidos.
    """
    cod_alt = _normalizar_codigos(altura)
    cod_pla = _normalizar_codigos(planta)
    ia = _resolver_factor(cod_alt, ALTURA_FACTORES, "Ia")
    ip = _resolver_factor(cod_pla, PLANTA_FACTORES, "Ip")
    return {
        "ia": ia["factor"],
        "ip": ip["factor"],
        "altura": ia,
        "planta": ip,
    }


def tabla_codigos_altura() -> list[dict[str, object]]:
    """Tabla CLI para mostrar códigos de irregularidades en altura."""
    return [
        {"Codigo": codigo, "Irregularidad en altura": meta["nombre"], "Ia": meta["factor"]}
        for codigo, meta in ALTURA_FACTORES.items()
    ]


def tabla_codigos_planta() -> list[dict[str, object]]:
    """Tabla CLI para mostrar códigos de irregularidades en planta."""
    return [
        {"Codigo": codigo, "Irregularidad en planta": meta["nombre"], "Ip": meta["factor"]}
        for codigo, meta in PLANTA_FACTORES.items()
    ]
