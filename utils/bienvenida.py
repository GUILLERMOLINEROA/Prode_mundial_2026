"""
utils/bienvenida.py
Genera comentarios de bienvenida con Gemini, cacheados cada 3 horas.
Dos modos: PREVIA (antes del mundial) y COMPETENCIA (durante el mundial).
"""
import os
import random
import streamlit as st
from datetime import datetime, timezone

GEMINI_CACHE_TTL = 10800  # 3 horas en segundos


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

    menciones_txt = ""
    for p in mencionados:
        menciones_txt += (
            f"- {p['nombre']} ({p['codigo']}): "
            f"Campeón={p.get('campeon','?')}, "
            f"Goleador={p.get('goleador','?')}, "
            f"Revelación={p.get('revelacion','?')}\n"
        )

    prompt = f"""{tono_prompt}

Contexto actual:
- Fecha: {fecha_str}
- Faltan {dias_para_mundial} días para el partido inaugural del Mundial 2026
- Entregaron {total_entregados} participantes de entre {esperados_min} y {esperados_max} esperados
- Todavía estamos en la previa, no hay partidos jugados

Participantes para mencionar (elegí 2 o 3 y hacé comentarios sobre sus apuestas):
{menciones_txt}

Generá DOS textos separados por la línea "---":

1. BIENVENIDA: Un párrafo de bienvenida (3-4 oraciones) que hable de cuánto falta, cuántos entregaron, y tire cargadas a los participantes mencionados.

2. FOOTER: Una oración corta y picante sobre los que todavía no entregaron el Excel (faltan {max(esperados_min - total_entregados, 0)} a {max(esperados_max - total_entregados, 0)}).
"""

    texto = _llamar_gemini(prompt)
    if not texto:
        return _fallback_previa(dias_para_mundial, total_entregados, esperados_min, esperados_max)

    # Separar bienvenida y footer
    partes = texto.split("---")
    bienvenida = partes[0].strip() if len(partes) >= 1 else ""
    footer = partes[1].strip() if len(partes) >= 2 else ""

    # Limpiar etiquetas
    for tag in ["BIENVENIDA:", "1.", "2.", "FOOTER:", "1)", "2)"]:
        bienvenida = bienvenida.replace(tag, "").strip()
        footer = footer.replace(tag, "").strip()

    return {"bienvenida": bienvenida, "footer": footer}


@st.cache_data(ttl=GEMINI_CACHE_TTL)
def generar_bienvenida_competencia(
    fecha_str,
    ultimos_resultados,
    proximos_partidos,
    top3_texto,
    ultimo_texto,
    participantes_random_texto,
    tono_prompt,
    seed_hora,
):
    """
    Genera comentario de bienvenida para modo COMPETENCIA (mundial en curso).
    Se cachea cada 3 horas.
    """
    prompt = f"""{tono_prompt}

Contexto del Mundial 2026 en vivo:
- Fecha: {fecha_str}

Últimos resultados:
{ultimos_resultados}

Tabla de posiciones del PRODE:
{top3_texto}
Último: {ultimo_texto}

Participantes para mencionar:
{participantes_random_texto}

Generá UN párrafo de bienvenida (4-5 oraciones) que:
- Comente los últimos resultados y cómo impactaron en el PRODE
- Tire cargadas a los participantes mencionados según cómo les va
- Mencione al líder y al último con tono picante
- Anticipe lo que viene
"""

    texto = _llamar_gemini(prompt)
    if not texto:
        return {"bienvenida": "⚽ El mundial está en vivo. Mirá cómo van las posiciones."}

    return {"bienvenida": texto.strip()}


def _fallback_previa(dias, entregados, esp_min, esp_max):
    """Comentario de fallback si Gemini no está disponible."""
    faltan = max(esp_min - entregados, 0)
    return {
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
    fecha_str = ahora.strftime("%d/%m/%Y %H:%M UTC")
    seed_hora = ahora.hour // 3  # Cambia cada 3 horas

    fecha_inaugural = datetime(2026, 6, 11, tzinfo=timezone.utc)
    dias_para_mundial = (fecha_inaugural - ahora).days

    # Detectar modo
    hay_resultados_reales = False
    if resultados is not None and not resultados.empty:
        from utils.api_football import ESTADOS_FINALIZADO
        if hasattr(resultados, "estado"):
            hay_resultados_reales = resultados["estado"].isin(ESTADOS_FINALIZADO).any()

    usar_simulacion = st.session_state.get("usar_simulacion", True)

    if hay_resultados_reales and not usar_simulacion:
        # MODO COMPETENCIA
        from utils.api_football import obtener_ultimos_resultados
        ultimos = obtener_ultimos_resultados(resultados, 3)
        ultimos_txt = ""
        if not ultimos.empty:
            for _, p in ultimos.iterrows():
                ultimos_txt += f"- {p['equipo_local']} {int(p['goles_local'])}-{int(p['goles_visitante'])} {p['equipo_visitante']}\n"

        top3_txt = ""
        ultimo_txt = ""
        participantes_random_txt = ""

        if leaderboard is not None and not leaderboard.empty:
            for _, row in leaderboard.head(3).iterrows():
                top3_txt += f"- #{int(row['Posición'])} {row['Participante']}: {int(row['Total'])} pts\n"
            ultimo_row = leaderboard.iloc[-1]
            ultimo_txt = f"{ultimo_row['Participante']} con {int(ultimo_row['Total'])} pts"

            # 2-3 aleatorios
            rng = random.Random(seed_hora)
            todos = leaderboard["Participante"].tolist()
            mencionados = rng.sample(todos, min(3, len(todos)))
            for nombre in mencionados:
                row = leaderboard[leaderboard["Participante"] == nombre].iloc[0]
                participantes_random_txt += f"- {nombre}: #{int(row['Posición'])} con {int(row['Total'])} pts\n"

        return generar_bienvenida_competencia(
            fecha_str, ultimos_txt, "", top3_txt, ultimo_txt,
            participantes_random_txt, tono, seed_hora,
        )

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
                    "revelacion": cats.get("Revelación", "?"),
                })

        if not participantes_data:
            return _fallback_previa(dias_para_mundial, 0, esp_min, esp_max)

        return generar_bienvenida_previa(
            fecha_str, dias_para_mundial, len(participantes_data),
            esp_min, esp_max, tuple(tuple(sorted(p.items())) for p in participantes_data),
            tono, seed_hora,
        )

