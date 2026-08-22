"""Mantiene un historial local (JSON) de todas las evaluaciones ya generadas
(Excel + Word confirmados), para poder calcular KPIs agregados después.

No reemplaza los borradores ni los documentos finales: es un registro liviano,
un renglón por evaluación, con lo mínimo necesario para sacar estadísticas.
"""
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORIAL_PATH = BASE_DIR / "historial_evaluaciones.json"
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
_SALIDAS_DIR = BASE_DIR / "salidas"


def _cargar_matriz() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        return json.load(f)


def _subtotales_por_categoria(evaluacion: dict) -> dict:
    """Suma los puntajes de los ítems de cada categoría, para poder comparar
    desempeño por categoría entre evaluaciones (ej. 'Comunicación Escrita': 0.13)."""
    matriz = _cargar_matriz()
    items_eval = evaluacion.get("items", {})
    subtotales = {}
    for cat in matriz["categorias"]:
        suma = sum(
            float(items_eval.get(it["id"], {}).get("puntaje", 0))
            for it in cat["items"]
        )
        subtotales[cat["nombre"]] = round(suma, 4)
    return subtotales


def _detalle_por_item(evaluacion: dict) -> dict:
    """Puntaje de CADA ítem individual (no solo el subtotal por categoría),
    para poder hacer drill-down: 'dentro de Comunicación Escrita, cuál ítem
    específico es el que más está fallando'."""
    items_eval = evaluacion.get("items", {})
    return {
        iid: round(float(v.get("puntaje", 0)), 4)
        for iid, v in items_eval.items()
    }


def registrar_evaluacion(metadata: dict, evaluacion: dict, nota: dict, calibracion: dict = None) -> dict:
    """Agrega un renglón al historial local. Se llama justo después de generar
    el Excel y el Word finales de una evaluación (no en el borrador)."""
    ahora = datetime.now()

    registro = {
        "timestamp": ahora.isoformat(timespec="seconds"),
        "fecha": ahora.strftime("%Y-%m-%d"),
        "agente": metadata.get("agente", ""),
        "bandeja": metadata.get("bandeja", ""),
        "id_caso": metadata.get("id_caso", ""),
        "pais": metadata.get("pais", ""),
        "evaluado_por": metadata.get("evaluado_por", ""),
        "nota_final": nota.get("nota_final", 0),
        "nota_bruta": nota.get("nota_bruta", 0),
        "critico_activado": nota.get("critico_activado"),
        "categorias": _subtotales_por_categoria(evaluacion),
        "items_detalle": _detalle_por_item(evaluacion),
        "oportunidades_mejora": evaluacion.get("oportunidades_mejora", []),
        "lo_positivo": evaluacion.get("lo_positivo", []),
        "calibracion": calibracion,
        "guia_utilizada": evaluacion.get("guia_utilizada"),
        "satisfaccion": evaluacion.get("satisfaccion"),
        "satisfaccion_comentarios": evaluacion.get("satisfaccion_comentarios"),
        # Con qué proveedor/modelo de IA se generó la evaluación — visible en
        # el historial para poder explicar diferencias entre corridas de la
        # misma conversación (ver nota en evaluator.py:_llamar_gemini).
        "proveedor_usado": evaluacion.get("proveedor_usado"),
        "modelo_usado": evaluacion.get("modelo_usado"),
        # Marca con qué versión de la matriz se hizo esta evaluación. Si la
        # matriz vuelve a cambiar en el futuro, este campo permite detectar
        # qué registros hay que volver a migrar (ver migrar_historial_v2.py
        # como referencia de cómo se hizo la última migración, V1 -> V2).
        "matriz_version": "v2",
    }

    historial = []
    if HISTORIAL_PATH.exists():
        try:
            with open(HISTORIAL_PATH, encoding="utf-8") as f:
                historial = json.load(f)
        except (json.JSONDecodeError, OSError):
            historial = []

    historial.append(registro)

    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    return registro


def cargar_historial(solo_hoy: bool = False) -> list:
    """Lee el historial completo de evaluaciones desde disco, opcionalmente filtrado solo a las de hoy."""
    if not HISTORIAL_PATH.exists():
        return []
    try:
        with open(HISTORIAL_PATH, encoding="utf-8") as f:
            historial = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if solo_hoy:
        hoy = datetime.now().strftime("%Y-%m-%d")
        historial = [r for r in historial if r.get("fecha") == hoy]

    return historial


def buscar_duplicado(id_caso: str) -> dict | None:
    """Devuelve la evaluación anterior más reciente con el mismo ID de caso,
    o None si no hay ninguna. Útil para avisar antes de evaluar dos veces
    el mismo caso por accidente."""
    id_caso = (id_caso or "").strip()
    if not id_caso:
        return None
    coincidencias = [r for r in cargar_historial() if (r.get("id_caso") or "").strip() == id_caso]
    if not coincidencias:
        return None
    return sorted(coincidencias, key=lambda r: r.get("timestamp", ""), reverse=True)[0]


def buscar_evaluacion_completa(id_caso: str) -> dict | None:
    """Busca si existe una evaluación CONFIRMADA anterior del mismo caso que
    incluya la evaluación completa (con justificaciones, lo_positivo,
    oportunidades_mejora) — no solo los puntajes numéricos del historial.

    Revisa primero si hay un borrador confirmado guardado en salidas/ con
    los datos completos; si no, devuelve None (no se puede reutilizar una
    evaluación de la que solo quedan los números, porque le faltarían las
    justificaciones que son justamente lo más valioso del análisis).
    """
    id_caso = (id_caso or "").strip()
    if not id_caso:
        return None

    # Busca en el directorio de salidas si existe un archivo de evaluación
    # completa previamente guardado para este caso.
    ruta_evaluacion = _SALIDAS_DIR / f"evaluacion_completa_{id_caso}.json"
    if not ruta_evaluacion.exists():
        return None

    try:
        with open(ruta_evaluacion, encoding="utf-8") as f:
            datos = json.load(f)
        # Validar que tenga la estructura mínima esperada
        if "evaluacion" not in datos or "metadata" not in datos or "nota" not in datos:
            return None
        return datos
    except (json.JSONDecodeError, OSError):
        return None


def guardar_evaluacion_completa(id_caso: str, metadata: dict, evaluacion: dict, nota: dict) -> None:
    """Guarda la evaluación completa (con justificaciones, lo_positivo,
    oportunidades_mejora) para poder reutilizarla si alguien vuelve a subir
    el mismo caso. Se llama al momento de CONFIRMAR la evaluación (no al
    crear el borrador), para que lo que se guarde sea la versión final
    ajustada por el auditor humano — no la versión cruda de la IA.

    Solo se guarda si hay un id_caso real (no se puede indexar por nada más
    de forma confiable — dos PDFs distintos pueden tener conversaciones
    distintas del mismo asesor)."""
    id_caso = (id_caso or "").strip()
    if not id_caso:
        return

    datos = {
        "metadata": metadata,
        "evaluacion": evaluacion,
        "nota": nota,
        "guardado_en": datetime.now().isoformat(timespec="seconds"),
        "matriz_version": "v2",
    }
    ruta = _SALIDAS_DIR / f"evaluacion_completa_{id_caso}.json"
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # no romper el flujo principal por esto


def tendencia_por_asesor(registros: list = None) -> dict:
    """Devuelve {fecha: {asesor: nota_promedio_ese_dia}}, para graficar la
    evolución de cada asesor a lo largo del tiempo."""
    from collections import defaultdict
    from statistics import mean

    if registros is None:
        registros = cargar_historial()

    datos = defaultdict(lambda: defaultdict(list))
    for r in registros:
        datos[r.get("fecha", "")][r.get("agente", "")].append(r.get("nota_final", 0))

    resultado = {}
    for fecha, por_asesor in datos.items():
        resultado[fecha] = {a: round(mean(v), 4) for a, v in por_asesor.items()}
    return resultado


def buscar_evaluaciones(asesor: str = None, id_caso: str = None, texto: str = None,
                         fecha_desde: str = None, fecha_hasta: str = None) -> list:
    """Filtra el historial por cualquier combinación de criterios. Todos son
    opcionales; el texto busca dentro de oportunidades_mejora y lo_positivo
    (no distingue mayúsculas/minúsculas)."""
    registros = cargar_historial()

    if asesor:
        asesor_lower = asesor.strip().lower()
        registros = [r for r in registros if asesor_lower in (r.get("agente") or "").lower()]
    if id_caso:
        id_lower = id_caso.strip().lower()
        registros = [r for r in registros if id_lower in (r.get("id_caso") or "").lower()]
    if fecha_desde:
        registros = [r for r in registros if (r.get("fecha") or "") >= fecha_desde]
    if fecha_hasta:
        registros = [r for r in registros if (r.get("fecha") or "") <= fecha_hasta]
    if texto:
        texto_lower = texto.strip().lower()
        def _coincide(r: dict) -> bool:
            textos = (r.get("oportunidades_mejora") or []) + (r.get("lo_positivo") or [])
            return any(texto_lower in t.lower() for t in textos)
        registros = [r for r in registros if _coincide(r)]

    registros.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return registros


def buscar_por_timestamp(timestamp: str) -> dict | None:
    """Devuelve el registro exacto con ese timestamp (clave única), o None."""
    for r in cargar_historial():
        if r.get("timestamp") == timestamp:
            return r
    return None
