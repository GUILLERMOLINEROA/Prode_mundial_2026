# =============================================================================
# pages/1_Leaderboard.py
# Tablero principal de posiciones.
#
# - El líder rodeado de fuego 🔥
# - Los últimos congelados ❄️
# - Gráfico de barras apiladas con desglose de puntos
# - Mensajes sarcásticos para top 3 y últimos 3
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from utils.excel_reader import cargar_todos_los_participantes
from utils.api_football import obtener_partidos_mundial, mapear_nombre_equipo, clasificar_ronda
from utils.scoring import calcular_puntuacion_total, generar_leaderboard
from utils.messages import obtener_mensaje_posicion

# --- Configuración ---
st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def extraer_equipos_reales_por_ronda(resultados: pd.DataFrame) -> dict:
    """
    Extrae qué equipos jugaron en cada ronda de eliminatorias
    a partir de los resultados reales de la API.
    Un equipo que llegó a semis también cuenta en 4tos, 8vos, etc.
    """
    if resultados.empty:
        return {}
    
    # Determinar la fase MÁXIMA de cada equipo
    fase_maxima = {}
    orden_fases = {"grupos": 0, "16vos": 1, "8vos": 2, "4tos": 3, "semis": 4, "final": 5}
    
    for _, partido in resultados.iterrows():
        ronda = clasificar_ronda(str(partido.get("ronda", "")))
        orden = orden_fases.get(ronda, -1)
        
        for equipo in [partido.get("equipo_local", ""), partido.get("equipo_visitante", "")]:
            if equipo:
                fase_maxima[equipo] = max(fase_maxima.get(equipo, -1), orden)
    
    # Construir acumulado
    equipos_por_ronda = {
        "16vos": set(), "8vos": set(), "4tos": set(),
        "semis": set(), "final": set(),
    }
    
    for equipo, max_orden in fase_maxima.items():
        if max_orden >= 1:
            equipos_por_ronda["16vos"].add(equipo)
        if max_orden >= 2:
            equipos_por_ronda["8vos"].add(equipo)
        if max_orden >= 3:
            equipos_por_ronda["4tos"].add(equipo)
        if max_orden >= 4:
            equipos_por_ronda["semis"].add(equipo)
        if max_orden >= 5:
            equipos_por_ronda["final"].add(equipo)
    
    return equipos_por_ronda


def determinar_campeon_y_tercero(resultados: pd.DataFrame) -> tuple:
    """Determina campeón y 3er puesto de los resultados reales."""
    campeon = ""
    tercero = ""
    
    if resultados.empty:
        return campeon, tercero
    
    # Buscar la final
    finales = resultados[
        resultados["ronda"].str.lower().str.contains("final", na=False) &
        ~resultados["ronda"].str.lower().str.contains("semi|quarter|3rd", na=False)
    ]
    if not finales.empty:
        f = finales.iloc[-1]
        gl, gv = f.get("goles_local"), f.get("goles_visitante")
        pl, pv = f.get("penales_local"), f.get("penales_visitante")
        if pd.notna(gl) and pd.notna(gv):
            if gl > gv:
                campeon = f["equipo_local"]
            elif gv > gl:
                campeon = f["equipo_visitante"]
            elif pd.notna(pl) and pd.notna(pv):
                campeon = f["equipo_local"] if pl > pv else f["equipo_visitante"]
    
    # Buscar 3er puesto
    terceros = resultados[
        resultados["ronda"].str.lower().str.contains("3rd|third|tercer", na=False)
    ]
    if not terceros.empty:
        t = terceros.iloc[-1]
        gl, gv = t.get("goles_local"), t.get("goles_visitante")
        pl, pv = t.get("penales_local"), t.get("penales_visitante")
        if pd.notna(gl) and pd.notna(gv):
            if gl > gv:
                tercero = t["equipo_local"]
            elif gv > gl:
                tercero = t["equipo_visitante"]
            elif pd.notna(pl) and pd.notna(pv):
                tercero = t["equipo_local"] if pl > pv else t["equipo_visitante"]
    
    return campeon, tercero


def mostrar_leaderboard():
    """Función principal del leaderboard."""
    
    st.markdown(
        '<h1 class="titulo-prode">🏆 LEADERBOARD 🏆</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center; color:#888;">'
        'Actualizado en tiempo real. Sin piedad. Sin misericordia.</p>',
        unsafe_allow_html=True
    )
    
    # --- Cargar apuestas ---
    with st.spinner("🔄 Cargando apuestas de los participantes..."):
        apuestas_grupos, pred_elim, categorias_todos, total_results_todos = (
            cargar_todos_los_participantes()
        )
    
    if not categorias_todos:
        st.warning("⚠️ No se encontraron archivos de participantes en `data/participantes/`.")
        _mostrar_demo()
        return
    
    # --- Cargar resultados reales ---
    with st.spinner("🔄 Obteniendo resultados reales de la API..."):
        resultados = obtener_partidos_mundial()
    
    if not resultados.empty:
        resultados["equipo_local"] = resultados["equipo_local"].apply(mapear_nombre_equipo)
        resultados["equipo_visitante"] = resultados["equipo_visitante"].apply(mapear_nombre_equipo)
    
    equipos_reales_por_ronda = extraer_equipos_reales_por_ronda(resultados)
    campeon_real, tercero_real = determinar_campeon_y_tercero(resultados)
    
    # Categorías reales (se llenan cuando avance el torneo)
    categorias_reales = {
        "Figura": "", "Goleador": "", "Revelación": "",
        "Decepción": "", "Mejor 1era Fase": "", "Peor Equipo": "",
    }
    
    # --- Calcular puntos ---
    participantes = list(categorias_todos.keys())
    todos_puntajes = []
    
    barra = st.progress(0, text="Calculando puntos...")
    for i, part in enumerate(participantes):
        puntaje = calcular_puntuacion_total(
            participante=part,
            apuestas_grupos=apuestas_grupos,
            categorias_pred=categorias_todos.get(part, {}),
            total_results_pred=total_results_todos.get(part, {}),
            resultados_reales=resultados,
            equipos_reales_por_ronda=equipos_reales_por_ronda,
            categorias_reales=categorias_reales,
            campeon_real=campeon_real,
            tercero_real=tercero_real,
        )
        todos_puntajes.append(puntaje)
        barra.progress((i + 1) / len(participantes), text=f"Calculando {part}...")
    barra.empty()
    
    leaderboard = generar_leaderboard(todos_puntajes)
    
    # Guardar en session_state para otras páginas
    st.session_state["leaderboard"] = leaderboard
    st.session_state["todos_puntajes"] = todos_puntajes
    st.session_state["resultados"] = resultados
    
    # --- Top 3 visual ---
    if not leaderboard.empty:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(leaderboard) >= 1:
                l = leaderboard.iloc[0]
                st.markdown(
                    f'<div class="card-lider"><p class="posicion-1">🥇 #1</p>'
                    f'<h2 style="color:#ffd700;">{l["Participante"]}</h2>'
                    f'<p class="puntos-grandes">{int(l["Total"])}</p>'
                    f'<p style="color:#aaa;">puntos</p></div>',
                    unsafe_allow_html=True
                )
        with col2:
            if len(leaderboard) >= 2:
                s = leaderboard.iloc[1]
                st.markdown(
                    f'<div class="card-normal" style="border-color:#c0c0c0;">'
                    f'<p class="posicion-2">🥈 #2</p><h3>{s["Participante"]}</h3>'
                    f'<h2>{int(s["Total"])} pts</h2></div>',
                    unsafe_allow_html=True
                )
        with col3:
            if len(leaderboard) >= 3:
                t = leaderboard.iloc[2]
                st.markdown(
                    f'<div class="card-normal" style="border-color:#cd7f32;">'
                    f'<p class="posicion-3">🥉 #3</p><h3>{t["Participante"]}</h3>'
                    f'<h2>{int(t["Total"])} pts</h2></div>',
                    unsafe_allow_html=True
                )
    
    st.markdown("---")
    
    # --- Tabla completa ---
    st.markdown("### 📋 Tabla Completa")
    
    def estilizar(row):
        pos = row["Posición"]
        n = len(leaderboard)
        if pos == 1:
            return ['background-color: rgba(255,69,0,0.3); font-weight:bold'] * len(row)
        elif pos == 2:
            return ['background-color: rgba(192,192,192,0.15)'] * len(row)
        elif pos == 3:
            return ['background-color: rgba(205,127,50,0.15)'] * len(row)
        elif pos >= n - 2 and n > 5:
            return ['background-color: rgba(0,100,200,0.15); font-style:italic'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        leaderboard.style.apply(estilizar, axis=1),
        use_container_width=True, hide_index=True,
        height=min(len(leaderboard) * 40 + 60, 700),
    )
    
    # --- Gráfico apilado ---
    st.markdown("### 📊 Desglose de Puntos")
    
    fig = go.Figure()
    for cat, color in [
        ("Grupos", "#2ecc71"), ("Eliminatorias", "#3498db"),
        ("Campeón", "#f1c40f"), ("3ero", "#e67e22"),
        ("Especiales", "#9b59b6"), ("Penalidades", "#e74c3c"),
    ]:
        fig.add_trace(go.Bar(
            x=leaderboard["Participante"], y=leaderboard[cat],
            name=cat, marker_color=color,
        ))
    
    fig.update_layout(
        barmode='stack', template="plotly_dark", height=500,
        xaxis_title="Participante", yaxis_title="Puntos",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Mensajes sarcásticos ---
    st.markdown("---")
    st.markdown("### 💬 Mensajes del Día")
    n = len(leaderboard)
    for _, row in leaderboard.iterrows():
        pos = int(row["Posición"])
        if pos <= 3 or pos >= n - 2:
            msg = obtener_mensaje_posicion(
                row["Participante"], pos, n, int(row["Total"])
            )
            st.markdown(f"> {msg}")


def _mostrar_demo():
    """Leaderboard de demostración."""
    st.info("📊 Datos de demo. Subí los archivos Excel para ver datos reales.")
    demo = pd.DataFrame({
        "Posición": [1, 2, 3, 4, 5],
        "Participante": ["Demo A", "Demo B", "Demo C", "Demo D", "Demo E"],
        "Total": [145, 132, 128, 87, 42],
        "Grupos": [78, 72, 65, 45, 22], "Eliminatorias": [45, 40, 43, 28, 15],
        "Campeón": [30, 0, 0, 0, 0], "3ero": [0, 5, 0, 0, 0],
        "Especiales": [12, 20, 20, 24, 5], "Penalidades": [-20, -5, 0, -10, 0],
    })
    st.dataframe(demo, use_container_width=True, hide_index=True)


# --- Ejecutar ---
mostrar_leaderboard()
