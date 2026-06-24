import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64
import random
from utils.participantes_info import cargar_participantes_info
from utils.comentarios_campeon import comentario_campeon_contextual
from utils.group_config import fotos_dir

st.set_page_config(
    page_title="PRODE Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

def cargar_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def foto_to_base64(nombre):
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(fotos_dir(), f"{nombre}{ext}")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/{ext[1:]};base64,{data}" style="width:70px; border-radius:50%; margin:5px 0;">'
    return ""

def main():
    cargar_css()

    # =================================================================
    # SIDEBAR: Banner API + Configuracion
    # =================================================================
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

    with st.sidebar:
        st.session_state["usar_simulacion"] = False

    # =================================================================
    # CARGA CENTRALIZADA
    # =================================================================
    from utils.data_loader import cargar_todo, foto_participante
    with st.spinner("🔄 Cargando todos los datos del PRODE..."):
        exito = cargar_todo()

    # =================================================================
    # TITULO
    # =================================================================
    # Banner
    banner_path = os.path.join("assets", "banner.png")
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as img_b:
            b64_banner = base64.b64encode(img_b.read()).decode()
        st.markdown(
            f'<div style="text-align:center; margin-bottom:20px;">'
            f'<img src="data:image/png;base64,{b64_banner}" style="max-width:100%; border-radius:10px;">'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown('<h1 class="titulo-prode">⚽ PRODE MUNDIALISTA 2026 ⚽</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
        'Donde las amistades se prueban y los egos se destruyen.</p>', unsafe_allow_html=True)

    col_refresh_1, col_refresh_2, col_refresh_3 = st.columns([3, 2, 3])
    with col_refresh_2:
        if st.button("🔄 Refrescar vista", key="refresh_vista_mundial", use_container_width=True):
            st.rerun()

    st.markdown(
        '<p style="text-align:center; color:#7C8C8D; font-size:0.85rem; margin-top:6px;">'
        'Usa el cache normal de la API (50s). Si todavía no hay datos nuevos, vas a ver lo mismo.'
        '</p>',
        unsafe_allow_html=True
    )

    st.divider()

    if not exito or "leaderboard" not in st.session_state:
        st.warning("⚠️ No se pudieron cargar los datos.")
        return

    leaderboard = st.session_state["leaderboard"]
    resultados = st.session_state.get("resultados", pd.DataFrame())
    apuestas_grupos = st.session_state.get("apuestas_grupos", pd.DataFrame())
    total_results_todos = st.session_state.get("total_results_todos", {})
    campeon = st.session_state.get("campeon_real", "")
    tercero = st.session_state.get("tercero_real", "")

    # Orden de entrega para ordenar listas de apostadores
    orden_entrega = {}
    try:
        from utils.group_config import entregas_path
        entregas_df = pd.read_csv(entregas_path())
        entregas_df.columns = entregas_df.columns.str.strip()
        for idx, row in entregas_df.iterrows():
            codigo = str(row.get("codigo", "")).strip().upper()
            if codigo:
                orden_entrega[codigo] = idx
    except Exception:
        orden_entrega = {}

    def ordenar_codigos(codigos):
        return sorted(
            codigos,
            key=lambda x: (orden_entrega.get(str(x).strip().upper(), 9999), str(x))
        )

    def etiqueta_ronda_visible(row):
        """
        Convierte 'Group Stage - X' en 'Grupo A/B/C...' usando el match real
        contra apuestas_grupos. Si no puede mapear, deja el texto original.
        """
        ronda_raw = str(row.get("ronda", "") or "").strip()
        if not ronda_raw.lower().startswith("group stage"):
            return ronda_raw

        local = str(row.get("equipo_local", "") or "").strip()
        visitante = str(row.get("equipo_visitante", "") or "").strip()

        if apuestas_grupos is None or apuestas_grupos.empty:
            return ronda_raw

        sub = apuestas_grupos[
            (apuestas_grupos["equipo_local"].astype(str).str.strip() == local) &
            (apuestas_grupos["equipo_visitante"].astype(str).str.strip() == visitante)
        ]

        if sub.empty:
            sub = apuestas_grupos[
                (apuestas_grupos["equipo_local"].astype(str).str.strip() == visitante) &
                (apuestas_grupos["equipo_visitante"].astype(str).str.strip() == local)
            ]

        if not sub.empty:
            grupo = str(sub.iloc[0].get("grupo", "") or "").strip().upper()
            if grupo:
                return f"Grupo {grupo}"

        return ronda_raw

    def ronda_prediccion_para_match(row):
        """
        Devuelve la ronda interna usada en equipos_por_ronda.
        """
        rr = str(row.get("ronda", "") or "").lower()

        if "32" in rr:
            return "16vos"
        if "16" in rr:
            return "8vos"
        if "quarter" in rr:
            return "4tos"
        if "semi" in rr:
            return "semis"
        if "3rd" in rr or "third" in rr:
            return "semis"
        if "final" in rr:
            return "final"

        # si es de grupos, devolvemos vacío
        return ""

    def quienes_pasan_a_16avos(equipo):
        """Participantes que en su Excel predijeron que `equipo` pasa a 16avos."""
        codigos = [
            nombre_ap for nombre_ap, tr in total_results_todos.items()
            if equipo in set((tr.get("equipos_por_ronda", {}) or {}).get("16vos", set()))
        ]
        return ordenar_codigos(codigos)

    bienvenida_data = {}
    try:
        from utils.bienvenida import obtener_bienvenida
        categorias_todos_para_ia = st.session_state.get("categorias_todos", {})
        bienvenida_data = obtener_bienvenida(
            categorias_todos=categorias_todos_para_ia,
            leaderboard=leaderboard,
            resultados=resultados,
        )
    except Exception:
        bienvenida_data = {}

    # =================================================================
    # CAMPEON + ULTIMOS RESULTADOS
    # =================================================================
    if campeon:
        st.success(f"🏆 Campeón: **{campeon}** | 🥉 3er puesto: **{tercero}**")

    from utils.api_football import obtener_ultimos_resultados, obtener_proximos_partidos, formatear_horarios_partido, ESTADOS_EN_VIVO

    # ================================
    # EN VIVO AHORA
    # ================================
    en_vivo = pd.DataFrame()
    if resultados is not None and not resultados.empty and "estado" in resultados.columns:
        en_vivo = resultados[resultados["estado"].isin(list(ESTADOS_EN_VIVO))].copy()
        if not en_vivo.empty:
            en_vivo = en_vivo.sort_values("fecha", ascending=True)

    if not en_vivo.empty:
        st.markdown("#### 🔴 En vivo ahora")
        st.caption("⏱️ Actualización automática cada 50 segundos")
        cols_live = st.columns(min(3, len(en_vivo)))

        for i, (_, p) in enumerate(en_vivo.head(3).iterrows()):
            with cols_live[i]:
                local = str(p["equipo_local"]).strip()
                visitante = str(p["equipo_visitante"]).strip()
                gl = int(p["goles_local"]) if pd.notna(p.get("goles_local")) else 0
                gv = int(p["goles_visitante"]) if pd.notna(p.get("goles_visitante")) else 0
                estado = str(p.get("estado", "")).strip()
                minuto = p.get("minuto")

                estado_txt = estado
                if estado == "HT":
                    estado_txt = "Entretiempo"
                elif minuto and pd.notna(minuto):
                    estado_txt = f"{estado} · {int(minuto)}'"

                estadio = str(p.get("estadio", "") or "").strip()
                ciudad = str(p.get("ciudad", "") or "").strip()

                if estadio and ciudad:
                    lugar = f"{estadio}, {ciudad}"
                elif estadio:
                    lugar = estadio
                elif ciudad:
                    lugar = ciudad
                else:
                    lugar = "Sede por confirmar"

                horarios_txt = formatear_horarios_partido(p.get("fecha"))

                apostadores_local = []
                apostadores_visitante = []
                apostadores_empate = []

                if apuestas_grupos is not None and not apuestas_grupos.empty:
                    sub_match = apuestas_grupos[
                        (apuestas_grupos["equipo_local"].astype(str).str.strip() == local) &
                        (apuestas_grupos["equipo_visitante"].astype(str).str.strip() == visitante)
                    ].copy()

                    for _, ap in sub_match.iterrows():
                        nombre_ap = str(ap.get("participante", "")).strip()
                        glp = ap.get("goles_local_pred")
                        gvp = ap.get("goles_visitante_pred")

                        if pd.isna(glp) or pd.isna(gvp):
                            continue

                        try:
                            glp = int(glp)
                            gvp = int(gvp)
                        except Exception:
                            continue

                        if glp > gvp:
                            apostadores_local.append(nombre_ap)
                        elif gvp > glp:
                            apostadores_visitante.append(nombre_ap)
                        else:
                            apostadores_empate.append(nombre_ap)

                local_txt = ", ".join(sorted(apostadores_local)) if apostadores_local else "nadie"
                visitante_txt = ", ".join(sorted(apostadores_visitante)) if apostadores_visitante else "nadie"
                empate_txt = ", ".join(sorted(apostadores_empate)) if apostadores_empate else ""

                empate_html = ""
                if empate_txt:
                    empate_html = f'<br><span style="color:#7C8C8D; font-size:0.72rem;">🤝 Empate: {empate_txt}</span>'

                st.markdown(
                    f'<div style="background:#2a1a1a; border:1px solid #E74C3C; border-radius:8px; '
                    f'padding:16px; text-align:center;">'
                    f'<small style="color:#FFB3B3; font-size:0.9rem;">{etiqueta_ronda_visible(p)}</small>'
                    f'<div style="margin:10px 0 6px 0; display:flex; justify-content:center; align-items:center; gap:14px; flex-wrap:wrap;">'
                    f'<span style="font-size:1.9rem; font-weight:800; color:#FFFFFF;">{local}</span>'
                    f'<span style="font-size:2.3rem; font-weight:900; color:#C8E600; letter-spacing:1px;">{gl}-{gv}</span>'
                    f'<span style="font-size:1.9rem; font-weight:800; color:#FFFFFF;">{visitante}</span>'
                    f'</div>'
                    f'<div style="color:#FFD0D0; font-size:1.05rem; font-weight:700; margin-bottom:8px;">🔴 {estado_txt}</div>'
                    f'<span style="color:#AEC6CF; font-size:0.88rem;">🕒 {horarios_txt}</span><br>'
                    f'<span style="color:#7C8C8D; font-size:0.82rem;">📍 {lugar}</span><br>'
                    f'<div style="margin-top:10px;">'
                    f'<span style="color:#AEC6CF; font-size:0.78rem;">🏠 <b>{local}</b>: {local_txt}</span><br>'
                    f'<span style="color:#AEC6CF; font-size:0.78rem;">✈️ <b>{visitante}</b>: {visitante_txt}</span>'
                    f'{empate_html}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.divider()

    proximos = obtener_proximos_partidos(resultados, 3)
    if not proximos.empty:
        st.markdown("#### 🗓️ Próximos Partidos")
        cols_prox = st.columns(3)
        for i, (_, p) in enumerate(proximos.iterrows()):
            with cols_prox[i]:
                horarios_txt = formatear_horarios_partido(p.get("fecha"))


                estadio = str(p.get("estadio", "") or "").strip()
                ciudad = str(p.get("ciudad", "") or "").strip()

                if estadio and ciudad:
                    lugar = f"{estadio}, {ciudad}"
                elif estadio:
                    lugar = estadio
                elif ciudad:
                    lugar = ciudad
                else:
                    lugar = "Sede por confirmar"

                local = str(p["equipo_local"]).strip()
                visitante = str(p["equipo_visitante"]).strip()

                apostadores_local = []
                apostadores_visitante = []
                apostadores_empate = []
                apostadores_ninguno = []

                ronda_visible = etiqueta_ronda_visible(p)
                es_grupo = ronda_visible.startswith("Grupo ")

                # "Pasa a 16avos" en partidos de grupos: predicción pura (el partido
                # no se jugó). Sale solo de los Excels, sin standings ni puntos.
                pasa16_html = ""

                if es_grupo:
                    if apuestas_grupos is not None and not apuestas_grupos.empty:
                        sub_match = apuestas_grupos[
                            (apuestas_grupos["equipo_local"].astype(str).str.strip() == local) &
                            (apuestas_grupos["equipo_visitante"].astype(str).str.strip() == visitante)
                        ].copy()

                        for _, ap in sub_match.iterrows():
                            nombre_ap = str(ap.get("participante", "")).strip()
                            glp = ap.get("goles_local_pred")
                            gvp = ap.get("goles_visitante_pred")

                            if pd.isna(glp) or pd.isna(gvp):
                                continue

                            try:
                                glp = int(glp)
                                gvp = int(gvp)
                            except Exception:
                                continue

                            if glp > gvp:
                                apostadores_local.append(nombre_ap)
                            elif gvp > glp:
                                apostadores_visitante.append(nombre_ap)
                            else:
                                apostadores_empate.append(nombre_ap)

                    local_txt = ", ".join(sorted(apostadores_local)) if apostadores_local else "nadie"
                    visitante_txt = ", ".join(sorted(apostadores_visitante)) if apostadores_visitante else "nadie"
                    empate_txt = ", ".join(sorted(apostadores_empate)) if apostadores_empate else ""
                    tercero_html = f'<br><span style="color:#7C8C8D; font-size:0.72rem;">🤝 Empate: {empate_txt}</span>' if empate_txt else ""

                    p16_local = ", ".join(quienes_pasan_a_16avos(local)) or "nadie"
                    p16_visit = ", ".join(quienes_pasan_a_16avos(visitante)) or "nadie"
                    pasa16_html = (
                        f'<br><span style="color:#7ED957; font-size:0.75rem;">🎟️ {local} pasa a 16avos: {p16_local}</span>'
                        f'<br><span style="color:#7ED957; font-size:0.75rem;">🎟️ {visitante} pasa a 16avos: {p16_visit}</span>'
                    )
                else:
                    ronda_pred = ronda_prediccion_para_match(p)

                    for nombre_ap, tr in total_results_todos.items():
                        equipos_pred = set((tr.get("equipos_por_ronda", {}) or {}).get(ronda_pred, set()))
                        tiene_local = local in equipos_pred
                        tiene_visitante = visitante in equipos_pred

                        if tiene_local:
                            apostadores_local.append(nombre_ap)
                        if tiene_visitante:
                            apostadores_visitante.append(nombre_ap)
                        if not tiene_local and not tiene_visitante:
                            apostadores_ninguno.append(nombre_ap)

                    local_txt = ", ".join(sorted(apostadores_local)) if apostadores_local else "nadie"
                    visitante_txt = ", ".join(sorted(apostadores_visitante)) if apostadores_visitante else "nadie"
                    ninguno_txt = ", ".join(sorted(apostadores_ninguno)) if apostadores_ninguno else "nadie"
                    tercero_html = f'<br><span style="color:#7C8C8D; font-size:0.72rem;">🚫 Ninguno: {ninguno_txt}</span>'

                st.markdown(
                    f'<div style="background:#1a1a2e; border:1px solid #4A90D9; border-radius:8px; '
                    f'padding:10px; text-align:center;">'
                    f'<small style="color:#888;">{ronda_visible}</small><br>'
                    f'<b>{local}</b> vs <b>{visitante}</b><br>'
                    f'<span style="color:#AEC6CF; font-size:0.9rem;">🕒 {horarios_txt}</span><br>'
                    f'<span style="color:#7C8C8D; font-size:0.8rem;">📍 {lugar}</span><br>'
                    f'<span style="color:#AEC6CF; font-size:0.75rem;">🏠 <b>{local}</b>: {local_txt}</span><br>'
                    f'<span style="color:#AEC6CF; font-size:0.75rem;">✈️ <b>{visitante}</b>: {visitante_txt}</span>'
                    f'{pasa16_html}'
                    f'{tercero_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.divider()

    ultimos = obtener_ultimos_resultados(resultados, 3)
    if not ultimos.empty:
        st.markdown("#### ⚡ Últimos Resultados")

        # --- "Pasa a 16avos": clasificados (provisionales) desde standings oficiales ---
        # DOBLE FUENTE (a propósito):
        #   - La tarjeta DERIVA "pasa a 16avos" de los STANDINGS (1º/2º + 8 mejores
        #     terceros), vía obtener_equipos_clasificados_16avos() — misma función
        #     que usa la condición de Decepción. Es informativo/provisional.
        #   - El +1 REAL que entra al leaderboard lo otorga el scoring desde los
        #     FIXTURES de 16avos de la API (extraer_equipos_reales_por_ronda en
        #     data_loader.py). Son fuentes DISTINTAS: pueden discrepar en una ventana
        #     corta (grupos ya cerrados en standings, pero cuadro de 16avos todavía
        #     sin poblar). Es tolerable porque la línea de la tarjeta es provisional.
        #   - REQUIERE VALIDACIÓN CONTRA STANDINGS REALES DURANTE EL TORNEO 2026.
        from utils.scoring import PUNTOS as _PUNTOS_16
        try:
            from utils.special_categories import (
                grupos_finalizados as _grupos_fin,
                obtener_equipos_clasificados_16avos as _clasificados_16avos_fn,
            )
            grupos_cerrados = bool(_grupos_fin(resultados))
            clasificados_16avos = _clasificados_16avos_fn(resultados)
        except Exception:
            grupos_cerrados = False
            clasificados_16avos = set()

        cols_res = st.columns(3)
        for i, (_, p) in enumerate(ultimos.iterrows()):
            with cols_res[i]:
                gl, gv = int(p["goles_local"]), int(p["goles_visitante"])
                pen = ""
                if pd.notna(p.get("penales_local")) and pd.notna(p.get("penales_visitante")):
                    pen = f" (Pen {int(p['penales_local'])}-{int(p['penales_visitante'])})"

                ronda_visible = etiqueta_ronda_visible(p)
                local = str(p["equipo_local"]).strip()
                visitante = str(p["equipo_visitante"]).strip()

                detalle_html = ""

                # Si es fase de grupos, mostrar quién sumó +2 / +1 / +0
                if ronda_visible.startswith("Grupo "):
                    plus2 = []
                    plus1 = []
                    plus0 = []

                    if apuestas_grupos is not None and not apuestas_grupos.empty:
                        sub_match = apuestas_grupos[
                            (apuestas_grupos["equipo_local"].astype(str).str.strip() == local) &
                            (apuestas_grupos["equipo_visitante"].astype(str).str.strip() == visitante)
                        ].copy()

                        resultado_real = "empate"
                        if gl > gv:
                            resultado_real = "local"
                        elif gv > gl:
                            resultado_real = "visitante"

                        for _, ap in sub_match.iterrows():
                            nombre_ap = str(ap.get("participante", "")).strip()
                            glp = ap.get("goles_local_pred")
                            gvp = ap.get("goles_visitante_pred")

                            if pd.isna(glp) or pd.isna(gvp):
                                continue

                            try:
                                glp = int(glp)
                                gvp = int(gvp)
                            except Exception:
                                continue

                            pts = 0
                            resultado_pred = "empate"
                            if glp > gvp:
                                resultado_pred = "local"
                            elif gvp > glp:
                                resultado_pred = "visitante"

                            if resultado_pred == resultado_real:
                                pts += 1
                            if glp == gl and gvp == gv:
                                pts += 1

                            if pts == 2:
                                plus2.append(nombre_ap)
                            elif pts == 1:
                                plus1.append(nombre_ap)
                            else:
                                plus0.append(nombre_ap)

                    plus2_txt = ", ".join(ordenar_codigos(plus2)) if plus2 else "nadie"
                    plus1_txt = ", ".join(ordenar_codigos(plus1)) if plus1 else "nadie"
                    plus0_txt = ", ".join(ordenar_codigos(plus0)) if plus0 else "nadie"

                    detalle_html = (
                        f'<br><span style="color:#C8E600; font-size:0.75rem;">✅ +2: {plus2_txt}</span>'
                        f'<br><span style="color:#4A90D9; font-size:0.75rem;">➕ +1: {plus1_txt}</span>'
                        f'<br><span style="color:#7C8C8D; font-size:0.75rem;">❌ +0: {plus0_txt}</span>'
                    )

                    # "Pasa a 16avos (+1)": solo para los equipos del partido que ya clasifican.
                    suf_prov = "" if grupos_cerrados else ", provisional"
                    for eq_card in (local, visitante):
                        if eq_card in clasificados_16avos:
                            cods = quienes_pasan_a_16avos(eq_card)
                            cods_txt = ", ".join(cods) if cods else "nadie"
                            detalle_html += (
                                f'<br><span style="color:#7ED957; font-size:0.75rem;">'
                                f'🎟️ {eq_card} pasa a 16avos (+{_PUNTOS_16["16vos"]}{suf_prov}): {cods_txt}</span>'
                            )
                else:
                    detalle_html = (
                        f'<br><span style="color:#7C8C8D; font-size:0.75rem;">'
                        f'🏟️ En eliminatorias el puntaje no depende del marcador, sino de quién hizo pasar a los equipos.'
                        f'</span>'
                    )

                st.markdown(
                    f'<div style="background:#1a1a2e; border:1px solid #333; border-radius:8px; '
                    f'padding:10px; text-align:center;">'
                    f'<small style="color:#888;">{ronda_visible}</small><br>'
                    f'<b>{local}</b> {gl}-{gv} <b>{visitante}</b>{pen}'
                    f'{detalle_html}'
                    f'</div>',
                    unsafe_allow_html=True)
    st.divider()

    # =================================================================
    # TOP 3 CON FOTOS
    # =================================================================
    if not leaderboard.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            if len(leaderboard) >= 1:
                l = leaderboard.iloc[0]
                foto_html = foto_to_base64(l["Participante"])
                st.markdown(f'''<div class="card-lider" style="text-align:center;">
                    <p class="posicion-1">🥇 #1</p>
                    {foto_html}
                    <h2 style="color:#C8E600; margin:5px 0;">{l["Participante"]}</h2>
                    <p class="puntos-grandes" style="margin:0;">{int(l["Total"])}</p>
                    <p style="color:#AEC6CF; margin:0;">puntos</p>
                </div>''', unsafe_allow_html=True)
        with col2:
            if len(leaderboard) >= 2:
                s = leaderboard.iloc[1]
                foto_html = foto_to_base64(s["Participante"])
                st.markdown(f'''<div class="card-normal" style="border-color:#AEC6CF; text-align:center;">
                    <p class="posicion-2">🥈 #2</p>
                    {foto_html}
                    <h3 style="margin:5px 0;">{s["Participante"]}</h3>
                    <h2 style="margin:0;">{int(s["Total"])} pts</h2>
                </div>''', unsafe_allow_html=True)
        with col3:
            if len(leaderboard) >= 3:
                t = leaderboard.iloc[2]
                foto_html = foto_to_base64(t["Participante"])
                st.markdown(f'''<div class="card-normal" style="border-color:#E67E22; text-align:center;">
                    <p class="posicion-3">🥉 #3</p>
                    {foto_html}
                    <h3 style="margin:5px 0;">{t["Participante"]}</h3>
                    <h2 style="margin:0;">{int(t["Total"])} pts</h2>
                </div>''', unsafe_allow_html=True)

    # =================================================================
    # ANALISIS IA DEL MOMENTO
    # =================================================================
    if bienvenida_data:
        intro_txt = str(bienvenida_data.get("bienvenida", "") or "").strip()
        generado_txt = str(bienvenida_data.get("analisis_generado_a", "") or "").strip()
        if intro_txt:
            st.markdown("---")
            st.markdown("### 🧠 Análisis del momento")
            if generado_txt:
                st.caption(f"Generado al momento del análisis: {generado_txt}")
            st.markdown(
                f'<div style="padding:14px 18px; background:linear-gradient(135deg, #1B2838, #2C3E50); '
                f'border-left:3px solid #C8E600; border-radius:8px;">'
                f'<p style="color:#E8EEF7; font-size:1rem; line-height:1.7; margin:0;">💬 {intro_txt}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    # =================================================================
    # TABLA COMPLETA CON SELECTOR DE COLUMNAS
    # =================================================================
    st.markdown("---")
    st.markdown("### 📋 Tabla Completa")

    with st.expander("⚙️ Personalizar columnas", expanded=False):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            mostrar_grupos = st.checkbox("Desglose Grupos", value=False)
        with col_b:
            mostrar_elim = st.checkbox("Desglose Eliminatorias", value=False)
        with col_c:
            mostrar_esp = st.checkbox("Desglose Especiales", value=False)
        with col_d:
            mostrar_pen = st.checkbox("Desglose Penalidades", value=False)

    cols_mostrar = ["Posición", "Participante", "Total"]
    if mostrar_grupos:
        cols_mostrar.extend(["Grupos L/E/V", "Grupos Exacto"])
    else:
        cols_mostrar.append("Grupos")
    if mostrar_elim:
        cols_mostrar.extend(["16vos", "8vos", "4tos", "Semis", "Final"])
    else:
        cols_mostrar.append("Eliminatorias")
    cols_mostrar.extend(["Campeón", "3ero"])
    if mostrar_esp:
        cols_mostrar.extend(["Figura", "Goleador", "Revelación", "Decepción", "Mejor 1era Fase", "Peor Equipo"])
    else:
        cols_mostrar.append("Especiales")
    if mostrar_pen:
        cols_mostrar.extend(["Pen. Revelación", "Pen. Campeón", "Pen. Peor Equipo", "Pen. Decepción"])
    else:
        cols_mostrar.append("Penalidades")

    cols_mostrar = [c for c in cols_mostrar if c in leaderboard.columns]
    df_mostrar = leaderboard[cols_mostrar]

    def estilizar(row):
        pos = row["Posición"]
        n = len(df_mostrar)
        if pos == 1:
            return ['background-color: rgba(255,69,0,0.3); font-weight:bold'] * len(row)
        elif pos == 2:
            return ['background-color: rgba(192,192,192,0.15)'] * len(row)
        elif pos == 3:
            return ['background-color: rgba(205,127,50,0.15)'] * len(row)
        elif pos >= n - 2 and n > 5:
            return ['background-color: rgba(0,100,200,0.15); font-style:italic'] * len(row)
        return [''] * len(row)

    st.dataframe(df_mostrar.style.apply(estilizar, axis=1),
        use_container_width=True, hide_index=True,
        height=min(len(leaderboard) * 40 + 60, 700))

    # =================================================================
    # GRAFICO DE BARRAS CON PENALIDADES
    # =================================================================
    st.markdown("### 📊 Desglose de Puntos")

    modo_grafico = st.radio(
        "Vista del gráfico:",
        ["Resumido", "Detallado"],
        horizontal=True,
        key="modo_grafico_puntos"
    )

    fig = go.Figure()

    if modo_grafico == "Resumido":
        categorias_barras = [
            ("Grupos", "#C8E600"),
            ("Eliminatorias", "#4A90D9"),
            ("Campeón", "#E67E22"),
            ("3ero", "#F39C12"),
            ("Especiales", "#9B59B6"),
        ]
    else:
        categorias_barras = [
            ("Grupos L/E/V", "#7ED957"),
            ("Grupos Exacto", "#C8E600"),
            ("Eliminatorias", "#4A90D9"),
            ("Campeón", "#E67E22"),
            ("3ero", "#F39C12"),
            ("Especiales", "#9B59B6"),
        ]

    # Solo usar columnas que realmente existan
    categorias_barras = [(cat, color) for cat, color in categorias_barras if cat in leaderboard.columns]

    for cat_idx, (cat, color) in enumerate(categorias_barras):
        bases = []
        for _, row in leaderboard.iterrows():
            pen = float(row["Penalidades"]) if "Penalidades" in leaderboard.columns else 0.0
            base = pen
            for prev_cat, _ in categorias_barras[:cat_idx]:
                if prev_cat in leaderboard.columns:
                    base += float(row[prev_cat])
            bases.append(base)

        fig.add_trace(go.Bar(
            x=leaderboard["Participante"],
            y=leaderboard[cat],
            base=bases,
            name=cat,
            marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + cat + ": %{y}<extra></extra>",
        ))

    if "Penalidades" in leaderboard.columns:
        for _, row in leaderboard.iterrows():
            pen = int(row["Penalidades"])
            if pen < 0:
                fig.add_annotation(
                    x=row["Participante"],
                    y=pen / 2,
                    text=f"<b>{pen}</b>",
                    showarrow=False,
                    font=dict(color="#E74C3C", size=11, family="Arial Black"),
                )

    fig.update_layout(
        barmode="overlay",
        template="plotly_dark",
        height=550,
        xaxis_title="Participante",
        yaxis_title="Puntos",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            zeroline=True,
            zerolinecolor="rgba(255,255,255,0.4)",
            zerolinewidth=2
        ),
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Comentario toxico para penalizados
    hay_penalidades = (leaderboard["Penalidades"] < 0).any()
    if hay_penalidades:
        penalizados = leaderboard[leaderboard["Penalidades"] < 0]["Participante"].tolist()
        if len(penalizados) == 1:
            msg_pen = f"⚠️ _{penalizados[0]} arranca desde el subsuelo por sus predicciones desastrosas._"
        elif len(penalizados) <= 3:
            msg_pen = f"⚠️ _{', '.join(penalizados[:-1])} y {penalizados[-1]}: arrancan en números rojos. Bienvenidos al sótano del PRODE._"
        else:
            msg_pen = f"⚠️ _{len(penalizados)} de {len(leaderboard)} arrancan en rojo. ¿Esto es un PRODE o un cementerio de predicciones?_"
        st.markdown(f"> {msg_pen}")

    # =================================================================
    # MENSAJES TOXICOS POR POSICION
    # =================================================================
    from utils.messages import obtener_mensaje_posicion
    st.markdown("---")
    st.markdown("### 💬 Mensajes del Día")
    n = len(leaderboard)
    mensajes_ia = bienvenida_data.get("mensajes_dia", {}) if isinstance(bienvenida_data, dict) else {}

    for _, row in leaderboard.iterrows():
        pos = int(row["Posición"])
        nombre = row["Participante"]
        if pos <= 3 or pos >= n - 2:
            msg = mensajes_ia.get(nombre, "")
            if not msg:
                msg = obtener_mensaje_posicion(nombre, pos, n, int(row["Total"]))
            st.markdown(f"> {msg}")

    # =================================================================
    # INFO GENERAL + APOSTADORES (colapsable)
    # =================================================================
    st.divider()
    with st.expander("🌍 Info del PRODE", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🌍 FIFA World Cup 2026")
            st.markdown("**Sedes:** USA, México, Canadá\n\n**Equipos:** 48\n\n**Máximo:** 431 pts")
        with col2:
            st.markdown("### 📋 Cómo funciona")
            st.markdown("1. Cada participante completó su Excel\n2. Resultados de la API\n3. Puntos automáticos\n4. **El último... sufre.**")
        with col3:
            st.markdown("### 🏆 Premios")
            st.markdown("🥇 Gloria eterna\n🥈 Respeto condicional\n🥉 Mejor en Grupos\n💀 Vergüenza pública")

    # Apostadores con comentarios
    if "categorias_todos" in st.session_state:
        with st.expander("🎭 Los Apostadores y sus Delirios", expanded=False):
            categorias_todos = st.session_state.get("categorias_todos", {})
            participantes_info_map = cargar_participantes_info()
            comentarios_campeon = {
                "Argentina": "Obvio, papá. ¿Quién no va con la Scaloneta?",
                "Brasil": "Ir con Brasil siendo argentino es como aplaudir un gol en contra. Traidor.",
                "Francia": "¿Francia? ¿Después de Qatar? Memoria selectiva.",
                "Alemania": "Eficiencia alemana. Aburrido pero respetable.",
                "España": "Tiki-taka hasta que los eliminen en cuartos.",
                "Inglaterra": "🚨 TRAIDOR A LA PATRIA DETECTADO. Las Malvinas son argentinas.",
                "Portugal": "CR7 con andador. Romántico pero delirante.",
                "Paises Bajos": "La naranja mecánica: siempre de novias, nunca de novia.",
                "Belgica": "Generación dorada que se oxida sin ganar nada.",
                "Uruguay": "Garra charrúa con mate y nostalgia.",
                "Colombia": "James, Díaz y mucha cumbia. ¿Alcanza?",
                "Croacia": "Modric tiene más mundiales que años de vida.",
                "Mexico": "Algún día van a pasar de octavos. ¿No?",
                "Estados Unidos": "Esto no es el Super Bowl, amigo.",
                "Japon": "Si el anime enseñó algo es que Japón siempre gana al final.",
                "Marruecos": "Los leones del Atlas. ¿Pueden rugir más fuerte?",
                "Escocia": "Escocia campeón... y yo soy astronauta.",
                "Noruega": "Haaland solo contra el mundo.",
                "Suiza": "Neutral en todo, hasta en las apuestas.",
                "Senegal": "Los Leones de la Teranga. Valiente apuesta.",
                "Ecuador": "¡Sí se puede! La historia dice que no.",
                "Canada": "Esto no es hockey sobre hielo, amigo.",
            }
            comentario_default_list = [
                "¿Esto va en serio o le hackearon el Excel?",
                "Apuesta tan arriesgada que debería pagar impuestos.",
                "Le puso más huevos que criterio. Respetable.",
                "Si esto sale, nos retiramos todos del PRODE.",
                "Audaz. Delirante. Probablemente borracho cuando lo completó.",
                "Eligió con el corazón. Lástima que el corazón no sabe de fútbol.",
            ]

            for i, (nombre, cats) in enumerate(sorted(categorias_todos.items()), 1):
                camp = cats.get("Campeon", "No definido")
                nacionalidad = participantes_info_map.get(nombre, {}).get("nacionalidad", "")
                comentario = comentario_campeon_contextual(nombre, camp, nacionalidad) or comentarios_campeon.get(camp, "")
                if not comentario:
                    random.seed(hash(nombre + camp))
                    comentario = random.choice(comentario_default_list)

                foto = foto_participante(nombre)
                col_num, col_foto, col_info = st.columns([0.5, 0.8, 10])
                with col_num:
                    st.markdown(f"**{i}.**")
                with col_foto:
                    if foto:
                        st.image(foto, width=35)
                with col_info:
                    st.markdown(f'**{nombre}** → 🏆 _{camp}_')
                    st.markdown(f'<span style="color: #888; font-size: 0.9rem;">{comentario}</span>',
                        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
