"""
Etapa 2 – Caracterización del edificio E.030.
Coeficiente de reducción de la fuerza sísmica R = R0 * Ia * Ip.
"""

from __future__ import annotations


def coeficiente_reduccion_r(r0: float, ia: float, ip: float) -> float:
    """
    Coeficiente de reducción de la fuerza sísmica.
    R = R0 * Ia * Ip (factores de irregularidad en altura y en planta).
    """
    if ia <= 0 or ip <= 0:
        raise ValueError("Ia e Ip deben ser mayores que 0.")
    return r0 * ia * ip
