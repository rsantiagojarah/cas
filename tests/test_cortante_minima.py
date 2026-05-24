"""Tests verificacion cortante minima E.030 (redondeo y escalamiento)."""

from __future__ import annotations

import unittest

from axis.sismico.etapa3_analisis import (
    cortante_cumple_umbral,
    cortante_minima_requerida,
    UMBRAL_CORTANTE_MINIMA_IRREGULAR,
)


class TestCortanteMinima(unittest.TestCase):
    def test_caso_usuario_escalado_cumple_tras_gamma(self) -> None:
        """Vest=89.99, Vdin=55.93, gamma~1.448: tras escalar debe cumplir (no falso negativo)."""
        vest = 89.99
        vdin = 55.93
        umbral = UMBRAL_CORTANTE_MINIMA_IRREGULAR
        self.assertFalse(cortante_cumple_umbral(vdin, vest, umbral))
        vmin = cortante_minima_requerida(vest, umbral)
        self.assertAlmostEqual(vmin, 80.99, places=2)
        gamma = vmin / abs(vdin)
        self.assertAlmostEqual(gamma, 1.448, places=3)
        v_esc = gamma * vdin
        self.assertTrue(cortante_cumple_umbral(v_esc, vest, umbral))
        self.assertTrue(cortante_cumple_umbral(vmin, vest, umbral))

    def test_sin_escalar_cumple_si_alcanza_umbral(self) -> None:
        vest = 100.0
        vdin = 80.0
        self.assertTrue(cortante_cumple_umbral(vdin, vest, 0.80))

    def test_regular_umbral_080(self) -> None:
        self.assertFalse(cortante_cumple_umbral(79.994, 100.0, 0.80))
        self.assertTrue(cortante_cumple_umbral(80.0, 100.0, 0.80))


if __name__ == "__main__":
    unittest.main()
