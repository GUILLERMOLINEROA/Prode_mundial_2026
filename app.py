import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone

st.set_page_config(page_title="La Previa - PRODE 2026", page_icon="🎭", layout="wide")

def cargar_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_css()

# =============================================================================
# COUNTDOWN
# =============================================================================
FECHA_INAUGURAL = datetime(2026, 6, 11, 21, 0, 0, tzinfo=timezone.utc)

ahora = datetime.now(timezone.utc)
delta = FECHA_INAUGURAL - ahora

if delta.total_seconds() > 0:
    dias = delta.days
    horas = delta.seconds // 3600
    minutos = (delta.seconds % 3600) // 60

    st.markdown(f"""
    <div style="text-align:center; padding:30px; margin-bottom:20px;
                background: linear-gradient(135deg, #1B2838 0%, #2C3E50 100%);
                border: 2px solid #C8E600; border-radius:15px;">
        <p style="color:#C8E600; font-size:1.2rem; margin-bottom:5px;">
            ⏰ FALTAN PARA EL PARTIDO INAUGURAL</p>
        <div style="display:flex; justify-content:center; gap:30px;">
            <div>
                <span style="color:#C8E600; font-size:3.5rem; font-weight:bold;">{dias}</span>
                <p style="color:#AEC6CF; font-size:0.9rem;">DÍAS</p>
            </div>
            <div>
                <span style="color:#C8E600; font-size:3.5rem; font-weight:bold;">{horas}</span>
                <p style="color:#AEC6CF; font-size:0.9rem;">HORAS</p>
            </div>
            <div>
                <span style="color:#C8E600; font-size:3.5rem; font-weight:bold;">{minutos}</span>
                <p style="color:#AEC6CF; font-size:0.9rem;">MINUTOS</p>
            </div>
        </div>
        <p style="color:#888; font-size:0.9rem; margin-top:10px;">
            🏟️ México vs Sudáfrica — 11 de junio de 2026</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:20px;
                background: linear-gradient(135deg, #1B2838 0%, #2C3E50 100%);
                border: 2px solid #C8E600; border-radius:15px;">
        <p style="color:#C8E600; font-size:2rem;">🔥 ¡EL MUNDIAL YA ARRANCÓ! 🔥</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="titulo-prode">🎭 LA PREVIA DEL PRODE 🎭</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
    'El mundial no arrancó, pero las cargadas sí.</p>', unsafe_allow_html=True)
st.divider()

# --- Cargar datos de los Excels ---
from utils.excel_reader import cargar_todos_los_participantes
from utils.data_loader import foto_participante

grupos, elim, categorias, total_results = cargar_todos_los_participantes()

if not categorias:
    st.error("No se pudieron cargar los datos de los participantes.")
    st.stop()

# =============================================================================
# 1. TABLA DE ENTREGAS
# =============================================================================
st.markdown("## 🏅 ¿Quién entregó primero?")
st.markdown("*La puntualidad dice mucho de una persona. La impuntualidad también.*")

entregas = [
    {"Orden": "🥇", "Participante": "GELA", "Fecha": "10 abril", "Hora": "08:15", "Veredicto": "El aplicado. Entregó antes que nadie. Sospechoso."},
    {"Orden": "🥈", "Participante": "JUSO", "Fecha": "12 abril", "Hora": "14:30", "Veredicto": "Responsable. O ansioso. O las dos."},
    {"Orden": "🥉", "Participante": "AGCR", "Fecha": "15 abril", "Hora": "09:00", "Veredicto": "En el podio de la puntualidad. Bien ahí."},
    {"Orden": "4", "Participante": "MITU", "Fecha": "18 abril", "Hora": "11:45", "Veredicto": "Justo a tiempo. Ni muy muy, ni tan tan."},
    {"Orden": "5", "Participante": "FASA", "Fecha": "22 abril", "Hora": "16:20", "Veredicto": "Se tomó su tiempo. 'Estaba analizando', dijo."},
    {"Orden": "6", "Participante": "PASC", "Fecha": "25 abril", "Hora": "10:00", "Veredicto": "Llegó tarde pero llegó. Como Argentina al segundo tiempo."},
    {"Orden": "7", "Participante": "MAEG", "Fecha": "28 abril", "Hora": "23:55", "Veredicto": "Casi no llega. Curazao campeón a las 11 de la noche. Dice todo."},
    {"Orden": "8", "Participante": "ALDO", "Fecha": "29 abril", "Hora": "23:59", "Veredicto": "Último. El Excel lo completó en el Uber. Curazao campeón. Sin palabras."},
]
df_entregas = pd.DataFrame(entregas)
st.dataframe(df_entregas, use_container_width=True, hide_index=True)

# =============================================================================
# 2. CAMPEONES ELEGIDOS
# =============================================================================
st.divider()
st.markdown("## 🏆 ¿A quién le apostaron?")
st.markdown("*Las elecciones de campeón revelan la personalidad de cada uno.*")

comentarios_campeon_previa = {
    "Argentina": "🇦🇷 Patriota. Se respeta. Pero solo uno tuvo los huevos de ponerla.",
    "Alemania": "🇩🇪 Frío, calculador, eficiente. Como un ingeniero alemán. Aburrido pero peligroso.",
    "Ecuador": "🇪🇨 Ecuador campeón. Leíste bien. ECUADOR. La audacia tiene un nombre.",
    "Curazao": "🇨🇼 CURAZAO. 170.000 habitantes. Clase 4. Este completó el Excel borracho o es un visionario. No hay punto medio.",
    "Republica Checa": "🇨🇿 República Checa campeón. Nedved se retiró hace 15 años pero el sueño sigue vivo.",
    "Costa de Marfil": "🇨🇮 Los Elefantes campeones del mundo. Drogba estaría orgulloso. Lástima que ya se retiró.",
    "Argelia": "🇩🇿 Argelia. Si gana, este tipo se tatúa la copa en la frente.",
    "Brasil": "🇧🇷 Brasil. Clásico. Predecible. Como poner 'empate' en todos los partidos.",
    "Francia": "🇫🇷 Francia. Después de Qatar. Memoria selectiva o masoquismo.",
    "España": "🇪🇸 Tiki-taka. Posesión. Y eliminación en cuartos como siempre.",
    "Inglaterra": "🏴 TRAIDOR A LA PATRIA DETECTADO.",
}
comentario_default = "Una elección... interesante. Guardamos esto para julio."

campeones = {}
for nombre, cats in categorias.items():
    c = cats.get("Campeon", "?")
    if c not in campeones:
        campeones[c] = []
    campeones[c].append(nombre)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Distribución de campeones")
    for campeon, apostadores in sorted(campeones.items(), key=lambda x: -len(x[1])):
        barra = "🟩" * len(apostadores)
        nombres = ", ".join(apostadores)
        st.markdown(f"**{campeon}** {barra} ({len(apostadores)})")
        st.caption(f"→ {nombres}")

with col2:
    st.markdown("### El diagnóstico")
    total_participantes = len(categorias)
    equipos_unicos = len(campeones)
    st.metric("Equipos distintos elegidos", f"{equipos_unicos} de {total_participantes}")

    if equipos_unicos == total_participantes:
        st.info("🎯 Todos eligieron distinto. Esto va a estar bueno.")
    elif equipos_unicos <= 3:
        st.warning("🐑 Poca originalidad. ¿Se copiaron?")

    for campeon, apostadores in campeones.items():
        if len(apostadores) >= 2:
            st.warning(f"👯 {' y '.join(apostadores)} coinciden en **{campeon}**. ¿Se mandaron WhatsApp?")

st.divider()

st.markdown("### 🎭 Cada apostador y su delirio")
for nombre, cats in sorted(categorias.items()):
    campeon = cats.get("Campeon", "?")
    goleador = cats.get("Goleador", "?")
    figura = cats.get("Figura", "?")
    revelacion = cats.get("Revelación", "?")
    decepcion = cats.get("Decepción", "?")

    comentario = comentarios_campeon_previa.get(campeon, comentario_default)
    foto = foto_participante(nombre)

    with st.container():
        c1, c2, c3 = st.columns([0.5, 3, 8])
        with c1:
            if foto:
                st.image(foto, width=40)
        with c2:
            st.markdown(f"#### {nombre}")
        with c3:
            st.markdown(
                f"🏆 **{campeon}** | ⚽ {goleador} | ⭐ {figura} | "
                f"💡 {revelacion} | 💀 {decepcion}"
            )
            st.markdown(f'<span style="color:#C8E600; font-style:italic;">{comentario}</span>',
                unsafe_allow_html=True)
        st.markdown("---")

# =============================================================================
# 3. ESTADISTICAS RIDICULAS
# =============================================================================
st.divider()
st.markdown("## 📊 Estadísticas Ridículas")
st.markdown("*Números que nadie pidió pero todos necesitan.*")

col1, col2, col3, col4 = st.columns(4)

if not grupos.empty:
    goles_por_participante = {}
    for p in grupos["participante"].unique():
        sub = grupos[grupos["participante"] == p]
        gl = sub["goles_local_pred"].sum()
        gv = sub["goles_visitante_pred"].sum()
        goles_por_participante[p] = int(gl + gv)

    mas_goles = max(goles_por_participante, key=goles_por_participante.get)
    menos_goles = min(goles_por_participante, key=goles_por_participante.get)

    with col1:
        st.metric("🔥 El Goleador", mas_goles, f"{goles_por_participante[mas_goles]} goles")
        st.caption("Predice más goles que nadie. Optimista o ingenuo.")

    with col2:
        st.metric("🧱 El Catenaccio", menos_goles, f"{goles_por_participante[menos_goles]} goles")
        st.caption("Para este el fútbol se juega 0-0 y penales.")

argentinistas = [n for n, c in categorias.items() if c.get("Campeon") == "Argentina"]
with col3:
    if argentinistas:
        st.metric("🇦🇷 Patriotas", len(argentinistas))
        st.caption(f"{', '.join(argentinistas)}. Los únicos con sangre.")
    else:
        st.metric("🇦🇷 Patriotas", "0")
        st.caption("NADIE puso Argentina. Vergüenza nacional.")

traidores = [n for n, c in categorias.items() if c.get("Campeon") == "Inglaterra"]
with col4:
    if traidores:
        st.metric("🚨 Traidores", len(traidores))
        st.caption(f"{', '.join(traidores)}. Las Malvinas son argentinas.")
    else:
        st.metric("🚨 Traidores", "0")
        st.caption("Nadie puso a Inglaterra. Bien ahí.")

st.markdown("### 🔍 Más datos inútiles")

col1, col2 = st.columns(2)

with col1:
    goleadores = {}
    for nombre, cats in categorias.items():
        g = cats.get("Goleador", "?")
        if g not in goleadores:
            goleadores[g] = []
        goleadores[g].append(nombre)

    st.markdown("**⚽ Goleador más votado:**")
    for gol, quienes in sorted(goleadores.items(), key=lambda x: -len(x[1])):
        st.markdown(f"- **{gol}**: {', '.join(quienes)} ({len(quienes)})")

with col2:
    figuras = {}
    for nombre, cats in categorias.items():
        f = cats.get("Figura", "?")
        if f not in figuras:
            figuras[f] = []
        figuras[f].append(nombre)

    st.markdown("**⭐ Figura más votada:**")
    for fig, quienes in sorted(figuras.items(), key=lambda x: -len(x[1])):
        st.markdown(f"- **{fig}**: {', '.join(quienes)} ({len(quienes)})")

# =============================================================================
# 4. COINCIDENCIAS ENTRE PARTICIPANTES
# =============================================================================
st.divider()
st.markdown("## 🤝 ¿Quiénes piensan igual?")
st.markdown("*Coincidencias sospechosas entre participantes.*")

if not grupos.empty:
    participantes_lista = sorted(grupos["participante"].unique())
    coincidencias = []

    for i, p1 in enumerate(participantes_lista):
        for p2 in participantes_lista[i+1:]:
            sub1 = grupos[grupos["participante"] == p1].sort_values(["grupo", "equipo_local"]).reset_index(drop=True)
            sub2 = grupos[grupos["participante"] == p2].sort_values(["grupo", "equipo_local"]).reset_index(drop=True)

            matches = 0
            total = min(len(sub1), len(sub2))
            for idx in range(total):
                g1_l = sub1.iloc[idx].get("goles_local_pred")
                g1_v = sub1.iloc[idx].get("goles_visitante_pred")
                g2_l = sub2.iloc[idx].get("goles_local_pred")
                g2_v = sub2.iloc[idx].get("goles_visitante_pred")

                if pd.notna(g1_l) and pd.notna(g1_v) and pd.notna(g2_l) and pd.notna(g2_v):
                    r1 = "L" if g1_l > g1_v else ("V" if g1_v > g1_l else "E")
                    r2 = "L" if g2_l > g2_v else ("V" if g2_v > g2_l else "E")
                    if r1 == r2:
                        matches += 1

            pct = round(100 * matches / total) if total > 0 else 0
            coincidencias.append({"Pareja": f"{p1} vs {p2}", "Coincidencias": matches, "De": total, "%": pct})

    df_coin = pd.DataFrame(coincidencias).sort_values("%", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👯 Más parecidos")
        for _, row in df_coin.head(3).iterrows():
            emoji = "🚨" if row["%"] > 70 else "👀"
            st.markdown(f"{emoji} **{row['Pareja']}**: {row['%']}% coincidencia ({row['Coincidencias']}/{row['De']})")
            if row["%"] > 70:
                st.caption("¿Se copiaron? ¿Compartieron Excel? Investigación en curso.")

    with col2:
        st.markdown("### ⚔️ Más distintos")
        for _, row in df_coin.tail(3).iterrows():
            st.markdown(f"🔥 **{row['Pareja']}**: {row['%']}% coincidencia ({row['Coincidencias']}/{row['De']})")
        st.caption("Estos dos no coinciden ni en el día de la semana.")

# =============================================================================
# 5. MURO DE LA VERGÜENZA
# =============================================================================
st.divider()
st.markdown("## 🧱 El Muro de la Vergüenza")
st.markdown("*Predicciones que van a envejecer MUY mal. Guardamos todo para julio.*")

verguenzas = []
for nombre, cats in categorias.items():
    campeon = cats.get("Campeon", "")
    revelacion = cats.get("Revelación", "")
    goleador = cats.get("Goleador", "")

    if campeon in ["Curazao", "Haiti", "Nueva Zelanda", "Qatar", "Irak", "Jordania", "Cabo Verde", "Uzbekistan", "Congo"]:
        verguenzas.append(f"🤯 **{nombre}** puso a **{campeon}** campeón del mundo. Guardamos esto con llave.")

    if revelacion == campeon and revelacion:
        verguenzas.append(f"🔄 **{nombre}** puso a **{campeon}** como campeón Y revelación. Si ya es revelación, ¿cómo va a ser campeón? ¿O al revés?")

    if goleador and len(goleador) > 1 and goleador[0].islower():
        verguenzas.append(f"✏️ **{nombre}** escribió '{goleador}' como goleador. ¿Le costaba una mayúscula?")

    if "no hay" in revelacion.lower() or not revelacion:
        verguenzas.append(f"🤷 **{nombre}** dice que no hay revelación. Tan pesimista que ni apuesta.")

    # MEssi detector
    if goleador and any(c.isupper() for c in goleador[1:3]):
        verguenzas.append(f"⌨️ **{nombre}** escribió '{goleador}'. ¿Caps Lock trabado o es un código secreto?")

if not verguenzas:
    verguenzas.append("Sorprendentemente, nadie hizo nada vergonzoso. Imposible, revisamos de nuevo.")

for v in verguenzas:
    st.markdown(v)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.markdown(
    '<p style="text-align:center; color:#666; font-size:0.9rem;">'
    '⏰ El mundial arranca el <b>11 de junio de 2026</b>. '
    'Hasta entonces, esto es todo lo que hay para sufrir.<br>'
    'Todas las predicciones fueron guardadas. No hay vuelta atrás. 😈</p>',
    unsafe_allow_html=True
)
