"""Rutas del buscador de evaluaciones pasadas por asesor, ID, fecha o texto."""
import json
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.typing import ResponseReturnValue

from historial import buscar_evaluaciones, buscar_por_timestamp

buscar_bp = Blueprint("buscar", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"


def _detalle_categorias_historial(registro: dict) -> list[dict]:
    """Construye el detalle desplegable de categorías e ítems para el historial.

    Usa la matriz vigente como fuente de nombres y pesos máximos, y combina esos
    datos con los puntajes individuales que quedaron archivados en
    ``items_detalle`` al momento de confirmar la evaluación.

    Si por alguna razón no se puede leer la matriz, devuelve una lista vacía y
    la plantilla conserva el resumen simple anterior como fallback.
    """
    try:
        with open(MATRIZ_PATH, encoding="utf-8") as f:
            matriz = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    items_detalle = registro.get("items_detalle") or {}
    categorias_guardadas = registro.get("categorias") or {}
    resultado = []

    for categoria in matriz.get("categorias", []):
        nombre_categoria = categoria.get("nombre", "")
        items = []
        suma_items = 0.0

        for item in categoria.get("items", []):
            item_id = item.get("id", "")
            try:
                puntaje = float(items_detalle.get(item_id, 0) or 0)
            except (TypeError, ValueError):
                puntaje = 0.0

            try:
                peso_max = float(item.get("peso", 0) or 0)
            except (TypeError, ValueError):
                peso_max = 0.0

            suma_items += puntaje
            items.append({
                "id": item_id,
                "nombre": item.get("nombre", item_id),
                "peso_max": peso_max,
                "puntaje": puntaje,
            })

        # El subtotal guardado es la fuente principal porque representa lo que
        # realmente quedó registrado en esa evaluación. Si no existe, usamos
        # la suma de los ítems individuales.
        subtotal_guardado = categorias_guardadas.get(nombre_categoria)
        try:
            subtotal = float(subtotal_guardado) if subtotal_guardado is not None else suma_items
        except (TypeError, ValueError):
            subtotal = suma_items

        try:
            peso_categoria = float(categoria.get("peso_categoria", 0) or 0)
        except (TypeError, ValueError):
            peso_categoria = sum(i["peso_max"] for i in items)

        resultado.append({
            "nombre": nombre_categoria,
            "peso_categoria": peso_categoria,
            "subtotal": subtotal,
            "items": items,
        })

    return resultado


@buscar_bp.route("/buscar")
def buscar() -> ResponseReturnValue:
    """Pantalla de búsqueda: sin filtros muestra el formulario vacío, con filtros muestra los resultados."""
    asesor = request.args.get("asesor", "").strip()
    id_caso = request.args.get("id_caso", "").strip()
    texto = request.args.get("texto", "").strip()
    fecha_desde = request.args.get("fecha_desde", "").strip()
    fecha_hasta = request.args.get("fecha_hasta", "").strip()

    hay_filtros = any([asesor, id_caso, texto, fecha_desde, fecha_hasta])
    resultados = buscar_evaluaciones(
        asesor=asesor or None, id_caso=id_caso or None, texto=texto or None,
        fecha_desde=fecha_desde or None, fecha_hasta=fecha_hasta or None,
    ) if hay_filtros else []

    return render_template(
        "buscar.html", resultados=resultados, hay_filtros=hay_filtros,
        filtros={"asesor": asesor, "id_caso": id_caso, "texto": texto, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta},
        activo="buscar",
    )


@buscar_bp.route("/buscar/detalle/<timestamp>")
def buscar_detalle(timestamp: str) -> ResponseReturnValue:
    """Detalle de una evaluación específica del historial, identificada por su timestamp único."""
    registro = buscar_por_timestamp(timestamp)
    if not registro:
        flash("No se encontró esa evaluación (puede que se haya reiniciado el historial).")
        return redirect(url_for("buscar.buscar"))

    sufijo = registro.get("id_caso") or ""
    ruta_excel = SALIDAS_DIR / f"Matriz_{sufijo}.xlsx"
    ruta_word = SALIDAS_DIR / f"Informe_{sufijo}.docx"
    detalle_categorias = _detalle_categorias_historial(registro)

    return render_template(
        "historial_detalle.html", r=registro,
        detalle_categorias=detalle_categorias,
        excel_disponible=ruta_excel.exists(), word_disponible=ruta_word.exists(),
        excel_nombre=ruta_excel.name, word_nombre=ruta_word.name, activo="buscar",
    )
