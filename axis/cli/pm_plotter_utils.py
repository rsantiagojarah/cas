"""
Filtrado de puntos para la superficie de interacción (ConvexHull).
Misma lógica que Diseño_Columnas/src/utils/pm_plotter_utils.py.
"""

from __future__ import annotations

from typing import List

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


def filter_points(puntos: List[dict], *, remove_outliers: bool = True) -> List[dict]:
    """
    Filtra puntos eliminando duplicados y, opcionalmente, outliers (IQR).
    puntos: lista de dicts con claves "p", "m2", "m3".
    remove_outliers: si False, solo deduplica (recomendado al graficar la envolvente).
    """
    if not puntos or not _NUMPY_AVAILABLE:
        return puntos

    pu = np.array([float(p["p"]) for p in puntos])
    m2 = np.array([float(p["m2"]) for p in puntos])
    m3 = np.array([float(p["m3"]) for p in puntos])

    unique_mask = np.ones(len(puntos), dtype=bool)
    seen = set()
    for i in range(len(puntos)):
        key = (round(pu[i], 6), round(m2[i], 6), round(m3[i], 6))
        if key in seen:
            unique_mask[i] = False
        else:
            seen.add(key)

    filtered_mask = unique_mask.copy()
    if remove_outliers:
        for arr in [pu, m2, m3]:
            if len(arr[filtered_mask]) < 4:
                continue
            q1 = np.percentile(arr[filtered_mask], 25)
            q3 = np.percentile(arr[filtered_mask], 75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 3 * iqr
                upper = q3 + 3 * iqr
                filtered_mask = filtered_mask & (arr >= lower) & (arr <= upper)

    out = [puntos[i] for i in range(len(puntos)) if filtered_mask[i]]
    return out if out else puntos
