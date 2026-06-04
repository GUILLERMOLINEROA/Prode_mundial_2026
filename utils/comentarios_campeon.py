import unicodedata


def _norm(txt):
    txt = str(txt or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt)
    return "".join(c for c in txt if not unicodedata.combining(c))


def _pais_propio_por_nacionalidad(nacionalidad):
    n = _norm(nacionalidad)

    if "argentin" in n:
        return "argentina"
    if "brasil" in n:
        return "brasil"
    if "mexican" in n:
        return "mexico"

    return None


def comentario_campeon_contextual(codigo, campeon, nacionalidad=""):
    campeon_n = _norm(campeon)
    nac_n = _norm(nacionalidad)
    pais_propio = _pais_propio_por_nacionalidad(nacionalidad)

    # Casos especiales según nacionalidad
    if campeon_n == "argentina":
        if "argentin" in nac_n:
            return "🇦🇷 VAMOS CARAJO. La Scaloneta no se discute. Patriota de ley."
        if "venezolan" in nac_n and "argentin" not in nac_n:
            return "🇦🇷 Se montó en la Scaloneta con fe prestada. No nació acá, pero eligió bien el bando."
        if "brasil" in nac_n:
            return "🇦🇷 Un/a brasilero/a poniendo a Argentina. Esto ya es conversión religiosa futbolera."
        if "mexican" in nac_n:
            return "🇦🇷 Se nacionalizó por conveniencia. Ojo, oportunista, pero boludo no."
        return "🇦🇷 Se subió a la Scaloneta. No será patriota, pero por lo menos no eligió una pavada."

    if campeon_n == "brasil":
        if pais_propio == "brasil":
            return "🇧🇷 Si sos brasilero/a y pusiste a Brasil, no es traición: es coherencia patriótica. Igual si se caen temprano, te van a cocinar vivo/a."
        if pais_propio == "argentina":
            return "🇧🇷 Ir con Brasil siendo argentino es como aplaudir un gol en contra. Audaz, pero peligrosísimo para tu reputación."
        return "🇧🇷 Apostó por Brasil. Resultadista, sí. Cobarde, quizá. Pero potencialmente rentable."

    if campeon_n == "mexico":
        if pais_propio == "mexico":
            return "🇲🇽 Patriota de manual. Banco la fe en el Tri, aunque el fantasma del quinto partido siempre pasa factura."
        if pais_propio == "argentina":
            return "🇲🇽 Apostar por México siendo argentino es una performance artística. Mucha fe, poca evidencia."
        return "🇲🇽 Se fue con México. Bastante romántico todo, ahora veamos si también era sensato."

    if campeon_n == "inglaterra":
        if pais_propio == "argentina":
            return "🏴 TRAIDOR A LA PATRIA DETECTADO. Inglaterra campeón no se explica ni con análisis clínico."
        return "🏴 Inglaterra campeón. Qué decisión de riesgo, hermano. O sos valiente o te gusta sufrir."

    # Fallbacks genéricos
    genericos = {
        "alemania": "🇩🇪 Frío, calculador, eficiente. Como un ingeniero alemán. Aburrido pero peligroso.",
        "ecuador": "🇪🇨 Ecuador campeón. Leíste bien. Ecuador. La audacia tiene un nombre.",
        "curazao": "🇨🇼 Curazao campeón. O sos un visionario o completaste el Excel con alcohol en sangre.",
        "republica checa": "🇨🇿 República Checa campeón. Hermoso delirio nostálgico.",
        "costa de marfil": "🇨🇮 Costa de Marfil campeón. Drogba te guiña un ojo desde el más allá futbolero.",
        "argelia": "🇩🇿 Argelia campeón. Si esto sale, merecés una estatua y terapia.",
        "francia": "🇫🇷 Francia. Después de Qatar. Memoria selectiva o masoquismo.",
        "espana": "🇪🇸 Tiki-taka, posesión y eliminación en cuartos. El clásico.",
        "portugal": "🇵🇹 CR7 con andador. Romántico pero delirante.",
        "paises bajos": "🇳🇱 La naranja mecánica: siempre de novios, nunca de boda.",
        "belgica": "🇧🇪 Generación dorada que se oxida sin ganar nada.",
        "uruguay": "🇺🇾 Los primos del charco. Garra charrúa, mate y nostalgia.",
        "colombia": "🇨🇴 Mucha cumbia, mucho talento. ¿Alcanza? Esa es la pregunta.",
        "croacia": "🇭🇷 Modric con 73 mundiales encima y todavía lo siguen bancando. Respetable.",
        "estados unidos": "🇺🇸 Esto no es el Super Bowl, hermano.",
        "japon": "🇯🇵 Si el anime enseñó algo es que Japón siempre pelea hasta el final.",
        "marruecos": "🇲🇦 Los leones del Atlas ya avisaron que no están para decorar.",
        "escocia": "🏴 Escocia campeón... y yo soy astronauta.",
        "noruega": "🇳🇴 Haaland y una oración.",
        "suiza": "🇨🇭 Neutral hasta en las apuestas.",
        "senegal": "🇸🇳 Valiente apuesta. Tiene más huevos que cálculo, pero respeto.",
        "bosnia": "🇧🇦 Bosnia. Inesperado. Audaz. Medio demente. Banco.",
        "canada": "🇨🇦 Esto no es hockey sobre hielo, amigo.",
    }

    return genericos.get(campeon_n, "Una elección interesante. Guardamos esto para julio.")
