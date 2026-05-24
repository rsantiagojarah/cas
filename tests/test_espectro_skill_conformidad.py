"""Conformidad del espectro E.030 2026 con SKILL / Tabla 6 (analisis dinamico)."""

from __future__ import annotations

import unittest

from axis.sismico.espectro_etabs_2026 import PERIODOS_ETABS, generar_filas_sa
from axis.sismico.etapa1_peligro_2026 import factor_amplificacion_c


def _c_skill_dinamico(t: float, tp: float, tl: float) -> float:
    """Referencia directa Tabla 6 SKILL (sin atajos de implementacion)."""
    if t <= 0:
        return 1.0
    if t < 0.2 * tp:
        return 1.0 + 7.5 * (t / tp)
    if t <= tp:
        return 2.5
    if t < tl:
        return 2.5 * (tp / t)
    return 2.5 * (tp * tl / (t * t))


class TestEspectroSkillConformidad(unittest.TestCase):
    tp = 0.9
    tl = 1.6

    def test_factor_c_coincide_con_tabla_6_skill(self) -> None:
        casos = [
            0.0, 0.05, 0.1, 0.18, 0.2, 0.5, 0.9, 1.0, 1.2, 1.5, 1.6, 1.7, 2.0, 5.0, 15.0,
        ]
        for t in casos:
            esperado = _c_skill_dinamico(t, self.tp, self.tl)
            obtenido = factor_amplificacion_c(t, self.tp, self.tl)
            self.assertAlmostEqual(obtenido, esperado, places=9, msg=f"T={t}")

    def test_continuidad_en_fronteras_tabla_6(self) -> None:
        tp, tl = self.tp, self.tl
        t_02tp = 0.2 * tp
        self.assertAlmostEqual(
            factor_amplificacion_c(t_02tp - 1e-9, tp, tl),
            factor_amplificacion_c(t_02tp, tp, tl),
        )
        self.assertAlmostEqual(factor_amplificacion_c(tp, tp, tl), 2.5)
        self.assertAlmostEqual(
            factor_amplificacion_c(tp + 1e-9, tp, tl),
            2.5 * tp / (tp + 1e-9),
            places=5,
        )
        c_tl = 2.5 * tp * tl / (tl * tl)
        self.assertAlmostEqual(factor_amplificacion_c(tl, tp, tl), c_tl)

    def test_tramo_1_crece_monotono_hasta_plateau(self) -> None:
        tp = self.tp
        z, u, s, r = 0.35, 1.0, 1.2, 3.0
        periodos = [t for t in PERIODOS_ETABS if t <= tp]
        sa_prev = -1.0
        for t in periodos:
            sa = z * u * s * factor_amplificacion_c(t, tp, self.tl) / r
            self.assertGreaterEqual(sa, sa_prev - 1e-9, msg=f"Sa baja en T={t}")
            sa_prev = sa
        self.assertAlmostEqual(sa_prev, 0.35, places=6)

    def test_caso_usuario_albanileria_tabla_completa(self) -> None:
        z, u, s, tp, tl, r = 0.35, 1.0, 1.2, 0.9, 1.6, 3.0
        referencia = {
            0.0: 0.14,
            0.1: 0.256667,
            0.2: 0.35,
            0.3: 0.35,
            0.9: 0.35,
            1.0: 0.315,
            1.2: 0.2625,
            1.5: 0.21,
            1.7: 0.174394,
            2.0: 0.126,
            2.5: 0.08064,
            3.0: 0.056,
            15.0: 0.00224,
        }
        filas = {f["Periodo"]: f["Sa/g"] for f in generar_filas_sa(z, u, s, tp, tl, r)}
        for t, sa_ref in referencia.items():
            self.assertAlmostEqual(filas[t], sa_ref, places=6, msg=f"T={t}")

    def test_sa_formula_skill_seccion_31(self) -> None:
        z, u, s, tp, tl, r = 0.35, 1.0, 1.2, 0.9, 1.6, 3.0
        t = 1.7
        c = _c_skill_dinamico(t, tp, tl)
        esperado = round(z * u * s * c / r, 6)
        fila = next(f for f in generar_filas_sa(z, u, s, tp, tl, r) if f["Periodo"] == t)
        self.assertEqual(fila["Sa/g"], esperado)

    def test_modo_estatico_no_afecta_espectro_etabs(self) -> None:
        self.assertAlmostEqual(factor_amplificacion_c(0.0, 0.9, 1.6), 1.0)
        self.assertAlmostEqual(factor_amplificacion_c(0.0, 0.9, 1.6, modo_estatico=True), 2.5)

    def test_plateau_hasta_tp(self) -> None:
        tp, tl = 0.9, 1.6
        for t in (0.2, 0.5, 0.9):
            self.assertEqual(factor_amplificacion_c(t, tp, tl), 2.5)

    def test_rechaza_tl_menor_igual_tp(self) -> None:
        with self.assertRaises(ValueError):
            generar_filas_sa(0.35, 1.0, 1.2, 0.9, 0.9, 3.0)


if __name__ == "__main__":
    unittest.main()
