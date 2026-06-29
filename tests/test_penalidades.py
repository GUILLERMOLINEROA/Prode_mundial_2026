"""
Penalidades y sus gatillos. Incluye tests de regresión:
 - #1 centinela "No hay Revelación"/"No hay Peor Equipo" no penaliza.
 - #4 penalidades de 16avos no disparan con el cuadro real vacío.

NOTA: en el código vigente las penalidades de 16avos/4tos/semis se gatean por
ronda COMPLETA exacta (len==32 / ==8 / ==4). Los tests reflejan ese comportamiento.
"""
import unittest

from utils.scoring import calcular_penalidades, PENALIDADES
from tests._builders import equipos


def reales(eq16=None, eq4=None, eqsemis=None):
    return {
        "16vos": eq16 if eq16 is not None else set(),
        "4tos": eq4 if eq4 is not None else set(),
        "semis": eqsemis if eqsemis is not None else set(),
    }


SET32 = equipos(32)        # T00..T31
SET8 = {f"Q{i}" for i in range(8)}
SET4 = {f"S{i}" for i in range(4)}


class TestPenalidades(unittest.TestCase):
    def test_revelacion_queda_en_grupos_resta_20(self):
        pen, raz = calcular_penalidades({"Revelación": "ZZZ"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, PENALIDADES["revelacion_queda_grupos"])
        self.assertTrue(any("revelaci" in r.lower() for r in raz))

    def test_revelacion_clasifico_no_penaliza(self):
        pen, _ = calcular_penalidades({"Revelación": "T05"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)

    def test_centinela_no_hay_revelacion_no_penaliza(self):  # REGRESIÓN #1
        pen, raz = calcular_penalidades({"Revelación": "No hay Revelación"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)
        self.assertFalse(any("revelaci" in r.lower() for r in raz))

    def test_peor_equipo_pasa_de_grupos_resta_10(self):
        pen, _ = calcular_penalidades({"Peor Equipo": "T03"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, PENALIDADES["peor_pasa_grupos"])

    def test_peor_equipo_no_paso_no_penaliza(self):
        pen, _ = calcular_penalidades({"Peor Equipo": "ZZZ"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)

    def test_centinela_no_hay_peor_equipo_no_penaliza(self):  # REGRESIÓN #1b
        pen, _ = calcular_penalidades({"Peor Equipo": "No hay Peor Equipo"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)

    def test_campeon_no_llega_a_4tos_resta_20(self):
        pen, _ = calcular_penalidades({"Campeon": "ZZZ"}, {}, reales(eq4=SET8))
        self.assertEqual(pen, PENALIDADES["campeon_no_llega_4tos"])

    def test_campeon_llega_a_4tos_no_penaliza(self):
        pen, _ = calcular_penalidades({"Campeon": "Q0"}, {}, reales(eq4=SET8))
        self.assertEqual(pen, 0)

    def test_decepcion_llega_a_semis_resta_20(self):
        pen, _ = calcular_penalidades({"Decepción": "S0"}, {}, reales(eqsemis=SET4))
        self.assertEqual(pen, PENALIDADES["decepcion_llega_semis"])

    def test_penalidades_16avos_no_disparan_con_bracket_vacio(self):  # REGRESIÓN #4
        # Cuadro real de 16avos vacío -> ni revelación ni peor equipo penalizan.
        pred = {"Revelación": "ZZZ", "Peor Equipo": "T03"}
        pen, raz = calcular_penalidades(pred, {}, reales(eq16=set()))
        self.assertEqual(pen, 0)
        self.assertEqual(raz, [])

    def test_suma_de_varias_penalidades(self):
        pred = {"Revelación": "ZZZ", "Peor Equipo": "T03"}
        pen, _ = calcular_penalidades(pred, {}, reales(eq16=SET32))
        self.assertEqual(pen, PENALIDADES["revelacion_queda_grupos"] + PENALIDADES["peor_pasa_grupos"])


if __name__ == "__main__":
    unittest.main()
