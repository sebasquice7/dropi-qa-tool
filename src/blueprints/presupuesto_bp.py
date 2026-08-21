"""Rutas del simulador de presupuesto de IA."""
from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue

from presupuesto import calcular_presupuesto, calcular_presupuesto_por_asesores, gasto_real_del_mes

presupuesto_bp = Blueprint("presupuesto", __name__)

# Conteo real de asesores activos (Reporte_Asesores_final_con_dia.xlsx,
# hoja "Conversaciones por Asesor") — se usa como valor por defecto en el
# simulador, editable por si el número de asesores cambia con el tiempo.
# Nota: el archivo trae 27 filas de personas, pero 4 no son asesores activos
# reales: una es la fila de "TOTAL" (una suma, no una persona), y 3 son casos
# que el propio archivo marca como "sin cuenta identificable en Intercom"
# (0, 0 y 3 conversaciones — no hay actividad real que evaluar). 27 - 4 = 23.
NUMERO_ASESORES_REAL = 23


@presupuesto_bp.route("/presupuesto")
def presupuesto_ver() -> ResponseReturnValue:
    """Página del simulador de presupuesto interactivo."""
    return render_template("presupuesto.html", activo="presupuesto", numero_asesores_real=NUMERO_ASESORES_REAL)


@presupuesto_bp.route("/api/presupuesto")
def api_presupuesto() -> ResponseReturnValue:
    """Cálculo del presupuesto en JSON — dos modos:
    'volumen_diario' (conversaciones/día, el histórico) o 'por_asesor'
    (número de asesores × evaluaciones/mes por asesor, el enfoque real de
    muestreo de calidad que pidió el equipo: 40/asesor/mes)."""
    modo = request.args.get("modo", "volumen_diario")

    if modo == "por_asesor":
        try:
            numero_asesores = int(request.args.get("numero_asesores", NUMERO_ASESORES_REAL))
            evaluaciones_por_asesor = int(request.args.get("evaluaciones_por_asesor", 40))
        except (TypeError, ValueError):
            numero_asesores, evaluaciones_por_asesor = NUMERO_ASESORES_REAL, 40
        return calcular_presupuesto_por_asesores(numero_asesores, evaluaciones_por_asesor)

    try:
        conversaciones_dia = int(request.args.get("conversaciones_dia", 5000))
        dias_mes = int(request.args.get("dias_mes", 30))
    except (TypeError, ValueError):
        conversaciones_dia, dias_mes = 5000, 30
    return calcular_presupuesto(conversaciones_dia, dias_mes)


@presupuesto_bp.route("/api/gasto-real")
def api_gasto_real() -> ResponseReturnValue:
    """Cuánto se ha gastado REALMENTE en IA este mes (o el mes que se pida
    con ?mes=YYYY-MM), a partir del log real de uso — no de una simulación."""
    mes = request.args.get("mes", "").strip() or None
    return gasto_real_del_mes(mes)
