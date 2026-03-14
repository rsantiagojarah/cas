"""Operaciones registradas. Importar para activar registros."""

from axis.operations.placeholder import test_operation  # noqa: F401
from axis.operations.flexion import flexion_viga, flexion_losa  # noqa: F401
from axis.operations.cortante import cortante_viga, cortante_losa  # noqa: F401
from axis.operations.inercia_fisurada import inercia_fisurada  # noqa: F401
from axis.operations.muros_nucleo import predimension_muro_nucleo  # noqa: F401
from axis.operations.muros_diseno import diseno_muro, diseno_muro_multi  # noqa: F401