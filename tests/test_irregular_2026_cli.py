"""Tests CLI y verificacion irregularidades E.030 2026."""

import unittest

from axis.cli.handlers_irregular import dispatch_irregular, CFG_2026, CFG_LEGACY
from axis.cli.handlers_irregular_2026 import handle_irregular_2026
from axis.sismico.irregularidades_verificacion import verificar_diafragma as verificar_diafragma_legacy
from axis.sismico.irregularidades_verificacion_2026 import verificar_diafragma as verificar_diafragma_2026


class TestIrregular2026Cli(unittest.TestCase):
    def test_help_menciona_2026(self) -> None:
        salida = handle_irregular_2026([])
        self.assertIn("E.030 2026", salida)
        self.assertIn("cas irregular 2026 rigidez", salida)
        self.assertIn("Tabla 11", salida)
        self.assertIn("Tabla 12", salida)

    def test_legacy_help_sin_2026_rapido(self) -> None:
        salida = dispatch_irregular([], CFG_LEGACY)
        self.assertIn("Tabla 8", salida)
        self.assertNotIn("cas sismo 2026 rapido", salida)

    def test_diafragma_criterio_seccion_2026(self) -> None:
        # 30% de area neta respecto al total: irregular en 2026 (<50%), no en legacy (<25%)
        r_legacy = verificar_diafragma_legacy(0, 100, 30, 100)
        r_2026 = verificar_diafragma_2026(0, 100, 30, 100)
        self.assertFalse(r_legacy["existe"])
        self.assertTrue(r_2026["existe"])


if __name__ == "__main__":
    unittest.main()
