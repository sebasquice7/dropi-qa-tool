"""Configuración centralizada del programa.

Todas las variables de entorno se leen UNA sola vez, aquí — el resto del
código las usa desde este único lugar (`from config import config`), en vez
de tener `os.environ.get(...)` desperdigado por 8 archivos distintos. Para
saber qué necesita el sistema para funcionar, alcanza con mirar este archivo.

Este módulo carga el .env por sí mismo (no depende de que algún otro archivo
lo haya hecho antes), para funcionar igual sin importar quién lo importe
primero — la app web, un script de línea de comandos, o una prueba.
"""
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def _es_placeholder_o_vacio(valor: str) -> bool:
    """Una API key vacía, o que todavía tenga el texto de ejemplo
    ('tu-key-aqui'), cuenta como 'no configurada de verdad'."""
    if not valor:
        return True
    return "tu-key-aqui" in valor.lower()


@dataclass(frozen=True)
class Config:
    # --- Acceso a la aplicación web ---
    app_username: str = os.environ.get("APP_USERNAME", "admin")
    app_password: str = os.environ.get("APP_PASSWORD", "")
    # Si no se define SECRET_KEY en el .env, se genera una aleatoria al arrancar
    # (mejor que tenerla fija en el código, pero cambia en cada reinicio — para
    # producción real, definirla fija en el .env es lo correcto).
    secret_key: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # --- Proveedores de IA ---
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_model: str = os.environ.get("OPENAI_MODEL", "")
    proveedor_forzado: str = os.environ.get("QA_PROVEEDOR", "")

    # --- Google Drive (respaldo de archivos) ---
    drive_sync_folder: str = os.environ.get("DRIVE_SYNC_FOLDER", "")
    drive_subfolder: str = os.environ.get("DRIVE_SUBFOLDER", "")

    # --- Alertas por correo de ítems críticos ---
    alerta_smtp_host: str = os.environ.get("ALERTA_SMTP_HOST", "")
    alerta_smtp_port: int = int(os.environ.get("ALERTA_SMTP_PORT") or 587)
    alerta_smtp_user: str = os.environ.get("ALERTA_SMTP_USER", "")
    alerta_smtp_pass: str = os.environ.get("ALERTA_SMTP_PASS", "")
    alerta_email_to: str = os.environ.get("ALERTA_EMAIL_TO", "")

    # --- Dashboard ---
    meta_calidad: float = float(os.environ.get("META_CALIDAD") or 0.85)

    # ---- Métodos de conveniencia: "¿está esto listo para usarse?" ----
    def gemini_configurado(self) -> bool:
        """True si hay una GEMINI_API_KEY real (no vacía, no placeholder)."""
        return not _es_placeholder_o_vacio(self.gemini_api_key)

    def anthropic_configurado(self) -> bool:
        """True si hay una ANTHROPIC_API_KEY real."""
        return not _es_placeholder_o_vacio(self.anthropic_api_key)

    def openai_configurado(self) -> bool:
        """True si hay una OPENAI_API_KEY real."""
        return not _es_placeholder_o_vacio(self.openai_api_key)

    def drive_configurado(self) -> bool:
        """True si DRIVE_SYNC_FOLDER está definido."""
        return bool(self.drive_sync_folder.strip())

    def alertas_configuradas(self) -> bool:
        """True si las 4 variables de alertas por correo están completas."""
        return all([
            self.alerta_smtp_host.strip(), self.alerta_smtp_user.strip(),
            self.alerta_smtp_pass.strip(), self.alerta_email_to.strip(),
        ])

    def hay_algun_proveedor_ia(self) -> bool:
        """True si al menos un proveedor de IA (Gemini, Claude u OpenAI) está listo para usarse."""
        return self.gemini_configurado() or self.anthropic_configurado() or self.openai_configurado()


# Instancia única, compartida por todo el programa — se carga al importar
# este módulo la primera vez, y todos los demás módulos reciben la misma.
config = Config()


def reporte_configuracion() -> str:
    """Resumen legible de qué está listo y qué falta — pensado para mostrarse
    al arrancar el programa, así el estado real se ve de un vistazo en vez de
    descubrirse a mitad de una evaluación."""
    ok, falta, opcional = "✅", "❌", "⬜"

    lineas = [
        "═══ Estado de configuración ═══",
        f"{ok if config.gemini_configurado() else falta} Gemini (gratis)"
        + ("" if config.gemini_configurado() else " — falta GEMINI_API_KEY, obténla gratis en https://aistudio.google.com/apikey"),
        f"{ok if config.anthropic_configurado() else opcional} Claude/Anthropic (de pago, opcional)",
        f"{ok if config.openai_configurado() else opcional} ChatGPT/OpenAI (de pago, opcional)",
        f"{ok if config.drive_configurado() else opcional} Respaldo en Google Drive (opcional)",
        f"{ok if config.alertas_configuradas() else opcional} Alertas por correo de ítems críticos (opcional)",
        f"{ok if config.app_password else '⚠️ '} Contraseña de acceso a la app"
        + ("" if config.app_password else " — SIN CONTRASEÑA, cualquiera en tu red la puede abrir"),
    ]

    if not config.hay_algun_proveedor_ia():
        lineas.append("")
        lineas.append("🛑 ADVERTENCIA: ningún proveedor de IA está configurado — las evaluaciones van a fallar.")

    return "\n".join(lineas)
