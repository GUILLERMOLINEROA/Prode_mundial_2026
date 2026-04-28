import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="⚽ Panel Principal - PRODE Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

def cargar_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    cargar_css()

    # Toggle de simulacion y boton de recarga en el sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        usar_sim = st.toggle("🎮 Simulación", value=st.session_state.get("usar_simulacion", True))
        if usar_sim:
            fase_sim = st.selectbox("📅 Simular hasta:", 
                ["todo", "grupos", "16vos", "8vos", "4tos", "semis"],
                index=0)
            st.session_state["fase_simulacion"] = fase_sim
        st.session_state["usar_simulacion"] = usar_sim
        if st.button("🔄 Recargar datos"):
            from utils.data_loader import forzar_recarga
            forzar_recarga()
            st.rerun()

    # CARGAR TODOS LOS DATOS AL INICIO
    from utils.data_loader import cargar_todo
    with st.spinner("🔄 Cargando todos los datos del PRODE..."):
        exito = cargar_todo()

    # Titulo
    st.markdown('<h1 class="titulo-prode">⚽ PRODE MUNDIALISTA 2026 ⚽</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
        'Donde las amistades se prueban y los egos se destruyen.</p>', unsafe_allow_html=True)
    st.divider()

    if exito and "leaderboard" in st.session_state:
        leaderboard = st.session_state["leaderboard"]
        campeon = st.session_state.get("campeon_real", "")
        tercero = st.session_state.get("tercero_real", "")

        if campeon:
            st.success(f"🏆 Campeón: **{campeon}** | 🥉 3er puesto: **{tercero}**")

        # Ultimos 3 resultados
        from utils.api_football import obtener_ultimos_resultados
        resultados = st.session_state.get("resultados", pd.DataFrame())
        ultimos = obtener_ultimos_resultados(resultados, 3)
        if not ultimos.empty:
            st.markdown("#### ⚡ Últimos Resultados")
            cols = st.columns(3)
            for i, (_, p) in enumerate(ultimos.iterrows()):
                with cols[i]:
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

        # Mini leaderboard
        st.markdown("### 🏆 Posiciones Actuales")
        col1, col2, col3 = st.columns(3)
        if len(leaderboard) >= 1:
            l = leaderboard.iloc[0]
            col1.metric(f"🥇 {l['Participante']}", f"{int(l['Total'])} pts")
        if len(leaderboard) >= 2:
            s = leaderboard.iloc[1]
            col2.metric(f"🥈 {s['Participante']}", f"{int(s['Total'])} pts")
        if len(leaderboard) >= 3:
            t = leaderboard.iloc[2]
            col3.metric(f"🥉 {t['Participante']}", f"{int(t['Total'])} pts")
    else:
        st.warning("⚠️ No se pudieron cargar los datos. Verificá que hay archivos Excel en `data/participantes/`.")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🌍 FIFA World Cup 2026")
        st.markdown("**Sedes:** USA, México, Canadá\n\n**Equipos:** 48\n\n**Máximo:** 577 pts")
    with col2:
        st.markdown("### 📋 Cómo funciona")
        st.markdown("1. Cada participante completó su Excel\n2. Resultados de la API\n3. Puntos automáticos\n4. **El último... sufre.**")
    with col3:
        st.markdown("### 🏆 Premios")
        st.markdown("🥇 Gloria eterna\n🥈 Respeto condicional\n🥉 Mejor en Grupos\n💀 Vergüenza pública")

    st.markdown('<p style="text-align:center; font-size:1.1rem; margin-top:20px;">'
        '👈 Usá el menú lateral para navegar</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
