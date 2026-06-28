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
    #    (clase 1) NO está en el CUADRO REAL de 16avos de la API. Es una cuestión
    #    de REPRESENTATIVIDAD: que la Decepción oficial sea un favorito realmente
    #    eliminado, no el clase-1 que clasificó peor.
    #
    #    Fuente = el cuadro real (equipos con fase_max>=1, o sea que llegaron a
    #    16avos o más), la MISMA que usa el scoring de eliminatorias. Antes esto
    #    salía de standings, pero ese endpoint es frágil: durante los 16avos
    #    devuelve un "grupo" fantasma (el ranking de terceros) y deja el conteo en
    #    31, con lo que el viejo candado `>= 32` no se cumplía nunca y la Decepción
    #    no se resolvía. El cuadro real no tiene ese problema.
    #
    #    NO usamos conteo exacto (`== 32`): es frágil ante un faltante por mapeo de
    #    nombres. Solo exigimos que el bracket esté MATERIALMENTE poblado (umbral
    #    defensivo) para no disparar falsos positivos en la ventana "grupos recién
    #    cerrados, fixtures de 16avos todavía sin equipos" (ahí el bracket está
    #    vacío y se deja pendiente; se resuelve solo cuando la API lo puebla).
    #
    #    Nota: NO se relaciona con la penalidad decepcion_llega_semis. Esa penalidad
    #    evalúa la decepción PRONOSTICADA por cada participante (categorias_pred), no
    #    esta decepción oficial. (Revelación queda intacta: solo se cierra a fin de
    #    torneo.)
    if not torneo_finalizado(resultados) and not equipos_clase.empty:
        bracket_real = {eq for eq, mx in fase_maxima.items() if mx >= 1}
        # "Poblado" = el cuadro de 16avos ya está armado. >=24 es muy superior a la
        # ventana vacía/parcial (la API publica las 16 llaves -> 32 equipos- juntas)
        # y tolera un faltante por mapeo sin trabarse en un número exacto.
        if len(bracket_real) >= 24:
            clase_1 = equipos_clase[equipos_clase["clase"] == 1]
            hay_favorito_eliminado = any(
                pais not in bracket_real for pais in clase_1["pais"]
            )
            if hay_favorito_eliminado:
                categorias["Decepción"] = determinar_decepcion(equipos_clase, fase_maxima, tabla_grupos)

    # 4) Al terminar el torneo cerramos Revelación y Decepción de forma definitiva
    if torneo_finalizado(resultados):
        categorias["Revelación"] = determinar_revelacion(equipos_clase, fase_maxima) or "No hay Revelación"
        categorias["Decepción"] = determinar_decepcion(equipos_clase, fase_maxima, tabla_grupos)

    return categorias
