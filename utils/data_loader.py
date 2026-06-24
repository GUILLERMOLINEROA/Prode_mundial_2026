import streamlit as st
import pandas as pd
import os
import json

from utils.excel_reader import cargar_todos_los_participantes
from utils.api_football import mapear_nombre_equipo, clasificar_ronda, obtener_partidos_mundial, obtener_ultimos_resultados
from utils.scoring import calcular_puntuacion_total, generar_leaderboard
from utils.special_categories import (
    calcular_todas_las_categorias, grupos_finalizados, torneo_finalizado,
    obtener_equipos_clasificados_16avos,
)
from utils.group_config import overrides_path, fotos_dir


def cargar_overrides():
    path = overrides_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def extraer_equipos_reales_por_ronda(resultados):
    if resultados.empty:
        return {}
    fase_maxima = {}
    orden_fases = {"grupos": 0, "16vos": 1, "8vos": 2, "4tos": 3, "semis": 4, "final": 5}
    for _, p in resultados.iterrows():
        ronda = clasificar_ronda(str(p.get("ronda", "")))
        orden = orden_fases.get(ronda, -1)
        for eq in [p.get("equipo_local", ""), p.get("equipo_visitante", "")]:
            if eq:
                fase_maxima[eq] = max(fase_maxima.get(eq, -1), orden)
    equipos = {"16vos": set(), "8vos": set(), "4tos": set(), "semis": set(), "final": set()}
    for eq, mx in fase_maxima.items():
        if mx >= 1: equipos["16vos"].add(eq)
        if mx >= 2: equipos["8vos"].add(eq)
        if mx >= 3: equipos["4tos"].add(eq)
        if mx >= 4: equipos["semis"].add(eq)
        if mx >= 5: equipos["final"].add(eq)
    return equipos


def determinar_campeon_y_tercero(resultados):
    campeon, tercero = "", ""
    if resultados.empty:
        return campeon, tercero
    finales = resultados[resultados["ronda"].str.lower().str.contains("final", na=False) &
        ~resultados["ronda"].str.lower().str.contains("semi|quarter|3rd", na=False)]
    if not finales.empty:
        f = finales.iloc[-1]
        gl, gv = f.get("goles_local"), f.get("goles_visitante")
        pl, pv = f.get("penales_local"), f.get("penales_visitante")
        if pd.notna(gl) and pd.notna(gv):
            if gl > gv: campeon = f["equipo_local"]
            elif gv > gl: campeon = f["equipo_visitante"]
            elif pd.notna(pl) and pd.notna(pv):
                campeon = f["equipo_local"] if pl > pv else f["equipo_visitante"]
    terceros = resultados[resultados["ronda"].str.lower().str.contains("3rd|third", na=False)]
    if not terceros.empty:
        t = terceros.iloc[-1]
        gl, gv = t.get("goles_local"), t.get("goles_visitante")
        pl, pv = t.get("penales_local"), t.get("penales_visitante")
        if pd.notna(gl) and pd.notna(gv):
            if gl > gv: tercero = t["equipo_local"]
            elif gv > gl: tercero = t["equipo_visitante"]
            elif pd.notna(pl) and pd.notna(pv):
                tercero = t["equipo_local"] if pl > pv else t["equipo_visitante"]
    return campeon, tercero


def foto_participante(nombre):
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(fotos_dir(), f"{nombre}{ext}")
        if os.path.exists(path):
            return path
    return None


def construir_puntajes(resultados, apuestas_grupos, categorias_todos,
                       total_results_todos, categorias_reales):
    """
    Builder COMPARTIDO de puntajes. Arma `equipos_reales_por_ronda` (con la
    inyección provisional de 16avos), calcula `grupos_cerrados` y puntúa a todos
    los participantes con la MISMA lógica, para que la app (cargar_todo) y los
    mails (notifications.obtener_leaderboard) NO puedan divergir.

    `categorias_reales` se recibe ya resuelto a propósito: cada caller lo arma a
    su manera (la app con calcular_todas_las_categorias + overrides; los mails con
    su propia fuente) y eso queda fuera de este builder.

    Retorna: (todos_puntajes, campeon_real, tercero_real, equipos_reales, grupos_cerrados)
    """
    equipos_reales = extraer_equipos_reales_por_ronda(resultados)

    # +1 de 16avos PROVISIONAL en vivo: si la API todavía NO pobló el cuadro real
    # de 16avos, lo rellenamos desde standings (1º/2º en fecha 3; los 32 al cerrar
    # grupos). Si la API ya lo pobló, ese set es AUTORITATIVO y NO se pisa. Solo
    # afecta ["16vos"]; 8vos/4tos/semis/final quedan intactos.
    grupos_cerrados = bool(grupos_finalizados(resultados))
    if not equipos_reales.get("16vos"):
        prov_16 = obtener_equipos_clasificados_16avos(resultados)
        if prov_16:
            equipos_reales["16vos"] = prov_16

    campeon_real, tercero_real = determinar_campeon_y_tercero(resultados)

    todos_puntajes = []
    for part in categorias_todos:
        todos_puntajes.append(calcular_puntuacion_total(
            participante=part, apuestas_grupos=apuestas_grupos,
            categorias_pred=categorias_todos.get(part, {}),
            total_results_pred=total_results_todos.get(part, {}),
            resultados_reales=resultados,
            equipos_reales_por_ronda=equipos_reales,
            categorias_reales=categorias_reales,
            campeon_real=campeon_real, tercero_real=tercero_real,
            grupos_cerrados=grupos_cerrados))

    return todos_puntajes, campeon_real, tercero_real, equipos_reales, grupos_cerrados


def cargar_todo():
    if "datos_cargados" in st.session_state and st.session_state["datos_cargados"]:
        return True

    apuestas_grupos, pred_elim, categorias_todos, total_results_todos = cargar_todos_los_participantes()
    if not categorias_todos:
        return False

    usar_simulacion = st.session_state.get("usar_simulacion", False)
    if usar_simulacion:
        from utils.simulacion import generar_resultados_simulados
        fase_sim = st.session_state.get("fase_simulacion", "todo")
        resultados = generar_resultados_simulados(fase_sim)
    else:
        resultados = obtener_partidos_mundial()
        if not resultados.empty:
            resultados["equipo_local"] = resultados["equipo_local"].apply(mapear_nombre_equipo)
            resultados["equipo_visitante"] = resultados["equipo_visitante"].apply(mapear_nombre_equipo)

    categorias_reales = calcular_todas_las_categorias(resultados)

    overrides = cargar_overrides()
    for k, v in overrides.items():
        if v and k in categorias_reales:
            categorias_reales[k] = v

    if usar_simulacion:
        from utils.simulacion import obtener_categorias_reales_simuladas
        cat_sim = obtener_categorias_reales_simuladas()
        if not categorias_reales.get("Figura"):
            categorias_reales["Figura"] = cat_sim.get("Figura", "")
        if not categorias_reales.get("Goleador"):
            categorias_reales["Goleador"] = cat_sim.get("Goleador", "")

    # Puntajes vía builder compartido (misma lógica de 16avos que los mails).
    todos_puntajes, campeon_real, tercero_real, _eq_reales, _gc = construir_puntajes(
        resultados, apuestas_grupos, categorias_todos, total_results_todos, categorias_reales,
    )

    leaderboard = generar_leaderboard(todos_puntajes)

    st.session_state["leaderboard"] = leaderboard
    st.session_state["todos_puntajes"] = todos_puntajes
    st.session_state["resultados"] = resultados
    st.session_state["categorias_reales"] = categorias_reales
    st.session_state["campeon_real"] = campeon_real
    st.session_state["tercero_real"] = tercero_real
    st.session_state["apuestas_grupos"] = apuestas_grupos
    st.session_state["categorias_todos"] = categorias_todos
    st.session_state["total_results_todos"] = total_results_todos
    st.session_state["datos_cargados"] = True

    return True


def forzar_recarga():
    st.session_state["datos_cargados"] = False
    st.cache_data.clear()
