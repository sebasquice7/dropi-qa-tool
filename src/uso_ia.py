"""Registra el uso real de tokens de cada llamada a la IA (aproximado por
caracteres del prompt/respuesta reales, ~4 caracteres por token), para que el
simulador de presupuesto se base en datos REALES de tu uso — no en una
estimación de una sola vez — y se vuelva más preciso mientras más evalúes.
"""
import json
from datetime import datetime
from pathlib import Path
from statistics import mean

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "uso_ia_log.jsonl"

CARACTERES_POR_TOKEN = 4  # aproximación estándar de la industria


def registrar_uso(proveedor: str, longitud_prompt: int, longitud_respuesta: int, tuvo_guia: bool) -> None:
    """Se llama automáticamente cada vez que una evaluación de verdad se
    completa. Nunca debe romper el flujo principal si algo falla al escribir."""
    try:
        registro = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "proveedor": proveedor,
            "tokens_entrada": round(longitud_prompt / CARACTERES_POR_TOKEN),
            "tokens_salida": round(longitud_respuesta / CARACTERES_POR_TOKEN),
            "tuvo_guia": bool(tuvo_guia),
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception:
        pass  # el registro de uso nunca debe tumbar una evaluación real


def cargar_uso() -> list:
    """Lee todos los registros de uso guardados en el log (uno por línea, formato JSONL)."""
    if not LOG_PATH.exists():
        return []
    registros = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                registros.append(json.loads(linea))
            except json.JSONDecodeError:
                continue
    return registros


def resumen_uso() -> dict:
    """Promedia el uso real registrado (tokens de entrada/salida, % de casos con guía) para alimentar el simulador de presupuesto."""
    registros = cargar_uso()
    if not registros:
        return {"hay_datos": False, "total": 0}

    tokens_entrada = [r["tokens_entrada"] for r in registros]
    tokens_salida = [r["tokens_salida"] for r in registros]
    con_guia = sum(1 for r in registros if r.get("tuvo_guia"))

    return {
        "hay_datos": True,
        "total": len(registros),
        "tokens_entrada_promedio": round(mean(tokens_entrada)),
        "tokens_salida_promedio": round(mean(tokens_salida)),
        "pct_con_guia": round(con_guia / len(registros), 4),
    }
