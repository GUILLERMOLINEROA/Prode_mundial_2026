import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone
from utils.group_config import entregas_path

st.set_page_config(page_title="La Previa - PRODE 2026", page_icon="🎭", layout="wide")

TOTAL_ESPERADO = None  # Se define cuando se cierre la lista

def cargar_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def cargar_entregas():
    path = entregas_path()
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df["codigo"] = df["codigo"].str.strip()
    return df

def comentario_entrega(posicion, total_entregados, nombre):
    if posicion == 1:
        return "El aplicado. Entregó antes que nadie. ¿Ansioso o responsable? El tiempo lo dirá."
    elif posicion == 2:
        return "Segundo. No le ganó al primero pero le ganó a todos los demás."
    elif posicion == 3:
        return "Podio de la puntualidad. Bronce en responsabilidad."
    elif posicion == total_entregados and TOTAL_ESPERADO is None:
        return "Último por ahora... pero todavía faltan muchos. Puede zafar."
    elif posicion == total_entregados and TOTAL_ESPERADO is not None and total_entregados >= TOTAL_ESPERADO:
        return "ÚLTIMO. El Excel no se completa solo. Vergüenza máxima."
    elif posicion <= 5:
        return "De los primeros. Responsable. O no tenía nada mejor que hacer."
    elif posicion <= 10:
        return "Mitad de tabla. Ni muy muy, ni tan tan."
    elif posicion <= 15:
        return "Se tomó su tiempo. 'Estaba analizando', dijo. Claro."
    else:
        return "Casi último. El Excel lo completó en el Uber."

cargar_css()

# =============================================================================
# =============================================================================
# BANNER ROTATIVO (cambia cada 5 minutos)
# =============================================================================
import base64
import glob
banners_dir = os.path.join("assets", "banners")
banner_files = sorted(glob.glob(os.path.join(banners_dir, "banner*.png")))
if not banner_files:
    # Fallback al banner original
    banner_path = os.path.join("assets", "banner.png")
    if os.path.exists(banner_path):
        banner_files = [banner_path]
if banner_files:
    # Rotar cada 5 minutos: todos ven el mismo banner al mismo tiempo
    from datetime import datetime, timezone
    _ahora = datetime.now(timezone.utc)
    idx = ((_ahora.hour * 12) + (_ahora.minute // 5)) % len(banner_files)
    banner_elegido = banner_files[idx]
    with open(banner_elegido, "rb") as img:
        b64 = base64.b64encode(img.read()).decode()
    st.markdown(
        f'<div style="text-align:center; margin-bottom:20px;">'
        f'<img src="data:image/png;base64,{b64}" style="max-width:100%; border-radius:10px;">'
        f'</div>',
        unsafe_allow_html=True)

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

# Recordatorio fecha limite
FECHA_LIMITE = datetime(2026, 6, 1, 23, 59, 59, tzinfo=timezone.utc)
delta_limite = FECHA_LIMITE - ahora
if delta_limite.total_seconds() > 0:
    dias_limite = delta_limite.days
    st.markdown(
        f'<div style="text-align:center; padding:10px; margin-bottom:15px; '
        f'background:#2C3E50; border:1px solid #E74C3C; border-radius:8px;">'
        f'<span style="color:#E74C3C; font-size:1rem;">'
        f'\U0001f4cb Tenés <b>{dias_limite} días</b> para entregar tu PRODE '
        f'— Fecha límite: <b>1 de junio de 2026</b></span></div>',
        unsafe_allow_html=True)


st.markdown('<h1 class="titulo-prode">🎭 LA PREVIA DEL PRODE 🎭</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:1.3rem; color:#aaa;">'
    'El mundial no arrancó, pero las cargadas sí.</p>', unsafe_allow_html=True)
st.divider()

# --- Cargar datos ---
from utils.excel_reader import cargar_todos_los_participantes
from utils.data_loader import foto_participante

grupos, elim, categorias, total_results = cargar_todos_los_participantes()

if not categorias:
    st.error("No se pudieron cargar los datos de los participantes.")
    st.stop()

entregas = cargar_entregas()

# =============================================================================
# 1. TABLA DE ENTREGAS
# =============================================================================
st.markdown("## 🏅 ¿Quién entregó primero?")
st.markdown("*La puntualidad dice mucho de una persona. La impuntualidad también.*")

total_entregados = len(entregas)
# Banner de estado
st.markdown(
    f'<div style="text-align:center; padding:12px; background:#1B2838; '
    f'border:1px solid #C8E600; border-radius:8px; margin-bottom:15px;">'
    f'<span style="color:#C8E600; font-size:1.1rem;">'
    f'📋 Entregaron: <b>{total_entregados}</b> '
    f'| Esperamos entre 25 y 30 participantes</span></div>',
    unsafe_allow_html=True)

if not entregas.empty:
    tabla_entregas = []
    for i, row in entregas.iterrows():
        pos = i + 1
        nombre = row["codigo"]
        fecha = row["fecha"]
        hora = row["hora"]

        if pos == 1:
            orden = "🥇"
        elif pos == 2:
            orden = "🥈"
        elif pos == 3:
            orden = "🥉"
        else:
            orden = str(pos)

        veredicto = comentario_entrega(pos, total_entregados, nombre)

        tabla_entregas.append({
            "Orden": orden,
            "Participante": nombre,
            "Fecha": fecha,
            "Hora": hora,
            "Veredicto": veredicto,
        })

    df_entregas = pd.DataFrame(tabla_entregas)
    st.dataframe(df_entregas, use_container_width=True, hide_index=True)

    st.markdown(
        '<p style="text-align:center; color:#888; font-style:italic;">'
        '⏳ Esperamos entre 25 y 30 participantes. '
        '¿Se habrán olvidado o le tienen miedo al PRODE?</p>',
        unsafe_allow_html=True)
else:
    st.warning("No hay entregas registradas aún.")

# =============================================================================
# 2. CAMPEONES ELEGIDOS
# =============================================================================
st.divider()
st.markdown("## 🏆 ¿A quién le apostaron?")
st.markdown("*Las elecciones de campeón revelan la personalidad de cada uno.*")

comentarios_campeon_previa = {
    "Argentina": "🇦🇷 VAMOS CARAJO. La Scaloneta no se discute. Patriota de ley.",
    "Alemania": "🇩🇪 Frío, calculador, eficiente. Como un ingeniero alemán. Aburrido pero peligroso.",
    "Ecuador": "🇪🇨 Ecuador campeón. Leíste bien. ECUADOR. La audacia tiene un nombre.",
    "Curazao": "🇨🇼 CURAZAO. 170.000 habitantes. Clase 4. Este completó el Excel borracho o es un visionario.",
    "Republica Checa": "🇨🇿 República Checa campeón. Nedved se retiró hace 15 años pero el sueño sigue vivo.",
    "Costa de Marfil": "🇨🇮 Los Elefantes campeones del mundo. Drogba estaría orgulloso.",
    "Argelia": "🇩🇿 Argelia. Si gana, este tipo se tatúa la copa en la frente.",
    "Brasil": "🇧🇷 Brasil. Ir con Brasil siendo argentino es como aplaudir un gol en contra.",
    "Francia": "🇫🇷 Francia. Después de Qatar. Memoria selectiva o masoquismo.",
    "España": "🇪🇸 Tiki-taka. Posesión. Y eliminación en cuartos como siempre.",
    "Inglaterra": "🏴 TRAIDOR A LA PATRIA DETECTADO. Las Malvinas son argentinas.",
    "Portugal": "🇵🇹 CR7 con andador. Romántico pero delirante.",
    "Paises Bajos": "🇳🇱 La naranja mecánica: siempre de novias, nunca de novia.",
    "Belgica": "🇧🇪 Generación dorada que se oxida sin ganar nada.",
    "Uruguay": "🇺🇾 Los primos del charco. Garra charrúa con mate y nostalgia.",
    "Colombia": "🇨🇴 James, Díaz y mucha cumbia. ¿Alcanza?",
    "Croacia": "🇭🇷 Modric tiene más mundiales encima que años de vida. Guerreros.",
    "Mexico": "🇲🇽 Algún día van a pasar de octavos. ¿No?",
    "Estados Unidos": "🇺🇸 Esto no es el Super Bowl, amigo.",
    "Japon": "🇯🇵 Si el anime enseñó algo es que Japón siempre gana al final.",
    "Marruecos": "🇲🇦 Los leones del Atlas. ¿Pueden rugir más fuerte?",
    "Escocia": "🏴 Escocia campeón... y yo soy astronauta.",
    "Noruega": "🇳🇴 Haaland solo contra el mundo.",
    "Suiza": "🇨🇭 Neutral en todo, hasta en las apuestas.",
    "Senegal": "🇸🇳 Los Leones de la Teranga. Valiente apuesta.",
    "Canada": "🇨🇦 Esto no es hockey sobre hielo, amigo.",
    "Bosnia": "🇧🇦 Bosnia. Audaz. Inesperado. Tiene huevos.",
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

    if equipos_unicos == 1:
        unico_campeon = list(campeones.keys())[0]
        st.success(f"🐑 UNANIMIDAD TOTAL. Todos pusieron **{unico_campeon}**. ¿Se juntaron a completar el Excel o es telepatía?")
    elif equipos_unicos == total_participantes:
        st.info("🎯 Todos eligieron distinto. Esto va a estar bueno.")
    elif equipos_unicos <= 3:
        st.warning("🐑 Poca originalidad. ¿Se copiaron?")

    for campeon, apostadores in campeones.items():
        if len(apostadores) >= 2 and len(apostadores) < total_participantes:
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
                f"🏆 Campeón: **{campeon}** | ⚽ Goleador: **{goleador}** | "
                f"⭐ Figura: **{figura}**"
            )
            st.markdown(
                f"💡 Revelación: **{revelacion}** | 💀 Decepción: **{decepcion}**"
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
    if len(argentinistas) == total_participantes:
        st.metric("🇦🇷 Patriotas", f"{len(argentinistas)}/{total_participantes}")
        st.caption("TODOS. Unanimidad scaloneta. Así se vota.")
    elif argentinistas:
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
    decepcion = cats.get("Decepción", "")

    # Campeon clase 4
    if campeon in ["Curazao", "Haiti", "Nueva Zelanda", "Qatar", "Irak", "Jordania", "Cabo Verde", "Uzbekistan", "Congo"]:
        verguenzas.append(f"🤯 **{nombre}** puso a **{campeon}** campeón del mundo. Guardamos esto con llave.")

    # Revelacion = Campeon
    if revelacion == campeon and revelacion and "no hay" not in revelacion.lower():
        verguenzas.append(f"🔄 **{nombre}** puso a **{campeon}** como campeón Y revelación. ¿No se contradice un poco?")

    # Sin revelacion
    if "no hay" in revelacion.lower():
        verguenzas.append(f"🤷 **{nombre}** dice que no hay revelación. Tan pesimista que ni apuesta.")

    # Decepcion = equipo fuerte que puso como campeon otro
    if decepcion and campeon and decepcion == campeon:
        verguenzas.append(f"🤔 **{nombre}** puso a **{campeon}** como campeón Y decepción. ¿Relación tóxica?")

# Stats globales vergonzosas
if len(campeones) == 1:
    unico = list(campeones.keys())[0]
    verguenzas.append(f"🐑 **TODOS** pusieron a **{unico}**. Cero originalidad. Si pierde en primera ronda, la vergüenza es colectiva.")

if not verguenzas:
    verguenzas.append("Sorprendentemente, nadie hizo nada vergonzoso. Imposible, revisamos de nuevo.")

for v in verguenzas:
    st.markdown(v)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.markdown(
    f'<p style="text-align:center; color:#666; font-size:0.9rem;">'
    f'⏰ El mundial arranca el <b>11 de junio de 2026</b>. '
    f'Van <b>{total_entregados}</b> Excels entregados. Esperamos entre 25 y 30 participantes.<br>'
    f'Todas las predicciones fueron guardadas. No hay vuelta atrás. 😈</p>',
    unsafe_allow_html=True
)
