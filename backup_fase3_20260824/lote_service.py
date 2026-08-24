"""Servicio de evaluación en lote: procesa varios PDFs de una sola pasada
(detecta metadata, evalúa con IA, genera documentos, guarda en Drive y
registra en el historial), sin pantalla de revisión manual — pensado para
backlog, no para el caso puntual donde se quiere ajustar cada puntaje.

Igual que evaluacion_service.py, este módulo no depende de Flask.
"""
import json
import uuid
from typing import Callable, Optional
from datetime import datetime
from pathlib import Path

from pdf_parser import extraer_texto_pdf, parsear_conversacion, detectar_metadata
from evaluator import evaluar_conversacion
from scoring import calcular_nota, normalizar_evaluacion
from excel_writer import generar_excel_matriz
from word_writer import generar_informe_word
from drive_local import guardar_en_drive
from historial import registrar_evaluacion, buscar_duplicado
from alertas import enviar_alerta_critico
from logging_config import obtener_logger

log = obtener_logger("lote_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALIDAS_DIR = BASE_DIR / "salidas"
LOTE_ESTADO_PATH = BASE_DIR / "ultimo_lote.json"


def guardar_estado_lote(resultados: list) -> None:
    """Guarda el resultado del último lote procesado, para poder volver a
    verlo (incluso después de navegar a otras pantallas) y completar los
    pendientes."""
    try:
        with open(LOTE_ESTADO_PATH, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        log.warning("No se pudo guardar el estado del lote: %s", e)


def cargar_estado_lote() -> Optional[list]:
    """Lee el estado del último lote procesado, o None si no hay ninguno guardado."""
    if not LOTE_ESTADO_PATH.exists():
        return None
    try:
        with open(LOTE_ESTADO_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def marcar_completado_en_lote(token: str, resultado_actualizado: dict) -> bool:
    """Cuando se completa (desde la pantalla individual) un caso que venía de
    un lote pendiente, actualiza esa entrada en el estado guardado del lote,
    para que al volver a /lote ya no aparezca como pendiente."""
    resultados = cargar_estado_lote()
    if not resultados:
        return False
    cambiado = False
    for r in resultados:
        if r.get("token") == token:
            r.clear()
            r.update(resultado_actualizado)
            cambiado = True
            break
    if cambiado:
        guardar_estado_lote(resultados)
    return cambiado


def procesar_un_pdf_de_lote(ruta_pdf: Path, nombre_original: str, auditor: str) -> tuple:
    """Procesa UN PDF dentro de un lote. Devuelve (resultado: dict,
    conservar_pdf: bool) — conservar_pdf es True solo para los 'omitidos'
    (sin asesor detectado), que se dejan listos para completar manualmente."""
    token = uuid.uuid4().hex[:8]

    texto_crudo = extraer_texto_pdf(str(ruta_pdf))
    conv = parsear_conversacion(texto_crudo)
    meta_detectada = detectar_metadata(conv, texto_crudo, nombre_archivo=nombre_original)
    asesores = list(conv.remitentes_staff().keys())

    if len(asesores) == 0:
        resultado = {
            "archivo": nombre_original,
            "estado": "omitido",
            "motivo": "No se detectó ningún asesor humano automáticamente.",
            "token": token,
            "asesores_detectados": asesores,
            "bandeja_detectada": meta_detectada.get("bandeja") or "",
            "id_caso_detectado": meta_detectada.get("id_caso") or "",
            "pais_detectado": meta_detectada.get("pais") or "",
        }
        return resultado, True

    asesor = " y ".join(asesores)  # 1 solo nombre queda igual; 2+ se juntan y se evalúan sin pausas
    id_detectado = meta_detectada.get("id_caso") or token
    duplicado = buscar_duplicado(id_detectado)

    evaluacion = evaluar_conversacion(
        conv.texto_plano(), asesor,
        pais=meta_detectada.get("pais") or "", bandeja=meta_detectada.get("bandeja") or "",
    )
    evaluacion = normalizar_evaluacion(evaluacion)
    nota = calcular_nota(evaluacion)

    metadata = {
        "agente": asesor,
        "bandeja": meta_detectada.get("bandeja") or "",
        "id_caso": id_detectado,
        "pais": meta_detectada.get("pais") or "",
        "evaluado_por": auditor,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
    }

    sufijo = metadata["id_caso"]
    ruta_excel = SALIDAS_DIR / f"Matriz_{sufijo}.xlsx"
    ruta_word = SALIDAS_DIR / f"Informe_{sufijo}.docx"
    generar_excel_matriz(evaluacion, metadata, str(ruta_excel))
    generar_informe_word(evaluacion, metadata, nota, str(ruta_word))

    drive_resultado = guardar_en_drive(
        str(ruta_excel), str(ruta_word), metadata["agente"], metadata["id_caso"], pais=metadata["pais"]
    )
    registrar_evaluacion(metadata, evaluacion, nota)
    if nota.get("critico_activado"):
        enviar_alerta_critico(metadata, nota)

    resultado = {
        "archivo": nombre_original,
        "estado": "ok",
        "asesor": asesor,
        "bandeja": metadata["bandeja"],
        "id_caso": metadata["id_caso"],
        "pais": metadata["pais"],
        "nota_final": nota["nota_final"],
        "critico": nota.get("critico_activado"),
        "excel_nombre": ruta_excel.name,
        "word_nombre": ruta_word.name,
        "drive_ok": drive_resultado.get("ok", False),
        "bandeja_es_sugerencia": meta_detectada.get("bandeja_es_sugerencia", False),
        "pais_es_sugerencia": meta_detectada.get("pais_es_sugerencia", False),
        "duplicado": duplicado,
    }
    return resultado, False


def procesar_lote(rutas_con_nombres: list, auditor: str, respaldar_historial: Optional[Callable[[], None]] = None) -> list:
    """rutas_con_nombres: lista de tuplas (ruta_pdf: Path, nombre_original: str).
    Procesa cada uno y devuelve la lista de resultados, en el mismo orden en
    que se recibieron.

    `respaldar_historial`, si se pasa, es una función que se llama tras cada
    evaluación exitosa — se inyecta así (en vez de importarla directo) para
    que este servicio no dependa de la lógica específica de respaldo en Drive
    de la app web; quien lo use decide si quiere ese efecto secundario."""
    resultados = []

    for ruta_pdf, nombre_original in rutas_con_nombres:
        conservar_pdf = False
        try:
            resultado, conservar_pdf = procesar_un_pdf_de_lote(ruta_pdf, nombre_original, auditor)
            resultados.append(resultado)
            if resultado["estado"] == "ok" and respaldar_historial:
                respaldar_historial()
        except Exception as e:
            log.error("Error procesando '%s' en lote: %s", nombre_original, e)
            resultados.append({"archivo": nombre_original, "estado": "error", "motivo": str(e)})
        finally:
            if not conservar_pdf:
                try:
                    ruta_pdf.unlink(missing_ok=True)
                except Exception:
                    pass

    guardar_estado_lote(resultados)
    return resultados
