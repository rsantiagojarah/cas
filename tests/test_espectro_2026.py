"""Tests del comando cas espectro (E.030 2026)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from axis.cli.handlers_espectro import handle_espectro
from axis.sismico.espectro_etabs_2026 import PERIODOS_ETABS, generar_filas_sa, serializar_tabla_etabs
from axis.sismico.etapa1_peligro_2026 import factor_amplificacion_c, tabla_c_vs_t


class TestEspectroE0302026(unittest.TestCase):
    def test_periodos_fijos(self) -> None:
        self.assertEqual(len(PERIODOS_ETABS), 23)
        self.assertEqual(PERIODOS_ETABS[0], 0.0)
        self.assertEqual(PERIODOS_ETABS[-1], 15.0)

    def test_sa_zusc_sobre_r(self) -> None:
        z, u, s, tp, tl, r = 0.35, 1.0, 1.15, 0.6, 3.0, 8.0
        t = 1.0
        c = factor_amplificacion_c(t, tp, tl)
        esperado = round(z * u * s * c / r, 6)
        filas = generar_filas_sa(z, u, s, tp, tl, r)
        fila_t1 = next(f for f in filas if f["Periodo"] == 1.0)
        self.assertEqual(fila_t1["Sa/g"], esperado)

    def test_t_cero_usa_c_uno_tramo_dinamico(self) -> None:
        z, u, s, tp, tl, r = 0.35, 1.0, 1.15, 0.6, 3.0, 8.0
        filas = generar_filas_sa(z, u, s, tp, tl, r)
        sa_t0 = filas[0]["Sa/g"]
        esperado = round(z * u * s * 1.0 / r, 6)
        self.assertEqual(sa_t0, esperado)

    def test_tramo_inicial_crece_sin_valle(self) -> None:
        """Tp=0.9: Sa debe crecer de T=0 a T=0.2*Tp sin bajar respecto a T=0."""
        filas = generar_filas_sa(0.35, 1.0, 1.2, 0.9, 1.6, 3.0)
        sa = [f["Sa/g"] for f in filas[:4]]
        self.assertLessEqual(sa[0], sa[1])
        self.assertLessEqual(sa[1], sa[2])
        self.assertAlmostEqual(sa[2], 0.35)
        self.assertAlmostEqual(sa[3], 0.35)

    def test_incluye_puntos_limite_tabla_6(self) -> None:
        tp, tl = 0.9, 1.6
        periodos_ct = [t for t, _c in tabla_c_vs_t(tp, tl)]
        periodos_sa = [fila["Periodo"] for fila in generar_filas_sa(0.35, 1.0, 1.2, tp, tl, 3.0)]
        for t in (0.0, 0.18, 0.9, 1.6):
            self.assertIn(t, periodos_ct)
            self.assertIn(t, periodos_sa)

    def test_serializar_sin_cabecera(self) -> None:
        filas = generar_filas_sa(0.35, 1.0, 1.15, 0.6, 3.0, 8.0)
        texto = serializar_tabla_etabs(filas)
        self.assertNotIn("Periodo", texto)
        self.assertIn("0.0000\t", texto)
        self.assertIn("15.0000\t", texto)

    def test_cli_exporta_archivo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta = Path(tmpdir) / "espectro.txt"
            with patch("axis.cli.handlers_espectro.seleccionar_ruta_guardado", return_value=ruta):
                salida = handle_espectro(["0.35", "1.0", "1.15", "0.6", "3.0", "1.0", "1.0", "8"])
            self.assertTrue(ruta.exists())
            self.assertIn("Archivo ETABS guardado", salida)
            lineas = ruta.read_text(encoding="ascii").strip().splitlines()
            self.assertIn("0.1200\t", lineas[2])
            self.assertEqual(len(lineas), 24)

    @patch("axis.cli.handlers_espectro.seleccionar_ruta_guardado", return_value=None)
    def test_cli_cancelacion(self, _mock) -> None:
        salida = handle_espectro(["0.35", "1.0", "1.15", "0.6", "3.0", "1.0", "1.0", "8"])
        self.assertIn("Guardado cancelado", salida)


if __name__ == "__main__":
    unittest.main()
