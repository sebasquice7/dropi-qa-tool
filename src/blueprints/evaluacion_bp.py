"""Rutas web del flujo de evaluación: subir un PDF, revisarlo, confirmarlo, y
las variantes de lote y comparación entre IAs.

Este archivo es deliberadamente "delgado": cada ruta hace poco más que leer
la petición, llamar a la función del servicio correspondiente (en
`services/`), y decidir qué plantilla mostrar. Toda la lógica real vive en
los servicios — aquí solo se traduce HTTP <-> llamadas de función.
"""
import uuid
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask.typing import ResponseReturnValue
from werkzeug.utils import secure_filename

from pdf_parser import cargar_conversacion_desde_pdf, extraer_texto_pdf, parsear_conversacion, detectar_metadata
from evaluator import proveedores_configurados, PROVEEDORES_INFO
from historial import buscar_duplicado, buscar_evaluacion_completa
from logging_config import obtener_logger

from services import evaluacion_service as ev_srv
from services import lote_service as lote_srv
from services import comparacion_service as cmp_srv

log = obtener_logger("evaluacion_bp")

evaluacion_bp = Blueprint("evaluacion", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
SALIDAS_DIR = BASE_DIR / "salidas"


def _renderizar_revision(resultado: dict) -> ResponseReturnValue:
    """Arma los datos que necesita revisar.html y la renderiza — el paso
    final compartido por el flujo individual, el de completar un omitido del
    lote, y el de elegir cuál IA usar tras comparar."""
    datos = ev_srv.datos_para_revision(resultado["token"], resultado["metadata"], resultado["evaluacion"], resultado["nota"])
    return render_template("revisar.html", activo="evaluar", **datos)


# ---------------------------------------------------------------- Individual

@evaluacion_bp.route("/")
def index() -> ResponseReturnValue:
    """Página principal: subir un PDF para evaluar, individual o en lote."""
    return render_template(
        "index.html",
        proveedores_disponibles=proveedores_configurados(),
        proveedores_info=PROVEEDORES_INFO,
        activo="evaluar",
    )


@evaluacion_bp.route("/detectar", methods=["POST"])
def detectar() -> ResponseReturnValue:
    """Lee el PDF apenas se sube (antes de evaluar) y devuelve bandeja/ID/país/
    asesores detectados, para autocompletar el formulario. No usa la IA, es
    solo lectura de texto."""
    pdf_file = request.files.get("pdf")
    if not pdf_file or pdf_file.filename == "":
        return {"error": "sin archivo"}, 400

    token = uuid.uuid4().hex[:8]
    nombre_seguro = secure_filename(pdf_file.filename)
    ruta_tmp = UPLOADS_DIR / f"tmp_{token}_{nombre_seguro}"
    pdf_file.save(ruta_tmp)
    try:
        texto_crudo = extraer_texto_pdf(str(ruta_tmp))
        conv = parsear_conversacion(texto_crudo)
        meta = detectar_metadata(conv, texto_crudo, nombre_archivo=nombre_seguro)
        asesores = list(conv.remitentes_staff().keys())
        duplicado = buscar_duplicado(meta.get("id_caso"))
        tiene_evaluacion_reutilizable = buscar_evaluacion_completa(meta.get("id_caso")) is not None

        return {
            "bandeja": meta.get("bandeja") or "",
            "bandeja_es_sugerencia": meta.get("bandeja_es_sugerencia", False),
            "id_caso": meta.get("id_caso") or "",
            "pais": meta.get("pais") or "",
            "pais_es_sugerencia": meta.get("pais_es_sugerencia", False),
            "asesores": asesores,
            "duplicado": {
                "fecha": duplicado.get("fecha"),
                "agente": duplicado.get("agente"),
                "nota_final": duplicado.get("nota_final"),
            } if duplicado else None,
            "reutilizable": tiene_evaluacion_reutilizable,
        }
    except Exception as e:
        log.error("Error al detectar metadata del PDF: %s", e)
        return {"error": str(e)}, 500
    finally:
        try:
            ruta_tmp.unlink()
        except OSError:
            pass


@evaluacion_bp.route("/evaluar", methods=["POST"])
def evaluar() -> ResponseReturnValue:
    """Sube un PDF y corre la evaluación individual completa."""
    pdf_file = request.files.get("pdf")
    if not pdf_file or pdf_file.filename == "":
        flash("Por favor selecciona un archivo PDF.")
        return redirect(url_for("evaluacion.index"))

    token = uuid.uuid4().hex[:8]
    ruta_pdf = UPLOADS_DIR / f"{token}_{secure_filename(pdf_file.filename)}"
    pdf_file.save(ruta_pdf)

    conv = cargar_conversacion_desde_pdf(str(ruta_pdf))
    remitentes = list(conv.remitentes_staff().keys())

    asesor = request.form.get("asesor", "").strip()
    if not asesor:
        if len(remitentes) == 0:
            flash("No se detectó ningún asesor humano en la conversación.")
            return redirect(url_for("evaluacion.index"))
        asesor = " y ".join(remitentes)  # varios asesores: se juntan y se sigue sin pausar

    try:
        resultado = ev_srv.iniciar_evaluacion(
            ruta_pdf, asesor, token,
            bandeja=request.form.get("bandeja", "").strip(),
            pais=request.form.get("pais", "").strip(),
            id_caso=request.form.get("id_caso", "").strip(),
            auditor=request.form.get("auditor", ""),
        )
    except Exception as e:
        log.error("Error al evaluar con la IA: %s", e)
        flash(f"Error al evaluar con la IA: {e}")
        return redirect(url_for("evaluacion.index"))

    return _renderizar_revision(resultado)


@evaluacion_bp.route("/reutilizar", methods=["POST"])
def reutilizar() -> ResponseReturnValue:
    """Carga la evaluación completa guardada de una evaluación anterior del
    mismo caso, en vez de volver a llamar a la IA. Garantiza consistencia
    100% para el mismo ticket: misma nota, mismas justificaciones, mismos
    positivos y oportunidades de mejora."""
    id_caso = request.form.get("id_caso", "").strip()
    if not id_caso:
        flash("No se puede reutilizar sin un ID de caso.")
        return redirect(url_for("evaluacion.index"))

    datos_anteriores = buscar_evaluacion_completa(id_caso)
    if not datos_anteriores:
        flash("No se encontró una evaluación completa guardada para este caso. Evalúa de nuevo.")
        return redirect(url_for("evaluacion.index"))

    metadata = datos_anteriores["metadata"]
    evaluacion = datos_anteriores["evaluacion"]
    nota = datos_anteriores["nota"]

    # Crear un borrador con los datos reutilizados para que la pantalla de
    # revisión funcione igual (el auditor puede ajustar si quiere).
    token = uuid.uuid4().hex[:8]
    ev_srv.guardar_borrador(token, metadata, evaluacion, nota)

    return _renderizar_revision({"token": token, "metadata": metadata, "evaluacion": evaluacion, "nota": nota})


@evaluacion_bp.route("/evaluar-con-asesor", methods=["POST"])
def evaluar_con_asesor() -> ResponseReturnValue:
    """Continúa la evaluación de un caso donde el asesor se pidió explícito
    (ej. al completar un omitido del lote), reutilizando el PDF ya subido."""
    ruta_pdf = Path(request.form["ruta_pdf"])
    asesor = request.form["asesor"]
    token = request.form["token"]

    try:
        resultado = ev_srv.iniciar_evaluacion(
            ruta_pdf, asesor, token,
            bandeja=request.form.get("bandeja", "").strip(),
            pais=request.form.get("pais", "").strip(),
            id_caso=request.form.get("id_caso", "").strip(),
            auditor=request.form.get("auditor", ""),
        )
    except Exception as e:
        log.error("Error al evaluar con la IA: %s", e)
        flash(f"Error al evaluar con la IA: {e}")
        return redirect(url_for("evaluacion.index"))

    return _renderizar_revision(resultado)


@evaluacion_bp.route("/generar", methods=["POST"])
def generar() -> ResponseReturnValue:
    """Confirma la evaluación con los ajustes que hizo el auditor en la
    pantalla de revisión, genera los documentos finales, y muestra el
    resultado."""
    token = request.form["token"]

    from matriz_editor import cargar_matriz_editable
    matriz = cargar_matriz_editable()

    puntajes, justificaciones, criticos_ocurrieron, criticos_justificaciones = {}, {}, {}, {}
    for cat in matriz["categorias"]:
        for it in cat["items"]:
            iid = it["id"]
            puntaje = request.form.get(f"puntaje__{iid}")
            if puntaje is not None:
                try:
                    puntajes[iid] = float(puntaje)
                except ValueError:
                    continue
                justificaciones[iid] = request.form.get(f"justificacion__{iid}", "")

    for c in matriz["items_criticos"]:
        cid = c["id"]
        criticos_ocurrieron[cid] = request.form.get(f"critico__{cid}") == "on"
        criticos_justificaciones[cid] = request.form.get(f"critico_just__{cid}", "")

    ajustes = {
        "puntajes": puntajes,
        "justificaciones": justificaciones,
        "criticos_ocurrieron": criticos_ocurrieron,
        "criticos_justificaciones": criticos_justificaciones,
        "lo_positivo": [l.strip() for l in request.form.get("lo_positivo", "").split("\n") if l.strip()],
        "oportunidades_mejora": [l.strip() for l in request.form.get("oportunidades_mejora", "").split("\n") if l.strip()],
        "resumen_caso": request.form.get("resumen_caso", ""),
        "satisfaccion": request.form.get("satisfaccion", ""),
        "satisfaccion_comentarios": request.form.get("satisfaccion_comentarios", ""),
    }

    try:
        resultado = ev_srv.aplicar_ajustes_y_confirmar(token, ajustes)
    except FileNotFoundError:
        flash("Ese borrador ya no está disponible (puede que el servidor se haya reiniciado). Evalúa la conversación de nuevo.")
        return redirect(url_for("evaluacion.index"))

    return render_template("resultado.html", **resultado)


@evaluacion_bp.route("/descargar/<nombre>")
def descargar(nombre: str) -> ResponseReturnValue:
    """Descarga un archivo generado (Excel o Word) desde la carpeta de salidas."""
    return send_from_directory(SALIDAS_DIR, nombre, as_attachment=True)


# --------------------------------------------------------------- Comparación

@evaluacion_bp.route("/evaluar-comparar", methods=["POST"])
def evaluar_comparar() -> ResponseReturnValue:
    """Evalúa la misma conversación con TODOS los proveedores de IA que
    tengan API key configurada (hoy probablemente solo Gemini; apenas
    agregues ANTHROPIC_API_KEY / OPENAI_API_KEY, se suman solos)."""
    pdf_file = request.files.get("pdf")
    if not pdf_file or pdf_file.filename == "":
        flash("Por favor selecciona un archivo PDF.")
        return redirect(url_for("evaluacion.index"))

    disponibles = proveedores_configurados()
    if len(disponibles) < 2:
        flash("Solo tienes 1 proveedor de IA configurado — agrega ANTHROPIC_API_KEY y/o OPENAI_API_KEY a tu .env para poder comparar entre varios.")
        return redirect(url_for("evaluacion.index"))

    token = uuid.uuid4().hex[:8]
    ruta_pdf = UPLOADS_DIR / f"{token}_{secure_filename(pdf_file.filename)}"
    pdf_file.save(ruta_pdf)

    conv = cargar_conversacion_desde_pdf(str(ruta_pdf))
    remitentes = list(conv.remitentes_staff().keys())

    asesor = request.form.get("asesor", "").strip()
    if not asesor:
        if len(remitentes) == 0:
            flash("No se detectó ningún asesor humano en la conversación.")
            return redirect(url_for("evaluacion.index"))
        asesor = " y ".join(remitentes)

    resultado = cmp_srv.comparar_con_varias_ias(
        conv.texto_plano(), asesor, disponibles,
        bandeja=request.form.get("bandeja", "").strip(), pais=request.form.get("pais", "").strip(),
        id_caso=request.form.get("id_caso", ""), auditor=request.form.get("auditor", ""), token=token,
    )

    return render_template(
        "comparar_resultado.html", token=token, proveedores_info=PROVEEDORES_INFO,
        modo_demo=False, activo="evaluar", **resultado,
    )


@evaluacion_bp.route("/evaluar-comparar-demo", methods=["POST"])
def evaluar_comparar_demo() -> ResponseReturnValue:
    """Genera una pantalla de comparación de DEMOSTRACIÓN: una evaluación
    real con Gemini + 2 variantes simuladas, para mostrar el alcance del
    programa antes de pagar por las otras IAs."""
    pdf_file = request.files.get("pdf")
    if not pdf_file or pdf_file.filename == "":
        flash("Por favor selecciona un archivo PDF.")
        return redirect(url_for("evaluacion.index"))

    token = uuid.uuid4().hex[:8]
    ruta_pdf = UPLOADS_DIR / f"{token}_{secure_filename(pdf_file.filename)}"
    pdf_file.save(ruta_pdf)

    conv = cargar_conversacion_desde_pdf(str(ruta_pdf))
    remitentes = list(conv.remitentes_staff().keys())

    asesor = request.form.get("asesor", "").strip()
    if not asesor:
        if len(remitentes) == 0:
            flash("No se detectó ningún asesor humano en la conversación.")
            return redirect(url_for("evaluacion.index"))
        asesor = " y ".join(remitentes)

    try:
        resultado = cmp_srv.generar_comparacion_demo(
            conv.texto_plano(), asesor,
            bandeja=request.form.get("bandeja", "").strip(), pais=request.form.get("pais", "").strip(),
            id_caso=request.form.get("id_caso", ""), auditor=request.form.get("auditor", ""), token=token,
        )
    except Exception as e:
        log.error("Error al evaluar con Gemini (modo demo): %s", e)
        flash(f"Error al evaluar con Gemini: {e}")
        return redirect(url_for("evaluacion.index"))

    return render_template(
        "comparar_resultado.html", token=token, proveedores_info=PROVEEDORES_INFO,
        modo_demo=True, activo="evaluar", **resultado,
    )


@evaluacion_bp.route("/evaluar-comparar/elegir/<token>/<proveedor>")
def elegir_comparacion(proveedor: str, token: str) -> ResponseReturnValue:
    """El usuario decidió cuál de las 3 evaluaciones (de qué IA) usar como la
    oficial; a partir de aquí sigue el flujo normal (revisar, ajustar, generar)."""
    nombre_proveedor = PROVEEDORES_INFO.get(proveedor, {}).get("nombre", proveedor)
    try:
        resultado = cmp_srv.elegir_resultado_de_comparacion(token, proveedor, nombre_proveedor)
    except FileNotFoundError:
        flash("Esa comparación ya no está disponible, vuelve a evaluar la conversación.")
        return redirect(url_for("evaluacion.index"))
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("evaluacion.index"))

    return _renderizar_revision(resultado)


# -------------------------------------------------------------------- Lote

@evaluacion_bp.route("/evaluar_lote", methods=["POST"])
def evaluar_lote() -> ResponseReturnValue:
    """Procesa varios PDFs en una sola pasada: detecta metadata, evalúa,
    genera documentos, guarda en Drive y registra en el historial — todo
    automático, sin pantalla de revisión manual (pensado para backlog)."""
    archivos = [f for f in request.files.getlist("pdfs") if f and f.filename]
    auditor = request.form.get("auditor", "").strip()

    if not archivos:
        flash("Selecciona al menos un PDF para evaluar en lote.")
        return redirect(url_for("evaluacion.index"))

    rutas_con_nombres = []
    for pdf_file in archivos:
        token = uuid.uuid4().hex[:8]
        ruta_pdf = UPLOADS_DIR / f"{token}_{secure_filename(pdf_file.filename)}"
        pdf_file.save(ruta_pdf)
        rutas_con_nombres.append((ruta_pdf, pdf_file.filename))

    from historial import HISTORIAL_PATH
    from drive_local import respaldar_historial_en_drive
    respaldar = lambda: respaldar_historial_en_drive(str(HISTORIAL_PATH))

    resultados = lote_srv.procesar_lote(rutas_con_nombres, auditor, respaldar_historial=respaldar)
    return render_template("lote_resultado.html", resultados=resultados, activo="evaluar")


@evaluacion_bp.route("/lote")
def ver_lote() -> ResponseReturnValue:
    """Vuelve a mostrar el resultado del último lote procesado (para retomar
    los casos pendientes sin tener que empezar un lote nuevo)."""
    resultados = lote_srv.cargar_estado_lote()
    if not resultados:
        flash("No hay ningún lote reciente para mostrar. Sube PDFs con 'Evaluar en lote' para empezar uno.")
        return redirect(url_for("evaluacion.index"))
    return render_template("lote_resultado.html", resultados=resultados, activo="evaluar")


@evaluacion_bp.route("/evaluar_lote/continuar/<token>")
def continuar_lote(token: str) -> ResponseReturnValue:
    """Retoma un caso 'omitido' del lote (0 asesores detectados), reutilizando
    el PDF ya subido, sin pedirle al usuario que lo suba de nuevo."""
    candidatos = list(UPLOADS_DIR.glob(f"{token}_*"))
    if not candidatos:
        flash("Ese PDF ya no está disponible (puede que ya lo hayas completado, o que el servidor se haya reiniciado). Súbelo de nuevo.")
        return redirect(url_for("evaluacion.index"))

    ruta_pdf = candidatos[0]
    texto_crudo = extraer_texto_pdf(str(ruta_pdf))
    conv = parsear_conversacion(texto_crudo)
    meta = detectar_metadata(conv, texto_crudo, nombre_archivo=ruta_pdf.name)
    asesores = list(conv.remitentes_staff().keys())

    return render_template(
        "elegir_asesor.html", asesores=asesores, token=token, ruta_pdf=str(ruta_pdf),
        bandeja=meta.get("bandeja") or "", id_caso=meta.get("id_caso") or "", pais=meta.get("pais") or "",
        activo="evaluar",
    )
