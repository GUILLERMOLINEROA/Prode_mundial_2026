import requests
import streamlit as st
import pandas as pd

API_BASE_URL = "https://v3.football.api-sports.io"
WORLD_CUP_2026_ID = 1
WORLD_CUP_2026_SEASON = 2026

def _get_headers():
    """Retorna headers para la API. No explota si no hay key."""
    try:
        api_key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        api_key = ""
    return {"x-apisports-key": api_key}

def _hay_api_key():
    """Verifica si hay una API key configurada."""
    try:
        api_key = st.secrets.get("API_FOOTBALL_KEY", "")
        return bool(api_key)
    except Exception:
        return False

# =============================================================================
# ESTADOS DE PARTIDO — MAPEO VISUAL
# =============================================================================
ESTADO_DISPLAY = {
    "NS": ("📅", "Programado"),
    "1H": ("🔴", "1er Tiempo"),
    "HT": ("⏸️", "Entretiempo"),
    "2H": ("🔴", "2do Tiempo"),
    "ET": ("🔴", "Tiempo Extra"),
    "BT": ("⏸️", "Break"),
    "P": ("🔴", "Penales"),
    "FT": ("✅", "Finalizado"),
    "AET": ("✅", "Final (prórroga)"),
    "PEN": ("✅", "Final (penales)"),
    "SUSP": ("⚠️", "Suspendido"),
    "INT": ("⚠️", "Interrumpido"),
    "PST": ("📋", "Postergado"),
    "CANC": ("❌", "Cancelado"),
    "ABD": ("❌", "Abandonado"),
    "AWD": ("⚖️", "Ganador asignado"),
    "WO": ("⚖️", "Walkover"),
    "LIVE": ("🔴", "En Vivo"),
}

ESTADOS_EN_VIVO = {"1H", "2H", "HT", "ET", "BT", "P", "LIVE"}
ESTADOS_FINALIZADO = {"FT", "AET", "PEN"}

def estado_display(codigo):
    """Devuelve (emoji, texto) para un código de estado."""
    return ESTADO_DISPLAY.get(codigo, ("❓", codigo))

def hay_partidos_en_vivo(resultados):
    """Verifica si hay partidos en curso en un DataFrame de resultados."""
    if resultados.empty:
        return False
    return resultados["estado"].isin(ESTADOS_EN_VIVO).any()

# =============================================================================
# PARTIDOS (Fixtures) — Cache 1 minuto
# =============================================================================
@st.cache_data(ttl=60)
def obtener_partidos_mundial():
    """
    Obtiene todos los partidos del Mundial 2026 desde la API.
    Cache de 1 minuto para actualizaciones en vivo.
    Con plan Pro (7500 req/dia) esto usa ~4320 req/dia (58%) en el peor caso.
    """
    if not _hay_api_key():
        return pd.DataFrame()
    url = f"{API_BASE_URL}/fixtures"
    params = {"league": WORLD_CUP_2026_ID, "season": WORLD_CUP_2026_SEASON}
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            return pd.DataFrame()
        partidos = []
        for fixture in data.get("response", []):
            partidos.append({
                "match_id": fixture["fixture"]["id"],
                "fecha": fixture["fixture"]["date"],
                "ronda": fixture["league"]["round"],
                "equipo_local": fixture["teams"]["home"]["name"],
                "equipo_visitante": fixture["teams"]["away"]["name"],
                "goles_local": fixture["goals"]["home"],
                "goles_visitante": fixture["goals"]["away"],
                "goles_local_ft": fixture["score"]["fulltime"]["home"],
                "goles_visitante_ft": fixture["score"]["fulltime"]["away"],
                "goles_local_et": fixture["score"]["extratime"]["home"],
                "goles_visitante_et": fixture["score"]["extratime"]["away"],
                "penales_local": fixture["score"]["penalty"]["home"],
                "penales_visitante": fixture["score"]["penalty"]["away"],
                "estado": fixture["fixture"]["status"]["short"],
                "minuto": fixture["fixture"]["status"].get("elapsed"),
            })
        df = pd.DataFrame(partidos)
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df = df.sort_values("fecha").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error obteniendo partidos: {e}")
        return pd.DataFrame()

# =============================================================================
# STANDINGS — Cache 1 minuto
# =============================================================================
@st.cache_data(ttl=60)
def obtener_standings_mundial():
    """
    Obtiene las tablas de posiciones OFICIALES de cada grupo.
    La FIFA resuelve empates y la API refleja la decision oficial.
    """
    if not _hay_api_key():
        return {}
    url = f"{API_BASE_URL}/standings"
    params = {"league": WORLD_CUP_2026_ID, "season": WORLD_CUP_2026_SEASON}
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            return {}
        standings = {}
        for league_data in data.get("response", []):
            for grupo in league_data.get("league", {}).get("standings", []):
                if not grupo:
                    continue
                grupo_nombre = grupo[0].get("group", "Unknown")
                equipos_grupo = []
                for equipo in grupo:
                    equipos_grupo.append({
                        "rank": equipo.get("rank", 0),
                        "equipo": equipo.get("team", {}).get("name", ""),
                        "equipo_id": equipo.get("team", {}).get("id", 0),
                        "puntos": equipo.get("points", 0),
                        "jugados": equipo.get("all", {}).get("played", 0),
                        "ganados": equipo.get("all", {}).get("win", 0),
                        "empatados": equipo.get("all", {}).get("draw", 0),
                        "perdidos": equipo.get("all", {}).get("lose", 0),
                        "goles_favor": equipo.get("all", {}).get("goals", {}).get("for", 0),
                        "goles_contra": equipo.get("all", {}).get("goals", {}).get("against", 0),
                        "diferencia": equipo.get("goalsDiff", 0),
                        "forma": equipo.get("form", ""),
                        "status": equipo.get("status", ""),
                        "descripcion": equipo.get("description", ""),
                    })
                standings[grupo_nombre] = sorted(equipos_grupo, key=lambda x: x["rank"])
        return standings
    except Exception as e:
        st.error(f"Error obteniendo standings: {e}")
        return {}

@st.cache_data(ttl=60)
def obtener_clasificados_por_grupo():
    """
    A partir de los standings oficiales, retorna quienes clasificaron
    en cada grupo (1ero, 2do, y potenciales mejores terceros).
    """
    standings = obtener_standings_mundial()
    if not standings:
        return {"primeros": {}, "segundos": {}, "terceros": {}, "standings_completos": {}}
    primeros = {}
    segundos = {}
    terceros = {}
    for grupo_nombre, equipos in standings.items():
        equipos_mapeados = []
        for eq in equipos:
            eq_copy = eq.copy()
            eq_copy["equipo"] = mapear_nombre_equipo(eq["equipo"])
            equipos_mapeados.append(eq_copy)
        if len(equipos_mapeados) >= 1:
            primeros[grupo_nombre] = equipos_mapeados[0]["equipo"]
        if len(equipos_mapeados) >= 2:
            segundos[grupo_nombre] = equipos_mapeados[1]["equipo"]
        if len(equipos_mapeados) >= 3:
            terceros[grupo_nombre] = equipos_mapeados[2]["equipo"]
    return {
        "primeros": primeros,
        "segundos": segundos,
        "terceros": terceros,
        "standings_completos": standings,
    }

# =============================================================================
# GOLEADORES — Cache 1 minuto
# =============================================================================
@st.cache_data(ttl=60)
def obtener_goleadores_mundial():
    """Obtiene la tabla de goleadores del Mundial 2026."""
    if not _hay_api_key():
        return pd.DataFrame()
    url = f"{API_BASE_URL}/players/topscorers"
    params = {"league": WORLD_CUP_2026_ID, "season": WORLD_CUP_2026_SEASON}
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        goleadores = []
        for item in data.get("response", []):
            goleadores.append({
                "jugador": item["player"]["name"],
                "equipo": mapear_nombre_equipo(item["statistics"][0]["team"]["name"]),
                "goles": item["statistics"][0]["goals"]["total"] or 0,
                "asistencias": item["statistics"][0]["goals"]["assists"] or 0,
            })
        return pd.DataFrame(goleadores)
    except Exception:
        return pd.DataFrame()

# =============================================================================
# ULTIMOS RESULTADOS
# =============================================================================
def obtener_ultimos_resultados(resultados, cantidad=3):
    """Retorna los ultimos N partidos finalizados."""
    if resultados.empty:
        return pd.DataFrame()
    finalizados = resultados[resultados["estado"].isin(ESTADOS_FINALIZADO)].copy()
    if finalizados.empty:
        return pd.DataFrame()
    finalizados = finalizados.sort_values("fecha", ascending=False)
    return finalizados.head(cantidad)

# =============================================================================
# MAPEO DE NOMBRES Y CLASIFICACION DE RONDAS
# =============================================================================
def mapear_nombre_equipo(nombre_api):
    """Mapea nombres de la API al formato del Excel."""
    mapeo = {
        "Netherlands": "Paises Bajos", "South Korea": "Corea del Sur",
        "Korea Republic": "Corea del Sur", "USA": "Estados Unidos",
        "United States": "Estados Unidos", "Ivory Coast": "Costa de Marfil",
        "Cote D'Ivoire": "Costa de Marfil",
        "Czech Republic": "Republica Checa", "Czechia": "Republica Checa",
        "Saudi Arabia": "Arabia Saudita", "New Zealand": "Nueva Zelanda",
        "Cape Verde": "Cabo Verde", "DR Congo": "Congo", "Congo DR": "Congo",
        "South Africa": "Sudafrica", "Morocco": "Marruecos",
        "Germany": "Alemania", "England": "Inglaterra",
        "France": "Francia", "Spain": "España", "Brazil": "Brasil",
        "Japan": "Japon", "Switzerland": "Suiza", "Turkey": "Turquia",
        "Norway": "Noruega", "Sweden": "Suecia", "Scotland": "Escocia",
        "Tunisia": "Tunez", "Egypt": "Egipto",
        "Bosnia and Herzegovina": "Bosnia", "Bosnia And Herzegovina": "Bosnia",
        "Jordan": "Jordania", "Iraq": "Irak", "Iran": "Iran",
        "Algeria": "Argelia", "Belgium": "Belgica", "Croatia": "Croacia",
        "Colombia": "Colombia", "Canada": "Canada",
        "Panama": "Panama", "Paraguay": "Paraguay",
        "Qatar": "Qatar", "Uzbekistan": "Uzbekistan",
        "Curacao": "Curazao", "Haiti": "Haiti",
        "Australia": "Australia", "Austria": "Austria",
    }
    return mapeo.get(nombre_api, nombre_api)

def clasificar_ronda(ronda_api):
    """Convierte nombre de ronda de la API al formato interno."""
    ronda = ronda_api.lower()
    if "group" in ronda: return "grupos"
    elif "32" in ronda: return "16vos"
    elif "16" in ronda: return "8vos"
    elif "quarter" in ronda: return "4tos"
    elif "semi" in ronda: return "semis"
    elif "3rd" in ronda or "third" in ronda: return "3ero"
    elif "final" in ronda: return "final"
    return ronda
