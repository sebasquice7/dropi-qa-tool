"""Rutas del buscador de evaluaciones pasadas por asesor, ID, fecha o texto."""
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.typing import ResponseReturnValue

from historial import buscar_evaluaciones, buscar_por_timestamp

buscar_bp = Blueprint("buscar", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"


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

    return render_template(
        "historial_detalle.html", r=registro,
        excel_disponible=ruta_excel.exists(), word_disponible=ruta_word.exists(),
        excel_nombre=ruta_excel.name, word_nombre=ruta_word.name, activo="buscar",
    )
