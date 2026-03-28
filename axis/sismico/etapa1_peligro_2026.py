"""
Etapa 1 – Peligro sísmico E.030.
Factor de amplificación C(T), parámetros de sitio y tabla C vs T.
"""

from __future__ import annotations

from typing import List, Tuple

from axis.sismico.tables_e030_2026 import obtener_parametros_sitio


def factor_amplificacion_c(t: float, tp: float, tl: float, modo_estatico: bool = False) -> float:
    """
    Factor de amplificación sísmica C según E.030 2026 resumida.
    - Estático: para 0 <= T <= Tp, C = 2.5
    - Dinámico:
      T < 0.2Tp: C = 1 + 7.5(T/Tp)
      0.2Tp <= T <= Tp: C = 2.5
      Tp < T < Tl: C = 2.5(Tp/T)
      T >= Tl: C = 2.5(Tp*Tl/T²)
    """
    if tp <= 0 or tl <= 0:
        raise ValueError("Tp y Tl deben ser mayores que 0.")
    if t <= 0:
        return 2.5
    if modo_estatico and t <= tp:
        return 2.5
    if t < 0.2 * tp:
        return 1.0 + 7.5 * (t / tp)
    if t <= tp:
        return 2.5
    if t < tl:
        return 2.5 * (tp / t)
    return 2.5 * (tp * tl / (t * t))


def parametros_sitio(perfil_suelo: str, zona: int, vs: float | None = None) -> dict:
    """
    Obtiene S, Tp y Tl según E.030: S de Tabla N° 3 (zona + perfil), Tp y Tl de Tabla N° 4 (perfil).
    Para S4 retorna dict con valores None (estudio específico).
    """
    return obtener_parametros_sitio(perfil_suelo, zona, vs=vs)


def tabla_c_vs_t(
    tp: float,
    tl: float,
    periodos: List[float] | None = None,
    paso: float = 0.05,
    modo_estatico: bool = False,
) -> List[Tuple[float, float]]:
    """
    Genera datos tabulados C vs T.
    Si periodos es None, usa desde paso hasta tl + 0.5 con incremento paso.
    """
    if periodos is not None:
        return [(t, factor_amplificacion_c(t, tp, tl, modo_estatico=modo_estatico)) for t in periodos]
    t_actual = paso
    t_max = tl + 0.5
    resultado: List[Tuple[float, float]] = []
    while t_actual <= t_max:
        resultado.append((t_actual, factor_amplificacion_c(t_actual, tp, tl, modo_estatico=modo_estatico)))
        t_actual += paso
    return resultado
