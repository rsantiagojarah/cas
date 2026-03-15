"""Modelos de datos para diseño de muros RNE E.060. Unidades: cm, kg, kg/cm², kg·cm."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class WallGeometry:
    """Geometría del muro (todo en cm)."""
    hm: float       # altura del muro
    lm: float       # longitud del muro
    t: float        # espesor
    is_basement: bool = False

    @property
    def Acw(self) -> float:
        return self.lm * self.t

    @property
    def Ig(self) -> float:
        return self.t * self.lm ** 3 / 12.0

    @property
    def Sg(self) -> float:
        return self.Ig / (self.lm / 2.0)


@dataclass
class WallMaterials:
    """Propiedades de materiales (kg/cm²)."""
    fc: float
    fy: float
    fyt: float
    Ec: Optional[float] = None

    def __post_init__(self) -> None:
        if self.Ec is None:
            self.Ec = 15000.0 * math.sqrt(self.fc)

    @property
    def sqrt_fc(self) -> float:
        return math.sqrt(self.fc)


@dataclass
class WallLoads:
    """Cargas amplificadas. Pu negativo = compresión (convención ETABS)."""
    Pu: float             # kg
    Vu: float             # kg (valor absoluto para diseño)
    Mu: float             # kg·cm (valor absoluto para diseño)
    delta_u: Optional[float] = None   # cm
    c: Optional[float] = None         # cm (eje neutro del análisis elástico)
    Mn_manual: Optional[float] = None  # kg·cm


@dataclass
class Reinforcement:
    """Distribución de refuerzo."""
    rho_h: float = 0.0025
    rho_v: float = 0.0025
    n_capas: int = 2


@dataclass
class FlexureResult:
    Mn: float              # kg·cm
    Mua: float             # kg·cm
    ok: bool
    Mcr: Optional[float] = None
    cracking_ok: Optional[bool] = None


@dataclass
class ShearResult:
    Vu_orig: float         # kg
    Vu_cap: float          # kg (amplificado por capacidad)
    Vc: float              # kg
    Vs: float              # kg
    Vn: float              # kg
    phi_Vn: float          # kg
    ok: bool
    vn_limit_ok: bool


@dataclass
class BoundaryResult:
    requires: bool
    method: str            # "DEFORMACION" | "ESFUERZO"
    details: dict = field(default_factory=dict)


@dataclass
class JointResult:
    Vn_joint: float
    phi_Vn_joint: float
    ok: bool
    Av: float = 0.0
    mu: float = 1.0


@dataclass
class WallDesignResult:
    """Resultado completo del diseño de un muro."""
    nombre: str
    geometry_ok: bool
    thickness_msg: str
    flexure: FlexureResult
    shear: ShearResult
    reinforcement: Reinforcement
    boundary: Optional[BoundaryResult] = None
    joint: Optional[JointResult] = None

    @property
    def ok(self) -> bool:
        base = (
            self.geometry_ok
            and self.flexure.ok
            and self.shear.ok
            and self.shear.vn_limit_ok
            and (self.flexure.cracking_ok is not False)
        )
        if self.joint is not None:
            base = base and self.joint.ok
        return base


@dataclass
class StoryData:
    """Datos de un piso para diseño multipiso."""
    piso: int
    hm: float            # cm
    Pu: float             # kg
    Vu: float             # kg
    Mu: float             # kg-cm
    Mn_manual: Optional[float] = None  # kg-cm
    c: Optional[float] = None          # cm
    Vu_cap_demand: Optional[float] = None  # kg; si se da, diseño a corte usa este en vez de Vua*min(Mn/Mua,R)


@dataclass
class StoryDesignResult:
    """Resultado de diseño de un piso individual."""
    piso: int
    result: WallDesignResult
    requires_boundary: bool = False
    boundary_height: Optional[float] = None
    largo_borde: Optional[float] = None


@dataclass
class MultiStoryResult:
    """Resultado completo de diseño multipiso."""
    nombre: str
    lm: float
    t: float
    H_total: float
    stories: list  # list[StoryDesignResult]
    boundary_global: Optional[BoundaryResult] = None
    delta_u: Optional[float] = None
    k_buckling: float = 1.0
    compression_phi_Pn: Optional[float] = None

    @property
    def ok(self) -> bool:
        return all(s.result.ok for s in self.stories)
