"""
notifications_previa.py — Reporte semanal de LA PREVIA del PRODE Mundialista 2026

Se envía durante la etapa previa, antes del Mundial.
No usa puntos ni resultados reales. Usa:
- Orden de entrega
- Apuestas declaradas en los Excels
- Estadísticas de color
- Comentarios sarcásticos generados por Gemini en batch

Ejemplos:
  python notifications_previa.py --test prodemundialista2026@gmail.com
  python notifications_previa.py --test-all prodemundialista2026@gmail.com
  python notifications_previa.py
"""
import os
import sys
import csv
import smtplib
import warnings
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="streamlit")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import pandas as pd

EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

ESTIMADO_MIN = 25
ESTIMADO_MAX = 30

SYSTEM_PROMPT_PREVIA = """Sos el cronista oficial de la PREVIA de un PRODE mundialista de oficina argentina.

Tu tarea es generar comentarios personalizados para cada participante basándote en:
- orden de entrega
- campeón elegido
- goleador
- figura
- revelación
- decepción
- goles totales predichos

Tono:
- sarcástico, futbolero argentino, gracioso y picante
- cargada amistosa de oficina
- si entregó primero, cargalo por aplicado/ansioso
- si va último por ahora, cargalo pero aclarando que todavía puede zafar
- si puso Argentina campeón, celebralo como patriota
- si puso muchos goles, decile que vino a ver básquet
- si puso pocos goles, decile catenaccio/Mourinho
- máximo 3 oraciones por participante

Reglas:
- No insultos fuertes
- No temas personales sensibles
- No inventes datos
- No racismo/sexismo/discriminación
- Formato exacto:
CODIGO: comentario
"""


def cargar_participantes_info():
    path = os.path.join("data", "participantes_info.csv")
    info = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codigo = row["codigo"].strip()
            info[codigo] = {
                "nombre": row["nombre"].strip(),
                "email": row["email"].strip(),
            }
    return info


def cargar_entregas():
    path = os.path.join("data", "entregas.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df["codigo"] = df["codigo"].str.strip()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["hora"] = df["hora"].astype(str).str.strip()
    return df


def cargar_apuestas():
    from utils.excel_reader import cargar_todos_los_participantes
    grupos, elim, categorias, total_results = cargar_todos_los_participantes()

    goles_por_participante = {}
    if not grupos.empty:
        for p in grupos["participante"].unique():
            sub = grupos[grupos["participante"] == p]
            gl = sub["goles_local_pred"].sum()
            gv = sub["goles_visitante_pred"].sum()
            goles_por_participante[p] = int(gl + gv)

    return grupos, categorias, goles_por_participante


def calcular_stats_globales(categorias, goles_por_participante):
    # Campeones
    campeones = {}
    for codigo, cats in categorias.items():
        c = cats.get("Campeon", "?")
        campeones[c] = campeones.get(c, 0) + 1

    campeon_mas = "-"
    campeon_n = 0
    if campeones:
        campeon_mas, campeon_n = max(campeones.items(), key=lambda x: x[1])

    if goles_por_participante:
        goleador_max = max(goles_por_participante, key=goles_por_participante.get)
        goles_max = goles_por_participante[goleador_max]
        goleador_min = min(goles_por_participante, key=goles_por_participante.get)
        goles_min = goles_por_participante[goleador_min]
    else:
        goleador_max, goles_max = "-", 0
        goleador_min, goles_min = "-", 0

    return {
        "campeon_mas_elegido": campeon_mas,
        "campeon_mas_elegido_n": campeon_n,
        "goleador_max": goleador_max,
        "goles_max": goles_max,
        "goleador_min": goleador_min,
        "goles_min": goles_min,
    }


def generar_comentarios_batch_previa(entregas, participantes_info, categorias, goles_por_participante):
    """Genera todos los comentarios de previa en 1 request a Gemini."""
    if not GEMINI_API_KEY:
        return {}

    lineas = []
    total_entregados = len(entregas)

    for i, row in entregas.iterrows():
        codigo = row["codigo"]
        info = participantes_info.get(codigo, {})
        nombre = info.get("nombre", codigo)
        cats = categorias.get(codigo, {})
        goles = goles_por_participante.get(codigo, 0)

        lineas.append(
            f"- #{i+1} {nombre} ({codigo}) | Entrega: {row['fecha']} {row['hora']} | "
            f"Campeón: {cats.get('Campeon','?')} | Goleador: {cats.get('Goleador','?')} | "
            f"Figura: {cats.get('Figura','?')} | Revelación: {cats.get('Revelación','?')} | "
            f"Decepción: {cats.get('Decepción','?')} | Goles predichos: {goles}"
        )

    tabla = chr(10).join(lineas)

    prompt = f"""{SYSTEM_PROMPT_PREVIA}

Estado general:
- Entregaron {total_entregados} participantes
- Esperamos entre {ESTIMADO_MIN} y {ESTIMADO_MAX}
- Todavía estamos en la etapa previa, no hay partidos jugados ni puntos reales.

Datos:
{tabla}

Genera un comentario para cada participante.
Formato EXACTO:
CODIGO: comentario
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

        comentarios = {}
        for linea in texto.split(chr(10)):
            linea = linea.strip()
            if ":" in linea and len(linea) > 5:
                cod, com = linea.split(":", 1)
                comentarios[cod.strip().upper()] = com.strip()

        print(f"  Gemini genero {len(comentarios)} comentarios de previa en 1 request")
        return comentarios

    except Exception as e:
        print(f"  Gemini previa error: {e}")
        return {}


def comentario_fallback_previa(nombre, codigo, orden, total_entregados, campeon, goles):
    if orden == 1:
        return f"{nombre}, arrancaste primero como alumno aplicado. Bien por la puntualidad, pero el Excel rápido no garantiza saber de fútbol."
    elif orden == 2:
        return f"{nombre}, segundo en entregar. Casi aplicado, casi líder, casi todo. Veremos si en el PRODE también te quedás en la puerta."
    elif orden == total_entregados:
        return f"{nombre}, último por ahora. Todavía puede aparecer alguien más lento, pero de momento el trono de la pachorra es tuyo."
    elif campeon == "Argentina":
        return f"{nombre}, al menos pusiste Argentina campeón. La patria agradece, aunque tu conocimiento futbolístico sigue bajo auditoría."
    elif goles > 210:
        return f"{nombre}, pronosticaste {goles} goles. Esto es un mundial, no la NBA con botines."
    elif goles < 175:
        return f"{nombre}, con {goles} goles predichos venís más defensivo que Mourinho cuidando un 0-0 en la Bombonera."
    else:
        return f"{nombre}, entregaste y cumpliste. No sos héroe, pero tampoco villano. Por ahora, estadísticamente tolerable."


def enviar_email(destinatario, nombre, asunto, html_body):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print(f"  [SKIP] Sin credenciales. No se envio a {destinatario}")
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


def main():
    print("=" * 60)
    print("  PRODE MUNDIALISTA 2026 — REPORTE DE PREVIA")
    print("=" * 60)

    test_email = None
    test_all = False

    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        test_email = sys.argv[2]
        print(f"\n🧪 MODO TEST — Enviando 1 mail a: {test_email}\n")

    elif len(sys.argv) >= 3 and sys.argv[1] == "--test-all":
        test_email = sys.argv[2]
        test_all = True
        print(f"\n🧪 MODO TEST-ALL — Enviando TODOS los mails a: {test_email}\n")

    print("\n1. Cargando datos...")
    participantes_info = cargar_participantes_info()
    entregas = cargar_entregas()
    grupos, categorias, goles_por_participante = cargar_apuestas()

    total_entregados = len(entregas)
    print(f"   Entregas: {total_entregados}")
    print(f"   Participantes con email: {len(participantes_info)}")
    print(f"   Excels leidos: {len(categorias)}")

    stats = calcular_stats_globales(categorias, goles_por_participante)

    tabla_entregas = []
    for i, row in entregas.iterrows():
        tabla_entregas.append({
            "orden": i + 1,
            "codigo": row["codigo"],
            "fecha": row["fecha"],
            "hora": row["hora"],
        })

    print("\n2. Generando comentarios con Gemini...")
    comentarios = generar_comentarios_batch_previa(
        entregas, participantes_info, categorias, goles_por_participante)

    print("\n3. Enviando emails...")
    from utils.email_templates_previa import generar_html_email_previa

    enviados = 0
    errores = 0

    for i, row in entregas.iterrows():
        codigo = row["codigo"]
        info = participantes_info.get(codigo)
        if not info:
            print(f"  [SKIP] {codigo} no tiene email en participantes_info.csv")
            continue

        if codigo not in categorias:
            print(f"  [SKIP] {codigo} no tiene Excel/categorias cargadas")
            continue

        nombre = info["nombre"]
        email = info["email"]
        if test_email:
            email = test_email

        cats = categorias.get(codigo, {})
        goles = goles_por_participante.get(codigo, 0)
        orden = i + 1

        comentario = comentarios.get(codigo, "")
        if not comentario:
            comentario = comentario_fallback_previa(
                nombre=nombre,
                codigo=codigo,
                orden=orden,
                total_entregados=total_entregados,
                campeon=cats.get("Campeon", ""),
                goles=goles,
            )

        print(f"\n  --- {codigo} ({nombre}) ---")
        print(f"  Comentario: {comentario[:90]}...")

        html = generar_html_email_previa(
            nombre=nombre,
            codigo=codigo,
            orden_entrega=orden,
            total_entregados=total_entregados,
            estimado_min=ESTIMADO_MIN,
            estimado_max=ESTIMADO_MAX,
            fecha_entrega=row["fecha"],
            hora_entrega=row["hora"],
            campeon=cats.get("Campeon", "?"),
            goleador=cats.get("Goleador", "?"),
            figura=cats.get("Figura", "?"),
            revelacion=cats.get("Revelación", "?"),
            decepcion=cats.get("Decepción", "?"),
            goles_totales=goles,
            comentario_ia=comentario,
            stats_globales=stats,
            tabla_entregas=tabla_entregas,
        )

        if test_all:
            asunto = f"[TEST {codigo}] 🎭 La Previa del PRODE — Entrega #{orden}"
        else:
            asunto = f"🎭 La Previa del PRODE — Entrega #{orden}"

        if enviar_email(email, nombre, asunto, html):
            enviados += 1
        else:
            errores += 1

        if not test_email:
            time.sleep(5)

        if test_email and not test_all:
            break

    print(f"\n{'=' * 60}")
    print(f"  RESUMEN: {enviados} enviados, {errores} errores")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
