"""Permite ver y editar los pesos de la matriz de calidad desde la web,
sin tener que tocar el archivo config/matriz_calidad.json a mano."""
import json
from pathlib import Path

from logging_config import obtener_logger

log = obtener_logger("matriz_editor")

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"

# Ítems que nunca deben poder desaparecer ni quedar en 0% desde el editor web
# (aunque alguien intente ponerlos en 0 por error) — id -> peso mínimo permitido.
# Vacío desde la migración a la Matriz V2 (agosto 2026): la V2 no tiene un ítem
# de "apego a guía operativa", así que ya no hay ningún ítem protegido por
# defecto. Si en el futuro se agrega un ítem crítico que nunca deba poder
# desactivarse, se registra aquí de la misma forma.
ITEMS_PROTEGIDOS = {}


def cargar_matriz_editable() -> dict:
    """Carga la matriz de calidad tal como está guardada en config/matriz_calidad.json."""
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)

    ids_presentes = {it["id"] for cat in matriz["categorias"] for it in cat["items"]}
    faltantes = set(ITEMS_PROTEGIDOS) - ids_presentes
    if faltantes:
        log.error(
            "¡ATENCIÓN! Falta(n) en config/matriz_calidad.json ítem(s) protegido(s) "
            "que no deberían poder eliminarse: %s — esto solo puede pasar si se editó "
            "el archivo JSON directamente, no desde el editor web.", faltantes,
        )

    return matriz


def guardar_pesos(pesos_por_item: dict, pesos_por_categoria: dict) -> dict:
    """
    pesos_por_item: {item_id: nuevo_peso_decimal}
    pesos_por_categoria: {nombre_categoria: nuevo_peso_categoria_decimal}
    Actualiza y guarda config/matriz_calidad.json, conservando nombres,
    descripciones y estructura — solo cambia los números de peso.

    Los ítems de ITEMS_PROTEGIDOS nunca se guardan por debajo de su peso
    mínimo, sin importar qué valor se haya enviado desde el formulario.
    """
    for item_id, minimo in ITEMS_PROTEGIDOS.items():
        if item_id in pesos_por_item and pesos_por_item[item_id] < minimo:
            log.warning(
                "Se intentó guardar '%s' en %.1f%% — se dejó en el mínimo protegido (%.1f%%).",
                item_id, pesos_por_item[item_id] * 100, minimo * 100,
            )
            pesos_por_item[item_id] = minimo

    matriz = cargar_matriz_editable()
    for cat in matriz["categorias"]:
        if cat["nombre"] in pesos_por_categoria:
            cat["peso_categoria"] = pesos_por_categoria[cat["nombre"]]
        for it in cat["items"]:
            if it["id"] in pesos_por_item:
                it["peso"] = pesos_por_item[it["id"]]

    with open(MATRIZ_PATH, "w", encoding="utf-8") as f:
        json.dump(matriz, f, ensure_ascii=False, indent=2)

    return matriz


def suma_total_pesos(matriz: dict = None) -> float:
    """Suma todos los pesos de todos los ítems — debería dar 1.0 (100%) si la matriz está bien balanceada."""
    matriz = matriz or cargar_matriz_editable()
    return round(sum(it["peso"] for cat in matriz["categorias"] for it in cat["items"]), 4)
