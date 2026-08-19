"""Envía una alerta por correo apenas se detecta un ítem crítico en una
evaluación — para que alguien pueda actuar rápido (ej. maltrato al cliente),
en vez de descubrirlo días después en un reporte.

Se activa solo si configuras estas variables en tu .env:
  ALERTA_SMTP_HOST=smtp.gmail.com
  ALERTA_SMTP_PORT=587
  ALERTA_SMTP_USER=tu_correo@gmail.com
  ALERTA_SMTP_PASS=tu_contraseña_de_aplicación
  ALERTA_EMAIL_TO=quien_debe_recibir_la_alerta@dropi.co

Si no están configuradas, esta función simplemente no hace nada (no rompe el
flujo principal) — igual que el patrón ya usado para las API keys de las IAs.
"""
import smtplib
from email.mime.text import MIMEText

from config import config
from logging_config import obtener_logger

log = obtener_logger("alertas")


def alerta_configurada() -> bool:
    """True si las 4 variables ALERTA_* necesarias están configuradas."""
    return config.alertas_configuradas()


def _armar_mensaje(metadata: dict, nota: dict) -> MIMEText:
    critico = nota.get("critico_activado", "desconocido")
    asunto = f"🚨 Ítem crítico detectado — {metadata.get('agente', '')} ({critico})"

    cuerpo = f"""Se detectó un ítem crítico al evaluar una conversación de soporte:

Asesor: {metadata.get('agente', '')}
Bandeja: {metadata.get('bandeja', '')}
País: {metadata.get('pais', '')}
ID del caso: {metadata.get('id_caso', '')}
Fecha: {metadata.get('fecha', '')}
Evaluado por: {metadata.get('evaluado_por', '(sin especificar)')}

Ítem crítico: {critico}
Nota final: 0% (forzada por el ítem crítico)

Revisa el caso completo en el programa de evaluación de calidad de Dropi.
"""
    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = config.alerta_smtp_user
    msg["To"] = config.alerta_email_to
    return msg


def enviar_alerta_critico(metadata: dict, nota: dict) -> dict:
    """Envía la alerta si hay algo que alertar y está configurado. Devuelve un
    dict con el resultado, pero NUNCA lanza una excepción que rompa el flujo
    principal de generar la evaluación — como mucho, falla en silencio."""
    if not nota.get("critico_activado"):
        return {"ok": False, "motivo": "No hay ítem crítico en esta evaluación (no aplica alerta)."}

    if not alerta_configurada():
        return {"ok": False, "motivo": "Alertas por correo no configuradas todavía (faltan variables ALERTA_* en el .env)."}

    try:
        msg = _armar_mensaje(metadata, nota)
        with smtplib.SMTP(config.alerta_smtp_host, config.alerta_smtp_port, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(config.alerta_smtp_user, config.alerta_smtp_pass)
            servidor.send_message(msg)

        log.info("Alerta de crítico enviada a %s (ítem: %s)", config.alerta_email_to, nota.get("critico_activado"))
        return {"ok": True, "motivo": f"Alerta enviada a {config.alerta_email_to}"}
    except Exception as e:
        log.error("No se pudo enviar la alerta de crítico: %s", e)
        return {"ok": False, "motivo": f"No se pudo enviar la alerta: {e}"}
