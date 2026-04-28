# =============================================================================
# pages/3_Partidos.py
# Vista de partidos: resultados reales y estado del torneo.
# =============================================================================

import streamlit as st
import pandas as pd
import os

from utils.api_football import obtener_partidos_mundial, mapear_nombre_equipo, clasificar_ronda

# --- Configuración ---
st.set_page_config(page_title="Partidos", page_icon="📊", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    st.markdown(
        '<h1 class="titulo-prode">📊 PARTIDOS Y RESULTADOS</h1>',
        unsafe_allow_html=True
    )
    
    with st.spinner("🔄 Cargando partidos..."):
        resultados = obtener_partidos_mundial()
    
    if resultados.empty:
        st.warning(
            "⚠️ No se pudieron obtener partidos de la API. "
            "Verificá tu API Key o esperá a que la competición esté disponible."
        )
        st.info(
            "El Mundial 2026 comienza el 11 de junio de 2026. "
            "Los datos estarán disponibles cuando la API los publique."
        )
        return
    
    # Mapear nombres
    resultados["equipo_local"] = resultados["equipo_local"].apply(mapear_nombre_equipo)
    resultados["equipo_visitante"] = resultados["equipo_visitante"].apply(mapear_nombre_equipo)
    resultados["ronda_interna"] = resultados["ronda"].apply(clasificar_ronda)
    
    # --- Filtros ---
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        rondas = ["Todas"] + sorted(resultados["ronda"].unique().tolist())
        ronda_filtro = st.selectbox("Filtrar por ronda:", rondas)
    
    with col_f2:
        estado_map = {"Todos": None, "Finalizados": "FT", "Programados": "NS"}
        estado_filtro = st.selectbox("Estado:", list(estado_map.keys()))
    
    df = resultados.copy()
    if ronda_filtro != "Todas":
        df = df[df["ronda"] == ronda_filtro]
    if estado_map[estado_filtro]:
        df = df[df["estado"] == estado_map[estado_filtro]]
    
    st.markdown(f"### {len(df)} partidos")
    
    # Mostrar cada partido
    for _, p in df.iterrows():
        local = p["equipo_local"]
        visitante = p["equipo_visitante"]
        gl = p["goles_local"]
        gv = p["goles_visitante"]
        estado = p["estado"]
        ronda = p["ronda"]
        
        if estado == "FT":
            resultado = f"**{int(gl)}** - **{int(gv)}**"
            borde = "#2ecc71"
        elif estado in ("1H", "2H", "HT"):
            resultado = (
                f"**{int(gl) if pd.notna(gl) else '?'}** - "
                f"**{int(gv) if pd.notna(gv) else '?'}** 🔴"
            )
            borde = "#e74c3c"
        else:
            resultado = "vs"
            borde = "#555"
        
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; '
            f'align-items:center; background:#1a1a2e; border-left:3px solid {borde}; '
            f'padding:10px 20px; border-radius:8px; margin:4px 0;">'
            f'<span style="width:150px; color:#aaa; font-size:0.85rem;">{ronda}</span>'
            f'<span style="width:180px; text-align:right; font-weight:bold;">{local}</span>'
            f'<span style="width:100px; text-align:center; font-size:1.2rem;">{resultado}</span>'
            f'<span style="width:180px; font-weight:bold;">{visitante}</span>'
            f'<span style="width:60px; text-align:right; color:{borde};">{estado}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Estadísticas generales
    finalizados = resultados[resultados["estado"] == "FT"]
    if not finalizados.empty:
        st.markdown("---")
        st.markdown("### 📈 Estadísticas del Torneo")
        c1, c2, c3 = st.columns(3)
        total_goles = finalizados["goles_local"].sum() + finalizados["goles_visitante"].sum()
        c1.metric("Partidos jugados", len(finalizados))
        c2.metric("Goles totales", int(total_goles))
        c3.metric("Promedio goles/partido", f"{total_goles / len(finalizados):.2f}")


# --- Ejecutar ---
main()
