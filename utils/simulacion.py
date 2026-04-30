import pandas as pd
import streamlit as st

def _generar_partidos_grupos():
    """Genera los 72 partidos de fase de grupos con datos fijos."""
    partidos = []
    mid = 1
    grupos_data = {
        "Group A": [
            ("Mexico",1,1,"Sudafrica","2026-06-11"),("Corea del Sur",2,1,"Republica Checa","2026-06-11"),
            ("Republica Checa",1,1,"Sudafrica","2026-06-18"),("Mexico",1,3,"Corea del Sur","2026-06-18"),
            ("Republica Checa",2,1,"Mexico","2026-06-24"),("Sudafrica",1,1,"Corea del Sur","2026-06-24"),
        ],
        "Group B": [
            ("Canada",1,3,"Bosnia","2026-06-12"),("Qatar",0,0,"Suiza","2026-06-13"),
            ("Suiza",1,1,"Bosnia","2026-06-18"),("Canada",1,0,"Qatar","2026-06-18"),
            ("Suiza",1,0,"Canada","2026-06-24"),("Bosnia",3,1,"Qatar","2026-06-24"),
        ],
        "Group C": [
            ("Brasil",2,3,"Marruecos","2026-06-13"),("Haiti",1,2,"Escocia","2026-06-13"),
            ("Brasil",3,3,"Haiti","2026-06-19"),("Escocia",1,1,"Marruecos","2026-06-19"),
            ("Escocia",3,2,"Brasil","2026-06-24"),("Marruecos",2,3,"Haiti","2026-06-24"),
        ],
        "Group D": [
            ("Estados Unidos",0,1,"Paraguay","2026-06-12"),("Australia",2,1,"Turquia","2026-06-14"),
            ("Turquia",3,1,"Paraguay","2026-06-20"),("Estados Unidos",3,0,"Australia","2026-06-19"),
            ("Turquia",0,1,"Estados Unidos","2026-06-25"),("Paraguay",2,3,"Australia","2026-06-25"),
        ],
        "Group E": [
            ("Alemania",3,1,"Curazao","2026-06-14"),("Costa de Marfil",2,0,"Ecuador","2026-06-14"),
            ("Alemania",1,0,"Costa de Marfil","2026-06-20"),("Ecuador",0,0,"Curazao","2026-06-20"),
            ("Ecuador",0,3,"Alemania","2026-06-25"),("Curazao",3,3,"Costa de Marfil","2026-06-25"),
        ],
        "Group F": [
            ("Paises Bajos",1,3,"Japon","2026-06-17"),("Suecia",0,0,"Tunez","2026-06-14"),
            ("Paises Bajos",1,1,"Suecia","2026-06-20"),("Tunez",0,2,"Japon","2026-06-21"),
            ("Japon",3,1,"Suecia","2026-06-25"),("Tunez",1,1,"Paises Bajos","2026-06-25"),
        ],
        "Group G": [
            ("Iran",2,0,"Nueva Zelanda","2026-06-15"),("Belgica",1,1,"Egipto","2026-06-15"),
            ("Belgica",3,2,"Iran","2026-06-21"),("Nueva Zelanda",2,1,"Egipto","2026-06-21"),
            ("Nueva Zelanda",2,0,"Belgica","2026-06-27"),("Egipto",0,1,"Iran","2026-06-27"),
        ],
        "Group H": [
            ("España",3,0,"Cabo Verde","2026-06-15"),("Arabia Saudita",1,2,"Uruguay","2026-06-15"),
            ("España",3,3,"Arabia Saudita","2026-06-21"),("Uruguay",1,0,"Cabo Verde","2026-06-21"),
            ("Uruguay",3,3,"España","2026-06-26"),("Cabo Verde",0,1,"Arabia Saudita","2026-06-26"),
        ],
        "Group I": [
            ("Francia",0,1,"Senegal","2026-06-16"),("Irak",0,1,"Noruega","2026-06-16"),
            ("Francia",2,3,"Irak","2026-06-22"),("Noruega",1,1,"Senegal","2026-06-22"),
            ("Noruega",2,1,"Francia","2026-06-26"),("Senegal",0,0,"Irak","2026-06-26"),
        ],
        "Group J": [
            ("Argentina",2,2,"Argelia","2026-06-16"),("Austria",3,1,"Jordania","2026-06-17"),
            ("Argentina",0,1,"Austria","2026-06-22"),("Jordania",2,3,"Argelia","2026-06-23"),
            ("Jordania",2,0,"Argentina","2026-06-27"),("Argelia",0,0,"Austria","2026-06-27"),
        ],
        "Group K": [
            ("Portugal",0,1,"Congo","2026-06-17"),("Uzbekistan",2,3,"Colombia","2026-06-17"),
            ("Portugal",3,2,"Uzbekistan","2026-06-23"),("Colombia",1,1,"Congo","2026-06-23"),
            ("Colombia",3,2,"Portugal","2026-06-27"),("Congo",0,1,"Uzbekistan","2026-06-27"),
        ],
        "Group L": [
            ("Inglaterra",3,1,"Croacia","2026-06-17"),("Ghana",0,2,"Panama","2026-06-17"),
            ("Inglaterra",1,1,"Ghana","2026-06-23"),("Panama",2,1,"Croacia","2026-06-23"),
            ("Panama",1,2,"Inglaterra","2026-06-27"),("Croacia",1,3,"Ghana","2026-06-27"),
        ],
    }
    for grupo, partidos_grupo in grupos_data.items():
        for local, gl, gv, visitante, fecha in partidos_grupo:
            partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha),
                "ronda": grupo, "equipo_local": local, "equipo_visitante": visitante,
                "goles_local": gl, "goles_visitante": gv,
                "penales_local": None, "penales_visitante": None, "estado": "FT"})
            mid += 1
    return partidos, mid

def _generar_eliminatorias(mid):
    """Genera los partidos de eliminatorias con datos fijos. Todos 1-0."""
    partidos = []
    fecha_e = pd.Timestamp("2026-07-01")
    eliminatorias = [
        # 16vos
        ("Republica Checa","Suiza","Round of 32"),("Alemania","Marruecos","Round of 32"),
        ("Japon","Haiti","Round of 32"),("Escocia","Paises Bajos","Round of 32"),
        ("Noruega","Turquia","Round of 32"),("Costa de Marfil","Senegal","Round of 32"),
        ("Corea del Sur","Arabia Saudita","Round of 32"),("Inglaterra","Irak","Round of 32"),
        ("Estados Unidos","Jordania","Round of 32"),("Iran","Sudafrica","Round of 32"),
        ("Congo","Panama","Round of 32"),("Uruguay","Argelia","Round of 32"),
        ("Bosnia","Belgica","Round of 32"),("Austria","España","Round of 32"),
        ("Colombia","Ghana","Round of 32"),("Australia","Nueva Zelanda","Round of 32"),
        # 8vos
        ("Alemania","Noruega","Round of 16"),("Republica Checa","Japon","Round of 16"),
        ("Escocia","Costa de Marfil","Round of 16"),("Corea del Sur","Inglaterra","Round of 16"),
        ("Congo","Uruguay","Round of 16"),("Estados Unidos","Iran","Round of 16"),
        ("Austria","Australia","Round of 16"),("Bosnia","Colombia","Round of 16"),
        # Cuartos
        ("Alemania","Republica Checa","Quarter-finals"),("Congo","Estados Unidos","Quarter-finals"),
        ("Escocia","Corea del Sur","Quarter-finals"),("Austria","Bosnia","Quarter-finals"),
        # Semis
        ("Alemania","Congo","Semi-finals"),("Escocia","Austria","Semi-finals"),
    ]
    for local, visitante, ronda in eliminatorias:
        partidos.append({"match_id": mid, "fecha": fecha_e,
            "ronda": ronda, "equipo_local": local, "equipo_visitante": visitante,
            "goles_local": 1, "goles_visitante": 0,
            "penales_local": None, "penales_visitante": None, "estado": "FT"})
        mid += 1
        fecha_e += pd.Timedelta(hours=6)
    # 3er puesto
    partidos.append({"match_id": mid, "fecha": pd.Timestamp("2026-07-18"),
        "ronda": "3rd Place", "equipo_local": "Congo", "equipo_visitante": "Austria",
        "goles_local": 1, "goles_visitante": 0,
        "penales_local": None, "penales_visitante": None, "estado": "FT"})
    mid += 1
    # Final
    partidos.append({"match_id": mid, "fecha": pd.Timestamp("2026-07-19"),
        "ronda": "Final", "equipo_local": "Alemania", "equipo_visitante": "Escocia",
        "goles_local": 1, "goles_visitante": 0,
        "penales_local": None, "penales_visitante": None, "estado": "FT"})
    return partidos

@st.cache_data
def generar_resultados_simulados(fase_hasta="todo"):
    """
    Genera resultados simulados hasta una fase determinada.
    fase_hasta puede ser:
    - "todo": Torneo completo (default)
    - "grupos": Solo fase de grupos
    - "16vos": Grupos + 16vos
    - "8vos": Hasta 8vos
    - "4tos": Hasta cuartos
    - "semis": Hasta semis
    - "nada": Sin partidos jugados (todo NS)
    """
    partidos_grupos, mid = _generar_partidos_grupos()
    partidos_elim = _generar_eliminatorias(mid)
    todos = partidos_grupos + partidos_elim
    if fase_hasta == "nada":
        for p in todos:
            p["estado"] = "NS"
            p["goles_local"] = None
            p["goles_visitante"] = None
        return pd.DataFrame(todos)
    if fase_hasta == "todo":
        return pd.DataFrame(todos)
    # Mapeo de fases a rondas
    fases_rondas = {
        "grupos": {"Group A","Group B","Group C","Group D","Group E","Group F",
                   "Group G","Group H","Group I","Group J","Group K","Group L"},
        "16vos": {"Round of 32"},
        "8vos": {"Round of 16"},
        "4tos": {"Quarter-finals"},
        "semis": {"Semi-finals"},
        "final": {"Final", "3rd Place"},
    }
    # Determinar que rondas estan "jugadas"
    orden_fases = ["grupos", "16vos", "8vos", "4tos", "semis", "final"]
    rondas_jugadas = set()
    for fase in orden_fases:
        rondas_jugadas |= fases_rondas[fase]
        if fase == fase_hasta:
            break
    # Marcar como NS los partidos de rondas no jugadas
    for p in todos:
        if p["ronda"] not in rondas_jugadas:
            p["estado"] = "NS"
            p["goles_local"] = None
            p["goles_visitante"] = None
    return pd.DataFrame(todos)

def obtener_categorias_reales_simuladas():
    from utils.special_categories import calcular_todas_las_categorias
    resultados = generar_resultados_simulados("todo")
    categorias = calcular_todas_las_categorias(resultados)
    categorias["Figura"] = "Messi"
    categorias["Goleador"] = "Kane"
    return categorias
