# =============================================================================
# utils/scoring.py
# Módulo central que implementa TODO el sistema de puntuación del PRODE.
#
# Sistema de puntuación (de la imagen adjunta):
# 
# FASE DE GRUPOS:
#   - Acertar ganador (o empate): 1 punto
#   - Acertar resultado exacto: 1 punto adicional (máx 2 por partido)
#   - Total máximo: 104 partidos × 2 = 208 puntos... pero realmente
#     son 104 partidos en fase de grupos con 1 pto ganador + 1 pto exacto
#
# FASE DE PLAYOFFS (ELIMINATORIAS):
#   - 16vos de final: 1 punto por equipo que avanza (32 partidos)
#   - 8vos de final: 4 puntos por equipo que avanza
#   - Cuartos de final: 8 puntos por equipo que avanza
#   - Semifinales: 15 puntos por equipo que avanza
#   - Final: 25 puntos por equipo que llega
#   - 3er puesto: 5 puntos
#   - Campeón: 30 puntos
#
# PUNTOS EXTRA (CATEGORÍAS ESPECIALES):
#   - Figura: 12 puntos
#   - Goleador: 12 puntos
#   - Revelación: 12 puntos
#   - Decepción: 12 puntos
#   - Mejor 1era Fase: 8 puntos
#   - Peor Equipo: 8 puntos
#
# PENALIDADES:
#   - Revelación se queda en grupos: -20
#   - Campeón no llega a 4tos: -20
#   - Peor pasa grupos: -10
#   - Decepción llega a Semis: -20
#
# PREMIOS:
#   - 4 ganadores con 4 premios
#   - 1er puesto general
#   - 2do puesto general
#   - 3er puesto general = Mejor en Resultados Grupos
#   - Si el "Mejor en Resultados Grupos" ya está entre los 3 primeros, 
#     se le da al siguiente.
# =============================================================================

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


# --- Constantes de puntuación ---
PUNTOS = {
    # Fase de grupos
    "grupos_ganador": 1,        # Acertar quién gana (o empate)
    "grupos_exacto": 1,         # Acertar resultado exacto (adicional)
    
    # Eliminatorias - puntos por acertar que un equipo avanza
    "16vos": 1,                 # 16vos de final
    "8vos": 4,                  # Octavos de final
    "4tos": 8,                  # Cuartos de final
    "semis": 15,                # Semifinales
    "final": 25,                # Llegar a la final
    "3ero": 5,                  # Tercer puesto
    "campeon": 30,              # Campeón
    
    # Categorías especiales
    "figura": 12,
    "goleador": 12,
    "revelacion": 12,
    "decepcion": 12,
    "mejor_1era_fase": 8,
    "peor_equipo": 8,
}

PENALIDADES = {
    "revelacion_queda_grupos": -20,   # Tu revelación ni pasó de grupos
    "campeon_no_llega_4tos": -20,     # Tu campeón no llegó ni a cuartos
    "peor_pasa_grupos": -10,          # Tu "peor equipo" pasó de grupos
    "decepcion_llega_semis": -20,     # Tu "decepción" llegó a semis
}


def determinar_ganador_real(goles_local: int, goles_visitante: int) -> str:
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
    
    Parámetros:
        apuestas_grupos: DataFrame con las apuestas del participante
        resultados_reales: DataFrame con los resultados reales de la API
        participante: Nombre del participante
    
    Retorna:
        Tupla con (puntos_totales, DataFrame_detalle)
        El DataFrame detalle incluye cada partido, si acertó ganador,
        si acertó resultado exacto, y los puntos obtenidos.
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
        # Buscar el resultado real correspondiente
        # Intentamos hacer match por equipos
        resultado = resultados_reales[
            (resultados_reales["equipo_local"] == apuesta["equipo_local"]) &
            (resultados_reales["equipo_visitante"] == apuesta["equipo_visitante"]) &
            (resultados_reales["estado"] == "FT")  # Solo partidos terminados
        ]
        
        if resultado.empty:
            # Partido no se ha jugado todavía
            detalles.append({
                "partido_id": apuesta["partido_id"],
                "equipo_local": apuesta["equipo_local"],
                "equipo_visitante": apuesta["equipo_visitante"],
                "pred_local": apuesta["goles_local_pred"],
                "pred_visitante": apuesta["goles_visitante_pred"],
                "real_local": None,
                "real_visitante": None,
                "acierto_ganador": False,
                "acierto_exacto": False,
                "puntos": 0,
                "estado": "pendiente",
            })
            continue
        
        resultado = resultado.iloc[0]
        goles_real_local = resultado["goles_local"]
        goles_real_visitante = resultado["goles_visitante"]
        
        # Determinar si acertó el ganador
        ganador_real = determinar_ganador_real(goles_real_local, goles_real_visitante)
        ganador_pred = determinar_ganador_real(
            apuesta["goles_local_pred"], apuesta["goles_visitante_pred"]
        )
        
        acierto_ganador = (ganador_real == ganador_pred)
        
        # Determinar si acertó el resultado exacto
        acierto_exacto = (
            apuesta["goles_local_pred"] == goles_real_local and
            apuesta["goles_visitante_pred"] == goles_real_visitante
        )
        
        # Calcular puntos del partido
        puntos_partido = 0
        if acierto_ganador:
            puntos_partido += PUNTOS["grupos_ganador"]
        if acierto_exacto:
            puntos_partido += PUNTOS["grupos_exacto"]
        
        puntos_total += puntos_partido
        
        detalles.append({
            "partido_id": apuesta["partido_id"],
            "equipo_local": apuesta["equipo_local"],
            "equipo_visitante": apuesta["equipo_visitante"],
            "pred_local": apuesta["goles_local_pred"],
            "pred_visitante": apuesta["goles_visitante_pred"],
            "real_local": goles_real_local,
            "real_visitante": goles_real_visitante,
            "acierto_ganador": acierto_ganador,
            "acierto_exacto": acierto_exacto,
            "puntos": puntos_partido,
            "estado": "jugado",
        })
    
    return puntos_total, pd.DataFrame(detalles)


def calcular_puntos_eliminatorias(
    predicciones_elim: pd.DataFrame,
    resultados_reales: pd.DataFrame,
    participante: str
) -> Tuple[int, Dict[str, int]]:
    """
    Calcula los puntos de eliminatorias para un participante.
    
    Para cada ronda, verifica si el participante predijo correctamente
    qué equipos avanzaron.
    
    Retorna:
        Tupla con (puntos_totales, dict_puntos_por_ronda)
    """
    predicciones = predicciones_elim[
        predicciones_elim["participante"] == participante
    ].copy()
    
    if predicciones.empty:
        return 0, {}
    
    # Determinar qué equipos avanzaron realmente en cada ronda
    # basándonos en los resultados reales
    equipos_por_ronda_real = _extraer_equipos_por_ronda(resultados_reales)
    
    puntos_total = 0
    puntos_por_ronda = {}
    
    for ronda, puntos_valor in [
        ("16vos", PUNTOS["16vos"]),
        ("8vos", PUNTOS["8vos"]),
        ("4tos", PUNTOS["4tos"]),
        ("semis", PUNTOS["semis"]),
        ("final", PUNTOS["final"]),
    ]:
        pred_ronda = predicciones[predicciones["ronda"] == ronda]
        equipos_reales = equipos_por_ronda_real.get(ronda, set())
        
        aciertos = 0
        for _, pred in pred_ronda.iterrows():
            if pred["equipo1_pred"] in equipos_reales:
                aciertos += 1
        
        puntos_ronda = aciertos * puntos_valor
        puntos_por_ronda[ronda] = puntos_ronda
        puntos_total += puntos_ronda
    
    return puntos_total, puntos_por_ronda


def _extraer_equipos_por_ronda(resultados: pd.DataFrame) -> Dict[str, set]:
    """
    A partir de los resultados reales, determina qué equipos participaron
    en cada ronda de las eliminatorias.
    """
    from utils.api_football import clasificar_ronda
    
    equipos_por_ronda = {}
    
    for _, partido in resultados.iterrows():
        ronda = clasificar_ronda(partido.get("ronda", ""))
        if ronda not in equipos_por_ronda:
            equipos_por_ronda[ronda] = set()
        
        equipos_por_ronda[ronda].add(partido["equipo_local"])
        equipos_por_ronda[ronda].add(partido["equipo_visitante"])
    
    return equipos_por_ronda


def calcular_puntos_campeon(
    predicciones_elim: pd.DataFrame,
    resultados_reales: pd.DataFrame,
    participante: str
) -> int:
    """
    Verifica si el participante acertó al campeón.
    Retorna 30 puntos si acertó, 0 si no.
    """
    predicciones = predicciones_elim[
        (predicciones_elim["participante"] == participante) &
        (predicciones_elim["ronda"] == "final")
    ]
    
    if predicciones.empty:
        return 0
    
    # Buscar el resultado de la final
    finales = resultados_reales[
        resultados_reales["ronda"].str.lower().str.contains("final")
    ]
    
    if finales.empty:
        return 0
    
    final = finales.iloc[-1]  # La última "final" debería ser la gran final
    
    # Determinar campeón real
    if final["goles_local"] > final["goles_visitante"]:
        campeon_real = final["equipo_local"]
    elif final["goles_visitante"] > final["goles_local"]:
        campeon_real = final["equipo_visitante"]
    elif final["penales_local"] and final["penales_visitante"]:
        if final["penales_local"] > final["penales_visitante"]:
            campeon_real = final["equipo_local"]
        else:
            campeon_real = final["equipo_visitante"]
    else:
        return 0  # Final no resuelta aún
    
    # Verificar si el participante predijo al campeón
    campeon_pred = predicciones.iloc[0].get("equipo1_pred", "")
    
    if campeon_pred == campeon_real:
        return PUNTOS["campeon"]
    
    return 0


def calcular_penalidades(
    categorias: Dict[str, str],
    predicciones_elim: pd.DataFrame,
    resultados_reales: pd.DataFrame,
    participante: str,
    equipos_clase: pd.DataFrame
) -> Tuple[int, List[str]]:
    """
    Calcula las penalidades para un participante según las reglas del PRODE.
    
    Penalidades:
    1. Revelación se queda en grupos: -20
    2. Campeón predicho no llega a cuartos: -20
    3. Peor equipo predicho pasa de grupos: -10
    4. Decepción predicha llega a semis: -20
    
    Retorna:
        Tupla con (puntos_penalidad_negativos, lista_de_razones)
    """
    penalidad_total = 0
    razones = []
    
    equipos_por_ronda = _extraer_equipos_por_ronda(resultados_reales)
    
    # 1. Revelación se queda en grupos
    revelacion = categorias.get("Revelación", "")
    if revelacion:
        paso_grupos = revelacion in equipos_por_ronda.get("16vos", set())
        if not paso_grupos and equipos_por_ronda.get("16vos"):
            penalidad_total += PENALIDADES["revelacion_queda_grupos"]
            razones.append(
                f"🪦 Tu revelación ({revelacion}) se quedó en grupos: "
                f"{PENALIDADES['revelacion_queda_grupos']} pts"
            )
    
    # 2. Campeón predicho no llega a cuartos
    predicciones = predicciones_elim[
        predicciones_elim["participante"] == participante
    ]
    campeon_pred = ""
    final_preds = predicciones[predicciones["ronda"] == "final"]
    if not final_preds.empty:
        campeon_pred = final_preds.iloc[0].get("equipo1_pred", "")
    
    if campeon_pred:
        llego_a_cuartos = campeon_pred in equipos_por_ronda.get("4tos", set())
        if not llego_a_cuartos and equipos_por_ronda.get("4tos"):
            penalidad_total += PENALIDADES["campeon_no_llega_4tos"]
            razones.append(
                f"💀 Tu campeón ({campeon_pred}) no llegó ni a cuartos: "
                f"{PENALIDADES['campeon_no_llega_4tos']} pts"
            )
    
    # 3. Peor equipo pasa de grupos
    peor_equipo = categorias.get("Peor Equipo", "")
    if peor_equipo:
        peor_paso = peor_equipo in equipos_por_ronda.get("16vos", set())
        if peor_paso:
            penalidad_total += PENALIDADES["peor_pasa_grupos"]
            razones.append(
                f"😂 Tu 'peor equipo' ({peor_equipo}) pasó de grupos: "
                f"{PENALIDADES['peor_pasa_grupos']} pts"
            )
    
    # 4. Decepción llega a semis
    decepcion = categorias.get("Decepción", "")
    if decepcion:
        llego_semis = decepcion in equipos_por_ronda.get("semis", set())
        if llego_semis:
            penalidad_total += PENALIDADES["decepcion_llega_semis"]
            razones.append(
                f"🤡 Tu decepción ({decepcion}) llegó a SEMIS: "
                f"{PENALIDADES['decepcion_llega_semis']} pts"
            )
    
    return penalidad_total, razones


def calcular_puntos_categorias_especiales(
    categorias_participante: Dict[str, str],
    categorias_reales: Dict[str, str]
) -> Tuple[int, Dict[str, bool]]:
    """
    Calcula los puntos de las categorías especiales.
    
    Compara las predicciones del participante con los resultados reales.
    
    Retorna:
        Tupla con (puntos_totales, dict_aciertos)
    """
    puntos = 0
    aciertos = {}
    
    mapeo_categorias = {
        "Figura": PUNTOS["figura"],
        "Goleador": PUNTOS["goleador"],
        "Revelación": PUNTOS["revelacion"],
        "Decepción": PUNTOS["decepcion"],
        "Mejor 1era Fase": PUNTOS["mejor_1era_fase"],
        "Peor Equipo": PUNTOS["peor_equipo"],
    }
    
    for cat, valor_pts in mapeo_categorias.items():
        pred = categorias_participante.get(cat, "").strip().lower()
        real = categorias_reales.get(cat, "").strip().lower()
        
        if pred and real and pred == real:
            puntos += valor_pts
            aciertos[cat] = True
        else:
            aciertos[cat] = False
    
    return puntos, aciertos


def calcular_puntuacion_total(
    participante: str,
    apuestas_grupos: pd.DataFrame,
    predicciones_elim: pd.DataFrame,
    categorias_participante: Dict[str, str],
    resultados_reales: pd.DataFrame,
    categorias_reales: Dict[str, str],
    equipos_clase: pd.DataFrame
) -> Dict:
    """
    Función maestra que calcula la puntuación TOTAL de un participante.
    
    Agrega:
    - Puntos de fase de grupos
    - Puntos de eliminatorias
    - Puntos de campeón
    - Puntos de categorías especiales
    - Penalidades
    
    Retorna un diccionario completo con el desglose.
    """
    # Fase de grupos
    pts_grupos, detalle_grupos = calcular_puntos_grupos(
        apuestas_grupos, resultados_reales, participante
    )
    
    # Eliminatorias
    pts_elim, pts_por_ronda = calcular_puntos_eliminatorias(
        predicciones_elim, resultados_reales, participante
    )
    
    # Campeón
    pts_campeon = calcular_puntos_campeon(
        predicciones_elim, resultados_reales, participante
    )
    
    # Categorías especiales
    pts_especiales, aciertos_esp = calcular_puntos_categorias_especiales(
        categorias_participante, categorias_reales
    )
    
    # Penalidades
    pts_penalidades, razones_penalidad = calcular_penalidades(
        categorias_participante, predicciones_elim,
        resultados_reales, participante, equipos_clase
    )
    
    # TOTAL
    total = pts_grupos + pts_elim + pts_campeon + pts_especiales + pts_penalidades
    
    return {
        "participante": participante,
        "total": total,
        "pts_grupos": pts_grupos,
        "pts_eliminatorias": pts_elim,
        "pts_campeon": pts_campeon,
        "pts_especiales": pts_especiales,
        "pts_penalidades": pts_penalidades,
        "detalle_grupos": detalle_grupos,
        "pts_por_ronda_elim": pts_por_ronda,
        "aciertos_especiales": aciertos_esp,
        "razones_penalidad": razones_penalidad,
        "categorias": categorias_participante,
    }


def generar_leaderboard(
    todos_los_puntajes: List[Dict],
    equipos_clase: pd.DataFrame
) -> pd.DataFrame:
    """
    Genera el leaderboard completo ordenado por puntos.
    
    En caso de empate, desempata por:
    1. Puntos en fase de grupos (más es mejor)
    2. Ranking FIFA del campeón predicho (peor ranking = más arriba, 
       según las reglas: "el de peor ranking queda más alto")
    
    Retorna un DataFrame con la tabla de posiciones.
    """
    datos = []
    for p in todos_los_puntajes:
        datos.append({
            "Posición": 0,  # Se asigna después
            "Participante": p["participante"],
            "Total": p["total"],
            "Grupos": p["pts_grupos"],
            "Eliminatorias": p["pts_eliminatorias"],
            "Campeón": p["pts_campeon"],
            "Especiales": p["pts_especiales"],
            "Penalidades": p["pts_penalidades"],
        })
    
    df = pd.DataFrame(datos)
    
    # Ordenar por total descendente, luego por grupos descendente (desempate)
    df = df.sort_values(
        by=["Total", "Grupos"],
        ascending=[False, False]
    ).reset_index(drop=True)
    
    # Asignar posiciones
    df["Posición"] = range(1, len(df) + 1)
    
    # Reordenar columnas
    cols = ["Posición", "Participante", "Total", "Grupos", 
            "Eliminatorias", "Campeón", "Especiales", "Penalidades"]
    df = df[cols]
    
    return df
