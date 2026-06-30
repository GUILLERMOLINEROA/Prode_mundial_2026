"""
Resolución de la zona horaria del usuario para mostrar UNA sola hora localizada
en las tarjetas de partidos.

Estrategia (degradación segura, sin dependencias nuevas):
  1. Manual: si el usuario eligió una zona en el selector, esa MANDA.
  2. Detección: `st.context.timezone` (nativo de Streamlit, lee el IANA del
     navegador). Se valida con `ZoneInfo` antes de aceptarla.
  3. Fallback: Argentina (`America/Argentina/Buenos_Aires`).

La zona se recuerda en `st.session_state`. Nada acá lanza excepción: si algo
falla, cae al default y sigue.
"""
import streamlit as st
from zoneinfo import ZoneInfo

TZ_DEFAULT = "America/Argentina/Buenos_Aires"

# Zonas frecuentes para el selector: (etiqueta visible, IANA).
ZONAS_COMUNES = [
    ("Argentina (Buenos Aires)", "America/Argentina/Buenos_Aires"),
    ("Brasil (São Paulo)", "America/Sao_Paulo"),
    ("México (Ciudad de México)", "America/Mexico_City"),
    ("Uruguay (Montevideo)", "America/Montevideo"),
    ("Chile (Santiago)", "America/Santiago"),
    ("Colombia / Perú (Bogotá)", "America/Bogota"),
    ("EE.UU. Este (Nueva York)", "America/New_York"),
    ("EE.UU. Pacífico (Los Ángeles)", "America/Los_Angeles"),
    ("España (Madrid)", "Europe/Madrid"),
    ("Reino Unido (Londres)", "Europe/London"),
    ("UTC", "UTC"),
]


def ciudad_label(iana):
    """Nombre presentable de la zona: último segmento del IANA, '_' -> ' '."""
    if not iana:
        return ""
    return str(iana).split("/")[-1].replace("_", " ")


def _es_zona_valida(nombre):
    if not nombre:
        return False
    try:
        ZoneInfo(str(nombre))
        return True
    except Exception:
        return False


def resolver_timezone():
    """
    Devuelve el IANA de la zona activa (manual > detección > Argentina).
    Actualiza `tz_usuario` y `tz_deteccion_fallo` en session_state. No lanza.
    """
    manual = st.session_state.get("tz_usuario_manual")
    if _es_zona_valida(manual):
        st.session_state["tz_deteccion_fallo"] = False
        st.session_state["tz_usuario"] = manual
        return manual

    try:
        detectada = st.context.timezone
    except Exception:
        detectada = None

    if _es_zona_valida(detectada):
        st.session_state["tz_deteccion_fallo"] = False
        st.session_state["tz_usuario"] = detectada
        return detectada

    st.session_state["tz_deteccion_fallo"] = True
    st.session_state["tz_usuario"] = TZ_DEFAULT
    return TZ_DEFAULT


def _opciones_con(actual):
    """Lista de (etiqueta, IANA) garantizando que `actual` esté presente."""
    ops = list(ZONAS_COMUNES)
    if actual not in [iana for _, iana in ops]:
        ops = [(f"{ciudad_label(actual)} (detectada)", actual)] + ops
    return ops


def _marcar_tz_manual():
    st.session_state["tz_usuario_manual"] = st.session_state.get("tz_selectbox")


def selector_timezone():
    """
    Renderiza el selector de zona horaria (pensado para el sidebar) y devuelve
    el IANA activo. Si el usuario elige a mano, eso pasa a mandar sobre la
    detección. Pensado para llamarse dentro de `st.sidebar`.
    """
    actual = resolver_timezone()
    fallo = st.session_state.get("tz_deteccion_fallo", False)

    opciones = _opciones_con(actual)
    valores = [iana for _, iana in opciones]
    etiquetas = {iana: lbl for lbl, iana in opciones}

    # Widget controlado: fijamos el valor ANTES de instanciar el selectbox, así
    # sigue a la detección mientras el usuario no elija a mano (on_change marca
    # la elección manual en otra key, que luego gana en resolver_timezone()).
    st.session_state["tz_selectbox"] = actual

    if fallo:
        st.caption("⚠️ No detectamos tu zona horaria; mostrando hora de Argentina. Elegí la tuya 👇")
    else:
        st.caption("🕒 Hora de los partidos en tu zona")

    st.selectbox(
        "Zona horaria de los partidos",
        options=valores,
        format_func=lambda iana: etiquetas.get(iana, ciudad_label(iana)),
        key="tz_selectbox",
        on_change=_marcar_tz_manual,
        label_visibility="collapsed",
    )

    return resolver_timezone()
