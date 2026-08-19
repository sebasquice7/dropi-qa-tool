"""Rutas del plan de coaching por asesor — sintetizado por IA a partir del
historial completo, con opción de descargarlo como Word."""
from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory
from flask.typing import ResponseReturnValue

from coaching import datos_para_coaching, MINIMO_EVALUACIONES
from evaluator import generar_coaching
from coaching_word import generar_word_coaching
from logging_config import obtener_logger
from services import coaching_service as coaching_srv

log = obtener_logger("coaching_bp")

coaching_bp = Blueprint("coaching", __name__)


@coaching_bp.route("/coaching/<asesor>")
def coaching_asesor(asesor: str) -> ResponseReturnValue:
    """Plan de coaching sintetizado por IA a partir de TODO el historial de un
    asesor (no de una sola conversación) — pensado para preparar una
    conversación de desarrollo real con evidencia concreta."""
    datos = datos_para_coaching(asesor)

    if not datos["suficientes_datos"]:
        return render_template(
            "coaching.html", asesor=asesor, suficientes_datos=False,
            total=datos["total"], minimo=MINIMO_EVALUACIONES, activo="dashboard",
        )

    try:
        plan = generar_coaching(datos)
        error = None
        coaching_srv.guardar_en_cache(asesor, datos, plan)
    except Exception as e:
        log.error("No se pudo generar el plan de coaching de %s: %s", asesor, e)
        plan = None
        error = str(e)

    return render_template(
        "coaching.html", asesor=asesor, suficientes_datos=True,
        datos=datos, plan=plan, error=error, activo="dashboard",
    )


@coaching_bp.route("/coaching/<asesor>/word")
def coaching_word(asesor: str) -> ResponseReturnValue:
    """Descarga el plan de coaching como Word — usa la caché si existe, o lo genera de cero."""
    en_cache = coaching_srv.cargar_de_cache(asesor)

    if en_cache:
        datos, plan = en_cache
    else:
        # No hay caché (ej. entraste directo a esta URL) -> generar de cero
        datos = datos_para_coaching(asesor)
        if not datos["suficientes_datos"]:
            flash(f"Todavía no hay suficientes evaluaciones de {asesor} para generar un plan de coaching.")
            return redirect(url_for("coaching.coaching_asesor", asesor=asesor))
        try:
            plan = generar_coaching(datos)
        except Exception as e:
            log.error("No se pudo generar el plan de coaching de %s: %s", asesor, e)
            flash(f"No se pudo generar el plan: {e}")
            return redirect(url_for("coaching.coaching_asesor", asesor=asesor))

    nombre_archivo = coaching_srv.nombre_archivo_word(asesor)
    ruta_word = coaching_srv.SALIDAS_DIR / nombre_archivo
    generar_word_coaching(asesor, datos, plan, str(ruta_word))
    return send_from_directory(coaching_srv.SALIDAS_DIR, nombre_archivo, as_attachment=True)
