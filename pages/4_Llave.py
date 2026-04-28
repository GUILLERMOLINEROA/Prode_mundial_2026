# =============================================================================
# pages/4_Llave.py
# Visualización del bracket/llave del Mundial 2026.
# Se llena automáticamente con los resultados de la API o simulación.
# =============================================================================

import streamlit as st
import pandas as pd
import os

from utils.api_football import clasificar_ronda

st.set_page_config(page_title="Llave del Mundial", page_icon="🏟️", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def obtener_resultados():
    """Obtiene resultados del session_state o genera simulación."""
    resultados = st.session_state.get("resultados", pd.DataFrame())
    if resultados.empty:
        usar_sim = st.toggle("🎮 Usar resultados simulados", value=True)
        if usar_sim:
            from utils.simulacion import generar_resultados_simulados
            resultados = generar_resultados_simulados()
    return resultados


def formato_resultado(row):
    """Formatea el resultado de un partido para mostrar."""
    gl = row.get("goles_local")
    gv = row.get("goles_visitante")
    pl = row.get("penales_local")
    pv = row.get("penales_visitante")
    
    if pd.isna(gl) or pd.isna(gv):
        return "vs"
    
    texto = f"{int(gl)} - {int(gv)}"
    if pd.notna(pl) and pd.notna(pv):
        texto += f" (Pen: {int(pl)}-{int(pv)})"
    return texto


def determinar_ganador(row):
    """Determina el ganador de un partido."""
    gl = row.get("goles_local")
    gv = row.get("goles_visitante")
    pl = row.get("penales_local")
    pv = row.get("penales_visitante")
    
    if pd.isna(gl) or pd.isna(gv):
        return ""
    
    if gl > gv:
        return row["equipo_local"]
    elif gv > gl:
        return row["equipo_visitante"]
    elif pd.notna(pl) and pd.notna(pv):
        return row["equipo_local"] if pl > pv else row["equipo_visitante"]
    return ""


def render_partido(row, ancho="100%"):
    """Renderiza un partido como una tarjeta HTML."""
    local = row.get("equipo_local", "?")
    visitante = row.get("equipo_visitante", "?")
    resultado = formato_resultado(row)
    ganador = determinar_ganador(row)
    estado = row.get("estado", "NS")
    
    # Colores según estado
    if estado == "FT":
        borde = "#2ecc71"
        bg = "#1a2e1a"
    elif estado in ("1H", "2H", "HT"):
        borde = "#e74c3c"
        bg = "#2e1a1a"
    else:
        borde = "#555"
        bg = "#1a1a2e"
    
    # Resaltar ganador
    local_style = "color: #ffd700; font-weight: bold;" if ganador == local else "color: #ccc;"
    visit_style = "color: #ffd700; font-weight: bold;" if ganador == visitante else "color: #ccc;"
    
    return f'''
    <div style="background: {bg}; border: 1px solid {borde}; border-radius: 8px;
                padding: 8px 12px; margin: 4px 0; min-width: 200px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="{local_style} font-size: 0.9rem;">{local}</span>
        </div>
        <div style="text-align: center; font-size: 1.1rem; font-weight: bold;
                    color: white; margin: 4px 0;">{resultado}</div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="{visit_style} font-size: 0.9rem;">{visitante}</span>
        </div>
    </div>
    '''


def render_partido_vacio(label="?"):
    """Renderiza un placeholder para un partido sin datos."""
    return f'''
    <div style="background: #1a1a2e; border: 1px dashed #333; border-radius: 8px;
                padding: 8px 12px; margin: 4px 0; min-width: 200px; opacity: 0.5;">
        <div style="text-align: center; color: #555; font-size: 0.9rem;">{label}</div>
        <div style="text-align: center; color: #555; font-size: 1rem; margin: 4px 0;">vs</div>
        <div style="text-align: center; color: #555; font-size: 0.9rem;">?</div>
    </div>
    '''


def obtener_partidos_ronda(resultados, ronda_nombre):
    """Filtra partidos por ronda."""
    if resultados.empty:
        return pd.DataFrame()
    return resultados[
        resultados["ronda"].apply(lambda x: clasificar_ronda(str(x))) == ronda_nombre
    ].reset_index(drop=True)


def main():
    st.markdown(
        '<h1 class="titulo-prode">🏟️ LLAVE DEL MUNDIAL 2026</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center; color:#888;">'
        'El camino hacia la gloria... o la eliminación.</p>',
        unsafe_allow_html=True
    )
    
    resultados = obtener_resultados()
    
    if resultados.empty:
        st.warning("⚠️ No hay resultados disponibles. Activá la simulación o configurá la API.")
        return
    
    # --- Fase de Grupos ---
    st.markdown("---")
    st.markdown("## 📋 Fase de Grupos")
    
    partidos_grupos = obtener_partidos_ronda(resultados, "grupos")
    
    if not partidos_grupos.empty:
        # Extraer grupos únicos
        grupos = sorted(partidos_grupos["ronda"].unique())
        
        # Selector de grupo
        grupo_sel = st.selectbox("Seleccioná un grupo:", grupos)
        
        partidos_grupo = resultados[resultados["ronda"] == grupo_sel].reset_index(drop=True)
        
        # Calcular tabla del grupo
        tabla = {}
        for _, p in partidos_grupo.iterrows():
            for eq in [p["equipo_local"], p["equipo_visitante"]]:
                if eq not in tabla:
                    tabla[eq] = {"PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "Pts": 0}
            
            gl, gv = p["goles_local"], p["goles_visitante"]
            if pd.notna(gl) and pd.notna(gv):
                gl, gv = int(gl), int(gv)
                for eq in [p["equipo_local"], p["equipo_visitante"]]:
                    tabla[eq]["PJ"] += 1
                
                if gl > gv:
                    tabla[p["equipo_local"]]["G"] += 1
                    tabla[p["equipo_local"]]["Pts"] += 3
                    tabla[p["equipo_visitante"]]["P"] += 1
                elif gv > gl:
                    tabla[p["equipo_visitante"]]["G"] += 1
                    tabla[p["equipo_visitante"]]["Pts"] += 3
                    tabla[p["equipo_local"]]["P"] += 1
                else:
                    tabla[p["equipo_local"]]["E"] += 1
                    tabla[p["equipo_visitante"]]["E"] += 1
                    tabla[p["equipo_local"]]["Pts"] += 1
                    tabla[p["equipo_visitante"]]["Pts"] += 1
                
                tabla[p["equipo_local"]]["GF"] += gl
                tabla[p["equipo_local"]]["GC"] += gv
                tabla[p["equipo_visitante"]]["GF"] += gv
                tabla[p["equipo_visitante"]]["GC"] += gl
        
        if tabla:
            df_tabla = pd.DataFrame([
                {"Equipo": eq, **stats, "DG": stats["GF"] - stats["GC"]}
                for eq, stats in tabla.items()
            ]).sort_values(by=["Pts", "DG", "GF"], ascending=[False, False, False])
            
            # Resaltar clasificados (primeros 2)
            def color_clasificados(row):
                idx = df_tabla.index.get_loc(row.name)
                if idx == 0:
                    return ['background-color: rgba(46, 204, 113, 0.3)'] * len(row)
                elif idx == 1:
                    return ['background-color: rgba(46, 204, 113, 0.15)'] * len(row)
                elif idx == 2:
                    return ['background-color: rgba(241, 196, 15, 0.1)'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df_tabla[["Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]]
                .style.apply(color_clasificados, axis=1),
                use_container_width=True, hide_index=True
            )
            st.caption("🟢 Clasificados directo | 🟡 Posible mejor tercero")
        
        # Mostrar partidos del grupo
        st.markdown(f"#### Partidos - {grupo_sel}")
        for _, p in partidos_grupo.iterrows():
            st.markdown(render_partido(p), unsafe_allow_html=True)
    
    # --- ELIMINATORIAS ---
    st.markdown("---")
    st.markdown("## 🏆 Fase Eliminatoria")
    
    # --- Round of 32 (16vos) ---
    partidos_16 = obtener_partidos_ronda(resultados, "16vos")
    
    if not partidos_16.empty:
        st.markdown("### 🔵 Dieciseisavos de Final (Round of 32)")
        
        col1, col2 = st.columns(2)
        mitad = len(partidos_16) // 2
        
        with col1:
            st.markdown("#### Itinerario 1")
            for _, p in partidos_16.iloc[:mitad].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Itinerario 2")
            for _, p in partidos_16.iloc[mitad:].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
    
    # --- Round of 16 (8vos) ---
    partidos_8 = obtener_partidos_ronda(resultados, "8vos")
    
    if not partidos_8.empty:
        st.markdown("### 🟢 Octavos de Final (Round of 16)")
        
        col1, col2 = st.columns(2)
        mitad = len(partidos_8) // 2
        
        with col1:
            st.markdown("#### Itinerario 1")
            for _, p in partidos_8.iloc[:mitad].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Itinerario 2")
            for _, p in partidos_8.iloc[mitad:].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
    
    # --- Cuartos ---
    partidos_4 = obtener_partidos_ronda(resultados, "4tos")
    
    if not partidos_4.empty:
        st.markdown("### 🟡 Cuartos de Final")
        
        col1, col2 = st.columns(2)
        mitad = max(len(partidos_4) // 2, 1)
        
        with col1:
            for _, p in partidos_4.iloc[:mitad].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
        
        with col2:
            for _, p in partidos_4.iloc[mitad:].iterrows():
                st.markdown(render_partido(p), unsafe_allow_html=True)
    
    # --- Semifinales ---
    partidos_semi = obtener_partidos_ronda(resultados, "semis")
    
    if not partidos_semi.empty:
        st.markdown("### 🟠 Semifinales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if len(partidos_semi) >= 1:
                st.markdown(render_partido(partidos_semi.iloc[0]), unsafe_allow_html=True)
        
        with col2:
            if len(partidos_semi) >= 2:
                st.markdown(render_partido(partidos_semi.iloc[1]), unsafe_allow_html=True)
    
    # --- 3er puesto y Final ---
    partidos_3ero = obtener_partidos_ronda(resultados, "3ero")
    partidos_final = obtener_partidos_ronda(resultados, "final")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not partidos_3ero.empty:
            st.markdown("### 🥉 Tercer Puesto")
            p = partidos_3ero.iloc[0]
            st.markdown(render_partido(p), unsafe_allow_html=True)
            ganador_3 = determinar_ganador(p)
            if ganador_3:
                st.success(f"🥉 **{ganador_3}** se lleva el tercer puesto")
    
    with col2:
        if not partidos_final.empty:
            st.markdown("### 🏆 FINAL")
            p = partidos_final.iloc[0]
            st.markdown(render_partido(p), unsafe_allow_html=True)
            campeon = determinar_ganador(p)
            if campeon:
                st.markdown(
                    f'<div style="text-align:center; background: linear-gradient(135deg, #4a0000, #8b0000); '
                    f'border: 2px solid #ffd700; border-radius: 15px; padding: 20px; margin: 10px 0;">'
                    f'<h1 style="color: #ffd700;">🏆 {campeon} 🏆</h1>'
                    f'<p style="color: #ffd700; font-size: 1.5rem;">¡CAMPEÓN DEL MUNDO 2026!</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    # --- Resumen del torneo ---
    if not partidos_final.empty:
        campeon = determinar_ganador(partidos_final.iloc[0])
        subcampeon = partidos_final.iloc[0]["equipo_visitante"] if campeon == partidos_final.iloc[0]["equipo_local"] else partidos_final.iloc[0]["equipo_local"]
        tercero = determinar_ganador(partidos_3ero.iloc[0]) if not partidos_3ero.empty else ""
        
        st.markdown("---")
        st.markdown("### 🏅 Resumen Final")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div style="text-align:center; padding:20px;">'
                f'<h1>🥇</h1><h3 style="color:#ffd700;">{campeon}</h3>'
                f'<p>Campeón</p></div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f'<div style="text-align:center; padding:20px;">'
                f'<h1>🥈</h1><h3 style="color:#c0c0c0;">{subcampeon}</h3>'
                f'<p>Sub-campeón</p></div>',
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f'<div style="text-align:center; padding:20px;">'
                f'<h1>🥉</h1><h3 style="color:#cd7f32;">{tercero}</h3>'
                f'<p>Tercer puesto</p></div>',
                unsafe_allow_html=True
            )


# --- Ejecutar ---
main()
