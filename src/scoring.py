"""Calcula la nota final de una evaluación, replicando la lógica de la matriz Excel:
suma de puntajes por ítem, salvo que algún ítem crítico haya ocurrido, en cuyo caso
la nota final es 0%.
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"


def _pesos_maximos() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)
    return {
        it["id"]: it["peso"]
        for cat in matriz["categorias"]
        for it in cat["items"]
    }


def _quitar_markdown(texto: str) -> str:
    """Quita asteriscos de negrita/cursiva estilo Markdown (**texto** o *texto*)
    que la IA a veces agrega por costumbre, aunque se le pida no hacerlo. El
    programa ya aplica su propia negrita (primera frase) al generar el Word."""
    if not isinstance(texto, str):
        return texto
    return re.sub(r"\*+", "", texto)


def normalizar_evaluacion(evaluacion: dict) -> dict:
    """
    Corrige puntajes que la IA haya devuelto fuera de escala (ej. 5 en vez de 0.05,
    o 500 en vez de 0.05). Detecta la escala comparando el puntaje contra el peso
    máximo real del ítem (definido en config/matriz_calidad.json) y lo reescala,
    luego lo limita (clamp) al rango [0, peso_máximo] por seguridad.

    También limpia cualquier asterisco de Markdown que se haya colado en los
    textos (justificaciones, lo_positivo, oportunidades_mejora, resumen_caso).
    """
    pesos = _pesos_maximos()
    items = evaluacion.get("items", {})

    for iid, peso_max in pesos.items():
        if iid not in items:
            continue
        try:
            valor = float(items[iid].get("puntaje", 0))
        except (TypeError, ValueError):
            valor = 0.0

        # Si el valor es mucho mayor al máximo esperado, probablemente la IA
        # devolvió el número en otra escala (enteros, porcentaje, etc.) -> reescalar.
        if peso_max > 0 and valor > peso_max * 1.5:
            # Prueba escalas comunes: /100 (si dio 5 queriendo decir 5%) o /1000
            for divisor in (100, 1000, 10):
                candidato = valor / divisor
                if 0 <= candidato <= peso_max * 1.5:
                    valor = candidato
                    break

        # Límite final de seguridad: nunca por debajo de 0 ni por encima del máximo
        valor = max(0.0, min(valor, peso_max))
        items[iid]["puntaje"] = round(valor, 4)
        if "justificacion" in items[iid]:
            items[iid]["justificacion"] = _quitar_markdown(items[iid]["justificacion"])

    evaluacion["items"] = items

    for cid, v in evaluacion.get("items_criticos", {}).items():
        if "justificacion" in v:
            v["justificacion"] = _quitar_markdown(v["justificacion"])

    # Si la IA se saltó algún ítem crítico en su respuesta (pasa de vez en
    # cuando, sobre todo con modelos más chicos bajo carga), se rellena con
    # "No" por defecto — nunca se asume "Sí" por un dato faltante, y así la
    # plantilla de revisión siempre encuentra los 6 ítems, sin importar si
    # la IA los trajo completos o no.
    criticos = evaluacion.setdefault("items_criticos", {})
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        criticos_esperados = json.load(f).get("items_criticos", [])
    for c in criticos_esperados:
        if c["id"] not in criticos:
            criticos[c["id"]] = {"ocurrio": "No", "justificacion": "(la IA no evaluó este ítem explícitamente — se asume 'No' por seguridad, revísalo a mano si el caso lo amerita)"}

    evaluacion["lo_positivo"] = [_quitar_markdown(p) for p in evaluacion.get("lo_positivo", [])]
    evaluacion["oportunidades_mejora"] = [_quitar_markdown(p) for p in evaluacion.get("oportunidades_mejora", [])]
    if "resumen_caso" in evaluacion:
        evaluacion["resumen_caso"] = _quitar_markdown(evaluacion["resumen_caso"])

    return evaluacion


def calcular_nota(evaluacion: dict) -> dict:
    """
    evaluacion: dict con 'items' (id -> {puntaje, justificacion}) e 'items_criticos'
    (id -> {ocurrio: 'Si'/'No', justificacion})

    Devuelve dict con: nota_bruta (suma de items sin aplicar críticos),
    nota_final (0 si algún crítico ocurrió), critico_activado (bool/id).
    """
    nota_bruta = sum(float(v["puntaje"]) for v in evaluacion.get("items", {}).values())

    critico_activado = None
    for cid, v in evaluacion.get("items_criticos", {}).items():
        if str(v.get("ocurrio", "No")).strip().lower() == "si":
            critico_activado = cid
            break

    nota_final = 0.0 if critico_activado else nota_bruta

    return {
        "nota_bruta": round(nota_bruta, 4),
        "nota_final": round(nota_final, 4),
        "critico_activado": critico_activado,
    }
