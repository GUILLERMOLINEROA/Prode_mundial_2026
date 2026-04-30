# =============================================================================
# utils/scoring.py
# Módulo central de puntuación del PRODE Mundial 2026.
#
# Máximo teórico: 577 puntos [1]
#
# FASE DE GRUPOS (máx 240):
#   - Ganador: 1 pto × 104 partidos (NOTA: son 72 partidos de grupos,
#     pero el Excel dice 104 como máximo. Verificar con reglas finales.)
#   - Resultado exacto: 1 pto adicional
#
# ELIMINATORIAS (máx 273):
#   - 16vos: 1 pto × equipo (máx 32)
#   - 8vos: 4 pts × equipo (máx 64)
#   - 4tos: 8 pts × equipo (máx 64)  
#   - Semis: 15 pts × equipo (máx 60)
#   - Final: 25 pts × equipo (máx 50)
#   - 3ero: 5 pts
#   - Campeón: 30 pts
#
# ESPECIALES (máx 64):
#   Figura, Goleador, Revelación, Decepción: 12 c/u
#   Mejor 1era Fase, Peor Equipo: 8 c/u
#
# PENALIDADES:
#   Revelación en grupos: -20 | Campeón no llega a 4tos: -20
#   Peor pasa grupos: -10 | Decepción llega a semis: -20
# =============================================================================

import pandas as pd
from typing import Dict, List, Tuple, Optional, Set

from utils.excel_reader import obtener_equipos_predichos_por_ronda


# --- Constantes de puntuación ---
PUNTOS = {
    "grupos_ganador": 1,
    "grupos_exacto": 1,
    "16vos": 1,
    "8vos": 3,
    "4tos": 6,
    "semis": 10,
    "final": 15,
    "3ero": 5,
    "campeon": 20,
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

def _determinar_resultado(goles_l: int, goles_v: int) -> str:
    """Retorna 'local', 'visitante' o 'empate'."""
    if goles_l > goles_v:
        return "local"
    elif goles_l < goles_v:
        return "visitante"
    return "empate"


def calcular_puntos_grupos(
    apuestas_grupos: pd.DataFrame,
    resultados_reales: pd.DataFrame,
    participante: str
) -> Tuple[int, pd.DataFrame]:
    """
    Calcula puntos de fase de grupos.
    1 pto por acertar ganador + 1 pto por resultado exacto.
    """
    apuestas = apuestas_grupos[apuestas_grupos["participante"] == participante].copy()
    
    if apuestas.empty:
        return 0, pd.DataFrame()
    
    puntos_total = 0
    detalles = []
    
    for _, ap in apuestas.iterrows():
        local = ap["equipo_local"]
        visitante = ap["equipo_visitante"]
        g_pred_l = ap["goles_local_pred"]
        g_pred_v = ap["goles_visitante_pred"]
        
        # Buscar resultado real
        res = resultados_reales[
            (resultados_reales["equipo_local"] == local) &
            (resultados_reales["equipo_visitante"] == visitante) &
            (resultados_reales["estado"] == "FT")
        ]
        
        if res.empty:
            detalles.append({
                "partido_id": ap["partido_id"], "grupo": ap.get("grupo", ""),
                "equipo_local": local, "equipo_visitante": visitante,
                "pred_local": g_pred_l, "pred_visitante": g_pred_v,
                "real_local": None, "real_visitante": None,
                "acierto_ganador": False, "acierto_exacto": False,
                "puntos": 0, "estado": "pendiente",
            })
            continue
        
        r = res.iloc[0]
        g_real_l = int(r["goles_local"])
        g_real_v = int(r["goles_visitante"])
        
        res_real = _determinar_resultado(g_real_l, g_real_v)
        res_pred = _determinar_resultado(g_pred_l, g_pred_v) if (
            g_pred_l is not None and g_pred_v is not None
        ) else None
        
        ac_gan = (res_real == res_pred) if res_pred else False
        ac_ex = (
            g_pred_l is not None and g_pred_v is not None and
            g_pred_l == g_real_l and g_pred_v == g_real_v
        )
        
        pts = 0
        if ac_gan:
            pts += PUNTOS["grupos_ganador"]
        if ac_ex:
            pts += PUNTOS["grupos_exacto"]
        puntos_total += pts
        
        detalles.append({
            "partido_id": ap["partido_id"], "grupo": ap.get("grupo", ""),
            "equipo_local": local, "equipo_visitante": visitante,
            "pred_local": g_pred_l, "pred_visitante": g_pred_v,
            "real_local": g_real_l, "real_visitante": g_real_v,
            "acierto_ganador": ac_gan, "acierto_exacto": ac_ex,
            "puntos": pts, "estado": "jugado",
        })
    
    return puntos_total, pd.DataFrame(detalles)


# =============================================================================
# ELIMINATORIAS — Usando Total Results
# =============================================================================

def calcular_puntos_eliminatorias(
    total_results_pred: Dict,
    equipos_reales_por_ronda: Dict[str, Set[str]],
) -> Tuple[int, Dict[str, int], List[dict]]:
    """
    Calcula puntos de eliminatorias comparando las predicciones del
    participante (desde Total Results) con la realidad (desde la API).
    
    Para cada ronda, verifica qué equipos el participante predijo
    que llegarían, y cuáles realmente llegaron. Cada acierto suma puntos.
    """
    equipos_pred = obtener_equipos_predichos_por_ronda(total_results_pred)
    
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
        pred = equipos_pred.get(ronda, set())
        real = equipos_reales_por_ronda.get(ronda, set())
        
        aciertos = pred & real  # Intersección
        pts_ronda = len(aciertos) * pts_valor
        puntos_por_ronda[ronda] = pts_ronda
        puntos_total += pts_ronda
        
        for equipo in sorted(pred):
            acerto = equipo in real
            detalles.append({
                "ronda": ronda,
                "equipo": equipo,
                "acerto": acerto,
                "puntos": pts_valor if acerto else 0,
            })
    
    return puntos_total, puntos_por_ronda, detalles


def calcular_puntos_campeon_y_tercero(
    total_results_pred: Dict,
    campeon_real: str,
    tercero_real: str,
) -> Tuple[int, int]:
    """Puntos por acertar campeón (30) y tercer puesto (5)."""
    pts_campeon = 0
    pts_tercero = 0
    
    campeon_pred = total_results_pred.get("campeon", "")
    tercero_pred = total_results_pred.get("tercero", "")
    
    if campeon_pred and campeon_real and campeon_pred.lower() == campeon_real.lower():
        pts_campeon = PUNTOS["campeon"]
    
    if tercero_pred and tercero_real and tercero_pred.lower() == tercero_real.lower():
        pts_tercero = PUNTOS["3ero"]
    
    return pts_campeon, pts_tercero


# =============================================================================
# CATEGORÍAS ESPECIALES
# =============================================================================

def calcular_puntos_categorias(
    categorias_pred: Dict[str, str],
    categorias_reales: Dict[str, str]
) -> Tuple[int, Dict[str, bool]]:
    """Compara predicción vs realidad para cada categoría especial."""
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
    total_results_pred: Dict,
    equipos_reales_por_ronda: Dict[str, Set[str]],
) -> Tuple[int, List[str]]:
    """
    Calcula penalidades según las reglas del PRODE [1]:
    
    1. Revelación se queda en grupos: -20
    2. Campeón predicho no llega a 4tos: -20
    3. Peor equipo predicho pasa de grupos: -10
    4. Decepción predicha llega a semis: -20
    """
    pen_total = 0
    razones = []
    
    eq_16vos_real = equipos_reales_por_ronda.get("16vos", set())
    eq_4tos_real = equipos_reales_por_ronda.get("4tos", set())
    eq_semis_real = equipos_reales_por_ronda.get("semis", set())
    
    # 1. Revelación se queda en grupos
    revelacion = categorias_pred.get("Revelación", "").strip()
    if revelacion and eq_16vos_real:
        if revelacion not in eq_16vos_real:
            pen_total += PENALIDADES["revelacion_queda_grupos"]
            razones.append(
                f"🪦 Tu revelación ({revelacion}) se quedó en grupos: "
                f"{PENALIDADES['revelacion_queda_grupos']} pts"
            )
    
    # 2. Campeón no llega a 4tos
    campeon_pred = categorias_pred.get("Campeon", "").strip()
    if campeon_pred and eq_4tos_real:
        if campeon_pred not in eq_4tos_real:
            pen_total += PENALIDADES["campeon_no_llega_4tos"]
            razones.append(
                f"💀 Tu campeón ({campeon_pred}) no llegó ni a cuartos: "
                f"{PENALIDADES['campeon_no_llega_4tos']} pts"
            )
    
    # 3. Peor equipo pasa de grupos
    peor = categorias_pred.get("Peor Equipo", "").strip()
    if peor and eq_16vos_real:
        if peor in eq_16vos_real:
            pen_total += PENALIDADES["peor_pasa_grupos"]
            razones.append(
                f"😂 Tu 'peor equipo' ({peor}) pasó de grupos: "
                f"{PENALIDADES['peor_pasa_grupos']} pts"
            )
    
    # 4. Decepción llega a semis
    decepcion = categorias_pred.get("Decepción", "").strip()
    if decepcion and eq_semis_real:
        if decepcion in eq_semis_real:
            pen_total += PENALIDADES["decepcion_llega_semis"]
            razones.append(
                f"🤡 Tu decepción ({decepcion}) llegó a SEMIS: "
                f"{PENALIDADES['decepcion_llega_semis']} pts"
            )
    
    return pen_total, razones


# =============================================================================
# FUNCIÓN MAESTRA: PUNTUACIÓN TOTAL
# =============================================================================

def calcular_puntuacion_total(
    participante: str,
    apuestas_grupos: pd.DataFrame,
    categorias_pred: Dict[str, str],
    total_results_pred: Dict,
    resultados_reales: pd.DataFrame,
    equipos_reales_por_ronda: Dict[str, Set[str]],
    categorias_reales: Dict[str, str],
    campeon_real: str = "",
    tercero_real: str = "",
) -> Dict:
    """
    Calcula la puntuación TOTAL de un participante.
    Máximo teórico: 577 puntos [1].
    """
    # 1. Fase de grupos
    pts_grupos, detalle_grupos = calcular_puntos_grupos(
        apuestas_grupos, resultados_reales, participante
    )
    
    # 2. Eliminatorias (desde Total Results del participante vs API)
    pts_elim, pts_por_ronda, detalles_elim = calcular_puntos_eliminatorias(
        total_results_pred, equipos_reales_por_ronda,
    )
    
    # 3. Campeón y 3er puesto
    pts_campeon, pts_tercero = calcular_puntos_campeon_y_tercero(
        total_results_pred, campeon_real, tercero_real,
    )
    
    # 4. Categorías especiales
    pts_especiales, aciertos_esp = calcular_puntos_categorias(
        categorias_pred, categorias_reales
    )
    
    # 5. Penalidades
    pts_penalidades, razones_pen = calcular_penalidades(
        categorias_pred, total_results_pred, equipos_reales_por_ronda,
    )
    
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
        "razones_penalidad": razones_pen,
        "categorias": categorias_pred,
        "total_results": total_results_pred,
    }


# =============================================================================
# LEADERBOARD
# =============================================================================

def generar_leaderboard(todos_los_puntajes):
    datos = []
    for p in todos_los_puntajes:
        pts_ronda = p.get("pts_por_ronda_elim", {})
        aciertos = p.get("aciertos_especiales", {})
        pts_figura = PUNTOS["Figura"] if aciertos.get("Figura", False) else 0
        pts_goleador = PUNTOS["Goleador"] if aciertos.get("Goleador", False) else 0
        pts_revelacion_esp = PUNTOS["Revelación"] if aciertos.get("Revelación", False) else 0
        pts_decepcion_esp = PUNTOS["Decepción"] if aciertos.get("Decepción", False) else 0
        pts_mejor1era = PUNTOS["Mejor 1era Fase"] if aciertos.get("Mejor 1era Fase", False) else 0
        pts_peor_esp = PUNTOS["Peor Equipo"] if aciertos.get("Peor Equipo", False) else 0
        pen_revelacion = 0
        pen_campeon = 0
        pen_peor = 0
        pen_decepcion = 0
        for r in p.get("razones_penalidad", []):
            rl = r.lower()
            if "revelaci" in rl: pen_revelacion = PENALIDADES["revelacion_queda_grupos"]
            elif "campe" in rl: pen_campeon = PENALIDADES["campeon_no_llega_4tos"]
            elif "peor" in rl: pen_peor = PENALIDADES["peor_pasa_grupos"]
            elif "decepc" in rl: pen_decepcion = PENALIDADES["decepcion_llega_semis"]
        detalle = p.get("detalle_grupos", pd.DataFrame())
        pts_ganador = 0
        pts_exacto = 0
        if isinstance(detalle, pd.DataFrame) and not detalle.empty:
            jugados = detalle[detalle["estado"] == "jugado"]
            if not jugados.empty:
                pts_ganador = int(jugados["acierto_ganador"].sum()) * PUNTOS["grupos_ganador"]
                pts_exacto = int(jugados["acierto_exacto"].sum()) * PUNTOS["grupos_exacto"]
        datos.append({
            "Posición": 0, "Participante": p["participante"], "Total": p["total"],
            "Grupos": p["pts_grupos"], "Grupos L/E/V": pts_ganador, "Grupos Exacto": pts_exacto,
            "Eliminatorias": p["pts_eliminatorias"],
            "16vos": pts_ronda.get("16vos", 0), "8vos": pts_ronda.get("8vos", 0),
            "4tos": pts_ronda.get("4tos", 0), "Semis": pts_ronda.get("semis", 0),
            "Final": pts_ronda.get("final", 0),
            "3ero": p["pts_tercero"], "Campeón": p["pts_campeon"],
            "Especiales": p["pts_especiales"],
            "Figura": pts_figura, "Goleador": pts_goleador,
            "Revelación": pts_revelacion_esp, "Decepción": pts_decepcion_esp,
            "Mejor 1era Fase": pts_mejor1era, "Peor Equipo": pts_peor_esp,
            "Penalidades": p["pts_penalidades"],
            "Pen. Revelación": pen_revelacion, "Pen. Campeón": pen_campeon,
            "Pen. Peor Equipo": pen_peor, "Pen. Decepción": pen_decepcion,
        })
    df = pd.DataFrame(datos)
    df = df.sort_values(by=["Total", "Grupos"], ascending=[False, False]).reset_index(drop=True)
    df["Posición"] = range(1, len(df) + 1)
    return df
