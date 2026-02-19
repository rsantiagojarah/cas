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


def get_table(
    table_name: str,
    group_name: str = "",
    alternate_names: Optional[list[str]] = None,
    log: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Obtiene una tabla de ETABS como DataFrame.

    Args:
        table_name: Nombre de la tabla en ETABS (ej. "Element Forces - Columns",
            "Story Forces", "Story Definitions", "Story Drifts").
        group_name: Nombre del grupo para filtrar (vacío = todas).
        alternate_names: Nombres alternativos a intentar si la tabla principal falla.
        log: Si True, imprime mensajes de éxito o error.

    Returns:
        DataFrame con columnas = headers de la tabla, o None si falla.
    """
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
            return None

        cols = table[2]
        no_of_rows = table[3]

        if no_of_rows == 0:
            if log:
                print(f"⚠ Advertencia: La tabla '{used_name}' está vacía.")
            return pd.DataFrame(columns=cols)

        vals = np.array_split(table[4], no_of_rows)
        df = pd.DataFrame(vals)
        df.columns = cols

        if log:
            print(f"✓ Se obtuvieron {no_of_rows} filas de '{used_name}'")
        return df

    except Exception as e:
        if log:
            print(f"⚠ Error inesperado al leer tabla '{table_name}': {e}")
            import traceback
            traceback.print_exc()
        return None
