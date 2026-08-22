"""Encuentra la guía operativa relevante para un caso específico, para dársela
a la IA como contexto de referencia al evaluar el ítem "precision_tecnica_fondo"
— así la IA compara los pasos técnicos que dio el asesor contra los pasos
documentados en la guía oficial, en vez de evaluar a ciegas.

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

    # Normaliza errores de tipeo reales conocidos (ej. "Traige general" ->
    # "Triage General") ANTES de buscar palabras clave — usa el mismo mapa de
    # config/bandejas_sinonimos.json que ya usa el dashboard, para que una
    # bandeja mal escrita no pierda su guía operativa solo por un typo.
    try:
        from areas import nombre_canonico_si_existe
        bandeja = nombre_canonico_si_existe(bandeja) or bandeja
    except Exception:
        pass  # si algo falla acá, se sigue con el nombre tal cual vino

    palabras_bandeja = _palabras_clave(bandeja)
    if not palabras_bandeja:
        return None

    candidatas = listar_guias_disponibles(pais)
    mejor = None
    mejor_score = 0.0

    for ruta in candidatas:
        titulo = ruta.stem.replace("_", " ")
        palabras_titulo = _palabras_clave(titulo)
        interseccion = palabras_bandeja & palabras_titulo
        if not interseccion:
            continue
        # Score tipo F1 (no solo "cuántas palabras de la bandeja aparecen en
        # el título" como antes): combina esa cobertura con qué tan PRECISO
        # es el título (cuánto de él se explica por la bandeja). Esto
        # corrige un bug real: con la fórmula vieja, "Triage General"
        # empataba en 0.50 tanto con 'modelo_guia_detallada_triage' (título
        # 100% explicado por la bandeja) como con
        # 'modelo_guia_detallada_lineal_general' (título con una palabra
        # ajena, "lineal") — y ese empate lo resolvía el orden en que el
        # sistema de archivos listaba los archivos, no la relevancia real.
        # Eso podía hacer que la MISMA bandeja terminara con guías distintas
        # en corridas distintas, sin que nadie lo notara.
        cobertura_bandeja = len(interseccion) / len(palabras_bandeja)
        precision_titulo = len(interseccion) / len(palabras_titulo)
        score = 2 * cobertura_bandeja * precision_titulo / (cobertura_bandeja + precision_titulo)
        if score > mejor_score:
            mejor_score = score
            mejor = ruta

    if mejor is None or mejor_score < 0.5:  # exige una coincidencia razonablemente fuerte de ambos lados
        return None

    texto = mejor.read_text(encoding="utf-8")
    return {"titulo": mejor.stem.replace("_", " "), "archivo": str(mejor), "texto": texto, "score": round(mejor_score, 2)}
