"""Encuentra la guía operativa relevante para un caso específico, para dársela
a la IA como referencia real al evaluar 'apego a la guía' — en vez de que
evalúe ese ítem a ciegas (que era justo la queja de Marlon en la reunión: la
IA penalizaba por no seguir un paso que ni siquiera aplicaba a ese caso).

Las guías viven en config/guias/<pais_slug>/*.md (específicas de cada país) y
config/guias/logistica_general/*.md (aplican a todos los países por igual).
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GUIAS_DIR = BASE_DIR / "config" / "guias"

STOPWORDS_MATCH = {
    "de", "la", "el", "los", "las", "y", "en", "a", "con", "para", "del",
    "sac", "modelo", "guia", "guía", "detallada", "sin", "un", "una",
}


def _slug(texto: str) -> str:
    texto = texto.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        texto = texto.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def _palabras_clave(texto: str) -> set:
    texto = _slug(texto).replace("_", " ")
    return {p for p in texto.split() if p not in STOPWORDS_MATCH and len(p) > 2}


def listar_guias_disponibles(pais: str = None) -> list:
    """Todas las guías que aplicarían a un país: las específicas de ese país +
    las de logística general (que aplican a todos)."""
    guias = []
    if pais:
        carpeta_pais = GUIAS_DIR / _slug(pais)
        if carpeta_pais.exists():
            guias += list(carpeta_pais.glob("*.md"))
    carpeta_logistica = GUIAS_DIR / "logistica_general"
    if carpeta_logistica.exists():
        guias += list(carpeta_logistica.glob("*.md"))
    return guias


def encontrar_guia_relevante(pais: str, bandeja: str) -> dict:
    """Busca, entre las guías disponibles para ese país, la que mejor coincide
    con el nombre de la bandeja del caso (por palabras en común). Si no hay
    ninguna coincidencia razonable, devuelve None — y el ítem de 'apego a la
    guía' se califica como 'no aplica' (puntaje máximo), no como una falla."""
    if not bandeja:
        return None

    palabras_bandeja = _palabras_clave(bandeja)
    if not palabras_bandeja:
        return None

    candidatas = listar_guias_disponibles(pais)
    mejor = None
    mejor_score = 0

    for ruta in candidatas:
        titulo = ruta.stem.replace("_", " ")
        palabras_titulo = _palabras_clave(titulo)
        interseccion = palabras_bandeja & palabras_titulo
        if not interseccion:
            continue
        # score: cuántas palabras de la bandeja aparecen en el título, ponderado
        score = len(interseccion) / len(palabras_bandeja)
        if score > mejor_score:
            mejor_score = score
            mejor = ruta

    if mejor is None or mejor_score < 0.5:  # exige que coincida al menos la mitad de las palabras clave de la bandeja
        return None

    texto = mejor.read_text(encoding="utf-8")
    return {"titulo": mejor.stem.replace("_", " "), "archivo": str(mejor), "texto": texto, "score": round(mejor_score, 2)}
