"""Rutas del simulador de presupuesto de IA."""
from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue

from presupuesto import calcular_presupuesto

presupuesto_bp = Blueprint("presupuesto", __name__)


@presupuesto_bp.route("/presupuesto")
def presupuesto_ver() -> ResponseReturnValue:
    """Página del simulador de presupuesto interactivo."""
    return render_template("presupuesto.html", activo="presupuesto")


@presupuesto_bp.route("/api/presupuesto")
def api_presupuesto() -> ResponseReturnValue:
    """Cálculo del presupuesto en JSON, según el volumen de conversaciones (query param)."""
    try:
        conversaciones_dia = int(request.args.get("conversaciones_dia", 5000))
        dias_mes = int(request.args.get("dias_mes", 30))
    except (TypeError, ValueError):
        conversaciones_dia, dias_mes = 5000, 30
    return calcular_presupuesto(conversaciones_dia, dias_mes)
