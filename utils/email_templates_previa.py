def generar_html_email_previa(
    nombre,
    codigo,
    orden_entrega,
    total_entregados,
    estimado_min,
    estimado_max,
    fecha_entrega,
    hora_entrega,
    campeon,
    goleador,
    figura,
    revelacion,
    decepcion,
    goles_totales,
    comentario_ia,
    stats_globales,
    tabla_entregas,
):
    """
    Genera HTML para el reporte semanal de LA PREVIA.
    No hay puntos ni posiciones competitivas; solo orden de entrega y datos de color.
    """

    # Medalla / estado de entrega
    if orden_entrega == 1:
        medalla = "🥇"
        titulo_entrega = "Primer valiente en entregar"
        color = "#C8E600"
    elif orden_entrega == 2:
        medalla = "🥈"
        titulo_entrega = "Segundo en llegar a la meta"
        color = "#AEC6CF"
    elif orden_entrega == 3:
        medalla = "🥉"
        titulo_entrega = "Podio de puntualidad"
        color = "#E67E22"
    elif orden_entrega == total_entregados:
        medalla = "🐢"
        titulo_entrega = "Último por ahora"
        color = "#E74C3C"
    else:
        medalla = "📋"
        titulo_entrega = "Entregado y archivado"
        color = "#7C8C8D"

    # Tabla de entregas
    entregas_html = ""
    for row in tabla_entregas:
        highlight = row["codigo"] == codigo
        bg = "background:#2C3E50; border-left:3px solid #C8E600;" if highlight else ""
        peso = "font-weight:bold; color:#C8E600;" if highlight else "color:#FFFFFF;"
        entregas_html += f"""
        <tr style="{bg}">
            <td style="padding:5px 10px; color:#7C8C8D;">{row['orden']}</td>
            <td style="padding:5px 10px; {peso}">{row['codigo']}</td>
            <td style="padding:5px 10px; color:#AEC6CF;">{row['fecha']}</td>
            <td style="padding:5px 10px; color:#AEC6CF;">{row['hora']}</td>
        </tr>
        """

    # Stats globales
    campeon_mas_elegido = stats_globales.get("campeon_mas_elegido", "-")
    campeon_mas_elegido_n = stats_globales.get("campeon_mas_elegido_n", 0)
    goleador_max = stats_globales.get("goleador_max", "-")
    goles_max = stats_globales.get("goles_max", 0)
    goleador_min = stats_globales.get("goleador_min", "-")
    goles_min = stats_globales.get("goles_min", 0)
    faltan_txt = f"entre {max(estimado_min - total_entregados, 0)} y {max(estimado_max - total_entregados, 0)}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin:0; padding:0; background-color:#0D1117; font-family:Segoe UI, Arial, sans-serif;">
        <div style="max-width:620px; margin:0 auto; background-color:#1B2838; border:1px solid #2C3E50;">
            
            <!-- Header -->
            <div style="background:linear-gradient(135deg, #1B2838, #2C3E50); padding:25px; text-align:center;
                        border-bottom:2px solid #C8E600;">
                <h1 style="color:#C8E600; margin:0; font-size:24px;">🎭 LA PREVIA DEL PRODE 🎭</h1>
                <p style="color:#AEC6CF; margin:5px 0 0 0; font-size:14px;">
                    Fabuloso Prode Mundialista 2026 — Reporte de oficina
                </p>
            </div>

            <!-- Estado general -->
            <div style="padding:20px 25px;">
                <div style="background:#2C3E50; border-radius:10px; padding:15px; text-align:center;">
                    <p style="color:#C8E600; font-size:18px; margin:0; font-weight:bold;">
                        📋 Ya entregaron {total_entregados} participantes
                    </p>
                    <p style="color:#AEC6CF; font-size:13px; margin:6px 0 0 0;">
                        Esperamos entre {estimado_min} y {estimado_max}. Todavía faltan {faltan_txt} valientes.
                    </p>
                </div>
            </div>

            <!-- Tu entrega -->
            <div style="padding:0 25px 20px 25px;">
                <p style="color:#FFFFFF; font-size:16px; margin:0 0 10px 0;">
                    Hola <b>{nombre}</b>,
                </p>
                <div style="background:#2C3E50; border-radius:10px; padding:15px; text-align:center;">
                    <span style="font-size:36px;">{medalla}</span>
                    <p style="color:{color}; font-size:20px; margin:5px 0; font-weight:bold;">
                        #{orden_entrega} — {titulo_entrega}
                    </p>
                    <p style="color:#AEC6CF; font-size:13px; margin:0;">
                        Entregado el {fecha_entrega} a las {hora_entrega}
                    </p>
                </div>
            </div>

            <!-- Comentario IA -->
            <div style="padding:0 25px 20px 25px;">
                <div style="background:#2C3E50; border-left:3px solid #C8E600; padding:15px; border-radius:0 8px 8px 0;">
                    <p style="color:#AEC6CF; font-size:12px; margin:0 0 5px 0;">💬 EL COMITÉ DEL HUMO DICE:</p>
                    <p style="color:#FFFFFF; font-size:14px; margin:0; line-height:1.5; font-style:italic;">
                        {comentario_ia}
                    </p>
                </div>
            </div>

            <!-- Tus apuestas -->
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">🎯 Tus delirios declarados</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <tr><td style="color:#AEC6CF; padding:4px 0;">🏆 Campeón</td><td style="color:#FFFFFF; text-align:right;">{campeon}</td></tr>
                    <tr><td style="color:#AEC6CF; padding:4px 0;">⚽ Goleador</td><td style="color:#FFFFFF; text-align:right;">{goleador}</td></tr>
                    <tr><td style="color:#AEC6CF; padding:4px 0;">⭐ Figura</td><td style="color:#FFFFFF; text-align:right;">{figura}</td></tr>
                    <tr><td style="color:#AEC6CF; padding:4px 0;">💡 Revelación</td><td style="color:#FFFFFF; text-align:right;">{revelacion}</td></tr>
                    <tr><td style="color:#AEC6CF; padding:4px 0;">💀 Decepción</td><td style="color:#FFFFFF; text-align:right;">{decepcion}</td></tr>
                    <tr><td style="color:#AEC6CF; padding:4px 0;">🔥 Goles predichos</td><td style="color:#C8E600; text-align:right; font-weight:bold;">{goles_totales}</td></tr>
                </table>
            </div>

            <!-- Datos de color -->
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">📊 Datos inútiles pero necesarios</h3>
                <ul style="margin:0; padding-left:20px;">
                    <li style="color:#AEC6CF; margin:4px 0;">Campeón más elegido: <b style="color:#FFFFFF;">{campeon_mas_elegido}</b> ({campeon_mas_elegido_n})</li>
                    <li style="color:#AEC6CF; margin:4px 0;">Más goleador: <b style="color:#FFFFFF;">{goleador_max}</b> ({goles_max} goles)</li>
                    <li style="color:#AEC6CF; margin:4px 0;">Más defensivo: <b style="color:#FFFFFF;">{goleador_min}</b> ({goles_min} goles)</li>
                </ul>
            </div>

            <!-- Tabla entregas -->
            <div style="padding:0 25px 20px 25px;">
                <h3 style="color:#C8E600; margin:0 0 10px 0; font-size:16px;">🏅 Orden de entrega</h3>
                <table style="width:100%; border-collapse:collapse;">
                    {entregas_html}
                </table>
            </div>

            <!-- Footer -->
            <div style="background:#0D1117; padding:15px 25px; text-align:center; border-top:1px solid #2C3E50;">
                <p style="color:#7C8C8D; font-size:12px; margin:0;">
                    Fabuloso Prode Mundialista 2026 — Oficina<br>
                    <span style="color:#C8E600;">Si llegaste hasta acá leyendo, ya sos más dedicado que la mitad de los participantes.</span>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
