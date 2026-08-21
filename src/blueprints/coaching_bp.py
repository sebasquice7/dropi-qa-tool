"""Rutas del plan de coaching por asesor — sintetizado por IA a partir del
historial completo, con revisión humana antes de que quede como versión
final (mismo patrón que /revisar para evaluaciones individuales: la IA
propone, un humano confirma o ajusta, y solo entonces queda oficial)."""
from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask.typing import ResponseReturnValue

from coaching import datos_para_coaching, MINIMO_EVALUACIONES
from evaluator import generar_coaching
from coaching_word import generar_word_coaching
from historial import cargar_historial
from drive_local import guardar_archivo_suelto_en_drive
from logging_config import obtener_logger
from services import coaching_service as coaching_srv

log = obtener_logger("coaching_bp")

coaching_bp = Blueprint("coaching", __name__)


@coaching_bp.route("/coaching")
def coaching_lista() -> ResponseReturnValue:
    """Punto de entrada propio de Coaching — lista a todos los asesores con
    al menos 1 evaluación registrada, para elegir a quién revisar."""
    por_asesor = defaultdict(list)
    for r in cargar_historial():
        agente = r.get("agente")
        if agente:
            por_asesor[agente].append(r)

    asesores = []
    for nombre, evals in por_asesor.items():
        notas = [e.get("nota_final", 0) for e in evals]
        asesores.append({
            "nombre": nombre,
            "total": len(evals),
            "promedio": round((sum(notas) / len(notas)) * 100, 1) if notas else 0,
            "listo_para_coaching": len(evals) >= MINIMO_EVALUACIONES,
        })
    asesores.sort(key=lambda a: a["nombre"])

    return render_template("coaching_lista.html", asesores=asesores, minimo=MINIMO_EVALUACIONES, activo="coaching")


@coaching_bp.route("/coaching/<asesor>")
def coaching_asesor(asesor: str) -> ResponseReturnValue:
    """La IA genera un BORRADOR del plan de coaching — se muestra en una
    pantalla editable (revisar_coaching.html), no como la versión final
    directamente. Nada queda guardado como oficial todavía; eso solo pasa
    cuando el coordinador confirma en /coaching/<asesor>/confirmar."""
    datos = datos_para_coaching(asesor)

    if not datos["suficientes_datos"]:
        return render_template(
            "coaching.html", asesor=asesor, suficientes_datos=False,
            total=datos["total"], minimo=MINIMO_EVALUACIONES, activo="coaching",
        )

    try:
        compromisos_anteriores = coaching_srv.obtener_plan_anterior(asesor)
        plan = generar_coaching(datos, compromisos_anteriores=compromisos_anteriores)
        error = None
    except Exception as e:
        log.error("No se pudo generar el plan de coaching de %s: %s", asesor, e)
        plan = None
        error = str(e)
        return render_template(
            "coaching.html", asesor=asesor, suficientes_datos=True,
            datos=datos, plan=None, error=error, activo="coaching",
        )

    return render_template(
        "revisar_coaching.html", asesor=asesor, datos=datos, plan=plan, activo="coaching",
    )


@coaching_bp.route("/coaching/<asesor>/confirmar", methods=["POST"])
def coaching_confirmar(asesor: str) -> ResponseReturnValue:
    """Guarda la versión FINAL del plan — la que el coordinador revisó y
    ajustó, no la que la IA propuso a ciegas. Esta es la que queda en el
    historial permanente (para el seguimiento de compromisos futuro) y la
    que se descarga como Word."""
    datos = datos_para_coaching(asesor)
    if not datos["suficientes_datos"]:
        flash(f"Todavía no hay suficientes evaluaciones de {asesor} para generar un plan de coaching.")
        return redirect(url_for("coaching.coaching_asesor", asesor=asesor))

    plan_final = {
        "resumen_general": request.form.get("resumen_general", "").strip(),
        "seguimiento_compromisos": request.form.get("seguimiento_compromisos", "").strip(),
        "tendencia": request.form.get("tendencia", "").strip(),
        "alerta_tendencia": request.form.get("alerta_tendencia", "ninguna"),
        "fortalezas_consistentes": [l.strip() for l in request.form.get("fortalezas_consistentes", "").split("\n") if l.strip()],
        "plan_accion": [l.strip() for l in request.form.get("plan_accion", "").split("\n") if l.strip()],
        "areas_prioritarias": [],
    }

    # Cada área prioritaria viene como 3 campos con el mismo índice
    # (area_0, evidencia_0, impacto_0 / area_1, evidencia_1, impacto_1 / ...)
    i = 0
    while f"area_{i}" in request.form:
        nombre_area = request.form.get(f"area_{i}", "").strip()
        if nombre_area:
            plan_final["areas_prioritarias"].append({
                "area": nombre_area,
                "evidencia": request.form.get(f"evidencia_{i}", "").strip(),
                "impacto": request.form.get(f"impacto_{i}", "medio"),
            })
        i += 1

    coaching_srv.guardar_en_cache(asesor, datos, plan_final)
    coaching_srv.guardar_plan_en_historial(asesor, datos, plan_final)

    return redirect(url_for("coaching.coaching_resultado", asesor=asesor))


@coaching_bp.route("/coaching/<asesor>/resultado")
def coaching_resultado(asesor: str) -> ResponseReturnValue:
    """Vista final de solo lectura, con lo que el coordinador ya confirmó."""
    en_cache = coaching_srv.cargar_de_cache(asesor)
    if not en_cache:
        return redirect(url_for("coaching.coaching_asesor", asesor=asesor))
    datos, plan = en_cache
    return render_template(
        "coaching.html", asesor=asesor, suficientes_datos=True,
        datos=datos, plan=plan, error=None, activo="coaching",
    )


@coaching_bp.route("/coaching/<asesor>/word")
def coaching_word(asesor: str) -> ResponseReturnValue:
    """Descarga el plan de coaching como Word — usa la versión CONFIRMADA de
    la caché (la que el coordinador ya revisó), no un borrador sin revisar.
    Además, lo guarda en la misma carpeta de Drive del asesor que ya usan
    sus evaluaciones individuales (<País-Asesor>/), directo ahí, no en una
    subcarpeta de un caso específico — el coaching no es de un caso, es de
    la persona."""
    en_cache = coaching_srv.cargar_de_cache(asesor)

    if en_cache:
        datos, plan = en_cache
    else:
        flash(f"Primero revisa y confirma el plan de {asesor} antes de descargarlo.")
        return redirect(url_for("coaching.coaching_asesor", asesor=asesor))

    nombre_archivo = coaching_srv.nombre_archivo_word(asesor)
    ruta_word = coaching_srv.SALIDAS_DIR / nombre_archivo
    generar_word_coaching(asesor, datos, plan, str(ruta_word))

    pais = datos.get("pais", "")
    nombre_carpeta = f"{pais}-{asesor}" if pais else asesor
    resultado_drive = guardar_archivo_suelto_en_drive(str(ruta_word), subcarpeta_nombre=nombre_carpeta)
    if resultado_drive.get("ok"):
        log.info("Plan de coaching de %s guardado en Drive: %s", asesor, resultado_drive["carpeta"])
    else:
        log.warning("No se pudo guardar el coaching de %s en Drive: %s", asesor, resultado_drive.get("motivo"))

    return send_from_directory(coaching_srv.SALIDAS_DIR, nombre_archivo, as_attachment=True)
