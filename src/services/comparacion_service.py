"""Servicio de comparación entre varias IAs — evalúa la misma conversación
con los proveedores configurados (Gemini, Claude, ChatGPT) y deja elegir cuál
usar como la oficial. También incluye el modo demostración: una evaluación
real + variantes simuladas, para mostrar el alcance sin pagar por las otras
IAs todavía.

Igual que los otros servicios, no depende de Flask.
"""
import json
import random
from pathlib import Path

from pdf_parser import cargar_conversacion_desde_pdf
from evaluator import evaluar_conversacion, evaluar_conversacion_multi
from scoring import calcular_nota, normalizar_evaluacion
from services.evaluacion_service import construir_metadata, guardar_borrador

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"


def _ruta_comparacion(token: str) -> Path:
    return SALIDAS_DIR / f"comparar_{token}.json"


def guardar_comparacion(token: str, metadata: dict, resultados: dict) -> None:
    """Guarda en disco los resultados de comparar entre varias IAs, para poder 'elegir' cuál usar después."""
    with open(_ruta_comparacion(token), "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "resultados": resultados}, f, ensure_ascii=False, indent=2)


def cargar_comparacion(token: str) -> dict:
    """Lanza FileNotFoundError si esa comparación no existe (o ya expiró)."""
    with open(_ruta_comparacion(token), encoding="utf-8") as f:
        return json.load(f)


def comparar_con_varias_ias(conversacion_texto: str, asesor: str, proveedores: list,
                             bandeja: str, pais: str, id_caso: str, auditor: str, token: str) -> dict:
    """Evalúa la misma conversación con cada proveedor de la lista, normaliza
    y calcula la nota de cada uno, y guarda todo para poder 'elegir' después.

    Devuelve: {"metadata": ..., "resultados": {proveedor: {evaluacion, nota} | {error}}}
    """
    resultados_crudos = evaluar_conversacion_multi(
        conversacion_texto, asesor, proveedores=proveedores, pais=pais, bandeja=bandeja,
    )

    resultados = {}
    for proveedor, r in resultados_crudos.items():
        if "error" in r:
            resultados[proveedor] = {"error": r["error"]}
            continue
        evaluacion = normalizar_evaluacion(r)
        nota = calcular_nota(evaluacion)
        resultados[proveedor] = {"evaluacion": evaluacion, "nota": nota}

    metadata = construir_metadata(asesor, bandeja, id_caso, pais, auditor)
    guardar_comparacion(token, metadata, resultados)

    return {"metadata": metadata, "resultados": resultados}


def _variante_simulada(evaluacion_real: dict, sesgo: float, semilla: int) -> dict:
    """Genera una variación SIMULADA de una evaluación real, para el modo
    demostración. No es una llamada real a ninguna IA — solo perturba los
    puntajes de la evaluación real dentro de rangos plausibles, para que la
    pantalla de comparación se vea completa mientras no hay las API keys de
    pago activas. `semilla` fija la aleatoriedad para que sea reproducible."""
    rng = random.Random(semilla)
    ev = json.loads(json.dumps(evaluacion_real))  # copia profunda simple

    for item in ev.get("items", {}).values():
        factor = 1 + sesgo + rng.uniform(-0.06, 0.06)
        item["puntaje"] = max(0, item["puntaje"] * factor)

    return normalizar_evaluacion(ev)


def generar_comparacion_demo(conversacion_texto: str, asesor: str,
                              bandeja: str, pais: str, id_caso: str, auditor: str, token: str) -> dict:
    """Hace UNA evaluación real con Gemini y arma 2 variantes SIMULADAS
    (etiquetadas como tal) para representar a Claude y ChatGPT — pensado para
    demostrar el alcance del programa antes de pagar por esas IAs."""
    evaluacion_real = evaluar_conversacion(conversacion_texto, asesor, proveedor="gemini", pais=pais, bandeja=bandeja)
    evaluacion_real = normalizar_evaluacion(evaluacion_real)
    nota_real = calcular_nota(evaluacion_real)

    ev_anthropic = _variante_simulada(evaluacion_real, sesgo=-0.03, semilla=1)
    ev_openai = _variante_simulada(evaluacion_real, sesgo=-0.06, semilla=2)

    resultados = {
        "gemini": {"evaluacion": evaluacion_real, "nota": nota_real},
        "anthropic": {"evaluacion": ev_anthropic, "nota": calcular_nota(ev_anthropic), "simulado": True},
        "openai": {"evaluacion": ev_openai, "nota": calcular_nota(ev_openai), "simulado": True},
    }

    metadata = construir_metadata(asesor, bandeja, id_caso, pais, auditor)
    guardar_comparacion(token, metadata, resultados)

    return {"metadata": metadata, "resultados": resultados}


def elegir_resultado_de_comparacion(token: str, proveedor: str, nombre_proveedor: str) -> dict:
    """El usuario decidió cuál de las evaluaciones comparadas usar como la
    oficial. Valida que exista, que no tenga error, y que no sea una
    simulación (eso nunca se puede usar como evaluación real) — y si todo
    está bien, guarda el borrador estándar para seguir el flujo normal.

    Lanza ValueError con un mensaje claro si algo no es válido para elegir;
    el caller decide cómo mostrarlo (la capa web lo convierte en flash)."""
    datos = cargar_comparacion(token)  # puede lanzar FileNotFoundError

    resultado = datos["resultados"].get(proveedor)
    if not resultado or "error" in resultado:
        raise ValueError(f"No hay una evaluación válida de {proveedor} para elegir.")
    if resultado.get("simulado"):
        raise ValueError(
            "Esta evaluación era una simulación de demostración (no una llamada real a la IA) — "
            "no se puede usar como evaluación oficial. Activa la API key real para poder usarla."
        )

    metadata = dict(datos["metadata"])
    metadata["evaluado_con_ia"] = nombre_proveedor

    guardar_borrador(token, metadata, resultado["evaluacion"], resultado["nota"])
    return {"token": token, "metadata": metadata, "evaluacion": resultado["evaluacion"], "nota": resultado["nota"]}
