from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from axis.sismico.etapa1_peligro_2026 import factor_amplificacion_c
from axis.sismico.etapa4_validacion_2026 import separacion_edificios
from axis.sismico.tables_e030_2026 import (
    obtener_distorsion_maxima,
    obtener_parametros_sitio,
    obtener_u,
)
from axis.cli.sismo_handlers import handle_sismo_separacion as handle_sismo_separacion_legacy
from axis.cli.sismo_handlers_2026 import (
    handle_sismo_2026,
    handle_sismo_calcular,
    handle_sismo_rapido,
    handle_sismo_separacion,
)


class SismoE030ActualizacionTests(unittest.TestCase):
    def test_parametros_sitio_s2_interpola_tp_con_vs(self) -> None:
        params = obtener_parametros_sitio("s2", 3, vs=450.0)
        self.assertAlmostEqual(params["s"], 1.15)
        self.assertAlmostEqual(params["tp"], 0.5)
        self.assertEqual(params["tl"], 3.0)
        self.assertFalse(params["requiere_estudio"])

    def test_parametros_sitio_s3_sin_vs_usa_default(self) -> None:
        params = obtener_parametros_sitio("s3", 2)
        self.assertAlmostEqual(params["s"], 1.40)
        self.assertAlmostEqual(params["tp"], 0.9)
        self.assertIn("Tp=0.90", " ".join(params["advertencias"]))

    def test_parametros_sitio_z4_s4_requiere_respuesta_sitio(self) -> None:
        params = obtener_parametros_sitio("s4", 4)
        self.assertIsNone(params["s"])
        self.assertTrue(params["requiere_estudio"])
        self.assertEqual(params["estado"], "requiere_respuesta_sitio")

    def test_parametros_sitio_s5_requiere_estudio_especial(self) -> None:
        params = obtener_parametros_sitio("s5", 3)
        self.assertTrue(params["requiere_estudio"])
        self.assertEqual(params["estado"], "requiere_estudio_especial")

    def test_categoria_d_se_rechaza(self) -> None:
        with self.assertRaisesRegex(ValueError, "Categoría D"):
            obtener_u("D")

    def test_factor_c_cuatro_tramos_y_estatico(self) -> None:
        tp = 0.6
        tl = 3.0
        self.assertAlmostEqual(factor_amplificacion_c(0.05, tp, tl), 1.625)
        self.assertAlmostEqual(factor_amplificacion_c(0.30, tp, tl), 2.5)
        self.assertAlmostEqual(factor_amplificacion_c(1.20, tp, tl), 1.25)
        self.assertAlmostEqual(factor_amplificacion_c(4.0, tp, tl), 0.28125)
        self.assertAlmostEqual(factor_amplificacion_c(0.10, tp, tl, modo_estatico=True), 2.5)

    def test_separacion_nueva_formula(self) -> None:
        sep = separacion_edificios(altura_nivel_h=10.0, z=0.45, s=1.2)
        self.assertAlmostEqual(sep["s_norma"], 0.108)
        self.assertAlmostEqual(sep["s_final"], 0.108)
        self.assertEqual(sep["advertencias"], [])

    def test_separacion_compatibilidad_antigua_advierte(self) -> None:
        sep = separacion_edificios(altura_nivel_h=10.0)
        self.assertAlmostEqual(sep["s_norma"], 0.06)
        self.assertTrue(sep["advertencias"])

    def test_separacion_legacy_sigue_disponible(self) -> None:
        salida = handle_sismo_separacion_legacy(["10", "0.01", "0.01"])
        self.assertIn("0.006·h", salida)

    def test_distorsion_emdl_actualizada(self) -> None:
        self.assertAlmostEqual(obtener_distorsion_maxima("emdl"), 0.004)

    @patch("axis.cli.sismo_handlers_2026._get_project_path", return_value=Path("."))
    @patch("axis.data.etabs_table_reader.clear_table_cache")
    @patch("axis.cli.sismo_handlers_2026.ejecutar_analisis_sismico")
    def test_cli_calcular_acepta_r0_y_material_nuevos(self, mock_ejecutar, _mock_cache, _mock_path) -> None:
        mock_ejecutar.return_value = {
            "z": 0.35,
            "u": 1.0,
            "s_val": 1.15,
            "tp": 0.6,
            "tl": 3.0,
            "filas_ct": [],
            "filas_espectro": [],
            "path": Path("."),
            "advertencias": [],
            "estado_peligro": "ok",
            "r": 3.5,
            "periodo": 0.0,
            "tbl_per": None,
            "tbl_modal": None,
            "cumple_masa": False,
            "tbl_masa": None,
            "df_peso": None,
            "tbl_est": None,
            "tbl_din": None,
            "cort": None,
            "datos_cort": None,
            "cl": None,
            "dr": None,
            "k": "x",
            "factor_drift": 0.75,
        }
        salida = handle_sismo_calcular(["X", "3", "C", "S2", "3.5", "1", "1", "emdl"])
        self.assertIn("ANALISIS SISMICO E.030 2026", salida)
        mock_ejecutar.assert_called_once()

    @patch("axis.cli.sismo_handlers_2026._get_project_path", return_value=Path("."))
    @patch("axis.data.etabs_table_reader.clear_table_cache")
    @patch("axis.cli.sismo_handlers_2026.ejecutar_analisis_sismico")
    def test_entrypoint_sismo_2026_despacha(self, mock_ejecutar, _mock_cache, _mock_path) -> None:
        mock_ejecutar.return_value = {
            "z": 0.35,
            "u": 1.0,
            "s_val": 1.15,
            "tp": 0.6,
            "tl": 3.0,
            "filas_ct": [],
            "filas_espectro": [],
            "path": Path("."),
            "advertencias": [],
            "estado_peligro": "ok",
            "r": 3.5,
            "periodo": 0.0,
            "tbl_per": None,
            "tbl_modal": None,
            "cumple_masa": False,
            "tbl_masa": None,
            "df_peso": None,
            "tbl_est": None,
            "tbl_din": None,
            "cort": None,
            "datos_cort": None,
            "cl": None,
            "dr": None,
            "k": "x",
            "factor_drift": 0.75,
        }
        salida = handle_sismo_2026(["X", "3", "C", "S2", "3.5", "1", "1", "emdl"])
        self.assertIn("ANALISIS SISMICO E.030 2026", salida)

    def test_cli_separacion_nueva_formula(self) -> None:
        salida = handle_sismo_separacion(["10", "4", "s3", "0.01", "0.01"])
        self.assertIn("0.02·Z·S·h", salida)
        self.assertIn("0.1080", salida)

    @patch("axis.cli.sismo_handlers_2026.handle_sismo_calcular", return_value="OK")
    def test_cli_rapido_reporta_irregularidad_extrema(self, mock_calcular) -> None:
        salida = handle_sismo_rapido(["X", "3", "B", "S2", "8", "concreto", "reb", "tors"])
        self.assertIn("Irregularidad extrema detectada: Si", salida)
        self.assertIn("no esta permitida", salida)
        mock_calcular.assert_called_once()


if __name__ == "__main__":
    unittest.main()
