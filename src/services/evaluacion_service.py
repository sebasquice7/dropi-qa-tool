"""Servicio de evaluación individual de una conversación.

Este módulo NO depende de Flask (nada de `request`, `flash`, `render_template`)
a propósito: la idea es que cualquier otro programa — incluido el sistema
"Monitor" al que se planea integrar esto — pueda llamar estas funciones
directamente, sin tener que pasar por una petición HTTP a este servidor web.

La capa web (blueprints/evaluacion_bp.py) es solo el "traductor": recibe la
petición HTTP, llama a estas funciones, y decide qué página mostrar según el
resultado. Toda la lógica real vive aquí.
"""
import json
from datetime import datetime
from pathlib import Path

from pdf_parser import cargar_conversacion_desde_pdf
from evaluator import evaluar_conversacion
from scoring import calcular_nota, normalizar_evaluacion
from matriz_editor import cargar_matriz_editable
from excel_writer import generar_excel_matriz
from word_writer import generar_informe_word
from drive_local import guardar_en_drive, respaldar_historial_en_drive
from historial import registrar_evaluacion, HISTORIAL_PATH
from calibracion import calcular_calibracion
from alertas import enviar_alerta_critico
from services.lote_service import marcar_completado_en_lote

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"


def construir_metadata(asesor: str, bandeja: str, id_caso: str, pais: str, auditor: str) -> dict:
    """Arma el diccionario de metadata en el formato estándar que usa todo el
    resto del programa (historial, documentos generados, etc.)."""
    return {
        "agente": asesor,
        "bandeja": bandeja or "",
        "id_caso": id_caso or "",
        "pais": pais or "Colombia",
        "evaluado_por": (auditor or "").strip(),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
    }


def guardar_borrador(token: str, metadata: dict, evaluacion: dict, nota: dict) -> Path:
    """Guarda en disco el borrador de la evaluación — incluye una copia de la
    evaluación TAL COMO la dio la IA (antes de que un humano la edite), que
    se usa después para calcular la calibración IA vs. humano.

    Devuelve la ruta del archivo guardado."""
    evaluacion_ia_original = json.loads(json.dumps(evaluacion))  # copia profunda simple
    borrador = {
        "metadata": metadata,
        "evaluacion": evaluacion,
        "evaluacion_ia_original": evaluacion_ia_original,
    }
    ruta_borrador = SALIDAS_DIR / f"borrador_{token}.json"
    with open(ruta_borrador, "w", encoding="utf-8") as f:
        json.dump(borrador, f, ensure_ascii=False, indent=2)
    return ruta_borrador


def cargar_borrador(token: str) -> dict:
    """Carga un borrador guardado previamente. Lanza FileNotFoundError si el
    token no existe (ej. el servidor se reinició, o el link es viejo)."""
    ruta_borrador = SALIDAS_DIR / f"borrador_{token}.json"
    with open(ruta_borrador, encoding="utf-8") as f:
        return json.load(f)


def iniciar_evaluacion(ruta_pdf: str, asesor: str, token: str, bandeja: str = "",
                        pais: str = "", id_caso: str = "", auditor: str = "") -> dict:
    """Corre el flujo completo de evaluar UNA conversación: lee el PDF, llama
    a la IA (con la guía operativa correspondiente si existe una), normaliza
    y calcula la nota, y guarda el borrador — todo en un solo paso, listo
    para mostrarse en pantalla o para que otro sistema lo consuma tal cual.

    Puede lanzar cualquier excepción que venga de leer el PDF o de la IA —
    el que llama a esta función decide cómo mostrar el error (la capa web lo
    convierte en un mensaje flash; otro sistema podría manejarlo distinto).
    """
    conv = cargar_conversacion_desde_pdf(str(ruta_pdf))

    evaluacion = evaluar_conversacion(conv.texto_plano(), asesor, pais=pais, bandeja=bandeja)
    evaluacion = normalizar_evaluacion(evaluacion)
    nota = calcular_nota(evaluacion)

    metadata = construir_metadata(asesor, bandeja, id_caso, pais, auditor)
    guardar_borrador(token, metadata, evaluacion, nota)

    return {"token": token, "metadata": metadata, "evaluacion": evaluacion, "nota": nota}


def criticos_activados_de(evaluacion: dict) -> set:
    """Ids de los ítems críticos marcados como ocurridos (ocurrio == 'Si'),
    útil para resaltar en la pantalla de revisión."""
    return {
        cid for cid, v in evaluacion.get("items_criticos", {}).items()
        if str(v.get("ocurrio", "No")).strip().lower() == "si"
    }


def datos_para_revision(token: str, metadata: dict, evaluacion: dict, nota: dict) -> dict:
    """Empaqueta todo lo que necesita la pantalla de 'revisar y ajustar' —
    separado de _guardar_borrador_y_revisar de antes, esta función ya no
    sabe nada de Flask ni de templates."""
    matriz = cargar_matriz_editable()
    return {
        "token": token,
        "metadata": metadata,
        "evaluacion": evaluacion,
        "nota": nota,
        "categorias": matriz["categorias"],
        "items_criticos": matriz["items_criticos"],
        "criticos_activados": criticos_activados_de(evaluacion),
    }


def aplicar_ajustes_y_confirmar(token: str, ajustes: dict) -> dict:
    """Toma el borrador guardado, le aplica los ajustes que hizo el auditor al
    revisar (puntajes, justificaciones, críticos, positivo/mejora, resumen),
    genera el Excel y el Word finales, guarda en Drive, calcula la
    calibración IA vs. humano, registra en el historial, envía la alerta si
    hay un ítem crítico, y marca el caso como completado si venía de un lote.

    `ajustes` es un dict plano (no depende de Flask):
      {
        "puntajes": {item_id: float},
        "justificaciones": {item_id: str},
        "criticos_ocurrieron": {critico_id: bool},
        "criticos_justificaciones": {critico_id: str},
        "lo_positivo": [str, ...],
        "oportunidades_mejora": [str, ...],
        "resumen_caso": str,
      }

    Devuelve todo lo que necesita la pantalla final de resultado.
    """
    borrador = cargar_borrador(token)
    metadata = borrador["metadata"]
    evaluacion = borrador["evaluacion"]
    matriz = cargar_matriz_editable()

    for iid, puntaje in ajustes.get("puntajes", {}).items():
        if iid in evaluacion.get("items", {}):
            evaluacion["items"][iid]["puntaje"] = puntaje
            evaluacion["items"][iid]["justificacion"] = ajustes.get("justificaciones", {}).get(iid, "")

    evaluacion.setdefault("items_criticos", {})
    for cid, ocurrio in ajustes.get("criticos_ocurrieron", {}).items():
        evaluacion["items_criticos"][cid] = {
            "ocurrio": "Si" if ocurrio else "No",
            "justificacion": ajustes.get("criticos_justificaciones", {}).get(cid, ""),
        }

    evaluacion["lo_positivo"] = ajustes.get("lo_positivo", [])
    evaluacion["oportunidades_mejora"] = ajustes.get("oportunidades_mejora", [])
    evaluacion["resumen_caso"] = ajustes.get("resumen_caso", "")

    evaluacion = normalizar_evaluacion(evaluacion)
    nota = calcular_nota(evaluacion)

    sufijo = metadata.get("id_caso") or token
    ruta_excel = SALIDAS_DIR / f"Matriz_{sufijo}.xlsx"
    ruta_word = SALIDAS_DIR / f"Informe_{sufijo}.docx"
    generar_excel_matriz(evaluacion, metadata, str(ruta_excel))
    generar_informe_word(evaluacion, metadata, nota, str(ruta_word))

    drive_resultado = guardar_en_drive(
        str(ruta_excel), str(ruta_word), metadata.get("agente", ""), metadata.get("id_caso", ""),
        pais=metadata.get("pais", ""),
    )

    calibracion = None
    evaluacion_ia_original = borrador.get("evaluacion_ia_original")
    if evaluacion_ia_original:
        calibracion = calcular_calibracion(evaluacion_ia_original, evaluacion, matriz)

    registrar_evaluacion(metadata, evaluacion, nota, calibracion=calibracion)
    respaldar_historial_en_drive(str(HISTORIAL_PATH))

    alerta_resultado = None
    if nota.get("critico_activado"):
        alerta_resultado = enviar_alerta_critico(metadata, nota)

    viene_de_lote = marcar_completado_en_lote(token, {
        "archivo": metadata.get("id_caso") or token,
        "estado": "ok",
        "asesor": metadata.get("agente", ""),
        "bandeja": metadata.get("bandeja", ""),
        "id_caso": metadata.get("id_caso", ""),
        "nota_final": nota["nota_final"],
        "critico": nota.get("critico_activado"),
        "excel_nombre": ruta_excel.name,
        "word_nombre": ruta_word.name,
        "drive_ok": drive_resultado.get("ok", False),
        "bandeja_es_sugerencia": False,
        "duplicado": None,
        "token": token,
    })

    return {
        "metadata": metadata,
        "nota": nota,
        "excel_nombre": ruta_excel.name,
        "word_nombre": ruta_word.name,
        "drive_resultado": drive_resultado,
        "viene_de_lote": viene_de_lote,
        "alerta_resultado": alerta_resultado,
    }
