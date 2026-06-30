"""
Builders de datos SINTÉTICOS para la suite de tests del scoring.

Cero dependencia de la API, de la API_FOOTBALL_KEY, de los Excels reales o de
datos de producción. Cada test arma sus propios datos mínimos con estos helpers.
"""
import pandas as pd


# --- Partidos (estructura `resultados` que usa la app) ---

def partido(local, visitante, gl=None, gv=None, ronda="Group Stage - 1",
            estado="FT", pen_l=None, pen_v=None, fecha="2026-06-12"):
    """Una fila de `resultados`. gl/gv = marcador; pen_l/pen_v = tanda de penales.
    `fecha` solo la usa el Timeline (las demás funciones la ignoran)."""
    return {
        "ronda": ronda,
        "equipo_local": local,
        "equipo_visitante": visitante,
        "goles_local": gl,
        "goles_visitante": gv,
        "estado": estado,
        "penales_local": pen_l,
        "penales_visitante": pen_v,
        "fecha": fecha,
    }


def df_resultados(filas):
    return pd.DataFrame(filas)


def grupos_72(estado="FT"):
    """72 partidos de fase de grupos (12 grupos A-L, 4 equipos, round-robin)."""
    import itertools
    filas = []
    for g in range(12):
        base = 4 * g
        equipos = [f"G{base+1:02d}", f"G{base+2:02d}", f"G{base+3:02d}", f"G{base+4:02d}"]
        for a, b in itertools.combinations(range(4), 2):
            filas.append(partido(equipos[a], equipos[b], 1, 0,
                                  ronda=f"Group Stage - {g+1}", estado=estado))
    return filas


def round_of_32(equipos, estado="NS", ganan_locales=True):
    """16 cruces de 16avos (Round of 32) entre los 32 `equipos` dados (en orden)."""
    assert len(equipos) == 32
    filas = []
    for i in range(16):
        l, v = equipos[2 * i], equipos[2 * i + 1]
        gl, gv = (1, 0) if ganan_locales else (0, 1)
        if estado == "NS":
            gl = gv = None
        filas.append(partido(l, v, gl, gv, ronda="Round of 32", estado=estado))
    return filas


# --- Apuestas de fase de grupos ---

def apuesta(participante, local, visitante, glp, gvp, grupo="A", pid="GA1"):
    return {
        "participante": participante,
        "equipo_local": local,
        "equipo_visitante": visitante,
        "goles_local_pred": glp,
        "goles_visitante_pred": gvp,
        "partido_id": pid,
        "grupo": grupo,
    }


def df_apuestas(filas):
    cols = ["participante", "equipo_local", "equipo_visitante",
            "goles_local_pred", "goles_visitante_pred", "partido_id", "grupo"]
    if not filas:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(filas)


# --- Total Results (predicción de eliminatorias/campeón por participante) ---

def total_results(equipos_por_ronda=None, campeon="", subcampeon="", tercero=""):
    return {
        "equipos_por_ronda": equipos_por_ronda or {},
        "campeon": campeon,
        "subcampeon": subcampeon,
        "tercero": tercero,
    }


# --- Equipos clase (insumo de Decepción/Revelación) ---

def clase_df(filas):
    """filas: lista de (ranking_fifa, pais, clase, class_1_sub)."""
    return pd.DataFrame(filas, columns=["ranking_fifa", "pais", "clase", "class_1_sub"])


# --- Sets de equipos genéricos para penalidades/eliminatorias ---

def equipos(n, prefix="T"):
    """Set de n nombres de equipo genéricos: T00, T01, ..."""
    return {f"{prefix}{i:02d}" for i in range(n)}
