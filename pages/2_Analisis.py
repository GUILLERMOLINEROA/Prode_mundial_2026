import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from utils.messages import obtener_mensaje_posicion, obtener_titulo_ficha

st.set_page_config(page_title="Análisis", page_icon="🔍", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="titulo-prode">🔍 ANÁLISIS DE PARTICIPANTE</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888;">Elegí a tu víctima... digo, compañero/a.</p>', unsafe_allow_html=True)

    leaderboard = st.session_state.get("leaderboard", pd.DataFrame())
    todos_puntajes = st.session_state.get("todos_puntajes", [])

    if leaderboard.empty or not todos_puntajes:
        st.warning("⚠️ Primero andá al **🏆 Leaderboard** para cargar los datos.")
        return

    # Obtener categorias reales del session_state o calcularlas
    categorias_reales = st.session_state.get("categorias_reales", {})
    if not categorias_reales:
        # Intentar calcularlas desde los resultados
        resultados = st.session_state.get("resultados", pd.DataFrame())
        if not resultados.empty:
            from utils.special_categories import calcular_todas_las_categorias
            categorias_reales = calcular_todas_las_categorias(resultados)
            # Agregar overrides manuales
            import json
            overrides_path = os.path.join("data", "overrides.json")
            if os.path.exists(overrides_path):
                with open(overrides_path) as f:
                    overrides = json.load(f)
                for k, v in overrides.items():
                    if v and k in categorias_reales:
                        categorias_reales[k] = v

    participantes = leaderboard["Participante"].tolist()
    seleccionado = st.selectbox("🎯 Seleccioná un participante:", participantes, index=0)

    if not seleccionado:
        return

    fila = leaderboard[leaderboard["Participante"] == seleccionado].iloc[0]
    posicion = int(fila["Posición"])
    total_p = len(leaderboard)
    puntos = int(fila["Total"])

    puntaje = None
    for p in todos_puntajes:
        if p["participante"] == seleccionado:
            puntaje = p
            break

    if not puntaje:
        st.error("No se encontraron datos del participante.")
        return

    st.markdown("---")

    # Foto de perfil
    def foto_participante(nombre):
        for ext in [".png", ".jpg", ".jpeg"]:
            path = os.path.join("assets", "fotos", f"{nombre}{ext}")
            if os.path.exists(path):
                return path
        return None

    titulo = obtener_titulo_ficha(posicion, total_p)
    col_foto, col_info = st.columns([1, 4])
    with col_foto:
        foto = foto_participante(seleccionado)
        if foto:
            st.image(foto, width=120)
    with col_info:
        st.markdown(f"## {titulo}")
        st.markdown(f"### {seleccionado}")

    mensaje = obtener_mensaje_posicion(seleccionado, posicion, total_p, puntos)
    color_borde = "#ff4500" if posicion <= 3 else "#1e90ff" if posicion >= total_p - 2 else "#555"
    st.markdown(
        f'<div style="background: linear-gradient(135deg, #1a1a2e, #16213e); '
        f'border-left: 4px solid {color_borde}; padding: 20px; '
        f'border-radius: 10px; margin: 20px 0; font-size: 1.1rem;">'
        f'{mensaje}</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🏅 Posición", f"#{posicion}")
    col2.metric("📊 Total", puntos)
    col3.metric("⚽ Grupos", puntaje["pts_grupos"])
    col4.metric("🏟️ Eliminatorias", puntaje["pts_eliminatorias"])
    pen = puntaje["pts_penalidades"]
    col5.metric("⚠️ Penalidades", pen,
        delta=f"{pen}" if pen < 0 else "Ninguna",
        delta_color="inverse" if pen < 0 else "off")

    st.markdown("---")

    # Radar
    st.markdown("### 🕸️ Rendimiento por Fase vs. Promedio de la Oficina")
    categorias_radar = ["Fase de Grupos", "16vos", "8vos", "4tos", "Semis/Final/Campeón", "Especiales"]
    pts_ronda = puntaje.get("pts_por_ronda_elim", {})
    valores_part = [
        puntaje["pts_grupos"], pts_ronda.get("16vos", 0), pts_ronda.get("8vos", 0),
        pts_ronda.get("4tos", 0),
        pts_ronda.get("semis", 0) + pts_ronda.get("final", 0) + puntaje["pts_campeon"],
        puntaje["pts_especiales"]]

    promedios = [0.0] * len(categorias_radar)
    n = len(todos_puntajes)
    for p in todos_puntajes:
        pr = p.get("pts_por_ronda_elim", {})
        promedios[0] += p["pts_grupos"]
        promedios[1] += pr.get("16vos", 0)
        promedios[2] += pr.get("8vos", 0)
        promedios[3] += pr.get("4tos", 0)
        promedios[4] += pr.get("semis", 0) + pr.get("final", 0) + p["pts_campeon"]
        promedios[5] += p["pts_especiales"]
    if n > 0:
        promedios = [v / n for v in promedios]

    # Calcular valores del primero y ultimo
    puntajes_ordenados = sorted(todos_puntajes, key=lambda x: x['total'], reverse=True)
    primero = puntajes_ordenados[0]
    ultimo = puntajes_ordenados[-1]
    
    def vals_de_puntaje(p):
        pr = p.get('pts_por_ronda_elim', {})
        return [
            p['pts_grupos'], pr.get('16vos',0), pr.get('8vos',0), pr.get('4tos',0),
            pr.get('semis',0)+pr.get('final',0)+p['pts_campeon'], p['pts_especiales']
        ]
    
    vals_primero = vals_de_puntaje(primero)
    vals_ultimo = vals_de_puntaje(ultimo)
    
    fig = go.Figure()
    
    # Primero (dorado, punteado)
    if primero['participante'] != seleccionado:
        fig.add_trace(go.Scatterpolar(r=vals_primero+[vals_primero[0]], theta=categorias_radar+[categorias_radar[0]],
            fill='toself', name=f"🥇 {primero['participante']}",
            line_color='#ffd700', fillcolor='rgba(255,215,0,0.1)',
            line=dict(width=2, dash='dot')))
    
    # Ultimo (azul hielo, punteado)
    if ultimo['participante'] != seleccionado:
        fig.add_trace(go.Scatterpolar(r=vals_ultimo+[vals_ultimo[0]], theta=categorias_radar+[categorias_radar[0]],
            fill='toself', name=f"💀 {ultimo['participante']}",
            line_color='#00bfff', fillcolor='rgba(0,191,255,0.05)',
            line=dict(width=2, dash='dot')))
    
    # Participante seleccionado (naranja, prominente)
    fig.add_trace(go.Scatterpolar(r=valores_part+[valores_part[0]], theta=categorias_radar+[categorias_radar[0]],
        fill='toself', name=seleccionado,
        line_color='#ff4500', fillcolor='rgba(255,69,0,0.3)',
        line=dict(width=3)))
    
    # Promedio oficina
    fig.add_trace(go.Scatterpolar(r=promedios+[promedios[0]], theta=categorias_radar+[categorias_radar[0]],
        fill='toself', name='Promedio Oficina',
        line_color='#1e90ff', fillcolor='rgba(30,144,255,0.15)',
        line=dict(width=2)))
    fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)',
        radialaxis=dict(visible=True, gridcolor='rgba(255,255,255,0.1)')),
        showlegend=True, template="plotly_dark", height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Errores vs Aciertos
    st.markdown("### 💀 Peores Errores vs. ✨ Mejores Aciertos")
    detalle = puntaje.get("detalle_grupos", pd.DataFrame())
    if not isinstance(detalle, pd.DataFrame) or detalle.empty:
        st.info("No hay datos de partidos jugados todavía.")
    else:
        jugados = detalle[detalle["estado"] == "jugado"]
        if jugados.empty:
            st.info("Aún no se jugaron partidos.")
        else:
            col_err, col_ok = st.columns(2)
            with col_err:
                st.markdown("#### 💀 Los Peores Fallos")
                fallos = jugados[~jugados["acierto_ganador"]].head(10)
                if not fallos.empty:
                    for _, f in fallos.iterrows():
                        st.markdown(f"- **{f['equipo_local']} vs {f['equipo_visitante']}**: "
                            f"Apostó `{f['pred_local']}-{f['pred_visitante']}`, "
                            f"fue `{f['real_local']}-{f['real_visitante']}` 😬")
                else:
                    st.markdown("*Increíblemente, no tiene fallos (por ahora)*")
            with col_ok:
                st.markdown("#### ✨ Resultados Exactos")
                exactos = jugados[jugados["acierto_exacto"]].head(10)
                if not exactos.empty:
                    for _, a in exactos.iterrows():
                        st.markdown(f"- **{a['equipo_local']} vs {a['equipo_visitante']}**: "
                            f"`{a['pred_local']}-{a['pred_visitante']}` 🎯")
                else:
                    st.markdown("*Sin resultados exactos. Cero. Nada. Vergüenza.*")

            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            total_j = len(jugados)
            ac_gan = int(jugados["acierto_ganador"].sum())
            ac_ex = int(jugados["acierto_exacto"].sum())
            tasa = (ac_gan / total_j * 100) if total_j > 0 else 0
            c1.metric("Partidos Jugados", total_j)
            c2.metric("Ganador Acertado", f"{ac_gan}/{total_j}")
            c3.metric("Resultado Exacto", f"{ac_ex}/{total_j}")
            c4.metric("Tasa de Acierto", f"{tasa:.1f}%")

    st.markdown("---")

    # Categorias Especiales - AHORA CON COMPARACION
    st.markdown("### 🎰 Apuestas Especiales")

    categorias = puntaje.get("categorias", {})
    aciertos_esp = puntaje.get("aciertos_especiales", {})

    cat_items = [
        ("Figura", "⭐", 12), ("Goleador", "⚽", 12), ("Revelación", "🌟", 12),
        ("Decepción", "📉", 12), ("Mejor 1era Fase", "🏅", 8), ("Peor Equipo", "💩", 8),
    ]

    cols = st.columns(3)
    for i, (cat, emoji, pts) in enumerate(cat_items):
        valor_pred = categorias.get(cat, "")
        valor_real = categorias_reales.get(cat, "")
        acerto = aciertos_esp.get(cat, False)

        # Determinar estado
        if not valor_pred:
            color = "#555"
            estado = "Sin apuesta"
            icono = "❓"
        elif not valor_real:
            color = "#f39c12"
            estado = "⏳ Pendiente"
            icono = "⏳"
        elif acerto:
            color = "#2ecc71"
            estado = "✅ ¡ACERTÓ!"
            icono = "✅"
        else:
            color = "#e74c3c"
            estado = "❌ Falló"
            icono = "❌"

        with cols[i % 3]:
            st.markdown(
                f'<div style="background: #1a1a2e; border: 2px solid {color}; '
                f'border-radius: 10px; padding: 15px; margin: 5px 0; text-align: center;">'
                f'<h4>{emoji} {cat}</h4>'
                f'<p style="font-size: 1.1rem;"><b>Apostó:</b> {valor_pred or "—"}</p>'
                f'<p style="font-size: 1.1rem; color: {color};"><b>Real:</b> {valor_real or "Por definir"}</p>'
                f'<p style="color: {color}; font-size: 1.2rem; font-weight: bold;">'
                f'{icono} {estado} ({pts} pts)</p></div>',
                unsafe_allow_html=True)

    # Penalidades
    if puntaje["razones_penalidad"]:
        st.markdown("---")
        st.markdown("### 🚨 PENALIDADES")
        for razon in puntaje["razones_penalidad"]:
            st.error(razon)

    # Confetti para el lider
    if posicion == 1:
        try:
            from streamlit_extras.let_it_rain import rain
            rain(emoji="🏆", font_size=30, falling_speed=3, animation_length=3)
        except ImportError:
            st.balloons()

main()
