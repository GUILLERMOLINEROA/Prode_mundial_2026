# =============================================================================
# utils/scoring.py
# Módulo central que implementa TODO el sistema de puntuación del PRODE.
#
# Sistema de puntuación (del Excel oficial):
#
# FASE DE GRUPOS (máx 240 pts):
#   - Acertar ganador (o empate): 1 punto (x104 partidos = 104 máx)
#   - Acertar resultado exacto: 1 punto adicional (x104 = 104 máx)
#
# FASE DE PLAYOFFS (máx 273 pts):
#   - 16vos: 1 pto por equipo que avanza (x32 = 32 máx)
#   - 8vos: 4 pts por equipo (x16 = 64 máx)
#   - 4tos: 8 pts por equipo (x8 = 64 máx)
#   - Semis: 15 pts por equipo (x4 = 60 máx)
#   - Final: 25 pts por equipo (x2 = 50 máx)
#   - 3er puesto: 5 pts (x1 = 5 máx)
#   - Campeón: 30 pts (x1 = 30 máx)
#
# PUNTOS EXTRA (máx 64 pts):
#   - Figura: 12 pts
#   - Goleador: 12 pts
#   - Revelación: 12 pts
#   - Decepción: 12 pts
#   - Mejor 1era Fase: 8 pts
#   - Peor Equipo: 8 pts
#
# PENALIDADES:
#   - Revelación se queda en grupos: -20
#   - Campeón no llega a 4tos: -20
#   - Peor equipo pasa de grupos: -10
#   - Decepción llega a Semis: -20
#
# TOTAL MÁXIMO POSIBLE: 577 puntos
# =============================================================================

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


# --- Constantes de puntuación (del Excel oficial) [1] ---
PUNTOS = {
    # Fase de grupos
    "grupos_ganador": 1,
    "grupos_exacto": 1,
    
    # Eliminatorias — puntos por equipo que avanza correctamente
    "16vos": 1,
    "8vos": 4,
    "4tos": 8,
    "semis": 15,
    "final": 25,
    "3ero": 5,
    "campeon": 30,
    
    # Categorías especiales
    "Figura": 12,
    "Goleador": 12,
    "Revelación": 12,
    "Decepción": 12,
    "Mejor 1era Fase": 8,
    "Peor Equipo": 8,
}

PENALIDADES = {
    "revelacion_queda_grupos": -20,
    "campeon_no_llega_4tos": -20,
    "peor_pasa_grupos": -10,
    "decepcion_llega_semis": -20,
}


# =============================================================================
# FASE DE GRUPOS
# =============================================================================

def _determinar_resultado(goles_local: int, goles_visitante: int) -> str:
    """
    Determina el resultado de un partido.
    Retorna: 'local', 'visitante', o 'empate'.
    """
    if goles_local > goles_visitante:
        return "local"
    elif goles_local < goles_visitante:
        return "visitante"
    else:
        return "empate"


def calcular_puntos_grupos(
    apuestas_grupos: pd.DataFrame,
    resultados_reales: pd.DataFrame,
    participante: str
) -> Tuple[int, pd.DataFrame]:
    """
    Calcula los puntos de fase de grupos para un participante.
    
    Compara cada apuesta contra el resultado real:
    - 1 punto si acertó el ganador (o empate)
    - 1 punto adicional si acertó el resultado exacto
    
    Parámetros:
        apuestas_grupos: DataFrame con las apuestas (del excel_reader)
        resultados_reales: DataFrame con resultados de la API
        participante: Nombre del participante
    
    Retorna:
        Tupla (puntos_totales, DataFrame_detalle_por_partido)
    """
    # Filtrar apuestas del participante
    apuestas = apuestas_grupos[
        apuestas_grupos["participante"] == participante
    ].copy()
    
    if apuestas.empty:
        return 0, pd.DataFrame()
    
    puntos_total = 0
    detalles = []
    
    for _, apuesta in apuestas.iterrows():
        local = apuesta["equipo_local"]
        visitante = apuesta["equipo_visitante"]
        g_pred_l = apuesta["goles_local_pred"]
        g_pred_v = apuesta["goles_visitante_pred"]
        
        # Buscar resultado real por equipos
        resultado = resultados_reales[
            (resultados_reales["equipo_local"] == local) &
            (resultados_reales["equipo_visitante"] == visitante) &
            (resultados_reales["estado"] == "FT")
        ]
        
        if resultado.empty:
            # Partido no jugado aún
            detalles.append({
                "partido_id": apuesta["partido_id"],
                "grupo": apuesta.get("grupo", ""),
                "equipo_local": local,
                "equipo_visitante": visitante,
                "pred_local": g_pred_l,
                "pred_visitante": g_pred_v,
                "real_local": None,
                "real_visitante": None,
                "acierto_ganador": False,
                "acierto_exacto": False,
                "puntos": 0,
                "estado": "pendiente",
            })
            continue
        
        res = resultado.iloc[0]
        g_real_l = int(res["goles_local"])
        g_real_v = int(res["goles_visitante"])
        
        # ¿Acertó el ganador?
        resultado_real = _determinar_resultado(g_real_l, g_real_v)
        resultado_pred = _determinar_resultado(g_pred_l, g_pred_v) if (
            g_pred_l is not None and g_pred_v is not None
        ) else None
        
        acierto_ganador = (resultado_real == resultado_pred) if resultado_pred else False
        
        # ¿Acertó el resultado exacto?
        acierto_exacto = (
            g_pred_l is not None and g_pred_v is not None and
            g_pred_l == g_real_l and g_pred_v == g_real_v
        )
        
        # Sumar puntos
        pts = 0
        if acierto_ganador:
            pts += PUNTOS["grupos_ganador"]
        if acierto_exacto:
            pts += PUNTOS["grupos_exacto"]
        
        puntos_total += pts
        
        detalles.append({
            "partido_id": apuesta["partido_id"],
            "grupo": apuesta.get("grupo", ""),
            "equipo_local": local,
            "equipo_visitante": visitante,
            "pred_local": g_pred_l,
            "pred_visitante": g_pred_v,
            "real_local": g_real_l,
            "real_visitante": g_real_v,
            "acierto_ganador": acierto_ganador,
            "acierto_exacto": acierto_exacto,
            "puntos": pts,
            "estado": "jugado",
        })
    
    return puntos_total, pd.DataFrame(detalles)


# =============================================================================
# ELIMINATORIAS
# =============================================================================

def calcular_puntos_eliminatorias(
    pred_elim: pd.DataFrame,
    equipos_reales_por_ronda: Dict[str, set],
    participante: str
) -> Tuple[int, Dict[str, int], List[dict]]:
    """
    Calcula los puntos de eliminatorias para un participante.
    
    La lógica es: por cada equipo que el participante predijo en una ronda
    Y que efectivamente participó en esa ronda en la realidad → suma puntos.
    
    Parámetros:
        pred_elim: DataFrame con predicciones de eliminatorias
        equipos_reales_por_ronda: Dict {ronda: set(equipos_que_jugaron)}
        participante: Nombre del participante
    
    Retorna:
        Tupla (puntos_totales, dict_puntos_por_ronda, lista_detalles)
    """
    from utils.excel_reader import obtener_equipos_predichos_por_ronda
    
    equipos_pred = obtener_equipos_predichos_por_ronda(pred_elim, participante)
    
    puntos_total = 0
    puntos_por_ronda = {}
    detalles = []
    
    for ronda, pts_valor in [
        ("16vos", PUNTOS["16vos"]),
        ("8vos", PUNTOS["8vos"]),
        ("4tos", PUNTOS["4tos"]),
        ("semis", PUNTOS["semis"]),
        ("final", PUNTOS["final"]),
    ]:
        equipos_predichos = equipos_pred.get(ronda, set())
        equipos_reales = equipos_reales_por_ronda.get(ronda, set())
        
        aciertos = equipos_predichos & equipos_reales  # Intersección
        pts_ronda = len(aciertos) * pts_valor
        
        puntos_por_ronda[ronda] = pts_ronda
        puntos_total += pts_ronda
        
        for equipo in equipos_predichos:
            acerto = equipo in equipos_reales
            detalles.append({
                "ronda": ronda,
                "equipo": equipo,
                "acerto": acerto,
                "puntos": pts_valor if acerto else 0,
            })
    
    return puntos_total, puntos_por_ronda, detalles


def calcular_puntos_campeon_y_tercero(
    pred_elim: pd.DataFrame,
    campeon_real: str,
    tercero_real: str,
    participante: str
) -> Tuple[int, int]:
    """
    Calcula puntos por acertar campeón y tercer puesto.
    
    Retorna: (pts_campeon, pts_tercero)
    """
    pred = pred_elim[pred_elim["participante"] == participante]
    
    pts_campeon = 0
    pts_tercero = 0
    
    # Buscar predicción de la final (M104)
    final_pred = pred[pred["partido_id"] == "M104"]
    if not final_pred.empty and campeon_real:
        ganador_pred = final_pred.iloc[0].get("ganador_pred", "")
        if ganador_pred == campeon_real:
            pts_campeon = PUNTOS["campeon"]
    
    # Buscar predicción del 3er puesto (M103)
    tercero_pred = pred[pred["partido_id"] == "M103"]
    if not tercero_pred.empty and tercero_real:
        ganador_pred_3 = tercero_pred.iloc[0].get("ganador_pred", "")
        if ganador_pred_3 == tercero_real:
            pts_tercero = PUNTOS["3ero"]
    
    return pts_campeon, pts_tercero


# =============================================================================
# CATEGORÍAS ESPECIALES
# =============================================================================

def calcular_puntos_categorias(
    categorias_pred: Dict[str, str],
    categorias_reales: Dict[str, str]
) -> Tuple[int, Dict[str, bool]]:
    """
    Calcula puntos de categorías especiales.
    Compara predicción vs. realidad para cada categoría.
    
    Retorna: (puntos_totales, dict_aciertos)
    """
    puntos = 0
    aciertos = {}
    
    for cat in ["Figura", "Goleador", "Revelación", "Decepción", "Mejor 1era Fase", "Peor Equipo"]:
        pred = categorias_pred.get(cat, "").strip()
        real = categorias_reales.get(cat, "").strip()
        
        if pred and real and pred.lower() == real.lower():
            puntos += PUNTOS[cat]
            aciertos[cat] = True
        else:
            aciertos[cat] = False
    
    return puntos, aciertos


# =============================================================================
# PENALIDADES
# =============================================================================

def calcular_penalidades(
    categorias_pred: Dict[str, str],
    pred_elim: pd.DataFrame,
    equipos_reales_por_ronda: Dict[str, set],
    participante: str
) -> Tuple[int, List[str]]:
    """
    Calcula las penalidades según las reglas del PRODE [1]:
    
    1. Revelación se queda en grupos: -20
       (Tu revelación predicha no pasó de fase de grupos en la realidad)
    
    2. Campeón predicho no llega a 4tos: -20
       (Tu campeón ni siquiera llegó a cuartos de final)
    
    3. Peor equipo predicho pasa de grupos: -10
       (Tu "peor equipo" resultó pasar de grupos)
    
    4. Decepción predicha llega a semis: -20
       (Tu "decepción" llegó a semifinales — no tan decepción, ¿eh?)
    
    Retorna: (puntos_negativos, lista_razones)
    """
    penalidad_total = 0
    razones = []
    
    # Equipos que pasaron de grupos (están en 16vos)
    equipos_16vos = equipos_reales_por_ronda.get("16vos", set())
    equipos_4tos = equipos_reales_por_ronda.get("4tos", set())
    equipos_semis = equipos_reales_por_ronda.get("semis", set())
    
    # Solo aplicar penalidades si la ronda ya se jugó
    # (si el set está vacío, la ronda no se jugó aún)
    
    # 1. Revelación se queda en grupos
    revelacion = categorias_pred.get("Revelación", "").strip()
    if revelacion and equipos_16vos:
        if revelacion not in equipos_16vos:
            penalidad_total += PENALIDADES["revelacion_queda_grupos"]
            razones.append(
                f"🪦 Tu revelación ({revelacion}) se quedó en grupos: "
                f"{PENALIDADES['revelacion_queda_grupos']} pts"
            )
    
    # 2. Campeón no llega a 4tos
    campeon_pred = categorias_pred.get("Campeon", "").strip()
    if campeon_pred and equipos_4tos:
        if campeon_pred not in equipos_4tos:
            penalidad_total += PENALIDADES["campeon_no_llega_4tos"]
            razones.append(
                f"💀 Tu campeón ({campeon_pred}) no llegó ni a cuartos: "
                f"{PENALIDADES['campeon_no_llega_4tos']} pts"
            )
    
    # 3. Peor equipo pasa de grupos
    peor = categorias_pred.get("Peor Equipo", "").strip()
    if peor and equipos_16vos:
        if peor in equipos_16vos:
            penalidad_total += PENALIDADES["peor_pasa_grupos"]
            razones.append(
                f"😂 Tu 'peor equipo' ({peor}) pasó de grupos: "
                f"{PENALIDADES['peor_pasa_grupos']} pts"
            )
    
    # 4. Decepción llega a semis
    decepcion = categorias_pred.get("Decepción", "").strip()
    if decepcion and equipos_semis:
        if decepcion in equipos_semis:
            penalidad_total += PENALIDADES["decepcion_llega_semis"]
            razones.append(
                f"🤡 Tu decepción ({decepcion}) llegó a SEMIS: "
                f"{PENALIDADES['decepcion_llega_semis']} pts"
            )
    
    return penalidad_total, razones


# =============================================================================
# FUNCIÓN MAESTRA: PUNTUACIÓN TOTAL
# =============================================================================

def calcular_puntuacion_total(
    participante: str,
    apuestas_grupos: pd.DataFrame,
    pred_elim: pd.DataFrame,
    categorias_pred: Dict[str, str],
    resultados_reales: pd.DataFrame,
    equipos_reales_por_ronda: Dict[str, set],
    categorias_reales: Dict[str, str],
    campeon_real: str = "",
    tercero_real: str = "",
) -> Dict:
    """
    Función maestra que calcula la puntuación TOTAL de un participante.
    Agrega todos los componentes y retorna un diccionario con el desglose.
    
    Máximo teórico: 577 puntos [1]
    """
    # 1. Fase de grupos
    pts_grupos, detalle_grupos = calcular_puntos_grupos(
        apuestas_grupos, resultados_reales, participante
    )
    
    # 2. Eliminatorias (equipos que avanzan)
    pts_elim, pts_por_ronda, detalles_elim = calcular_puntos_eliminatorias(
        pred_elim, equipos_reales_por_ronda, participante
    )
    
    # 3. Campeón y 3er puesto
    pts_campeon, pts_tercero = calcular_puntos_campeon_y_tercero(
        pred_elim, campeon_real, tercero_real, participante
    )
    
    # 4. Categorías especiales
    pts_especiales, aciertos_esp = calcular_puntos_categorias(
        categorias_pred, categorias_reales
    )
    
    # 5. Penalidades
    pts_penalidades, razones_penalidad = calcular_penalidades(
        categorias_pred, pred_elim, equipos_reales_por_ronda, participante
    )
    
    # TOTAL
    total = (
        pts_grupos + pts_elim + pts_campeon + pts_tercero +
        pts_especiales + pts_penalidades
    )
    
    return {
        "participante": participante,
        "total": total,
        "pts_grupos": pts_grupos,
        "pts_eliminatorias": pts_elim,
        "pts_campeon": pts_campeon,
        "pts_tercero": pts_tercero,
        "pts_especiales": pts_especiales,
        "pts_penalidades": pts_penalidades,
        "detalle_grupos": detalle_grupos,
        "detalles_elim": detalles_elim,
        "pts_por_ronda_elim": pts_por_ronda,
        "aciertos_especiales": aciertos_esp,
        "razones_penalidad": razones_penalidad,
        "categorias": categorias_pred,
    }


# =============================================================================
# LEADERBOARD
# =============================================================================

def generar_leaderboard(todos_los_puntajes: List[Dict]) -> pd.DataFrame:
    """
    Genera el leaderboard completo ordenado por puntos.
    
    Desempate [1]:
    1. Total de puntos (mayor es mejor)
    2. Puntos en fase de grupos (mayor es mejor)
    3. Ranking FIFA del campeón predicho (peor ranking = más arriba)
    """
    datos = []
    for p in todos_los_puntajes:
        datos.append({
            "Posición": 0,
            "Participante": p["participante"],
            "Total": p["total"],
            "Grupos": p["pts_grupos"],
            "Eliminatorias": p["pts_eliminatorias"],
            "Campeón": p["pts_campeon"],
            "3ero": p["pts_tercero"],
            "Especiales": p["pts_especiales"],
            "Penalidades": p["pts_penalidades"],
        })
    
    df = pd.DataFrame(datos)
    
    # Ordenar: total desc, luego grupos desc (desempate)
    df = df.sort_values(
        by=["Total", "Grupos"],
        ascending=[False, False]
    ).reset_index(drop=True)
    
    # Asignar posiciones
    df["Posición"] = range(1, len(df) + 1)
    
    # Reordenar columnas
    cols = [
        "Posición", "Participante", "Total", "Grupos",
        "Eliminatorias", "Campeón", "3ero", "Especiales", "Penalidades"
    ]
    df = df[cols]
    
    return df
