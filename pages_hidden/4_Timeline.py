import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from utils.data_loader import cargar_todo, foto_participante, cargar_overrides
from utils.timeline import construir_evolucion

st.set_page_config(page_title="Timeline", page_icon="📈", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def calcular_evolucion_puntos():
    """Evolución desde la MISMA fuente que el leaderboard (construir_puntajes truncado
    por hito). El último punto de cada línea == su Total en la tabla. Retorna (df, hitos)."""
    cargar_todo()
    return construir_evolucion(
        st.session_state.get("resultados", pd.DataFrame()),
        st.session_state.get("apuestas_grupos", pd.DataFrame()),
        st.session_state.get("categorias_todos", {}),
        st.session_state.get("total_results_todos", {}),
        st.session_state.get("todos_puntajes", []),
        cargar_overrides(),
    )


def main():
    st.markdown('<h1 class="titulo-prode">📈 EVOLUCIÓN DE PUNTOS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888;">La carrera por la gloria... o la vergüenza.</p>', unsafe_allow_html=True)

    cargar_todo()
    leaderboard = st.session_state.get("leaderboard", pd.DataFrame())
    if leaderboard.empty:
        st.warning("⚠️ No hay datos cargados.")
        return

    with st.spinner("📊 Calculando evolución..."):
        df_evol, hitos = calcular_evolucion_puntos()

    if not df_evol.empty and "fecha" in df_evol.columns:
        df_evol["fecha"] = pd.to_datetime(df_evol["fecha"], utc=True, errors="coerce")
        df_evol = df_evol.dropna(subset=["fecha"])

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
    st.caption(
        "ℹ️ Los puntos de clasificación se reparten a medida que se juega cada partido de "
        "eliminatoria. Durante una ronda en curso, el extremo de la curva puede quedar por "
        "debajo del Total de la tabla (la diferencia es el pase aún no repartido); al "
        "completarse la ronda, vuelven a coincidir.")

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
        fecha_ts = pd.Timestamp(fecha_str, tz="UTC")
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
            range=[pd.Timestamp("2026-06-08", tz="UTC"), pd.Timestamp("2026-07-22", tz="UTC")],
            tickformat="%d/%m",
        ),
        yaxis_title="Puntos Acumulados",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # === POSICION POR FASE ===
    # Solo fases que ya se jugaron (hitos); no mostramos totales en rondas no jugadas.
    st.markdown("---")
    st.markdown("### 📊 Posición por Fase")

    opciones_fase = [lbl for (lbl, rk, fts) in hitos]
    fecha_por_fase = {lbl: fts for (lbl, rk, fts) in hitos}
    fase_selec = st.select_slider("Seleccioná una fase:", options=opciones_fase,
                                  value=opciones_fase[-1])

    fecha_corte = fecha_por_fase[fase_selec]
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

    df_grupos = df_evol[df_evol["fecha"] <= pd.Timestamp("2026-06-28", tz="UTC")]
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
