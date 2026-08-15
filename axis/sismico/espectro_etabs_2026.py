"""Espectro de diseño E.030 2026 para importación en ETABS (Periodo, Sa/g)."""

from __future__ import annotations

from axis.sismico.etapa1_peligro_2026 import factor_amplificacion_c, periodos_espectro_con_limites

PERIODOS_ETABS: tuple[float, ...] = (
    0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    1.0, 1.2, 1.5, 1.7, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 8.0, 11.0, 15.0,
)


def generar_filas_sa(
    z: float,
    u: float,
    s: float,
    tp: float,
    tl: float,
    r: float,
    periodos: tuple[float, ...] | list[float] | None = None,
) -> list[dict[str, float]]:
    """
    Genera filas Periodo / Sa/g con Sa = Z * U * S * C(T) / R.
    C según Tabla 6 E.030 2026 (análisis dinámico modal espectral).
    """
    if r <= 0:
        raise ValueError("R debe ser mayor que 0.")
    if tp <= 0 or tl <= 0:
        raise ValueError("Tp y Tl deben ser mayores que 0.")
    if tl <= tp:
        raise ValueError("Tl debe ser mayor que Tp (Tabla 6 E.030 2026).")
    base = periodos if periodos is not None else PERIODOS_ETABS
    lista = periodos_espectro_con_limites(tp, tl, periodos=base)
    filas: list[dict[str, float]] = []
    for t in lista:
        c = factor_amplificacion_c(t, tp, tl)
        sa = z * u * s * c / r
        filas.append({"Periodo": round(t, 4), "Sa/g": round(sa, 6)})
    return filas


def serializar_tabla_etabs(filas: list[dict[str, float]]) -> str:
    """Dos columnas tabuladas sin cabecera (ASCII) para ETABS."""
    lineas = [f'{fila["Periodo"]:.4f}\t{fila["Sa/g"]:.6f}' for fila in filas]
    return "\n".join(lineas) + "\n"
