"""Función maestra (calcular_puntuacion_total) y armado del leaderboard."""
import unittest

from utils.scoring import calcular_puntuacion_total, generar_leaderboard
from tests._builders import df_apuestas, df_resultados, partido, apuesta, total_results


def _puntaje(participante, glp, gvp, pred_16vos=None):
    """Puntaje de un participante para un único partido ARG-BRA 1-0 FT."""
    apuestas = df_apuestas([apuesta(participante, "ARG", "BRA", glp, gvp)])
    resultados = df_resultados([partido("ARG", "BRA", 1, 0, estado="FT")])
    tr = total_results(equipos_por_ronda={"16vos": set(pred_16vos)} if pred_16vos else {})
    return calcular_puntuacion_total(
        participante=participante,
        apuestas_grupos=apuestas,
        categorias_pred={},
        total_results_pred=tr,
        resultados_reales=resultados,
        equipos_reales_por_ronda={"16vos": {"ARG"}},
        categorias_reales={},
    )


class TestPuntuacionTotal(unittest.TestCase):
    def test_suma_componentes_grupos_y_elim(self):
        p = _puntaje("ALTO", 1, 0, pred_16vos={"ARG"})
        self.assertEqual(p["pts_grupos"], 2)        # ganador + exacto
        self.assertEqual(p["pts_eliminatorias"], 1)  # ARG en 16vos
        self.assertEqual(p["total"], 3)

    def test_participante_sin_aciertos_cero(self):
        p = _puntaje("BAJO", 0, 1)  # marcador al revés, sin pred de elim
        self.assertEqual(p["total"], 0)

    def test_ajuste_manual_ALDO_resta_10(self):
        p = _puntaje("ALDO", 0, 1)  # base 0
        self.assertEqual(p["total"], -10)
        self.assertTrue(any("ajuste manual" in r.lower() for r in p["razones_penalidad"]))


class TestLeaderboard(unittest.TestCase):
    def test_orden_por_total_desc_y_posiciones(self):
        alto = _puntaje("ALTO", 1, 0, pred_16vos={"ARG"})  # total 3
        bajo = _puntaje("BAJO", 0, 1)                        # total 0
        lb = generar_leaderboard([bajo, alto])  # desordenados a propósito
        self.assertEqual(list(lb["Participante"]), ["ALTO", "BAJO"])
        self.assertEqual(list(lb["Posición"]), [1, 2])

    def test_columnas_esperadas_presentes(self):
        lb = generar_leaderboard([_puntaje("ALTO", 1, 0)])
        for col in ["Posición", "Participante", "Total", "Grupos", "Eliminatorias",
                    "Campeón", "3ero", "Especiales", "Penalidades"]:
            self.assertIn(col, lb.columns)


if __name__ == "__main__":
    unittest.main()
