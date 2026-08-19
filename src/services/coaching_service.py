"""Caché del plan de coaching: se guarda apenas se genera, para poder
descargarlo como Word sin volver a llamar la IA (y para que el Word coincida
exactamente con lo que se vio en pantalla)."""
import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"


def slug(texto: str) -> str:
    """Convierte un nombre a un identificador seguro para usar en nombres de archivo (sin espacios ni tildes)."""
    return "".join(c if c.isalnum() else "_" for c in texto.strip().lower())


def _ruta_cache(asesor: str) -> Path:
    return SALIDAS_DIR / f"coaching_cache_{slug(asesor)}.json"


def guardar_en_cache(asesor: str, datos: dict, plan: dict) -> None:
    """Guarda el plan ya generado, para no tener que volver a llamar la IA al descargarlo como Word."""
    with open(_ruta_cache(asesor), "w", encoding="utf-8") as f:
        json.dump({"datos": datos, "plan": plan}, f, ensure_ascii=False, indent=2)


def cargar_de_cache(asesor: str) -> Optional[tuple]:
    """Devuelve (datos, plan) o None si no hay caché para ese asesor."""
    ruta = _ruta_cache(asesor)
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        cache = json.load(f)
    return cache["datos"], cache["plan"]


def nombre_archivo_word(asesor: str) -> str:
    """Nombre de archivo estándar para el Word del plan de coaching de un asesor."""
    return f"Coaching_{slug(asesor)}.docx"
