# =============================================================================
# utils/normalizar.py
# Normaliza nombres de equipos para corregir typos y variaciones
# entre los Excel de los participantes y los datos de la API/simulación.
# =============================================================================

# Mapeo de nombres incorrectos o con variaciones → nombre correcto
CORRECCIONES = {
    # Typos encontrados en los Excel
    "Repubilca Checa": "Republica Checa",
    "Republica checa": "Republica Checa",
    "republica checa": "Republica Checa",
    
    # Variaciones posibles de nombres
    "Países Bajos": "Paises Bajos",
    "Paises bajos": "Paises Bajos",
    "Corea Del Sur": "Corea del Sur",
    "corea del sur": "Corea del Sur",
    "Estados unidos": "Estados Unidos",
    "estados unidos": "Estados Unidos",
    "Costa De Marfil": "Costa de Marfil",
    "costa de marfil": "Costa de Marfil",
    "Arabia saudita": "Arabia Saudita",
    "arabia saudita": "Arabia Saudita",
    "Nueva zelanda": "Nueva Zelanda",
    "nueva zelanda": "Nueva Zelanda",
    "Cabo verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",
}


def normalizar_nombre_equipo(nombre: str) -> str:
    """
    Normaliza el nombre de un equipo corrigiendo typos y variaciones.
    Primero busca en el diccionario de correcciones.
    Si no lo encuentra, retorna el nombre original con strip.
    """
    if not nombre or not isinstance(nombre, str):
        return nombre
    
    nombre = nombre.strip()
    
    # Buscar corrección exacta
    if nombre in CORRECCIONES:
        return CORRECCIONES[nombre]
    
    return nombre
