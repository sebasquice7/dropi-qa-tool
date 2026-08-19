"""Calcula el presupuesto estimado de la IA para cualquier volumen de
conversaciones — usa datos REALES de tu uso (medidos automáticamente en cada
evaluación) apenas tengas suficientes; mientras tanto, usa una estimación
medida manualmente una vez con el programa real (no un número inventado).
"""
from uso_ia import resumen_uso

MINIMO_MUESTRAS_PARA_DATOS_REALES = 10

# Estimación de respaldo: medida directamente con evaluator.py el 12-ago-2026,
# con una conversación de tamaño típico (~18 mensajes). Se usa solo mientras
# no haya suficientes evaluaciones reales registradas en uso_ia_log.jsonl.
FALLBACK_TOKENS_ENTRADA_CON_GUIA = 7807
FALLBACK_TOKENS_ENTRADA_SIN_GUIA = 6502
FALLBACK_TOKENS_SALIDA = 1650
FALLBACK_PCT_CON_GUIA = 0.30

# Precios verificados por búsqueda web en agosto de 2026 (USD por millón de tokens).
# Actualízalos aquí si cambian — son los únicos números "mágicos" del módulo.
PRECIOS_MODELOS = [
    {"id": "gemini_lite_25", "nombre": "Gemini 2.5 Flash-Lite", "nota": "El que usa tu programa hoy (1ra opción)", "input": 0.10, "output": 0.40, "color": "verde"},
    {"id": "gemini_lite_31", "nombre": "Gemini 3.1 Flash-Lite", "nota": "Sucesor — 2.5 se retira 16-oct-2026", "input": 0.25, "output": 1.50, "color": "verde"},
    {"id": "gemini_flash_36", "nombre": "Gemini 3.6 Flash", "nota": "Respaldo automático si falla el anterior", "input": 1.50, "output": 7.50, "color": "ambar"},
    {"id": "claude_sonnet_46", "nombre": "Claude Sonnet 4.6", "nota": "Proveedor #2, listo para activar", "input": 3.00, "output": 15.00, "color": "ambar"},
    {"id": "gpt_55", "nombre": "ChatGPT / GPT-5.5", "nota": "Proveedor #3, listo para activar", "input": 5.00, "output": 30.00, "color": "rojo"},
]


def obtener_base_tokens() -> dict:
    """Devuelve los tokens de entrada/salida a usar en el cálculo, priorizando
    datos reales de tu uso sobre la estimación de respaldo."""
    resumen = resumen_uso()

    if resumen["hay_datos"] and resumen["total"] >= MINIMO_MUESTRAS_PARA_DATOS_REALES:
        return {
            "fuente": "real",
            "total_muestras": resumen["total"],
            "tokens_entrada": resumen["tokens_entrada_promedio"],
            "tokens_salida": resumen["tokens_salida_promedio"],
            "pct_con_guia": resumen["pct_con_guia"],
        }

    tokens_entrada_estimado = round(
        FALLBACK_TOKENS_ENTRADA_CON_GUIA * FALLBACK_PCT_CON_GUIA
        + FALLBACK_TOKENS_ENTRADA_SIN_GUIA * (1 - FALLBACK_PCT_CON_GUIA)
    )
    return {
        "fuente": "estimado",
        "total_muestras": resumen.get("total", 0),
        "tokens_entrada": tokens_entrada_estimado,
        "tokens_salida": FALLBACK_TOKENS_SALIDA,
        "pct_con_guia": FALLBACK_PCT_CON_GUIA,
    }


def calcular_presupuesto(conversaciones_dia: int, dias_mes: int = 30) -> dict:
    """Calcula el costo estimado (por evaluación, diario y mensual) para cada modelo de IA soportado, dado un volumen de conversaciones."""
    base = obtener_base_tokens()

    modelos = []
    for m in PRECIOS_MODELOS:
        costo_evaluacion = (base["tokens_entrada"] / 1_000_000) * m["input"] + (base["tokens_salida"] / 1_000_000) * m["output"]
        modelos.append({
            **m,
            "costo_evaluacion": round(costo_evaluacion, 6),
            "costo_diario": round(costo_evaluacion * conversaciones_dia, 2),
            "costo_mensual": round(costo_evaluacion * conversaciones_dia * dias_mes, 2),
        })

    return {
        "base": base,
        "conversaciones_dia": conversaciones_dia,
        "dias_mes": dias_mes,
        "modelos": modelos,
    }
