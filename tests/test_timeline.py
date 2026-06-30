"""
Timeline: la evolución sale del MISMO scoring que el leaderboard.

Invariante clave (evita que vuelva el cálculo paralelo): el último punto de cada
participante == su `total` en el leaderboard. Además: los hitos pasados salen de
construir_puntajes truncado, y no se grafican rondas no jugadas.
"""
import unittest

from utils.data_loader import construir_puntajes
from utils.timeline import construir_evolucion
from tests._builders import df_resultados, partido, df_apuestas, apuesta, total_results


def _escenario():
    # Grupos jugados (ARG-BRA 1-0) + 16avos jugado (ARG-GER 1-0, ARG gana -> 8vos).
    resultados = df_resultados([
        partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT"),
        partido("ARG", "GER", 1, 0, ronda="Round of 32", estado="FT"),
        partido("MEX", "USA", None, None, ronda="Round of 16", estado="NS"),  # 8vos futuro
    ])
    apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
    cats_todos = {"P1": {}}
    trs = {"P1": total_results(equipos_por_ronda={"16vos": {"ARG"}, "8vos": {"ARG"}})}
    todos, *_ = construir_puntajes(resultados, apuestas, cats_todos, trs, {})
    return resultados, apuestas, cats_todos, trs, todos


class TestTimeline(unittest.TestCase):
    def test_ultimo_punto_igual_total_leaderboard(self):  # INVARIANTE
        resultados, apuestas, cats_todos, trs, todos = _escenario()
        df, hitos = construir_evolucion(resultados, apuestas, cats_todos, trs, todos, {})
        for pj in todos:
            ultimo = df[df["participante"] == pj["participante"]].sort_values("fecha").iloc[-1]
            self.assertEqual(int(ultimo["puntos"]), pj["total"])

    def test_total_esperado(self):
        # grupos +2 (exacto) + 16vos +1 + 8vos +3 (ARG ganó su 16avos) = 6.
        _, _, _, _, todos = _escenario()
        self.assertEqual(todos[0]["total"], 6)

    def test_no_grafica_rondas_no_jugadas(self):
        resultados, apuestas, cats_todos, trs, todos = _escenario()
        df, hitos = construir_evolucion(resultados, apuestas, cats_todos, trs, todos, {})
        eventos = set(df["evento"])
        # 8vos está NS -> no aparece; solo Inicio / Fin Grupos / 16vos.
        self.assertEqual(eventos, {"Inicio Grupos", "Fin Grupos", "16vos"})
        self.assertNotIn("8vos", [rk for (_, rk, _) in hitos])

    def test_hito_pasado_desde_scoring_truncado(self):
        # El hito "Fin Grupos" == construir_puntajes sobre solo los grupos.
        resultados, apuestas, cats_todos, trs, todos = _escenario()
        df, _ = construir_evolucion(resultados, apuestas, cats_todos, trs, todos, {})
        solo_grupos = resultados[resultados["ronda"].str.contains("Group", na=False)]
        esperado, *_ = construir_puntajes(solo_grupos, apuestas, cats_todos, trs, {})
        fin_grupos = df[(df["participante"] == "P1") & (df["evento"] == "Fin Grupos")].iloc[0]
        self.assertEqual(int(fin_grupos["puntos"]), esperado[0]["total"])
        self.assertEqual(int(fin_grupos["puntos"]), 2)  # solo los +2 de grupos


if __name__ == "__main__":
    unittest.main()
