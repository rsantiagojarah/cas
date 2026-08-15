"""
Etapa 1 – Peligro sísmico E.030.
Factor de amplificación C(T), parámetros de sitio y tabla C vs T.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from axis.sismico.tables_e030_2026 import obtener_parametros_sitio


def factor_amplificacion_c(t: float, tp: float, tl: float, modo_estatico: bool = False) -> float:
    """
    Factor de amplificación sísmica C según E.030 2026 resumida.
    - Estático: para 0 <= T <= Tp, C = 2.5
    - Dinámico (Tabla 6 / SKILL seccion 11 y 31):
      T=0: C=1 (limite del tramo 1)
      T < 0.2Tp: C = 1 + 7.5(T/Tp)
      0.2Tp <= T <= Tp: C = 2.5
      Tp < T < Tl: C = 2.5(Tp/T)
      T >= Tl: C = 2.5(Tp*Tl/T²)
    """
    if tp <= 0 or tl <= 0:
        raise ValueError("Tp y Tl deben ser mayores que 0.")
    if modo_estatico and t <= tp:
        return 2.5
    if t <= 0:
        return 1.0
    if t < 0.2 * tp:
        return 1.0 + 7.5 * (t / tp)
    if t <= tp:
        return 2.5
    if t < tl:
        return 2.5 * (tp / t)
    return 2.5 * (tp * tl / (t * t))


def periodos_espectro_con_limites(
    tp: float,
    tl: float,
    periodos: Iterable[float] | None = None,
    paso: float = 0.05,
    t_max: float | None = None,
) -> list[float]:
    """
    Genera/normaliza periodos incluyendo siempre los quiebres de Tabla 6.
    Mantiene la grilla regular, pero agrega 0, 0.2Tp, Tp y Tl aunque no caigan en el paso.
    """
    if tp <= 0 or tl <= 0:
        raise ValueError("Tp y Tl deben ser mayores que 0.")
    if paso <= 0:
        raise ValueError("El paso debe ser mayor que 0.")

    if periodos is None:
        limite = tl + 0.5 if t_max is None else t_max
        n_pasos = int(limite / paso)
        base = [round(i * paso, 4) for i in range(n_pasos + 1)]
        if not base or base[-1] < round(limite, 4):
            base.append(round(limite, 4))
    else:
        base = [float(t) for t in periodos]

    puntos_limite = [0.0, 0.2 * tp, tp, tl]
    return sorted({round(t, 4) for t in [*base, *puntos_limite] if t >= 0})


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
    Si periodos es None, usa desde 0 hasta tl + 0.5 con incremento paso.
    Siempre incluye 0, 0.2Tp, Tp y Tl como puntos de quiebre.
    """
    periodos_finales = periodos_espectro_con_limites(tp, tl, periodos=periodos, paso=paso)
    return [(t, factor_amplificacion_c(t, tp, tl, modo_estatico=modo_estatico)) for t in periodos_finales]
