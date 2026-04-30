import streamlit as st
import pandas as pd
import os
from utils.data_loader import cargar_todo
from utils.api_football import clasificar_ronda, estado_display, hay_partidos_en_vivo, ESTADOS_EN_VIVO, ESTADOS_FINALIZADO

st.set_page_config(page_title="Partidos", page_icon="📊", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="titulo-prode">📊 PARTIDOS Y RESULTADOS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#AEC6CF;">Todos los partidos del Mundial 2026.</p>',
        unsafe_allow_html=True)

    cargar_todo()

    resultados = st.session_state.get("resultados", pd.DataFrame())
    if resultados.empty:
        st.warning("No hay resultados disponibles. Activa la simulacion o configura la API.")
        return

    resultados = resultados.copy()
    resultados["ronda_interna"] = resultados["ronda"].apply(lambda x: clasificar_ronda(str(x)))

    # --- Auto-refresh si hay partidos en vivo ---
    en_vivo = hay_partidos_en_vivo(resultados)
    if en_vivo:
        st.markdown(
            '<div style="text-align:center; padding:10px; background:#2a1a1a; '
            'border:1px solid #E74C3C; border-radius:8px; margin-bottom:15px;">'
            '<span style="color:#E74C3C; font-size:1.1rem;">🔴 HAY PARTIDOS EN VIVO '
            '— Actualización automática cada 60 segundos</span></div>',
            unsafe_allow_html=True)
        st.html('<meta http-equiv="refresh" content="60">')

    # --- Estadísticas rápidas ---
    finalizados = resultados[resultados["estado"].isin(ESTADOS_FINALIZADO)]
    programados = resultados[resultados["estado"] == "NS"]
    partidos_vivo = resultados[resultados["estado"].isin(ESTADOS_EN_VIVO)]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏟️ Total partidos", len(resultados))
    col2.metric("✅ Finalizados", len(finalizados))
    col3.metric("🔴 En curso", len(partidos_vivo))
    col4.metric("📅 Programados", len(programados))

    if not finalizados.empty:
        total_goles = finalizados["goles_local"].sum() + finalizados["goles_visitante"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("⚽ Goles totales", int(total_goles))
        c2.metric("📊 Promedio goles/partido", f"{total_goles / len(finalizados):.2f}")
        empates = len(finalizados[finalizados["goles_local"] == finalizados["goles_visitante"]])
        c3.metric("🤝 Empates", empates)

    # --- Partidos en vivo destacados ---
    if not partidos_vivo.empty:
        st.markdown("---")
        st.markdown("### 🔴 Partidos en Vivo")
        for _, p in partidos_vivo.iterrows():
            local = p["equipo_local"]
            visitante = p["equipo_visitante"]
            gl = int(p["goles_local"]) if pd.notna(p["goles_local"]) else 0
            gv = int(p["goles_visitante"]) if pd.notna(p["goles_visitante"]) else 0
            estado = p["estado"]
            minuto = p.get("minuto")
            emoji, texto_estado = estado_display(estado)

            # Construir texto del minuto
            if estado == "HT":
                info_tiempo = "⏸️ ENTRETIEMPO"
                color_estado = "#F39C12"
            else:
                min_txt = f"{int(minuto)}'" if pd.notna(minuto) else ""
                info_tiempo = f"{emoji} {texto_estado} {min_txt}"
                color_estado = "#E74C3C"

            st.markdown(
                f'<div style="display:flex; justify-content:center; align-items:center; '
                f'background:linear-gradient(135deg, #2a1a1a, #1B2838); '
                f'border:2px solid {color_estado}; padding:15px 30px; '
                f'border-radius:12px; margin:8px 0; gap:20px;">'
                f'<span style="font-size:1.3rem; min-width:180px; text-align:right;">{local}</span>'
                f'<span style="font-size:2rem; font-weight:bold; color:#C8E600; min-width:80px; text-align:center;">'
                f'{gl} - {gv}</span>'
                f'<span style="font-size:1.3rem; min-width:180px;">{visitante}</span>'
                f'<span style="color:{color_estado}; font-size:0.9rem; min-width:140px; text-align:center;">'
                f'{info_tiempo}</span>'
                f'</div>',
                unsafe_allow_html=True)

    st.markdown("---")

    # --- Filtros ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        rondas_opciones = ["Todas"] + sorted(resultados["ronda"].unique().tolist())
        ronda_filtro = st.selectbox("🏆 Filtrar por ronda:", rondas_opciones)
    with col_f2:
        estado_map = {
            "Todos": None,
            "Finalizados": list(ESTADOS_FINALIZADO),
            "Programados": ["NS"],
            "En curso": list(ESTADOS_EN_VIVO),
        }
        estado_filtro = st.selectbox("📋 Estado:", list(estado_map.keys()))
    with col_f3:
        orden = st.selectbox("📅 Orden:", ["Más recientes primero", "Más antiguos primero"])

    # Aplicar filtros
    df = resultados.copy()
    if ronda_filtro != "Todas":
        df = df[df["ronda"] == ronda_filtro]
    estado_val = estado_map[estado_filtro]
    if estado_val is not None:
        df = df[df["estado"].isin(estado_val)]
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
        minuto = p.get("minuto")

        emoji, texto_estado = estado_display(estado)

        if estado in ESTADOS_FINALIZADO:
            resultado = f"<b>{int(gl)}</b> - <b>{int(gv)}</b>"
            if pd.notna(pl) and pd.notna(pv):
                resultado += f" <span style='color:#AEC6CF; font-size:0.8rem;'>(Pen {int(pl)}-{int(pv)})</span>"
            borde = "#C8E600"
            bg = "#1B2838"
            estado_txt = f"{emoji} {texto_estado}"
        elif estado in ESTADOS_EN_VIVO:
            g1 = int(gl) if pd.notna(gl) else 0
            g2 = int(gv) if pd.notna(gv) else 0
            resultado = f"<b>{g1}</b> - <b>{g2}</b>"
            borde = "#E74C3C" if estado != "HT" else "#F39C12"
            bg = "#2a1a1a"
            if estado == "HT":
                estado_txt = "⏸️ Entretiempo"
            else:
                min_txt = f"{int(minuto)}'" if pd.notna(minuto) else ""
                estado_txt = f"{emoji} {texto_estado} {min_txt}"
        else:
            resultado = "vs"
            borde = "#7C8C8D"
            bg = "#1B2838"
            estado_txt = f"{emoji} {texto_estado}"

        # Determinar ganador para resaltarlo
        ganador_local = ""
        ganador_visit = ""
        if estado in ESTADOS_FINALIZADO and pd.notna(gl) and pd.notna(gv):
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
            f'<span style="width:130px; text-align:right; color:{borde}; font-size:0.8rem;">'
            f'{estado_txt}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

main()
