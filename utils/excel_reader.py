# =============================================================================
# utils/excel_reader.py
# Módulo encargado de leer y parsear el archivo Excel (.xlsm) del PRODE.
#
# El Excel tiene múltiples hojas con las apuestas de cada participante.
# Este módulo extrae:
# - Las apuestas de cada participante para cada partido (fase de grupos)
# - Las predicciones de eliminatorias (quién avanza en cada ronda)
# - Las categorías especiales (Figura, Goleador, Revelación, etc.)
# =============================================================================

import pandas as pd
import streamlit as st
import os
from typing import Dict, List, Tuple, Optional


# --- Ruta por defecto del archivo Excel ---
DEFAULT_EXCEL_PATH = os.path.join("data", "prode.xlsm")


@st.cache_data
def cargar_excel(ruta: str = DEFAULT_EXCEL_PATH) -> Dict[str, pd.DataFrame]:
    """
    Carga todas las hojas del archivo Excel y las retorna como un diccionario.
    
    Retorna:
        Dict donde la clave es el nombre de la hoja y el valor es un DataFrame.
    """
    try:
        xls = pd.ExcelFile(ruta, engine="openpyxl")
        hojas = {}
        for nombre_hoja in xls.sheet_names:
            hojas[nombre_hoja] = pd.read_excel(
                xls, sheet_name=nombre_hoja, header=None
            )
        return hojas
    except FileNotFoundError:
        st.error(
            f"❌ No se encontró el archivo Excel en: `{ruta}`. "
            "Por favor, colócalo en la carpeta `data/`."
        )
        return {}
    except Exception as e:
        st.error(f"❌ Error leyendo el Excel: {e}")
        return {}


def obtener_participantes(hojas: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Identifica los nombres de los participantes a partir de las hojas del Excel.
    
    Estrategia: Cada participante tiene su propia hoja. Las hojas que NO son
    de participantes incluyen hojas de resumen, instrucciones, etc.
    Se filtran por convención de nombres.
    
    NOTA: Ajustar la lógica de filtrado según la estructura real del Excel.
    Las hojas de sistema típicas son: 'Inputs summary', 'Total Results',
    'Rules', 'Teams', etc.
    """
    # Hojas que NO son de participantes (ajustar según el Excel real)
    hojas_sistema = {
        "inputs summary", "total results", "rules", "teams", "config",
        "instrucciones", "resumen", "draw - select", "sheet1", "sheet2",
        "hoja1", "hoja2", "clasificacion", "fixture", "calendario"
    }
    
    participantes = []
    for nombre_hoja in hojas.keys():
        if nombre_hoja.strip().lower() not in hojas_sistema:
            participantes.append(nombre_hoja.strip())
    
    return sorted(participantes)


def parsear_apuestas_grupos(
    df_hoja: pd.DataFrame,
    nombre_participante: str
) -> pd.DataFrame:
    """
    Extrae las apuestas de fase de grupos de la hoja de un participante.
    
    Busca las filas que contienen los partidos de grupo (GA1, GA2, GB1, etc.)
    y extrae los resultados predichos.
    
    Retorna un DataFrame con columnas:
    - partido_id: Identificador del partido (ej: "GA1")
    - equipo_local: Nombre del equipo local
    - equipo_visitante: Nombre del equipo visitante
    - goles_local_pred: Goles predichos para el local
    - goles_visitante_pred: Goles predichos para el visitante
    - participante: Nombre del participante
    
    NOTA: La estructura exacta depende del layout del Excel.
    Se debe ajustar las coordenadas (fila, columna) según el archivo real.
    """
    apuestas = []
    
    # Recorrer el DataFrame buscando patrones de partido de grupo
    # Los partidos de grupo en el Excel siguen el formato "GA1", "GA2", etc.
    # donde G = Group, A-L = letra del grupo, 1-6 = número de partido
    for idx, row in df_hoja.iterrows():
        for col_idx, valor in enumerate(row):
            if isinstance(valor, str) and len(valor) >= 2:
                # Buscar celdas que parezcan IDs de partido (GA1, GB2, etc.)
                valor_limpio = valor.strip()
                if (len(valor_limpio) == 3 and 
                    valor_limpio[0] == 'G' and 
                    valor_limpio[1] in 'ABCDEFGHIJKL' and 
                    valor_limpio[2].isdigit()):
                    
                    try:
                        # Asumimos layout: ID | Equipo1 | Goles1 | Goles2 | Equipo2
                        # Ajustar offsets según el Excel real
                        equipo_local = str(df_hoja.iloc[idx, col_idx + 1]).strip() if col_idx + 1 < len(row) else ""
                        goles_local = df_hoja.iloc[idx, col_idx + 2] if col_idx + 2 < len(row) else None
                        goles_visitante = df_hoja.iloc[idx, col_idx + 3] if col_idx + 3 < len(row) else None
                        equipo_visitante = str(df_hoja.iloc[idx, col_idx + 4]).strip() if col_idx + 4 < len(row) else ""
                        
                        # Convertir goles a enteros
                        goles_local = int(goles_local) if pd.notna(goles_local) else None
                        goles_visitante = int(goles_visitante) if pd.notna(goles_visitante) else None
                        
                        apuestas.append({
                            "partido_id": valor_limpio,
                            "equipo_local": equipo_local,
                            "equipo_visitante": equipo_visitante,
                            "goles_local_pred": goles_local,
                            "goles_visitante_pred": goles_visitante,
                            "participante": nombre_participante,
                        })
                    except (IndexError, ValueError, TypeError):
                        continue
    
    return pd.DataFrame(apuestas)


def parsear_apuestas_eliminatorias(
    df_hoja: pd.DataFrame,
    nombre_participante: str
) -> pd.DataFrame:
    """
    Extrae las predicciones de eliminatorias de la hoja de un participante.
    
    En las eliminatorias, lo que importa es:
    - Quién avanza en cada ronda (16vos, 8vos, 4tos, semis, final)
    - El campeón predicho
    - El tercer lugar
    
    Retorna un DataFrame con columnas:
    - ronda: La ronda de la eliminatoria
    - match_code: Código del partido (M75, M76, etc.)
    - equipo_predicho: Equipo que el participante predice como ganador
    - participante: Nombre del participante
    """
    predicciones = []
    
    # Buscar las secciones de eliminatorias en el Excel
    # Los partidos eliminatorios tienen códigos como M75, M76, W75, W76, etc.
    for idx, row in df_hoja.iterrows():
        for col_idx, valor in enumerate(row):
            if isinstance(valor, str):
                valor_limpio = valor.strip()
                # Buscar códigos de partido tipo "M75", "M76", etc.
                if (len(valor_limpio) >= 2 and 
                    valor_limpio[0] == 'M' and 
                    valor_limpio[1:].isdigit()):
                    
                    match_num = int(valor_limpio[1:])
                    
                    # Determinar la ronda según el número de partido
                    if 75 <= match_num <= 90:
                        ronda = "16vos"
                    elif 91 <= match_num <= 98:
                        ronda = "8vos"
                    elif 99 <= match_num <= 102:
                        ronda = "4tos"
                    elif match_num in (103,):
                        ronda = "3ero"
                    elif match_num in (104,):
                        ronda = "final"
                    else:
                        ronda = "desconocida"
                    
                    # Los equipos predichos están en celdas adyacentes
                    try:
                        equipo1 = str(df_hoja.iloc[idx, col_idx + 1]).strip() if col_idx + 1 < len(row) else ""
                        equipo2 = str(df_hoja.iloc[idx, col_idx + 2]).strip() if col_idx + 2 < len(row) else ""
                        
                        if equipo1 and equipo1 != "nan":
                            predicciones.append({
                                "ronda": ronda,
                                "match_code": valor_limpio,
                                "equipo1_pred": equipo1,
                                "equipo2_pred": equipo2 if equipo2 != "nan" else "",
                                "participante": nombre_participante,
                            })
                    except (IndexError, ValueError):
                        continue
    
    return pd.DataFrame(predicciones)


def parsear_categorias_especiales(
    df_hoja: pd.DataFrame,
    nombre_participante: str
) -> Dict[str, str]:
    """
    Extrae las categorías especiales de la hoja de un participante:
    - Figura: Jugador estrella del torneo
    - Goleador: Máximo goleador predicho
    - Revelación: Equipo revelación
    - Decepción: Equipo decepción
    - Mejor 1era Fase: Mejor equipo en fase de grupos
    - Peor Equipo: Peor equipo del torneo
    
    Retorna un diccionario con cada categoría y su valor predicho.
    """
    categorias = {
        "Figura": "",
        "Goleador": "",
        "Revelación": "",
        "Decepción": "",
        "Mejor 1era Fase": "",
        "Peor Equipo": "",
    }
    
    # Buscar las etiquetas de categorías especiales en el Excel
    for idx, row in df_hoja.iterrows():
        for col_idx, valor in enumerate(row):
            if isinstance(valor, str):
                valor_limpio = valor.strip()
                for cat in categorias.keys():
                    if valor_limpio.lower() == cat.lower():
                        # El valor predicho está en la celda siguiente
                        try:
                            prediccion = str(df_hoja.iloc[idx, col_idx + 1]).strip()
                            if prediccion and prediccion != "nan":
                                categorias[cat] = prediccion
                        except (IndexError, ValueError):
                            pass
    
    return categorias


def cargar_todas_las_apuestas(
    ruta_excel: str = DEFAULT_EXCEL_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, str]]]:
    """
    Función principal que carga y procesa TODAS las apuestas de TODOS
    los participantes.
    
    Retorna una tupla con:
    1. DataFrame con todas las apuestas de fase de grupos
    2. DataFrame con todas las predicciones de eliminatorias
    3. Diccionario {participante: {categoría: valor}} con categorías especiales
    """
    hojas = cargar_excel(ruta_excel)
    if not hojas:
        return pd.DataFrame(), pd.DataFrame(), {}
    
    participantes = obtener_participantes(hojas)
    
    todas_grupos = []
    todas_eliminatorias = []
    todas_categorias = {}
    
    for nombre in participantes:
        df_hoja = hojas[nombre]
        
        # Parsear apuestas de fase de grupos
        apuestas_grupos = parsear_apuestas_grupos(df_hoja, nombre)
        todas_grupos.append(apuestas_grupos)
        
        # Parsear predicciones de eliminatorias
        pred_elim = parsear_apuestas_eliminatorias(df_hoja, nombre)
        todas_eliminatorias.append(pred_elim)
        
        # Parsear categorías especiales
        categorias = parsear_categorias_especiales(df_hoja, nombre)
        todas_categorias[nombre] = categorias
    
    df_grupos = pd.concat(todas_grupos, ignore_index=True) if todas_grupos else pd.DataFrame()
    df_elim = pd.concat(todas_eliminatorias, ignore_index=True) if todas_eliminatorias else pd.DataFrame()
    
    return df_grupos, df_elim, todas_categorias
