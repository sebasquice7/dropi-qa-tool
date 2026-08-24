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


def _pesos_maximos_por_item() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)
    return {it["id"]: it["peso"] for cat in matriz["categorias"] for it in cat["items"]}


def _nombres_items() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)
    return {it["id"]: it["nombre"] for cat in matriz["categorias"] for it in cat["items"]}


def _categoria_de_items() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)
    return {it["id"]: cat["nombre"] for cat in matriz["categorias"] for it in cat["items"]}


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
            # min(..., 1.0): si la matriz cambió de pesos después de que esta
            # evaluación se guardó, el puntaje viejo puede quedar por encima
            # del máximo actual — nunca debe mostrarse más de 100%.
            por_categoria[cat] = round(min(mean(valores) / peso_max, 1.0), 4)

    categorias_ordenadas = sorted(por_categoria.items(), key=lambda x: x[1])

    # Mes actual vs. mes anterior (no "primera evaluación de siempre" vs.
    # "la más reciente") — con ~40 evaluaciones/asesor/mes, comparar contra
    # el inicio de todo el historial deja de ser útil apenas pasan unos
    # meses. El ciclo mensual es la unidad real de coaching: cada mes se
    # compara contra el mes inmediatamente anterior, siempre vigente.
    def _mes_de(registro):
        fecha = registro.get("fecha") or ""
        return fecha[:7] if len(fecha) >= 7 else None  # "2026-08-15" -> "2026-08"

    meses_presentes = sorted({m for m in (_mes_de(r) for r in registros) if m})
    mes_actual = meses_presentes[-1] if meses_presentes else None
    mes_anterior = meses_presentes[-2] if len(meses_presentes) >= 2 else None

    registros_mes_actual = [r for r in registros if _mes_de(r) == mes_actual]
    registros_mes_anterior = [r for r in registros if _mes_de(r) == mes_anterior] if mes_anterior else []

    def _promedio_categorias_de(regs):
        resultado = {}
        for cat, peso_max in pesos.items():
            valores = [r.get("categorias", {}).get(cat) for r in regs if r.get("categorias", {}).get(cat) is not None]
            if valores and peso_max:
                resultado[cat] = round(min(mean(valores) / peso_max, 1.0), 4)
        return resultado

    categorias_mes_actual = _promedio_categorias_de(registros_mes_actual)
    categorias_mes_anterior = _promedio_categorias_de(registros_mes_anterior)

    pesos_max_item = _pesos_maximos_por_item()
    categoria_de_item = _categoria_de_items()
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        pesos_categoria = {cat["nombre"]: cat["peso_categoria"] for cat in json.load(f)["categorias"]}
    por_item = {}
    for r in registros:
        for item_id, detalle in (r.get("items_detalle") or {}).items():
            puntaje = detalle.get("puntaje") if isinstance(detalle, dict) else detalle
            if puntaje is not None:
                por_item.setdefault(item_id, []).append(puntaje)

    items_ordenados = []
    for item_id, valores in por_item.items():
        peso_max = pesos_max_item.get(item_id)
        if valores and peso_max:
            categoria = categoria_de_item.get(item_id, "OTROS")
            peso_categoria = pesos_categoria.get(categoria)
            # Peso RELATIVO a su categoría, no al total de la matriz — así, dentro
            # de cada categoría desplegada, los pesos de sus ítems suman 100%,
            # que es lo que cualquiera espera ver al mirar un grupo ya aislado.
            peso_relativo = round((peso_max / peso_categoria) * 100, 1) if peso_categoria else 0
            items_ordenados.append({
                "id": item_id,
                "nombre": _nombres_items().get(item_id, item_id),
                "categoria": categoria,
                "peso": peso_relativo,
                "porcentaje": round(min(mean(valores) / peso_max, 1.0), 4),
                "veces_evaluado": len(valores),
            })
    items_ordenados.sort(key=lambda x: x["porcentaje"])  # peor a mejor

    # Detalle para la UI de Coaching en la misma escala de la matriz de calidad:
    # peso máximo real de cada ítem/categoría y puntaje promedio obtenido.
    # Se mantiene ``categorias_ordenadas`` arriba porque la IA usa el porcentaje
    # de cumplimiento normalizado (0-100%) para detectar patrones. Esta estructura
    # adicional es exclusivamente para mostrar los puntos reales al auditor.
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz_ui = json.load(f)

    categorias_detalle = []
    for categoria in matriz_ui.get("categorias", []):
        nombre_categoria = categoria.get("nombre", "")
        peso_categoria = float(categoria.get("peso_categoria", 0) or 0)

        valores_categoria = [
            r.get("categorias", {}).get(nombre_categoria)
            for r in registros
            if r.get("categorias", {}).get(nombre_categoria) is not None
        ]
        puntaje_categoria_promedio = (
            round(mean(valores_categoria), 4) if valores_categoria else 0.0
        )

        items_ui = []
        for item in categoria.get("items", []):
            item_id = item.get("id", "")
            peso_max = float(item.get("peso", 0) or 0)
            valores_item = []
            for r in registros:
                detalle = (r.get("items_detalle") or {}).get(item_id)
                if detalle is None:
                    continue
                puntaje = detalle.get("puntaje") if isinstance(detalle, dict) else detalle
                if puntaje is not None:
                    valores_item.append(puntaje)

            puntaje_promedio = round(mean(valores_item), 4) if valores_item else 0.0
            items_ui.append({
                "id": item_id,
                "nombre": item.get("nombre", item_id),
                "peso_max": peso_max,
                "puntaje_promedio": min(puntaje_promedio, peso_max) if peso_max else puntaje_promedio,
                "veces_evaluado": len(valores_item),
            })

        categorias_detalle.append({
            "nombre": nombre_categoria,
            "peso_categoria": peso_categoria,
            "puntaje_promedio": min(puntaje_categoria_promedio, peso_categoria) if peso_categoria else puntaje_categoria_promedio,
            "items": items_ui,
        })

    # Mantiene el mismo orden visual de peor a mejor desempeño que ya tenía
    # Coaching, pero mostrando ahora puntos reales sobre el peso máximo.
    categorias_detalle.sort(
        key=lambda c: (c["puntaje_promedio"] / c["peso_categoria"]) if c["peso_categoria"] else 1.0
    )

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
                oportunidades_recientes.append({"fecha": r.get("fecha"), "id_caso": r.get("id_caso"), "texto": punto})
        for punto in r.get("lo_positivo") or []:
            if len(positivos_recientes) < 6:
                positivos_recientes.append({"fecha": r.get("fecha"), "id_caso": r.get("id_caso"), "texto": punto})

    return {
        "suficientes_datos": True,
        "asesor": asesor,
        "pais": registros[-1].get("pais", ""),  # el país de su evaluación más reciente
        "total": len(registros),
        "primera_fecha": registros[0].get("fecha"),
        "ultima_fecha": registros[-1].get("fecha"),
        "nota_promedio": round(mean(notas), 4),
        "nota_primera_mitad": round(mean(notas[:len(notas)//2 or 1]), 4),
        "nota_segunda_mitad": round(mean(notas[len(notas)//2:]), 4),
        "categorias_ordenadas": categorias_ordenadas,  # peor a mejor
        "items_ordenados": items_ordenados,  # desglose normalizado usado por IA, peor a mejor
        "categorias_detalle": categorias_detalle,  # puntos reales/promedio para el acordeón de la UI
        "mes_actual": mes_actual,
        "mes_anterior": mes_anterior,
        "cantidad_mes_actual": len(registros_mes_actual),
        "cantidad_mes_anterior": len(registros_mes_anterior),
        "categorias_mes_actual": categorias_mes_actual,
        "categorias_mes_anterior": categorias_mes_anterior,
        "total_criticos": len(criticos),
        "criticos_detalle": criticos,
        "oportunidades_recientes": oportunidades_recientes,
        "positivos_recientes": positivos_recientes,
        "hay_evidencia_textual": bool(oportunidades_recientes or positivos_recientes),
    }
