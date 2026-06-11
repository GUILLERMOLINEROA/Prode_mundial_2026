import os
import re
import pandas as pd
import streamlit as st

from utils.data_loader import cargar_todo, foto_participante
from utils.excel_reader import cargar_todos_los_participantes

st.set_page_config(page_title="Mi Prode", page_icon="🧾", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _resultado_texto(gl, gv):
    if pd.isna(gl) or pd.isna(gv):
        return ""
    gl = int(gl)
    gv = int(gv)
    if gl > gv:
        return "Local"
    elif gv > gl:
        return "Visitante"
    return "Empate"


def _extraer_num_partido(pid):
    m = re.search(r"(\\d+)", str(pid))
    return int(m.group(1)) if m else 9999


def main():
    st.markdown('<h1 class="titulo-prode">🧾 MI PRODE</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center; color:#AEC6CF;">'
        'Elegí un participante y mirá exactamente qué apostó.</p>',
        unsafe_allow_html=True
    )

    exito = cargar_todo()
    if not exito:
        st.warning("⚠️ No se pudieron cargar los datos del grupo.")
        return

    apuestas_grupos = st.session_state.get("apuestas_grupos", pd.DataFrame())
    categorias_todos = st.session_state.get("categorias_todos", {})
    total_results_todos = st.session_state.get("total_results_todos", {})

    # pred_elim no estaba en session_state; lo recargamos desde excel_reader
    _, pred_elim, _, _ = cargar_todos_los_participantes()

    participantes = sorted(categorias_todos.keys())
    if not participantes:
        st.warning("⚠️ No hay participantes cargados.")
        return

    participante = st.selectbox("🎯 Seleccioná un participante:", participantes)

    cats = categorias_todos.get(participante, {})
    foto = foto_participante(participante)

    grupos_sub = apuestas_grupos[apuestas_grupos["participante"] == participante].copy()
    elim_sub = pred_elim[pred_elim["participante"] == participante].copy()

    goles_grupos = int(
        grupos_sub["goles_local_pred"].fillna(0).sum() +
        grupos_sub["goles_visitante_pred"].fillna(0).sum()
    ) if not grupos_sub.empty else 0

    goles_elim = int(
        elim_sub["goles1_pred"].fillna(0).sum() +
        elim_sub["goles2_pred"].fillna(0).sum()
    ) if not elim_sub.empty else 0

    goles_total = goles_grupos + goles_elim

    # Header del participante
    c1, c2 = st.columns([1, 4])
    with c1:
        if foto:
            st.image(foto, width=120)
    with c2:
        st.markdown(f"## {participante}")
        st.markdown(
            f"🏆 **Campeón:** {cats.get('Campeon', '?')}  \n"
            f"⚽ **Goleador:** {cats.get('Goleador', '?')}  \n"
            f"⭐ **Figura:** {cats.get('Figura', '?')}  \n"
            f"💡 **Revelación:** {cats.get('Revelación', '?')}  \n"
            f"💀 **Decepción:** {cats.get('Decepción', '?')}"
        )

    st.divider()

    # Métricas rápidas
    m1, m2, m3 = st.columns(3)
    m1.metric("🔥 Goles en grupos", goles_grupos)
    m2.metric("🏟️ Goles en eliminatorias", goles_elim)
    m3.metric("⚽ Goles totales predichos", goles_total)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🌍 Fase de grupos", "🏟️ Eliminatorias", "📋 Tabla final pronosticada"])

    # =========================
    # TAB 1 — Fase de grupos
    # =========================
    with tab1:
        if grupos_sub.empty:
            st.info("No hay apuestas de fase de grupos para este participante.")
        else:
            grupos_sub = grupos_sub.copy()
            grupos_sub["Resultado predicho"] = grupos_sub.apply(
                lambda r: _resultado_texto(r["goles_local_pred"], r["goles_visitante_pred"]),
                axis=1
            )

            filtro_grupo = st.selectbox(
                "Filtrar grupo:",
                ["Todos"] + sorted(grupos_sub["grupo"].dropna().astype(str).unique().tolist()),
                key="filtro_mi_prode_grupos"
            )

            df_show = grupos_sub.copy()
            if filtro_grupo != "Todos":
                df_show = df_show[df_show["grupo"].astype(str) == filtro_grupo]

            df_show = df_show[[
                "partido_id", "grupo", "equipo_local", "goles_local_pred",
                "goles_visitante_pred", "equipo_visitante", "Resultado predicho"
            ]].rename(columns={
                "partido_id": "Partido",
                "grupo": "Grupo",
                "equipo_local": "Local",
                "goles_local_pred": "GL",
                "goles_visitante_pred": "GV",
                "equipo_visitante": "Visitante",
            })

            st.dataframe(df_show, use_container_width=True, hide_index=True)

    # =========================
    # TAB 2 — Eliminatorias
    # =========================
    with tab2:
        if elim_sub.empty:
            st.info("No hay apuestas de eliminatorias para este participante.")
        else:
            elim_sub = elim_sub.copy()
            elim_sub["orden_partido"] = elim_sub["partido_id"].apply(_extraer_num_partido)
            elim_sub = elim_sub.sort_values(["orden_partido", "ronda"], ascending=[True, True])

            elim_sub["Resultado predicho"] = elim_sub.apply(
                lambda r: _resultado_texto(r["goles1_pred"], r["goles2_pred"]),
                axis=1
            )

            show = elim_sub[[
                "partido_id", "ronda", "equipo1", "goles1_pred", "goles2_pred",
                "equipo2", "penales1_pred", "penales2_pred", "ganador_pred"
            ]].rename(columns={
                "partido_id": "Partido",
                "ronda": "Ronda",
                "equipo1": "Local",
                "goles1_pred": "GL",
                "goles2_pred": "GV",
                "equipo2": "Visitante",
                "penales1_pred": "Pen L",
                "penales2_pred": "Pen V",
                "ganador_pred": "Ganador predicho",
            })

            st.dataframe(show, use_container_width=True, hide_index=True)

    # =========================
    # TAB 3 — Total Results
    # =========================
    with tab3:
        total_info = total_results_todos.get(participante, {})
        tabla = total_info.get("tabla_completa", pd.DataFrame())

        if tabla is None or tabla.empty:
            st.info("No hay tabla final pronosticada disponible para este participante.")
        else:
            st.markdown(
                f"**Campeón pronosticado:** {total_info.get('campeon', '?')}  \n"
                f"**Subcampeón pronosticado:** {total_info.get('subcampeon', '?')}  \n"
                f"**3er puesto pronosticado:** {total_info.get('tercero', '?')}"
            )
            st.dataframe(tabla, use_container_width=True, hide_index=True)


main()
