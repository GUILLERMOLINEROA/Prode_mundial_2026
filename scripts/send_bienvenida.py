"""
Mail de bienvenida genérico para cualquier grupo del PRODE Mundialista 2026.
Lee el config.json del grupo para ajustar tono y nombre.

Uso:
  python scripts/send_bienvenida.py losamigosesos --test prodemundialista2026@gmail.com
  python scripts/send_bienvenida.py losamigosesos --test-all prodemundialista2026@gmail.com
  python scripts/send_bienvenida.py losamigosesos   (envía a todos los reales)
"""
import os
import sys
import json
import smtplib
import base64
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def cargar_config(group_id):
    path = os.path.join("data", "groups", group_id, "config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_participantes(group_id):
    path = os.path.join("data", "groups", group_id, "participantes_info.csv")
    participantes = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            participantes.append({
                "codigo": row["codigo"].strip(),
                "nombre": row["nombre"].strip(),
                "email": row["email"].strip(),
            })
    return participantes


def cargar_banner_url(group_id):
    """Devuelve URL pública del banner desde GitHub (Gmail no soporta base64)."""
    return f"https://raw.githubusercontent.com/GUILLERMOLINEROA/Prode_mundial_2026/main/data/groups/{group_id}/banners/banner1_email.jpg"


def generar_html(nombre, banner_url, config, group_id, app_url, participantes):
    nombre_display = config.get("nombre_display", f"PRODE {group_id}")
    tono = config.get("tono", "normal")

    if tono == "ultra_picante":
        saludo = f"Epa <b>{nombre}</b>, ¿qué más pana?"
        nombres_todos = [pp["nombre"] for pp in participantes]
        if len(nombres_todos) > 1:
            lista_nombres = ", ".join(nombres_todos[:-1]) + " y " + nombres_todos[-1]
        else:
            lista_nombres = nombres_todos[0] if nombres_todos else "nadie"
        intro = (
            f"Esto es oficial: el <b style='color:#C8E600;'>{nombre_display}</b> está en marcha, "
            f"marico. Sí, así como lo lees. Somos {len(nombres_todos)} pajúos en esta vaina: "
            f"<b>{lista_nombres}</b>. "
            "Vamos a ver quién de este grupo sabe de verdad de fútbol y quién solo sabe hablar paja."
        )
        que_es_titulo = "🤔 ¿QUÉ VERGA ES UN PRODE?"
        que_es_texto = (
            "Simple, pana: completás un Excel con tus predicciones para <b>TODOS</b> los partidos "
            "del Mundial 2026. Fase de grupos, eliminatorias, quién gana, cuántos goles, "
            "quién es el campeón, goleador, figura, revelación, decepción... TODO. "
            "Después la realidad te destruye los sueños y sumamos puntos según "
            "cuánto le pegaste. El que más puntos tenga al final es el crack. "
            "El último es el pajúo oficial del grupo."
        )
        penalidades_intro = "Si la cagás feo con tus predicciones, te restan puntos, pajúo:"
        penalidades_cierre = "Así que pensá bien antes de poner cualquier chimbazo."
        pasos = (
            "1️⃣ Agarrá el Excel que te van a mandar (o que ya te mandaron)<br>"
            "2️⃣ Completalo con tus predicciones. <b>TODO</b>, no seas flojo<br>"
            "3️⃣ Mandalo de vuelta antes del <b style='color:#E74C3C;'>1 de junio de 2026</b><br>"
            "4️⃣ Sentate a esperar que el mundial te demuestre que no sabés nada<br>"
            "5️⃣ Recibí los mails semanales donde te vamos a humillar públicamente"
        )
        app_texto = (
            "Tenemos una app donde vas a poder ver en tiempo real quién va ganando, "
            "quién la está cagando, y quién merece que le caigan a coñazos por sus predicciones. "
            "Durante el mundial se actualiza cada minuto con los resultados en vivo."
        )
        cierre = (
            f"Así que ya sabés, <b>{nombre}</b>: completá el Excel, mandalo, y preparate "
            "para sufrir. Esto va a ser burda de arrecho. 🔥"
        )
        cierre2 = (
            "El que no participe es un cobarde. Y el que participe y pierda... bueno, "
            "al menos tuvo los huevos de intentarlo. 😈"
        )
        header_sub = "🔥 ARRANCÓ ESTA VAINA, CHAMO 🔥"
        footer_tag = "Sin piedad, sin filtro, full pana"
    else:
        saludo = f"Hola <b>{nombre}</b>,"
        intro = (
            f"Te damos la bienvenida al <b style='color:#C8E600;'>{nombre_display}</b>. "
            "Preparate para competir, sufrir y probablemente perder con dignidad."
        )
        que_es_titulo = "🤔 ¿QUÉ ES UN PRODE?"
        que_es_texto = (
            "Completás un Excel con tus predicciones para todos los partidos "
            "del Mundial 2026: fase de grupos, eliminatorias, campeón, goleador, "
            "figura, revelación, decepción. Se suman puntos según cuánto acertás. "
            "El que más puntos tenga gana. El último sufre."
        )
        penalidades_intro = "Si te equivocás feo, te restan puntos:"
        penalidades_cierre = "Pensá bien antes de apostar."
        pasos = (
            "1️⃣ Completá el Excel con tus predicciones<br>"
            "2️⃣ Mandalo antes del <b style='color:#E74C3C;'>1 de junio de 2026</b><br>"
            "3️⃣ Esperá que arranque el mundial<br>"
            "4️⃣ Recibí reportes semanales con tu posición"
        )
        app_texto = (
            "Tenemos una app donde podés ver en tiempo real las posiciones, "
            "resultados y estadísticas. Se actualiza cada minuto durante los partidos."
        )
        cierre = f"Así que ya sabés, <b>{nombre}</b>: completá el Excel y preparate."
        cierre2 = "El que no participa se lo pierde. 😈"
        header_sub = "🏆 ARRANCÓ LA COMPETENCIA 🏆"
        footer_tag = "Donde las amistades se prueban"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0; padding:0; background-color:#0D1117; font-family:Segoe UI, Arial, sans-serif;">
        <div style="max-width:620px; margin:0 auto; background-color:#1B2838; border:1px solid #2C3E50;">

            <div style="text-align:center; padding:0;">
                <img src="{banner_url}"
                     style="max-width:100%; border-radius:0;">
            </div>

            <div style="background:linear-gradient(135deg, #1B2838, #2C3E50); padding:25px; text-align:center;
                        border-bottom:2px solid #C8E600;">
                <h1 style="color:#C8E600; margin:0; font-size:24px;">⚽ {nombre_display} ⚽</h1>
                <p style="color:#E74C3C; margin:8px 0 0 0; font-size:16px; font-weight:bold;">
                    {header_sub}</p>
            </div>

            <div style="padding:25px;">
                <p style="color:#FFFFFF; font-size:16px; line-height:1.6;">{saludo}</p>
                <p style="color:#AEC6CF; font-size:15px; line-height:1.7;">{intro}</p>

                <div style="background:#2C3E50; border-left:3px solid #C8E600; padding:15px; margin:20px 0;
                            border-radius:0 8px 8px 0;">
                    <p style="color:#C8E600; font-size:14px; font-weight:bold; margin:0 0 8px 0;">
                        {que_es_titulo}</p>
                    <p style="color:#FFFFFF; font-size:14px; margin:0; line-height:1.6;">{que_es_texto}</p>
                </div>

                <div style="background:#2C3E50; border-left:3px solid #E74C3C; padding:15px; margin:20px 0;
                            border-radius:0 8px 8px 0;">
                    <p style="color:#E74C3C; font-size:14px; font-weight:bold; margin:0 0 10px 0;">
                        📊 SISTEMA DE PUNTUACIÓN (431 pts máximo)</p>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <tr><td style="color:#AEC6CF; padding:3px 0;">⚽ Acertar ganador en grupos</td>
                            <td style="color:#C8E600; text-align:right;">1 pt x 72 = 72</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🎯 Resultado exacto en grupos</td>
                            <td style="color:#C8E600; text-align:right;">1 pt x 72 = 72</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏟️ Acertar clasificado 16vos</td>
                            <td style="color:#C8E600; text-align:right;">1 pt x 32 = 32</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏟️ Acertar clasificado 8vos</td>
                            <td style="color:#C8E600; text-align:right;">3 pts x 16 = 48</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏟️ Acertar clasificado 4tos</td>
                            <td style="color:#C8E600; text-align:right;">6 pts x 8 = 48</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏟️ Acertar semifinalista</td>
                            <td style="color:#C8E600; text-align:right;">10 pts x 4 = 40</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏟️ Acertar finalista</td>
                            <td style="color:#C8E600; text-align:right;">15 pts x 2 = 30</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🥉 Acertar 3er puesto</td>
                            <td style="color:#C8E600; text-align:right;">5 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">🏆 Acertar campeón</td>
                            <td style="color:#C8E600; text-align:right;">20 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">⭐ Acertar figura del torneo</td>
                            <td style="color:#C8E600; text-align:right;">12 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">⚽ Acertar goleador</td>
                            <td style="color:#C8E600; text-align:right;">12 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">💡 Acertar revelación</td>
                            <td style="color:#C8E600; text-align:right;">12 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">💀 Acertar decepción</td>
                            <td style="color:#C8E600; text-align:right;">12 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">📈 Acertar mejor 1era fase</td>
                            <td style="color:#C8E600; text-align:right;">8 pts</td></tr>
                        <tr><td style="color:#AEC6CF; padding:3px 0;">📉 Acertar peor equipo</td>
                            <td style="color:#C8E600; text-align:right;">8 pts</td></tr>
                    </table>
                </div>

                <div style="background:#2C3E50; border-left:3px solid #F39C12; padding:15px; margin:20px 0;
                            border-radius:0 8px 8px 0;">
                    <p style="color:#F39C12; font-size:14px; font-weight:bold; margin:0 0 8px 0;">
                        ⚠️ PENALIDADES (máximo -70 pts)</p>
                    <p style="color:#FFFFFF; font-size:13px; margin:0; line-height:1.6;">
                        {penalidades_intro}<br>
                        • Tu revelación se queda en grupos: <b style="color:#E74C3C;">-20 pts</b><br>
                        • Tu campeón no llega ni a 4tos: <b style="color:#E74C3C;">-20 pts</b><br>
                        • Tu peor equipo pasa de grupos: <b style="color:#E74C3C;">-10 pts</b><br>
                        • Tu decepción llega a semis: <b style="color:#E74C3C;">-20 pts</b><br>
                        <span style="color:#E74C3C;">{penalidades_cierre}</span>
                    </p>
                </div>

                <div style="background:#2C3E50; border-left:3px solid #9B59B6; padding:15px; margin:20px 0;
                            border-radius:0 8px 8px 0;">
                    <p style="color:#9B59B6; font-size:14px; font-weight:bold; margin:0 0 8px 0;">
                        📋 ¿QUÉ TENÉS QUE HACER?</p>
                    <p style="color:#FFFFFF; font-size:14px; margin:0; line-height:1.8;">{pasos}</p>
                </div>

                <div style="background:#2C3E50; border-left:3px solid #4A90D9; padding:15px; margin:20px 0;
                            border-radius:0 8px 8px 0;">
                    <p style="color:#4A90D9; font-size:14px; font-weight:bold; margin:0 0 8px 0;">
                        📱 LA APP</p>
                    <p style="color:#FFFFFF; font-size:14px; margin:0; line-height:1.6;">
                        {app_texto}<br><br>
                        <a href="{app_url}" style="color:#C8E600; font-size:16px; font-weight:bold;
                           text-decoration:none;">👉 {app_url} 👈</a>
                    </p>
                </div>

                <p style="color:#AEC6CF; font-size:15px; line-height:1.7; margin-top:20px;">{cierre}</p>
                <p style="color:#E74C3C; font-size:14px; font-style:italic;">{cierre2}</p>
            </div>

            <div style="background:#0D1117; padding:15px 25px; text-align:center; border-top:1px solid #2C3E50;">
                <p style="color:#7C8C8D; font-size:12px; margin:0;">
                    {nombre_display} — {footer_tag}<br>
                    <a href="{app_url}" style="color:#C8E600; text-decoration:none;">Ver la app</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def enviar_email(destinatario, nombre, asunto, html_body, nombre_display):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print(f"  [SKIP] Sin credenciales")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"{nombre_display} <{EMAIL_USER}>"
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
        print(f"  [ERROR] {e}")
        return False


# URLs de las apps por grupo
APP_URLS = {
    "oficina": "https://fpm2026oficina.streamlit.app",
    "losamigosesos": "https://fpm2026losamigosesos.streamlit.app",
}


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/send_bienvenida.py GRUPO [--test email] [--test-all email]")
        print("Ejemplo: python scripts/send_bienvenida.py losamigosesos --test-all prodemundialista2026@gmail.com")
        return

    group_id = sys.argv[1]
    test_email = None
    test_all = False

    if len(sys.argv) >= 4 and sys.argv[2] == "--test":
        test_email = sys.argv[3]
        print(f"\n🧪 MODO TEST — 1 mail a: {test_email}\n")
    elif len(sys.argv) >= 4 and sys.argv[2] == "--test-all":
        test_email = sys.argv[3]
        test_all = True
        print(f"\n🧪 MODO TEST-ALL — Todos los mails a: {test_email}\n")

    print("=" * 60)
    print(f"  BIENVENIDA — {group_id.upper()}")
    print("=" * 60)

    config = cargar_config(group_id)
    participantes = cargar_participantes(group_id)
    banner_url = cargar_banner_url(group_id)
    nombre_display = config.get("nombre_display", f"PRODE {group_id}")
    app_url = APP_URLS.get(group_id, f"https://{group_id}2026.streamlit.app")

    print(f"\nGrupo: {nombre_display}")
    print(f"Tono: {config.get('tono', 'normal')}")
    print(f"Participantes: {len(participantes)}")
    print(f"Banner URL: {banner_url}")
    print(f"App URL: {app_url}\n")

    asunto = f"🔥 ARRANCÓ {nombre_display} — ¡Entrá ya!"

    enviados = 0
    for p in participantes:
        email = test_email if test_email else p["email"]
        html = generar_html(p["nombre"], banner_url, config, group_id, app_url, participantes)

        if enviar_email(email, p["nombre"], asunto, html, nombre_display):
            enviados += 1

        if test_email and not test_all:
            break

    print(f"\n{'=' * 60}")
    print(f"  RESUMEN: {enviados} enviados")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

