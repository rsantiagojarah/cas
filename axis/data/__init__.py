"""
Fuentes de datos externas (ETABS, etc.) para uso en operaciones y análisis.
"""

from __future__ import annotations

from axis.data.etabs_connection import (
    conectar_con_etabs,
    verificar_etabs_disponible,
    ETABS_AVAILABLE,
)
from axis.data.etabs_table_reader import get_table

__all__ = [
    "conectar_con_etabs",
    "verificar_etabs_disponible",
    "ETABS_AVAILABLE",
    "get_table",
]
