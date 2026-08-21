"""Caché del plan de coaching: se guarda apenas se genera, para poder
descargarlo como Word sin volver a llamar la IA (y para que el Word coincida
exactamente con lo que se vio en pantalla).

Además, mantiene un HISTORIAL PERMANENTE de los planes generados (distinto
de la caché, que solo guarda el último) — para que el próximo plan pueda
comparar contra los compromisos de la sesión anterior, y así cerrar el ciclo
real de coaching (no solo generar un reporte aislado cada vez)."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"
HISTORIAL_PLANES_PATH = BASE_DIR / "historial_planes_coaching.json"


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


def _cargar_historial_planes() -> list:
    if not HISTORIAL_PLANES_PATH.exists():
        return []
    try:
        with open(HISTORIAL_PLANES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def obtener_plan_anterior(asesor: str) -> Optional[dict]:
    """Devuelve el plan de coaching guardado más reciente de este asesor
    (antes del que se está generando ahora), o None si es el primero."""
    planes = [p for p in _cargar_historial_planes() if p["asesor"] == asesor]
    if not planes:
        return None
    planes.sort(key=lambda p: p["guardado_en"])
    return planes[-1]


def guardar_plan_en_historial(asesor: str, datos: dict, plan: dict) -> None:
    """Agrega este plan al historial PERMANENTE — pero solo si hay datos
    genuinamente nuevos desde el último plan guardado (para no llenar el
    historial de duplicados cada vez que alguien solo entra a mirar la
    página sin que haya evaluaciones nuevas de por medio)."""
    anterior = obtener_plan_anterior(asesor)
    if anterior and anterior.get("ultima_fecha") == datos.get("ultima_fecha") and anterior.get("total") == datos.get("total"):
        return  # mismos datos que la última vez guardada — no duplicar

    planes = _cargar_historial_planes()
    planes.append({
        "asesor": asesor,
        "guardado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "primera_fecha": datos.get("primera_fecha"),
        "ultima_fecha": datos.get("ultima_fecha"),
        "total": datos.get("total"),
        "nota_promedio": datos.get("nota_promedio"),
        "categorias_ordenadas": datos.get("categorias_ordenadas"),
        "plan_accion": plan.get("plan_accion", []),
        "areas_prioritarias": plan.get("areas_prioritarias", []),
    })
    with open(HISTORIAL_PLANES_PATH, "w", encoding="utf-8") as f:
        json.dump(planes, f, ensure_ascii=False, indent=2)
