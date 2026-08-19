"""Prepara los datos de UN asesor (su historial completo de evaluaciones) para
que la IA sintetice un plan de coaching — a diferencia del resto del programa,
que evalúa una conversación a la vez, esto analiza PATRONES a través de varias
evaluaciones para detectar fortalezas y áreas de oportunidad reales.
"""
import json
from pathlib import Path
from statistics import mean

from historial import cargar_historial

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"

MINIMO_EVALUACIONES = 2  # menos que esto no alcanza para ver un patrón real


def _pesos_por_categoria() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)
    return {cat["nombre"]: cat["peso_categoria"] for cat in matriz["categorias"]}


def datos_para_coaching(asesor: str) -> dict:
    """Arma el paquete de datos de un asesor específico: estadísticas agregadas
    + evidencia textual real (sus últimas oportunidades de mejora y puntos
    positivos), listo para pasarle a la IA."""
    todos = cargar_historial()
    registros = [r for r in todos if r.get("agente") == asesor]
    registros.sort(key=lambda r: r.get("timestamp", ""))

    if len(registros) < MINIMO_EVALUACIONES:
        return {"suficientes_datos": False, "total": len(registros), "asesor": asesor}

    pesos = _pesos_por_categoria()
    notas = [r["nota_final"] for r in registros]

    por_categoria = {}
    for cat, peso_max in pesos.items():
        valores = [r.get("categorias", {}).get(cat) for r in registros if r.get("categorias", {}).get(cat) is not None]
        if valores and peso_max:
            por_categoria[cat] = round(mean(valores) / peso_max, 4)

    categorias_ordenadas = sorted(por_categoria.items(), key=lambda x: x[1])

    criticos = [r["critico_activado"] for r in registros if r.get("critico_activado")]

    # Evidencia textual real: hasta 10 oportunidades de mejora y 6 puntos
    # positivos más recientes, para que la IA cite casos concretos, no
    # generalidades. Solo evaluaciones posteriores a la actualización que
    # empezó a guardar este texto tendrán estos campos.
    oportunidades_recientes = []
    positivos_recientes = []
    for r in reversed(registros):
        for punto in r.get("oportunidades_mejora") or []:
            if len(oportunidades_recientes) < 10:
                oportunidades_recientes.append({"fecha": r.get("fecha"), "texto": punto})
        for punto in r.get("lo_positivo") or []:
            if len(positivos_recientes) < 6:
                positivos_recientes.append({"fecha": r.get("fecha"), "texto": punto})

    return {
        "suficientes_datos": True,
        "asesor": asesor,
        "total": len(registros),
        "primera_fecha": registros[0].get("fecha"),
        "ultima_fecha": registros[-1].get("fecha"),
        "nota_promedio": round(mean(notas), 4),
        "nota_primera_mitad": round(mean(notas[:len(notas)//2 or 1]), 4),
        "nota_segunda_mitad": round(mean(notas[len(notas)//2:]), 4),
        "categorias_ordenadas": categorias_ordenadas,  # peor a mejor
        "total_criticos": len(criticos),
        "criticos_detalle": criticos,
        "oportunidades_recientes": oportunidades_recientes,
        "positivos_recientes": positivos_recientes,
        "hay_evidencia_textual": bool(oportunidades_recientes or positivos_recientes),
    }
