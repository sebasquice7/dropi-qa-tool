"""
Evalúa una conversación de Intercom contra la matriz de calidad + política de
comunicación de Dropi, usando la API GRATUITA de Google Gemini.

Requiere la variable de entorno GEMINI_API_KEY (gratis, sin tarjeta, en
https://aistudio.google.com/apikey).

También soporta Anthropic Claude como alternativa de pago (ver evaluar_conversacion,
parámetro `proveedor`), por si en el futuro decides usarlo.
"""
import json
import sys
import time
from pathlib import Path

from config import config
from logging_config import obtener_logger

log = obtener_logger("evaluator")

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
POLITICA_PATH = BASE_DIR / "config" / "politica_comunicacion.md"
POLITICA_SLA_PATH = BASE_DIR / "config" / "politica_sla.md"

# Cadena de modelos a intentar, en orden de preferencia. gemini-2.5-flash-lite va
# primero porque tiene la cuota gratuita más generosa (hasta 1.000-1.500/día). Si
# Google descontinúa o renombra alguno de estos con el tiempo (ya ha pasado varias
# veces), el programa prueba automáticamente el siguiente de la lista sin que haga
# falta tocar el código — puedes agregar/quitar nombres aquí si hace falta.
GEMINI_MODELOS_A_INTENTAR = [
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
]
ANTHROPIC_MODEL_DEFAULT = "claude-sonnet-4-6"

# Igual que con Gemini: cadena de modelos de OpenAI a intentar en orden, para no
# depender de un solo nombre que Google... digo, OpenAI, puede renombrar o
# descontinuar con el tiempo (les pasa con mucha frecuencia).
OPENAI_MODELOS_A_INTENTAR = [
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.1",
    "gpt-4o",
    "gpt-4o-mini",
]


def _cargar_matriz() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        return json.load(f)


def _cargar_politica() -> str:
    with open(POLITICA_PATH, encoding="utf-8") as f:
        return f.read()


def _cargar_politica_sla() -> str:
    if not POLITICA_SLA_PATH.exists():
        return ""
    with open(POLITICA_SLA_PATH, encoding="utf-8") as f:
        return f.read()


def _construir_prompt(conversacion_texto: str, asesor: str, matriz: dict, politica: str, politica_sla: str = "", guia_relevante: dict = None, contexto_gali: str = "", texto_notas_internas: str = None) -> str:
    items_desc = []
    for cat in matriz["categorias"]:
        items_desc.append(f"\n### {cat['nombre']} (peso total: {cat['peso_categoria']*100:.0f}%)")
        for it in cat["items"]:
            items_desc.append(
                f"- id: \"{it['id']}\" | \"{it['nombre']}\" | peso máximo: {it['peso']*100:.0f}%\n"
                f"  Qué se evalúa: {it['que_evalua']}\n"
                f"  Qué tener en cuenta: {it['que_tener_en_cuenta']}"
            )

    criticos_desc = "\n".join(
        f"- id: \"{c['id']}\" | \"{c['nombre']}\"" for c in matriz["items_criticos"]
    )

    items_json_ids = [it["id"] for cat in matriz["categorias"] for it in cat["items"]]
    criticos_ids = [c["id"] for c in matriz["items_criticos"]]

    formato_json = {
        "resumen_caso": "2-3 frases que describan el caso desde la perspectiva de calidad: tipo de solicitud, complejidad del caso, expectativa del cliente, y resultado final de la gestión (resuelto, parcial, no resuelto). No solo 'qué pasó', sino 'qué tan bien se manejó y por qué'.",
        "items": {
            iid: {"puntaje": "número entre 0 y el peso máximo del ítem", "justificacion": "2-3 frases con análisis de calidad: qué hizo o dejó de hacer el asesor, qué evidencia lo respalda (cita textual breve o timestamp), y qué impacto tuvo eso en la experiencia del cliente. No describas el criterio del ítem — analiza la gestión real."}
            for iid in items_json_ids
        },
        "items_criticos": {
            cid: {"ocurrio": "Si o No", "justificacion": "SIEMPRE explica en 1-2 frases citando la evidencia exacta de la conversación. Si marcas 'Si', cita el mensaje o acción específica. Si marcas 'No', explica qué evidencia te permite descartarlo con confianza."}
            for cid in criticos_ids
        },
        "lo_positivo": ["3 a 6 puntos. Formato: 'Comportamiento replicable. Evidencia concreta y por qué es valioso para el cliente/operación.' Enfócate en COMPORTAMIENTOS que vale la pena reforzar en coaching, no en cumplimiento básico que se da por sentado (saludar, despedirse). El concepto breve termina en PUNTO, no en dos puntos ':'. NO uses asteriscos ni markdown."],
        "oportunidades_mejora": ["1 a 5 puntos. Formato: 'Brecha detectada. Qué pasó exactamente (con evidencia), qué debió pasar según la documentación, y qué efecto tuvo en el cliente.' Piensa como coach: cada punto debe ser accionable — algo que el asesor pueda practicar o cambiar en su siguiente interacción. NO uses asteriscos ni markdown."],
    }

    prompt = f"""Eres un analista senior de calidad y experiencia del cliente (CX) para Dropi, plataforma de dropshipping. Tu rol NO es el de un auditor que marca casillas — eres un profesional de calidad que diagnostica la gestión del asesor con profundidad analítica, detecta patrones de comportamiento, identifica causa raíz de los problemas, y produce hallazgos que sirvan directamente para coaching.

Tu mentalidad al evaluar:
- Pregúntate siempre "¿por qué pasó esto?" antes de calificar. Un error puede ser falta de conocimiento, falta de proceso, descuido, o una limitación del sistema — cada uno requiere una acción de mejora distinta.
- Evalúa el IMPACTO en el cliente, no solo si se siguió el paso. Un asesor puede seguir todos los pasos del proceso y aun así dejar al cliente insatisfecho (ej. responder correctamente pero sin empatía ante una queja legítima). También puede saltarse un paso menor sin impacto real.
- Distingue entre errores de HABILIDAD (el asesor no sabe cómo hacerlo) y errores de EJECUCIÓN (sabe pero no lo hizo en este caso). Esto cambia completamente la recomendación de coaching.
- "Lo positivo" no es una lista de cosas que no salieron mal — son comportamientos que demuestran competencia real y que vale la pena reforzar. Si el asesor solo hizo lo mínimo esperado, di eso con respeto, no lo infles.
- "Oportunidades de mejora" no es una lista de fallas — son brechas entre lo que se hizo y lo que la documentación/política exige, con una línea clara hacia qué practicar. Si no hay brechas significativas, di eso honestamente.

Tu tarea: evaluar la gestión del asesor **{asesor}** en la conversación de abajo, aplicando ESTRICTAMENTE la matriz de calidad, las políticas y la documentación operativa de la empresa.

=== POLÍTICA DE COMUNICACIÓN Y REDACCIÓN ===
{politica}

{"=== POLÍTICA DE TIEMPOS DE RESPUESTA (SLA) ===" + chr(10) + politica_sla if politica_sla else ""}

{("=== GUÍA OPERATIVA DE REFERENCIA PARA ESTE CASO (\"" + guia_relevante["titulo"] + "\") ===" + chr(10) + "Esta es la guía oficial del proceso que aplica a este caso específico. Úsala como referencia real para el ítem \"precision_tecnica_fondo\" — compara los pasos técnicos que dio el asesor contra los pasos documentados aquí. Si el asesor se desvió de la guía, analiza si fue un error o una adaptación razonable al contexto del caso." + chr(10) + chr(10) + guia_relevante["texto"]) if guia_relevante else ""}

{("=== BASE DE CONOCIMIENTO DE GALI (referencia oficial) ===" + chr(10) + contexto_gali) if contexto_gali else "=== BASE DE CONOCIMIENTO DE GALI: no se encontró ninguna pregunta/respuesta oficial que aplique a lo que Gali dijo en este caso. Los ítems sobre Gali deben calificarse según el criterio general (no penalizar por falta de una referencia específica). ==="}

{("=== NOTAS INTERNAS DEL EQUIPO (fuente confirmada, aisladas del resto de la conversación) ===" + chr(10) + "Estas líneas SÍ están confirmadas como notas internas (no visibles al cliente) — evalúa el ítem \"notas_internas_tipificacion\" con confianza total, usando SOLO este texto como evidencia." + chr(10) + chr(10) + texto_notas_internas) if texto_notas_internas else "=== NOTAS INTERNAS DEL EQUIPO: no se pudo aislar con certeza cuáles líneas de la conversación son notas internas y cuáles son mensajes al cliente (limitación del formato PDF exportado, no de este caso en particular). Para el ítem \"notas_internas_tipificacion\", sé CONSERVADOR: solo penaliza si encuentras evidencia muy clara e inequívoca dentro de la conversación completa (por ejemplo, un comentario que menciona explícitamente ser una nota interna o de seguimiento). Ante la duda genuina, no penalices — es preferible no calificar con certeza baja que penalizar por una mala interpretación del formato. ==="}

=== MATRIZ DE CALIDAD (ítems y pesos) ===
{"".join(items_desc)}

=== ÍTEMS CRÍTICOS (si CUALQUIERA ocurre, la nota final es 0%) ===
{criticos_desc}

=== CONVERSACIÓN A EVALUAR ===
Los mensajes marcados [STAFF] son del equipo de Dropi (bots o asesores). Los marcados [CLIENTE] son del dropshipper/proveedor.
Evalúa ÚNICAMENTE la gestión del asesor humano "{asesor}", no la del bot Gali (que solo enruta al inicio).

{conversacion_texto}

=== INSTRUCCIONES DE SALIDA ===
Responde ÚNICAMENTE con un JSON válido (sin texto adicional, sin markdown, sin ```), con esta estructura exacta:

{json.dumps(formato_json, ensure_ascii=False, indent=2)}

Reglas de análisis:
1. PUNTAJE GRANULAR: el "puntaje" de cada ítem debe ser un número entre 0 y su peso máximo. Usa TODO el rango disponible (ej. si el peso máximo es 0.10, puedes dar 0.10, 0.08, 0.06, 0.04, 0.02, 0 según el nivel de cumplimiento real). Evita calificar solo en 0%, 50% o 100% del peso — la granularidad intermedia refleja mejor la realidad de un caso (ej. "hizo la gestión técnica correcta pero no adjuntó la evidencia" merece más que 50% pero menos que 100%).
2. ÍTEMS QUE NO APLICAN: si un ítem no aplica al caso por contexto (ej. no hubo interacción con Gali porque el cliente llegó directo, o no hubo necesidad de escalar a IT porque no hubo falla de sistema), otorga el puntaje máximo — la ausencia de una situación no es una falla del asesor.
3. JUSTIFICACIONES CON PROFUNDIDAD ANALÍTICA: cada justificación debe responder tres preguntas: (a) ¿qué hizo o dejó de hacer el asesor? (cita el mensaje o timestamp exacto), (b) ¿qué dice la documentación/política que debió pasar?, (c) ¿qué impacto tuvo esto en la experiencia del cliente? Una justificación que no menciona ningún dato concreto de la conversación (solo una opinión general como "buena gestión" o "podría mejorar") NO es aceptable — si no hay evidencia que citar, dilo explícitamente.
4. ÍTEMS CRÍTICOS — UMBRAL ALTO: marcar "Si" un ítem crítico lleva la nota a 0%, así que exige evidencia INEQUÍVOCA antes de activarlo. Si hay una zona gris (ej. el cierre fue un poco apresurado pero sí hubo gestión previa), refleja eso bajando el puntaje del ítem regular correspondiente, no activando el crítico. Pero si la evidencia es clara, no dudes en activarlo — ser conservador no es ser permisivo.
5. LO POSITIVO — ENFOQUE EN COACHING: identifica comportamientos que demuestran competencia profesional genuina (no lo mínimo esperado). Pregúntate: "¿qué hizo este asesor que yo quisiera que todos los asesores replicaran?" Si no hay nada destacable más allá del cumplimiento básico, sé honesto — di que cumplió lo esperado sin inventar puntos fuertes artificiales.
6. OPORTUNIDADES DE MEJORA — CAUSA RAÍZ Y ACCIÓN: cada punto debe ir más allá de "no hizo X". Analiza la CAUSA PROBABLE (¿no sabía?, ¿se le pasó?, ¿el sistema no le dio la información?) y sugiere una ACCIÓN CONCRETA que el asesor pueda practicar. Ej. malo: "No confirmó satisfacción antes de cerrar." Ej. bueno: "Cierre sin verificación. El asesor anunció el cierre del caso en el mismo mensaje donde daba la explicación (02:41 PM), sin esperar confirmación del cliente. Según el protocolo de cierre (ítem 4.1), debió validar primero que el cliente revisara la solución. Esto sugiere un hábito de cierre automático que se puede corregir practicando la secuencia: solución → pausa → pregunta de conformidad → despedida."
7. No inventes información que no esté en la conversación. Si un dato no se puede verificar desde el chat (ej. si dejó nota interna o no), dilo.
8. FORMATO DE TEXTO: en NINGÚN campo uses asteriscos (**) ni ningún otro marcado tipo Markdown. Escribe texto plano; el sistema ya aplica formato visual automáticamente.
9. TIEMPOS Y HORARIO LABORAL: al evaluar "sla_tiempo_respuesta_concentracion", compara los tiempos reales de la conversación (usa los timestamps de cada mensaje) contra los tiempos máximos de la política de SLA para el proceso/bandeja correspondiente. Los huecos de tiempo que caen FUERA del horario laboral (lunes a viernes 8am-5pm, sábados/lunes festivos 8am-12m) NO cuentan como demora del asesor — un mensaje del cliente a las 6pm que se responde a las 8am del siguiente día hábil está DENTRO del SLA, no es una falla.
10. CIERRE VÁLIDO vs. ABANDONO ("cierre_prematuro_abandono"): usa la regla fija de "Cierre por inactividad del cliente" de la política de SLA (arriba): el asesor puede cerrar válidamente tras 4 horas de tiempo LABORAL de silencio del cliente después de una gestión clara, siempre que haya avisado antes de cerrar. Marca este ítem crítico como "Si" ÚNICAMENTE si el asesor cierra sin haber dado una gestión clara, sin avisar antes de cerrar, o cierra con MENOS de esas 4 horas de inactividad sin justificación. NO lo marques como "Si" si el asesor gestionó el caso apropiadamente, esperó el tiempo debido, y avisó antes de cerrar — eso es un cierre válido por inactividad del cliente, marca "No". Si el cierre fue algo prematuro pero no un abandono claro, refléjalo bajando el puntaje de "sla_tiempo_respuesta_concentracion" en vez de activar el crítico.
"""
    return prompt


def _limpiar_json(texto_respuesta: str) -> str:
    texto_respuesta = texto_respuesta.strip()
    if texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta.strip("`")
        if texto_respuesta.startswith("json"):
            texto_respuesta = texto_respuesta[4:]
        texto_respuesta = texto_respuesta.strip()
    return texto_respuesta


def _llamar_gemini(prompt: str, api_key: str, modelo_preferido: str = None) -> tuple:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError(
            "Falta la librería google-genai. Instálala con: pip install google-genai --break-system-packages"
        )

    client = genai.Client(api_key=api_key)
    # Temperatura en 0 (no 0.1): para una herramienta de AUDITORÍA, el
    # objetivo es que la misma conversación dé el mismo resultado cada vez
    # que se reevalúe — no que "suene natural" o creativo. 0 empuja al
    # modelo a la respuesta de mayor probabilidad (decodificación greedy) en
    # vez de muestrear entre varias, lo que reduce la variabilidad al mínimo
    # que la API permite (no elimina el 100% — Google no garantiza
    # determinismo absoluto incluso en temperature=0 por cómo procesa las
    # solicitudes en paralelo — pero es sensiblemente más estable que 0.1).
    # max_output_tokens alto: el JSON completo (22 ítems + justificaciones +
    # lo_positivo + oportunidades) puede ser largo; sin este límite explícito,
    # algunos modelos lo cortan a la mitad y el JSON queda inválido.
    config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=8192)

    # Si el .env fija un modelo específico (GEMINI_MODEL), se prueba primero;
    # después la cadena de respaldo normal.
    modelos = GEMINI_MODELOS_A_INTENTAR
    if modelo_preferido and modelo_preferido not in modelos:
        modelos = [modelo_preferido] + modelos

    ultimo_error = None
    for modelo in modelos:
        for intento in range(2):  # pocos reintentos por modelo: si falla feo, mejor saltar al siguiente
            try:
                response = client.models.generate_content(model=modelo, contents=prompt, config=config)
                texto = response.text

                # Validar que el JSON esté completo (no cortado a la mitad por límite
                # de longitud) ANTES de darlo por bueno; si está incompleto, se trata
                # como error transitorio y se reintenta, en vez de devolver texto roto.
                try:
                    json.loads(_limpiar_json(texto))
                except json.JSONDecodeError:
                    raise RuntimeError("La respuesta llegó incompleta/cortada (JSON inválido)")

                # Se devuelve también qué modelo respondió DE VERDAD — si por cupo
                # agotado el programa saltó de "gemini-2.5-flash-lite" a otro modelo
                # de la cadena a mitad de una sesión de evaluaciones, dos corridas
                # de la MISMA conversación pueden quedar procesadas por modelos
                # distintos (y por lo tanto con resultados distintos) sin que se
                # note — con este dato visible en el resultado, eso deja de ser
                # invisible.
                return texto, modelo
            except Exception as e:
                ultimo_error = e
                texto_error = str(e)

                # Modelo descontinuado/renombrado, o cupo DIARIO agotado: no vale la
                # pena reintentar el mismo modelo, saltar directo al siguiente.
                if (
                    "PerDay" in texto_error
                    or "GenerateRequestsPerDay" in texto_error
                    or "NOT_FOUND" in texto_error
                    or "no longer available" in texto_error
                ):
                    log.info("'%s' no disponible ahora mismo, probando el siguiente modelo...", modelo)
                    break

                # Error transitorio (503, límite por minuto, respuesta cortada, etc.):
                # reintentar un poco antes de pasar al siguiente modelo.
                espera = 5 * (intento + 1)
                log.warning("Límite/error temporal en '%s', reintentando en %ss... (%s)", modelo, espera, e)
                time.sleep(espera)

    raise RuntimeError(
        f"No se pudo obtener respuesta de Gemini con ninguno de los modelos disponibles "
        f"({', '.join(modelos)}). Último error: {ultimo_error}"
    )


def _llamar_anthropic(prompt: str, api_key: str, modelo: str) -> tuple:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "Falta la librería anthropic. Instálala con: pip install anthropic --break-system-packages"
        )
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=modelo,
        max_tokens=4000,
        # BUG corregido (agosto 2026): esta llamada no traía 'temperature', así
        # que usaba el valor por defecto de la API (1.0 — bastante variable).
        # Se fija en 0 por la misma razón que en Gemini/OpenAI: en auditoría,
        # la misma conversación debe dar el mismo resultado al reevaluarla.
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    return texto, modelo


def _llamar_openai(prompt: str, api_key: str, modelo_preferido: str = None) -> tuple:
    try:
        import openai
    except ImportError:
        raise RuntimeError(
            "Falta la librería openai. Instálala con: pip install openai --break-system-packages"
        )

    client = openai.OpenAI(api_key=api_key)

    modelos = OPENAI_MODELOS_A_INTENTAR
    if modelo_preferido and modelo_preferido not in modelos:
        modelos = [modelo_preferido] + modelos

    ultimo_error = None
    for modelo in modelos:
        for intento in range(2):
            try:
                response = client.chat.completions.create(
                    model=modelo,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=8192,
                    response_format={"type": "json_object"},
                )
                texto = response.choices[0].message.content

                try:
                    json.loads(_limpiar_json(texto))
                except json.JSONDecodeError:
                    raise RuntimeError("La respuesta llegó incompleta/cortada (JSON inválido)")

                return texto, modelo
            except Exception as e:
                ultimo_error = e
                texto_error = str(e)

                if "model_not_found" in texto_error or "does not exist" in texto_error or "404" in texto_error:
                    log.info("'%s' no disponible ahora mismo, probando el siguiente modelo...", modelo)
                    break

                espera = 5 * (intento + 1)
                log.warning("Límite/error temporal en '%s' (OpenAI), reintentando en %ss... (%s)", modelo, espera, e)
                time.sleep(espera)

    raise RuntimeError(
        f"No se pudo obtener respuesta de OpenAI con ninguno de los modelos disponibles "
        f"({', '.join(modelos)}). Último error: {ultimo_error}"
    )


def evaluar_conversacion(
    conversacion_texto: str,
    asesor: str,
    api_key: str = None,
    proveedor: str = None,
    pais: str = None,
    bandeja: str = None,
    texto_gali: str = None,
    texto_notas_internas: str = None,
) -> dict:
    """
    proveedor: "gemini" (gratis, por defecto) o "anthropic" (de pago).
    Si no se especifica, se autodetecta según qué variable de entorno esté configurada,
    priorizando GEMINI_API_KEY (gratis).

    pais/bandeja: si se pasan, el programa busca automáticamente la guía
    operativa correspondiente (ver guias.py) y se la da a la IA como
    contexto adicional para evaluar el ítem "precision_tecnica_fondo". Si no
    hay ninguna guía que coincida con esa bandeja, simplemente no se agrega
    contexto adicional — no penaliza al asesor.

    texto_gali: si se pasa (los mensajes que envió Gali en esta conversación),
    el programa busca en la base de conocimiento de Gali las preguntas/
    respuestas oficiales relevantes, y se las da a la IA como referencia para
    evaluar si Gali dio información correcta.

    texto_notas_internas: ENGANCHE PARA LA API DE INTERCOM (todavía no
    conectada). Hoy, leyendo desde PDF, no hay forma de aislar con certeza
    cuáles líneas de la conversación fueron notas internas del equipo (no
    visibles al cliente) — en la interfaz de Intercom se ven en una caja
    amarilla distinta, pero esa marca se pierde al exportar a PDF, todo
    queda como texto plano igual de ambiguo. La API de Intercom sí expone
    las notas como un campo separado y confirmado. Cuando ese dato llegue
    (vía este parámetro), el ítem "Claridad y argumentación en Notas
    Internas" se evalúa con evidencia real y aislada, con confianza total —
    sin este parámetro, se evalúa igual que siempre, pero con una instrucción
    explícita de ser conservador, ya que no hay certeza de qué es nota y qué
    es mensaje al cliente.
    """
    proveedor = proveedor or config.proveedor_forzado
    if not proveedor:
        if config.gemini_api_key:
            proveedor = "gemini"
        elif config.anthropic_api_key:
            proveedor = "anthropic"
        else:
            proveedor = "gemini"  # por defecto, ya que es la opción gratuita

    matriz = _cargar_matriz()
    politica = _cargar_politica()
    politica_sla = _cargar_politica_sla()

    guia_relevante = None
    if pais and bandeja:
        try:
            from guias import encontrar_guia_relevante
            guia_relevante = encontrar_guia_relevante(pais, bandeja)
        except Exception as e:
            log.warning("No se pudo buscar la guía operativa: %s", e)

    contexto_gali = ""
    if texto_gali and pais:
        try:
            from faqs_gali_buscador import contexto_faqs_gali
            contexto_gali = contexto_faqs_gali(texto_gali, pais)
        except Exception as e:
            log.warning("No se pudo buscar en la base de conocimiento de Gali: %s", e)

    prompt = _construir_prompt(conversacion_texto, asesor, matriz, politica, politica_sla, guia_relevante, contexto_gali, texto_notas_internas)

    if proveedor == "gemini":
        api_key = api_key or config.gemini_api_key
        if not api_key:
            raise RuntimeError(
                "No se encontró GEMINI_API_KEY. Consíguela gratis en https://aistudio.google.com/apikey "
                "y agrégala a tu archivo .env"
            )
        modelo_preferido = config.gemini_model or None  # si no está, usa la cadena de respaldo
        texto_respuesta, modelo_usado = _llamar_gemini(prompt, api_key, modelo_preferido)

    elif proveedor == "anthropic":
        api_key = api_key or config.anthropic_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una ANTHROPIC_API_KEY real (todavía tiene el valor de ejemplo).")
        modelo = config.anthropic_model or ANTHROPIC_MODEL_DEFAULT
        texto_respuesta, modelo_usado = _llamar_anthropic(prompt, api_key, modelo)

    elif proveedor == "openai":
        api_key = api_key or config.openai_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una OPENAI_API_KEY real (todavía tiene el valor de ejemplo).")
        modelo_preferido = config.openai_model or None
        texto_respuesta, modelo_usado = _llamar_openai(prompt, api_key, modelo_preferido)

    else:
        raise RuntimeError(f"Proveedor desconocido: {proveedor}. Usa 'gemini', 'anthropic' u 'openai'.")

    texto_limpio = _limpiar_json(texto_respuesta)
    try:
        resultado = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"El modelo ({proveedor}) no devolvió un JSON válido. Error: {e}\n\n"
            f"Respuesta cruda (primeros 2000 caracteres):\n{texto_limpio[:2000]}"
        )

    try:
        from uso_ia import registrar_uso
        registrar_uso(proveedor, len(prompt), len(texto_limpio), bool(guia_relevante), modelo=modelo_usado)
    except Exception:
        pass  # nunca romper la evaluación real por esto

    # Se deja visible qué guía se usó (o que no había ninguna aplicable) para
    # que el auditor lo vea directamente en la pantalla de revisión, sin tener
    # que inferirlo leyendo la justificación del ítem "precision_tecnica_fondo".
    resultado["guia_utilizada"] = (
        {"encontrada": True, "titulo": guia_relevante["titulo"]}
        if guia_relevante
        else {"encontrada": False, "titulo": None}
    )

    # Se deja visible con qué proveedor/modelo se generó esta evaluación —
    # antes esto no se registraba en ningún lado, así que si dos corridas de
    # la MISMA conversación caían en modelos distintos de la cadena de
    # respaldo (ej. por cupo agotado a mitad de una sesión de evaluaciones),
    # no había forma de saber por qué daban resultados distintos.
    resultado["proveedor_usado"] = proveedor
    resultado["modelo_usado"] = modelo_usado

    return resultado


# Nombre visible de cada proveedor, para mostrar en la interfaz.
PROVEEDORES_INFO = {
    "gemini": {"nombre": "Gemini (Google)", "env_key": "GEMINI_API_KEY"},
    "anthropic": {"nombre": "Claude (Anthropic)", "env_key": "ANTHROPIC_API_KEY"},
    "openai": {"nombre": "ChatGPT (OpenAI)", "env_key": "OPENAI_API_KEY"},
}


def _es_key_valida(valor: str) -> bool:
    """Descarta valores vacíos o que todavía sean el placeholder de ejemplo
    (ej. 'sk-ant-tu-key-aqui'), para no confundir un recordatorio con una key real."""
    if not valor:
        return False
    return "tu-key-aqui" not in valor.lower()


def proveedores_configurados() -> list:
    """Devuelve la lista de proveedores que ya tienen una API key REAL puesta en
    el .env (no un placeholder de ejemplo), en el orden en que deberían
    mostrarse/evaluarse. Hoy (si solo tienes GEMINI_API_KEY) devuelve ['gemini'];
    apenas agregues ANTHROPIC_API_KEY y/o OPENAI_API_KEY reales al .env, aparecen
    solos aquí, sin tocar código."""
    disponibles = []
    if config.gemini_configurado():
        disponibles.append("gemini")
    if config.anthropic_configurado():
        disponibles.append("anthropic")
    if config.openai_configurado():
        disponibles.append("openai")
    return disponibles


def evaluar_conversacion_multi(conversacion_texto: str, asesor: str, proveedores: list = None, pais: str = None, bandeja: str = None) -> dict:
    """
    Evalúa la misma conversación con varios proveedores de IA a la vez (los que
    estén configurados), para comparar sus resultados en vez de confiar en uno
    solo. Si un proveedor fallara (ej. se le acabó el crédito), no tumba a los
    demás: ese proveedor queda con {"error": "..."} y los otros siguen normal.

    Devuelve: {"gemini": {...evaluación...}, "anthropic": {"error": "..."}, ...}
    """
    proveedores = proveedores or proveedores_configurados()
    resultados = {}
    for proveedor in proveedores:
        try:
            resultados[proveedor] = evaluar_conversacion(conversacion_texto, asesor, proveedor=proveedor, pais=pais, bandeja=bandeja)
        except Exception as e:
            resultados[proveedor] = {"error": str(e)}
    return resultados


def _construir_prompt_coaching(datos: dict, compromisos_anteriores: dict = None) -> str:
    """Arma el prompt para que la IA sintetice un plan de coaching a partir del
    HISTORIAL COMPLETO de un asesor (varias evaluaciones), no de una sola
    conversación — el objetivo es detectar patrones reales, no repetir lo que
    ya dice cada informe individual."""

    cats_texto = "\n".join(
        f"- {cat}: {round(val*100,1)}% de eficiencia (promedio de sus {datos['total']} evaluaciones)"
        for cat, val in datos["categorias_ordenadas"]
    )

    oportunidades_texto = "\n".join(
        f"- (ID {o['id_caso'] or 'N/A'}, {o['fecha']}) {o['texto']}" for o in datos["oportunidades_recientes"]
    ) or "(sin datos de texto disponibles todavía para este asesor)"

    positivos_texto = "\n".join(
        f"- (ID {p['id_caso'] or 'N/A'}, {p['fecha']}) {p['texto']}" for p in datos["positivos_recientes"]
    ) or "(sin datos de texto disponibles todavía para este asesor)"

    criticos_texto = (
        f"{datos['total_criticos']} ítem(s) crítico(s) activado(s) en el periodo: {', '.join(datos['criticos_detalle'])}"
        if datos["total_criticos"] else "Ningún ítem crítico activado en el periodo — buen historial en ese sentido."
    )

    if compromisos_anteriores:
        acciones_previas = "\n".join(f"- {a}" for a in compromisos_anteriores.get("plan_accion", [])) or "(sin acciones registradas)"
        compromisos_texto = f"""=== COMPROMISOS DE LA SESIÓN DE COACHING ANTERIOR ({compromisos_anteriores.get('guardado_en', '')}) ===
En esa sesión, el plan de acción acordado fue:
{acciones_previas}

Nota promedio en ese momento: {round(compromisos_anteriores.get('nota_promedio', 0)*100, 1)}%
Nota promedio ahora: {round(datos['nota_promedio']*100, 1)}%

IMPORTANTE: en el campo "seguimiento_compromisos" de tu respuesta, evalúa HONESTAMENTE si estos compromisos se cumplieron,
comparando los números de antes contra los de ahora, y citando evidencia real (con ID de caso) de las oportunidades de
mejora recientes de abajo — si el mismo problema sigue apareciendo, dilo directamente, no lo suavices."""
    else:
        compromisos_texto = "=== COMPROMISOS DE LA SESIÓN ANTERIOR: no aplica, esta es la primera vez que se genera un plan de coaching para este asesor. ==="

    tendencia_cruda = (
        f"Primera mitad del periodo: {round(datos['nota_primera_mitad']*100,1)}% -> "
        f"Segunda mitad: {round(datos['nota_segunda_mitad']*100,1)}%"
    )

    return f"""Eres un coach de calidad de atención al cliente (QA Lead) en Dropi, una
plataforma de dropshipping en LATAM. Tu tarea es sintetizar un PLAN DE COACHING
para UN asesor específico, a partir de su historial de evaluaciones de calidad
— no estás evaluando una conversación puntual, estás buscando PATRONES a través
del tiempo para ayudar a su líder a preparar una conversación de desarrollo
constructiva y accionable.

=== DATOS DEL ASESOR: {datos['asesor']} ===
Periodo analizado: {datos['primera_fecha']} a {datos['ultima_fecha']} ({datos['total']} evaluaciones)
Nota promedio general: {round(datos['nota_promedio']*100,1)}%
Tendencia: {tendencia_cruda}

Eficiencia por categoría (ordenado de la más débil a la más fuerte):
{cats_texto}

Ítems críticos: {criticos_texto}

{compromisos_texto}

Oportunidades de mejora detectadas en sus evaluaciones recientes (evidencia real, más reciente primero):
{oportunidades_texto}

Puntos positivos detectados en sus evaluaciones recientes:
{positivos_texto}

=== TU TAREA ===
Devuelve ÚNICAMENTE un JSON válido (sin texto antes ni después, sin markdown),
con exactamente esta forma:

{{
  "resumen_general": "2-3 frases resumiendo el desempeño general del asesor en este periodo, en tono profesional pero humano — esto lo va a leer su líder antes de una conversación de desarrollo con él/ella",
  "seguimiento_compromisos": "Si hay compromisos de una sesión anterior (ver arriba): 2-4 frases evaluando HONESTAMENTE si se cumplieron, con cifras exactas y al menos 1 ID de caso como evidencia. Si el problema persiste, dilo directo. Si no hay sesión anterior, escribe exactamente: 'Este es el primer plan de coaching de este asesor — no hay compromisos previos que evaluar.'",
  "tendencia": "3-4 frases, citando SIEMPRE los porcentajes exactos en cifras (ej. 'pasó de 84% a 82.2%', nunca 'de ochenta y cuatro a ochenta y dos'): ¿está mejorando, estable o empeorando? Compara primera mitad vs. segunda mitad del periodo con el número exacto, y menciona también qué categoría específica explica ese cambio (la que más subió o más bajó). Sé específico, no genérico.",
  "alerta_tendencia": "'ninguna' si el cambio entre mitades es menor a 3 puntos porcentuales, 'atencion' si bajó entre 3 y 8 puntos, 'critica' si bajó más de 8 puntos o hay un ítem crítico en el periodo",
  "fortalezas_consistentes": ["fortaleza 1 con evidencia breve, citando el ID del caso de donde sale la evidencia", "fortaleza 2 con evidencia breve, citando el ID"],
  "areas_prioritarias": [
    {{"area": "nombre corto del área", "evidencia": "1-2 frases citando patrones reales de las oportunidades de mejora de arriba — SIEMPRE menciona el ID del caso (o los IDs, si citas más de uno) como evidencia concreta, no solo la fecha", "impacto": "alto, medio o bajo"}}
  ],
  "plan_accion": ["acción concreta y específica 1 para la próxima capacitación/1:1, citando el ID del caso real que se va a usar como ejemplo (no solo la fecha)", "acción concreta 2, con su ID si aplica", "acción concreta 3"]
}}

Reglas:
1. Basa TODO en los datos reales de arriba — no inventes patrones que no estén respaldados por la evidencia.
2. NÚMEROS SIEMPRE EN CIFRAS, nunca en palabras — escribe "84%" y "82.2%", nunca "ochenta y cuatro por ciento". Esto aplica a todos los campos, no solo a "tendencia".
3. CITA EL ID DEL CASO, no solo la fecha, en "fortalezas_consistentes", "areas_prioritarias" y "plan_accion" — cada vez que menciones un caso real de las oportunidades/positivos de arriba, usa el formato "el caso ID {{numero}}", para que quien lea el plan pueda ir a buscarlo directo en el programa sin tener que adivinar cuál fue.
4. "areas_prioritarias": máximo 3, ordenadas de mayor a menor impacto. Si el asesor no tiene problemas claros, dilo honestamente (no inventes debilidades por rellenar).
5. "plan_accion": deben ser acciones ESPECÍFICAS, accionables, y basadas en evidencia real citada con ID — nunca genéricas tipo "mejorar la comunicación". Ejemplo bueno: "Revisar el caso ID 215475502389312 en la sesión 1:1, donde el asesor no confirmó la satisfacción del cliente antes de cerrar el chat, y practicar 3 frases de cierre alternativas".
6. No uses asteriscos ni markdown en ningún texto.
7. Tono: profesional, constructivo, directo — ni demasiado duro ni condescendiente. Sé asertivo: afirma lo que los datos muestran con seguridad, sin rodeos ni frases vagas tipo "podría ser que" — si la evidencia lo respalda, dilo con precisión. El objetivo final es que el asesor MEJORE, no solo documentar que le fue mal — enmarca las áreas prioritarias como oportunidades concretas de crecimiento, no como una lista de fallas.
"""


def generar_coaching(datos: dict, proveedor: str = None, api_key: str = None, compromisos_anteriores: dict = None) -> dict:
    """A partir de los datos agregados de un asesor (ver coaching.datos_para_coaching),
    le pide a la IA que sintetice un plan de coaching. Reutiliza toda la
    infraestructura de proveedores/cadena de respaldo ya existente.

    compromisos_anteriores: el plan de coaching guardado más reciente de este
    asesor (ver coaching_service.obtener_plan_anterior) — si existe, la IA lo
    usa para evaluar si los compromisos de la sesión pasada se cumplieron,
    cerrando el ciclo real de seguimiento en vez de generar un reporte
    aislado cada vez."""
    proveedor = proveedor or ("gemini" if config.gemini_api_key else None)
    if not proveedor:
        raise RuntimeError("No hay ningún proveedor de IA configurado.")

    prompt = _construir_prompt_coaching(datos, compromisos_anteriores)

    if proveedor == "gemini":
        api_key = api_key or config.gemini_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una GEMINI_API_KEY real.")
        modelo_preferido = config.gemini_model or None
        texto_respuesta, _modelo_usado = _llamar_gemini(prompt, api_key, modelo_preferido)
    elif proveedor == "anthropic":
        api_key = api_key or config.anthropic_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una ANTHROPIC_API_KEY real.")
        modelo = config.anthropic_model or ANTHROPIC_MODEL_DEFAULT
        texto_respuesta, _modelo_usado = _llamar_anthropic(prompt, api_key, modelo)
    elif proveedor == "openai":
        api_key = api_key or config.openai_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una OPENAI_API_KEY real.")
        modelo_preferido = config.openai_model or None
        texto_respuesta, _modelo_usado = _llamar_openai(prompt, api_key, modelo_preferido)
    else:
        raise RuntimeError(f"Proveedor desconocido: {proveedor}")

    texto_limpio = _limpiar_json(texto_respuesta)
    try:
        plan = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"La IA no devolvió un JSON válido para el plan de coaching: {e}")

    if plan.get("alerta_tendencia") not in ("ninguna", "atencion", "critica"):
        # Respaldo si la IA no trajo el campo, o lo trajo con un valor
        # inesperado: se calcula directo de los números, sin depender de la IA.
        cambio = round((datos.get("nota_segunda_mitad", 0) - datos.get("nota_primera_mitad", 0)) * 100, 1)
        if datos.get("total_criticos", 0) > 0 or cambio <= -8:
            plan["alerta_tendencia"] = "critica"
        elif cambio <= -3:
            plan["alerta_tendencia"] = "atencion"
        else:
            plan["alerta_tendencia"] = "ninguna"

    return plan


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python evaluator.py <ruta_pdf> <nombre_asesor> [proveedor]")
        sys.exit(1)

    sys.path.insert(0, str(BASE_DIR / "src"))
    from pdf_parser import cargar_conversacion_desde_pdf

    ruta_pdf, asesor = sys.argv[1], sys.argv[2]
    proveedor = sys.argv[3] if len(sys.argv) > 3 else None
    conv = cargar_conversacion_desde_pdf(ruta_pdf)
    resultado = evaluar_conversacion(conv.texto_plano(), asesor, proveedor=proveedor)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
