"""
Evolución DIARIA de puntos para el Timeline, desde la MISMA fuente que el leaderboard,
con el +N del pase REPARTIDO por día de partido (curva suave).

Por cada día con partidos terminados, el total de cada participante =
    puntos de grupos acumulados a esa fecha        (de detalle_grupos del leaderboard)
  + +N del pase de eliminatoria REPARTIDO          (elim sobre cuadro "solo terminados")
  + resto correcto-en-su-día                        (campeón/3ero/especiales/penalidades)

Dos vistas a propósito (no se mezclan):
  - PASE (+N): cuadro de eliminatoria armado SOLO con partidos terminados hasta el día
    -> el +N de cada equipo aparece el día que juega/gana su partido de esa ronda.
    Atribución COSMÉTICA: el +1 de 16avos se gana al clasificar (fin de grupos), pero se
    muestra el día del partido de 16avos para suavizar la curva. Consecuencia: durante
    una ronda EN CURSO el extremo de la curva queda por DEBAJO del Total de la tabla por
    el pase aún no repartido (la nota del gráfico lo aclara).
  - PENALIDADES / especiales / campeón / 3ero: desde el cuadro CON PRESENCIA (16avos
    publicados al cerrar grupos), para que sean correctas y caigan en su día real (p.ej.
    revelación/peor en fin de grupos sin falsos positivos; el -20 del campeón Japón el día
    de su partido). NO se reparten.

El provisional EN VIVO no entra a la curva.

Invariante: con la ronda en curso COMPLETA (todos sus partidos terminados) y sin vivo, el
último punto == Total del leaderboard. Con la ronda en curso incompleta, el extremo ==
Total - (pase aún no repartido).
"""
import collections
import pandas as pd

from utils.api_football import clasificar_ronda
from utils.scoring import ajuste_manual_de, calcular_puntos_eliminatorias
from utils.special_categories import calcular_todas_las_categorias, grupos_finalizados
from utils.data_loader import construir_puntajes, extraer_equipos_reales_por_ronda

_FINALIZADO = {"FT", "AET", "PEN"}

_MILESTONES = [
    ("Fin Grupos", "grupos", "2026-06-28"),
    ("16vos", "16vos", "2026-07-04"),
    ("8vos", "8vos", "2026-07-08"),
    ("4tos", "4tos", "2026-07-12"),
    ("Semis", "semis", "2026-07-17"),
    ("Final", "final", "2026-07-21"),
]
_INICIO = ("Inicio Grupos", "2026-06-11")

_APUESTAS_VACIAS = pd.DataFrame(columns=[
    "participante", "equipo_local", "equipo_visitante",
    "goles_local_pred", "goles_visitante_pred", "partido_id", "grupo"])


def _dia(fecha):
    return pd.Timestamp(pd.to_datetime(fecha, utc=True).date(), tz="UTC")


def _snapshot(res, dia, grupos_fin_dia, presencia_16):
    """Partidos terminados hasta `dia` (con resultado). Si `presencia_16` y los grupos ya
    cerraron, agrega los 16avos como PRESENCIA (NS, sin resultado) -> el cuadro de
    clasificados está completo (para penalidades/especiales). Sin `presencia_16`, solo
    terminados -> el pase aparece a medida que se juega cada partido."""
    term = res["_term"] & (res["_dia"] <= dia)
    snap = res[term]
    if presencia_16 and grupos_fin_dia is not None and grupos_fin_dia <= dia:
        pres = res[(res["_ronda"] == "16vos") & ~term].copy()
        if not pres.empty:
            pres["estado"] = "NS"
            for c in ("goles_local", "goles_visitante", "penales_local", "penales_visitante"):
                if c in pres.columns:
                    pres[c] = None
            snap = pd.concat([snap, pres], ignore_index=True)
    return snap.drop(columns=["_dia", "_ronda", "_term"], errors="ignore")


def _grupos_acumulado(todos_puntajes, fecha_map, dias):
    """{participante: {dia: puntos de grupos acumulados hasta dia}} desde detalle_grupos."""
    por_dia = {}
    for pj in todos_puntajes:
        d = collections.defaultdict(int)
        det = pj.get("detalle_grupos")
        if isinstance(det, pd.DataFrame) and not det.empty:
            for _, r in det.iterrows():
                if r.get("estado") != "jugado":  # solo terminados (no en vivo)
                    continue
                dia = fecha_map.get((r.get("equipo_local"), r.get("equipo_visitante")))
                if dia is not None:
                    d[dia] += int(r.get("puntos", 0))
        por_dia[pj["participante"]] = d
    cum = {}
    for part, d in por_dia.items():
        acc, c = 0, {}
        for dia in dias:
            acc += d.get(dia, 0)
            c[dia] = acc
        cum[part] = c
    return cum


def construir_evolucion(resultados, apuestas_grupos, categorias_todos,
                        total_results_todos, todos_puntajes, overrides=None):
    """
    Retorna (df_evolucion, fases):
      - df_evolucion: filas {participante, fecha, puntos, evento}, un punto por día con
        partidos terminados (+ punto inicial). Pase repartido; resto correcto en su día.
      - fases: [(label, round_key, fecha_ts)] de las fases ya empezadas (para el slider).
    """
    overrides = overrides or {}
    if resultados is None or resultados.empty or not todos_puntajes:
        return pd.DataFrame(), []

    res = resultados.copy()
    res["_dia"] = res["fecha"].apply(_dia)
    res["_ronda"] = res["ronda"].apply(lambda r: clasificar_ronda(str(r)))
    res["_term"] = res["estado"].apply(lambda e: str(e or "").strip() in _FINALIZADO)

    dias = sorted(res.loc[res["_term"], "_dia"].unique())
    if not dias:
        return pd.DataFrame(), []

    grupos_fin_dia = None
    if grupos_finalizados(resultados):
        g = res[(res["_ronda"] == "grupos") & res["_term"]]
        if not g.empty:
            grupos_fin_dia = g["_dia"].max()

    fecha_map = {}
    for _, p in res[res["_ronda"] == "grupos"].iterrows():
        fecha_map[(p.get("equipo_local"), p.get("equipo_visitante"))] = p["_dia"]
    grupos_cum = _grupos_acumulado(todos_puntajes, fecha_map, dias)

    ajustes = {pj["participante"]: ajuste_manual_de(pj["participante"])[0]
               for pj in todos_puntajes}

    filas = []
    inicio_ts = pd.Timestamp(_INICIO[1], tz="UTC")
    for pj in todos_puntajes:
        filas.append({"participante": pj["participante"], "fecha": inicio_ts,
                      "puntos": ajustes[pj["participante"]], "evento": _INICIO[0]})

    for d in dias:
        # Vista CON PRESENCIA -> resto correcto en su día (penalidades/especiales/campeón).
        snap_pen = _snapshot(res, d, grupos_fin_dia, presencia_16=True)
        cr = calcular_todas_las_categorias(snap_pen)
        for k, v in overrides.items():
            if v and k in cr:
                cr[k] = v
        resto, *_ = construir_puntajes(snap_pen, _APUESTAS_VACIAS, categorias_todos,
                                       total_results_todos, cr)

        # Vista SOLO TERMINADOS -> +N del pase repartido por día de partido.
        eq_pase = extraer_equipos_reales_por_ronda(
            _snapshot(res, d, grupos_fin_dia, presencia_16=False))

        et = pd.Timestamp(d).strftime("%d/%m")
        for pj in resto:
            part = pj["participante"]
            no_elim = pj["total"] - pj["pts_eliminatorias"]  # campeón+3ero+especiales+penal+ajuste
            elim_pase, _, _ = calcular_puntos_eliminatorias(
                total_results_todos.get(part, {}), eq_pase)
            puntos = grupos_cum.get(part, {}).get(d, 0) + elim_pase + no_elim
            filas.append({"participante": part, "fecha": d, "puntos": puntos, "evento": et})

    started = set(res.loc[res["estado"].apply(lambda e: str(e or "").strip() != "NS"), "_ronda"])
    fases = [(lbl, rk, pd.Timestamp(f, tz="UTC")) for (lbl, rk, f) in _MILESTONES if rk in started]
    return pd.DataFrame(filas), fases
