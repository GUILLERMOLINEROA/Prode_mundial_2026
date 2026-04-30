import streamlit as st
import pandas as pd
import os

from utils.data_loader import cargar_todo
from utils.api_football import clasificar_ronda

st.set_page_config(page_title="Partidos", page_icon="📊", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    st.markdown('<h1 class="titulo-prode">📊 PARTIDOS Y RESULTADOS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#AEC6CF;">Todos los partidos del Mundial 2026.</p>', unsafe_allow_html=True)

    cargar_todo()
    resultados = st.session_state.get("resultados", pd.DataFrame())

    if resultados.empty:
        st.warning("⚠️ No hay resultados disponibles. Activá la simulación o configurá la API.")
        return

    # Agregar ronda interna para filtros
    resultados = resultados.copy()
    resultados["ronda_interna"] = resultados["ronda"].apply(lambda x: clasificar_ronda(str(x)))

    # --- Estadísticas rápidas arriba ---
    finalizados = resultados[resultados["estado"] == "FT"]
    programados = resultados[resultados["estado"] == "NS"]
    en_curso = resultados[resultados["estado"].isin(["1H", "2H", "HT", "LIVE"])]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏟️ Total partidos", len(resultados))
    col2.metric("✅ Finalizados", len(finalizados))
    col3.metric("🔴 En curso", len(en_curso))
    col4.metric("📅 Programados", len(programados))

    if not finalizados.empty:
        total_goles = finalizados["goles_local"].sum() + finalizados["goles_visitante"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("⚽ Goles totales", int(total_goles))
        c2.metric("📊 Promedio goles/partido", f"{total_goles / len(finalizados):.2f}")
        empates = len(finalizados[finalizados["goles_local"] == finalizados["goles_visitante"]])
        c3.metric("🤝 Empates", empates)

    st.markdown("---")

    # --- Filtros ---
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        rondas_opciones = ["Todas"] + sorted(resultados["ronda"].unique().tolist())
        ronda_filtro = st.selectbox("🏆 Filtrar por ronda:", rondas_opciones)

    with col_f2:
        estado_map = {"Todos": None, "Finalizados": "FT", "Programados": "NS", "En curso": ["1H", "2H", "HT"]}
        estado_filtro = st.selectbox("📋 Estado:", list(estado_map.keys()))

    with col_f3:
        orden = st.selectbox("📅 Orden:", ["Más recientes primero", "Más antiguos primero"])

    # Aplicar filtros
    df = resultados.copy()
    if ronda_filtro != "Todas":
        df = df[df["ronda"] == ronda_filtro]

    estado_val = estado_map[estado_filtro]
    if estado_val is not None:
        if isinstance(estado_val, list):
            df = df[df["estado"].isin(estado_val)]
        else:
            df = df[df["estado"] == estado_val]

    if orden == "Más recientes primero":
        df = df.sort_values("fecha", ascending=False)
    else:
        df = df.sort_values("fecha", ascending=True)

    st.markdown(f"### Mostrando {len(df)} partidos")

    # --- Mostrar partidos ---
    for _, p in df.iterrows():
        local = p["equipo_local"]
        visitante = p["equipo_visitante"]
        gl = p["goles_local"]
        gv = p["goles_visitante"]
        estado = p["estado"]
        ronda = p["ronda"]
        pl = p.get("penales_local")
        pv = p.get("penales_visitante")

        if estado == "FT":
            resultado = f"<b>{int(gl)}</b> - <b>{int(gv)}</b>"
            if pd.notna(pl) and pd.notna(pv):
                resultado += f" <span style='color:#AEC6CF; font-size:0.8rem;'>(Pen {int(pl)}-{int(pv)})</span>"
            borde = "#C8E600"
            bg = "#1B2838"
        elif estado in ("1H", "2H", "HT", "LIVE"):
            g1 = int(gl) if pd.notna(gl) else "?"
            g2 = int(gv) if pd.notna(gv) else "?"
            resultado = f"<b>{g1}</b> - <b>{g2}</b> 🔴"
            borde = "#E74C3C"
            bg = "#2a1a1a"
        else:
            resultado = "vs"
            borde = "#7C8C8D"
            bg = "#1B2838"

        # Determinar ganador para resaltarlo
        ganador_local = ""
        ganador_visit = ""
        if estado == "FT" and pd.notna(gl) and pd.notna(gv):
            if gl > gv:
                ganador_local = "color: #C8E600; font-weight: bold;"
            elif gv > gl:
                ganador_visit = "color: #C8E600; font-weight: bold;"
            elif pd.notna(pl) and pd.notna(pv):
                if pl > pv:
                    ganador_local = "color: #C8E600; font-weight: bold;"
                else:
                    ganador_visit = "color: #C8E600; font-weight: bold;"

        st.markdown(
            f'<div style="display:flex; justify-content:space-between; align-items:center; '
            f'background:{bg}; border-left:3px solid {borde}; padding:10px 20px; '
            f'border-radius:8px; margin:4px 0;">'
            f'<span style="width:140px; color:#7C8C8D; font-size:0.85rem;">{ronda}</span>'
            f'<span style="width:180px; text-align:right; {ganador_local}">{local}</span>'
            f'<span style="width:120px; text-align:center; font-size:1.1rem;">{resultado}</span>'
            f'<span style="width:180px; {ganador_visit}">{visitante}</span>'
            f'<span style="width:50px; text-align:right; color:{borde}; font-size:0.8rem;">{estado}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

main()
