"""
Cálculos de diseño por cortante E-060 (vigas).
Unidades: kg, cm, kg/cm². Referencia: cortante_vigas.md
"""

from __future__ import annotations

import math

PHI_CORTANTE = 0.85  # Art. 9.3.2.1


def vc(fc: float, b: float, d: float) -> float:
    """Cortante que resiste el concreto (Art. 11.3.1): Vc = 0.53*sqrt(fc)*b*d."""
    return 0.53 * (fc**0.5) * b * d


def vs_max(fc: float, b: float, d: float) -> float:
    """Cortante que resiste el acero máximo (Art. 11.3.1): Vs_max = 2.1*sqrt(fc)*b*d."""
    return 2.1 * (fc**0.5) * b * d


def vn_max(vc_kg: float, vs_max_kg: float) -> float:
    """Cortante nominal máximo: Vn_max = Vc + Vs_max (Art. 11.3.1)."""
    return vc_kg + vs_max_kg


def vs_requerido(vu_kg: float, vc_kg: float) -> float:
    """Cortante a resistir por acero: Vs = Vu/phi - Vc (Art. 11.3.1)."""
    return vu_kg / PHI_CORTANTE - vc_kg


def av_s_requerido(vs_kg: float, fy: float, d: float) -> float:
    """Av/s requerido (cm²/cm): Vs/(fy*d) cuando se requiere refuerzo."""
    if fy <= 0 or d <= 0:
        return 0.0
    return vs_kg / (fy * d)


def s_max_base(d: float) -> float:
    """Espaciamiento máximo base: min(d/2, 60 cm) (Art. 11.3.1)."""
    return min(d / 2, 60.0)


def s_max_reducido(s_max_base_cm: float, vs_kg: float, fc: float, b: float, d: float) -> float:
    """
    Si Vs > 1.1*sqrt(fc)*b*d entonces Smax = S/2 (Art. 11.3.1).
    Retorna espaciamiento máximo en cm.
    """
    umbral = 1.1 * (fc**0.5) * b * d
    if vs_kg > umbral:
        return s_max_base_cm / 2
    return s_max_base_cm


def av_s_min(fc: float, b: float, fy: float) -> float:
    """
    Cuantía mínima de estribos (Art. 11.3.1): Av/s_min = max(Av_s_min1/s, Av_s_min2/s).
    Av_s_min1/s = 0.2*sqrt(fc)*b/fy; Av_s_min2/s = 3.5*b/fy.
    """
    av_s_min1 = 0.2 * (fc**0.5) * b / fy
    av_s_min2 = 3.5 * b / fy
    return max(av_s_min1, av_s_min2)
