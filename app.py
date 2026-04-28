import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="⚽ PRODE Mundial 2026",
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
    
    st.markdown(
        '<h1 class="titulo-prode">⚽ PRODE MUNDIALISTA 2026 ⚽</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
        'Donde las amistades se prueban y los egos se destruyen.'
        '</p>',
        unsafe_allow_html=True
    )
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🌍 FIFA World Cup 2026")
        st.markdown(
            "**Sedes:** Estados Unidos, México, Canadá\n\n"
            "**Equipos:** 48 selecciones\n\n"
            "**Partidos:** 104 partidos\n\n"
            "**Máximo posible:** 577 puntos"
        )
    
    with col2:
        st.markdown("### 📋 Cómo funciona")
        st.markdown(
            "1. Cada participante completó su Excel con las apuestas\n"
            "2. Los resultados se actualizan desde la API de fútbol\n"
            "3. Los puntos se calculan automáticamente\n"
            "4. **El que más puntos tenga, gana. El último... sufre.**"
        )
    
    with col3:
        st.markdown("### 🏆 Premios")
        st.markdown(
            "- 🥇 **1er lugar:** Gloria eterna + premio\n"
            "- 🥈 **2do lugar:** Respeto condicional\n"
            "- 🥉 **3er lugar:** Mejor en Fase de Grupos\n"
            "- 💀 **Último lugar:** Vergüenza pública"
        )
    
    st.divider()
    
    st.markdown("### 📊 Sistema de Puntuación")
    
    with st.expander("Ver sistema de puntuación completo", expanded=False):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("#### ✅ Puntos Positivos")
            puntos_data = {
                "Categoría": [
                    "Ganador (grupos)", "Resultado exacto (grupos)",
                    "16vos (por equipo)", "8vos (por equipo)",
                    "4tos (por equipo)", "Semis (por equipo)",
                    "Final (por equipo)", "3er puesto", "Campeón",
                    "Figura", "Goleador", "Revelación", "Decepción",
                    "Mejor 1era Fase", "Peor Equipo"
                ],
                "Pts": [1, 1, 1, 4, 8, 15, 25, 5, 30, 12, 12, 12, 12, 8, 8],
                "Cant": [104, 104, 32, 16, 8, 4, 2, 1, 1, 1, 1, 1, 1, 1, 1],
                "Máx": [104, 104, 32, 64, 64, 60, 50, 5, 30, 12, 12, 12, 12, 8, 8],
            }
            st.dataframe(pd.DataFrame(puntos_data), hide_index=True, use_container_width=True)
            st.markdown("**Total máximo posible: 577 puntos**")
        
        with col_b:
            st.markdown("#### ⚠️ Penalidades")
            pen_data = {
                "Situación": [
                    "Revelación se queda en grupos",
                    "Campeón no llega a 4tos",
                    "Peor equipo pasa de grupos",
                    "Decepción llega a Semis",
                ],
                "Penalidad": [-20, -20, -10, -20],
            }
            st.dataframe(pd.DataFrame(pen_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    st.markdown("### ⚙️ Estado del Sistema")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    participantes_dir = os.path.join("data", "participantes")
    archivos_excel = []
    if os.path.exists(participantes_dir):
        archivos_excel = [
            f for f in os.listdir(participantes_dir)
            if f.endswith((".xlsm", ".xlsx"))
        ]
    
    with col_s1:
        if archivos_excel:
            st.success(f"✅ {len(archivos_excel)} archivos de participantes encontrados")
            with st.expander("Ver participantes"):
                for f in sorted(archivos_excel):
                    nombre = os.path.splitext(f)[0]
                    st.markdown(f"- {nombre}")
        else:
            st.error("❌ No hay archivos Excel en data/participantes/")
    
    with col_s2:
        try:
            api_key = st.secrets.get("API_FOOTBALL_KEY", "")
        except Exception:
            api_key = ""
        if api_key:
            st.success("✅ API Key configurada")
        else:
            st.warning("⚠️ API Key no configurada (opcional para probar)")
    
    with col_s3:
        clases_path = os.path.join("data", "equipos_clase.csv")
        if os.path.exists(clases_path):
            equipos = pd.read_csv(clases_path)
            st.success(f"✅ {len(equipos)} equipos con clasificación")
        else:
            st.warning("⚠️ equipos_clase.csv no encontrado")
    
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; font-size:1.1rem;">'
        '👈 Usá el menú lateral para navegar entre las secciones'
        '</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center; color:#555; margin-top:40px;">'
        'Desarrollado con ❤️ y mucho sarcasmo para la oficina.'
        '</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
