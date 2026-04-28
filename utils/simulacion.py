import pandas as pd
import random
import streamlit as st

GRUPOS = {
    "A": ["Mexico", "Corea del Sur", "Republica Checa", "Sudafrica"],
    "B": ["Canada", "Qatar", "Suiza", "Bosnia"],
    "C": ["Brasil", "Haiti", "Escocia", "Marruecos"],
    "D": ["Estados Unidos", "Australia", "Turquia", "Paraguay"],
    "E": ["Alemania", "Costa de Marfil", "Ecuador", "Curazao"],
    "F": ["Paises Bajos", "Suecia", "Tunez", "Japon"],
    "G": ["Iran", "Belgica", "Nueva Zelanda", "Egipto"],
    "H": ["España", "Arabia Saudita", "Uruguay", "Cabo Verde"],
    "I": ["Francia", "Irak", "Noruega", "Senegal"],
    "J": ["Argentina", "Austria", "Jordania", "Argelia"],
    "K": ["Portugal", "Uzbekistan", "Colombia", "Congo"],
    "L": ["Inglaterra", "Ghana", "Panama", "Croacia"],
}

def _generar_goles(rng):
    return rng.choices([0, 1, 2, 3, 4], weights=[25, 35, 25, 10, 5])[0]

def _calcular_tabla_grupo(partidos_grupo):
    tabla = {}
    for p in partidos_grupo:
        for eq in [p["equipo_local"], p["equipo_visitante"]]:
            if eq not in tabla:
                tabla[eq] = {"pts": 0, "gf": 0, "gc": 0}
        gl, gv = p["goles_local"], p["goles_visitante"]
        if gl > gv: tabla[p["equipo_local"]]["pts"] += 3
        elif gv > gl: tabla[p["equipo_visitante"]]["pts"] += 3
        else:
            tabla[p["equipo_local"]]["pts"] += 1
            tabla[p["equipo_visitante"]]["pts"] += 1
        tabla[p["equipo_local"]]["gf"] += gl
        tabla[p["equipo_local"]]["gc"] += gv
        tabla[p["equipo_visitante"]]["gf"] += gv
        tabla[p["equipo_visitante"]]["gc"] += gl
    ranking = sorted(tabla.items(),
        key=lambda x: (x[1]["pts"], x[1]["gf"] - x[1]["gc"], x[1]["gf"]), reverse=True)
    return [eq for eq, _ in ranking]

def _generar_partido_eliminatoria(rng, eq1, eq2, match_id, fecha, ronda):
    g1 = _generar_goles(rng)
    g2 = _generar_goles(rng)
    pen1, pen2 = None, None
    if g1 == g2:
        pen1 = rng.randint(2, 5)
        pen2 = rng.randint(2, 5)
        while pen1 == pen2:
            pen2 = rng.randint(2, 5)
    ganador = eq1 if (g1 > g2 or (g1 == g2 and (pen1 or 0) > (pen2 or 0))) else eq2
    perdedor = eq2 if ganador == eq1 else eq1
    partido = {
        "match_id": match_id, "fecha": fecha, "ronda": ronda,
        "equipo_local": eq1, "equipo_visitante": eq2,
        "goles_local": g1, "goles_visitante": g2,
        "penales_local": pen1, "penales_visitante": pen2,
        "estado": "FT",
    }
    return partido, ganador, perdedor

@st.cache_data
def generar_resultados_simulados():
    rng = random.Random(42)
    partidos = []
    fecha_base = pd.Timestamp("2026-06-11")
    dia = 0
    
    # Fase de grupos
    for grupo, equipos in GRUPOS.items():
        cruces = [
            (equipos[0], equipos[2]), (equipos[1], equipos[3]),
            (equipos[0], equipos[3]), (equipos[2], equipos[1]),
            (equipos[2], equipos[0]), (equipos[3], equipos[1]),
        ]
        for local, visitante in cruces:
            partidos.append({
                "match_id": len(partidos) + 1,
                "fecha": fecha_base + pd.Timedelta(days=dia),
                "ronda": f"Group {grupo}",
                "equipo_local": local, "equipo_visitante": visitante,
                "goles_local": _generar_goles(rng),
                "goles_visitante": _generar_goles(rng),
                "penales_local": None, "penales_visitante": None,
                "estado": "FT",
            })
            dia += 0.5
    
    # Clasificados
    clasificados = {}
    for grupo, equipos in GRUPOS.items():
        pg = [p for p in partidos if p["equipo_local"] in equipos and p["equipo_visitante"] in equipos]
        clasificados[grupo] = _calcular_tabla_grupo(pg)
    
    primeros = {g: eq[0] for g, eq in clasificados.items()}
    segundos = {g: eq[1] for g, eq in clasificados.items()}
    terceros = [clasificados[g][2] for g in sorted(GRUPOS.keys())]
    rng.shuffle(terceros)
    
    mid = len(partidos) + 1
    fecha = pd.Timestamp("2026-07-01")
    t = 0
    
    # 16vos
    cruces_16 = [
        (segundos["A"], segundos["B"]), (primeros["E"], terceros[t:=0] if True else ""),
        (primeros["F"], segundos["C"]), (primeros["C"], segundos["F"]),
        (primeros["I"], terceros[1]), (segundos["E"], segundos["I"]),
        (primeros["A"], terceros[2]), (primeros["L"], terceros[3]),
        (primeros["D"], terceros[4]), (primeros["G"], terceros[5]),
        (segundos["K"], segundos["L"]), (primeros["H"], segundos["J"]),
        (primeros["B"], terceros[6]), (segundos["G"], segundos["H"]),
        (primeros["K"], terceros[7] if len(terceros) > 7 else terceros[0]),
        (segundos["D"], segundos["G"]),
    ]
    # Fix terceros
    cruces_16_fix = []
    ti = 0
    for eq1, eq2 in cruces_16:
        if not eq2 or eq2 == "":
            eq2 = terceros[ti % len(terceros)]
            ti += 1
        cruces_16_fix.append((eq1, eq2))
    
    gan_16 = []
    for eq1, eq2 in cruces_16_fix:
        p, gan, _ = _generar_partido_eliminatoria(rng, eq1, eq2, mid, fecha, "Round of 32")
        partidos.append(p)
        gan_16.append(gan)
        mid += 1
        fecha += pd.Timedelta(hours=12)
    
    # 8vos
    gan_8 = []
    for i in range(0, len(gan_16) - 1, 2):
        p, gan, _ = _generar_partido_eliminatoria(rng, gan_16[i], gan_16[i+1], mid, fecha, "Round of 16")
        partidos.append(p)
        gan_8.append(gan)
        mid += 1
        fecha += pd.Timedelta(hours=12)
    
    # 4tos
    gan_4 = []
    perd_4 = []
    for i in range(0, len(gan_8) - 1, 2):
        p, gan, perd = _generar_partido_eliminatoria(rng, gan_8[i], gan_8[i+1], mid, fecha, "Quarter-finals")
        partidos.append(p)
        gan_4.append(gan)
        perd_4.append(perd)
        mid += 1
        fecha += pd.Timedelta(hours=12)
    
    # Semis
    gan_semi = []
    perd_semi = []
    for i in range(0, len(gan_4) - 1, 2):
        p, gan, perd = _generar_partido_eliminatoria(rng, gan_4[i], gan_4[i+1], mid, fecha, "Semi-finals")
        partidos.append(p)
        gan_semi.append(gan)
        perd_semi.append(perd)
        mid += 1
        fecha += pd.Timedelta(days=1)
    
    # 3er puesto
    if len(perd_semi) >= 2:
        p, _, _ = _generar_partido_eliminatoria(rng, perd_semi[0], perd_semi[1], mid, fecha, "3rd Place")
        partidos.append(p)
        mid += 1
        fecha += pd.Timedelta(days=1)
    
    # Final
    if len(gan_semi) >= 2:
        p, _, _ = _generar_partido_eliminatoria(rng, gan_semi[0], gan_semi[1], mid, fecha, "Final")
        partidos.append(p)
    
    return pd.DataFrame(partidos)
