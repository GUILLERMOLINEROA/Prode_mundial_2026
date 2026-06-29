"""Categorías especiales: puntos por acierto y detector de no-apuesta."""
import unittest

from utils.scoring import calcular_puntos_categorias, _es_no_apuesta, PUNTOS


class TestEsNoApuesta(unittest.TestCase):
    def test_centinelas_son_no_apuesta(self):
        for v in ["", "  ", "No hay Revelación", "no hay revelacion",
                  "No hay Decepción", "Sin decepción", "Ninguno", "ninguna",
                  "N/A", "na", "-", "--"]:
            with self.subTest(v=v):
                self.assertTrue(_es_no_apuesta(v))

    def test_equipo_real_no_es_no_apuesta(self):
        for v in ["Argentina", "Nueva Zelanda", "Uruguay", "Haiti"]:
            with self.subTest(v=v):
                self.assertFalse(_es_no_apuesta(v))


class TestPuntosCategorias(unittest.TestCase):
    def test_acierto_cada_categoria(self):
        cats = ["Figura", "Goleador", "Revelación", "Decepción", "Mejor 1era Fase", "Peor Equipo"]
        pred = {c: f"valor_{c}" for c in cats}
        real = dict(pred)
        pts, ac = calcular_puntos_categorias(pred, real)
        esperado = sum(PUNTOS[c] for c in cats)
        self.assertEqual(pts, esperado)
        self.assertTrue(all(ac[c] for c in cats))

    def test_case_insensitive(self):
        pts, ac = calcular_puntos_categorias({"Figura": "messi"}, {"Figura": "Messi"})
        self.assertEqual(pts, PUNTOS["Figura"])
        self.assertTrue(ac["Figura"])

    def test_real_vacio_no_suma(self):
        pts, ac = calcular_puntos_categorias({"Figura": "Messi"}, {"Figura": ""})
        self.assertEqual(pts, 0)
        self.assertFalse(ac["Figura"])

    def test_centinela_vs_real_vacio_no_suma_puntos_falsos(self):
        # Regresión: "No hay Revelación" predicho vs real vacío NO debe sumar.
        pts, ac = calcular_puntos_categorias({"Revelación": "No hay Revelación"}, {"Revelación": ""})
        self.assertEqual(pts, 0)
        self.assertFalse(ac["Revelación"])

    def test_no_acierto_no_suma(self):
        pts, ac = calcular_puntos_categorias({"Decepción": "Brasil"}, {"Decepción": "Uruguay"})
        self.assertEqual(pts, 0)
        self.assertFalse(ac["Decepción"])


if __name__ == "__main__":
    unittest.main()
