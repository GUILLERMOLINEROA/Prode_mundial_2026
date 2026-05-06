"""
notifications.py — Reporte semanal del PRODE Mundialista 2026 (Oficina)

Envía un email personalizado a cada participante con:
- Su posición actual y puntos
- Un comentario sarcástico generado por Gemini
- Top 3 y leaderboard completo
- Resultados recientes

Ejecutado por GitHub Actions cada lunes a las 9 AM ART.
También se puede correr manualmente: python notifications.py [--test EMAIL]
"""
import os
import sys
import csv
import smtplib
import warnings
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="streamlit")
import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)

# Simular entorno Streamlit para que los imports funcionen
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

import pandas as pd
from utils.group_config import participantes_info_path

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =============================================================================
# PROMPT PARA GEMINI
# =============================================================================
SYSTEM_PROMPT = """Sos un analista de fútbol argentino, cínico, sarcástico y con humor negro.
Tu estilo es el de un hincha de café que sabe de fútbol pero se burla de todo el mundo.
Usás jerga argentina: "papá", "crack", "mufa", "colgado", "se comió los mocos", "está en el horno",
"la pegó", "está en llamas", "vendió humo", etc.

REGLAS ESTRICTAS:
- Máximo 3 oraciones.
- Si le va bien: alabalo con ironía, como que no te lo esperabas.
- Si le va mal: humillalo amistosamente, como un amigo que te carga.
- Si está en el medio: decile que es invisible, que nadie se acuerda de él.
- NUNCA uses insultos fuertes, racismo, sexismo ni nada ofensivo.
- NUNCA menciones temas fuera del fútbol o el PRODE.
- Siempre terminá con algo que duela pero con cariño.
"""

# =============================================================================
# FUNCIONES
# =============================================================================
def cargar_participantes_info():
    """Carga la lista de participantes con emails."""
    path = participantes_info_path()
    participantes = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codigo = row["codigo"].strip()
            participantes[codigo] = {
                "nombre": row["nombre"].strip(),
                "email": row["email"].strip(),
            }
    return participantes


def obtener_leaderboard():
    """Calcula el leaderboard actual usando la lógica existente. Retorna si usa simulación."""
    from utils.excel_reader import cargar_todos_los_participantes
    from utils.simulacion import generar_resultados_simulados, obtener_categorias_reales_simuladas
    from utils.scoring import calcular_puntuacion_total, generar_leaderboard
    from utils.data_loader import extraer_equipos_reales_por_ronda, determinar_campeon_y_tercero

    apuestas_grupos, pred_elim, categorias_todos, total_results_todos = cargar_todos_los_participantes()

    if not categorias_todos:
        print("ERROR: No se pudieron cargar participantes")
        return pd.DataFrame(), pd.DataFrame(), {}

    # Intentar datos reales primero, sino simulación
    usando_simulacion = False
    try:
        from utils.api_football import obtener_partidos_mundial, mapear_nombre_equipo
        resultados = obtener_partidos_mundial()
        if not resultados.empty:
            resultados["equipo_local"] = resultados["equipo_local"].apply(mapear_nombre_equipo)
            resultados["equipo_visitante"] = resultados["equipo_visitante"].apply(mapear_nombre_equipo)
        else:
            usando_simulacion = True
            resultados = generar_resultados_simulados("todo")
    except Exception:
        usando_simulacion = True
        resultados = generar_resultados_simulados("todo")

    categorias_reales = obtener_categorias_reales_simuladas()
    equipos_reales = extraer_equipos_reales_por_ronda(resultados)
    campeon_real, tercero_real = determinar_campeon_y_tercero(resultados)

    todos_puntajes = []
    for part in categorias_todos:
        puntaje = calcular_puntuacion_total(
            participante=part, apuestas_grupos=apuestas_grupos,
            categorias_pred=categorias_todos.get(part, {}),
            total_results_pred=total_results_todos.get(part, {}),
            resultados_reales=resultados,
            equipos_reales_por_ronda=equipos_reales,
            categorias_reales=categorias_reales,
            campeon_real=campeon_real, tercero_real=tercero_real)
        todos_puntajes.append(puntaje)

    leaderboard = generar_leaderboard(todos_puntajes)
    return leaderboard, resultados, categorias_todos, usando_simulacion


def obtener_resultados_recientes(resultados, cantidad=5):
    """Obtiene los últimos N resultados como strings."""
    if resultados.empty:
        return []
    finalizados = resultados[resultados["estado"] == "FT"].copy()
    if finalizados.empty:
        return []
    finalizados = finalizados.sort_values("fecha", ascending=False).head(cantidad)
    lista = []
    for _, p in finalizados.iterrows():
        gl = int(p["goles_local"])
        gv = int(p["goles_visitante"])
        lista.append(f"{p['equipo_local']} {gl} - {gv} {p['equipo_visitante']}")
    return lista


def generar_comentarios_batch(leaderboard, participantes_info):
    """Genera TODOS los comentarios en 1 sola llamada a Gemini (ahorra cuota)."""
    if not GEMINI_API_KEY:
        return {}

    # Construir contexto de todos los participantes
    lineas = []
    for _, row in leaderboard.iterrows():
        codigo = row["Participante"]
        posicion = int(row["Posición"])
        puntos = int(row["Total"])
        info = participantes_info.get(codigo, {})
        nombre = info.get("nombre", codigo)
        lineas.append(f"- #{posicion} {nombre} ({codigo}): {puntos} puntos")

    tabla = chr(10).join(lineas)
    total = len(leaderboard)
    lider = leaderboard.iloc[0]["Participante"] if len(leaderboard) > 0 else "?"

    prompt = f"""{SYSTEM_PROMPT}

Aca esta la tabla de posiciones del PRODE con {total} participantes:

{tabla}

Genera UN comentario corto (maximo 3 oraciones) para CADA participante.
Formato EXACTO (una linea por participante, sin saltar lineas extra):
CODIGO: comentario

Ejemplo:
GELA: Comentario para Guillermo...
FASA: Comentario para Facundo...
"""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        for intento in range(3):
            try:
                response = model.generate_content(prompt)
                texto = response.text.strip()
                break
            except Exception as api_err:
                if "429" in str(api_err) and intento < 2:
                    wait = 15 * (2 ** intento)
                    print(f"  Rate limit, esperando {wait}s (intento {intento+1}/3)...")
                    time.sleep(wait)
                else:
                    raise api_err

        # Parsear respuesta: "CODIGO: comentario"
        comentarios = {}
        for linea in texto.split(chr(10)):
            linea = linea.strip()
            if ":" in linea and len(linea) > 5:
                partes = linea.split(":", 1)
                cod = partes[0].strip().upper()
                com = partes[1].strip()
                if cod and com:
                    comentarios[cod] = com
        
        print(f"  Gemini genero {len(comentarios)} comentarios en 1 request")
        return comentarios

    except Exception as e:
        print(f"  Gemini batch error: {e}")
        return {}


def generar_comentario_gemini(nombre, codigo, posicion, total, puntos, puntos_lider):
    """Genera un comentario personalizado con Gemini."""
    if not GEMINI_API_KEY:
        return generar_comentario_fallback(nombre, posicion, total, puntos)

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        diferencia = puntos_lider - puntos
        if posicion == 1:
            contexto = f"{nombre} ({codigo}) va PRIMERO con {puntos} puntos. Es el líder."
        elif posicion <= 3:
            contexto = f"{nombre} ({codigo}) va #{posicion} con {puntos} puntos. Está a {diferencia} del líder."
        elif posicion <= total * 0.5:
            contexto = f"{nombre} ({codigo}) va #{posicion} de {total} con {puntos} puntos. Mitad de tabla. Mediocre."
        elif posicion < total:
            contexto = f"{nombre} ({codigo}) va #{posicion} de {total} con {puntos} puntos. En zona de descenso."
        else:
            contexto = f"{nombre} ({codigo}) va ÚLTIMO (#{posicion} de {total}) con {puntos} puntos. Desastre total."

        prompt = f"{SYSTEM_PROMPT}\n\nContexto: {contexto}\n\nGenerá el comentario para {nombre}:"

        # Retry con backoff: hasta 3 intentos, esperando 10s, 20s, 40s
        for intento in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as api_err:
                if "429" in str(api_err) and intento < 2:
                    wait = 10 * (2 ** intento)  # 10s, 20s, 40s
                    print(f"  Rate limit, esperando {wait}s (intento {intento+1}/3)...")
                    time.sleep(wait)
                else:
                    raise api_err
        return generar_comentario_fallback(nombre, posicion, total, puntos)

    except Exception as e:
        print(f"  Gemini error para {codigo}: {e}")
        return generar_comentario_fallback(nombre, posicion, total, puntos)


def generar_comentario_fallback(nombre, posicion, total, puntos):
    """Comentario de respaldo si Gemini no está disponible."""
    if posicion == 1:
        return f"{nombre} lidera con {puntos} puntos. ¿Suerte o talento? Seguramente suerte, pero disfrutalo mientras dure."
    elif posicion <= 3:
        return f"{nombre} en el podio con {puntos} puntos. Tan cerca del primero y tan lejos de la gloria. Seguí intentando."
    elif posicion <= total * 0.5:
        return f"{nombre} en el puesto {posicion} con {puntos} puntos. Ni frío ni calor. Invisible. Ni tu vieja se acuerda de tu PRODE."
    elif posicion < total:
        return f"{nombre} en el puesto {posicion}. Con {puntos} puntos estás más cerca del sótano que del podio. Repensá tus elecciones de vida."
    else:
        return f"{nombre}, último con {puntos} puntos. Un mono tirando dardos lo haría mejor. Literal."


def enviar_email(destinatario, nombre, asunto, html_body):
    """Envía un email por SMTP Gmail."""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print(f"  [SKIP] Sin credenciales de email. No se envió a {destinatario}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"Fabuloso Prode Mundialista <{EMAIL_USER}>"
    msg["To"] = destinatario

    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        print(f"  [OK] Email enviado a {nombre} ({destinatario})")
        return True
    except Exception as e:
        print(f"  [ERROR] Fallo enviando a {destinatario}: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 60)
    print("  PRODE MUNDIALISTA 2026 — REPORTE SEMANAL")
    print("=" * 60)

    # Modos de prueba:
    #   python notifications.py --test email@ejemplo.com      -> manda 1 mail
    #   python notifications.py --test-all email@ejemplo.com  -> manda todos los mails a esa casilla
    test_email = None
    test_all = False

    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        test_email = sys.argv[2]
        test_all = False
        print(f"\n🧪 MODO TEST — Enviando solo 1 mail a: {test_email}\n")

    elif len(sys.argv) >= 3 and sys.argv[1] == "--test-all":
        test_email = sys.argv[2]
        test_all = True
        print(f"\n🧪 MODO TEST-ALL — Enviando TODOS los mails a: {test_email}\n")

    # 1. Cargar datos
    print("\n1. Cargando participantes...")
    participantes_info = cargar_participantes_info()
    print(f"   {len(participantes_info)} participantes con email")

    print("\n2. Calculando leaderboard...")
    leaderboard, resultados, categorias, usando_simulacion = obtener_leaderboard()

    if leaderboard.empty:
        print("   ERROR: Leaderboard vacío. Abortando.")
        return

    if usando_simulacion:
        print("   ⚠️ ATENCIÓN: Se está usando SIMULACIÓN porque no hay datos reales de API.")
        if not test_email:
            print("   Envío real abortado para no mandar reportes con datos simulados.")
            return
        else:
            print("   Modo test: se permite usar simulación para validar el diseño del mail.")

    # Protección adicional:
    # Si la API tiene fixtures pero todos están programados (NS),
    # todavía no empezó la competencia. No mandar reporte competitivo.
    if not usando_simulacion and "estado" in resultados.columns:
        estados_competencia = {"1H", "2H", "HT", "ET", "P", "LIVE", "FT", "AET", "PEN"}
        hay_partido_jugado_o_en_vivo = resultados["estado"].isin(estados_competencia).any()
        if not hay_partido_jugado_o_en_vivo:
            print("   ⚠️ API disponible, pero todavía no hay partidos jugados/en vivo.")
            print("   Envío competitivo abortado hasta que empiece el Mundial.")
            return

    print(f"   {len(leaderboard)} participantes en el leaderboard")

    # 3. Obtener resultados recientes
    resultados_semana = obtener_resultados_recientes(resultados)
    print(f"\n3. Resultados recientes: {len(resultados_semana)}")

    # 4. Preparar datos comunes
    top3 = []
    for _, row in leaderboard.head(3).iterrows():
        top3.append({"nombre": row["Participante"], "puntos": int(row["Total"])})

    leaderboard_mini = []
    for _, row in leaderboard.iterrows():
        leaderboard_mini.append({
            "posicion": int(row["Posición"]),
            "nombre": row["Participante"],
            "puntos": int(row["Total"]),
        })

    puntos_lider = int(leaderboard.iloc[0]["Total"]) if len(leaderboard) > 0 else 0
    total_participantes = len(leaderboard)

    # 5. Generar y enviar emails
    print(f"\n4. Generando y enviando emails...")
    from utils.email_templates import generar_html_email

    # Generar todos los comentarios en 1 sola llamada a Gemini
    print(f"  Generando comentarios con Gemini (1 request para todos)...")
    comentarios_ia = generar_comentarios_batch(leaderboard, participantes_info)

    enviados = 0
    errores = 0

    for _, row in leaderboard.iterrows():
        codigo = row["Participante"]
        posicion = int(row["Posición"])
        puntos = int(row["Total"])

        info = participantes_info.get(codigo)
        if not info:
            print(f"  [SKIP] {codigo} no tiene email configurado")
            continue

        nombre = info["nombre"]
        email = info["email"]

        # En modo test, solo enviar al email de prueba
        if test_email:
            email = test_email

        print(f"\n  --- {codigo} ({nombre}) ---")

        # Usar comentario pre-generado por Gemini (batch) o fallback
        comentario = comentarios_ia.get(codigo, "")
        if not comentario:
            comentario = generar_comentario_fallback(nombre, posicion, total_participantes, puntos)
        print(f"  Comentario: {comentario[:80]}...")

        # Generar HTML
        html = generar_html_email(
            nombre=nombre,
            codigo=codigo,
            posicion=posicion,
            total_participantes=total_participantes,
            puntos=puntos,
            top3=top3,
            comentario_ia=comentario,
            resultados_semana=resultados_semana,
            leaderboard_mini=leaderboard_mini,
        )

        # Enviar
        if test_all:
            asunto = f"[TEST {codigo}] ⚽ PRODE Semanal — Va #{posicion} con {puntos} pts"
        else:
            asunto = f"⚽ PRODE Semanal — Vas #{posicion} con {puntos} pts"
        if enviar_email(email, nombre, asunto, html):
            enviados += 1
        else:
            errores += 1

        # Pausa entre participantes para no saturar Gemini (5s)
        if not test_email:
            time.sleep(5)

        # En modo test simple, solo enviar 1. En test-all, enviar todos.
        if test_email and not test_all:
            break

    print(f"\n{'=' * 60}")
    print(f"  RESUMEN: {enviados} enviados, {errores} errores")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
