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
# Cada participante tiene su propio archivo .xlsm
# Se leen todos los archivos de la carpeta data/participantes/
# =============================================================================

import pandas as pd
import streamlit as st
import os
import glob
from typing import Dict, List, Tuple, Optional


# --- Ruta por defecto de la carpeta de participantes ---
DEFAULT_PARTICIPANTES_DIR = os.path.join("data", "participantes")

# --- Nombres de las pestañas del Excel ---
HOJA_GRUPOS = "Groups Stage"
HOJA_ELIMINATORIAS = "Round of 32 & Round of 16"
HOJA_FINAL = "Quarter, Semis & Final"


# =============================================================================
# MAPEO DE CELDAS — FASE DE GRUPOS
# Confirmado con las capturas del Excel real.
# Cada grupo tiene 6 partidos. Las filas están separadas por una fila de
# encabezado entre cada grupo.
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

# Filas donde empiezan los partidos de cada grupo (índice 0 = fila 1 del Excel)
# Grupo A: partidos en filas Excel 3-8 → índice 2-7
# Grupo B: partidos en filas Excel 12-17 → índice 11-16
# etc.
GRUPOS_FILAS = {
    "A": [2, 3, 4, 5, 6, 7],       # GA1-GA6 (filas Excel 3-8)
    "B": [11, 12, 13, 14, 15, 16],  # GB1-GB6 (filas Excel 12-17)
    "C": [20, 21, 22, 23, 24, 25],  # GC1-GC6 (filas Excel 21-26)
    "D": [29, 30, 31, 32, 33, 34],  # GD1-GD6 (filas Excel 30-35)
    "E": [38, 39, 40, 41, 42, 43],  # GE1-GE6 (filas Excel 39-44)
    "F": [47, 48, 49, 50, 51, 52],  # GF1-GF6 (filas Excel 48-53)
    "G": [56, 57, 58, 59, 60, 61],  # GG1-GG6 (filas Excel 57-62)
    "H": [65, 66, 67, 68, 69, 70],  # GH1-GH6 (filas Excel 66-71)
    "I": [74, 75, 76, 77, 78, 79],  # GI1-GI6 (filas Excel 75-80)
    "J": [83, 84, 85, 86, 87, 88],  # GJ1-GJ6 (filas Excel 84-89)
    "K": [92, 93, 94, 95, 96, 97],  # GK1-GK6 (filas Excel 93-98)
    "L": [101, 102, 103, 104, 105, 106],  # GL1-GL6 (filas Excel 102-107)
}

# Columnas para fase de grupos (índice 0)
COL_GRUPOS = {
    "id": 0,        # A - ID del partido
    "fecha": 1,     # B - Fecha
    "local": 4,     # E - Equipo local
    "goles_l": 5,   # F - Goles local (APUESTA)
    "goles_v": 6,   # G - Goles visitante (APUESTA)
    "visitante": 7,  # H - Equipo visitante
}


# =============================================================================
# MAPEO DE CELDAS — ROUND OF 32 (16vos de Final)
#
# Lado izquierdo (M73-M80):
#   Col A=0 → Código, Col B=1 → Equipo1, Col C=2 → Goles1, Col D=3 → Goles2, Col E=4 → Equipo2
#   Penales en fila+1: Col B=1 → "Penales", Col C=2 → Pen1, Col D=3 → Pen2
#
# Lado derecho (M81-M88):
#   Col G=6 → Código, Col H=7 → Equipo1, Col I=8 → Goles1, Col J=9 → Goles2, Col K=10 → Equipo2
#   Penales en fila+1: Col H=7 → "Penales", Col I=8 → Pen1, Col J=9 → Pen2
# =============================================================================

# Fila Excel → índice 0 (restar 1)
ROUND32_IZQUIERDA = {
    # partido: (fila_idx, col_codigo, col_eq1, col_g1, col_g2, col_eq2)
    "M73": (4, 0, 1, 2, 3, 4),
    "M74": (8, 0, 1, 2, 3, 4),
    "M75": (12, 0, 1, 2, 3, 4),
    "M76": (16, 0, 1, 2, 3, 4),
    "M77": (20, 0, 1, 2, 3, 4),
    "M78": (24, 0, 1, 2, 3, 4),
    "M79": (28, 0, 1, 2, 3, 4),
    "M80": (32, 0, 1, 2, 3, 4),
}

ROUND32_DERECHA = {
    "M81": (4, 6, 7, 8, 9, 10),
    "M82": (8, 6, 7, 8, 9, 10),
    "M83": (12, 6, 7, 8, 9, 10),
    "M84": (16, 6, 7, 8, 9, 10),
    "M85": (20, 6, 7, 8, 9, 10),
    "M86": (24, 6, 7, 8, 9, 10),
    "M87": (28, 6, 7, 8, 9, 10),
    "M88": (32, 6, 7, 8, 9, 10),
}


# =============================================================================
# MAPEO DE CELDAS — ROUND OF 16 (8vos de Final)
#
# Lado izquierdo (M89-M92):
#   Col N=13 → Código, Col P=15 → Equipo1, Col Q=16 → Goles1,
#   Col R=17 → Goles2, Col S=18 → Equipo2
#
# Lado derecho (M93-M96):
#   Col T=19 → Código, Col V=21 → Equipo1, Col W=22 → Goles1,
#   Col X=23 → Goles2, Col Y=24 → Equipo2
# =============================================================================

ROUND16_IZQUIERDA = {
    "M89": (4, 13, 15, 16, 17, 18),
    "M90": (12, 13, 15, 16, 17, 18),
    "M91": (20, 13, 15, 16, 17, 18),
    "M92": (28, 13, 15, 16, 17, 18),
}

ROUND16_DERECHA = {
    "M93": (4, 19, 21, 22, 23, 24),
    "M94": (12, 19, 21, 22, 23, 24),
    "M95": (20, 19, 21, 22, 23, 24),
    "M96": (28, 19, 21, 22, 23, 24),
}


# =============================================================================
# MAPEO DE CELDAS — QUARTER FINALS, SEMIS & FINAL
#
# Cuartos izquierda (M97-M98):
#   B=1→Equipo1, C=2→Goles1, D=3→Goles2, E=4→Equipo2
#
# Cuartos derecha (M99-M100):
#   H=7→Equipo1, I=8→Goles1, J=9→Goles2, K=10→Equipo2
#
# Semis (M101-M102): misma estructura que cuartos
#
# 3er puesto (M103):
#   O=14→Equipo1, P=15→Goles1, Q=16→Goles2, R=17→Equipo2
#
# Final (M104):
#   O=14→Equipo1, P=15→Goles1, Q=16→Goles2, R=17→Equipo2
#
# Categorías especiales:
#   Etiqueta en col N=13, Valor en col O=14
# =============================================================================

CUARTOS_IZQUIERDA = {
    "M97": (4, 0, 1, 2, 3, 4),
    "M98": (8, 0, 1, 2, 3, 4),
}

CUARTOS_DERECHA = {
    "M99": (4, 6, 7, 8, 9, 10),
    "M100": (8, 6, 7, 8, 9, 10),
}

SEMIS = {
    "M101": (18, 0, 1, 2, 3, 4),   # Fila Excel 19 → índice 18
    "M102": (18, 6, 7, 8, 9, 10),   # Fila Excel 19 → índice 18
}

TERCER_PUESTO = {
    "M103": (13, 13, 14, 15, 16, 17),  # Fila Excel 14 → índice 13
}

FINAL = {
    "M104": (4, 13, 14, 15, 16, 17),  # Fila Excel 5 → índice 4
}

# Categorías especiales — Pestaña "Quarter, Semis & Final"
# Fila Excel → índice 0
CATEGORIAS_CELDAS = {
    "Figura": (20, 14),           # Fila 21, col O (índice 14)
    "Goleador": (21, 14),         # Fila 22, col O
    "Revelación": (22, 14),       # Fila 23, col O
    "Decepción": (23, 14),        # Fila 24, col O
    "Mejor 1era Fase": (24, 14),  # Fila 25, col O
    "Peor Equipo": (25, 14),      # Fila 26, col O
}


# =============================================================================
# FUNCIONES DE LECTURA
# =============================================================================

def _leer_celda(df: pd.DataFrame, fila: int, col: int) -> Optional[str]:
    """
    Lee una celda del DataFrame de forma segura.
    Retorna None si está fuera de rango o es NaN.
    """
    try:
        valor = df.iloc[fila, col]
        if pd.isna(valor):
            return None
        return valor
    except (IndexError, KeyError):
        return None


def _leer_celda_num(df: pd.DataFrame, fila: int, col: int) -> Optional[int]:
    """
    Lee una celda numérica (goles) del DataFrame.
    Retorna None si no es un número válido.
    """
    valor = _leer_celda(df, fila, col)
    if valor is None:
        return None
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None


def _leer_celda_str(df: pd.DataFrame, fila: int, col: int) -> str:
    """
    Lee una celda como string. Retorna "" si está vacía.
    """
    valor = _leer_celda(df, fila, col)
    if valor is None:
        return ""
    return str(valor).strip()


def _determinar_ganador(g1: int, g2: int, pen1: Optional[int], pen2: Optional[int]) -> str:
    """
    Determina quién gana un partido de eliminatoria.
    Si hay empate en tiempo regular, se revisan los penales.
    
    Retorna: 'equipo1', 'equipo2', o 'empate' (solo en grupos)
    """
    if g1 > g2:
        return "equipo1"
    elif g2 > g1:
        return "equipo2"
    else:
        # Empate en tiempo regular → revisar penales
        if pen1 is not None and pen2 is not None:
            if pen1 > pen2:
                return "equipo1"
            elif pen2 > pen1:
                return "equipo2"
        return "empate"


# =============================================================================
# PARSEO DE FASE DE GRUPOS
# =============================================================================

def parsear_grupos(df: pd.DataFrame, participante: str) -> pd.DataFrame:
    """
    Extrae las 72 apuestas de fase de grupos de un participante.
    
    Lee la pestaña "Groups Stage" usando las coordenadas exactas confirmadas
    con las capturas del Excel real.
    
    Retorna un DataFrame con columnas:
    - partido_id, grupo, fecha, equipo_local, equipo_visitante,
      goles_local_pred, goles_visitante_pred, participante
    """
    apuestas = []
    
    for grupo, filas in GRUPOS_FILAS.items():
        for i, fila_idx in enumerate(filas):
            partido_id = _leer_celda_str(df, fila_idx, COL_GRUPOS["id"])
            fecha = _leer_celda_str(df, fila_idx, COL_GRUPOS["fecha"])
            local = _leer_celda_str(df, fila_idx, COL_GRUPOS["local"])
            goles_l = _leer_celda_num(df, fila_idx, COL_GRUPOS["goles_l"])
            goles_v = _leer_celda_num(df, fila_idx, COL_GRUPOS["goles_v"])
            visitante = _leer_celda_str(df, fila_idx, COL_GRUPOS["visitante"])
            
            # Generar ID si no se lee correctamente
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
# PARSEO DE ELIMINATORIAS
# =============================================================================

def _parsear_bloque_eliminatoria(
    df: pd.DataFrame,
    mapeo: Dict,
    ronda: str,
    participante: str
) -> List[dict]:
    """
    Parsea un bloque de partidos de eliminatoria.
    
    Para cada partido:
    1. Lee equipos y goles de la fila principal
    2. Si hay empate (goles iguales), lee la fila siguiente para penales
    3. Determina el ganador
    
    Parámetros:
        df: DataFrame de la pestaña correspondiente
        mapeo: Dict con {código_partido: (fila, col_cod, col_eq1, col_g1, col_g2, col_eq2)}
        ronda: Nombre de la ronda ("16vos", "8vos", "4tos", "semis", "3ero", "final")
        participante: Nombre del participante
    """
    partidos = []
    
    for codigo, (fila, col_cod, col_eq1, col_g1, col_g2, col_eq2) in mapeo.items():
        equipo1 = _leer_celda_str(df, fila, col_eq1)
        goles1 = _leer_celda_num(df, fila, col_g1)
        goles2 = _leer_celda_num(df, fila, col_g2)
        equipo2 = _leer_celda_str(df, fila, col_eq2)
        
        # Revisar si hay penales (fila siguiente, mismas columnas de goles)
        penales1 = None
        penales2 = None
        
        # Verificar si la fila siguiente tiene "Penales" en la columna del equipo1
        texto_penales = _leer_celda_str(df, fila + 1, col_eq1)
        if "penal" in texto_penales.lower():
            penales1 = _leer_celda_num(df, fila + 1, col_g1)
            penales2 = _leer_celda_num(df, fila + 1, col_g2)
        
        # Determinar ganador
        ganador = ""
        if goles1 is not None and goles2 is not None:
            resultado = _determinar_ganador(goles1, goles2, penales1, penales2)
            if resultado == "equipo1":
                ganador = equipo1
            elif resultado == "equipo2":
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
    Extrae TODAS las predicciones de eliminatorias de un participante.
    
    Lee las pestañas "Round of 32 & Round of 16" y "Quarter, Semis & Final"
    usando las coordenadas exactas mapeadas.
    
    Retorna un DataFrame con todos los partidos M73 a M104.
    """
    todos_partidos = []
    
    # --- Pestaña "Round of 32 & Round of 16" ---
    
    # 16vos de final izquierda (M73-M80)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_elim, ROUND32_IZQUIERDA, "16vos", participante)
    )
    
    # 16vos de final derecha (M81-M88)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_elim, ROUND32_DERECHA, "16vos", participante)
    )
    
    # 8vos de final izquierda (M89-M92)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_elim, ROUND16_IZQUIERDA, "8vos", participante)
    )
    
    # 8vos de final derecha (M93-M96)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_elim, ROUND16_DERECHA, "8vos", participante)
    )
    
    # --- Pestaña "Quarter, Semis & Final" ---
    
    # Cuartos izquierda (M97-M98)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_final, CUARTOS_IZQUIERDA, "4tos", participante)
    )
    
    # Cuartos derecha (M99-M100)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_final, CUARTOS_DERECHA, "4tos", participante)
    )
    
    # Semifinales (M101-M102)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_final, SEMIS, "semis", participante)
    )
    
    # 3er puesto (M103)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_final, TERCER_PUESTO, "3ero", participante)
    )
    
    # Final (M104)
    todos_partidos.extend(
        _parsear_bloque_eliminatoria(df_final, FINAL, "final", participante)
    )
    
    return pd.DataFrame(todos_partidos)


# =============================================================================
# PARSEO DE CATEGORÍAS ESPECIALES
# =============================================================================

def parsear_categorias_especiales(
    df_final: pd.DataFrame,
    participante: str
) -> Dict[str, str]:
    """
    Extrae las categorías especiales de la pestaña "Quarter, Semis & Final".
    
    Lee las celdas exactas donde están Figura, Goleador, Revelación,
    Decepción, Mejor 1era Fase y Peor Equipo.
    
    Retorna un diccionario {categoría: valor_predicho}
    """
    categorias = {}
    
    for nombre_cat, (fila, col) in CATEGORIAS_CELDAS.items():
        valor = _leer_celda_str(df_final, fila, col)
        categorias[nombre_cat] = valor
    
    return categorias


# =============================================================================
# FUNCIÓN PRINCIPAL: CARGAR TODOS LOS PARTICIPANTES
# =============================================================================

@st.cache_data
def cargar_todos_los_participantes(
    directorio: str = DEFAULT_PARTICIPANTES_DIR
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, str]]]:
    """
    Función principal que carga y procesa TODOS los archivos Excel
    de la carpeta de participantes.
    
    Busca todos los archivos .xlsm en el directorio especificado.
    El nombre del archivo (sin extensión) se usa como nombre del participante.
    
    Retorna una tupla con:
    1. DataFrame con TODAS las apuestas de fase de grupos de TODOS los participantes
    2. DataFrame con TODAS las predicciones de eliminatorias de TODOS los participantes
    3. Diccionario {participante: {categoría: valor}} con categorías especiales
    """
    # Buscar todos los archivos .xlsm en la carpeta
    patron = os.path.join(directorio, "*.xlsm")
    archivos = glob.glob(patron)
    
    # También buscar .xlsx por si alguien convierte el formato
    patron_xlsx = os.path.join(directorio, "*.xlsx")
    archivos.extend(glob.glob(patron_xlsx))
    
    if not archivos:
        st.warning(
            f"⚠️ No se encontraron archivos Excel en `{directorio}/`. "
            f"Colocá los archivos .xlsm de cada participante ahí."
        )
        return pd.DataFrame(), pd.DataFrame(), {}
    
    st.info(f"📂 Se encontraron {len(archivos)} archivos de participantes.")
    
    todas_apuestas_grupos = []
    todas_predicciones_elim = []
    todas_categorias = {}
    
    for archivo in sorted(archivos):
        # Extraer nombre del participante del nombre del archivo
        nombre_archivo = os.path.basename(archivo)
        participante = os.path.splitext(nombre_archivo)[0]
        
        try:
            # Leer las 3 pestañas del Excel
            xls = pd.ExcelFile(archivo, engine="openpyxl")
            
            # Verificar que las pestañas existen
            hojas_disponibles = xls.sheet_names
            
            if HOJA_GRUPOS not in hojas_disponibles:
                st.error(f"❌ {participante}: No tiene la pestaña '{HOJA_GRUPOS}'")
                continue
            if HOJA_ELIMINATORIAS not in hojas_disponibles:
                st.error(f"❌ {participante}: No tiene la pestaña '{HOJA_ELIMINATORIAS}'")
                continue
            if HOJA_FINAL not in hojas_disponibles:
                st.error(f"❌ {participante}: No tiene la pestaña '{HOJA_FINAL}'")
                continue
            
            # Leer cada pestaña sin encabezado (header=None) para usar índices
            df_grupos = pd.read_excel(xls, sheet_name=HOJA_GRUPOS, header=None)
            df_elim = pd.read_excel(xls, sheet_name=HOJA_ELIMINATORIAS, header=None)
            df_final = pd.read_excel(xls, sheet_name=HOJA_FINAL, header=None)
            
            # --- Parsear fase de grupos ---
            apuestas_grupos = parsear_grupos(df_grupos, participante)
            todas_apuestas_grupos.append(apuestas_grupos)
            
            # --- Parsear eliminatorias ---
            pred_elim = parsear_eliminatorias(df_elim, df_final, participante)
            todas_predicciones_elim.append(pred_elim)
            
            # --- Parsear categorías especiales ---
            categorias = parsear_categorias_especiales(df_final, participante)
            todas_categorias[participante] = categorias
            
            # Extraer campeón predicho (ganador de M104)
            final_pred = pred_elim[pred_elim["partido_id"] == "M104"]
            if not final_pred.empty:
                campeon = final_pred.iloc[0]["ganador_pred"]
                todas_categorias[participante]["Campeon"] = campeon
            
            st.success(f"✅ {participante}: cargado correctamente")
            
        except Exception as e:
            st.error(f"❌ Error leyendo archivo de {participante}: {e}")
            continue
    
    # Concatenar todos los DataFrames
    df_grupos_total = (
        pd.concat(todas_apuestas_grupos, ignore_index=True) 
        if todas_apuestas_grupos else pd.DataFrame()
    )
    df_elim_total = (
        pd.concat(todas_predicciones_elim, ignore_index=True) 
        if todas_predicciones_elim else pd.DataFrame()
    )
    
    return df_grupos_total, df_elim_total, todas_categorias


def obtener_equipos_predichos_por_ronda(
    df_elim: pd.DataFrame,
    participante: str
) -> Dict[str, set]:
    """
    Extrae los equipos que un participante predice en cada ronda.
    
    Esto es clave para el cálculo de puntos: se otorgan puntos por cada
    equipo que el participante predijo correctamente que avanzaría a esa ronda.
    
    Retorna: Dict {ronda: set(equipos)}
    """
    pred = df_elim[df_elim["participante"] == participante]
    
    equipos_por_ronda = {}
    
    for ronda in ["16vos", "8vos", "4tos", "semis", "3ero", "final"]:
        partidos_ronda = pred[pred["ronda"] == ronda]
        equipos = set()
        
        for _, partido in partidos_ronda.iterrows():
            eq1 = partido.get("equipo1", "")
            eq2 = partido.get("equipo2", "")
            if eq1:
                equipos.add(eq1)
            if eq2:
                equipos.add(eq2)
        
        equipos_por_ronda[ronda] = equipos
    
    return equipos_por_ronda
