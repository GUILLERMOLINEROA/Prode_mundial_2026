import os
import re
import pandas as pd
import streamlit as st

from utils.data_loader import cargar_todo, foto_participante
from utils.excel_reader import cargar_todos_los_participantes
from utils.api_football import estado_display

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

def _resultado_predicho_completo(local, gl, gv, visitante):
    if pd.isna(gl) or pd.isna(gv):
        return "—"
    try:
        return f"{local} {int(gl)}-{int(gv)} {visitante}"
    except Exception:
        return "—"


def _extraer_num_partido(pid):
    m = re.search(r"(\\d+)", str(pid))
    return int(m.group(1)) if m else 9999


def _buscar_resultado_real(local, visitante, resultados):
    """
    Busca el partido real por local/visitante.
    Si lo encuentra invertido, devuelve invertido=True para dar vuelta el score.
    """
    if resultados is None or resultados.empty:
        return None, False

    sub = resultados[
        (resultados["equipo_local"].astype(str).str.strip() == str(local).strip()) &
        (resultados["equipo_visitante"].astype(str).str.strip() == str(visitante).strip())
    ]
    if not sub.empty:
        return sub.iloc[0], False

    sub_inv = resultados[
        (resultados["equipo_local"].astype(str).str.strip() == str(visitante).strip()) &
        (resultados["equipo_visitante"].astype(str).str.strip() == str(local).strip())
    ]
    if not sub_inv.empty:
        return sub_inv.iloc[0], True

    return None, False


def _estado_api_humano(row):
    if row is None:
        return "—"
    codigo = str(row.get("estado", "") or "").strip()
    if not codigo:
        return "—"
    emoji, texto = estado_display(codigo)
    return f"{codigo} · {texto}"


def _resultado_real_texto(row, invertido=False, local_name="", visitante_name=""):
    if row is None:
        return "—"

    gl = row.get("goles_local")
    gv = row.get("goles_visitante")
    pl = row.get("penales_local")
    pv = row.get("penales_visitante")

    if invertido:
        gl, gv = gv, gl
        pl, pv = pv, pl

    if pd.notna(gl) and pd.notna(gv):
        txt = f"{local_name} {int(gl)}-{int(gv)} {visitante_name}".strip()
        if pd.notna(pl) and pd.notna(pv):
            txt += f" (Pen {int(pl)}-{int(pv)})"
        return txt

    return "—"


def _fecha_real_texto(row):
    if row is None:
        return "—"
    try:
        return row["fecha"].strftime("%d/%m %H:%M")
    except Exception:
        return str(row.get("fecha", "—"))


def main():
    st.markdown('<h1 class="titulo-prode">🧾 MI PRODE</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center; color:#AEC6CF;">'
        'Elegí un participante y mirá exactamente qué apostó vs lo que va pasando en la realidad.</p>',
        unsafe_allow_html=True
    )

    exito = cargar_todo()
    if not exito:
        st.warning("⚠️ No se pudieron cargar los datos del grupo.")
        return

    apuestas_grupos = st.session_state.get("apuestas_grupos", pd.DataFrame())
    categorias_todos = st.session_state.get("categorias_todos", {})
    total_results_todos = st.session_state.get("total_results_todos", {})
    resultados = st.session_state.get("resultados", pd.DataFrame())

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

    with st.expander("ℹ️ Leyenda de estados de la API", expanded=False):
        st.markdown(
            "- **NS** = No empezó  \n"
            "- **1H** = Primer tiempo  \n"
            "- **HT** = Entretiempo  \n"
            "- **2H** = Segundo tiempo  \n"
            "- **ET** = Tiempo extra  \n"
            "- **P** = Penales  \n"
            "- **FT** = Finalizado  \n"
            "- **AET** = Finalizado en prórroga  \n"
            "- **PEN** = Finalizado por penales"
        )

    tab1, tab2, tab3 = st.tabs(["🌍 Fase de grupos", "🏟️ Eliminatorias", "📋 Tabla final pronosticada"])

    # =========================
    # TAB 1 — Fase de grupos
    # =========================
    with tab1:
        if grupos_sub.empty:
            st.info("No hay apuestas de fase de grupos para este participante.")
        else:
            grupos_sub = grupos_sub.copy()

            filas = []
            for _, r in grupos_sub.iterrows():
                real_row, invertido = _buscar_resultado_real(
                    r["equipo_local"], r["equipo_visitante"], resultados
                )

                filas.append({
                    "Partido": r["partido_id"],
                    "Predicción": _resultado_predicho_completo(
                        str(r["equipo_local"]),
                        r["goles_local_pred"],
                        r["goles_visitante_pred"],
                        str(r["equipo_visitante"]),
                    ),
                    "Estado API": _estado_api_humano(real_row),
                    "Resultado real": _resultado_real_texto(
                        real_row,
                        invertido,
                        str(r["equipo_local"]),
                        str(r["equipo_visitante"]),
                    ),
                    "Fecha real": _fecha_real_texto(real_row),
                })

            df_show = pd.DataFrame(filas)

            # El grupo ya está implícito en el código de partido (GA1, GB2, etc.)
            # así que usamos eso para filtrar sin necesitar columna "Grupo".
            grupos_disponibles = sorted(df_show["Partido"].astype(str).str[1].dropna().unique().tolist())

            filtro_grupo = st.selectbox(
                "Filtrar grupo:",
                ["Todos"] + grupos_disponibles,
                key="filtro_mi_prode_grupos"
            )

            if filtro_grupo != "Todos":
                df_show = df_show[df_show["Partido"].astype(str).str[1] == filtro_grupo]

            st.dataframe(df_show, use_container_width=True, hide_index=True)

    # =========================
    # TAB 2 — Eliminatorias
    # =========================
    with tab2:
        if elim_sub.empty:
            st.info("No hay apuestas de eliminatorias para este participante.")
        else:
            st.caption("Si el cruce pronosticado no coincide con el fixture real, el partido puede aparecer sin match real todavía.")

            elim_sub = elim_sub.copy()
            elim_sub["orden_partido"] = elim_sub["partido_id"].apply(_extraer_num_partido)
            elim_sub = elim_sub.sort_values(["orden_partido", "ronda"], ascending=[True, True])

            filas = []
            for _, r in elim_sub.iterrows():
                real_row, invertido = _buscar_resultado_real(
                    r["equipo1"], r["equipo2"], resultados
                )

                filas.append({
                    "Partido": r["partido_id"],
                    "Ronda": r["ronda"],
                    "Local pred": r["equipo1"],
                    "GL pred": r["goles1_pred"],
                    "GV pred": r["goles2_pred"],
                    "Visitante pred": r["equipo2"],
                    "Ganador pred": r["ganador_pred"],
                    "Estado API": _estado_api_humano(real_row) if real_row is not None else "Ese delirio no existió",
                    "Resultado real": _resultado_real_texto(
                        real_row,
                        invertido,
                        str(r["equipo1"]),
                        str(r["equipo2"]),
                    ) if real_row is not None else "—",
                    "Fecha real": _fecha_real_texto(real_row) if real_row is not None else "—",
                })

            show = pd.DataFrame(filas)
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
