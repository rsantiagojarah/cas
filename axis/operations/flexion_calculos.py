"""
Cálculos de diseño por flexión E-060 (criterio cuantía máxima).
Unidades: kg, cm, kg/cm2. Referencia: flexion_vigas_cuantia_max.md
"""

from __future__ import annotations

import math

from axis.core.exceptions import InvalidInput

PHI_FLEXION = 0.9
E_C = 0.003
ES = 2000000


def beta1(fc: float) -> float:
    """Factor beta1 (Art. 10.2.7.3)."""
    if fc <= 280:
        return 0.85
    return max(0.65, 0.85 - 0.05 * (fc - 280) / 70)


def profundidad_bloque_compresion(d: float, mu_kgcm: float, fc: float, b: float) -> float:
    """a = d - sqrt(d^2 - 2*Mu/(phi*0.85*fc*b)) (Art. 10.2.7.1)."""
    denom = PHI_FLEXION * 0.85 * fc * b
    if denom <= 0:
        raise InvalidInput("fc y b deben ser positivos")
    disc = d**2 - 2 * mu_kgcm / denom
    if disc < 0:
        raise InvalidInput("El momento es demasiado grande para la sección dada")
    return d - math.sqrt(disc)


def a_max_balanceada(d: float, fy: float, fc: float) -> float:
    """a_max = 0.75*a_bal (Art. 10.3.4)."""
    c_bal = E_C * d / (E_C + fy / ES)
    a_bal = beta1(fc) * c_bal
    return 0.75 * a_bal


def acero_vsr(mu_kgcm: float, d: float, a: float, fy: float) -> tuple[float, float]:
    """As = Mu/(phi*fy*(d-a/2)) (Art. 10.2). Devuelve (As, 0.0)."""
    as_req = mu_kgcm / (PHI_FLEXION * fy * (d - a / 2))
    return as_req, 0.0


def acero_vdr(
    mu_kgcm: float, fc: float, fy: float, b: float, d: float, d_prima: float,
    a_max: float, b1: float
) -> tuple[float, float, float]:
    """Acero VDR (Art. 10.3.3). Devuelve (As, As', fs')."""
    muc_nominal = 0.85 * fc * b * a_max * (d - a_max / 2)
    mus = mu_kgcm - PHI_FLEXION * muc_nominal
    c_max = a_max / b1
    fs_prima = ES * E_C * (c_max - d_prima) / c_max if c_max > 0 else 0.0
    fs_prima = min(fs_prima, fy)
    denom = PHI_FLEXION * (fs_prima - 0.85 * fc) * (d - d_prima)
    as_prima = mus / denom if denom > 0 else 0.0
    as1 = muc_nominal / (PHI_FLEXION * fy * (d - a_max / 2))
    as2 = mus / (PHI_FLEXION * fy * (d - d_prima))
    return as1 + as2, as_prima, fs_prima


def asmin(fc: float, b: float, d: float, fy: float) -> float:
    """
    Acero mínimo (Art. 10.5.1 y Anexo II): Asmin = max(Asmin1, Asmin2).
    Asmin1 = 0.7*sqrt(fc)*b*d/fy [Ec. 10-3]; Asmin2 = 1.4*b*d/fy.
    """
    asmin1 = 0.7 * math.sqrt(fc) * b * d / fy
    asmin2 = 1.4 * b * d / fy
    return max(asmin1, asmin2)


def asmax_vsr(fc: float, a_max: float, fy: float, b: float) -> float:
    """Acero máximo VSR (Art. 10.3.5)."""
    return 0.85 * fc * a_max * b / fy


def asmax_vdr(
    fc: float, a_max: float, b: float, fy: float, as_prima: float, fs_prima: float
) -> float:
    """Acero máximo VDR (Art. 10.3.5)."""
    return 0.85 * fc * a_max * b / fy + as_prima * fs_prima / fy


def mcr(fc: float, b: float, h: float) -> float:
    """Mcr = fr*Ig/yt, fr = 2*sqrt(fc) (Art. 9.6.2.3)."""
    fr = 2 * math.sqrt(fc)
    ig = b * h**3 / 12
    return fr * ig / (h / 2)


def phi_mn_vsr(as_provista: float, fy: float, fc: float, b: float, d: float) -> float:
    """Resistencia de diseño VSR (paso 7)."""
    a_real = as_provista * fy / (0.85 * fc * b)
    return PHI_FLEXION * as_provista * fy * (d - a_real / 2)


def phi_mn_vdr(
    as_total: float, as_prima: float, fc: float, fy: float,
    b: float, d: float, d_prima: float, b1: float
) -> float:
    """Resistencia de diseño VDR: cuadrática a_real, fs', phi*Mn (paso 7)."""
    A = 0.85 * fc * b
    B = as_prima * ES * E_C - as_total * fy
    C = -as_prima * ES * E_C * b1 * d_prima
    disc = B**2 - 4 * A * C
    if disc < 0:
        return 0.0
    a_real = (-B + math.sqrt(disc)) / (2 * A)
    fs_prima = ES * E_C * (1 - d_prima * b1 / a_real) if a_real > 0 else 0.0
    fs_prima = min(fs_prima, fy)
    return PHI_FLEXION * (
        0.85 * fc * b * a_real * (d - a_real / 2) + as_prima * fs_prima * (d - d_prima)
    )
