"""Modelos de datos para diseño de columnas RNE E.060."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class ColumnProperties:
    """Propiedades de una columna para análisis de esbeltez."""
    story: str
    unique_name: str
    k: float = 1.0
    lu: float = 0.0
    I: float = 0.0
    Ag: float = 0.0
    Ec: float = 0.0
    Bd: float = 0.5
    fc: float = 210.0
    fy: float = 4200.0

    @property
    def r(self) -> float:
        if self.Ag <= 0 or self.I < 0:
            return 0.0
        return math.sqrt(self.I / self.Ag)

    @property
    def klu_r(self) -> float:
        r = self.r
        if r <= 1e-10:
            return 0.0
        return (self.k * self.lu) / r


@dataclass
class QResult:
    """Resultado del análisis de estabilidad Q por piso."""
    story: str
    direction: str
    selected_case: str
    Pu: float
    Vus: float
    drift_ratio: float
    he: float
    delta_o: float
    Q: float
    classification: str


@dataclass
class SlendernessResult:
    """Resultado del análisis de esbeltez (M1, M2)."""
    story: str
    unique_name: str
    M1_X: float = 0.0
    M2_X: float = 0.0
    M1_Y: float = 0.0
    M2_Y: float = 0.0
    curvatura_X: str = "N/A"
    curvatura_Y: str = "N/A"


@dataclass
class SecondOrderResult:
    """Resultado de evaluación de segundo orden."""
    story: str
    unique_name: str
    direction: str
    arriostrado: str
    k: float
    r: float
    lu: float
    M1_M2: float
    formula_34_12: float
    klu_r: float
    ignorar_2do_orden: str


@dataclass
class CmResult:
    """Resultado del factor Cm."""
    story: str
    unique_name: str
    M1_X: float = 0.0
    M2_X: float = 0.0
    Cm_X: float = 1.0
    M1_Y: float = 0.0
    M2_Y: float = 0.0
    Cm_Y: float = 1.0


@dataclass
class DeltaResult:
    """Resultado del factor delta."""
    story: str
    unique_name: str
    Pu: float = 0.0
    EI: float = 0.0
    Pc: float = 0.0
    Cm_X: float = 1.0
    Delta_X: float = 1.0
    Cm_Y: float = 1.0
    Delta_Y: float = 1.0


@dataclass
class InteractionPoint:
    """Punto en un diagrama de interacción."""
    p: float
    m2: float
    m3: float
    angle: float


@dataclass
class PMVerificationResult:
    """Resultado de verificación P-M."""
    story: str
    unique_name: str
    load_case: str
    pu: float
    m2: float
    m3: Optional[float]
    mn_nominal: float
    capacity_ultimate: float
    ratio: float
    passes: bool
    is_biaxial: bool
