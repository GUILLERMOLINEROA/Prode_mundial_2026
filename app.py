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

    # Banner de estado API
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

    # Lista de participantes con comentarios picantes sobre sus campeones
    if exito and "categorias_todos" in st.session_state:
        st.divider()
        st.markdown("### 🎭 Los Apostadores y sus Delirios")
        st.markdown("*Cada uno eligió a su campeón... algunos con más criterio que otros.*")
        st.markdown("")
        
        categorias_todos = st.session_state.get("categorias_todos", {})
        
        # Comentarios picantes - contexto: oficina ARGENTINA
        comentarios_campeon = {
            "Argentina": "Obvio, papá. ¿Quién no va con la Scaloneta? Ah sí... los traidores de abajo.",
            "Brasil": "Ir con Brasil siendo argentino es como aplaudir un gol en contra. Traidor.",
            "Francia": "¿Francia? ¿Después de lo que nos hicieron sufrir en Qatar? Memoria selectiva la tuya.",
            "Alemania": "Eficiencia alemana. Aburrido pero respetable. Al menos no es Inglaterra.",
            "España": "Tiki-taka hasta que los eliminen en cuartos como siempre.",
            "Inglaterra": "🚨 ALERTA: TRAIDOR A LA PATRIA DETECTADO. ¿Inglaterra? ¿EN SERIO? Las Malvinas son argentinas y este pone a Inglaterra campeón. Que le revisen el DNI.",
            "Portugal": "CR7 con andador. Romántico pero delirante.",
            "Paises Bajos": "La naranja mecánica: siempre de novias, nunca de novia.",
            "Belgica": "Generación dorada que se oxida sin ganar nada. Dale, esta vez sí...",
            "Uruguay": "Los primos del otro lado del charco. Garra charrúa con mate y nostalgia.",
            "Colombia": "James, Díaz y mucha cumbia. ¿Alcanza? Spoiler: probablemente no.",
            "Croacia": "Modric tiene más mundiales encima que años de vida. Guerreros.",
            "Mexico": "Quinto partido, sexto partido... algún día van a pasar de octavos. ¿No?",
            "Estados Unidos": "Campeón de local? Esto no es el Super Bowl, amigo.",
            "Japon": "Si el anime nos enseñó algo es que Japón siempre gana al final. ¿Será?",
            "Marruecos": "Los leones del Atlas rugieron en Qatar. ¿Pueden rugir más fuerte?",
            "Escocia": "Escocia campeón... y yo soy astronauta. Puntos por la creatividad.",
            "Noruega": "Haaland solo contra el mundo. Un vikingo con gol pero sin equipo.",
            "Suiza": "Neutral en todo, hasta en las apuestas. Tibio.",
            "Senegal": "Los Leones de la Teranga. Valiente apuesta, hay que reconocerlo.",
            "Ecuador": "¡Sí se puede! Gritó la hinchada. La historia dice que no.",
            "Canada": "¿Canadá campeón del mundo? Esto no es hockey sobre hielo, amigo.",
        }
        
        comentario_default_list = [
            "¿Esto va en serio o le hackearon el Excel?",
            "Apuesta tan arriesgada que debería pagar impuestos.",
            "Le puso más huevos que criterio. Respetable.",
            "Si esto sale, nos retiramos todos del PRODE.",
            "Audaz. Delirante. Probablemente borracho cuando lo completó.",
            "Eligió con el corazón. Lástima que el corazón no sabe de fútbol.",
        ]
        
        import random
        for i, (nombre, cats) in enumerate(sorted(categorias_todos.items()), 1):
            campeon = cats.get("Campeon", "No definido")
            comentario = comentarios_campeon.get(campeon, "")
            if not comentario:
                random.seed(hash(nombre + campeon))
                comentario = random.choice(comentario_default_list)
            
            # Buscar foto
            from utils.data_loader import foto_participante
            foto = foto_participante(nombre)
            
            col_num, col_foto, col_info = st.columns([0.5, 0.8, 10])
            with col_num:
                st.markdown(f"**{i}.**")
            with col_foto:
                if foto:
                    st.image(foto, width=35)
            with col_info:
                comentario_html = f'<span style="color: #888; font-size: 0.9rem;">{comentario}</span>'
                st.markdown(f'**{nombre}** → 🏆 *{campeon}*')
                st.markdown(comentario_html, unsafe_allow_html=True)
if __name__ == "__main__":
    main()
