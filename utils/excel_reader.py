# =============================================================================
# utils/excel_reader.py
# Módulo encargado de leer y parsear los archivos Excel (.xlsm) del PRODE.
#
# ESTRUCTURA DEL EXCEL (confirmada con capturas del archivo real):
#
# Pestaña "Groups Stage":
#   - 12 grupos (A-L), 6 partidos cada uno = 72 partidos
#   - Columnas: A=ID, B=Fecha, E=Local, F=GolesLocal, G=GolesVisitante, H=Visitante
#
# Pestaña "Round of 32 & Round of 16":
#   - 16vos (M73-M88): dos bloques (izq y der)
#   - 8vos (M89-M96): dos bloques (izq y der)
#   - Si hay empate, los penales van en la fila de abajo
#
# Pestaña "Quarter, Semis & Final":
#   - Cuartos (M97-M100), Semis (M101-M102)
#   - 3er puesto (M103), Final (M104)
#   - Categorías especiales: Figura, Goleador, Revelación, Decepción,
#     Mejor 1era Fase, Peor Equipo
#
# Pestaña "Total Results":
#   - Tabla de 48 filas con la clasificación completa del torneo
#   - Columnas: A=Posición, B=Fase alcanzada, D=País, E=Puntos,
#     F=G(ganados), G=E(empates), H=P(perdidos), I=Dif, J=G+, K=G-
#   - FUENTE CLAVE: nos dice qué equipos llegaron a cada ronda
#     según las predicciones del participante
#
# Cada participante tiene su propio archivo .xlsm
# Se leen todos los archivos de la carpeta data/participantes/
# =============================================================================

import pandas as pd
import streamlit as st
import os
import glob
from typing import Dict, List, Tuple, Optional, Set
from utils.normalizar import normalizar_nombre_equipo


# --- Ruta por defecto de la carpeta de participantes ---
DEFAULT_PARTICIPANTES_DIR = os.path.join("data", "participantes")

# --- Nombres de las pestañas del Excel ---
HOJA_GRUPOS = "Groups Stage"
HOJA_ELIMINATORIAS = "Round of 32 & Round of 16"
HOJA_FINAL = "Quarter, Semis & Final"
HOJA_TOTAL_RESULTS = "Total Results"


# =============================================================================
# MAPEO DE CELDAS — FASE DE GRUPOS
#
# Columnas (índice 0):
#   A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7
#
# Para fase de grupos:
#   Col 0 (A) = ID partido (GA1, GA2...)
#   Col 1 (B) = Fecha
#   Col 4 (E) = Equipo Local
#   Col 5 (F) = Goles Local (APUESTA) ← celda amarilla
#   Col 6 (G) = Goles Visitante (APUESTA) ← celda amarilla
#   Col 7 (H) = Equipo Visitante
# =============================================================================

GRUPOS_FILAS = {
    "A": [2, 3, 4, 5, 6, 7],
    "B": [11, 12, 13, 14, 15, 16],
    "C": [20, 21, 22, 23, 24, 25],
    "D": [29, 30, 31, 32, 33, 34],
    "E": [38, 39, 40, 41, 42, 43],
    "F": [47, 48, 49, 50, 51, 52],
    "G": [56, 57, 58, 59, 60, 61],
    "H": [65, 66, 67, 68, 69, 70],
    "I": [74, 75, 76, 77, 78, 79],
    "J": [83, 84, 85, 86, 87, 88],
    "K": [92, 93, 94, 95, 96, 97],
    "L": [101, 102, 103, 104, 105, 106],
}

COL_GRUPOS = {
    "id": 0,         # A
    "fecha": 1,      # B
    "local": 4,      # E
    "goles_l": 5,    # F (apuesta)
    "goles_v": 6,    # G (apuesta)
    "visitante": 7,  # H
}


# =============================================================================
# MAPEO DE CELDAS — ELIMINATORIAS
#
# Round of 32 (16vos) - Pestaña "Round of 32 & Round of 16"
#   Izquierda (M73-M80): B=equipo1, C=goles1, D=goles2, E=equipo2
#   Derecha (M81-M88): H=equipo1, I=goles1, J=goles2, K=equipo2
#   Penales en fila+1: mismas columnas de goles
#
# Round of 16 (8vos) - misma pestaña
#   Izquierda (M89-M92): P=equipo1, Q=goles1, R=goles2, S=equipo2
#   Derecha (M93-M96): V=equipo1, W=goles1, X=goles2, Y=equipo2
#
# Quarter, Semis & Final - Pestaña "Quarter, Semis & Final"
#   Cuartos izq (M97-M98): B=eq1, C=g1, D=g2, E=eq2
#   Cuartos der (M99-M100): H=eq1, I=g1, J=g2, K=eq2
#   Semis (M101): B=eq1, C=g1, D=g2, E=eq2
#   Semis (M102): H=eq1, I=g1, J=g2, K=eq2
#   3er puesto (M103): O=eq1, P=g1, Q=g2, R=eq2
#   Final (M104): O=eq1, P=g1, Q=g2, R=eq2
# =============================================================================

# Cada entrada: (fila_idx, col_eq1, col_g1, col_g2, col_eq2)
ROUND32_IZQUIERDA = {
    "M73": (4, 1, 2, 3, 4),
    "M74": (8, 1, 2, 3, 4),
    "M75": (12, 1, 2, 3, 4),
    "M76": (16, 1, 2, 3, 4),
    "M77": (20, 1, 2, 3, 4),
    "M78": (24, 1, 2, 3, 4),
    "M79": (28, 1, 2, 3, 4),
    "M80": (32, 1, 2, 3, 4),
}

ROUND32_DERECHA = {
    "M81": (4, 7, 8, 9, 10),
    "M82": (8, 7, 8, 9, 10),
    "M83": (12, 7, 8, 9, 10),
    "M84": (16, 7, 8, 9, 10),
    "M85": (20, 7, 8, 9, 10),
    "M86": (24, 7, 8, 9, 10),
    "M87": (28, 7, 8, 9, 10),
    "M88": (32, 7, 8, 9, 10),
}

ROUND16_IZQUIERDA = {
    "M89": (4, 15, 16, 17, 18),
    "M90": (12, 15, 16, 17, 18),
    "M91": (20, 15, 16, 17, 18),
    "M92": (28, 15, 16, 17, 18),
}

ROUND16_DERECHA = {
    "M93": (4, 21, 22, 23, 24),
    "M94": (12, 21, 22, 23, 24),
    "M95": (20, 21, 22, 23, 24),
    "M96": (28, 21, 22, 23, 24),
}

CUARTOS_IZQUIERDA = {
    "M97": (4, 1, 2, 3, 4),
    "M98": (8, 1, 2, 3, 4),
}

CUARTOS_DERECHA = {
    "M99": (4, 7, 8, 9, 10),
    "M100": (8, 7, 8, 9, 10),
}

SEMIS = {
    "M101": (18, 1, 2, 3, 4),
    "M102": (18, 7, 8, 9, 10),
}

TERCER_PUESTO = {
    "M103": (13, 14, 15, 16, 17),
}

FINAL = {
    "M104": (4, 14, 15, 16, 17),
}

# Categorías especiales — Pestaña "Quarter, Semis & Final"
CATEGORIAS_CELDAS = {
    "Figura": (17, 18),           # Fila 18 idx 17, col S idx 18
    "Goleador": (18, 18),         # Fila 19 idx 18, col S idx 18
    "Revelación": (19, 18),       # Fila 20 idx 19, col S idx 18
    "Decepción": (20, 18),        # Fila 21 idx 20, col S idx 18
    "Mejor 1era Fase": (21, 18),  # Fila 22 idx 21, col S idx 18
    "Peor Equipo": (22, 18),      # Fila 23 idx 22, col S idx 18
}


# =============================================================================
# MAPEO DE CELDAS — TOTAL RESULTS
#
# La pestaña "Total Results" tiene 48 filas (una por equipo) + 1 encabezado.
# Fila 0 (índice) = Encabezado: Fase, Pts*, País, Puntos, G, E, P, Dif, G+, G-
# Filas 1-48 (índice) = Datos de cada equipo
#
# Columnas (índice 0):
#   A=0 → Número de posición
#   B=1 → Fase alcanzada (Campeón, Sub-campeón, 3er puesto, Semifinal,
#          4tos de final, 8vos de final, 16vos de final, Groups stage)
#   D=3 → País
#   E=4 → Puntos
#   F=5 → Ganados
#   G=6 → Empates
#   H=7 → Perdidos
#   I=8 → Diferencia de goles
#   J=9 → Goles a favor (G+)
#   K=10 → Goles en contra (G-)
# =============================================================================

COL_TR = {
    "posicion": 0,   # A
    "fase": 1,       # B
    "pais": 3,       # D
    "puntos": 4,     # E
    "ganados": 5,    # F
    "empates": 6,    # G
    "perdidos": 7,   # H
    "dif": 8,        # I
    "goles_favor": 9,   # J
    "goles_contra": 10,  # K
}

# Mapeo de nombres de fases en "Total Results" a nombres internos
FASE_MAPEO = {
    "campeón": "campeon",
    "campeon": "campeon",
    "sub-campeón": "subcampeon",
    "sub-campeon": "subcampeon",
    "subcampeón": "subcampeon",
    "subcampeon": "subcampeon",
    "3er puesto": "3ero",
    "semifinal": "semis",
    "4tos de final": "4tos",
    "8vos de final": "8vos",
    "16vos de final": "16vos",
    "groups stage": "grupos",
}


# =============================================================================
# FUNCIONES AUXILIARES DE LECTURA
# =============================================================================

def _leer_celda(df: pd.DataFrame, fila: int, col: int):
    """Lee una celda de forma segura. Retorna None si está fuera de rango o NaN."""
    try:
        valor = df.iloc[fila, col]
        if pd.isna(valor):
            return None
        return valor
    except (IndexError, KeyError):
        return None


def _leer_celda_num(df: pd.DataFrame, fila: int, col: int) -> Optional[int]:
    """Lee una celda numérica (goles). Retorna None si no es número."""
    valor = _leer_celda(df, fila, col)
    if valor is None:
        return None
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def _leer_celda_str(df: pd.DataFrame, fila: int, col: int) -> str:
    """Lee una celda como string. Retorna "" si está vacía."""
    valor = _leer_celda(df, fila, col)
    if valor is None:
        return ""
    return str(valor).strip()


def _determinar_ganador(g1: int, g2: int, pen1: Optional[int], pen2: Optional[int]) -> str:
    """
    Determina quién gana un partido de eliminatoria.
    Si hay empate en tiempo regular, se revisan los penales.
    Retorna: 'equipo1', 'equipo2', o 'empate'
    """
    if g1 > g2:
        return "equipo1"
    elif g2 > g1:
        return "equipo2"
    else:
        if pen1 is not None and pen2 is not None:
            if pen1 > pen2:
                return "equipo1"
            elif pen2 > pen1:
                return "equipo2"
        return "empate"


# =============================================================================
# PARSEO DE TOTAL RESULTS (NUEVA FUNCIÓN CLAVE)
# =============================================================================

def parsear_total_results(df: pd.DataFrame, participante: str) -> Dict:
    """
    Lee la pestaña "Total Results" y extrae la clasificación completa
    del torneo según las predicciones del participante.
    
    Esta pestaña es generada automáticamente por las fórmulas del Excel
    y nos da directamente qué equipos llegaron a cada fase [1].
    
    Retorna un diccionario con:
    - "campeon": str (nombre del equipo campeón)
    - "subcampeon": str
    - "tercero": str (3er puesto)
    - "equipos_por_ronda": Dict[str, set] → {ronda: set(equipos)}
      Cada equipo aparece en la ronda MÁS LEJANA que alcanzó.
      Pero para el cálculo de puntos, un equipo que llegó a semis
      también "llegó" a 4tos, 8vos y 16vos.
    - "tabla_completa": pd.DataFrame con toda la tabla
    - "equipos_grupos_eliminados": set → equipos que NO pasaron de grupos
    """
    resultado = {
        "campeon": "",
        "subcampeon": "",
        "tercero": "",
        "cuarto": "",  # Semifinalista perdedor que no es 3ero
        "equipos_por_fase": {},  # Fase exacta alcanzada
        "equipos_por_ronda": {},  # Acumulado (para cálculo de puntos)
        "equipos_grupos_eliminados": set(),
        "tabla_completa": pd.DataFrame(),
        "participante": participante,
    }
    
    # Leer todas las filas de la tabla (empezando desde fila 1, la 0 es encabezado)
    filas_datos = []
    
    for fila_idx in range(1, min(len(df), 50)):  # Máximo 48 equipos + margen
        fase_raw = _leer_celda_str(df, fila_idx, COL_TR["fase"])
        pais = normalizar_nombre_equipo(_leer_celda_str(df, fila_idx, COL_TR["pais"]))
        puntos = _leer_celda_num(df, fila_idx, COL_TR["puntos"])
        ganados = _leer_celda_num(df, fila_idx, COL_TR["ganados"])
        empates = _leer_celda_num(df, fila_idx, COL_TR["empates"])
        perdidos = _leer_celda_num(df, fila_idx, COL_TR["perdidos"])
        dif = _leer_celda_num(df, fila_idx, COL_TR["dif"])
        gf = _leer_celda_num(df, fila_idx, COL_TR["goles_favor"])
        gc = _leer_celda_num(df, fila_idx, COL_TR["goles_contra"])
        
        if not pais or not fase_raw:
            continue
        
        # Normalizar el nombre de la fase
        fase_normalizada = FASE_MAPEO.get(fase_raw.lower().strip(), "desconocida")
        
        filas_datos.append({
            "posicion": fila_idx,
            "fase_raw": fase_raw,
            "fase": fase_normalizada,
            "pais": pais,
            "puntos": puntos or 0,
            "ganados": ganados or 0,
            "empates": empates or 0,
            "perdidos": perdidos or 0,
            "dif": dif or 0,
            "goles_favor": gf or 0,
            "goles_contra": gc or 0,
        })
    
    if not filas_datos:
        return resultado
    
    tabla = pd.DataFrame(filas_datos)
    resultado["tabla_completa"] = tabla
    
    # --- Extraer equipos clave ---
    campeon_rows = tabla[tabla["fase"] == "campeon"]
    if not campeon_rows.empty:
        resultado["campeon"] = campeon_rows.iloc[0]["pais"]
    
    subcampeon_rows = tabla[tabla["fase"] == "subcampeon"]
    if not subcampeon_rows.empty:
        resultado["subcampeon"] = subcampeon_rows.iloc[0]["pais"]
    
    tercero_rows = tabla[tabla["fase"] == "3ero"]
    if not tercero_rows.empty:
        resultado["tercero"] = tercero_rows.iloc[0]["pais"]
    
    cuarto_rows = tabla[tabla["fase"] == "semis"]
    if not cuarto_rows.empty:
        resultado["cuarto"] = cuarto_rows.iloc[0]["pais"]
    
    # --- Equipos por fase exacta ---
    equipos_por_fase = {}
    for _, row in tabla.iterrows():
        fase = row["fase"]
        if fase not in equipos_por_fase:
            equipos_por_fase[fase] = set()
        equipos_por_fase[fase].add(row["pais"])
    resultado["equipos_por_fase"] = equipos_por_fase
    
    # --- Equipos eliminados en grupos ---
    resultado["equipos_grupos_eliminados"] = equipos_por_fase.get("grupos", set())
    
    # --- Equipos por ronda ACUMULADO ---
    # Un equipo que llegó a semis también "estuvo" en 4tos, 8vos y 16vos.
    # Esto es lo que necesitamos para calcular puntos de eliminatorias:
    # si predijiste que Brasil llega a 8vos y realmente llegó a semis,
    # igualmente sumás los puntos de 8vos.
    
    # Jerarquía de fases (de más lejos a más cerca)
    jerarquia = ["campeon", "subcampeon", "3ero", "semis", "4tos", "8vos", "16vos"]
    
    equipos_por_ronda = {
        "16vos": set(),
        "8vos": set(),
        "4tos": set(),
        "semis": set(),
        "final": set(),  # Campeón + subcampeón
    }
    
    for _, row in tabla.iterrows():
        fase = row["fase"]
        pais = row["pais"]
        
        if fase == "grupos":
            continue  # No pasó de grupos, no suma en ninguna ronda
        
        # El equipo llegó al menos a 16vos
        equipos_por_ronda["16vos"].add(pais)
        
        if fase in ["8vos", "4tos", "semis", "3ero", "campeon", "subcampeon"]:
            equipos_por_ronda["8vos"].add(pais)
        
        if fase in ["4tos", "semis", "3ero", "campeon", "subcampeon"]:
            equipos_por_ronda["4tos"].add(pais)
        
        if fase in ["semis", "3ero", "campeon", "subcampeon"]:
            equipos_por_ronda["semis"].add(pais)
        
        if fase in ["campeon", "subcampeon"]:
            equipos_por_ronda["final"].add(pais)
    
    resultado["equipos_por_ronda"] = equipos_por_ronda
    
    return resultado


# =============================================================================
# PARSEO DE FASE DE GRUPOS
# =============================================================================

def parsear_grupos(df: pd.DataFrame, participante: str) -> pd.DataFrame:
    """
    Extrae las 72 apuestas de fase de grupos de un participante.
    Lee la pestaña "Groups Stage" usando coordenadas exactas.
    """
    apuestas = []
    
    for grupo, filas in GRUPOS_FILAS.items():
        for i, fila_idx in enumerate(filas):
            partido_id = _leer_celda_str(df, fila_idx, COL_GRUPOS["id"])
            fecha = _leer_celda_str(df, fila_idx, COL_GRUPOS["fecha"])
            local = normalizar_nombre_equipo(_leer_celda_str(df, fila_idx, COL_GRUPOS["local"]))
            goles_l = _leer_celda_num(df, fila_idx, COL_GRUPOS["goles_l"])
            goles_v = _leer_celda_num(df, fila_idx, COL_GRUPOS["goles_v"])
            visitante = normalizar_nombre_equipo(_leer_celda_str(df, fila_idx, COL_GRUPOS["visitante"]))
            
            if not partido_id:
                partido_id = f"G{grupo}{i+1}"
            
            apuestas.append({
                "partido_id": partido_id,
                "grupo": grupo,
                "fecha": fecha,
                "equipo_local": local,
                "equipo_visitante": visitante,
                "goles_local_pred": goles_l,
                "goles_visitante_pred": goles_v,
                "participante": participante,
                "ronda": "grupos",
            })
    
    return pd.DataFrame(apuestas)


# =============================================================================
# PARSEO DE ELIMINATORIAS (partidos individuales con goles y penales)
# =============================================================================

def _parsear_bloque_eliminatoria(
    df: pd.DataFrame,
    mapeo: Dict,
    ronda: str,
    participante: str
) -> List[dict]:
    """
    Parsea un bloque de partidos de eliminatoria.
    Lee equipos, goles, y penales (si hay empate en la fila siguiente).
    """
    partidos = []
    
    for codigo, (fila, col_eq1, col_g1, col_g2, col_eq2) in mapeo.items():
        equipo1 = normalizar_nombre_equipo(_leer_celda_str(df, fila, col_eq1))
        goles1 = _leer_celda_num(df, fila, col_g1)
        goles2 = _leer_celda_num(df, fila, col_g2)
        equipo2 = normalizar_nombre_equipo(_leer_celda_str(df, fila, col_eq2))
        
        # Revisar penales en la fila siguiente
        penales1 = None
        penales2 = None
        texto_pen = _leer_celda_str(df, fila + 1, col_eq1)
        if "penal" in texto_pen.lower():
            penales1 = _leer_celda_num(df, fila + 1, col_g1)
            penales2 = _leer_celda_num(df, fila + 1, col_g2)
        
        # Determinar ganador
        ganador = ""
        if goles1 is not None and goles2 is not None:
            res = _determinar_ganador(goles1, goles2, penales1, penales2)
            if res == "equipo1":
                ganador = equipo1
            elif res == "equipo2":
                ganador = equipo2
        
        partidos.append({
            "partido_id": codigo,
            "ronda": ronda,
            "equipo1": equipo1,
            "equipo2": equipo2,
            "goles1_pred": goles1,
            "goles2_pred": goles2,
            "penales1_pred": penales1,
            "penales2_pred": penales2,
            "ganador_pred": ganador,
            "participante": participante,
        })
    
    return partidos


def parsear_eliminatorias(
    df_elim: pd.DataFrame,
    df_final: pd.DataFrame,
    participante: str
) -> pd.DataFrame:
    """
    Extrae TODAS las predicciones de eliminatorias (M73 a M104).
    """
    todos = []
    
    # Pestaña "Round of 32 & Round of 16"
    todos.extend(_parsear_bloque_eliminatoria(df_elim, ROUND32_IZQUIERDA, "16vos", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_elim, ROUND32_DERECHA, "16vos", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_elim, ROUND16_IZQUIERDA, "8vos", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_elim, ROUND16_DERECHA, "8vos", participante))
    
    # Pestaña "Quarter, Semis & Final"
    todos.extend(_parsear_bloque_eliminatoria(df_final, CUARTOS_IZQUIERDA, "4tos", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_final, CUARTOS_DERECHA, "4tos", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_final, SEMIS, "semis", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_final, TERCER_PUESTO, "3ero", participante))
    todos.extend(_parsear_bloque_eliminatoria(df_final, FINAL, "final", participante))
    
    return pd.DataFrame(todos)


# =============================================================================
# PARSEO DE CATEGORÍAS ESPECIALES
# =============================================================================

def parsear_categorias_especiales(
    df_final: pd.DataFrame,
    participante: str
) -> Dict[str, str]:
    """
    Extrae las categorías especiales de la pestaña "Quarter, Semis & Final":
    Figura, Goleador, Revelación, Decepción, Mejor 1era Fase, Peor Equipo.
    """
    categorias = {}
    for nombre_cat, (fila, col) in CATEGORIAS_CELDAS.items():
        categorias[nombre_cat] = normalizar_nombre_equipo(_leer_celda_str(df_final, fila, col))
    return categorias


# =============================================================================
# FUNCIÓN PRINCIPAL: CARGAR TODOS LOS PARTICIPANTES
# =============================================================================

@st.cache_data
def cargar_todos_los_participantes(
    directorio: str = DEFAULT_PARTICIPANTES_DIR
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, str]], Dict[str, Dict]]:
    """
    Función principal que carga y procesa TODOS los archivos Excel.
    
    Busca todos los .xlsm / .xlsx en la carpeta de participantes.
    El nombre del archivo (sin extensión) = nombre del participante.
    
    Retorna una tupla con:
    1. DataFrame con TODAS las apuestas de fase de grupos
    2. DataFrame con TODAS las predicciones de eliminatorias
    3. Dict {participante: {categoría: valor}} → categorías especiales
    4. Dict {participante: {...}} → datos de Total Results
       Incluye: campeon, subcampeon, tercero, equipos_por_ronda,
       equipos_por_fase, equipos_grupos_eliminados, tabla_completa
    """
    # Buscar archivos
    archivos = []
    if os.path.exists(directorio):
        for ext in ["*.xlsm", "*.xlsx"]:
            archivos.extend(glob.glob(os.path.join(directorio, ext)))
    
    if not archivos:
        st.warning(
            f"⚠️ No se encontraron archivos Excel en `{directorio}/`. "
            f"Colocá los archivos .xlsm de cada participante ahí."
        )
        return pd.DataFrame(), pd.DataFrame(), {}, {}
    
    participantes_ok = []
    
    todas_apuestas_grupos = []
    todas_pred_elim = []
    todas_categorias = {}
    todos_total_results = {}
    
    for archivo in sorted(archivos):
        nombre_archivo = os.path.basename(archivo)
        participante = os.path.splitext(nombre_archivo)[0]
        
        try:
            xls = pd.ExcelFile(archivo, engine="openpyxl")
            hojas = xls.sheet_names
            
            # Verificar que todas las pestañas existen
            pestanas_requeridas = [HOJA_GRUPOS, HOJA_ELIMINATORIAS, HOJA_FINAL, HOJA_TOTAL_RESULTS]
            faltantes = [h for h in pestanas_requeridas if h not in hojas]
            if faltantes:
                st.error(f"❌ {participante}: Faltan pestañas: {', '.join(faltantes)}")
                continue
            
            # Leer cada pestaña sin encabezado
            df_grupos = pd.read_excel(xls, sheet_name=HOJA_GRUPOS, header=None)
            df_elim = pd.read_excel(xls, sheet_name=HOJA_ELIMINATORIAS, header=None)
            df_final = pd.read_excel(xls, sheet_name=HOJA_FINAL, header=None)
            df_total = pd.read_excel(xls, sheet_name=HOJA_TOTAL_RESULTS, header=None)
            
            # --- 1. Parsear fase de grupos ---
            apuestas_grupos = parsear_grupos(df_grupos, participante)
            todas_apuestas_grupos.append(apuestas_grupos)
            
            # --- 2. Parsear eliminatorias (partidos individuales) ---
            pred_elim = parsear_eliminatorias(df_elim, df_final, participante)
            todas_pred_elim.append(pred_elim)
            
            # --- 3. Parsear categorías especiales ---
            categorias = parsear_categorias_especiales(df_final, participante)
            
            # --- 4. Parsear Total Results (CLAVE) ---
            total_results = parsear_total_results(df_total, participante)
            todos_total_results[participante] = total_results
            
            # Agregar campeón a las categorías para cálculo de penalidades
            categorias["Campeon"] = total_results.get("campeon", "")
            categorias["Subcampeon"] = total_results.get("subcampeon", "")
            categorias["Tercero"] = total_results.get("tercero", "")
            
            todas_categorias[participante] = categorias
            
            participantes_ok.append(participante)
            
        except Exception as e:
            st.error(f"❌ Error leyendo archivo de {participante}: {e}")
            continue
    
    # Carga silenciosa - sin mensajes

    # Concatenar DataFrames
    df_grupos_total = (
        pd.concat(todas_apuestas_grupos, ignore_index=True)
        if todas_apuestas_grupos else pd.DataFrame()
    )
    df_elim_total = (
        pd.concat(todas_pred_elim, ignore_index=True)
        if todas_pred_elim else pd.DataFrame()
    )
    
    return df_grupos_total, df_elim_total, todas_categorias, todos_total_results


def obtener_equipos_predichos_por_ronda(
    total_results: Dict
) -> Dict[str, Set[str]]:
    """
    Extrae los equipos que un participante predice en cada ronda,
    directamente desde la pestaña Total Results.
    
    Esto reemplaza la lógica anterior de deducir ronda por ronda
    desde los partidos individuales. Total Results ya tiene todo
    calculado por las fórmulas del Excel [1].
    
    Retorna: Dict {ronda: set(equipos)}
    """
    return total_results.get("equipos_por_ronda", {
        "16vos": set(),
        "8vos": set(),
        "4tos": set(),
        "semis": set(),
        "final": set(),
    })
