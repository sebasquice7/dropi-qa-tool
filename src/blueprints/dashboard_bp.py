"""Rutas del dashboard en vivo — la página solo carga la plantilla; los datos
los pide el navegador vía JavaScript a /api/dashboard."""
from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue

from dashboard_data import obtener_datos_dashboard, guardar_meta

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard() -> ResponseReturnValue:
    """Página del dashboard en vivo — los datos los pide el navegador vía JavaScript a /api/dashboard."""
    return render_template("dashboard.html", activo="dashboard")


@dashboard_bp.route("/api/dashboard")
def api_dashboard() -> ResponseReturnValue:
    """Datos del dashboard en JSON, filtrados por periodo/país/bandeja/área (query params)."""
    periodo = request.args.get("periodo", "todo")
    pais = request.args.get("pais", "").strip() or None
    bandeja = request.args.get("bandeja", "").strip() or None
    area = request.args.get("area", "").strip() or None
    fecha_desde = request.args.get("fecha_desde", "").strip() or None
    fecha_hasta = request.args.get("fecha_hasta", "").strip() or None
    return obtener_datos_dashboard(periodo=periodo, pais=pais, bandeja=bandeja, area=area, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@dashboard_bp.route("/api/dashboard/meta", methods=["POST"])
def api_dashboard_guardar_meta() -> ResponseReturnValue:
    """Guarda la meta de calidad configurada desde el dashboard."""
    try:
        valor = float(request.json.get("meta"))
        valor = max(0.0, min(1.0, valor))
    except (TypeError, ValueError, AttributeError):
        return {"ok": False, "error": "Valor inválido"}, 400
    guardar_meta(valor)
    return {"ok": True, "meta": valor}
