"""Puntos por acertar campeón (+20) y 3er puesto (+5)."""
import unittest

from utils.scoring import calcular_puntos_campeon_y_tercero, PUNTOS
from tests._builders import total_results


class TestCampeonTercero(unittest.TestCase):
    def test_acierto_campeon_suma_20(self):
        c, t = calcular_puntos_campeon_y_tercero(total_results(campeon="ARG"), "ARG", "")
        self.assertEqual(c, PUNTOS["campeon"])
        self.assertEqual(t, 0)

    def test_acierto_tercero_suma_5(self):
        c, t = calcular_puntos_campeon_y_tercero(total_results(tercero="CRO"), "", "CRO")
        self.assertEqual(t, PUNTOS["3ero"])
        self.assertEqual(c, 0)

    def test_case_insensitive(self):
        c, _ = calcular_puntos_campeon_y_tercero(total_results(campeon="argentina"), "Argentina", "")
        self.assertEqual(c, PUNTOS["campeon"])

    def test_no_acierto_no_suma(self):
        c, t = calcular_puntos_campeon_y_tercero(total_results(campeon="BRA", tercero="GER"), "ARG", "CRO")
        self.assertEqual((c, t), (0, 0))

    def test_pred_vacia_no_suma(self):
        c, t = calcular_puntos_campeon_y_tercero(total_results(), "ARG", "CRO")
        self.assertEqual((c, t), (0, 0))

    def test_real_vacio_no_suma(self):
        c, t = calcular_puntos_campeon_y_tercero(total_results(campeon="ARG", tercero="CRO"), "", "")
        self.assertEqual((c, t), (0, 0))


if __name__ == "__main__":
    unittest.main()
