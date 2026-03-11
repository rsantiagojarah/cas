"""
Dataclasses para elementos estructurales (vigas, columnas).
Permite agregar columnas/losas sin romper vigas; validación y serialización centralizada.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass(frozen=False)
class Viga:
    """Viga: geometría, materiales y esfuerzos (Mu, Vu) para diseño E.060."""
    nombre: str
    fc: float  # kg/cm²
    fy: float  # kg/cm²
    b: float   # cm
    h: float   # cm
    rec: float # cm
    Mu: float  # Tn-m
    Vu: float  # Tn

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Viga":
        """Crea Viga desde dict (ej. fila CSV); acepta strings numéricos."""
        def f(k: str, default: float = 0.0) -> float:
            v = d.get(k, default)
            if v is None or v == "":
                return default
            if isinstance(v, (int, float)):
                return float(v)
            return float(str(v).replace(",", "."))
        return cls(
            nombre=str(d.get("nombre") or "").strip() or "Viga",
            fc=f("fc"), fy=f("fy"), b=f("b"), h=f("h"), rec=f("rec"),
            Mu=f("Mu"), Vu=f("Vu", 0.0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Dict para escribir en CSV (vigas.csv)."""
        return asdict(self)


@dataclass(frozen=False)
class Columna:
    """Columna: geometría, materiales y esfuerzos (Pu, Mux, Muy) para diseño E.060."""
    nombre: str
    fc: float
    fy: float
    b: float
    h: float
    rec: float
    Pu: float   # Tn
    Mux: float  # Tn-m
    Muy: float  # Tn-m

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Columna":
        def f(k: str, default: float = 0.0) -> float:
            v = d.get(k, default)
            if v is None or v == "":
                return default
            if isinstance(v, (int, float)):
                return float(v)
            return float(str(v).replace(",", "."))
        return cls(
            nombre=str(d.get("nombre") or "").strip() or "Columna",
            fc=f("fc"), fy=f("fy"), b=f("b"), h=f("h"), rec=f("rec"),
            Pu=f("Pu"), Mux=f("Mux"), Muy=f("Muy"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
