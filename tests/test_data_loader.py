"""
data_loader: ganador de eliminatoria, armado de equipos_reales_por_ronda,
campeón/3er puesto, y el builder compartido. Incluye regresiones:
 - #5 ganador propaga a la ronda siguiente (penales por tanda, grupos no propaga, en-curso no).
 - #6 anti-doble-conteo: ganador temprano + fixture de la API -> +N una sola vez.
 - #7 app y mail consistentes: construir_puntajes es la única fuente, determinística.
"""
import unittest

from utils.data_loader import (
    _ganador_eliminatoria, extraer_equipos_reales_por_ronda,
    determinar_campeon_y_tercero, construir_puntajes,
)
from utils.scoring import calcular_puntos_eliminatorias, calcular_puntuacion_total, PUNTOS
from tests._builders import df_resultados, partido, df_apuestas, apuesta, total_results


class TestGanadorEliminatoria(unittest.TestCase):
    def test_gana_por_marcador(self):
        self.assertEqual(_ganador_eliminatoria(partido("ARG", "BRA", 2, 1, estado="FT")), "ARG")

    def test_gana_por_penales(self):
        p = partido("ARG", "BRA", 1, 1, estado="PEN", pen_l=4, pen_v=2)
        self.assertEqual(_ganador_eliminatoria(p), "ARG")

    def test_penales_gana_visitante(self):
        p = partido("ARG", "BRA", 1, 1, estado="PEN", pen_l=2, pen_v=4)
        self.assertEqual(_ganador_eliminatoria(p), "BRA")

    def test_empate_sin_penales_none(self):
        self.assertIsNone(_ganador_eliminatoria(partido("ARG", "BRA", 1, 1, estado="FT")))

    def test_dato_faltante_none(self):
        self.assertIsNone(_ganador_eliminatoria(partido("ARG", "BRA", None, None, estado="FT")))


class TestExtraerEquiposReales(unittest.TestCase):
    def test_ganador_propaga_penales_grupos_y_envivo(self):  # REGRESIÓN #5
        res = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Round of 32", estado="FT"),       # ARG -> 8vos
            partido("GER", "FRA", 1, 1, ronda="Round of 32", estado="PEN",
                    pen_l=5, pen_v=4),                                            # GER (tanda) -> 8vos
            partido("ZZZ", "WWW", 1, 0, ronda="Group Stage - 1", estado="FT"),   # grupos: NO propaga
            partido("LIVE", "DEAD", 2, 0, ronda="Round of 32", estado="2H"),     # en curso: NO propaga
        ])
        eqr = extraer_equipos_reales_por_ronda(res)
        self.assertIn("ARG", eqr["8vos"])
        self.assertIn("GER", eqr["8vos"])      # ganó la tanda
        self.assertNotIn("FRA", eqr["8vos"])   # perdió la tanda (marcador empatado)
        self.assertNotIn("ZZZ", eqr["8vos"])   # ganó en grupos, no propaga
        self.assertNotIn("LIVE", eqr["8vos"])  # partido en curso

    def test_anti_doble_conteo_con_fixture_api(self):  # REGRESIÓN #6
        # ARG gana su 16avos (propaga a 8vos) Y la API ya publicó el R16 con ARG.
        res = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Round of 32", estado="FT"),
            partido("ARG", "MEX", None, None, ronda="Round of 16", estado="NS"),
        ])
        eqr = extraer_equipos_reales_por_ronda(res)
        self.assertIn("ARG", eqr["8vos"])
        # El scoring cuenta el +3 una sola vez (es un set, no se duplica).
        _, por_ronda, _ = calcular_puntos_eliminatorias(
            total_results(equipos_por_ronda={"8vos": {"ARG"}}), eqr)
        self.assertEqual(por_ronda["8vos"], PUNTOS["8vos"])

    def test_propaga_por_ronda_completa(self):
        res = df_resultados([
            partido("A", "B", 1, 0, ronda="Round of 32", estado="FT"),       # -> 8vos
            partido("C", "D", 2, 0, ronda="Round of 16", estado="FT"),       # -> 4tos
            partido("E", "F", 1, 0, ronda="Quarter-finals", estado="FT"),    # -> semis
            partido("G", "H", 3, 0, ronda="Semi-finals", estado="FT"),       # -> final
        ])
        eqr = extraer_equipos_reales_por_ronda(res)
        self.assertIn("A", eqr["8vos"])
        self.assertIn("C", eqr["4tos"])
        self.assertIn("E", eqr["semis"])
        self.assertIn("G", eqr["final"])


class TestCampeonTercero(unittest.TestCase):
    def test_campeon_y_tercero(self):
        res = df_resultados([
            partido("ARG", "FRA", 2, 1, ronda="Final", estado="FT"),
            partido("CRO", "MAR", 2, 1, ronda="3rd Place Final", estado="FT"),
        ])
        campeon, tercero = determinar_campeon_y_tercero(res)
        self.assertEqual(campeon, "ARG")
        self.assertEqual(tercero, "CRO")

    def test_campeon_por_penales(self):
        res = df_resultados([partido("ARG", "FRA", 1, 1, ronda="Final", estado="PEN",
                                     pen_l=4, pen_v=2)])
        campeon, _ = determinar_campeon_y_tercero(res)
        self.assertEqual(campeon, "ARG")

    def test_sin_final_vacio(self):
        res = df_resultados([partido("ARG", "FRA", 1, 0, ronda="Semi-finals", estado="FT")])
        campeon, tercero = determinar_campeon_y_tercero(res)
        self.assertEqual((campeon, tercero), ("", ""))


class TestConstruirPuntajes(unittest.TestCase):
    def _datos(self):
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT"),
            partido("ARG", "GER", 1, 0, ronda="Round of 32", estado="FT"),  # ARG gana -> 8vos
        ])
        apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
        cats_todos = {"P1": {}}
        trs = {"P1": total_results(equipos_por_ronda={"16vos": {"ARG"}, "8vos": {"ARG"}})}
        return resultados, apuestas, cats_todos, trs

    def test_app_y_mail_consistentes(self):  # REGRESIÓN #7
        resultados, apuestas, cats_todos, trs = self._datos()
        a = construir_puntajes(resultados, apuestas, cats_todos, trs, {})
        b = construir_puntajes(resultados, apuestas, cats_todos, trs, {})
        # Determinístico: mismos datos -> mismos puntajes por ambos caminos.
        self.assertEqual(a[0][0]["total"], b[0][0]["total"])
        # Y no diverge de la primitiva de scoring con el mismo equipos_reales.
        todos, _campeon, _tercero, equipos_reales = a
        directo = calcular_puntuacion_total(
            participante="P1", apuestas_grupos=apuestas, categorias_pred={},
            total_results_pred=trs["P1"], resultados_reales=resultados,
            equipos_reales_por_ronda=equipos_reales, categorias_reales={})
        self.assertEqual(todos[0]["total"], directo["total"])

    def test_total_esperado(self):
        resultados, apuestas, cats_todos, trs = self._datos()
        todos, *_ = construir_puntajes(resultados, apuestas, cats_todos, trs, {})
        # grupos +2 (exacto) + 16vos +1 + 8vos +3 (ARG ganó su 16avos) = 6
        self.assertEqual(todos[0]["total"], 6)


if __name__ == "__main__":
    unittest.main()
