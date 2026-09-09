"""Casos de prueba para validar que la IA evalúa correctamente — no es lo mismo
que tests/ (que prueba la LÓGICA del programa con datos falsos); esto prueba el
CRITERIO de la IA con conversaciones sintéticas reales, cada una con una falla
específica puesta a propósito.

Idea original de Diego Forero en la reunión del 6-ago-2026: crear conversaciones
de prueba con errores intencionales (ortografía, proceso, etc.) para confirmar
que la IA las detecta — no solo confiar en que "se ve bien".

Cada caso tiene:
  - texto: la conversación sintética, en el mismo formato que produce texto_plano()
  - asesor, pais, bandeja: metadata del caso
  - verificar(evaluacion, nota) -> (bool, mensaje): confirma si la IA detectó
    la falla (o la ausencia de falla) que se esperaba
"""


def _item(evaluacion, item_id):
    return evaluacion.get("items", {}).get(item_id, {}).get("puntaje", None)


def _critico(evaluacion, critico_id):
    return str(evaluacion.get("items_criticos", {}).get(critico_id, {}).get("ocurrio", "No")).strip().lower()


CASOS = []


# ============================================================ Caso 1
def _verificar_ortografia(evaluacion, nota):
    puntaje = _item(evaluacion, "ortografia")
    if puntaje is None:
        return False, "El ítem 'ortografia' no aparece en la evaluación"
    peso_max = 0.04  # ver config/matriz_calidad.json si cambia
    if puntaje < peso_max * 0.5:
        return True, f"Detectó la ortografía deficiente (puntaje {puntaje} de {peso_max})"
    return False, f"NO detectó la ortografía deficiente (dio {puntaje} de {peso_max}, esperaba menos de la mitad)"


CASOS.append({
    "nombre": "Ortografía deficiente",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
10:00 AM [CLIENTE] Juan Perez: ola nesesito ayuda con mi pedido q no a llegado
10:02 AM [STAFF] Asesor Prueba: ola juan como estas, dejame verificar tu pedido
10:03 AM [STAFF] Asesor Prueba: ya lo revise, tu pedido esta en transito y deveria llegar mañana sin falta
10:04 AM [CLIENTE] Juan Perez: ok gracias
10:04 AM [STAFF] Asesor Prueba: aver cualqier cosa me escrives, q tengas buen dia
""",
    "verificar": _verificar_ortografia,
})


# ============================================================ Caso 2
def _verificar_cierre_prematuro(evaluacion, nota):
    ocurrio = _critico(evaluacion, "cierre_prematuro_abandono")
    if ocurrio == "si":
        return True, "Detectó correctamente el cierre sin resolver (crítico activado)"
    return False, f"NO detectó el cierre sin resolver (crítico quedó en '{ocurrio}', esperaba 'Si')"


CASOS.append({
    "nombre": "Cierra sin resolver, sin avisar, sin esperar",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
10:00 AM [CLIENTE] Maria Lopez: Hola, mi producto llegó dañado, necesito la garantía
10:02 AM [STAFF] Asesor Prueba: Hola, para eso debes subir la garantía al módulo correspondiente
10:15 AM [STAFF] Asesor Prueba: Conversación cerrada
""",
    "verificar": _verificar_cierre_prematuro,
})


# ============================================================ Caso 3
def _verificar_maltrato(evaluacion, nota):
    ocurrio = _critico(evaluacion, "maltrato_lenguaje_inadecuado")
    if ocurrio == "si":
        return True, "Detectó correctamente el lenguaje inadecuado (crítico activado)"
    return False, f"NO detectó el lenguaje inadecuado (crítico quedó en '{ocurrio}', esperaba 'Si')"


CASOS.append({
    "nombre": "Lenguaje inadecuado hacia el cliente",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
10:00 AM [CLIENTE] Carlos Ruiz: Llevo 3 días esperando respuesta, esto es inaceptable
10:02 AM [STAFF] Asesor Prueba: Mire, si no le gusta como trabajamos puede irse a comprar a otro lado
10:03 AM [CLIENTE] Carlos Ruiz: ¿Perdón? Solo quiero una solución
10:04 AM [STAFF] Asesor Prueba: Ya le dije, deje de molestar con lo mismo
""",
    "verificar": _verificar_maltrato,
})


# ============================================================ Caso 4
def _verificar_info_falsa(evaluacion, nota):
    ocurrio = _critico(evaluacion, "informacion_falsa_enganosa")
    if ocurrio == "si":
        return True, "Detectó correctamente la información incorrecta (crítico activado)"
    return False, f"NO detectó la información incorrecta (crítico quedó en '{ocurrio}', esperaba 'Si')"


CASOS.append({
    "nombre": "Información técnica incorrecta / inventada",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
10:00 AM [CLIENTE] Laura Gil: ¿Cuánto tiempo tengo para subir una garantía?
10:02 AM [STAFF] Asesor Prueba: Tienes 90 días desde la entrega para subir cualquier garantía, sin excepción
10:03 AM [CLIENTE] Laura Gil: Perfecto, entonces tengo tiempo. Gracias
""",
    "verificar": _verificar_info_falsa,
})


# ============================================================ Caso 5
# NOTA (migración a Matriz V2, agosto 2026): el caso "Comparte información
# interna/confidencial" se retiró de aquí porque la Matriz V2 ya no incluye
# un ítem crítico equivalente a "comparte_info_interna" — su cobertura fue
# una decisión explícita al reemplazar la matriz (ver ARQUITECTURA.md).


# ============================================================ Caso 6 (control positivo)
def _verificar_caso_bien_manejado(evaluacion, nota):
    criticos_activados = [
        cid for cid, v in evaluacion.get("items_criticos", {}).items()
        if str(v.get("ocurrio", "No")).strip().lower() == "si"
    ]
    if criticos_activados:
        return False, f"Activó crítico(s) que NO debería: {criticos_activados} (caso bien manejado, no debería tener ninguno)"
    if nota["nota_final"] < 0.85:
        return False, f"Nota muy baja para un caso bien manejado: {nota['nota_final']*100:.1f}% (esperaba 85%+)"
    return True, f"Sin críticos activados y nota alta ({nota['nota_final']*100:.1f}%), como se esperaba"


CASOS.append({
    "nombre": "Control: caso bien manejado de principio a fin",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
10:00 AM [CLIENTE] Ana Torres: Hola, mi producto llegó con una falla, ¿qué debo hacer?
10:01 AM [STAFF] Asesor Prueba: ¡Hola Ana! Soy Camila de soporte Dropi, con gusto te ayudo. ¿Me confirmas el número de tu pedido para revisar el caso?
10:02 AM [CLIENTE] Ana Torres: Claro, es el 998877
10:04 AM [STAFF] Asesor Prueba: Gracias Ana. Ya revisé tu pedido: para gestionar la garantía debes subir el reporte con fotos del producto dañado en el módulo de garantías de la plataforma, dentro de los 10 días desde la entrega. Te dejo el tutorial: https://ejemplo.com/garantias
10:05 AM [CLIENTE] Ana Torres: Perfecto, ya entendí, muchas gracias
10:06 AM [STAFF] Asesor Prueba: Con gusto Ana, cualquier otra duda aquí estoy. ¡Que tengas un excelente día!
""",
    "verificar": _verificar_caso_bien_manejado,
})


# ============================================================ Caso 7 (el caso de Marlon: cierre válido por inactividad)
def _verificar_cierre_valido_por_inactividad(evaluacion, nota):
    ocurrio = _critico(evaluacion, "cierre_prematuro_abandono")
    if ocurrio == "no":
        return True, "NO penalizó el cierre por inactividad justificada (correcto — el asesor sí gestionó y avisó)"
    return False, f"Penalizó un cierre que SÍ estaba justificado (crítico quedó en '{ocurrio}', esperaba 'No') — revisar la regla de inactividad"


CASOS.append({
    "nombre": "Cierre VÁLIDO por inactividad del cliente (no debe penalizar)",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Garantías",
    "texto": """
--- 2026-08-10 ---
09:00 AM [CLIENTE] Diego Ramirez: Hola, ¿cómo subo una garantía?
09:02 AM [STAFF] Asesor Prueba: ¡Hola Diego! Debes subir el reporte con fotos en el módulo de garantías, dentro de los 10 días desde la entrega. Aquí el tutorial: https://ejemplo.com/garantias
09:03 AM [CLIENTE] Diego Ramirez: Ok, gracias
--- 2026-08-10 ---
01:30 PM [STAFF] Asesor Prueba: Hola Diego, veo que no has tenido más consultas. Cierro este chat por ahora, cualquier cosa que necesites no dudes en escribirnos de nuevo. ¡Buen día!
""",
    "verificar": _verificar_cierre_valido_por_inactividad,
})


# ============================================================ Caso 8
# NOTA (migración a Matriz V2, agosto 2026): el caso "Apego a guía operativa"
# se retiró de aquí porque la Matriz V2 no incluye un ítem de "apego_guia_
# operativa" — la guía operativa sigue cargándose como contexto (ver
# guias.py) pero ya no se evalúa como un ítem independiente, sino como
# respaldo del ítem "precision_tecnica_fondo" (ver src/evaluator.py).


# ============================================================ Caso 9 (excepción Cartera — NO debe penalizar)
def _verificar_redireccion_cartera_valida(evaluacion, nota):
    ocurrio = _critico(evaluacion, "transferencia_injustificada")
    if ocurrio == "no":
        return True, "NO penalizó la redirección a WhatsApp de Cartera (correcto — es el proceso oficial)"
    return False, f"Penalizó una redirección a Cartera que SÍ era válida (crítico quedó en '{ocurrio}', esperaba 'No') — revisar el campo 'excepciones' de transferencia_injustificada"


CASOS.append({
    "nombre": "Redirección válida a WhatsApp de Cartera (no debe penalizar, aunque llegue por Triage Administrativo)",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Triage Administrativo",
    "texto": """
--- 2026-09-04 ---
10:00 AM [CLIENTE] Marcela Ruiz: Hola, tengo mi cartera congelada y no entiendo por qué, necesito que me ayuden
10:02 AM [STAFF] Asesor Prueba: Hola Marcela, entiendo tu inquietud. Los casos de congelación de cartera los gestiona directamente el equipo de Cartera para poder revisar tu cuenta a fondo. Te comparto el WhatsApp oficial de Cartera para que te atiendan: +57 300 000 0000
10:03 AM [CLIENTE] Marcela Ruiz: Ok, muchas gracias
10:04 AM [STAFF] Asesor Prueba: Con gusto Marcela, cualquier otra cosa aquí estamos. ¡Buen día!
""",
    "verificar": _verificar_redireccion_cartera_valida,
})


# ============================================================ Caso 10 (control: transferencia SIN relación a Cartera SÍ debe penalizar)
def _verificar_transferencia_no_cartera_si_penaliza(evaluacion, nota):
    ocurrio = _critico(evaluacion, "transferencia_injustificada")
    if ocurrio == "si":
        return True, "SÍ penalizó la transferencia injustificada sin relación a Cartera (correcto — la excepción no se sobre-aplicó)"
    return False, f"NO penalizó una transferencia injustificada real (crítico quedó en '{ocurrio}', esperaba 'Si') — la excepción de Cartera puede estarse aplicando de más"


CASOS.append({
    "nombre": "Control: transferencia injustificada SIN relación a Cartera (SÍ debe penalizar, para confirmar que la excepción no se sobre-aplica)",
    "asesor": "Asesor Prueba",
    "pais": "Colombia",
    "bandeja": "Triage Administrativo",
    "texto": """
--- 2026-09-04 ---
10:00 AM [CLIENTE] Julian Torres: Hola, mi pedido llegó incompleto, faltó un producto
10:02 AM [STAFF] Asesor Prueba: Hola Julian, para eso escríbenos por WhatsApp al +57 300 111 2222, ahí te ayudan
10:03 AM [CLIENTE] Julian Torres: ¿Pero ustedes no me pueden ayudar aquí?
10:04 AM [STAFF] Asesor Prueba: No, debes escribir por ese canal. Buen día.
""",
    "verificar": _verificar_transferencia_no_cartera_si_penaliza,
})

