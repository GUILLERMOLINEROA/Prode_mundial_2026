"""
Categorías especiales (utils/special_categories). Incluye regresiones:
 - #2 Decepción se resuelve desde el cuadro real (no un conteo de standings).
 - #3 Decepción no degenerada: el clase-1 ELIMINADO es la decepción, no uno que avanzó.

calcular_todas_las_categorias lee data/equipos_clase.csv vía cargar_equipos_clase();
para no depender del CSV real, los tests lo monkeypatchean con datos sintéticos.
"""
import unittest
from unittest.mock import patch

from utils.special_categories import (
    grupos_finalizados, torneo_finalizado, calcular_fase_maxima_por_equipo,
    calcular_tabla_grupos, determinar_decepcion, determinar_revelacion,
    determinar_mejor_primera_fase, determinar_peor_equipo, calcular_todas_las_categorias,
)
from tests._builders import df_resultados, partido, grupos_72, clase_df


def _mundial_post_grupos(con_bracket=True):
    """72 grupos FT (incluye 'Uruguay') + 16avos publicados con 32 equipos (sin Uruguay)."""
    import itertools
    teams = ["Uruguay"] + [f"T{i:02d}" for i in range(1, 48)]  # 48 equipos
    filas = []
    for g in range(12):
        grupo = teams[4 * g: 4 * g + 4]
        for a, b in itertools.combinations(range(4), 2):
            filas.append(partido(grupo[a], grupo[b], 1, 0,
                                  ronda=f"Group Stage - {g+1}", estado="FT"))
    if con_bracket:
        clasificados = teams[16:48]  # 32 equipos, Uruguay (teams[0]) afuera
        for i in range(16):
            filas.append(partido(clasificados[2 * i], clasificados[2 * i + 1],
                                 None, None, ronda="Round of 32", estado="NS"))
    return df_resultados(filas)


class TestGruposFinalizados(unittest.TestCase):
    def test_72_FT_true(self):
        self.assertTrue(grupos_finalizados(df_resultados(grupos_72(estado="FT"))))

    def test_menos_de_72_false(self):
        self.assertFalse(grupos_finalizados(df_resultados(grupos_72()[:71])))

    def test_alguno_NS_false(self):
        filas = grupos_72()
        filas[0]["estado"] = "NS"
        self.assertFalse(grupos_finalizados(df_resultados(filas)))

    def test_vacio_false(self):
        import pandas as pd
        self.assertFalse(grupos_finalizados(pd.DataFrame()))


class TestTorneoFinalizado(unittest.TestCase):
    def test_con_final_FT_true(self):
        res = df_resultados([partido("ARG", "FRA", 3, 2, ronda="Final", estado="FT")])
        self.assertTrue(torneo_finalizado(res))

    def test_sin_final_false(self):
        res = df_resultados([partido("ARG", "FRA", 3, 2, ronda="Semi-finals", estado="FT")])
        self.assertFalse(torneo_finalizado(res))


class TestFaseMaximaYTabla(unittest.TestCase):
    def test_fase_maxima_por_ronda(self):
        res = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT"),
            partido("ARG", "GER", 2, 1, ronda="Round of 32", estado="FT"),
        ])
        fm = calcular_fase_maxima_por_equipo(res)
        self.assertEqual(fm["ARG"], 1)   # llegó a 16avos
        self.assertEqual(fm["BRA"], 0)   # solo grupos

    def test_campeon_fase_6(self):
        res = df_resultados([partido("ARG", "FRA", 3, 2, ronda="Final", estado="FT")])
        fm = calcular_fase_maxima_por_equipo(res)
        self.assertEqual(fm["ARG"], 6)

    def test_tabla_grupos_puntos(self):
        res = df_resultados([
            partido("ARG", "BRA", 1, 0, ronda="Group Stage - 1", estado="FT"),
            partido("ARG", "GER", 2, 0, ronda="Group Stage - 1", estado="FT"),
        ])
        tabla = calcular_tabla_grupos(res)
        arg = tabla[tabla["equipo"] == "ARG"].iloc[0]
        self.assertEqual(arg["pts"], 6)


class TestDeterminarDecepcion(unittest.TestCase):
    def test_menor_fase_max(self):
        ec = clase_df([(1, "ARG", 1, 1), (17, "URU", 1, 2), (6, "BRA", 1, 1)])
        fm = {"ARG": 3, "BRA": 3, "URU": 0}
        self.assertEqual(determinar_decepcion(ec, fm, None), "URU")

    def test_desempate_por_sub_y_ranking(self):
        ec = clase_df([(1, "ARG", 1, 1), (17, "URU", 1, 2)])
        fm = {"ARG": 0, "URU": 0}  # ambos eliminados -> gana sub menor (ARG sub1)
        self.assertEqual(determinar_decepcion(ec, fm, None), "ARG")

    def test_sin_clase1_devuelve_vacio(self):
        ec = clase_df([(8, "MAR", 2, None)])
        self.assertEqual(determinar_decepcion(ec, {"MAR": 0}, None), "")


class TestDeterminarRevelacion(unittest.TestCase):
    def test_clase4_que_paso_de_grupos(self):
        ec = clase_df([(50, "NZL", 4, None), (40, "MAR", 2, None)])
        fm = {"NZL": 1, "MAR": 2}  # NZL(clase4) fase>=1 ok; MAR(clase2) necesita >=4
        self.assertEqual(determinar_revelacion(ec, fm), "NZL")

    def test_nadie_cumple_devuelve_none(self):
        ec = clase_df([(50, "NZL", 4, None)])
        self.assertIsNone(determinar_revelacion(ec, {"NZL": 0}))


class TestMejorYPeor(unittest.TestCase):
    def _tabla(self):
        res = df_resultados([
            partido("ARG", "BRA", 3, 0, ronda="Group Stage - 1", estado="FT"),
            partido("GER", "BRA", 0, 0, ronda="Group Stage - 2", estado="FT"),
        ])
        return calcular_tabla_grupos(res)

    def test_mejor_primera_fase(self):
        self.assertEqual(determinar_mejor_primera_fase(self._tabla()), "ARG")

    def test_peor_equipo(self):
        tabla = self._tabla()
        fm = {"ARG": 3, "GER": 1, "BRA": 0}
        self.assertEqual(determinar_peor_equipo(tabla, fm), "BRA")


class TestCalcularTodasLasCategorias(unittest.TestCase):
    def test_pre_grupos_todo_vacio(self):
        res = df_resultados(grupos_72(estado="NS"))  # grupos sin cerrar
        cats = calcular_todas_las_categorias(res)
        self.assertTrue(all(v == "" for v in cats.values()))

    @patch("utils.special_categories.cargar_equipos_clase")
    def test_post_grupos_setea_mejor_y_peor(self, mock_clase):
        mock_clase.return_value = clase_df([(17, "Uruguay", 1, 2)])
        cats = calcular_todas_las_categorias(_mundial_post_grupos())
        self.assertNotEqual(cats["Mejor 1era Fase"], "")
        self.assertNotEqual(cats["Peor Equipo"], "")
        self.assertEqual(cats["Revelación"], "")  # solo a fin de torneo

    @patch("utils.special_categories.cargar_equipos_clase")
    def test_decepcion_desde_cuadro_real_no_conteo_standings(self, mock_clase):  # REGRESIÓN #2
        # Uruguay (clase 1) NO está en el bracket real -> es la Decepción, sin
        # depender de un conteo exacto de standings (que daría 31).
        mock_clase.return_value = clase_df([
            (17, "Uruguay", 1, 2), (1, "T20", 1, 1), (2, "T25", 1, 1),
        ])
        cats = calcular_todas_las_categorias(_mundial_post_grupos())
        self.assertEqual(cats["Decepción"], "Uruguay")

    @patch("utils.special_categories.cargar_equipos_clase")
    def test_decepcion_no_degenerada_elige_eliminado(self, mock_clase):  # REGRESIÓN #3
        # Hay clase-1 que avanzaron (T20, T25 en el bracket) y uno eliminado (Uruguay).
        # Debe elegir el ELIMINADO, no uno que avanzó.
        mock_clase.return_value = clase_df([
            (17, "Uruguay", 1, 2), (1, "T20", 1, 1), (2, "T25", 1, 1),
        ])
        cats = calcular_todas_las_categorias(_mundial_post_grupos())
        self.assertEqual(cats["Decepción"], "Uruguay")
        self.assertNotIn(cats["Decepción"], {"T20", "T25"})

    @patch("utils.special_categories.cargar_equipos_clase")
    def test_decepcion_pendiente_con_bracket_vacio(self, mock_clase):  # ventana ciega
        mock_clase.return_value = clase_df([(17, "Uruguay", 1, 2)])
        cats = calcular_todas_las_categorias(_mundial_post_grupos(con_bracket=False))
        self.assertEqual(cats["Decepción"], "")  # bracket vacío -> sin falso positivo


if __name__ == "__main__":
    unittest.main()
