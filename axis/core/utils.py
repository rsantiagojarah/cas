"""
Utilidades compartidas: conversión de tipos y validaciones.
Principio DRY: un solo lugar para to_float y validaciones comunes.
"""

from __future__ import annotations

from typing import Optional

from axis.core.exceptions import InvalidInput


def to_float(val: Optional[str | int | float], default: Optional[float] = None) -> float:
    """
    Convierte a float; acepta coma como decimal. Si default no es None, usa default cuando vacío.
    Lanza InvalidInput si val es None y default es None, o si la conversión falla.
    """
    if val is None or val == "":
        if default is not None:
            return default
        raise InvalidInput("Parámetro faltante")
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip().replace(",", "."))
    except ValueError as e:
        raise InvalidInput(f"Valor no numérico: {val}") from e


def validar_positivo(val: float, nombre: str = "valor") -> None:
    """Lanza InvalidInput si val <= 0."""
    if val <= 0:
        raise InvalidInput(f"{nombre} debe ser positivo")
