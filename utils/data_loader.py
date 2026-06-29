import streamlit as st
import pandas as pd
import os
import json

from utils.excel_reader import cargar_todos_los_participantes
from utils.api_football import mapear_nombre_equipo, clasificar_ronda, obtener_partidos_mundial, obtener_ultimos_resultados, ESTADOS_FINALIZADO
from utils.scoring import calcular_puntuacion_total, generar_leaderboard
from utils.special_categories import calcular_todas_las_categorias, grupos_finalizados, torneo_finalizado
from utils.group_config import overrides_path, fotos_dir


def cargar_overrides():
    path = overrides_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _ganador_eliminatoria(p):
    """
    Ganador de un cruce de eliminatoria TERMINADO, o None si no se puede
    determinar (dato faltante -> degradación segura, no se inventa).
    El marcador (goles_local/visitante) ya incluye el alargue; si está empatado,
    define la tanda de penales (penales_local/visitante). Misma lógica que
    determinar_campeon_y_tercero.
    """
    gl, gv = p.get("goles_local"), p.get("goles_visitante")
    if pd.isna(gl) or pd.isna(gv):
        return None
    gl, gv = int(gl), int(gv)
    if gl > gv:
        return p.get("equipo_local", "")
    if gv > gl:
        return p.get("equipo_visitante", "")
    # Empate en el marcador -> lo define la tanda de penales (estado PEN).
    pl, pv = p.get("penales_local"), p.get("penales_visitante")
    if pd.notna(pl) and pd.notna(pv):
        pl, pv = int(pl), int(pv)
        if pl > pv:
            return p.get("equipo_local", "")
        if pv > pl:
            return p.get("equipo_visitante", "")
    return None


def extraer_equipos_reales_por_ronda(resultados):
    """
    Arma el set de equipos por ronda con DOS vistas separadas a propósito:

      - Las claves 16vos..final son la vista del PASE (scoring del +N): ganadores de
        partidos terminados propagados a la ronda siguiente.
      - La clave "penalidades" es la vista TERMINADOS (autoritativa para
        calcular_penalidades), que incluye `eliminados_pre_4tos`. Separar las vistas
        deja lista la inyección del provisional en vivo (cambio siguiente) sin que
        contamine las penalidades.
    """
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

    siguiente_ronda = {"16vos": "8vos", "8vos": "4tos", "4tos": "semis", "semis": "final"}

    # --- VISTA TERMINADOS (para penalidades) ---
    # El que gana un cruce TERMINADO pasa a la ronda siguiente (sin esperar el cuadro
    # de la API). El PERDEDOR de 16avos/8vos queda "eliminado antes de cuartos". `term`
    # es una vista SEPARADA del pase: solo FT/AET/PEN, para que el provisional en vivo
    # de abajo no la contamine.
    term = {r: set(s) for r, s in equipos.items()}
    eliminados_pre_4tos = set()
    for _, p in resultados.iterrows():
        if str(p.get("estado", "") or "").strip() not in ESTADOS_FINALIZADO:
            continue
        ronda = clasificar_ronda(str(p.get("ronda", "")))
        sig = siguiente_ronda.get(ronda)
        if not sig:
            continue  # grupos / final / 3er puesto: no propagan acá
        ganador = _ganador_eliminatoria(p)
        if not ganador:
            continue
        loc, vis = p.get("equipo_local", ""), p.get("equipo_visitante", "")
        perdedor = vis if ganador == loc else loc
        equipos[sig].add(mapear_nombre_equipo(ganador))
        term[sig].add(mapear_nombre_equipo(ganador))
        if ronda in ("16vos", "8vos"):
            eliminados_pre_4tos.add(mapear_nombre_equipo(perdedor))
    # Campeón eliminado en FASE DE GRUPOS: una vez poblado el bracket (>=24, umbral
    # defensivo, no conteo ==N), los equipos con fase_max==0 quedan eliminados.
    if len(term["16vos"]) >= 24:
        eliminados_pre_4tos |= {mapear_nombre_equipo(eq) for eq, mx in fase_maxima.items() if mx == 0}

    # Facts TERMINADOS para las penalidades (vista separada del pase).
    equipos["penalidades"] = {
        "16vos": term["16vos"],
        "4tos": term["4tos"],
        "semis": term["semis"],
        "eliminados_pre_4tos": eliminados_pre_4tos,
    }
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
    Builder COMPARTIDO de puntajes. Arma `equipos_reales_por_ronda` desde el
    cuadro real de la API y puntúa a todos los participantes con la MISMA lógica,
    para que la app (cargar_todo) y los mails (notifications.obtener_leaderboard)
    NO puedan divergir.

    `categorias_reales` se recibe ya resuelto a propósito: cada caller lo arma a
    su manera (la app con calcular_todas_las_categorias + overrides; los mails con
    su propia fuente) y eso queda fuera de este builder.

    16avos: el set ["16vos"] sale SOLO del cuadro real de la API
    (extraer_equipos_reales_por_ronda). No se inyecta nada desde standings: el +1
    de 16avos suma recién cuando la API publica la Round of 32 (al cerrar grupos).
    Durante la fase de grupos la columna 16avos queda en 0 para todos.

    Retorna: (todos_puntajes, campeon_real, tercero_real, equipos_reales)
    """
    equipos_reales = extraer_equipos_reales_por_ronda(resultados)

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
            campeon_real=campeon_real, tercero_real=tercero_real))

    return todos_puntajes, campeon_real, tercero_real, equipos_reales


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
    todos_puntajes, campeon_real, tercero_real, _eq_reales = construir_puntajes(
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
