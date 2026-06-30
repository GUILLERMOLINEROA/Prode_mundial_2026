"""
Evolución de puntos para el Timeline, desde la MISMA fuente que el leaderboard.

Por cada hito de ronda que YA empezó, el total de cada participante sale de
`construir_puntajes` sobre `resultados` recortado a esa ronda o anteriores (con su
`categorias_reales` recomputada para ese corte). El hito de la ronda EN CURSO usa el
total del leaderboard (`todos_puntajes`) -> el último punto de cada línea coincide
exactamente con la tabla de posiciones. Las rondas no jugadas NO se grafican.
"""
import pandas as pd

from utils.api_football import clasificar_ronda
from utils.scoring import AJUSTES_MANUALES
from utils.special_categories import calcular_todas_las_categorias
from utils.data_loader import construir_puntajes

# Orden de rondas para truncar (3er puesto cuenta como ronda final).
_ORDEN = {"grupos": 0, "16vos": 1, "8vos": 2, "4tos": 3, "semis": 4, "3ero": 5, "final": 5}

# Hitos del eje (label, clave de ronda, fecha representativa).
_MILESTONES = [
    ("Fin Grupos", "grupos", "2026-06-28"),
    ("16vos", "16vos", "2026-07-04"),
    ("8vos", "8vos", "2026-07-08"),
    ("4tos", "4tos", "2026-07-12"),
    ("Semis", "semis", "2026-07-17"),
    ("Final", "final", "2026-07-21"),
]
_INICIO = ("Inicio Grupos", "2026-06-11")


def _ronda_orden(ronda):
    return _ORDEN.get(clasificar_ronda(str(ronda)), -1)


def construir_evolucion(resultados, apuestas_grupos, categorias_todos,
                        total_results_todos, todos_puntajes, overrides=None):
    """
    Retorna (df_evolucion, hitos) donde:
      - df_evolucion: filas {participante, fecha, puntos, evento}, una por hito jugado.
      - hitos: [(label, round_key, fecha_ts)] de los hitos que ya empezaron.
    El último punto de cada participante == su `total` en todos_puntajes (leaderboard).
    """
    overrides = overrides or {}
    if resultados is None or resultados.empty or not todos_puntajes:
        return pd.DataFrame(), []

    # Rondas que ya arrancaron (algún partido no-NS: jugado o en vivo).
    started = set()
    for _, p in resultados.iterrows():
        if str(p.get("estado", "") or "").strip() != "NS":
            started.add(clasificar_ronda(str(p.get("ronda", ""))))

    hitos = [(lbl, rk, pd.Timestamp(f, tz="UTC")) for (lbl, rk, f) in _MILESTONES if rk in started]
    if not hitos:
        return pd.DataFrame(), []
    current_rk = hitos[-1][1]

    total_actual = {pj["participante"]: pj["total"] for pj in todos_puntajes}

    # Total por hito: el de la ronda EN CURSO == leaderboard; los pasados, scoring
    # real truncado (construir_puntajes sobre resultados <= esa ronda).
    total_por_hito = {}
    for (lbl, rk, fts) in hitos:
        if rk == current_rk:
            total_por_hito[rk] = total_actual
            continue
        res_r = resultados[resultados["ronda"].apply(
            lambda x, _o=_ORDEN[rk]: _ronda_orden(x) <= _o)]
        cr = calcular_todas_las_categorias(res_r)
        for k, v in overrides.items():
            if v and k in cr:
                cr[k] = v
        puntajes_r, *_ = construir_puntajes(res_r, apuestas_grupos, categorias_todos,
                                            total_results_todos, cr)
        total_por_hito[rk] = {pj["participante"]: pj["total"] for pj in puntajes_r}

    inicio_lbl, inicio_f = _INICIO
    inicio_ts = pd.Timestamp(inicio_f, tz="UTC")
    filas = []
    for pj in todos_puntajes:
        part = pj["participante"]
        ajuste = AJUSTES_MANUALES.get(str(part).strip().upper(), 0)
        filas.append({"participante": part, "fecha": inicio_ts, "puntos": ajuste, "evento": inicio_lbl})
        for (lbl, rk, fts) in hitos:
            filas.append({"participante": part, "fecha": fts,
                          "puntos": total_por_hito[rk].get(part, ajuste), "evento": lbl})
    return pd.DataFrame(filas), hitos
