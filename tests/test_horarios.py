"""
formatear_horarios_partido: la hora del partido localizada a UNA sola zona.

Cubre:
 - Conversión correcta desde UTC a una zona nombrada (Argentina, UTC-3).
 - Caso DST: misma zona del norte (New York) en invierno (UTC-5) y verano
   (UTC-4) -> la zona nombrada respeta el horario de verano automáticamente.
 - Etiqueta de ciudad presentable ('_' -> ' ', multi-segmento).
 - Degradación segura: fecha None/NaT -> "", zona inválida -> Argentina.
"""
import unittest

import pandas as pd

from utils.api_football import formatear_horarios_partido


class TestFormatearHorarios(unittest.TestCase):
    def test_utc_a_argentina(self):
        # 2026-06-11 16:00 UTC -> 13:00 en Buenos Aires (UTC-3, sin DST).
        out = formatear_horarios_partido("2026-06-11T16:00:00+00:00",
                                         "America/Argentina/Buenos_Aires")
        self.assertEqual(out, "11/06 13:00 (Buenos Aires)")

    def test_dst_new_york_invierno_y_verano(self):
        # Misma zona nombrada, dos instantes: en enero NY es UTC-5, en julio
        # UTC-4 (horario de verano). Probamos que la conversión lo respeta.
        invierno = formatear_horarios_partido("2026-01-15T17:00:00+00:00",
                                              "America/New_York")
        verano = formatear_horarios_partido("2026-07-15T17:00:00+00:00",
                                            "America/New_York")
        self.assertEqual(invierno, "15/01 12:00 (New York)")  # UTC-5
        self.assertEqual(verano, "15/07 13:00 (New York)")    # UTC-4 (DST)

    def test_fecha_naive_se_asume_utc(self):
        # Sin tzinfo (modo simulación) se interpreta como UTC.
        out = formatear_horarios_partido(pd.Timestamp("2026-06-11 16:00:00"),
                                         "America/Argentina/Buenos_Aires")
        self.assertEqual(out, "11/06 13:00 (Buenos Aires)")

    def test_ciudad_multisegmento_presentable(self):
        out = formatear_horarios_partido("2026-06-11T16:00:00+00:00",
                                         "America/Sao_Paulo")
        self.assertTrue(out.endswith("(Sao Paulo)"), out)

    def test_default_es_argentina(self):
        out = formatear_horarios_partido("2026-06-11T16:00:00+00:00")
        self.assertEqual(out, "11/06 13:00 (Buenos Aires)")

    def test_zona_invalida_cae_a_argentina(self):
        out = formatear_horarios_partido("2026-06-11T16:00:00+00:00", "Zona/Inexistente")
        self.assertEqual(out, "11/06 13:00 (Buenos Aires)")

    def test_fecha_vacia_devuelve_string_vacio(self):
        self.assertEqual(formatear_horarios_partido(None), "")
        self.assertEqual(formatear_horarios_partido(pd.NaT), "")


if __name__ == "__main__":
    unittest.main()
