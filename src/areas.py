"""Agrupa las bandejas en áreas más amplias (Logística, Administrativo,
Comercial, Garantías, Soporte Técnico, Triage) y da acceso al roster de
asesores (qué proceso/bandeja maneja cada uno, y en qué país).

Los datos vienen de config/areas_bandejas.json y config/roster_asesores.json,
extraídos del mapa operativo real de SAC LATAM.
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AREAS_PATH = BASE_DIR / "config" / "areas_bandejas.json"
ROSTER_PATH = BASE_DIR / "config" / "roster_asesores.json"
SINONIMOS_PATH = BASE_DIR / "config" / "bandejas_sinonimos.json"

AREAS_DISPONIBLES = ["TRIAGE", "LOGISTICA", "ADMINISTRATIVO", "COMERCIAL", "GARANTÍAS", "SOPORTE TÉCNICO"]


def _limpiar_bandeja(bandeja: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", bandeja or "").strip()


def _sin_tildes(texto: str) -> str:
    texto = (texto or "").strip().lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        texto = texto.replace(a, b)
    return " ".join(texto.split())


def _cargar_mapa_sinonimos() -> dict:
    """Carga config/bandejas_sinonimos.json: {variante_normalizada: nombre_canónico}
    — para errores de tipeo reales (ej. 'Traige' en vez de 'Triage'), que no
    son solo tildes/mayúsculas. Compartido con dashboard_data.py, para que el
    filtro de bandeja y el de área agrupen exactamente las mismas variantes."""
    if not SINONIMOS_PATH.exists():
        return {}
    try:
        with open(SINONIMOS_PATH, encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    mapa = {}
    for grupo in datos.get("grupos", []):
        canonico = grupo["canonico"]
        for variante in grupo["variantes"]:
            mapa[_sin_tildes(_limpiar_bandeja(variante))] = canonico
    return mapa


def normalizar_bandeja(bandeja: str) -> str:
    """Forma 'canónica' de una bandeja: primero revisa si coincide con un
    sinónimo explícito (error de tipeo real), y si no, agrupa solo por
    tildes/mayúsculas/espacios."""
    base = _sin_tildes(_limpiar_bandeja(bandeja))
    canonico = _cargar_mapa_sinonimos().get(base)
    return _sin_tildes(canonico) if canonico else base


def nombre_canonico_si_existe(bandeja: str) -> str:
    """Si esta bandeja coincide con un sinónimo explícito conocido (ej.
    'Traige general'), devuelve el nombre canónico bien escrito ('Triage
    General'). Si no coincide con ningún sinónimo, devuelve None."""
    base = _sin_tildes(_limpiar_bandeja(bandeja))
    return _cargar_mapa_sinonimos().get(base)


def _cargar_mapa_areas() -> dict:
    """Carga config/areas_bandejas.json, normalizando sus claves (sin tildes)
    al vuelo — así da igual si el archivo tiene 'garantías' o 'garantias'
    guardado, siempre va a coincidir con normalizar_bandeja()."""
    with open(AREAS_PATH, encoding="utf-8") as f:
        mapa_crudo = json.load(f)
    return {_sin_tildes(clave): valor for clave, valor in mapa_crudo.items()}


def area_de_bandeja(bandeja: str) -> str:
    """Devuelve el área a la que pertenece una bandeja (ej. 'Anulaciones' ->
    'LOGISTICA'), o 'SIN CLASIFICAR' si no hay ninguna coincidencia — nunca
    inventa un área, para no mostrar una agrupación incorrecta.

    Reconoce variantes con errores de tipeo o tildes distintas (ej. 'Traige
    general', 'Triage General', y 'Triage' se tratan como la misma bandeja)."""
    if not bandeja:
        return "SIN CLASIFICAR"
    mapa = _cargar_mapa_areas()
    clave = normalizar_bandeja(bandeja)
    return mapa.get(clave, "SIN CLASIFICAR")


def cargar_roster() -> list:
    """Lista completa: cada registro es {pais, nombre, email, bandeja, area}."""
    with open(ROSTER_PATH, encoding="utf-8") as f:
        return json.load(f)


def roster_por_area(area: str = None, pais: str = None) -> list:
    """Roster filtrado, opcionalmente por área y/o país."""
    roster = cargar_roster()
    if area:
        roster = [r for r in roster if r["area"] == area.upper()]
    if pais:
        roster = [r for r in roster if r["pais"].lower() == pais.lower()]
    return roster


def areas_de_asesor(nombre_asesor: str) -> list:
    """Todas las áreas/bandejas/países en los que aparece un asesor específico
    (algunos manejan más de una bandeja)."""
    roster = cargar_roster()
    return [r for r in roster if r["nombre"].strip().lower() == nombre_asesor.strip().lower()]


def asesores_detectados_en_historial() -> list:
    """El mapa operativo (roster_asesores.json) se actualiza a mano, así que
    siempre va a estar un paso atrás de la realidad — un asesor nuevo puede
    empezar a evaluarse antes de que alguien actualice el Excel y te lo
    comparta. Esta función busca en el HISTORIAL REAL de evaluaciones
    cualquier combinación (asesor, bandeja, país) que no esté todavía en el
    roster oficial, y la devuelve por separado — para que el equipo la vea
    y decida si confirmarla en el mapa operativo oficial, sin tener que
    esperar a la próxima actualización manual del Excel.

    Nunca modifica roster_asesores.json directamente — solo lo complementa
    en la pantalla, para no mezclar datos confirmados con datos detectados."""
    try:
        from historial import cargar_historial
    except ImportError:
        return []

    roster = cargar_roster()
    combos_conocidos = {
        (r["nombre"].strip().lower(), (r["bandeja"] or "").strip().lower(), r["pais"].strip().lower())
        for r in roster
    }

    vistos = set()
    detectados = []
    for r in cargar_historial():
        agente = (r.get("agente") or "").strip()
        bandeja = (r.get("bandeja") or "").strip()
        pais = (r.get("pais") or "").strip()
        if not agente or not bandeja or not pais:
            continue

        clave = (agente.lower(), bandeja.lower(), pais.lower())
        if clave in combos_conocidos or clave in vistos:
            continue
        vistos.add(clave)

        detectados.append({
            "pais": pais, "nombre": agente, "bandeja": bandeja,
            "area": area_de_bandeja(bandeja),
        })

    return sorted(detectados, key=lambda d: (d["pais"], d["nombre"]))
