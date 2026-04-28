import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from utils.data_loader import cargar_todo, foto_participante
from utils.api_football import clasificar_ronda
from utils.scoring import PUNTOS

st.set_page_config(page_title="Timeline", page_icon="📈", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def calcular_evolucion_puntos():
    cargar_todo()
    resultados = st.session_state.get("resultados", pd.DataFrame())
    todos_puntajes = st.session_state.get("todos_puntajes", [])

    if resultados.empty or not todos_puntajes:
        return pd.DataFrame()

    partidos_ordenados = resultados.sort_values("fecha").reset_index(drop=True)
    evolucion = []

    for puntaje_data in todos_puntajes:
        part = puntaje_data["participante"]
        detalle_grupos = puntaje_data.get("detalle_grupos", pd.DataFrame())
        total_results = puntaje_data.get("total_results", {})
        equipos_pred_por_ronda = total_results.get("equipos_por_ronda", {}) if isinstance(total_results, dict) else {}

        puntos_acum = 0
        equipos_ya_contados = {}

        evolucion.append({
            "participante": part,
            "fecha": pd.Timestamp("2026-06-10"),
            "puntos": 0,
            "evento": "Inicio del torneo",
        })

        for _, partido in partidos_ordenados.iterrows():
            fecha = partido["fecha"]
            local = partido["equipo_local"]
            visitante = partido["equipo_visitante"]
            gl = partido["goles_local"]
            gv = partido["goles_visitante"]
            estado = partido["estado"]
            ronda = clasificar_ronda(str(partido["ronda"]))

            if estado != "FT" or pd.isna(gl) or pd.isna(gv):
                continue

            gl, gv = int(gl), int(gv)
            puntos_partido = 0
            evento = f"{local} {gl}-{gv} {visitante}"

            if ronda == "grupos":
                if isinstance(detalle_grupos, pd.DataFrame) and not detalle_grupos.empty:
                    match = detalle_grupos[
                        (detalle_grupos["equipo_local"] == local) &
                        (detalle_grupos["equipo_visitante"] == visitante) &
                        (detalle_grupos["estado"] == "jugado")
                    ]
                    if not match.empty:
                        puntos_partido = int(match.iloc[0]["puntos"])
            else:
                equipos_pred = equipos_pred_por_ronda.get(ronda, set())
                if ronda not in equipos_ya_contados:
                    equipos_ya_contados[ronda] = set()
                for equipo in [local, visitante]:
                    if equipo in equipos_pred and equipo not in equipos_ya_contados[ronda]:
                        puntos_partido += PUNTOS.get(ronda, 0)
                        equipos_ya_contados[ronda].add(equipo)

            puntos_acum += puntos_partido
            evolucion.append({
                "participante": part,
                "fecha": fecha,
                "puntos": puntos_acum,
                "evento": evento,
            })

        # Bonos y penalidades al final
        pts_extras = (puntaje_data["pts_campeon"] + puntaje_data["pts_tercero"] +
                     puntaje_data["pts_especiales"] + puntaje_data["pts_penalidades"])
        if pts_extras != 0:
            evolucion.append({
                "participante": part,
                "fecha": pd.Timestamp("2026-07-20"),
                "puntos": puntos_acum + pts_extras,
                "evento": f"Bonos: +{pts_extras}" if pts_extras > 0 else f"Bonos y Penalidades: {pts_extras}",
            })

    return pd.DataFrame(evolucion)


def main():
    st.markdown('<h1 class="titulo-prode">📈 EVOLUCIÓN DE PUNTOS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888;">La carrera por la gloria... o la vergüenza.</p>', unsafe_allow_html=True)

    cargar_todo()
    leaderboard = st.session_state.get("leaderboard", pd.DataFrame())
    if leaderboard.empty:
        st.warning("⚠️ No hay datos cargados.")
        return

    with st.spinner("📊 Calculando evolución..."):
        df_evol = calcular_evolucion_puntos()

    if df_evol.empty:
        st.warning("No hay datos suficientes.")
        return

    # Colores por posicion en el leaderboard
    colores_lista = ["#ffd700", "#c0c0c0", "#cd7f32", "#e74c3c", "#3498db",
                     "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c", "#e67e22"]
    colores = {}
    for i, (_, row) in enumerate(leaderboard.iterrows()):
        colores[row["Participante"]] = colores_lista[i % len(colores_lista)]

    # === GRAFICO PRINCIPAL ===
    st.markdown("### 🏁 Carrera de Puntos")

    fig = go.Figure()

    for part in leaderboard["Participante"].tolist():
        df_part = df_evol[df_evol["participante"] == part].sort_values("fecha")
        if df_part.empty:
            continue
        color = colores.get(part, "#888")
        fig.add_trace(go.Scatter(
            x=df_part["fecha"], y=df_part["puntos"],
            mode='lines+markers', name=part,
            line=dict(color=color, width=3),
            marker=dict(size=5),
            hovertemplate=f"<b>{part}</b><br>Fecha: %{{x|%d/%m}}<br>Puntos: %{{y}}<br>%{{text}}<extra></extra>",
            text=df_part["evento"],
        ))

    # Lineas verticales para cada fase
    fases_fechas = [
        ("Inicio Grupos", "2026-06-11"),
        ("Fin Grupos", "2026-06-28"),
        ("16vos", "2026-07-01"),
        ("8vos", "2026-07-05"),
        ("4tos", "2026-07-09"),
        ("Semis", "2026-07-13"),
        ("Final", "2026-07-19"),
    ]

    shapes = []
    annotations = []
    for fase, fecha_str in fases_fechas:
        fecha_ts = pd.Timestamp(fecha_str)
        shapes.append(dict(
            type="line", x0=fecha_ts, x1=fecha_ts, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dash"),
        ))
        annotations.append(dict(
            x=fecha_ts, y=1.05, xref="x", yref="paper",
            text=fase, showarrow=False,
            font=dict(size=10, color="rgba(255,255,255,0.5)"),
        ))

    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        template="plotly_dark",
        height=600,
        xaxis=dict(
            title="Fecha",
            range=[pd.Timestamp("2026-06-08"), pd.Timestamp("2026-07-22")],
            tickformat="%d/%m",
        ),
        yaxis_title="Puntos Acumulados",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # === POSICION POR FASE ===
    st.markdown("---")
    st.markdown("### 📊 Posición por Fase")

    fase_selec = st.select_slider("Seleccioná una fase:", options=[
        "Fase de Grupos", "16vos de Final", "8vos de Final",
        "Cuartos de Final", "Semifinales", "Final y Bonos"
    ], value="Final y Bonos")

    fase_map = {
        "Fase de Grupos": "2026-06-28", "16vos de Final": "2026-07-04",
        "8vos de Final": "2026-07-08", "Cuartos de Final": "2026-07-12",
        "Semifinales": "2026-07-17", "Final y Bonos": "2026-07-22",
    }

    fecha_corte = pd.Timestamp(fase_map[fase_selec])
    tabla_fase = []
    for part in leaderboard["Participante"].tolist():
        df_part = df_evol[(df_evol["participante"] == part) & (df_evol["fecha"] <= fecha_corte)]
        pts = int(df_part["puntos"].iloc[-1]) if not df_part.empty else 0
        tabla_fase.append({"Participante": part, "Puntos": pts})

    df_tabla = pd.DataFrame(tabla_fase).sort_values("Puntos", ascending=False).reset_index(drop=True)
    df_tabla.insert(0, "Pos", range(1, len(df_tabla) + 1))

    for _, row in df_tabla.iterrows():
        pos = row["Pos"]
        nombre = row["Participante"]
        pts = int(row["Puntos"])
        foto = foto_participante(nombre)
        medalla = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"#{pos}"
        color = colores.get(nombre, "#888")

        col_f, col_n, col_p = st.columns([1, 4, 2])
        with col_f:
            if foto:
                st.image(foto, width=40)
            else:
                st.markdown(f"**{medalla}**")
        with col_n:
            st.markdown(f"**{medalla} {nombre}**")
        with col_p:
            st.markdown(f'<span style="color:{color}; font-size:1.3rem; font-weight:bold;">{pts} pts</span>',
                unsafe_allow_html=True)

    # === MOVIMIENTOS ===
    st.markdown("---")
    st.markdown("### 🔄 Movimientos Destacados")

    df_grupos = df_evol[df_evol["fecha"] <= pd.Timestamp("2026-06-28")]
    pos_grupos = {}
    for part in leaderboard["Participante"].tolist():
        df_p = df_grupos[df_grupos["participante"] == part]
        pos_grupos[part] = int(df_p["puntos"].iloc[-1]) if not df_p.empty else 0

    ranking_g = sorted(pos_grupos.items(), key=lambda x: x[1], reverse=True)
    pos_g = {n: i+1 for i, (n, _) in enumerate(ranking_g)}

    for _, row in leaderboard.iterrows():
        nombre = row["Participante"]
        pos_actual = int(row["Posición"])
        pos_grp = pos_g.get(nombre, pos_actual)
        cambio = pos_grp - pos_actual
        foto = foto_participante(nombre)

        col_f, col_t = st.columns([1, 10])
        with col_f:
            if foto:
                st.image(foto, width=30)
        with col_t:
            if cambio > 0:
                st.markdown(f"📈 **{nombre}** subió **{cambio}** posiciones desde la fase de grupos")
            elif cambio < 0:
                st.markdown(f"📉 **{nombre}** bajó **{abs(cambio)}** posiciones desde la fase de grupos")
            else:
                st.markdown(f"➡️ **{nombre}** se mantuvo en la misma posición")

main()
