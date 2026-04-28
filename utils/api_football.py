# =============================================================================
# utils/api_football.py
# Módulo encargado de conectarse a la API de api-sports.io para obtener
# resultados reales del Mundial 2026.
#
# IMPORTANTE: Necesitas una API key gratuita de https://www.api-football.com/
# El plan gratuito permite 100 requests/día, suficiente para nuestro PRODE.
# =============================================================================

import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


# --- Constantes de la API ---
API_BASE_URL = "https://v3.football.api-sports.io"
# El ID de la Copa del Mundo 2026 en api-sports (puede cambiar, verificar)
# Por ahora usamos un placeholder; se actualizará cuando la API lo publique.
WORLD_CUP_2026_ID = 1  # TODO: Actualizar con el ID real del Mundial 2026
WORLD_CUP_2026_SEASON = 2026


def _get_headers() -> dict:
    """
    Retorna los headers necesarios para autenticarse con la API.
    La API key se lee desde los secrets de Streamlit (archivo .streamlit/secrets.toml)
    o desde una variable de entorno.
    
    Para configurar secrets en Streamlit, crear el archivo:
    .streamlit/secrets.toml con el contenido:
    API_FOOTBALL_KEY = "tu_clave_aqui"
    """
    api_key = st.secrets.get("API_FOOTBALL_KEY", "")
    if not api_key:
        st.warning(
            "⚠️ No se encontró la API key de football. "
            "Configúrala en `.streamlit/secrets.toml` como: "
            '`API_FOOTBALL_KEY = "tu_clave"`'
        )
    return {
        "x-apisports-key": api_key
    }


@st.cache_data(ttl=600)  # Cache de 10 minutos para no gastar requests
def obtener_partidos_mundial() -> pd.DataFrame:
    """
    Obtiene TODOS los partidos del Mundial 2026 desde la API.
    Retorna un DataFrame con columnas estandarizadas.
    
    Columnas del DataFrame resultante:
    - match_id: ID único del partido
    - fecha: Fecha y hora del partido
    - ronda: Fase del torneo (Group A, Round of 32, etc.)
    - equipo_local: Nombre del equipo local
    - equipo_visitante: Nombre del equipo visitante
    - goles_local: Goles del equipo local (None si no se jugó)
    - goles_visitante: Goles del equipo visitante (None si no se jugó)
    - penales_local: Goles en penales local (None si no hubo penales)
    - penales_visitante: Goles en penales visitante (None si no hubo penales)
    - estado: Estado del partido (NS=No Started, FT=Full Time, etc.)
    """
    url = f"{API_BASE_URL}/fixtures"
    params = {
        "league": WORLD_CUP_2026_ID,
        "season": WORLD_CUP_2026_SEASON,
    }
    
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("errors"):
            st.error(f"Error de API: {data['errors']}")
            return pd.DataFrame()
        
        partidos = []
        for fixture in data.get("response", []):
            partido = {
                "match_id": fixture["fixture"]["id"],
                "fecha": fixture["fixture"]["date"],
                "ronda": fixture["league"]["round"],
                "equipo_local": fixture["teams"]["home"]["name"],
                "equipo_visitante": fixture["teams"]["away"]["name"],
                "goles_local": fixture["goals"]["home"],
                "goles_visitante": fixture["goals"]["away"],
                "penales_local": fixture["score"]["penalty"]["home"],
                "penales_visitante": fixture["score"]["penalty"]["away"],
                "estado": fixture["fixture"]["status"]["short"],
                # Resultado en tiempo regular (sin penales, para puntaje)
                "goles_local_ft": fixture["score"]["fulltime"]["home"],
                "goles_visitante_ft": fixture["score"]["fulltime"]["away"],
            }
            partidos.append(partido)
        
        df = pd.DataFrame(partidos)
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df = df.sort_values("fecha").reset_index(drop=True)
        
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error conectando con la API de fútbol: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache de 1 hora
def obtener_goleadores_mundial() -> pd.DataFrame:
    """
    Obtiene la tabla de goleadores del Mundial 2026.
    Retorna un DataFrame con jugador, equipo y goles.
    """
    url = f"{API_BASE_URL}/players/topscorers"
    params = {
        "league": WORLD_CUP_2026_ID,
        "season": WORLD_CUP_2026_SEASON,
    }
    
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        goleadores = []
        for item in data.get("response", []):
            goleador = {
                "jugador": item["player"]["name"],
                "equipo": item["statistics"][0]["team"]["name"],
                "goles": item["statistics"][0]["goals"]["total"] or 0,
                "asistencias": item["statistics"][0]["goals"]["assists"] or 0,
            }
            goleadores.append(goleador)
        
        return pd.DataFrame(goleadores)
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error obteniendo goleadores: {e}")
        return pd.DataFrame()


def mapear_nombre_equipo(nombre_api: str) -> str:
    """
    Mapea nombres de equipos de la API a los nombres usados en el Excel del PRODE.
    Esto es CRÍTICO porque la API puede usar 'Netherlands' pero el Excel dice 
    'Paises Bajos', o la API dice 'South Korea' y el Excel 'Corea del Sur'.
    
    IMPORTANTE: Este diccionario DEBE ser revisado y completado cuando la API
    publique los datos reales del Mundial 2026.
    """
    mapeo = {
        # Nombre API -> Nombre Excel
        "Netherlands": "Paises Bajos",
        "South Korea": "Corea del Sur",
        "Korea Republic": "Corea del Sur",
        "USA": "Estados Unidos",
        "United States": "Estados Unidos",
        "Ivory Coast": "Costa de Marfil",
        "Cote D'Ivoire": "Costa de Marfil",
        "Czech Republic": "Republica Checa",
        "Czechia": "Republica Checa",
        "Saudi Arabia": "Arabia Saudita",
        "New Zealand": "Nueva Zelanda",
        "Cape Verde": "Cabo Verde",
        "DR Congo": "Congo",
        "Congo DR": "Congo",
        "South Africa": "Sudafrica",
        "Morocco": "Marruecos",
        "Germany": "Alemania",
        "England": "Inglaterra",
        "France": "Francia",
        "Spain": "España",
        "Brazil": "Brasil",
        "Japan": "Japon",
        "Switzerland": "Suiza",
        "Turkey": "Turquia",
        "Norway": "Noruega",
        "Sweden": "Suecia",
        "Scotland": "Escocia",
        "Tunisia": "Tunez",
        "Egypt": "Egipto",
        "Bosnia and Herzegovina": "Bosnia",
        "Bosnia And Herzegovina": "Bosnia",
        "Jordan": "Jordania",
        "Iraq": "Irak",
        "Iran": "Iran",
        "Algeria": "Argelia",
        "Austria": "Austria",
        "Australia": "Australia",
        "Belgium": "Belgica",
        "Croatia": "Croacia",
        "Colombia": "Colombia",
        "Canada": "Canada",
        "Panama": "Panama",
        "Paraguay": "Paraguay",
        "Qatar": "Qatar",
        "Uzbekistan": "Uzbekistan",
        "Curacao": "Curazao",
        "Haiti": "Haiti",
    }
    return mapeo.get(nombre_api, nombre_api)


def clasificar_ronda(ronda_api: str) -> str:
    """
    Convierte el nombre de la ronda de la API al formato interno del PRODE.
    
    Ejemplos de lo que la API puede devolver:
    - "Group A", "Group B", ... -> "grupos"
    - "Round of 32" -> "16vos"
    - "Round of 16" -> "8vos"
    - "Quarter-finals" -> "4tos"
    - "Semi-finals" -> "semis"
    - "3rd Place" -> "3ero"
    - "Final" -> "final"
    """
    ronda = ronda_api.lower()
    if "group" in ronda:
        return "grupos"
    elif "32" in ronda:
        return "16vos"
    elif "16" in ronda:
        return "8vos"
    elif "quarter" in ronda:
        return "4tos"
    elif "semi" in ronda:
        return "semis"
    elif "3rd" in ronda or "third" in ronda:
        return "3ero"
    elif "final" in ronda:
        return "final"
    else:
        return ronda
