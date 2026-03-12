"""
Parser para diagramas de interacción desde Excel exportados desde SAP2000.
Formato: Fila 0 curvas (Curve 1, 0. degrees...), Fila 1 P/M2/M3, Fila 2+ datos.
Salida: lista de dicts {"p", "m2", "m3", "angle"} compatible con diagramas.json.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


def import_from_excel(file_path: Path) -> list[dict[str, Any]]:
    """
    Importa puntos del diagrama desde un Excel en formato SAP2000/Diseño_Columnas.

    Returns:
        Lista de dicts con claves "p", "m2", "m3", "angle" (Tn, Tn-m, grados).
    """
    if not _PANDAS_AVAILABLE:
        raise ValueError("Se requiere pandas para leer Excel. Instale: pip install pandas openpyxl")
    try:
        df = pd.read_excel(file_path, header=None)
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo Excel: {e}") from e
    if df.empty:
        raise ValueError("El archivo Excel está vacío")
    curves = _extract_curves_from_headers(df)
    if not curves:
        raise ValueError("No se encontraron curvas en el archivo Excel (formato SAP2000 esperado).")
    points: list[dict[str, Any]] = []
    for curve_info in curves:
        angle = curve_info["angle"]
        col_p = curve_info["col_p"]
        col_m2 = curve_info["col_m2"]
        col_m3 = curve_info["col_m3"]
        for idx in range(2, len(df)):
            try:
                p_val = df.iloc[idx, col_p]
                m2_val = df.iloc[idx, col_m2]
                m3_val = df.iloc[idx, col_m3]
                if pd.isna(p_val) or pd.isna(m2_val) or pd.isna(m3_val):
                    continue
                points.append({
                    "p": float(p_val),
                    "m2": float(m2_val),
                    "m3": float(m3_val),
                    "angle": angle,
                })
            except (ValueError, IndexError):
                continue
    return points


def _extract_curves_from_headers(df: "pd.DataFrame") -> list[dict[str, Any]]:
    curves: list[dict[str, Any]] = []
    if len(df) < 2:
        return curves
    fila_encabezados = df.iloc[0]
    fila_datos = df.iloc[1]
    i = 0
    while i < len(fila_encabezados):
        if pd.isna(fila_encabezados.iloc[i]):
            i += 1
            continue
        texto_curva = str(fila_encabezados.iloc[i]).strip()
        if not texto_curva.startswith("Curve"):
            i += 1
            continue
        if i + 2 >= len(fila_encabezados):
            break
        texto_angulo = str(fila_encabezados.iloc[i + 1]).strip()
        angulo = _extract_angle(texto_angulo)
        if angulo is None:
            i += 1
            continue
        col_p, col_m2, col_m3 = i, i + 1, i + 2
        if col_m3 >= len(fila_datos):
            break
        texto_p = str(fila_datos.iloc[col_p]).strip().upper()
        texto_m2 = str(fila_datos.iloc[col_m2]).strip().upper()
        texto_m3 = str(fila_datos.iloc[col_m3]).strip().upper()
        ok_p = texto_p == "P" or (texto_p.startswith("P") and ("TONF" in texto_p or "TON" in texto_p))
        ok_m2 = texto_m2 == "M2" or (texto_m2.startswith("M2") and ("TONF" in texto_m2 or "TON" in texto_m2))
        ok_m3 = texto_m3 == "M3" or (texto_m3.startswith("M3") and ("TONF" in texto_m3 or "TON" in texto_m3))
        if ok_p and ok_m2 and ok_m3:
            curves.append({"angle": angulo, "col_p": col_p, "col_m2": col_m2, "col_m3": col_m3})
        i += 1
        while i < len(fila_encabezados) and pd.isna(fila_encabezados.iloc[i]):
            i += 1
    return curves


def _extract_angle(header: str) -> float | None:
    m = re.search(r"([\d.]+)\s*\.?\s*degrees?", header, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m = re.search(r"([\d.]+)\s*deg(?!rees)", header, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None
