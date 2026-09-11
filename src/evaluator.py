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
    # "gemini-2.5-flash" — RETIRADO por Google (404 permanente, no temporal:
    # "no longer available to new users"). Se quitó de la cadena para no
    # perder tiempo llamando a un modelo que sabemos que siempre va a fallar.
    "gemini-3.6-flash",  # el reemplazo que el propio error de Google recomienda
]
ANTHROPIC_MODEL_DEFAULT = "claude-sonnet-4-6"

# Salvedades a nivel de ÁREA (no de bandeja individual) — para reglas que
# aplican parejo a TODAS las bandejas de un área, sin tener que repetir el
# mismo texto en cada guía operativa por separado. Se determina el área real
# de la bandeja (ver areas.py) y, si hay una salvedad definida para esa área,
# se inyecta en el prompt sin importar cuál guía específica haya coincidido
# (o incluso si ninguna coincidió).
SALVEDADES_POR_AREA = {
    "LOGISTICA": (
        "En logística, el cliente puede llegar a distintas bandejas por caminos distintos (otros "
        "botones/flujos de Intercom), así que no siempre el caso corresponde exactamente al alcance de "
        "esa bandeja. Cuando el caso es sobre un siniestro, novedad, indemnización, o cualquier gestión "
        "que le corresponde al módulo CAS de Dropi con las transportadoras — y el asesor redirige "
        "correctamente al cliente al CAS (por ejemplo, guiándolo con el video explicativo de YouTube "
        "sobre cómo usarlo) en vez de intentar resolverlo él mismo — ESO ES LO CORRECTO, no una falla. "
        "En ese escenario, califica los ítems de Procedimiento y Solución como CUMPLIDOS: redirigir al "
        "CAS es la solución correcta para ese tipo de caso, no la ausencia de una solución. No penalices "
        "al asesor por 'no resolver' cuando lo correcto era, precisamente, redirigir.\n\n"
        "Adicionalmente, en las bandejas de Anulaciones y Órdenes sin despacho, decirle al cliente que "
        "'se va a gestionar' (sin dar una resolución inmediata en el mismo chat) ES el proceso correcto "
        "— esas solicitudes requieren coordinación interna o con la transportadora que no se resuelve al "
        "instante. No penalices al asesor por no resolver en el momento cuando el proceso documentado "
        "es, precisamente, escalar la gestión y comunicarle al cliente que quedó en trámite. IMPORTANTE: "
        "esto NO exime del tiempo de SLA ya establecido para estas bandejas (ver Política de Tiempos de "
        "Respuesta, Cierre Final de Anulaciones/Órdenes sin despachar) — 'se va a gestionar' es la "
        "respuesta correcta EN EL MOMENTO, pero el caso completo debe seguir resolviéndose dentro del "
        "tiempo de SLA que ya le corresponde a ese proceso; no uses esta salvedad para justificar un "
        "caso que se demoró más de lo que el SLA permite."
    ),
    "GARANTÍAS": (
        "En Garantías, solo se puede atender UNA garantía por conversación — si el cliente necesita "
        "reportar otra garantía distinta, debe abrir un chat nuevo, no continuar en el mismo. Por esta "
        "razón, NO se debe esperar ni penalizar al asesor por no preguntar '¿hay algo más en lo que te "
        "pueda ayudar?' al cerrar — en esta bandeja específica, esa pregunta no aplica y no debe tratarse "
        "como una falla de cierre incompleto. Al contrario: si el asesor SÍ intenta atender una SEGUNDA "
        "garantía distinta dentro del mismo chat (en vez de pedirle al cliente que abra una conversación "
        "nueva para esa otra garantía), eso SÍ es un error de proceso y debe señalarse como tal — no es "
        "un gesto de buena atención, es una desviación del proceso correcto de esta bandeja."
    ),
}

# Reglas generales de evaluación — SIEMPRE se incluyen en el prompt, sin
# importar la bandeja, el área, o si hay guía operativa que coincida.
# Cada una viene de una corrección real señalada por el equipo, tras
# encontrar que la IA estaba penalizando comportamientos que en realidad
# son correctos.
REGLAS_GENERALES_EVALUACION = """1. CIERRE POR DOBLE CHAT: si el asesor cierra la conversación porque el cliente abrió un chat duplicado
   sobre el mismo tema (ya existe otra conversación abierta con el mismo caso), NO penalices esto como
   cierre prematuro o abandono — es el manejo correcto de un chat duplicado, no una falla de servicio.

2. MENSAJE DE VALIDACIÓN, NO DE CIERRE: el siguiente mensaje, cuando aparece justo después de dar una
   respuesta o solución (no al final de la conversación), es una validación de si el cliente necesita algo
   más — NO es un mensaje de cierre ni de despedida, y no debe evaluarse como tal ni penalizarse por
   "cerrar sin confirmar satisfacción":
   "¡Ha sido un gusto poder ayudarte! Si tienes otra consulta o hay algo más en lo que te pueda colaborar,
   por favor indícamelo aquí abajo y con gusto lo validamos."

3. NÚMERO DE GUÍA vs. NÚMERO DE ORDEN: el número de guía (de la transportadora) y el número de orden (de
   Dropi) usan sistemas de numeración DISTINTOS para el mismo pedido — es normal y esperado que las CIFRAS
   no coincidan entre sí; eso por sí solo NO es un error. Lo que sí debes verificar es que ambos números
   correspondan realmente al MISMO pedido/conversación que se está atendiendo — si el asesor da un número
   de guía u orden que pertenece a un pedido distinto al del cliente, eso sí es un error real de precisión,
   distinto de la simple diferencia de formato entre los 2 sistemas de numeración.

(Nota: el cierre por inactividad del cliente después de un tiempo sin respuesta ya está definido con su
regla exacta — incluyendo el requisito de avisar antes de cerrar — en la Política de Tiempos de Respuesta
(SLA) que se incluye más abajo; no la dupliques ni la contradigas aquí.)"""

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


def _construir_prompt(conversacion_texto: str, asesor: str, matriz: dict, politica: str, politica_sla: str = "", guia_relevante: dict = None, contexto_gali: str = "", texto_notas_internas: str = None, contexto_aprendizaje: str = "", salvedad_area: str = None) -> str:
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
        "resumen_caso": "1-2 frases describiendo el caso (bandeja, motivo, resultado)",
        "items": {
            iid: {"puntaje": "número entre 0 y el peso máximo del ítem", "justificacion": "1-2 frases con evidencia concreta de la conversación"}
            for iid in items_json_ids
        },
        "items_criticos": {
            cid: {"ocurrio": "Si o No", "justificacion": "SIEMPRE explica en 1 frase por qué sí ocurrió o por qué no ocurrió, con referencia concreta a la conversación"}
            for cid in criticos_ids
        },
        "lo_positivo": ["lista de 3 a 6 puntos fuertes; cada uno con el formato 'Concepto breve. Explicación con evidencia concreta.' (el concepto breve termina en PUNTO, no en dos puntos ':'; el sistema resalta esa primera parte en negrita automáticamente, NO uses asteriscos ni markdown)"],
        "oportunidades_mejora": ["lista de 1 a 5 puntos de mejora; mismo formato 'Concepto breve. Explicación con evidencia concreta.' (NO uses asteriscos ni markdown)"],
    }

    prompt = f"""Eres un auditor senior de calidad de soporte al cliente para Dropi (plataforma de dropshipping), evaluando conversaciones de Intercom.

Tu tarea es evaluar la gestión del asesor **{asesor}** en la siguiente conversación, aplicando ESTRICTAMENTE la matriz de calidad y la política de comunicación de la empresa.

=== POLÍTICA DE COMUNICACIÓN Y REDACCIÓN ===
{politica}

=== REGLAS GENERALES DE EVALUACIÓN (aplican siempre, a cualquier bandeja o caso) ===
{REGLAS_GENERALES_EVALUACION}

{"=== POLÍTICA DE TIEMPOS DE RESPUESTA (SLA) ===" + chr(10) + politica_sla if politica_sla else ""}

{("=== GUÍA OPERATIVA DE REFERENCIA PARA ESTE CASO (\"" + guia_relevante["titulo"] + "\") ===" + chr(10) + "Esta es la guía oficial del proceso que aplica a este caso específico. Úsala como referencia real para el ítem \"apego_guia_operativa\" — compara los pasos que dio el asesor contra los pasos documentados aquí. IMPORTANTE: si esta guía trae una sección explícita de \"INSTRUCCIÓN PARA LA EVALUACIÓN\" o similar, esas instrucciones tienen prioridad y aplican a TODOS los ítems relevantes (no solo apego_guia_operativa) — por ejemplo, si la guía dice que redirigir a cierto canal es la respuesta correcta para casos fuera de su alcance, eso también debe reflejarse en los ítems de Procedimiento y Solución, no solo en el de apego a la guía." + chr(10) + chr(10) + guia_relevante["texto"]) if guia_relevante else "=== GUÍA OPERATIVA: no se encontró ninguna guía documentada que aplique específicamente a este caso. El ítem \"apego_guia_operativa\" debe calificarse con el puntaje máximo (no aplica, no es una falla). ==="}

{("=== SALVEDAD DEL ÁREA (aplica a todas las bandejas de esta área, sin importar cuál coincidió arriba) ===" + chr(10) + salvedad_area) if salvedad_area else ""}

{("=== BASE DE CONOCIMIENTO DE GALI (referencia oficial) ===" + chr(10) + contexto_gali) if contexto_gali else "=== BASE DE CONOCIMIENTO DE GALI: no se encontró ninguna pregunta/respuesta oficial que aplique a lo que Gali dijo en este caso. Los ítems sobre Gali deben calificarse según el criterio general (no penalizar por falta de una referencia específica). ==="}

{("=== NOTAS INTERNAS DEL EQUIPO (fuente confirmada, aisladas del resto de la conversación) ===" + chr(10) + "Estas líneas SÍ están confirmadas como notas internas (no visibles al cliente) — evalúa el ítem \"Claridad y argumentación en Notas Internas\" con confianza total, usando SOLO este texto como evidencia." + chr(10) + chr(10) + texto_notas_internas) if texto_notas_internas else "=== NOTAS INTERNAS DEL EQUIPO: no se pudo aislar con certeza cuáles líneas de la conversación son notas internas y cuáles son mensajes al cliente (limitación del formato PDF exportado, no de este caso en particular). Para el ítem \"Claridad y argumentación en Notas Internas\", sé CONSERVADOR: solo penaliza si encuentras evidencia muy clara e inequívoca dentro de la conversación completa (por ejemplo, un comentario que menciona explícitamente ser una nota interna o de seguimiento). Ante la duda genuina, no penalices — es preferible no calificar con certeza baja que penalizar por una mala interpretación del formato. ==="}

{("=== APRENDIZAJE DE CALIBRACIONES HUMANAS PREVIAS ===" + chr(10) + "Estos son patrones de corrección reales hechos por auditores. NO son reglas para copiar ciegamente ni reemplazan la evidencia del caso actual; úsalos como alertas para evitar errores que la IA ha repetido antes." + chr(10) + contexto_aprendizaje) if contexto_aprendizaje else "=== APRENDIZAJE DE CALIBRACIONES: todavía no hay patrones repetidos suficientes para este contexto. ==="}

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

Reglas importantes:
1. El "puntaje" de cada ítem debe ser un número entre 0 y su peso máximo (puedes usar decimales, ej: si el peso máximo es 0.05, puedes dar 0.05, 0.03, 0.025, 0, etc. según el nivel de cumplimiento).
2. Sé estricto pero justo: si un ítem no aplica al caso (ej. no hubo necesidad de preguntas de clarificación porque el caso era claro desde el inicio), otorga el puntaje máximo de ese ítem.
3. En "lo_positivo" y "oportunidades_mejora", basa cada punto en evidencia concreta de la conversación (cita datos, tiempos, decisiones), en el mismo estilo de un informe de auditoría de calidad: profesional, específico, sin relleno genérico.
4. Para CADA ítem crítico, sin excepción, escribe una justificación de 1 frase explicando tu análisis: si marcas "Si", sé muy conservador y cita la evidencia exacta; si marcas "No", explica brevemente por qué consideras que no ocurrió (ej. "El asesor resolvió el caso sin necesidad de escalar" o "No se detectó lenguaje inadecuado en ningún mensaje"). Esta justificación ayuda al auditor humano a confirmar tu criterio, así que nunca la dejes vacía.
5. No inventes información que no esté en la conversación.
6. IMPORTANTE - formato de texto: en NINGÚN campo de texto (justificaciones, lo_positivo, oportunidades_mejora) uses asteriscos (**) ni ningún otro marcado tipo Markdown. Escribe texto plano; el sistema ya se encarga de aplicar la negrita a la primera frase de cada punto de "lo_positivo" y "oportunidades_mejora" automáticamente.
7. TIEMPOS Y HORARIO LABORAL: al evaluar "sla_primera_respuesta" y "seguimiento_tiempo", compara los tiempos reales de la conversación (usa los timestamps de cada mensaje) contra los tiempos máximos de la política de SLA para el proceso/bandeja correspondiente. Los huecos de tiempo que caen FUERA del horario laboral (lunes a viernes 8am-5pm, sábados/lunes festivos 8am-12m) NO cuentan como demora del asesor — un mensaje del cliente a las 6pm que se responde a las 8am del siguiente día hábil está DENTRO del SLA, no es una falla.
8. CIERRE VÁLIDO vs. ABANDONO ("cierra_sin_resolver"): usa la regla fija de "Cierre por inactividad del cliente" de la política de SLA (arriba): el asesor puede cerrar válidamente tras 4 horas de tiempo LABORAL de silencio del cliente después de una gestión clara, siempre que haya avisado antes de cerrar. Marca este ítem crítico como "Si" ÚNICAMENTE si el asesor cierra sin haber dado una gestión clara, sin avisar antes de cerrar, o cierra con MENOS de esas 4 horas de inactividad sin justificación. NO lo marques como "Si" si el asesor gestionó el caso apropiadamente, esperó el tiempo debido, y avisó antes de cerrar — eso es un cierre válido por inactividad del cliente, marca "No". Si el cierre fue algo prematuro pero no un abandono claro, refléjalo bajando el puntaje de "seguimiento_tiempo" en vez de activar el crítico.
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


def _llamar_gemini(prompt: str, api_key: str, modelo_preferido: str = None) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError(
            "Falta la librería google-genai. Instálala con: pip install google-genai --break-system-packages"
        )

    client = genai.Client(api_key=api_key)
    # Temperatura baja = respuestas más consistentes entre llamadas repetidas
    # con el mismo texto (no elimina 100% la variabilidad propia de la IA,
    # pero la reduce bastante para uso de auditoría).
    # max_output_tokens alto: el JSON completo (22 ítems + justificaciones +
    # lo_positivo + oportunidades) puede ser largo; sin este límite explícito,
    # algunos modelos lo cortan a la mitad y el JSON queda inválido.
    config = types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192)

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

                return texto
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


def _llamar_anthropic(prompt: str, api_key: str, modelo: str) -> str:
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
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def _llamar_openai(prompt: str, api_key: str, modelo_preferido: str = None) -> str:
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
                    temperature=0.1,
                    max_tokens=8192,
                    response_format={"type": "json_object"},
                )
                texto = response.choices[0].message.content

                try:
                    json.loads(_limpiar_json(texto))
                except json.JSONDecodeError:
                    raise RuntimeError("La respuesta llegó incompleta/cortada (JSON inválido)")

                return texto
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
    referencia real para evaluar el ítem "apego_guia_operativa". Si no hay
    ninguna guía que coincida con esa bandeja, el ítem se evalúa como "no
    aplica" (puntaje máximo), no como una falla — así se evita el problema de
    penalizar por no seguir un paso que ni siquiera correspondía a ese caso.

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

    salvedad_area = None
    if bandeja:
        try:
            from areas import area_de_bandeja
            salvedad_area = SALVEDADES_POR_AREA.get(area_de_bandeja(bandeja))
        except Exception as e:
            log.warning("No se pudo determinar el área de la bandeja: %s", e)

    contexto_gali = ""
    if texto_gali and pais:
        try:
            from faqs_gali_buscador import contexto_faqs_gali
            contexto_gali = contexto_faqs_gali(texto_gali, pais)
        except Exception as e:
            log.warning("No se pudo buscar en la base de conocimiento de Gali: %s", e)

    contexto_aprendizaje = ""
    try:
        from fase3 import contexto_aprendizaje_para_prompt
        contexto_aprendizaje = contexto_aprendizaje_para_prompt(pais or "", bandeja or "")
    except Exception as e:
        log.warning("No se pudo cargar aprendizaje de calibraciones: %s", e)

    prompt = _construir_prompt(conversacion_texto, asesor, matriz, politica, politica_sla, guia_relevante, contexto_gali, texto_notas_internas, contexto_aprendizaje, salvedad_area)

    if proveedor == "gemini":
        api_key = api_key or config.gemini_api_key
        if not api_key:
            raise RuntimeError(
                "No se encontró GEMINI_API_KEY. Consíguela gratis en https://aistudio.google.com/apikey "
                "y agrégala a tu archivo .env"
            )
        modelo_preferido = config.gemini_model or None  # si no está, usa la cadena de respaldo
        texto_respuesta = _llamar_gemini(prompt, api_key, modelo_preferido)

    elif proveedor == "anthropic":
        api_key = api_key or config.anthropic_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una ANTHROPIC_API_KEY real (todavía tiene el valor de ejemplo).")
        modelo = config.anthropic_model or ANTHROPIC_MODEL_DEFAULT
        texto_respuesta = _llamar_anthropic(prompt, api_key, modelo)

    elif proveedor == "openai":
        api_key = api_key or config.openai_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una OPENAI_API_KEY real (todavía tiene el valor de ejemplo).")
        modelo_preferido = config.openai_model or None
        texto_respuesta = _llamar_openai(prompt, api_key, modelo_preferido)

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
        registrar_uso(proveedor, len(prompt), len(texto_limpio), bool(guia_relevante))
    except Exception:
        pass  # nunca romper la evaluación real por esto

    # Se deja visible qué guía se usó (o que no había ninguna aplicable) para
    # que el auditor lo vea directamente en la pantalla de revisión, sin tener
    # que inferirlo leyendo la justificación del ítem "apego_guia_operativa".
    resultado["guia_utilizada"] = (
        {"encontrada": True, "titulo": guia_relevante["titulo"]}
        if guia_relevante
        else {"encontrada": False, "titulo": None}
    )

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
        texto_respuesta = _llamar_gemini(prompt, api_key, modelo_preferido)
    elif proveedor == "anthropic":
        api_key = api_key or config.anthropic_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una ANTHROPIC_API_KEY real.")
        modelo = config.anthropic_model or ANTHROPIC_MODEL_DEFAULT
        texto_respuesta = _llamar_anthropic(prompt, api_key, modelo)
    elif proveedor == "openai":
        api_key = api_key or config.openai_api_key
        if not _es_key_valida(api_key or ""):
            raise RuntimeError("No se encontró una OPENAI_API_KEY real.")
        modelo_preferido = config.openai_model or None
        texto_respuesta = _llamar_openai(prompt, api_key, modelo_preferido)
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
