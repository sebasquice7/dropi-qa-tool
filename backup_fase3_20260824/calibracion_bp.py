"""Ruta del reporte de calibración: qué tan seguido el auditor corrige a la
IA, y en qué categorías lo hace sistemáticamente."""
from flask import Blueprint, render_template
from flask.typing import ResponseReturnValue

from historial import cargar_historial
from calibracion import resumen_calibracion

calibracion_bp = Blueprint("calibracion", __name__)


@calibracion_bp.route("/calibracion")
def calibracion_ver() -> ResponseReturnValue:
    """Solo cuenta evaluaciones hechas vía revisión manual (no las de lote,
    que no pasan por esa pantalla)."""
    registros = cargar_historial()
    resumen = resumen_calibracion(registros)
    return render_template("calibracion.html", resumen=resumen, activo="calibracion")
