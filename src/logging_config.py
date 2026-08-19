"""Configuración central de logging del programa.

Reemplaza los `print()` sueltos por un logging real: con niveles (info,
warning, error), con fecha/hora, y guardado en un archivo (logs/app.log) que
rota automáticamente para no crecer sin límite — así, cuando algo falla en
producción, hay un historial real para diagnosticarlo, no solo lo que haya
quedado en la terminal en ese momento.

Uso en cualquier módulo del programa:
    from logging_config import obtener_logger
    log = obtener_logger(__name__)
    log.info("Evaluación completada para %s", asesor)
    log.warning("No se pudo guardar en Drive: %s", motivo)
    log.error("Falló la llamada a la IA", exc_info=True)
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

_configurado = False


def _configurar_una_vez() -> None:
    """Prepara los handlers del logger raíz la primera vez que se pide un
    logger — las llamadas siguientes son gratis (no duplica handlers)."""
    global _configurado
    if _configurado:
        return

    LOGS_DIR.mkdir(exist_ok=True)
    raiz = logging.getLogger("dropi_qa")
    raiz.setLevel(logging.INFO)

    formato = logging.Formatter(_FORMATO, datefmt=_FORMATO_FECHA)

    consola = logging.StreamHandler(sys.stdout)
    consola.setFormatter(formato)
    raiz.addHandler(consola)

    # 5 archivos de 2MB cada uno (10MB en total) — suficiente historial para
    # diagnosticar una falla, sin crecer sin control con el tiempo.
    archivo = RotatingFileHandler(
        LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    archivo.setFormatter(formato)
    raiz.addHandler(archivo)

    _configurado = True


def obtener_logger(nombre: str) -> logging.Logger:
    """Logger con el nombre del módulo que lo pide (ej. 'evaluator', 'app'),
    para que cada línea del log diga de dónde vino."""
    _configurar_una_vez()
    return logging.getLogger(f"dropi_qa.{nombre}")
