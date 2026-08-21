"""Encuentra las preguntas/respuestas de la base de conocimiento de Gali que
son relevantes para una conversación específica — revisa TODAS las entradas
de ese país cada vez (no se salta ninguna), pero solo devuelve las que de
verdad tienen coincidencia real, con un tope máximo de resultados.

Mismo principio que guias.py: mejor devolver pocas o ninguna, que forzar un
número fijo de resultados mediocres solo por completar una cantidad.
"""
import json
import re
from pathlib import Path

STOPWORDS = {
    "de", "la", "el", "los", "las", "y", "en", "a", "con", "para", "del",
    "un", "una", "que", "como", "cómo", "es", "mi", "me", "por", "se",
    "tu", "su", "lo", "al", "no", "si", "sí", "puedo", "hacer", "donde",
    "dónde", "cuando", "cuándo", "qué", "cual", "cuál",
    # --- Lenguaje conversacional genérico: aparece en casi cualquier mensaje,
    # así que NO debe contar como señal de que el tema coincide ---
    "hola", "buenas", "buenos", "dias", "tardes", "noches", "gracias",
    "porfa", "porfavor", "favor", "ayuda", "ayudame", "necesito", "quiero",
    "quisiera", "tengo", "tener", "saber", "hoy", "ahora", "ya", "bien",
    "mal", "algo", "esto", "eso", "aca", "aqui", "alli", "ahi", "les",
    "nos", "les", "muy", "mas", "menos", "solo", "aun", "todavia", "vez",
    "caso", "mensaje", "cliente", "asesor", "conversacion", "pedido",
}

MINIMO_COINCIDENCIAS_REALES = 2  # al menos 2 palabras clave genuinas en común, no solo 1 por azar


def _palabras_clave(texto: str) -> set:
    texto = texto.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"), ("¿", " "), ("?", " "), ("¡", " "), ("!", " ")]:
        texto = texto.replace(a, b)
    palabras = re.findall(r"[a-z0-9]+", texto)
    return {p for p in palabras if p not in STOPWORDS and len(p) > 2}


def _score_entrada(palabras_conversacion: set, entrada: dict) -> tuple:
    """Puntúa una entrada de FAQ contra las palabras de la conversación.
    Las 'tags' pesan más que la pregunta (son palabras clave curadas a mano),
    y las 'variaciones' (formas reales en que preguntan los clientes) también
    pesan fuerte, porque son el lenguaje natural real, no la versión formal.

    Devuelve (score, cantidad_de_palabras_distintas_en_comun) — lo segundo se
    usa para exigir un mínimo real, y no dejar pasar una entrada solo porque
    una palabra suelta coincidió por casualidad."""
    score = 0.0
    palabras_en_comun = set()

    palabras_tags = _palabras_clave(entrada.get("tags", ""))
    if palabras_tags:
        comunes = palabras_conversacion & palabras_tags
        palabras_en_comun |= comunes
        score += 3.0 * len(comunes) / len(palabras_tags)

    palabras_variaciones = _palabras_clave(entrada.get("variaciones", ""))
    if palabras_variaciones:
        comunes = palabras_conversacion & palabras_variaciones
        palabras_en_comun |= comunes
        score += 2.0 * len(comunes) / len(palabras_variaciones)

    palabras_pregunta = _palabras_clave(entrada.get("pregunta", ""))
    if palabras_pregunta:
        comunes = palabras_conversacion & palabras_pregunta
        palabras_en_comun |= comunes
        score += 1.0 * len(comunes) / len(palabras_pregunta)

    return score, len(palabras_en_comun)


def buscar_faqs_relevantes(texto_conversacion: str, entradas_pais: list, top_n: int = 8, umbral_minimo: float = 0.35) -> list:
    """Revisa TODAS las entradas de FAQ de ese país (sin excepción) y devuelve
    solo las que tuvieron una coincidencia real — hasta `top_n`, pero puede
    devolver menos (o ninguna) si no hay coincidencias genuinas."""
    palabras_conversacion = _palabras_clave(texto_conversacion)
    if not palabras_conversacion:
        return []

    puntuadas = []
    for entrada in entradas_pais:  # se revisan TODAS, sin excepción
        score, cantidad_en_comun = _score_entrada(palabras_conversacion, entrada)
        if score >= umbral_minimo and cantidad_en_comun >= MINIMO_COINCIDENCIAS_REALES:
            puntuadas.append((score, entrada))

    puntuadas.sort(key=lambda x: x[0], reverse=True)
    return [entrada for score, entrada in puntuadas[:top_n]]


def _slug_pais(pais: str) -> str:
    texto = (pais or "").lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        texto = texto.replace(a, b)
    return re.sub(r"[^a-z]+", "", texto)


def _cargar_entradas_pais(pais: str) -> list:
    ruta = Path(__file__).resolve().parent / "config" / "faqs_gali" / f"faqs_gali_{_slug_pais(pais)}.json"
    # también puede vivir directo dentro de src/ si config/ no aplica en este entorno
    if not ruta.exists():
        ruta = Path(__file__).resolve().parent.parent / "config" / "faqs_gali" / f"faqs_gali_{_slug_pais(pais)}.json"
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def contexto_faqs_gali(texto_de_gali: str, pais: str, top_n: int = 8) -> str:
    """Arma el bloque de texto listo para inyectar en el prompt de evaluación:
    las preguntas/respuestas oficiales más relevantes para lo que Gali dijo en
    esta conversación específica. Si Gali no habló, o no hay FAQs para ese
    país, o no hubo ninguna coincidencia real, devuelve cadena vacía (nunca
    inventa contenido)."""
    if not texto_de_gali or not texto_de_gali.strip():
        return ""

    entradas = _cargar_entradas_pais(pais)
    if not entradas:
        return ""

    relevantes = buscar_faqs_relevantes(texto_de_gali, entradas, top_n=top_n)
    if not relevantes:
        return ""

    partes = ["Preguntas/respuestas OFICIALES de la base de conocimiento de Gali, relevantes a esta conversación (úsalas como referencia para juzgar si Gali dio información correcta):"]
    for r in relevantes:
        partes.append(f"- P: {r['pregunta']}\n  R oficial: {r['respuesta']}")
    return "\n".join(partes)
