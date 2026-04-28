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
        Tupla (puntos_totales, DataFrame_detalle
