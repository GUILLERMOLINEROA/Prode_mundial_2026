# =============================================================================
# utils/special_categories.py
# Módulo que determina los resultados reales de las categorías especiales:
# Revelación, Decepción, Mejor 1era Fase, Peor Equipo, etc.
#
# REGLAS (de la imagen adjunta):
# - Hay 4 clases de equipos según historia, importancia, vigencia y Ranking FIFA.
# - El PEOR de los equipos Clase 1 es automáticamente la Decepción.
#   (Si hay 3 equipos Clase 1'; si hay empate entre un 1' y un 1, 
#    el Clase 1 será decepción)
# - Los equipos Clase 2, 3 y 4 podrán ser Revelación:
#   * Clase 2: solo si llega a Semis
#   * Clase 3: solo si llega a 4tos
#   * Clase 4: solo si pasa de grupos
# - El que haya llegado más lejos de los equipos Clase 2, 3 o 4 será la Revelación.
# - En caso de empate en ronda, se valora mejor a los de peor clase.
# - Dentro de una misma clase, se desempata por puntos/goles en tabla general.
# - El último criterio de desempate es el Ranking FIFA al 1/4/2026 
#   (el de peor ranking queda más alto).
# - Puede darse que NO HAYA equipo revelación.
# =============================================================================

import pandas as pd
from typing import Dict, Optional, Tuple


# Orden jerárquico de las rondas (mayor = llegó más lejos)
ORDEN_RONDAS = {
    "grupos": 0,
    "16vos": 1,
    "8vos": 2,
    "4tos": 3,
    "semis": 4,
    "final": 5,
    "campeon": 6,
}


def determinar_decepcion(
    equipos_clase: pd.DataFrame,
    max_ronda_por_equipo: Dict[str, str]
) -> str:
    """
    Determina el equipo Decepción del torneo.
    
    Regla: El PEOR de los equipos Clase 1 es automáticamente la Decepción.
    Si hay sub-clases (1 y 1'), y hay empate, el Clase 1 puro pierde.
    
    Parámetros:
        equipos_clase: DataFrame con columnas [pais, clase, ranking_fifa, class_1_sub]
        max_ronda_por_equipo: Dict {equipo: máxima_ronda_alcanzada}
    
    Retorna: Nombre del equipo decepción
    """
    # Filtrar equipos Clase 1
    clase_1 = equipos_clase[equipos_clase["clase"] == 1].copy()
    
    if clase_1.empty:
        return ""
    
    # Asignar la ronda máxima alcanzada
    clase_1["max_ronda"] = clase_1["pais"].map(max_ronda_por_equipo).fillna("grupos")
    clase_1["ronda_orden"] = clase_1["max_ronda"].map(ORDEN_RONDAS).fillna(0)
    
    # Ordenar: menor ronda primero (peor rendimiento), luego por sub-clase
    # (class_1_sub=1 es "puro" Clase 1, class_1_sub=2 es Clase 1')
    # En empate de ronda, el Clase 1 puro (sub=1) es más decepcionante
    clase_1 = clase_1.sort_values(
        by=["ronda_orden", "class_1_sub", "ranking_fifa"],
        ascending=[True, True, True]  # Menor ronda, clase pura, mejor ranking = más decepción
    )
    
    return clase_1.iloc[0]["pais"]


def determinar_revelacion(
    equipos_clase: pd.DataFrame,
    max_ronda_por_equipo: Dict[str, str]
) -> Optional[str]:
    """
    Determina el equipo Revelación del torneo.
    
    Reglas:
    - Clase 2: revelación solo si llega a Semis
    - Clase 3: revelación solo si llega a 4tos
    - Clase 4: revelación solo si pasa de grupos (16vos)
    - El que llegó más lejos gana.
    - En empate de ronda: se valora mejor al de peor clase.
    - Dentro de misma clase: desempate por puntos/goles.
    - Último desempate: Ranking FIFA (peor ranking = más arriba).
    - Puede NO haber revelación.
    """
    # Requisitos mínimos por clase
    requisitos_minimos = {
        2: "semis",     # Clase 2 debe llegar al menos a semis
        3: "4tos",      # Clase 3 debe llegar al menos a cuartos
        4: "16vos",     # Clase 4 debe al menos pasar de grupos
    }
    
    candidatos = []
    
    for clase, ronda_minima in requisitos_minimos.items():
        equipos_clase_n = equipos_clase[equipos_clase["clase"] == clase]
        ronda_min_orden = ORDEN_RONDAS.get(ronda_minima, 0)
        
        for _, equipo in equipos_clase_n.iterrows():
            max_ronda = max_ronda_por_equipo.get(equipo["pais"], "grupos")
            max_ronda_ord = ORDEN_RONDAS.get(max_ronda, 0)
            
            if max_ronda_ord >= ronda_min_orden:
                candidatos.append({
                    "pais": equipo["pais"],
                    "clase": clase,
                    "max_ronda": max_ronda,
                    "ronda_orden": max_ronda_ord,
                    "ranking_fifa": equipo["ranking_fifa"],
                })
    
    if not candidatos:
        return None  # No hay revelación
    
    df_candidatos = pd.DataFrame(candidatos)
    
    # Ordenar: mayor ronda primero, luego peor clase (mayor número),
    # luego peor ranking (mayor número = más mérito)
    df_candidatos = df_candidatos.sort_values(
        by=["ronda_orden", "clase", "ranking_fifa"],
        ascending=[False, False, False]
    )
    
    return df_candidatos.iloc[0]["pais"]


def determinar_mejor_primera_fase(
    resultados_grupos: pd.DataFrame
) -> str:
    """
    Determina el equipo con mejor rendimiento en fase de grupos.
    Se basa en puntos (3 por victoria, 1 por empate) y diferencia de goles.
    """
    # Calcular tabla de posiciones de fase de grupos
    equipos_stats = {}
    
    for _, partido in resultados_grupos.iterrows():
        local = partido["equipo_local"]
        visitante = partido["equipo_visitante"]
        gl = partido["goles_local"]
        gv = partido["goles_visitante"]
        
        if pd.isna(gl) or pd.isna(gv):
            continue
        
        for equipo in [local, visitante]:
            if equipo not in equipos_stats:
                equipos_stats[equipo] = {"puntos": 0, "gf": 0, "gc": 0, "dg": 0}
        
        if gl > gv:  # Gana local
            equipos_stats[local]["puntos"] += 3
        elif gv > gl:  # Gana visitante
            equipos_stats[visitante]["puntos"] += 3
        else:  # Empate
            equipos_stats[local]["puntos"] += 1
            equipos_stats[visitante]["puntos"] += 1
        
        equipos_stats[local]["gf"] += gl
        equipos_stats[local]["gc"] += gv
        equipos_stats[visitante]["gf"] += gv
        equipos_stats[visitante]["gc"] += gl
    
    # Calcular diferencia de goles
    for equipo in equipos_stats:
        equipos_stats[equipo]["dg"] = (
            equipos_stats[equipo]["gf"] - equipos_stats[equipo]["gc"]
        )
    
    if not equipos_stats:
        return ""
    
    # Ordenar por puntos desc, dg desc, gf desc
    ranking = sorted(
        equipos_stats.items(),
        key=lambda x: (x[1]["puntos"], x[1]["dg"], x[1]["gf"]),
        reverse=True
    )
    
    return ranking[0][0]  # El mejor equipo


def determinar_peor_equipo(
    resultados_grupos: pd.DataFrame,
    max_ronda_por_equipo: Dict[str, str]
) -> str:
    """
    Determina el peor equipo del torneo.
    El que fue eliminado más temprano con peor rendimiento.
    """
    equipos_stats = {}
    
    for _, partido in resultados_grupos.iterrows():
        local = partido["equipo_local"]
        visitante = partido["equipo_visitante"]
        gl = partido["goles_local"]
        gv = partido["goles_visitante"]
        
        if pd.isna(gl) or pd.isna(gv):
            continue
        
        for equipo in [local, visitante]:
            if equipo not in equipos_stats:
                equipos_stats[equipo] = {"puntos": 0, "gf": 0, "gc": 0}
        
        if gl > gv:
            equipos_stats[local]["puntos"] += 3
        elif gv > gl:
            equipos_stats[visitante]["puntos"] += 3
        else:
            equipos_stats[local]["puntos"] += 1
            equipos_stats[visitante]["puntos"] += 1
        
        equipos_stats[local]["gf"] += gl
        equipos_stats[local]["gc"] += gv
        equipos_stats[visitante]["gf"] += gv
        equipos_stats[visitante]["gc"] += gl
    
    if not equipos_stats:
        return ""
    
    # Solo considerar equipos que se quedaron en grupos
    eliminados_grupos = {
        eq: stats for eq, stats in equipos_stats.items()
        if max_ronda_por_equipo.get(eq, "grupos") == "grupos"
    }
    
    if not eliminados_grupos:
        eliminados_grupos = equipos_stats
    
    # Ordenar por puntos asc, dg asc (peor primero)
    ranking = sorted(
        eliminados_grupos.items(),
        key=lambda x: (x[1]["puntos"], x[1]["gf"] - x[1]["gc"], x[1]["gf"]),
        ascending_default=True
    )
    
    return ranking[0][0]
