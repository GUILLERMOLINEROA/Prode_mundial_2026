import pandas as pd
import os
from typing import Dict, Optional
from utils.api_football import clasificar_ronda

ORDEN_FASES = {
    "grupos": 0, "16vos": 1, "8vos": 2, "4tos": 3,
    "semis": 4, "final": 5, "campeon": 6,
}

REQUISITOS_REVELACION = {
    2: 4,  # Clase 2: debe llegar a semis
    3: 3,  # Clase 3: debe llegar a 4tos
    4: 1,  # Clase 4: debe pasar de grupos
}

ESTADOS_FINALIZADO = {"FT", "AET", "PEN"}

def grupos_finalizados(resultados):
    """
    Retorna True si los 72 partidos de grupos están finalizados.
    """
    if resultados.empty or "ronda" not in resultados.columns or "estado" not in resultados.columns:
        return False

    partidos_g = resultados[resultados["ronda"].apply(lambda x: clasificar_ronda(str(x))) == "grupos"].copy()
    if partidos_g.empty:
        return False

    if len(partidos_g) < 72:
        return False

    return partidos_g["estado"].isin(ESTADOS_FINALIZADO).all()

def torneo_finalizado(resultados):
    """
    Retorna True si existe una final finalizada.
    """
    if resultados.empty or "ronda" not in resultados.columns or "estado" not in resultados.columns:
        return False

    finales = resultados[
        resultados["ronda"].str.lower().str.contains("final", na=False) &
        ~resultados["ronda"].str.lower().str.contains("semi|quarter|3rd", na=False)
    ]

    if finales.empty:
        return False

    return finales["estado"].isin(ESTADOS_FINALIZADO).any()


def obtener_equipos_clasificados_16avos(resultados=None):
    """
    Set de equipos clasificados a 16avos según los STANDINGS oficiales:
    12 primeros + 12 segundos + 8 mejores terceros.

    DOS MODOS, según `resultados` (vía grupos_finalizados):
      - PROVISIONAL (grupos en curso): solo 1º y 2º de cada grupo. SIN terceros
        (el corte de los 8 mejores no tiene sentido hasta cerrar los 12 grupos).
      - DEFINITIVO (grupos cerrados): los 32 (1º + 2º + 8 mejores terceros).

    Fuente única y compartida por TRES callers, sin que uno pise al otro:
      - tarjetas de "pasa a 16avos" (provisional/definitivo según el momento);
      - condición de Decepción post-grupos (exige el set de 32 completo, len>=32);
      - inyección del +1 de 16avos PROVISIONAL en vivo del scoring
        (data_loader.cargar_todo), solo si la API aún no pobló el cuadro real.

    Detalles:
    - Los 8 mejores terceros se incluyen SOLO si los grupos terminaron
      (`grupos_finalizados`); antes, el corte de los mejores terceros no tiene
      sentido. Si `resultados` es None, se asume que NO terminaron.
    - Si la API ya emite el ranking oficial de terceros, se usa ese (tiebreak
      FIFA). Si no, fallback: 3º de cada grupo ordenado por pts -> DG -> GF.
    - Nombres MAPEADOS (mapear_nombre_equipo) al mismo namespace que el Excel /
      equipos_por_ronda["16vos"], para que el matcheo no tenga huecos silenciosos
      (p.ej. Türkiye->Turquia). `primeros/segundos/ranking_terceros` ya vienen
      mapeados de obtener_clasificados_por_grupo; el fallback mapea explícitamente
      porque standings_completos trae nombres crudos.
    - Sin API key / sin standings -> set() (degradación segura).
    - Garantía dura: con grupos cerrados el set nunca supera 32 (12+12+8).
    - Defensivo: si un grupo trae menos de 3 equipos, no asume el índice 2.

    REQUIERE VALIDACIÓN CONTRA STANDINGS REALES DURANTE EL TORNEO 2026.
    """
    from utils.api_football import obtener_clasificados_por_grupo, mapear_nombre_equipo

    grupos_cerrados = bool(grupos_finalizados(resultados)) if resultados is not None else False

    try:
        clasif = obtener_clasificados_por_grupo()
    except Exception:
        return set()

    primeros = [e for e in clasif.get("primeros", {}).values() if e]
    segundos = [e for e in clasif.get("segundos", {}).values() if e]

    terceros = []
    if grupos_cerrados:
        ranking = clasif.get("ranking_terceros", []) or []
        if ranking:
            # Tiebreak oficial FIFA, ya resuelto y mapeado por la API.
            terceros = [t.get("equipo", "") for t in ranking]
        else:
            # Fallback sin ranking de la API: 3º de cada grupo por pts -> DG -> GF.
            cands = []
            for grupo, eqs in (clasif.get("standings_completos", {}) or {}).items():
                gl = str(grupo).lower()
                if "third" in gl or "ranking of third" in gl:
                    continue  # saltar el pseudo-grupo de terceros (no es un grupo real)
                if len(eqs) >= 3:  # defensivo: no asumir índice 2 siempre presente
                    t = eqs[2]  # lista ya ordenada por rank -> índice 2 = 3º
                    cands.append((
                        t.get("puntos", 0), t.get("diferencia", 0),
                        t.get("goles_favor", 0),
                        mapear_nombre_equipo(t.get("equipo", "")),
                    ))
            cands.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
            terceros = [c[3] for c in cands]
        terceros = [e for e in terceros if e][:8]  # clamp duro: nunca más de 8

    # Construcción con prioridad 1º > 2º > 3º y corte defensivo en 32.
    clasificados = set()
    for eq in primeros + segundos + terceros:
        clasificados.add(eq)
        if grupos_cerrados and len(clasificados) >= 32:
            break
    clasificados.discard("")
    return clasificados


def cargar_equipos_clase():
    path = os.path.join("data", "equipos_clase.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def calcular_fase_maxima_por_equipo(resultados):
    if resultados.empty:
        return {}
    fase_maxima = {}
    for _, p in resultados.iterrows():
        ronda = clasificar_ronda(str(p.get("ronda", "")))
        orden = ORDEN_FASES.get(ronda, -1)
        for eq in [p.get("equipo_local", ""), p.get("equipo_visitante", "")]:
            if eq:
                fase_maxima[eq] = max(fase_maxima.get(eq, 0), orden)
    finales = resultados[
        resultados["ronda"].str.lower().str.contains("final", na=False) &
        ~resultados["ronda"].str.lower().str.contains("semi|quarter|3rd", na=False)]
    if not finales.empty:
        f = finales.iloc[-1]
        gl, gv = f.get("goles_local"), f.get("goles_visitante")
        pl, pv = f.get("penales_local"), f.get("penales_visitante")
        campeon = ""
        if pd.notna(gl) and pd.notna(gv):
            if gl > gv: campeon = f["equipo_local"]
            elif gv > gl: campeon = f["equipo_visitante"]
            elif pd.notna(pl) and pd.notna(pv):
                campeon = f["equipo_local"] if pl > pv else f["equipo_visitante"]
        if campeon:
            fase_maxima[campeon] = 6
    return fase_maxima

def calcular_tabla_grupos(resultados):
    if resultados.empty:
        return pd.DataFrame()
    partidos_g = resultados[resultados["ronda"].apply(lambda x: clasificar_ronda(str(x))) == "grupos"]
    if partidos_g.empty:
        return pd.DataFrame()
    tabla = {}
    for _, p in partidos_g.iterrows():
        local, visitante = p["equipo_local"], p["equipo_visitante"]
        gl, gv = p["goles_local"], p["goles_visitante"]
        if pd.isna(gl) or pd.isna(gv):
            continue
        gl, gv = int(gl), int(gv)
        for eq in [local, visitante]:
            if eq not in tabla:
                tabla[eq] = {"equipo": eq, "grupo": p["ronda"], "pts": 0, "gf": 0, "gc": 0, "jugados": 0}
        tabla[local]["jugados"] += 1
        tabla[visitante]["jugados"] += 1
        if gl > gv:
            tabla[local]["pts"] += 3
        elif gv > gl:
            tabla[visitante]["pts"] += 3
        else:
            tabla[local]["pts"] += 1
            tabla[visitante]["pts"] += 1
        tabla[local]["gf"] += gl
        tabla[local]["gc"] += gv
        tabla[visitante]["gf"] += gv
        tabla[visitante]["gc"] += gl
    datos = list(tabla.values())
    if not datos:
        return pd.DataFrame()
    for d in datos:
        d["dg"] = d["gf"] - d["gc"]
    return pd.DataFrame(datos).sort_values(by=["pts", "dg", "gf"], ascending=[False, False, False])

def determinar_decepcion(equipos_clase, fase_maxima, tabla_grupos):
    if equipos_clase.empty:
        return ""
    clase_1 = equipos_clase[equipos_clase["clase"] == 1].copy()
    if clase_1.empty:
        return ""
    clase_1["fase_max"] = clase_1["pais"].map(fase_maxima).fillna(0).astype(int)
    clase_1["sub"] = clase_1["class_1_sub"].fillna(1).astype(int)
    clase_1 = clase_1.sort_values(by=["fase_max", "sub", "ranking_fifa"], ascending=[True, True, True])
    return clase_1.iloc[0]["pais"]

def determinar_revelacion(equipos_clase, fase_maxima):
    if equipos_clase.empty:
        return None
    candidatos = []
    for clase, min_orden in REQUISITOS_REVELACION.items():
        eqs = equipos_clase[equipos_clase["clase"] == clase]
        for _, eq in eqs.iterrows():
            fase = fase_maxima.get(eq["pais"], 0)
            if fase >= min_orden:
                candidatos.append({"pais": eq["pais"], "clase": clase,
                    "fase_max": fase, "ranking_fifa": eq["ranking_fifa"]})
    if not candidatos:
        return None
    df = pd.DataFrame(candidatos)
    df = df.sort_values(by=["fase_max", "clase", "ranking_fifa"], ascending=[False, False, False])
    return df.iloc[0]["pais"]

def determinar_mejor_primera_fase(tabla_grupos):
    if tabla_grupos.empty:
        return ""
    mejor = tabla_grupos.sort_values(by=["pts", "dg", "gf"], ascending=[False, False, False]).iloc[0]
    return mejor["equipo"]

def determinar_peor_equipo(tabla_grupos, fase_maxima):
    if tabla_grupos.empty:
        return ""
    df = tabla_grupos.copy()
    df["fase_max"] = df["equipo"].map(fase_maxima).fillna(0).astype(int)
    df = df.sort_values(by=["fase_max", "pts", "dg", "gf"], ascending=[True, True, True, True])
    return df.iloc[0]["equipo"]

def calcular_todas_las_categorias(resultados):
    """
    Calcula categorías especiales con lógica por etapas:

    - Antes de terminar grupos: nada definido
    - Después de grupos: solo Mejor 1era Fase y Peor Equipo
    - Después del torneo: Revelación y Decepción también
    - Figura y Goleador quedan para overrides/manual
    """
    vacio = {
        "Figura": "",
        "Goleador": "",
        "Revelación": "",
        "Decepción": "",
        "Mejor 1era Fase": "",
        "Peor Equipo": "",
    }

    if resultados is None or resultados.empty:
        return vacio

    equipos_clase = cargar_equipos_clase()
    fase_maxima = calcular_fase_maxima_por_equipo(resultados)
    tabla_grupos = calcular_tabla_grupos(resultados)

    # 1) Antes del final de grupos: nada
    if not grupos_finalizados(resultados):
        return vacio

    # 2) Después de grupos: ya podemos saber estas dos
    categorias = {
        "Figura": "",
        "Goleador": "",
        "Revelación": "",
        "Decepción": "",
        "Mejor 1era Fase": determinar_mejor_primera_fase(tabla_grupos),
        "Peor Equipo": determinar_peor_equipo(tabla_grupos, fase_maxima),
    }

    # 3) Decepción TAMBIÉN al terminar grupos, pero SOLO si un favorito real
    #    (clase 1) NO está entre los 32 clasificados a 16avos (según standings).
    #    Es una cuestión de REPRESENTATIVIDAD: que la Decepción oficial sea un
    #    favorito realmente eliminado, no el clase-1 que clasificó peor.
    #
    #    OJO: NO se puede usar fase_maxima acá. Apenas terminan los grupos, los
    #    fixtures de 16avos de la API todavía no tienen equipos reales (vienen null
    #    hasta que se arma el cuadro), así que TODOS los equipos tendrían fase_max==0
    #    —incluidos los que clasificaron— y la condición se dispararía siempre. Por
    #    eso usamos el set de clasificados de standings (misma fuente que las
    #    tarjetas de "pasa a 16avos").
    #
    #    Nota: NO se relaciona con la penalidad decepcion_llega_semis. Esa penalidad
    #    evalúa la decepción PRONOSTICADA por cada participante (categorias_pred), no
    #    esta decepción oficial. (Revelación queda intacta: solo se cierra a fin de
    #    torneo.)
    if not torneo_finalizado(resultados) and not equipos_clase.empty:
        clasificados_16 = obtener_equipos_clasificados_16avos(resultados)
        # Exigimos las 32 plazas COMPLETAS antes de decidir. grupos_finalizados()
        # mira los FIXTURES, pero los standings vienen de OTRO endpoint y pueden
        # llegar parciales (solo algunos de los 12 grupos). Con un set incompleto,
        # un clase-1 que SÍ clasificó podría contar como "no clasificado" -> falsa
        # Decepción. Si faltan plazas (o no hay standings), dejamos pendiente.
        if len(clasificados_16) >= 32:
            clase_1 = equipos_clase[equipos_clase["clase"] == 1]
            hay_favorito_eliminado = any(
                pais not in clasificados_16 for pais in clase_1["pais"]
            )
            if hay_favorito_eliminado:
                categorias["Decepción"] = determinar_decepcion(equipos_clase, fase_maxima, tabla_grupos)

    # 4) Al terminar el torneo cerramos Revelación y Decepción de forma definitiva
    if torneo_finalizado(resultados):
        categorias["Revelación"] = determinar_revelacion(equipos_clase, fase_maxima) or "No hay Revelación"
        categorias["Decepción"] = determinar_decepcion(equipos_clase, fase_maxima, tabla_grupos)

    return categorias
