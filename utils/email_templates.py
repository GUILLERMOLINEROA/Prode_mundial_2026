def generar_html_email(nombre, codigo, posicion, total_participantes, puntos,
                       top3, comentario_ia, resultados_semana, leaderboard_mini):
    """
    Genera el HTML del email semanal del PRODE.
    
    Args:
        nombre: nombre real del participante
        codigo: código (GELA, FASA, etc.)
        posicion: posición actual en el leaderboard
        total_participantes: total de participantes
        puntos: puntos actuales
        top3: lista de dicts [{nombre, puntos}, ...] con el top 3
        comentario_ia: comentario generado por Gemini
        resultados_semana: lista de strings con resultados recientes
        leaderboard_mini: lista de dicts [{posicion, nombre, puntos}, ...]
    """
    
    # Emoji según posición
    if posicion == 1:
        pos_emoji = "👑"
        pos_color = "#C8E600"
    elif posicion == 2:
        pos_emoji = "🥈"
        pos_color = "#AEC6CF"
    elif posicion == 3:
        pos_emoji = "🥉"
        pos_color = "#E67E22"
    elif posicion <= total_participantes * 0.5:
        pos_emoji = "😐"
        pos_color = "#7C8C8D"
    elif posicion < total_participantes:
        pos_emoji = "📉"
        pos_color = "#E74C3C"
    else:
        pos_emoji = "💀"
        pos_color = "#E74C3C"

    # Top 3 HTML
    top3_html = ""
    medallas = ["🥇", "🥈", "🥉"]
    for i, t in enumerate(top3[:3]):
        top3_html += f"""
        <tr>
            <td style="padding:5px 10px; color:#C8E600;">{medallas[i]}</td>
            <td style="padding:5px 10px; color:#FFFFFF;">{t['nombre']}</td>
            <td style="padding:5px 10px; color:#C8E600; text-align:right; font-weight:bold;">{t['puntos']} pts</td>
        </tr>"""

    # Resultados de la semana
    resultados_html = ""
    for r in resultados_semana[:5]:
        resultados_html += f'<li style="color:#AEC6CF; margin:3px 0;">{r}</li>'

    # Leaderboard mini (posición del usuario resaltada)
    leaderboard_html = ""
    for row in leaderboard_mini:
        if row['nombre'] == codigo:
            bg = "background:#2C3E50; border-left:3px solid #C8E600;"
            peso = "font-weight:bold; color:#C8E600;"
        else:
            bg = ""
            peso = "color:#FFFFFF;"
        leaderboard_html += f"""
        <tr style="{bg}">
            <td style="padding:4px 10px; color:#7C8C8D;">{row['posicion']}</td>
            <td style="padding:4px 10px; {peso}">{row['nombre']}</td>
            <td style="padding:4px 10px; color:#AEC6CF; text-align:right;">{row['puntos']} pts</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin:0; padding:0; background-color:#0D1117; font-family:Segoe UI, Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; background-color:#1B2838; border:1px solid #2C3E50;">
            
            <!-- Header -->
            <div style="background:linear-gradient(135deg, #1B2838, #2C3E50); padding:25px; text-align:center;
                        border-bottom:2px solid #C8E600;">
                <h1 style="color:#C8E600; margin:0; font-size:24px;">⚽ FABULOSO PRODE MUNDIALISTA 2026 ⚽</h1>
                <p style="color:#AEC6CF; margin:5px 0 0 0; font-size:14px;">Reporte Semanal</p>
            </div>

            <!-- Saludo + Posición -->
            <div style="padding:20px 25px;">
                <p style="color:#FFFFFF; font-size:16px; margin:0 0 10px 0;">
                    Hola <b>{nombre}</b>,
                </p>
                <div style="background:#2C3E50; border-radius:10px; padding:15px; text-align:center; margin:10px 0;">
                    <span style="font-size:36px;">{pos_emoji}</span>
                    <p style="color:{pos_color}; font-size:20px; margin:5px 0; font-weight:bold;">
                        Posición #{posicion} de {total_participantes}
                    </p>
                    <p style="color:#C8E600; font-size:28px; margin:0; font-weight:bold;">{puntos} puntos</p>
                </div>
            </div>

            <!-- Comentario IA -->
            <div style="padding:0 25px 20px 25px;">
                <div style="background:#2C3E50; border-left:3px solid #C8E600; padding:15px; border-radius:0 8px 8px 0;">
                    <p style="color:#AEC6CF; font-size:12px; margin:0 0 5px 0;">💬 EL ANALISTA DICE:</p>
                    <p style="color:#FFFFFF; font-size:14px; margin:0; line-height:1.5; font-style:italic;">
                        {comentario_ia}
                    </p>
                </div>
            </div>

            <!-- Top 3 -->
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">🏆 Top 3</h3>
                <table style="width:100%; border-collapse:collapse;">
                    {top3_html}
                </table>
            </div>

            <!-- Resultados de la semana -->
            {f'''
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">⚡ Resultados Recientes</h3>
                <ul style="margin:0; padding-left:20px;">
                    {resultados_html}
                </ul>
            </div>
            ''' if resultados_semana else ''}

            <!-- Leaderboard -->
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">📋 Tabla de Posiciones</h3>
                <table style="width:100%; border-collapse:collapse;">
                    {leaderboard_html}
                </table>
            </div>

            <!-- Footer -->
            <div style="background:#0D1117; padding:15px 25px; text-align:center; border-top:1px solid #2C3E50;">
                <p style="color:#7C8C8D; font-size:12px; margin:0;">
                    Fabuloso Prode Mundialista 2026 — Oficina<br>
                    <a href="https://fpm2026oficina.streamlit.app" style="color:#C8E600; text-decoration:none;">
                        Ver app completa</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
