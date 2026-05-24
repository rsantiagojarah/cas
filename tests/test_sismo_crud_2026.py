"""Tests persistencia y CRUD sismo E.030 2026."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from axis.cli.sismo_handlers_2026 import handle_sismo_2026, handle_sismo_calcular
from axis.sismico.sismo_persistencia_2026 import (
    STORE_SISMO_2026,
    guardar_analisis_sismo,
    listar_analisis_sismo,
    obtener_analisis_sismo,
)


def _resultado_minimo() -> dict:
    return {
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
        "r": 8.0,
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


class TestSismoCrud2026(unittest.TestCase):
    def test_list_show_delete_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            parametros = {
                "modo": "manual",
                "sentido": "X",
                "zona": 3,
                "categoria": "C",
                "perfil": "s2",
                "r0": 8.0,
                "ia": 1.0,
                "ip": 1.0,
                "material": "concreto_armado",
                "nombre": "prueba",
            }
            aid = guardar_analisis_sismo(
                path, parametros, ["# Paso 1\n"], "Salida de prueba X"
            )
            self.assertEqual(len(listar_analisis_sismo(path)), 1)
            with patch("axis.cli.sismo_handlers_2026._get_project_path", return_value=path):
                lista = handle_sismo_2026(["list"])
                self.assertIn(aid, lista)
                self.assertIn("prueba", lista)
                show = handle_sismo_2026(["show", aid])
                self.assertIn("Salida de prueba X", show)
                self.assertIn("Sentido X", show)
                reporte = handle_sismo_2026(["report", "memoria"])
                self.assertIn("REPORTE DE ANALISIS SISMICO", reporte)
                self.assertTrue((path / "results" / "sismo_reporte_2026_memoria.md").exists())
                borrado = handle_sismo_2026(["delete", aid])
                self.assertIn("eliminado", borrado)
                self.assertEqual(listar_analisis_sismo(path), [])

    @patch("axis.cli.sismo_handlers_2026._get_project_path")
    @patch("axis.data.etabs_table_reader.clear_table_cache")
    @patch("axis.cli.sismo_handlers_2026.ejecutar_analisis_sismico")
    def test_calcular_guarda_automaticamente(self, mock_ejecutar, _cache, mock_path) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            mock_path.return_value = path
            mock_ejecutar.return_value = _resultado_minimo()
            salida = handle_sismo_calcular(["X", "3", "C", "S2", "8", "1", "1", "concreto"])
            self.assertIn("Guardado (id:", salida)
            items = listar_analisis_sismo(path)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["parametros"]["sentido"], "X")

    @patch("axis.cli.sismo_handlers_2026._get_project_path")
    @patch("axis.data.etabs_table_reader.clear_table_cache")
    @patch("axis.cli.sismo_handlers_2026.ejecutar_analisis_sismico")
    def test_edit_actualiza_mismo_id(self, mock_ejecutar, _cache, mock_path) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            mock_path.return_value = path
            mock_ejecutar.return_value = _resultado_minimo()
            handle_sismo_calcular(["X", "3", "C", "S2", "8", "1", "1", "concreto"])
            aid = listar_analisis_sismo(path)[0]["id"]
            salida = handle_sismo_2026(["edit", aid, "Y", "3", "C", "S2", "8", "1", "1", "concreto"])
            self.assertIn("Actualizado", salida)
            rec = obtener_analisis_sismo(path, aid)
            self.assertIsNotNone(rec)
            assert rec is not None
            self.assertEqual(rec["parametros"]["sentido"], "Y")
            self.assertEqual(len(listar_analisis_sismo(path)), 1)

    def test_help_incluye_persistencia(self) -> None:
        salida = handle_sismo_2026([])
        self.assertIn("cas sismo 2026 list", salida)
        self.assertIn("cas sismo 2026 report", salida)


if __name__ == "__main__":
    unittest.main()
