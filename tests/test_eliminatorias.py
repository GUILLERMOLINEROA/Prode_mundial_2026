"""Puntos de eliminatorias por ronda desde equipos_reales_por_ronda."""
import unittest

from utils.scoring import calcular_puntos_eliminatorias, PUNTOS
from tests._builders import total_results


class TestPuntosEliminatorias(unittest.TestCase):
    def _por_ronda(self, pred, real):
        total, por_ronda, _ = calcular_puntos_eliminatorias(total_results(equipos_por_ronda=pred), real)
        return total, por_ronda

    def test_acierto_16vos_suma_1(self):
        total, pr = self._por_ronda({"16vos": {"ARG"}}, {"16vos": {"ARG"}})
        self.assertEqual(pr["16vos"], PUNTOS["16vos"])
        self.assertEqual(total, 1)

    def test_acierto_8vos_suma_3(self):
        _, pr = self._por_ronda({"8vos": {"ARG"}}, {"8vos": {"ARG"}})
        self.assertEqual(pr["8vos"], PUNTOS["8vos"])

    def test_acierto_4tos_suma_6(self):
        _, pr = self._por_ronda({"4tos": {"ARG"}}, {"4tos": {"ARG"}})
        self.assertEqual(pr["4tos"], PUNTOS["4tos"])

    def test_acierto_semis_suma_10(self):
        _, pr = self._por_ronda({"semis": {"ARG"}}, {"semis": {"ARG"}})
        self.assertEqual(pr["semis"], PUNTOS["semis"])

    def test_acierto_final_suma_15(self):
        _, pr = self._por_ronda({"final": {"ARG"}}, {"final": {"ARG"}})
        self.assertEqual(pr["final"], PUNTOS["final"])

    def test_acumulado_multironda(self):
        pred = {"16vos": {"ARG"}, "8vos": {"ARG"}}
        real = {"16vos": {"ARG"}, "8vos": {"ARG"}}
        total, pr = self._por_ronda(pred, real)
        self.assertEqual(pr["16vos"], 1)
        self.assertEqual(pr["8vos"], 3)
        self.assertEqual(total, 4)

    def test_pred_fuera_del_set_no_suma(self):
        _, pr = self._por_ronda({"8vos": {"ARG"}}, {"8vos": {"BRA"}})
        self.assertEqual(pr["8vos"], 0)

    def test_sets_vacios_no_suman(self):
        total, _ = self._por_ronda({}, {})
        self.assertEqual(total, 0)

    def test_varios_equipos_misma_ronda(self):
        _, pr = self._por_ronda({"8vos": {"ARG", "BRA"}}, {"8vos": {"ARG", "BRA", "GER"}})
        self.assertEqual(pr["8vos"], 2 * PUNTOS["8vos"])


if __name__ == "__main__":
    unittest.main()
