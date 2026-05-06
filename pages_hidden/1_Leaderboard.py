import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64
import json

from utils.excel_reader import cargar_todos_los_participantes
from utils.simulacion import generar_resultados_simulados, obtener_categorias_reales_simuladas
from utils.api_football import mapear_nombre_equipo, clasificar_ronda
from utils.scoring import calcular_puntuacion_total, generar_leaderboard
from utils.messages import obtener_mensaje_posicion
from utils.group_config import overrides_path, fotos_dir

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def cargar_overrides():
    """Carga overrides manuales desde data/overrides.json"""
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

def mostrar_leaderboard():
    st.markdown('<h1 class="titulo-prode">🏆 LEADERBOARD 🏆</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888;">Actualizado en tiempo real. Sin piedad. Sin misericordia.</p>', unsafe_allow_html=True)

    with st.spinner("🔄 Cargando apuestas..."):
        apuestas_grupos, pred_elim, categorias_todos, total_results_todos = cargar_todos_los_participantes()
    if not categorias_todos:
        st.warning("⚠️ No se encontraron archivos de participantes.")
        return

    st.markdown("---")
    usar_simulacion = st.toggle("🎮 Usar resultados SIMULADOS (para probar)", value=True)

    if usar_simulacion:
        st.info("🎮 Usando resultados simulados fijos para validación.")
        resultados = generar_resultados_simulados()
        categorias_reales = obtener_categorias_reales_simuladas()
    else:
        from utils.api_football import obtener_partidos_mundial
        with st.spinner("🔄 Obteniendo resultados de la API..."):
            resultados = obtener_partidos_mundial()
        if not resultados.empty:
            resultados["equipo_local"] = resultados["equipo_local"].apply(mapear_nombre_equipo)
            resultados["equipo_visitante"] = resultados["equipo_visitante"].apply(mapear_nombre_equipo)
        # Cargar overrides manuales
        overrides = cargar_overrides()
        categorias_reales = {
            "Figura": overrides.get("Figura", ""),
            "Goleador": overrides.get("Goleador", ""),
            "Revelación": overrides.get("Revelación", ""),
            "Decepción": overrides.get("Decepción", ""),
            "Mejor 1era Fase": overrides.get("Mejor 1era Fase", ""),
            "Peor Equipo": overrides.get("Peor Equipo", ""),
        }

    equipos_reales = extraer_equipos_reales_por_ronda(resultados)
    campeon_real, tercero_real = determinar_campeon_y_tercero(resultados)

    if campeon_real:
        st.success(f"🏆 Campeón: **{campeon_real}** | 🥉 3er puesto: **{tercero_real}**")

    # Mostrar ultimos 3 resultados
    from utils.api_football import obtener_ultimos_resultados
    ultimos = obtener_ultimos_resultados(resultados, 3)
    if not ultimos.empty:
        st.markdown("#### ⚡ Últimos Resultados")
        cols = st.columns(3)
        for i, (_, p) in enumerate(ultimos.iterrows()):
            with cols[i]:
                gl = int(p["goles_local"])
                gv = int(p["goles_visitante"])
                pen_txt = ""
                if pd.notna(p.get("penales_local")) and pd.notna(p.get("penales_visitante")):
                    pen_txt = f" (Pen {int(p['penales_local'])}-{int(p['penales_visitante'])})"
                st.markdown(
                    f'<div style="background:#1a1a2e; border:1px solid #333; border-radius:8px; '
                    f'padding:10px; text-align:center;">'
                    f'<small style="color:#888;">{p["ronda"]}</small><br>'
                    f'<b>{p["equipo_local"]}</b> {gl} - {gv} <b>{p["equipo_visitante"]}</b>'
                    f'{pen_txt}</div>', unsafe_allow_html=True)

    # Calcular puntos
    participantes = list(categorias_todos.keys())
    todos_puntajes = []
    barra = st.progress(0, text="Calculando puntos...")
    for i, part in enumerate(participantes):
        puntaje = calcular_puntuacion_total(
            participante=part, apuestas_grupos=apuestas_grupos,
            categorias_pred=categorias_todos.get(part, {}),
            total_results_pred=total_results_todos.get(part, {}),
            resultados_reales=resultados,
            equipos_reales_por_ronda=equipos_reales,
            categorias_reales=categorias_reales,
            campeon_real=campeon_real, tercero_real=tercero_real)
        todos_puntajes.append(puntaje)
        barra.progress((i + 1) / len(participantes), text=f"Calculando {part}...")
    barra.empty()

    leaderboard = generar_leaderboard(todos_puntajes)
    st.session_state["leaderboard"] = leaderboard
    st.session_state["todos_puntajes"] = todos_puntajes
    st.session_state["resultados"] = resultados
    st.session_state["categorias_reales"] = categorias_reales

    # Top 3
    if not leaderboard.empty:
        st.markdown("---")
        
        def foto_to_base64(nombre):
            for ext in [".png", ".jpg", ".jpeg"]:
                path = os.path.join(fotos_dir(), f"{nombre}{ext}")
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        data = base64.b64encode(f.read()).decode()
                    return f'<img src="data:image/{ext[1:]};base64,{data}" style="width:70px; border-radius:50%; margin:5px 0;">'
            return ''
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(leaderboard) >= 1:
                l = leaderboard.iloc[0]
                foto_html = foto_to_base64(l["Participante"])
                st.markdown(f'''<div class="card-lider" style="text-align:center;">
                    <p class="posicion-1">🥇 #1</p>
                    {foto_html}
                    <h2 style="color:#C8E600; margin:5px 0;">{l["Participante"]}</h2>
                    <p class="puntos-grandes" style="margin:0;">{int(l["Total"])}</p>
                    <p style="color:#AEC6CF; margin:0;">puntos</p>
                </div>''', unsafe_allow_html=True)
        
        with col2:
            if len(leaderboard) >= 2:
                s = leaderboard.iloc[1]
                foto_html = foto_to_base64(s["Participante"])
                st.markdown(f'''<div class="card-normal" style="border-color:#AEC6CF; text-align:center;">
                    <p class="posicion-2">🥈 #2</p>
                    {foto_html}
                    <h3 style="margin:5px 0;">{s["Participante"]}</h3>
                    <h2 style="margin:0;">{int(s["Total"])} pts</h2>
                </div>''', unsafe_allow_html=True)
        
        with col3:
            if len(leaderboard) >= 3:
                t = leaderboard.iloc[2]
                foto_html = foto_to_base64(t["Participante"])
                st.markdown(f'''<div class="card-normal" style="border-color:#E67E22; text-align:center;">
                    <p class="posicion-3">🥉 #3</p>
                    {foto_html}
                    <h3 style="margin:5px 0;">{t["Participante"]}</h3>
                    <h2 style="margin:0;">{int(t["Total"])} pts</h2>
                </div>''', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 Tabla Completa")

    # Selector de columnas
    with st.expander("⚙️ Personalizar columnas", expanded=False):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            mostrar_grupos = st.checkbox("Desglose Grupos", value=False)
        with col_b:
            mostrar_elim = st.checkbox("Desglose Eliminatorias", value=False)
        with col_c:
            mostrar_esp = st.checkbox("Desglose Especiales", value=False)
        with col_d:
            mostrar_pen = st.checkbox("Desglose Penalidades", value=False)

    # Construir columnas a mostrar
    cols_mostrar = ["Posición", "Participante", "Total"]
    if mostrar_grupos:
        cols_mostrar.extend(["Grupos L/E/V", "Grupos Exacto"])
    else:
        cols_mostrar.append("Grupos")
    if mostrar_elim:
        cols_mostrar.extend(["16vos", "8vos", "4tos", "Semis", "Final"])
    else:
        cols_mostrar.append("Eliminatorias")
    cols_mostrar.extend(["Campeón", "3ero"])
    if mostrar_esp:
        cols_mostrar.extend(["Figura", "Goleador", "Revelación", "Decepción", "Mejor 1era Fase", "Peor Equipo"])
    else:
        cols_mostrar.append("Especiales")
    if mostrar_pen:
        cols_mostrar.extend(["Pen. Revelación", "Pen. Campeón", "Pen. Peor Equipo", "Pen. Decepción"])
    else:
        cols_mostrar.append("Penalidades")

    cols_mostrar = [c for c in cols_mostrar if c in leaderboard.columns]
    df_mostrar = leaderboard[cols_mostrar]

    def estilizar(row):
        pos = row["Posición"]
        n = len(df_mostrar)
        if pos == 1: return ['background-color: rgba(255,69,0,0.3); font-weight:bold'] * len(row)
        elif pos == 2: return ['background-color: rgba(192,192,192,0.15)'] * len(row)
        elif pos == 3: return ['background-color: rgba(205,127,50,0.15)'] * len(row)
        elif pos >= n - 2 and n > 5: return ['background-color: rgba(0,100,200,0.15); font-style:italic'] * len(row)
        return [''] * len(row)

    st.dataframe(df_mostrar.style.apply(estilizar, axis=1),
        use_container_width=True, hide_index=True,
        height=min(len(leaderboard) * 40 + 60, 700))

    # Grafico
    st.markdown("### 📊 Desglose de Puntos")
    fig = go.Figure()
    # Construir barras manualmente con base = penalidad
    # Cada participante empieza desde su penalidad (piso negativo)
    categorias_barras = [("Grupos", "#C8E600"), ("Eliminatorias", "#4A90D9"),
        ("Campeón", "#E67E22"), ("3ero", "#F39C12"), ("Especiales", "#9B59B6")]
    
    # Calcular la base acumulada para cada participante
    for cat_idx, (cat, color) in enumerate(categorias_barras):
        bases = []
        for _, row in leaderboard.iterrows():
            pen = float(row["Penalidades"])
            # Sumar las categorias anteriores para calcular la base
            base = pen
            for prev_cat, _ in categorias_barras[:cat_idx]:
                base += float(row[prev_cat])
            bases.append(base)
        
        fig.add_trace(go.Bar(
            x=leaderboard["Participante"],
            y=leaderboard[cat],
            base=bases,
            name=cat,
            marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + cat + ": %{y}<extra></extra>",
        ))
    
    # Anotaciones de penalidad en la zona negativa
    for _, row in leaderboard.iterrows():
        pen = int(row["Penalidades"])
        if pen < 0:
            fig.add_annotation(
                x=row["Participante"], y=pen/2,
                text=f"<b>{pen}</b>",
                showarrow=False,
                font=dict(color="#E74C3C", size=11, family="Arial Black"),
            )
    
    fig.update_layout(barmode="overlay", template="plotly_dark", height=550,
        xaxis_title="Participante", yaxis_title="Puntos",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            zeroline=True, zerolinecolor="rgba(255,255,255,0.4)", zerolinewidth=2,
        ),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)
    # Verificar si hay penalidades para el comentario toxico
    hay_penalidades = (leaderboard["Penalidades"] < 0).any()
    if hay_penalidades:
        penalizados = leaderboard[leaderboard["Penalidades"] < 0]["Participante"].tolist()
        if len(penalizados) == 1:
            msg_pen = f"⚠️ *{penalizados[0]} arranca desde el subsuelo por sus predicciones desastrosas. Mientras otros parten de cero, vos partís desde la vergüenza.*"
        elif len(penalizados) <= 3:
            msg_pen = f"⚠️ *{', '.join(penalizados[:-1])} y {penalizados[-1]}: sus predicciones fueron tan malas que ni siquiera arrancan de cero. Bienvenidos al sótano del PRODE.*"
        else:
            msg_pen = f"⚠️ *{len(penalizados)} de {len(leaderboard)} participantes arrancan en números rojos. ¿Esto es un PRODE o un cementerio de predicciones? Las penalidades no perdonan.*"
        st.markdown(f"> {msg_pen}")

    # Mensajes
    st.markdown("---")
    st.markdown("### 💬 Mensajes del Día")
    n = len(leaderboard)
    for _, row in leaderboard.iterrows():
        pos = int(row["Posición"])
        if pos <= 3 or pos >= n - 2:
            msg = obtener_mensaje_posicion(row["Participante"], pos, n, int(row["Total"]))
            st.markdown(f"> {msg}")

mostrar_leaderboard()
