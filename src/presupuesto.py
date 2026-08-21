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
    {"id": "gpt_41", "nombre": "ChatGPT / GPT-4.1", "nota": "El mismo modelo que usa Gali — proveedor #3", "input": 2.00, "output": 8.00, "color": "ambar"},
    {"id": "gpt_55", "nombre": "ChatGPT / GPT-5.5", "nota": "Alternativa más nueva de OpenAI", "input": 5.00, "output": 30.00, "color": "rojo"},
]

# Qué modelo/precio representa a cada proveedor cuando se calcula el gasto
# real (el log de uso guarda el proveedor usado en cada llamada, pero no
# siempre el modelo exacto — se usa el modelo por defecto de ese proveedor).
PRECIO_POR_DEFECTO_DEL_PROVEEDOR = {
    "gemini": "gemini_lite_25",
    "anthropic": "claude_sonnet_46",
    "openai": "gpt_41",
}


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
    """Calcula el costo estimado (por evaluación, diario y mensual) para cada modelo de IA soportado, dado un volumen de conversaciones por día."""
    base = obtener_base_tokens()
    modelos = _costos_por_modelo(base, conversaciones_dia * dias_mes)

    return {
        "base": base,
        "modo": "volumen_diario",
        "conversaciones_dia": conversaciones_dia,
        "dias_mes": dias_mes,
        "modelos": modelos,
    }


def calcular_presupuesto_por_asesores(numero_asesores: int, evaluaciones_por_asesor: int = 40, dias_mes: int = 30) -> dict:
    """Calcula el presupuesto según la instrucción real del equipo: un número
    fijo de evaluaciones por asesor al mes (muestreo de calidad), no evaluar
    el 100% de las conversaciones. evaluaciones_mes = asesores × evaluaciones_por_asesor.
    """
    base = obtener_base_tokens()
    evaluaciones_mes = numero_asesores * evaluaciones_por_asesor
    modelos = _costos_por_modelo(base, evaluaciones_mes)

    return {
        "base": base,
        "modo": "por_asesor",
        "numero_asesores": numero_asesores,
        "evaluaciones_por_asesor": evaluaciones_por_asesor,
        "evaluaciones_mes": evaluaciones_mes,
        "dias_mes": dias_mes,
        "modelos": modelos,
    }


def _costos_por_modelo(base: dict, evaluaciones_mes: int) -> list:
    """Costo por evaluación, diario (aproximado sobre 30 días) y mensual,
    para cada modelo soportado — dado un total de evaluaciones al mes."""
    modelos = []
    for m in PRECIOS_MODELOS:
        costo_evaluacion = (base["tokens_entrada"] / 1_000_000) * m["input"] + (base["tokens_salida"] / 1_000_000) * m["output"]
        costo_mensual = costo_evaluacion * evaluaciones_mes
        modelos.append({
            **m,
            "costo_evaluacion": round(costo_evaluacion, 6),
            "costo_diario": round(costo_mensual / 30, 2),
            "costo_mensual": round(costo_mensual, 2),
        })
    return modelos


def gasto_real_del_mes(mes: str = None) -> dict:
    """Cuánto se ha gastado REALMENTE en IA este mes (o el mes que se pida,
    formato 'YYYY-MM') — a partir del log de uso real, no de una simulación.

    Funciona igual sin importar qué tan pocas o muchas evaluaciones haya, y
    sigue funcionando sin cambios el día que se conecte Intercom y el volumen
    suba — no depende de nada más que del log de uso, que ya se llena solo en
    cada evaluación real."""
    from datetime import datetime
    from collections import defaultdict
    from uso_ia import cargar_uso

    if not mes:
        mes = datetime.now().strftime("%Y-%m")

    registros = [r for r in cargar_uso() if r.get("timestamp", "").startswith(mes)]

    precios_por_id = {m["id"]: m for m in PRECIOS_MODELOS}
    gasto_por_dia = defaultdict(float)
    gasto_por_proveedor = defaultdict(float)
    total = 0.0

    for r in registros:
        proveedor = r.get("proveedor", "gemini")
        id_precio = PRECIO_POR_DEFECTO_DEL_PROVEEDOR.get(proveedor, "gemini_lite_25")
        precio = precios_por_id[id_precio]
        costo = (r.get("tokens_entrada", 0) / 1_000_000) * precio["input"] + (r.get("tokens_salida", 0) / 1_000_000) * precio["output"]
        total += costo
        dia = r.get("timestamp", "")[:10]  # "YYYY-MM-DD"
        gasto_por_dia[dia] += costo
        gasto_por_proveedor[proveedor] += costo

    # Proyección simple de fin de mes: al ritmo diario promedio de lo que
    # llevamos, ¿cuánto se gastaría en el mes completo?
    hoy = datetime.now()
    if mes == hoy.strftime("%Y-%m") and gasto_por_dia:
        dias_transcurridos = hoy.day
        dias_en_el_mes = (datetime(hoy.year, hoy.month % 12 + 1, 1) - datetime(hoy.year, hoy.month, 1)).days if hoy.month < 12 else 31
        proyeccion_fin_mes = round((total / dias_transcurridos) * dias_en_el_mes, 2) if dias_transcurridos else None
    else:
        proyeccion_fin_mes = None

    return {
        "mes": mes,
        "total_evaluaciones": len(registros),
        "gasto_total": round(total, 4),
        "gasto_por_dia": dict(sorted(gasto_por_dia.items())),
        "gasto_por_proveedor": {k: round(v, 4) for k, v in gasto_por_proveedor.items()},
        "proyeccion_fin_mes": proyeccion_fin_mes,
    }
