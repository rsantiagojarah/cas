"""
Implementación de DataSource que obtiene datos desde ETABS vía COM.

Delega en las funciones existentes de etapa3_analisis y etapa4_validacion
para no duplicar lógica (DRY).
"""

from __future__ import annotations

from typing import Any, Optional

from axis.data.source import DataSource
from axis.data.etabs_connection import conectar_con_etabs, verificar_etabs_disponible
from axis.sismico.etapa3_analisis import (
    periodo_fundamental_etabs,
    masa_participante_etabs,
    peso_edificio_etabs,
    story_forces_estatico_etabs,
    story_forces_dinamico_etabs,
    verificar_cortante_minima_etabs,
)
from axis.sismico.etapa4_validacion import (
    clasificar_sistema_estructural_etabs,
    distorsion_admisible_etabs,
)


class EtabsSource(DataSource):
    """Fuente de datos que lee desde ETABS (tablas Database Tables vía COM)."""

    def get_periodo_fundamental(self, log: bool = True) -> Optional[dict[str, Any]]:
        return periodo_fundamental_etabs(log=log)

    def get_masa_participante(self, log: bool = True) -> Optional[dict[str, Any]]:
        return masa_participante_etabs(log=log)

    def get_peso_edificio(self, log: bool = True) -> Optional[Any]:
        return peso_edificio_etabs(log=log)

    def get_story_forces_estatico(self, log: bool = True) -> Optional[dict[str, Any]]:
        return story_forces_estatico_etabs(log=log)

    def get_story_forces_dinamico(self, log: bool = True) -> Optional[dict[str, Any]]:
        return story_forces_dinamico_etabs(log=log)

    def get_cortante_minima(
        self,
        ia: float = 1.0,
        ip: float = 1.0,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        return verificar_cortante_minima_etabs(log=log, ia=ia, ip=ip)

    def get_clasificacion_sistema(
        self,
        cortante_basal_x: Optional[float] = None,
        cortante_basal_y: Optional[float] = None,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        return clasificar_sistema_estructural_etabs(
            cortante_basal_x=cortante_basal_x,
            cortante_basal_y=cortante_basal_y,
            log=log,
        )

    def get_distorsion(
        self,
        r: float,
        material: str,
        factor_drift: float = 0.75,
        log: bool = True,
    ) -> Optional[dict[str, Any]]:
        return distorsion_admisible_etabs(
            r=r,
            material=material,
            factor_drift=factor_drift,
            log=log,
        )

    def disponible(self) -> bool:
        if not verificar_etabs_disponible():
            return False
        return conectar_con_etabs() is not None
