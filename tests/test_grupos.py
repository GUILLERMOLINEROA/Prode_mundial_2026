"""Puntos de fase de grupos: ganador (+1) y exacto (+1 adicional)."""
import unittest

from utils.scoring import calcular_puntos_grupos, _determinar_resultado
from tests._builders import df_apuestas, df_resultados, partido, apuesta


class TestDeterminarResultado(unittest.TestCase):
    def test_local(self):
        self.assertEqual(_determinar_resultado(2, 0), "local")

    def test_visitante(self):
        self.assertEqual(_determinar_resultado(0, 2), "visitante")

    def test_empate(self):
        self.assertEqual(_determinar_resultado(1, 1), "empate")


class TestPuntosGrupos(unittest.TestCase):
    def _pts(self, apuestas, resultados, participante="JUAN"):
        pts, det = calcular_puntos_grupos(df_apuestas(apuestas), df_resultados(resultados), participante)
        return pts, det

    def test_acierto_ganador_suma_1(self):
        # Predijo gana local (2-0); real gana local (1-0) -> +1 (ganador, no exacto)
        ap = [apuesta("JUAN", "ARG", "BRA", 2, 0)]
        res = [partido("ARG", "BRA", 1, 0, estado="FT")]
        pts, _ = self._pts(ap, res)
        self.assertEqual(pts, 1)

    def test_acierto_exacto_suma_2(self):
        ap = [apuesta("JUAN", "ARG", "BRA", 2, 1)]
        res = [partido("ARG", "BRA", 2, 1, estado="FT")]
        pts, _ = self._pts(ap, res)
        self.assertEqual(pts, 2)

    def test_empate_acertado_suma_1(self):
        ap = [apuesta("JUAN", "ARG", "BRA", 1, 1)]
        res = [partido("ARG", "BRA", 0, 0, estado="FT")]
        pts, _ = self._pts(ap, res)
        self.assertEqual(pts, 1)

    def test_resultado_distinto_no_suma(self):
        ap = [apuesta("JUAN", "ARG", "BRA", 2, 0)]
        res = [partido("ARG", "BRA", 0, 2, estado="FT")]
        pts, _ = self._pts(ap, res)
        self.assertEqual(pts, 0)

    def test_partido_NS_no_suma(self):
        ap = [apuesta("JUAN", "ARG", "BRA", 2, 0)]
        res = [partido("ARG", "BRA", None, None, estado="NS")]
        pts, det = self._pts(ap, res)
        self.assertEqual(pts, 0)
        self.assertEqual(det.iloc[0]["estado"], "pendiente")

    def test_sin_resultado_real_es_pendiente(self):
        ap = [apuesta("JUAN", "ARG", "BRA", 2, 0)]
        res = [partido("XXX", "YYY", 1, 0, estado="FT")]  # otro partido
        pts, det = self._pts(ap, res)
        self.assertEqual(pts, 0)
        self.assertEqual(det.iloc[0]["estado"], "pendiente")

    def test_provisional_en_vivo_cuenta_pero_marca_en_vivo(self):
        # En vivo con marcador que coincide: suma provisional, estado="en_vivo"
        ap = [apuesta("JUAN", "ARG", "BRA", 1, 0)]
        res = [partido("ARG", "BRA", 1, 0, estado="2H")]
        pts, det = self._pts(ap, res)
        self.assertEqual(pts, 2)  # ganador + exacto provisional
        self.assertEqual(det.iloc[0]["estado"], "en_vivo")

    def test_participante_sin_apuestas_devuelve_cero(self):
        ap = [apuesta("OTRO", "ARG", "BRA", 1, 0)]
        res = [partido("ARG", "BRA", 1, 0, estado="FT")]
        pts, det = self._pts(ap, res, participante="JUAN")
        self.assertEqual(pts, 0)
        self.assertTrue(det.empty)


if __name__ == "__main__":
    unittest.main()
