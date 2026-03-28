"""Constantes RNE E.060 para diseño de muros estructurales."""

from __future__ import annotations


class RNE:
    """Constantes normativas RNE E.060 para muros."""

    # Espesores mínimos (Art. 21.9)
    THICKNESS_RATIO: float = 25.0
    MIN_T_GENERAL: float = 15.0       # cm
    MIN_T_BASEMENT: float = 20.0      # cm

    # Cuantías mínimas de refuerzo
    MIN_RHO_H: float = 0.0025
    MIN_RHO_V: float = 0.0025

    # Factores de reducción φ
    PHI_FLEX: float = 0.9
    PHI_SHEAR: float = 0.85

    # Coeficientes de corte (Art. 11.10 y 21.9)
    SHEAR_COEF_1: float = 0.27        # umbral 0.27√f'c·Acw
    SHEAR_COEF_2: float = 2.6         # límite 2.6√f'c·Acw

    # Amplificación por capacidad (Art. 21.9.5.3 E.060)
    # Factor de amplificación = min(Mn/Mua, R); R según E.030 (ej. R=6 muros ductiles)
    R: float = 6.0
    CAPACITY_AMP_LIMIT: float = 6.0   # alias de R (Mn/Mua ≤ R)

    # Agrietamiento
    CRACKING_FACTOR: float = 1.2      # Mn ≥ 1.2 Mcr

    # Elementos de borde – Esfuerzos (Art. 21.9.7.5)
    STRESS_ON: float = 0.20           # requiere borde si σ > 0.20 f'c
    STRESS_OFF: float = 0.15          # no requiere si σ < 0.15 f'c

    # Elementos de borde – Deformación (Art. 21.9.7.4)
    DEFORM_DENOM: float = 600.0       # C_lim = lm / [600·(δu/H)]
    DEFORM_RATIO_MIN: float = 0.005   # δu/H_total ≥ 0.005

    # Juntas de construcción (Art. 11.7.4.3 — corte por fricción)
    PHI_JOINT_FRICTION: float = 0.85
    JOINT_COEF_1: float = 0.2         # Vn < 0.2 f'c · Ac
    JOINT_COEF_2: float = 55.0        # Vn < 55 · Ac

    # Compresión pura (14.5.2)
    COMPRESSION_FACTOR: float = 0.55
