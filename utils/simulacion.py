import pandas as pd
import streamlit as st

@st.cache_data
def generar_resultados_simulados():
    partidos = []
    mid = 1

    # GRUPO A
    for local, gl, gv, visitante, fecha in [
        ("Mexico", 1, 1, "Sudafrica", "11/6/2026"), ("Corea del Sur", 2, 1, "Republica Checa", "11/6/2026"),
        ("Republica Checa", 1, 1, "Sudafrica", "18/6/2026"), ("Mexico", 1, 3, "Corea del Sur", "18/6/2026"),
        ("Republica Checa", 2, 1, "Mexico", "24/6/2026"), ("Sudafrica", 1, 1, "Corea del Sur", "24/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group A",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO B
    for local, gl, gv, visitante, fecha in [
        ("Canada", 1, 3, "Bosnia", "12/6/2026"), ("Qatar", 0, 0, "Suiza", "13/6/2026"),
        ("Suiza", 1, 1, "Bosnia", "18/6/2026"), ("Canada", 1, 1, "Qatar", "18/6/2026"),
        ("Suiza", 1, 0, "Canada", "24/6/2026"), ("Bosnia", 3, 1, "Qatar", "24/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group B",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO C
    for local, gl, gv, visitante, fecha in [
        ("Brasil", 2, 3, "Marruecos", "13/6/2026"), ("Haiti", 1, 2, "Escocia", "13/6/2026"),
        ("Brasil", 3, 3, "Haiti", "19/6/2026"), ("Escocia", 1, 1, "Marruecos", "19/6/2026"),
        ("Escocia", 3, 2, "Brasil", "24/6/2026"), ("Marruecos", 2, 3, "Haiti", "24/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group C",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO D
    for local, gl, gv, visitante, fecha in [
        ("Estados Unidos", 0, 1, "Paraguay", "12/6/2026"), ("Australia", 2, 1, "Turquia", "14/6/2026"),
        ("Turquia", 3, 1, "Paraguay", "20/6/2026"), ("Estados Unidos", 3, 0, "Australia", "19/6/2026"),
        ("Turquia", 0, 1, "Estados Unidos", "25/6/2026"), ("Paraguay", 2, 3, "Australia", "25/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group D",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO E
    for local, gl, gv, visitante, fecha in [
        ("Alemania", 3, 1, "Curazao", "14/6/2026"), ("Costa de Marfil", 2, 0, "Ecuador", "14/6/2026"),
        ("Alemania", 1, 0, "Costa de Marfil", "20/6/2026"), ("Ecuador", 0, 0, "Curazao", "20/6/2026"),
        ("Ecuador", 0, 3, "Alemania", "25/6/2026"), ("Curazao", 3, 3, "Costa de Marfil", "25/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group E",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO F
    for local, gl, gv, visitante, fecha in [
        ("Paises Bajos", 1, 3, "Japon", "17/6/2026"), ("Suecia", 0, 0, "Tunez", "14/6/2026"),
        ("Paises Bajos", 1, 1, "Suecia", "20/6/2026"), ("Tunez", 0, 2, "Japon", "21/6/2026"),
        ("Japon", 3, 1, "Suecia", "25/6/2026"), ("Tunez", 1, 1, "Paises Bajos", "25/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group F",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO G
    for local, gl, gv, visitante, fecha in [
        ("Iran", 2, 0, "Nueva Zelanda", "15/6/2026"), ("Belgica", 1, 1, "Egipto", "15/6/2026"),
        ("Belgica", 3, 2, "Iran", "21/6/2026"), ("Nueva Zelanda", 2, 1, "Egipto", "21/6/2026"),
        ("Nueva Zelanda", 2, 0, "Belgica", "27/6/2026"), ("Egipto", 0, 1, "Iran", "27/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group G",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO H
    for local, gl, gv, visitante, fecha in [
        ("España", 3, 0, "Cabo Verde", "15/6/2026"), ("Arabia Saudita", 1, 2, "Uruguay", "15/6/2026"),
        ("España", 3, 3, "Arabia Saudita", "21/6/2026"), ("Uruguay", 1, 0, "Cabo Verde", "21/6/2026"),
        ("Uruguay", 3, 3, "España", "26/6/2026"), ("Cabo Verde", 0, 1, "Arabia Saudita", "26/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group H",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO I
    for local, gl, gv, visitante, fecha in [
        ("Francia", 0, 1, "Senegal", "16/6/2026"), ("Irak", 0, 1, "Noruega", "16/6/2026"),
        ("Francia", 2, 3, "Irak", "22/6/2026"), ("Noruega", 1, 1, "Senegal", "22/6/2026"),
        ("Noruega", 2, 1, "Francia", "26/6/2026"), ("Senegal", 0, 0, "Irak", "26/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group I",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO J
    for local, gl, gv, visitante, fecha in [
        ("Argentina", 2, 2, "Argelia", "16/6/2026"), ("Austria", 3, 1, "Jordania", "17/6/2026"),
        ("Argentina", 0, 1, "Austria", "22/6/2026"), ("Jordania", 2, 3, "Argelia", "23/6/2026"),
        ("Jordania", 2, 0, "Argentina", "27/6/2026"), ("Argelia", 0, 0, "Austria", "27/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group J",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO K
    for local, gl, gv, visitante, fecha in [
        ("Portugal", 0, 1, "Congo", "17/6/2026"), ("Uzbekistan", 2, 3, "Colombia", "17/6/2026"),
        ("Portugal", 3, 2, "Uzbekistan", "23/6/2026"), ("Colombia", 1, 1, "Congo", "23/6/2026"),
        ("Colombia", 3, 2, "Portugal", "27/6/2026"), ("Congo", 0, 1, "Uzbekistan", "27/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group K",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # GRUPO L
    for local, gl, gv, visitante, fecha in [
        ("Inglaterra", 0, 1, "Croacia", "17/6/2026"), ("Ghana", 0, 2, "Panama", "17/6/2026"),
        ("Inglaterra", 1, 1, "Ghana", "23/6/2026"), ("Panama", 2, 3, "Croacia", "23/6/2026"),
        ("Panama", 1, 2, "Inglaterra", "27/6/2026"), ("Croacia", 1, 3, "Ghana", "27/6/2026")]:
        partidos.append({"match_id": mid, "fecha": pd.Timestamp(fecha), "ronda": "Group L",
            "equipo_local": local, "equipo_visitante": visitante, "goles_local": gl, "goles_visitante": gv,
            "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1

    # ELIMINATORIAS - todos 1-0
    fecha_e = pd.Timestamp("2026-07-01")
    for local, visitante, ronda in [
        ("Republica Checa","Suiza","Round of 32"),("Alemania","Marruecos","Round of 32"),
        ("Japon","Haiti","Round of 32"),("Escocia","Paises Bajos","Round of 32"),
        ("Noruega","Turquia","Round of 32"),("Costa de Marfil","Senegal","Round of 32"),
        ("Corea del Sur","Arabia Saudita","Round of 32"),("Croacia","Irak","Round of 32"),
        ("Estados Unidos","Jordania","Round of 32"),("Iran","Sudafrica","Round of 32"),
        ("Congo","Ghana","Round of 32"),("Uruguay","Argelia","Round of 32"),
        ("Bosnia","Belgica","Round of 32"),("Austria","España","Round of 32"),
        ("Colombia","Inglaterra","Round of 32"),("Australia","Nueva Zelanda","Round of 32"),
        ("Alemania","Noruega","Round of 16"),("Republica Checa","Japon","Round of 16"),
        ("Escocia","Costa de Marfil","Round of 16"),("Corea del Sur","Croacia","Round of 16"),
        ("Congo","Uruguay","Round of 16"),("Estados Unidos","Iran","Round of 16"),
        ("Austria","Australia","Round of 16"),("Bosnia","Colombia","Round of 16"),
        ("Alemania","Republica Checa","Quarter-finals"),("Congo","Estados Unidos","Quarter-finals"),
        ("Escocia","Corea del Sur","Quarter-finals"),("Austria","Bosnia","Quarter-finals"),
        ("Alemania","Congo","Semi-finals"),("Escocia","Austria","Semi-finals")]:
        partidos.append({"match_id": mid, "fecha": fecha_e, "ronda": ronda,
            "equipo_local": local, "equipo_visitante": visitante,
            "goles_local": 1, "goles_visitante": 0,
            "penales_local": None, "penales_visitante": None, "estado": "FT"})
        mid += 1; fecha_e += pd.Timedelta(hours=6)

    # 3er puesto y Final
    partidos.append({"match_id": mid, "fecha": pd.Timestamp("2026-07-18"), "ronda": "3rd Place",
        "equipo_local": "Congo", "equipo_visitante": "Austria", "goles_local": 1, "goles_visitante": 0,
        "penales_local": None, "penales_visitante": None, "estado": "FT"}); mid += 1
    partidos.append({"match_id": mid, "fecha": pd.Timestamp("2026-07-19"), "ronda": "Final",
        "equipo_local": "Alemania", "equipo_visitante": "Escocia", "goles_local": 1, "goles_visitante": 0,
        "penales_local": None, "penales_visitante": None, "estado": "FT"})

    return pd.DataFrame(partidos)


def obtener_categorias_reales_simuladas():
    """
    Calcula las categorias automaticamente a partir de los resultados simulados.
    Figura y Goleador se definen manualmente.
    """
    from utils.special_categories import calcular_todas_las_categorias
    resultados = generar_resultados_simulados()
    categorias = calcular_todas_las_categorias(resultados)
    # Override manual para Figura y Goleador
    categorias["Figura"] = "Messi"
    categorias["Goleador"] = "Messi"
    return categorias
