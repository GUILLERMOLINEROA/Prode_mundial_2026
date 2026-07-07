"""
Timeline diario: la evolución sale del MISMO scoring que el leaderboard, con un punto
por día con partidos terminados, y con el +N del pase REPARTIDO por día de partido.

Invariantes clave (evitan que vuelva el cálculo paralelo / los puntos fantasma):
 - Con la ronda en curso COMPLETA (todos sus partidos terminados) y sin vivo, el último
   punto de cada participante == su `total` (leaderboard).
 - Con la ronda en curso INCOMPLETA, el extremo == `total` - (pase aún no repartido):
   el +N de los equipos clasificados cuyo partido de esa ronda todavía no se jugó NO
   está en la curva (aparece el día de su partido). Cambio de invariante a propósito:
   antes era "siempre último == total"; ahora vale solo con la ronda completa.
 - Granularidad diaria (más de un punto entre hitos de fase).
 - No grafica rondas no jugadas (nada después del último día con partidos terminados).
 - Una penalidad aparece como bajón el día en que su partido detonante terminó (las
   penalidades NO se reparten: usan el cuadro con presencia, caen en su día real).
"""
import unittest
from unittest.mock import patch

import pandas as pd

from utils.data_loader import construir_puntajes
from utils.timeline import construir_evolucion
from tests._builders import (df_resultados, partido, df_apuestas, apuesta,
                             total_results, grupos_72)


def _con_total(resultados, apuestas, cats_todos, trs):
    todos, *_ = construir_puntajes(resultados, apuestas, cats_todos, trs, {})
    return todos


class TestTimelineDiario(unittest.TestCase):
    def test_invariante_ronda_completa_ultimo_igual_total(self):
        # Ronda completa: el único 16avos está FT (no quedan partidos de esa ronda sin
        # jugar) -> el último punto == total del leaderboard.
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
            partido("GER", "FRA", 2, 0, ronda="Group Stage - 2", estado="FT", fecha="2026-06-13"),
            partido("ARG", "MEX", 1, 0, ronda="Round of 32", estado="FT", fecha="2026-07-01"),
        ])
        apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
        cats = {"P1": {}}
        trs = {"P1": total_results(equipos_por_ronda={"16vos": {"ARG"}, "8vos": {"ARG"}})}
        todos = _con_total(resultados, apuestas, cats, trs)
        df, fases = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        for pj in todos:
            ultimo = df[df["participante"] == pj["participante"]].sort_values("fecha").iloc[-1]
            self.assertEqual(int(ultimo["puntos"]), pj["total"])

    def test_invariante_ronda_en_curso_extremo_es_total_menos_pase_no_repartido(self):
        # 72 grupos FT (clasificados publicados) + 16avos EN CURSO: G01-G02 jugado (FT),
        # G03-G04 sin jugar (NS). P clasificó G01 y G03 en 16avos (ambos en el cuadro).
        # Leaderboard (presencia): +1 por G01 y +1 por G03 = +2.
        # Curva (solo terminados): solo el +1 de G01 (su partido se jugó); el +1 de G03
        # aún no se reparte -> extremo == total - 1.
        resultados = df_resultados(grupos_72(estado="FT") + [
            partido("G01", "G02", 1, 0, ronda="Round of 32", estado="FT", fecha="2026-07-01"),
            partido("G03", "G04", None, None, ronda="Round of 32", estado="NS", fecha="2026-07-02"),
        ])
        apuestas = df_apuestas([])
        cats = {"P1": {}}
        trs = {"P1": total_results(equipos_por_ronda={"16vos": {"G01", "G03"}})}
        todos = _con_total(resultados, apuestas, cats, trs)
        self.assertEqual(todos[0]["total"], 2)  # leaderboard cuenta los 2 clasificados
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        ultimo = int(df[df["participante"] == "P1"].sort_values("fecha").iloc[-1]["puntos"])
        self.assertEqual(ultimo, 1)                       # solo el pase ya jugado
        self.assertEqual(ultimo, todos[0]["total"] - 1)   # diferencia == pase no repartido

    def test_total_esperado(self):
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
            partido("ARG", "MEX", 1, 0, ronda="Round of 32", estado="FT", fecha="2026-07-01"),
        ])
        apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
        cats = {"P1": {}}
        trs = {"P1": total_results(equipos_por_ronda={"16vos": {"ARG"}, "8vos": {"ARG"}})}
        todos = _con_total(resultados, apuestas, cats, trs)
        # grupos +2 + 16vos +1 + 8vos +3 = 6
        self.assertEqual(todos[0]["total"], 6)
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        self.assertEqual(int(df[df["participante"] == "P1"].sort_values("fecha").iloc[-1]["puntos"]), 6)

    def test_granularidad_diaria(self):
        # 3 días de grupos -> al menos 3 puntos-fecha (no solo hitos de fase).
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
            partido("ARG", "CHI", 2, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-15"),
            partido("BRA", "CHI", 1, 1, ronda="Group Stage - 1", estado="FT", fecha="2026-06-18"),
        ])
        apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
        cats = {"P1": {}}
        trs = {"P1": total_results()}
        todos = _con_total(resultados, apuestas, cats, trs)
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        dias = df[df["evento"] != "Inicio Grupos"]["fecha"].nunique()
        self.assertGreaterEqual(dias, 3)

    def test_no_grafica_rondas_no_jugadas(self):
        # Un 8vos NS en el futuro NO genera punto; el último día es el del 16avos FT.
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
            partido("ARG", "MEX", 1, 0, ronda="Round of 32", estado="FT", fecha="2026-07-01"),
            partido("ARG", "USA", None, None, ronda="Round of 16", estado="NS", fecha="2026-07-05"),
        ])
        apuestas = df_apuestas([apuesta("P1", "ARG", "BRA", 1, 0)])
        cats = {"P1": {}}
        trs = {"P1": total_results(equipos_por_ronda={"16vos": {"ARG"}})}
        todos = _con_total(resultados, apuestas, cats, trs)
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        ult = df[df["evento"] != "Inicio Grupos"]["fecha"].max()
        self.assertEqual(pd.Timestamp(ult), pd.Timestamp("2026-07-01", tz="UTC"))

    def test_penalidad_campeon_es_bajon_en_su_dia(self):
        # P2 puso campeón GER; GER pierde su 16avos el 02/07 -> -20 ese día.
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
            partido("X", "GER", 1, 0, ronda="Round of 32", estado="FT", fecha="2026-07-02"),  # GER eliminado
        ])
        apuestas = df_apuestas([])
        cats = {"P2": {"Campeon": "GER"}}
        trs = {"P2": total_results(campeon="GER")}
        todos = _con_total(resultados, apuestas, cats, trs)
        self.assertEqual(todos[0]["total"], -20)  # campeón eliminado antes de cuartos
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        serie = df[df["participante"] == "P2"].sort_values("fecha")
        # antes del 02/07 estaba en 0; el 02/07 cae a -20.
        pre = serie[serie["fecha"] < pd.Timestamp("2026-07-02", tz="UTC")]["puntos"].iloc[-1]
        post = serie[serie["fecha"] == pd.Timestamp("2026-07-02", tz="UTC")]["puntos"].iloc[0]
        self.assertEqual(int(pre), 0)
        self.assertEqual(int(post), -20)

    @patch.dict("utils.scoring.AJUSTES_MANUALES", {"TESTPEN": -10}, clear=True)
    def test_ajuste_manual_arranca_en_su_valor(self):
        # El punto inicial arranca en el ajuste manual. Testea el MECANISMO con un código
        # sintético (TESTPEN); no depende de ninguna sanción real cargada en producción.
        resultados = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT", fecha="2026-06-12"),
        ])
        apuestas = df_apuestas([apuesta("TESTPEN", "ARG", "BRA", 0, 1)])  # falla -> 0 de grupos
        cats = {"TESTPEN": {}}
        trs = {"TESTPEN": total_results()}
        todos = _con_total(resultados, apuestas, cats, trs)
        df, _ = construir_evolucion(resultados, apuestas, cats, trs, todos, {})
        inicio = df[(df["participante"] == "TESTPEN") & (df["evento"] == "Inicio Grupos")].iloc[0]
        self.assertEqual(int(inicio["puntos"]), -10)


if __name__ == "__main__":
    unittest.main()
