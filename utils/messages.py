# =============================================================================
# utils/messages.py
# Generador de mensajes sarcásticos y burlones según la posición del
# participante en el leaderboard.
#
# Porque en un PRODE de oficina, el bullying deportivo es parte del juego. 😈
# =============================================================================

import random
from typing import List


def obtener_mensaje_posicion(
    participante: str,
    posicion: int,
    total_participantes: int,
    puntos: int
) -> str:
    """
    Genera un mensaje sarcástico basado en la posición actual del participante.
    
    El tono varía dramáticamente:
    - Top 1: Adoración total
    - Top 3: Respeto con reservas
    - Mitad de tabla: Burla suave
    - Últimos 3: Humillación pública
    - Último lugar: Destrucción total
    """
    nombre = participante.split()[0] if " " in participante else participante
    
    # --- PRIMER LUGAR ---
    if posicion == 1:
        mensajes = [
            f"👑 {nombre} reina con puño de hierro. {puntos} puntos de pura genialidad futbolística. "
            f"¿O será pura suerte? El tiempo lo dirá... pero por ahora, ARRODÍLLENSE.",
            
            f"🔥 {nombre} lidera con {puntos} puntos. Mientras ustedes apostaban con el corazón, "
            f"este/a apostaba con el cerebro. Se acepta la rendición incondicional.",
            
            f"🏆 {nombre} va primero con {puntos} puntos. Dicen que el poder corrompe... "
            f"pero qué lindo se siente estar arriba, ¿no {nombre}?",
            
            f"⚡ {nombre} domina con {puntos} puntos. Si el PRODE fuera un deporte olímpico, "
            f"ya tendría la medalla de oro colgada.",
        ]
    
    # --- SEGUNDO LUGAR ---
    elif posicion == 2:
        mensajes = [
            f"🥈 {nombre} va segundo con {puntos} puntos. Tan cerca y tan lejos. "
            f"El segundo es el primero de los perdedores, dicen...",
            
            f"📈 {nombre} acecha desde el segundo lugar ({puntos} pts). "
            f"Como un tiburón esperando que el líder se relaje. Paciencia, joven padawan.",
            
            f"🔥 {nombre} va pisándole los talones al líder con {puntos} puntos. "
            f"¿Remontada épica o eterno subcampeón? Apuesten.",
        ]
    
    # --- TERCER LUGAR ---
    elif posicion == 3:
        mensajes = [
            f"🥉 {nombre} completa el podio con {puntos} puntos. "
            f"Tercer lugar: lo suficiente para presumir, no tanto para ganar.",
            
            f"🎖️ {nombre} en el 3er puesto ({puntos} pts). "
            f"El bronce no brilla como el oro, pero al menos no da vergüenza.",
        ]
    
    # --- MITAD SUPERIOR (top 40%) ---
    elif posicion <= total_participantes * 0.4:
        mensajes = [
            f"😐 {nombre} va en el puesto {posicion} con {puntos} puntos. "
            f"Ni frío ni calor. Como empate 0-0 en un amistoso.",
            
            f"🤷 {nombre} navega en el puesto {posicion} ({puntos} pts). "
            f"Rendimiento tibio. Ni para celebrar ni para llorar.",
            
            f"📊 {nombre} en posición {posicion} con {puntos} puntos. "
            f"Estadísticamente irrelevante, pero técnicamente vivo/a.",
        ]
    
    # --- MITAD INFERIOR ---
    elif posicion <= total_participantes * 0.7:
        mensajes = [
            f"😬 {nombre} languidece en el puesto {posicion} ({puntos} pts). "
            f"¿Hiciste las apuestas con los ojos cerrados o fue intencional?",
            
            f"📉 {nombre} cae al puesto {posicion} con apenas {puntos} puntos. "
            f"A este ritmo, el conserje del estadio hace mejor PRODE.",
            
            f"🥶 {nombre} tirita en el puesto {posicion} ({puntos} pts). "
            f"Si esto fuera fútbol, ya te habrían mandado a la reserva.",
        ]
    
    # --- PENÚLTIMOS ---
    elif posicion < total_participantes:
        mensajes = [
            f"💀 {nombre} agoniza en el puesto {posicion} con {puntos} puntos miserables. "
            f"¿Estás seguro/a de que ves fútbol? Porque no parece.",
            
            f"🪦 {nombre} se arrastra en el puesto {posicion} ({puntos} pts). "
            f"Tu PRODE es tan malo que debería ser ilegal.",
            
            f"🚨 {nombre} en el puesto {posicion} ({puntos} pts). "
            f"ALERTA: nivel de vergüenza deportiva crítico. Evacuación inmediata.",
            
            f"❄️ CONGELADO/A: {nombre} en el puesto {posicion} ({puntos} pts). "
            f"Más frío/a que un pingüino en la Antártida.",
        ]
    
    # --- ÚLTIMO LUGAR ---
    else:
        mensajes = [
            f"🗑️ {nombre} es ÚLTIMO/A con {puntos} puntos. "
            f"Enhorabuena, has logrado lo imposible: ser peor que TODOS. "
            f"Tu conocimiento futbolístico es oficialmente una leyenda... de terror.",
            
            f"☠️ ÚLTIMO LUGAR para {nombre} ({puntos} pts). "
            f"Si las apuestas fueran al revés, serías campeón/a. "
            f"Quizás deberías probar esa estrategia.",
            
            f"🤡 {nombre} cierra la tabla con {puntos} puntos. "
            f"Ni un mono tirando dardos lo haría peor. De hecho, "
            f"un mono probablemente lo haría MEJOR.",
            
            f"💩 {nombre}... {puntos} puntos... último lugar... "
            f"No hay palabras. Solo silencio. Y vergüenza. Mucha vergüenza.",
        ]
    
    return random.choice(mensajes)


def obtener_titulo_ficha(posicion: int, total: int) -> str:
    """
    Retorna el título de la ficha de un participante según su posición.
    """
    if posicion == 1:
        return "🏆 FICHA DE GLORIA ABSOLUTA 🏆"
    elif posicion <= 3:
        return "⭐ Ficha de Gloria (con asterisco)"
    elif posicion <= total * 0.5:
        return "📋 Ficha del Mediocre"
    elif posicion < total:
        return "📉 Ficha de Humillación"
    else:
        return "💀 FICHA DE VERGÜENZA MÁXIMA 💀"


def obtener_mensajes_errores(errores: List[dict]) -> List[str]:
    """
    Genera mensajes sarcásticos para los peores errores de un participante.
    """
    mensajes = []
    
    comentarios_error = [
        "¿En serio? ¿EN SERIO?",
        "Ni tu abuela habría apostado eso.",
        "Esto es de museo de los horrores.",
        "¿Estabas dormido/a cuando hiciste esta apuesta?",
        "Un generador de números random lo hacía mejor.",
        "Esto duele de solo verlo.",
        "Apuesta criminal. Debería haber consecuencias legales.",
        "¿Le pediste consejo a un gato?",
    ]
    
    for i, error in enumerate(errores):
        comentario = comentarios_error[i % len(comentarios_error)]
        partido = error.get("partido", "Desconocido")
        pred = error.get("prediccion", "?-?")
        real = error.get("real", "?-?")
        mensajes.append(
            f"**{partido}**: Apostaste {pred}, fue {real}. {comentario}"
        )
    
    return mensajes
