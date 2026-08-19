"""Rutas de informes: el Excel de KPIs y la exportación CSV del historial
completo."""
import csv
import io
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, Response
from flask.typing import ResponseReturnValue

from historial import cargar_historial
from kpi_report import generar_informe_kpis
from drive_local import guardar_archivo_suelto_en_drive
from logging_config import obtener_logger

log = obtener_logger("informes_bp")

informes_bp = Blueprint("informes", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"


@informes_bp.route("/informe")
def informe_kpis() -> ResponseReturnValue:
    """Genera y muestra el informe de KPIs en Excel (de hoy o histórico, según el parámetro 'alcance')."""
    alcance = request.args.get("alcance", "todo")  # "hoy" o "todo"
    solo_hoy = alcance == "hoy"

    registros = cargar_historial(solo_hoy=solo_hoy)

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if solo_hoy:
        titulo = f"Informe de evaluaciones del día ({fecha_hoy})"
        nombre_archivo = f"Informe de todas las conversaciones - Hoy {fecha_hoy}.xlsx"
    else:
        titulo = "Informe histórico de todas las evaluaciones"
        nombre_archivo = f"Informe de todas las conversaciones - Historico {fecha_hoy}.xlsx"

    ruta_informe = SALIDAS_DIR / nombre_archivo
    generar_informe_kpis(registros, str(ruta_informe), titulo=titulo)

    drive_resultado = guardar_archivo_suelto_en_drive(str(ruta_informe))
    if drive_resultado.get("ok"):
        log.info("Informe KPI guardado en Drive: %s", drive_resultado["carpeta"])
    else:
        log.warning("Informe KPI no se guardó en Drive: %s", drive_resultado.get("motivo"))

    return render_template(
        "informe_kpis.html", alcance=alcance, total=len(registros),
        nombre_archivo=nombre_archivo, drive_resultado=drive_resultado, activo="informes",
    )


@informes_bp.route("/historial.csv")
def exportar_historial_csv() -> ResponseReturnValue:
    """Descarga el historial completo de evaluaciones como CSV, para abrirlo
    en Excel/Google Sheets y cruzarlo con lo que necesites por fuera del
    programa."""
    registros = cargar_historial()
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["Fecha", "Asesor", "Bandeja", "ID Caso", "País", "Evaluado por", "Nota Final (%)", "Ítem Crítico"])
    for r in sorted(registros, key=lambda x: x.get("timestamp", ""), reverse=True):
        escritor.writerow([
            r.get("fecha", ""), r.get("agente", ""), r.get("bandeja", ""), r.get("id_caso", ""),
            r.get("pais", ""), r.get("evaluado_por", ""),
            round(r.get("nota_final", 0) * 100, 1), r.get("critico_activado") or "",
        ])

    nombre_archivo = f"historial_evaluaciones_{datetime.now().strftime('%Y-%m-%d')}.csv"
    return Response(
        "\ufeff" + salida.getvalue(),  # BOM al inicio: para que Excel abra bien los acentos
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )
