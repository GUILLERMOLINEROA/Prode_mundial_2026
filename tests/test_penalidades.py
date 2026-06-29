"""
Penalidades y sus gatillos. Incluye tests de regresión:
 - #1 centinela "No hay Revelación"/"No hay Peor Equipo" no penaliza.
 - #4 penalidades de 16avos no disparan con el cuadro real vacío.

Gatillos por HECHO DIRECTO (sin conteo ==N): revelación = jugó grupos y no clasificó
(`in grupos_jugados` + bracket poblado `>=24` + `not in eq_16vos`); peor = `in eq_16vos`;
decepción = `in eq_semis` (dispara apenas llega, sin esperar las semis completas);
campeón = `in eliminados_pre_4tos`.
"""
import unittest

from utils.scoring import calcular_penalidades, PENALIDADES
from tests._builders import equipos


def reales(eq16=None, eqsemis=None, eliminados=None, grupos=None):
    return {
        "16vos": eq16 if eq16 is not None else set(),
        "semis": eqsemis if eqsemis is not None else set(),
        "eliminados_pre_4tos": eliminados if eliminados is not None else set(),
        "grupos_jugados": grupos if grupos is not None else set(),
    }


SET32 = equipos(32)        # T00..T31
SET4 = {f"S{i}" for i in range(4)}


class TestRevelacion(unittest.TestCase):
    def test_queda_en_grupos_resta_20(self):
        # Jugó grupos, bracket completo, no clasificó -> -20.
        pen, raz = calcular_penalidades({"Revelación": "ZZZ"}, {}, reales(eq16=SET32, grupos={"ZZZ"}))
        self.assertEqual(pen, PENALIDADES["revelacion_queda_grupos"])
        self.assertTrue(any("revelaci" in r.lower() for r in raz))

    def test_clasifico_no_penaliza(self):
        # Jugó grupos PERO clasificó (está en el bracket) -> sin penalidad.
        pen, _ = calcular_penalidades({"Revelación": "T05"}, {}, reales(eq16=SET32, grupos={"T05"}))
        self.assertEqual(pen, 0)

    def test_centinela_no_hay_revelacion_no_penaliza(self):  # REGRESIÓN #1
        pen, raz = calcular_penalidades({"Revelación": "No hay Revelación"}, {},
                                        reales(eq16=SET32, grupos={"No hay Revelación"}))
        self.assertEqual(pen, 0)
        self.assertFalse(any("revelaci" in r.lower() for r in raz))

    def test_bracket_parcial_no_falso_positivo(self):  # EL BORDE del `not in`
        # Bracket a 20 (<24): no evaluamos -> no penalizamos por "ausencia" provisional.
        parcial = set(list(SET32)[:20])
        pen, _ = calcular_penalidades({"Revelación": "ZZZ"}, {}, reales(eq16=parcial, grupos={"ZZZ"}))
        self.assertEqual(pen, 0)

    def test_bracket_31_escapa_al_trap(self):  # discriminante: bajo ==32 daba 0
        # Un nombre faltante deja el bracket en 31; con >=24 igual evaluamos -> -20.
        casi = set(list(SET32)[:31])
        pen, _ = calcular_penalidades({"Revelación": "ZZZ"}, {}, reales(eq16=casi, grupos={"ZZZ"}))
        self.assertEqual(pen, PENALIDADES["revelacion_queda_grupos"])

    def test_no_jugo_grupos_no_penaliza(self):  # guard (A): typo / equipo desconocido
        # La revelación no figura entre los que jugaron grupos -> no inventamos penalidad.
        pen, _ = calcular_penalidades({"Revelación": "TYPO"}, {}, reales(eq16=SET32, grupos=set()))
        self.assertEqual(pen, 0)


class TestPeorEquipo(unittest.TestCase):
    def test_pasa_de_grupos_resta_10(self):
        pen, _ = calcular_penalidades({"Peor Equipo": "T03"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, PENALIDADES["peor_pasa_grupos"])

    def test_no_paso_no_penaliza(self):
        pen, _ = calcular_penalidades({"Peor Equipo": "ZZZ"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)

    def test_in_sin_bracket_completo(self):  # discriminante: bajo ==32 daba 0
        # El `in` no necesita bracket completo: si el peor está, pasó de grupos -> -10.
        pen, _ = calcular_penalidades({"Peor Equipo": "T0"}, {}, reales(eq16={"T0", "T1", "T2"}))
        self.assertEqual(pen, PENALIDADES["peor_pasa_grupos"])

    def test_centinela_no_hay_peor_equipo_no_penaliza(self):  # REGRESIÓN #1b
        pen, _ = calcular_penalidades({"Peor Equipo": "No hay Peor Equipo"}, {}, reales(eq16=SET32))
        self.assertEqual(pen, 0)


class TestDecepcionSemis(unittest.TestCase):
    def test_llega_a_semis_resta_20(self):
        pen, _ = calcular_penalidades({"Decepción": "S0"}, {}, reales(eqsemis=SET4))
        self.assertEqual(pen, PENALIDADES["decepcion_llega_semis"])

    def test_dispara_apenas_gana_su_4to(self):  # discriminante: bajo ==4 daba 0
        # Semis incompletas (1 solo semifinalista): igual dispara apenas la decepción llega.
        pen, _ = calcular_penalidades({"Decepción": "S0"}, {}, reales(eqsemis={"S0"}))
        self.assertEqual(pen, PENALIDADES["decepcion_llega_semis"])

    def test_no_llega_no_penaliza(self):
        pen, _ = calcular_penalidades({"Decepción": "ZZZ"}, {}, reales(eqsemis=SET4))
        self.assertEqual(pen, 0)


class TestCampeon(unittest.TestCase):
    def test_eliminado_resta_20(self):
        pen, _ = calcular_penalidades({"Campeon": "ZZZ"}, {}, reales(eliminados={"ZZZ"}))
        self.assertEqual(pen, PENALIDADES["campeon_no_llega_4tos"])

    def test_no_eliminado_no_penaliza(self):
        pen, _ = calcular_penalidades({"Campeon": "ARG"}, {}, reales(eliminados={"BRA"}))
        self.assertEqual(pen, 0)


class TestVarias(unittest.TestCase):
    def test_penalidades_16avos_no_disparan_con_bracket_vacio(self):  # REGRESIÓN #4
        pred = {"Revelación": "ZZZ", "Peor Equipo": "T03"}
        pen, raz = calcular_penalidades(pred, {}, reales(eq16=set(), grupos={"ZZZ", "T03"}))
        self.assertEqual(pen, 0)
        self.assertEqual(raz, [])

    def test_suma_de_varias_penalidades(self):
        pred = {"Revelación": "ZZZ", "Peor Equipo": "T03"}
        pen, _ = calcular_penalidades(pred, {}, reales(eq16=SET32, grupos={"ZZZ"}))
        self.assertEqual(pen, PENALIDADES["revelacion_queda_grupos"] + PENALIDADES["peor_pasa_grupos"])


if __name__ == "__main__":
    unittest.main()
