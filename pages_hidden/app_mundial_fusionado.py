import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64
import random

st.set_page_config(
    page_title="PRODE Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

def cargar_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def foto_to_base64(nombre):
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join("assets", "fotos", f"{nombre}{ext}")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/{ext[1:]};base64,{data}" style="width:70px; border-radius:50%; margin:5px 0;">'
    return ""

def main():
    cargar_css()

    # =================================================================
    # SIDEBAR: Banner API + Configuracion
    # =================================================================
    from utils.api_football import obtener_partidos_mundial, _hay_api_key
    with st.sidebar:
        if _hay_api_key():
            api_data = obtener_partidos_mundial()
            if not api_data.empty:
                ft = len(api_data[api_data["estado"] == "FT"])
                ns = len(api_data[api_data["estado"] == "NS"])
                if ft > 0:
                    st.success(f"🟢 API EN VIVO — {ft} partidos jugados")
                else:
                    st.info(f"🔵 API conectada — {ns} partidos programados")
            else:
                st.warning("🟡 API configurada — Sin datos del Mundial 2026 aún")
        else:
            st.caption("⚪ Sin API key — Modo simulación")

    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        usar_sim = st.toggle("🎮 Simulación", value=st.session_state.get("usar_simulacion", True))
        if usar_sim:
            fase_sim = st.selectbox("📅 Simular hasta:",
                ["todo", "grupos", "16vos", "8vos", "4tos", "semis"], index=0)
            st.session_state["fase_simulacion"] = fase_sim
        st.session_state["usar_simulacion"] = usar_sim
        if st.button("🔄 Recargar datos"):
            from utils.data_loader import forzar_recarga
            forzar_recarga()
            st.rerun()

    # =================================================================
    # CARGA CENTRALIZADA
    # =================================================================
    from utils.data_loader import cargar_todo, foto_participante
    with st.spinner("🔄 Cargando todos los datos del PRODE..."):
        exito = cargar_todo()

    # =================================================================
    # TITULO
    # =================================================================
    # Banner
    banner_path = os.path.join("assets", "banner.png")
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as img_b:
            b64_banner = base64.b64encode(img_b.read()).decode()
        st.markdown(
            f'<div style="text-align:center; margin-bottom:20px;">'
            f'<img src="data:image/png;base64,{b64_banner}" style="max-width:100%; border-radius:10px;">'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown('<h1 class="titulo-prode">⚽ PRODE MUNDIALISTA 2026 ⚽</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
        'Donde las amistades se prueban y los egos se destruyen.</p>', unsafe_allow_html=True)
    st.divider()

    if not exito or "leaderboard" not in st.session_state:
        st.warning("⚠️ No se pudieron cargar los datos.")
        return

    leaderboard = st.session_state["leaderboard"]
    resultados = st.session_state.get("resultados", pd.DataFrame())
    campeon = st.session_state.get("campeon_real", "")
    tercero = st.session_state.get("tercero_real", "")

    # =================================================================
    # CAMPEON + ULTIMOS RESULTADOS
    # =================================================================
    if campeon:
        st.success(f"🏆 Campeón: **{campeon}** | 🥉 3er puesto: **{tercero}**")

    from utils.api_football import obtener_ultimos_resultados
    ultimos = obtener_ultimos_resultados(resultados, 3)
    if not ultimos.empty:
        st.markdown("#### ⚡ Últimos Resultados")
        cols_res = st.columns(3)
        for i, (_, p) in enumerate(ultimos.iterrows()):
            with cols_res[i]:
                gl, gv = int(p["goles_local"]), int(p["goles_visitante"])
                pen = ""
                if pd.notna(p.get("penales_local")) and pd.notna(p.get("penales_visitante")):
                    pen = f" (Pen {int(p['penales_local'])}-{int(p['penales_visitante'])})"
                st.markdown(
                    f'<div style="background:#1a1a2e; border:1px solid #333; border-radius:8px; '
                    f'padding:10px; text-align:center;">'
                    f'<small style="color:#888;">{p["ronda"]}</small><br>'
                    f'<b>{p["equipo_local"]}</b> {gl}-{gv} <b>{p["equipo_visitante"]}</b>{pen}</div>',
                    unsafe_allow_html=True)
    st.divider()

    # =================================================================
    # TOP 3 CON FOTOS
    # =================================================================
    if not leaderboard.empty:
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

    # =================================================================
    # TABLA COMPLETA CON SELECTOR DE COLUMNAS
    # =================================================================
    st.markdown("---")
    st.markdown("### 📋 Tabla Completa")

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
        if pos == 1:
            return ['background-color: rgba(255,69,0,0.3); font-weight:bold'] * len(row)
        elif pos == 2:
            return ['background-color: rgba(192,192,192,0.15)'] * len(row)
        elif pos == 3:
            return ['background-color: rgba(205,127,50,0.15)'] * len(row)
        elif pos >= n - 2 and n > 5:
            return ['background-color: rgba(0,100,200,0.15); font-style:italic'] * len(row)
        return [''] * len(row)

    st.dataframe(df_mostrar.style.apply(estilizar, axis=1),
        use_container_width=True, hide_index=True,
        height=min(len(leaderboard) * 40 + 60, 700))

    # =================================================================
    # GRAFICO DE BARRAS CON PENALIDADES
    # =================================================================
    st.markdown("### 📊 Desglose de Puntos")
    fig = go.Figure()

    categorias_barras = [
        ("Grupos", "#C8E600"), ("Eliminatorias", "#4A90D9"),
        ("Campeón", "#E67E22"), ("3ero", "#F39C12"), ("Especiales", "#9B59B6")
    ]

    for cat_idx, (cat, color) in enumerate(categorias_barras):
        bases = []
        for _, row in leaderboard.iterrows():
            pen = float(row["Penalidades"])
            base = pen
            for prev_cat, _ in categorias_barras[:cat_idx]:
                base += float(row[prev_cat])
            bases.append(base)
        fig.add_trace(go.Bar(
            x=leaderboard["Participante"], y=leaderboard[cat],
            base=bases, name=cat, marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + cat + ": %{y}<extra></extra>",
        ))

    for _, row in leaderboard.iterrows():
        pen = int(row["Penalidades"])
        if pen < 0:
            fig.add_annotation(
                x=row["Participante"], y=pen / 2,
                text=f"<b>{pen}</b>", showarrow=False,
                font=dict(color="#E74C3C", size=11, family="Arial Black"),
            )

    fig.update_layout(
        barmode="overlay", template="plotly_dark", height=550,
        xaxis_title="Participante", yaxis_title="Puntos",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(zeroline=True, zerolinecolor="rgba(255,255,255,0.4)", zerolinewidth=2),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Comentario toxico para penalizados
    hay_penalidades = (leaderboard["Penalidades"] < 0).any()
    if hay_penalidades:
        penalizados = leaderboard[leaderboard["Penalidades"] < 0]["Participante"].tolist()
        if len(penalizados) == 1:
            msg_pen = f"⚠️ _{penalizados[0]} arranca desde el subsuelo por sus predicciones desastrosas._"
        elif len(penalizados) <= 3:
            msg_pen = f"⚠️ _{', '.join(penalizados[:-1])} y {penalizados[-1]}: arrancan en números rojos. Bienvenidos al sótano del PRODE._"
        else:
            msg_pen = f"⚠️ _{len(penalizados)} de {len(leaderboard)} arrancan en rojo. ¿Esto es un PRODE o un cementerio de predicciones?_"
        st.markdown(f"> {msg_pen}")

    # =================================================================
    # MENSAJES TOXICOS POR POSICION
    # =================================================================
    from utils.messages import obtener_mensaje_posicion
    st.markdown("---")
    st.markdown("### 💬 Mensajes del Día")
    n = len(leaderboard)
    for _, row in leaderboard.iterrows():
        pos = int(row["Posición"])
        if pos <= 3 or pos >= n - 2:
            msg = obtener_mensaje_posicion(row["Participante"], pos, n, int(row["Total"]))
            st.markdown(f"> {msg}")

    # =================================================================
    # INFO GENERAL + APOSTADORES (colapsable)
    # =================================================================
    st.divider()
    with st.expander("🌍 Info del PRODE", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🌍 FIFA World Cup 2026")
            st.markdown("**Sedes:** USA, México, Canadá\n\n**Equipos:** 48\n\n**Máximo:** 431 pts")
        with col2:
            st.markdown("### 📋 Cómo funciona")
            st.markdown("1. Cada participante completó su Excel\n2. Resultados de la API\n3. Puntos automáticos\n4. **El último... sufre.**")
        with col3:
            st.markdown("### 🏆 Premios")
            st.markdown("🥇 Gloria eterna\n🥈 Respeto condicional\n🥉 Mejor en Grupos\n💀 Vergüenza pública")

    # Apostadores con comentarios
    if "categorias_todos" in st.session_state:
        with st.expander("🎭 Los Apostadores y sus Delirios", expanded=False):
            categorias_todos = st.session_state.get("categorias_todos", {})
            comentarios_campeon = {
                "Argentina": "Obvio, papá. ¿Quién no va con la Scaloneta?",
                "Brasil": "Ir con Brasil siendo argentino es como aplaudir un gol en contra. Traidor.",
                "Francia": "¿Francia? ¿Después de Qatar? Memoria selectiva.",
                "Alemania": "Eficiencia alemana. Aburrido pero respetable.",
                "España": "Tiki-taka hasta que los eliminen en cuartos.",
                "Inglaterra": "🚨 TRAIDOR A LA PATRIA DETECTADO. Las Malvinas son argentinas.",
                "Portugal": "CR7 con andador. Romántico pero delirante.",
                "Paises Bajos": "La naranja mecánica: siempre de novias, nunca de novia.",
                "Belgica": "Generación dorada que se oxida sin ganar nada.",
                "Uruguay": "Garra charrúa con mate y nostalgia.",
                "Colombia": "James, Díaz y mucha cumbia. ¿Alcanza?",
                "Croacia": "Modric tiene más mundiales que años de vida.",
                "Mexico": "Algún día van a pasar de octavos. ¿No?",
                "Estados Unidos": "Esto no es el Super Bowl, amigo.",
                "Japon": "Si el anime enseñó algo es que Japón siempre gana al final.",
                "Marruecos": "Los leones del Atlas. ¿Pueden rugir más fuerte?",
                "Escocia": "Escocia campeón... y yo soy astronauta.",
                "Noruega": "Haaland solo contra el mundo.",
                "Suiza": "Neutral en todo, hasta en las apuestas.",
                "Senegal": "Los Leones de la Teranga. Valiente apuesta.",
                "Ecuador": "¡Sí se puede! La historia dice que no.",
                "Canada": "Esto no es hockey sobre hielo, amigo.",
            }
            comentario_default_list = [
                "¿Esto va en serio o le hackearon el Excel?",
                "Apuesta tan arriesgada que debería pagar impuestos.",
                "Le puso más huevos que criterio. Respetable.",
                "Si esto sale, nos retiramos todos del PRODE.",
                "Audaz. Delirante. Probablemente borracho cuando lo completó.",
                "Eligió con el corazón. Lástima que el corazón no sabe de fútbol.",
            ]

            for i, (nombre, cats) in enumerate(sorted(categorias_todos.items()), 1):
                camp = cats.get("Campeon", "No definido")
                comentario = comentarios_campeon.get(camp, "")
                if not comentario:
                    random.seed(hash(nombre + camp))
                    comentario = random.choice(comentario_default_list)

                foto = foto_participante(nombre)
                col_num, col_foto, col_info = st.columns([0.5, 0.8, 10])
                with col_num:
                    st.markdown(f"**{i}.**")
                with col_foto:
                    if foto:
                        st.image(foto, width=35)
                with col_info:
                    st.markdown(f'**{nombre}** → 🏆 _{camp}_')
                    st.markdown(f'<span style="color: #888; font-size: 0.9rem;">{comentario}</span>',
                        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
