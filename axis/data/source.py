"""
Abstracción de fuente de datos para análisis sísmico E.030.

Permite obtener datos desde ETABS o desde entrada manual (JSON/CSV/dict),
manteniendo el mismo flujo de análisis. Principio de inversión de dependencias (SOLID).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

# Tipo genérico para tablas (DataFrame o estructura equivalente)
# Evita importar pandas en la ABC para reducir acoplamiento.
TableType = Any


class DataSource(ABC):
    """
    Fuente de datos para el análisis sísmico E.030.
    Implementaciones: EtabsSource (ETABS vía COM), ManualSource (datos ingresados).
    """

    @abstractmethod
    def get_periodo_fundamental(self, log: bool = True) -> Optional[dict[str, Any]]:
        """
        Periodo fundamental en X e Y.
        Retorna: periodo_x, periodo_y, tabla_case_period, tabla_modal_periods.
        """
        ...

    @abstractmethod
    def get_masa_participante(self, log: bool = True) -> Optional[dict[str, Any]]:
        """
        Masa participante modal.
        Retorna: tabla, cumple_90_x, cumple_90_y.
        """
        ...

    @abstractmethod
    def get_peso_edificio(self, log: bool = True) -> Optional[TableType]:
        """
        Peso por piso (Story, Peso X, Peso Y).
        """
        ...

    @abstractmethod
    def get_story_forces_estatico(self, log: bool = True) -> Optional[dict[str, TableType]]:
        """
        Fuerzas por piso (análisis estático). Claves: SISMOX, SISMOY.
        """
        ...

    @abstractmethod
    def get_story_forces_dinamico(self, log: bool = True) -> Optional[dict[str, TableType]]:
        """
        Fuerzas por piso (análisis dinámico). Claves: SPX, SPY.
        """
        ...

    @abstractmethod
    def get_cortante_minima(
        self,
        ia: float = 1.0,
        ip: float = 1.0,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        """
        Verificación cortante mínima dinámica vs estática. Claves: x, y.
        """
        ...

    @abstractmethod
    def get_clasificacion_sistema(
        self,
        cortante_basal_x: Optional[float] = None,
        cortante_basal_y: Optional[float] = None,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        """
        Clasificación sistema estructural (pórtico/dual/muros).
        """
        ...

    @abstractmethod
    def get_distorsion(
        self,
        r: float,
        material: str,
        factor_drift: float = 0.75,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        """
        Distorsión admisible por material. Retorna tabla_x/y, cumple_x/y, etc.
        """
        ...

    def disponible(self) -> bool:
        """
        Indica si la fuente puede proporcionar datos (ej. ETABS conectado).
        Por defecto True; EtabsSource puede sobreescribir.
        """
        return True
