"""
Motor genérico para leer tablas desde ETABS mediante su API.

Permite obtener cualquier tabla de Database Tables como DataFrame para
reutilizar en vigas, columnas, análisis sísmico, etc.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from axis.data.etabs_connection import conectar_con_etabs, verificar_etabs_disponible

_table_cache: dict[str, Optional[pd.DataFrame]] = {}


def clear_table_cache() -> None:
    """Limpia la caché de tablas (útil si el modelo ETABS cambia)."""
    _table_cache.clear()


def get_table(
    table_name: str,
    group_name: str = "",
    alternate_names: Optional[list[str]] = None,
    log: bool = True,
    use_cache: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Obtiene una tabla de ETABS como DataFrame. Cachea el resultado para
    evitar lecturas COM repetidas de la misma tabla.

    Args:
        table_name: Nombre de la tabla en ETABS.
        group_name: Nombre del grupo para filtrar (vacío = todas).
        alternate_names: Nombres alternativos a intentar si la tabla principal falla.
        log: Si True, imprime mensajes de éxito o error.
        use_cache: Si True, devuelve copia del cache si ya se leyó la tabla.

    Returns:
        DataFrame con columnas = headers de la tabla, o None si falla.
    """
    cache_key = f"{table_name}|{group_name}"

    if use_cache and cache_key in _table_cache:
        cached = _table_cache[cache_key]
        return cached.copy() if cached is not None else None

    if not verificar_etabs_disponible():
        if log:
            print("⚠ Error: comtypes no está disponible. Instale con: pip install comtypes")
        return None

    try:
        resultado = conectar_con_etabs()
        if resultado is None:
            if log:
                print("⚠ Error: No se pudo establecer conexión con ETABS")
            return None

        SapModel, _etabs_obj, _helper = resultado
        names_to_try = [table_name]
        if alternate_names:
            names_to_try = [table_name] + list(alternate_names)

        table = None
        used_name = None
        last_error = None

        for name in names_to_try:
            try:
                table = SapModel.DatabaseTables.GetTableForDisplayArray(
                    name, GroupName=group_name
                )
                used_name = name
                break
            except Exception as e:
                last_error = e
                continue

        if table is None or used_name is None:
            if log:
                print(f"⚠ Error al obtener tabla '{table_name}': {last_error}")
                print("   Verifique que el modelo tenga los datos y que se haya ejecutado el análisis.")
            _table_cache[cache_key] = None
            return None

        cols = table[2]
        no_of_rows = table[3]

        if no_of_rows == 0:
            if log:
                print(f"⚠ Advertencia: La tabla '{used_name}' está vacía.")
            df = pd.DataFrame(columns=cols)
            _table_cache[cache_key] = df
            return df.copy()

        vals = np.array_split(table[4], no_of_rows)
        df = pd.DataFrame(vals)
        df.columns = cols

        if log:
            print(f"✓ Se obtuvieron {no_of_rows} filas de '{used_name}'")

        _table_cache[cache_key] = df
        return df.copy()

    except Exception as e:
        if log:
            print(f"⚠ Error inesperado al leer tabla '{table_name}': {e}")
            import traceback
            traceback.print_exc()
        return None
