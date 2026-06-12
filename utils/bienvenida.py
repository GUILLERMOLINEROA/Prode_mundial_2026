"""
utils/bienvenida.py
Genera comentarios de bienvenida con Gemini, cacheados cada 3 horas.
Dos modos: PREVIA (antes del mundial) y COMPETENCIA (durante el mundial).
"""
import os
import random
import streamlit as st
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

GEMINI_CACHE_TTL = 43200  # 3 horas en segundos


def _get_gemini_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


def _llamar_gemini(prompt):
    """Llama a Gemini y retorna el texto. Retorna '' si falla."""
    key = _get_gemini_key()
    if not key:
        return ""
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return ""


@st.cache_data(ttl=GEMINI_CACHE_TTL)
def generar_bienvenida_previa(
    fecha_str,
    dias_para_mundial,
    total_entregados,
    esperados_min,
    esperados_max,
    participantes_data,
    entregas_data,
    tono_prompt,
    seed_hora,
):
    """
    Genera comentario de bienvenida para modo PREVIA.
    Se cachea cada 3 horas (seed_hora cambia cada 3h para renovar cache).
    """
    # Reconvertir tuplas a dicts (se pasaron como tuplas para ser hashables)
    participantes_list = [dict(p) for p in participantes_data]
    # Seleccionar 2-3 participantes aleatorios para mencionar
    rng = random.Random(seed_hora)
    mencionados = rng.sample(participantes_list, min(3, len(participantes_list)))

    # Construir texto de entregas
    entregas_list = [dict(e) for e in entregas_data] if entregas_data else []
    entregas_txt = ""
    for i, e in enumerate(entregas_list):
        entregas_txt += f"- #{i+1} {e.get('codigo','?')} (entregó {e.get('fecha','?')} a las {e.get('hora','?')})"
        # Buscar campeon en participantes
        for p in participantes_list:
            if p.get('codigo') == e.get('codigo'):
                entregas_txt += f" — Campeón: {p.get('campeon','?')}"
                break
        entregas_txt += "\n"

    menciones_txt = ""
    for p in mencionados:
        menciones_txt += (
            f"- {p['nombre']} ({p['codigo']}): "
            f"Campeón={p.get('campeon','?')}, "
            f"Goleador={p.get('goleador','?')}, "
            f"Revelación={p.get('revelacion','?')}\n"
        )

    # Lista completa de TODOS los participantes (para DELIRIOS)
    todos_txt = ""
    for p in participantes_list:
        todos_txt += (
            f"- {p.get('nombre', p.get('codigo','?'))} ({p.get('codigo','?')}): "
            f"Campeón={p.get('campeon','?')}, "
            f"Goleador={p.get('goleador','?')}, "
            f"Figura={p.get('figura','?')}, "
            f"Revelación={p.get('revelacion','?')}, "
            f"Decepción={p.get('decepcion','?')}\n"
        )

    # Candidatos al muro de la vergüenza
    muro_candidatos_txt = ""
    equipos_falopa = {"Curazao", "Haiti", "Nueva Zelanda", "Qatar", "Irak", "Jordania", "Cabo Verde", "Uzbekistan", "Congo"}

    for p in participantes_list:
        codigo = p.get("codigo", "?")
        campeon = str(p.get("campeon", ""))
        revelacion = str(p.get("revelacion", ""))
        goleador = str(p.get("goleador", ""))
        decepcion = str(p.get("decepcion", ""))

        if campeon in equipos_falopa:
            muro_candidatos_txt += f"- {codigo}: puso a {campeon} campeón del mundo.\\n"

        if revelacion and revelacion.lower() == "no hay revelación":
            muro_candidatos_txt += f"- {codigo}: dice que no hay revelación.\\n"

        if revelacion and campeon and revelacion == campeon and "no hay" not in revelacion.lower():
            muro_candidatos_txt += f"- {codigo}: puso a {campeon} como campeón y revelación.\\n"

        if decepcion and campeon and decepcion == campeon:
            muro_candidatos_txt += f"- {codigo}: puso a {campeon} como campeón y decepción.\\n"

        if goleador and len(goleador) > 1 and any(c.isupper() for c in goleador[1:3]):
            muro_candidatos_txt += f"- {codigo}: escribió raro el goleador ({goleador}).\\n"

    if not muro_candidatos_txt.strip():
        muro_candidatos_txt = "- Nadie hizo una vergüenza particularmente escandalosa todavía.\\n"

    prompt = f"""{tono_prompt}

Contexto actual:
- Fecha: {fecha_str}
- Faltan {dias_para_mundial} días para el partido inaugural del Mundial 2026
- Entregaron {total_entregados} participantes de entre {esperados_min} y {esperados_max} esperados
- Todavía estamos en la previa, no hay partidos jugados

Participantes para mencionar (elegí 2 o 3 y hacé comentarios sobre sus apuestas):
{menciones_txt}

Orden de entrega (quién entregó primero y quién último):
{entregas_txt}

Generá CINCO textos separados por la línea "---":

1. BIENVENIDA: Un párrafo LARGO y jugoso de bienvenida (MÍNIMO 4-5 oraciones, puede ser más) que hable de cuánto falta para el mundial, cuántos entregaron, tire cargadas a los participantes mencionados, se burle de sus apuestas, y genere hype. Este texto tiene que ser el más largo y completo de todos. NO lo hagas corto.

2. FOOTER: Una oración corta y picante sobre los que todavía no entregaron el Excel (faltan {max(esperados_min - total_entregados, 0)} a {max(esperados_max - total_entregados, 0)}).

3. VEREDICTOS: Un comentario corto y picante (1 oración) para CADA participante que entregó, basándote en su orden de entrega, su campeón y sus apuestas. Formato exacto:
CODIGO: comentario

4. DELIRIOS: Un comentario cortito y jugoso (1-2 oraciones) para CADA UNO de los siguientes participantes sobre sus apuestas. No repitas lo del veredicto, acá concentrate en burlarte de sus elecciones futbolísticas.

Lista COMPLETA de participantes y sus apuestas (generá un delirio para CADA UNO, no te saltees ninguno):
{todos_txt}

Formato exacto:
CODIGO: comentario

5. MURO: Reescribí los siguientes candidatos del “Muro de la Vergüenza” con más picante, humor y veneno amistoso, respetando el tono del grupo. Una línea por candidato. Formato exacto:
- comentario

Candidatos:
{muro_candidatos_txt}
"""

    texto = _llamar_gemini(prompt)
    if not texto:
        return _fallback_previa(dias_para_mundial, total_entregados, esperados_min, esperados_max)

    # Separar bienvenida, footer, veredictos, delirios y muro
    partes = texto.split("---")
    bienvenida = partes[0].strip() if len(partes) >= 1 else ""
    footer = partes[1].strip() if len(partes) >= 2 else ""
    veredictos_raw = partes[2].strip() if len(partes) >= 3 else ""
    delirios_raw = partes[3].strip() if len(partes) >= 4 else ""
    muro_raw = partes[4].strip() if len(partes) >= 5 else ""

    # Limpiar etiquetas
    for tag in ["BIENVENIDA:", "1.", "2.", "3.", "FOOTER:", "VEREDICTOS:", "1)", "2)", "3)"]:
        bienvenida = bienvenida.replace(tag, "").strip()
        footer = footer.replace(tag, "").strip()

    # Parsear veredictos
    veredictos = {}
    for linea in veredictos_raw.split("\n"):
        linea = linea.strip()
        if ":" in linea and len(linea) > 3:
            cod, com = linea.split(":", 1)
            cod = cod.strip().upper()
            # Limpiar numeración si quedó
            for tag in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "- "]:
                cod = cod.replace(tag, "").strip()
            if cod and com.strip():
                veredictos[cod] = com.strip()

    # Parsear delirios
    delirios = {}
    for linea in delirios_raw.split("\n"):
        linea = linea.strip()
        if ":" in linea and len(linea) > 3:
            cod, com = linea.split(":", 1)
            cod = cod.strip().upper()
            for tag in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "- ", "4."]:
                cod = cod.replace(tag, "").strip()
            if cod and com.strip():
                delirios[cod] = com.strip()

    # Parsear muro
    muro = []
    for linea in muro_raw.split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("- "):
            linea = linea[2:].strip()
        muro.append(linea)

    return {"bienvenida": bienvenida, "footer": footer, "veredictos": veredictos, "delirios": delirios, "muro": muro}


@st.cache_data(ttl=GEMINI_CACHE_TTL)
def generar_bienvenida_competencia(
    fecha_str,
    ultimos_resultados,
    partidos_en_vivo,
    proximos_partidos,
    top3_texto,
    ultimo_texto,
    lider_actual,
    participantes_random_texto,
    tono_prompt,
    seed_hora,
):
    """
    Genera comentario de bienvenida para modo COMPETENCIA (mundial en curso).
    Devuelve:
    - bienvenida (texto largo de análisis)
    - mensajes_dia (dict CODIGO -> comentario)
    - analisis_generado_a (timestamp textual)
    """
    prompt = f"""{tono_prompt}

Contexto del Mundial 2026 en vivo:
- Momento del análisis: {fecha_str}

Partidos en vivo ahora:
{partidos_en_vivo}

Últimos resultados:
{ultimos_resultados}

Próximos partidos:
{proximos_partidos}

Tabla actual del PRODE:
{top3_texto}
Último actual: {ultimo_texto}
Líder actual al momento del análisis: {lider_actual}

Participantes a destacar:
{participantes_random_texto}

Generá DOS bloques separados por la línea "---":

1. INTRO:
Un análisis jugoso de 4 a 6 oraciones que:
- diga explícitamente que es “al momento del análisis”
- mencione si hay uno o varios partidos en vivo
- si hay partidos en vivo, diga en qué estado estaban (1H, HT, 2H, etc.) y con qué marcador
- diga quién iba liderando el PRODE con esos datos
- mencione cómo impactaron los últimos resultados
- anticipe lo que viene
- mantenga el tono del grupo

2. MENSAJES_DIA:
Un comentario corto y picante para varios participantes importantes.
Incluí al menos:
- líder
- segundo
- tercero
- último
- y 1 o 2 participantes extra si querés

Formato exacto:
CODIGO: comentario
CODIGO: comentario
"""

    texto = _llamar_gemini(prompt)
    if not texto:
        return {
            "bienvenida": "⚽ El mundial ya está en marcha. Mirá cómo se están moviendo las posiciones del PRODE con los resultados y partidos en vivo disponibles al momento del análisis.",
            "mensajes_dia": {},
            "analisis_generado_a": fecha_str,
        }

    partes = texto.split("---")
    bienvenida = partes[0].strip() if len(partes) >= 1 else ""
    mensajes_raw = partes[1].strip() if len(partes) >= 2 else ""

    for tag in ["INTRO:", "MENSAJES_DIA:", "1.", "2.", "1)", "2)"]:
        bienvenida = bienvenida.replace(tag, "").strip()

    mensajes_dia = {}
    for linea in mensajes_raw.split("\n"):
        linea = linea.strip()
        if ":" in linea and len(linea) > 3:
            cod, com = linea.split(":", 1)
            cod = cod.strip().upper()
            for tag in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "- "]:
                cod = cod.replace(tag, "").strip()
            if cod and com.strip():
                mensajes_dia[cod] = com.strip()

    return {
        "bienvenida": bienvenida,
        "mensajes_dia": mensajes_dia,
        "analisis_generado_a": fecha_str,
    }


def _fallback_previa(dias, entregados, esp_min, esp_max):
    """Comentario de fallback si Gemini no está disponible."""
    faltan = max(esp_min - entregados, 0)
    return {
        "veredictos": {},
        "delirios": {},
        "muro": [],
        "bienvenida": f"⏰ Faltan {dias} días para el Mundial 2026. Ya entregaron {entregados} valientes. ¿El resto? Seguramente todavía están googleando quién juega en el grupo de la muerte.",
        "footer": f"⏳ Esperamos entre {esp_min} y {esp_max} participantes. Faltan {faltan}+ vagos por entregar.",
    }


def obtener_bienvenida(categorias_todos=None, leaderboard=None, resultados=None):
    """
    Función principal. Detecta modo (previa/competencia) y genera el texto.
    """
    from utils.group_config import group_config

    config = group_config()
    tono = config.get("prompt_gemini", "Sarcástico y futbolero argentino. Máximo 3 oraciones.")
    esp_min = config.get("participantes_esperados_min", 20)
    esp_max = config.get("participantes_esperados_max", 30)

    ahora = datetime.now(timezone.utc)
    ahora_art = ahora.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    seed_hora = ahora.hour // 3

    # Clave interna para el cache de Gemini
    fecha_cache = ahora.strftime("%d/%m/%Y") + f" (bloque {seed_hora})"

    # Texto lindo para mostrar en la app
    fecha_visible = ahora_art.strftime("%d/%m/%Y %H:%M ART")

    fecha_inaugural = datetime(2026, 6, 11, tzinfo=timezone.utc)
    dias_para_mundial = (fecha_inaugural - ahora).days

    # Detectar modo
    hay_resultados_reales = False
    hay_partidos_en_vivo = False
    if resultados is not None and not resultados.empty:
        from utils.api_football import ESTADOS_FINALIZADO, ESTADOS_EN_VIVO
        if hasattr(resultados, "estado"):
            hay_resultados_reales = resultados["estado"].isin(ESTADOS_FINALIZADO).any()
            hay_partidos_en_vivo = resultados["estado"].isin(ESTADOS_EN_VIVO).any()

    usar_simulacion = st.session_state.get("usar_simulacion", False)

    if (hay_resultados_reales or hay_partidos_en_vivo) and not usar_simulacion:
        # MODO COMPETENCIA
        from utils.api_football import obtener_ultimos_resultados, obtener_proximos_partidos, estado_display

        ultimos = obtener_ultimos_resultados(resultados, 3)
        ultimos_txt = ""
        if not ultimos.empty:
            for _, p in ultimos.iterrows():
                ultimos_txt += f"- {p['equipo_local']} {int(p['goles_local'])}-{int(p['goles_visitante'])} {p['equipo_visitante']}\n"

        vivos_txt = ""
        if resultados is not None and not resultados.empty:
            from utils.api_football import ESTADOS_EN_VIVO
            en_vivo = resultados[resultados["estado"].isin(ESTADOS_EN_VIVO)].copy()
            if not en_vivo.empty:
                for _, p in en_vivo.head(3).iterrows():
                    estado = str(p.get("estado", "") or "").strip()
                    minuto = p.get("minuto")
                    _, texto_estado = estado_display(estado)
                    estado_txt = texto_estado
                    if minuto is not None and pd.notna(minuto) and estado != "HT":
                        estado_txt += f" · {int(minuto)}'"
                    gl = int(p["goles_local"]) if pd.notna(p.get("goles_local")) else 0
                    gv = int(p["goles_visitante"]) if pd.notna(p.get("goles_visitante")) else 0
                    vivos_txt += f"- {p['equipo_local']} {gl}-{gv} {p['equipo_visitante']} ({estado_txt})\n"

        proximos = obtener_proximos_partidos(resultados, 3)
        proximos_txt = ""
        if proximos is not None and not proximos.empty:
            for _, p in proximos.iterrows():
                try:
                    ftxt = p["fecha"].strftime("%d/%m %H:%M")
                except Exception:
                    ftxt = str(p.get("fecha", ""))
                proximos_txt += f"- {p['equipo_local']} vs {p['equipo_visitante']} ({ftxt})\n"

        top3_txt = ""
        ultimo_txt = ""
        lider_actual = ""
        participantes_random_txt = ""

        if leaderboard is not None and not leaderboard.empty:
            for _, row in leaderboard.head(3).iterrows():
                top3_txt += f"- #{int(row['Posición'])} {row['Participante']}: {int(row['Total'])} pts\n"

            lider_row = leaderboard.iloc[0]
            lider_actual = f"{lider_row['Participante']} con {int(lider_row['Total'])} pts"

            ultimo_row = leaderboard.iloc[-1]
            ultimo_txt = f"{ultimo_row['Participante']} con {int(ultimo_row['Total'])} pts"

            rng = random.Random(seed_hora)
            todos = leaderboard["Participante"].tolist()
            mencionados = rng.sample(todos, min(4, len(todos)))
            for nombre in mencionados:
                row = leaderboard[leaderboard["Participante"] == nombre].iloc[0]
                participantes_random_txt += f"- {nombre}: #{int(row['Posición'])} con {int(row['Total'])} pts\n"

        resultado_comp = generar_bienvenida_competencia(
            fecha_cache,
            ultimos_txt,
            vivos_txt,
            proximos_txt,
            top3_txt,
            ultimo_txt,
            lider_actual,
            participantes_random_txt,
            tono,
            seed_hora,
        )
        if isinstance(resultado_comp, dict):
            resultado_comp["analisis_generado_a"] = fecha_visible
        return resultado_comp

    else:
        # MODO PREVIA
        participantes_data = []
        if categorias_todos:
            for codigo, cats in categorias_todos.items():
                participantes_data.append({
                    "codigo": codigo,
                    "nombre": codigo,
                    "campeon": cats.get("Campeon", "?"),
                    "goleador": cats.get("Goleador", "?"),
                    "figura": cats.get("Figura", "?"),
                    "revelacion": cats.get("Revelación", "?"),
                    "decepcion": cats.get("Decepción", "?"),
                })

        if not participantes_data:
            return _fallback_previa(dias_para_mundial, 0, esp_min, esp_max)

        # Preparar datos de entregas
        entregas_info = []
        try:
            import pandas as pd
            from utils.group_config import entregas_path
            edf = pd.read_csv(entregas_path())
            edf.columns = edf.columns.str.strip()
            for _, row in edf.iterrows():
                entregas_info.append({
                    "codigo": str(row["codigo"]).strip(),
                    "fecha": str(row["fecha"]).strip(),
                    "hora": str(row["hora"]).strip(),
                })
        except Exception:
            pass

        return generar_bienvenida_previa(
            fecha_cache, dias_para_mundial, len(participantes_data),
            esp_min, esp_max, tuple(tuple(sorted(p.items())) for p in participantes_data),
            tuple(tuple(sorted(e.items())) for e in entregas_info),
            tono, seed_hora,
        )

