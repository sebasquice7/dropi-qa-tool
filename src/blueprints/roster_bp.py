"""Ruta del roster: qué asesor maneja cada proceso/bandeja, y a qué área y
país pertenece — vista de solo lectura sobre config/roster_asesores.json."""
from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue

from areas import cargar_roster, asesores_detectados_en_historial, AREAS_DISPONIBLES

roster_bp = Blueprint("roster", __name__)


@roster_bp.route("/roster")
def roster_ver() -> ResponseReturnValue:
    """Tabla completa del roster de asesores, filtrable por área y país —
    más los asesores detectados en evaluaciones reales que todavía no están
    confirmados en el mapa operativo oficial."""
    area = request.args.get("area", "").strip()
    pais = request.args.get("pais", "").strip()

    registros = cargar_roster()
    if area:
        registros = [r for r in registros if r["area"] == area.upper()]
    if pais:
        registros = [r for r in registros if r["pais"].lower() == pais.lower()]

    registros.sort(key=lambda r: (r["area"], r["pais"], r["nombre"]))
    paises_disponibles = sorted({r["pais"] for r in cargar_roster()})

    detectados = asesores_detectados_en_historial()
    if area:
        detectados = [d for d in detectados if d["area"] == area.upper()]
    if pais:
        detectados = [d for d in detectados if d["pais"].lower() == pais.lower()]

    return render_template(
        "roster.html", registros=registros, areas=AREAS_DISPONIBLES,
        paises=paises_disponibles, filtro_area=area, filtro_pais=pais,
        total=len(registros), detectados=detectados, activo="roster",
    )
