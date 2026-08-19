"""
Extrae y estructura una conversación de Intercom exportada en PDF.

Formato típico de exportación de Intercom (texto plano):

    Conversation with Dropi Colombia
    Started on July 21, 2026 at 12:10 PM Bogota time -05 (GMT-0500)
    --- July 21, 2026 ---
    12:10 PM | Juan Restrepo: Productos y proveedores
    12:10 PM | Gali: ¿Cómo te podemos ayudar hoy?
    ...
    11:57 AM | Stephany from Dropi Colombia: ¡Hola Juan Restrepo!
    ---
    Exported from Dropi Colombia on July 27, 2026 at 11:26 AM Bogota time -05 (GMT-0500)
"""
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

LINE_RE = re.compile(
    r"^(?P<time>\d{1,2}:\d{2}\s?[APap][Mm])\s*\|\s*(?P<sender>[^:]+):\s?(?P<text>.*)$"
)
DATE_HEADER_RE = re.compile(r"^---\s*(.+?)\s*---$")
STARTED_RE = re.compile(r"^Started on (.+?)(?: at (.+))?$")
EXPORTED_RE = re.compile(r"^Exported from (.+?) on (.+)$")

# Nombres que son bots / IA de Intercom y NUNCA deben contar como el asesor humano evaluado
BOTS_CONOCIDOS = {"gali"}


@dataclass
class Mensaje:
    fecha: str
    hora: str
    remitente: str
    es_staff: bool
    texto: str


@dataclass
class Conversacion:
    bandeja: Optional[str] = None
    iniciado: Optional[str] = None
    exportado: Optional[str] = None
    mensajes: list = field(default_factory=list)

    def remitentes_staff(self) -> dict:
        """Devuelve remitentes 'from Dropi Colombia' distintos, excluyendo bots conocidos."""
        vistos = {}
        for m in self.mensajes:
            if m.es_staff:
                key = m.remitente.strip().lower()
                if key not in BOTS_CONOCIDOS:
                    vistos.setdefault(m.remitente.strip(), 0)
                    vistos[m.remitente.strip()] += 1
        return vistos

    def texto_plano(self) -> str:
        """Serializa la conversación en un texto legible para pasar al modelo de evaluación."""
        lineas = []
        fecha_actual = None
        for m in self.mensajes:
            if m.fecha != fecha_actual:
                lineas.append(f"\n--- {m.fecha} ---")
                fecha_actual = m.fecha
            etiqueta = "[STAFF]" if m.es_staff else "[CLIENTE]"
            lineas.append(f"{m.hora} {etiqueta} {m.remitente}: {m.texto}")
        return "\n".join(lineas)


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae el texto plano de un PDF exportado de Intercom, página por página."""
    if pdfplumber is None:
        raise RuntimeError(
            "Falta la librería pdfplumber. Instálala con: pip install pdfplumber --break-system-packages"
        )
    texto_paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text() or ""
            texto_paginas.append(t)
    return "\n".join(texto_paginas)


def parsear_conversacion(texto: str) -> Conversacion:
    """Convierte el texto crudo del PDF en una Conversacion estructurada (mensajes con remitente, fecha y si es staff)."""
    conv = Conversacion()
    lineas = texto.split("\n")
    fecha_actual = None
    mensaje_actual = None

    for linea in lineas:
        linea = linea.rstrip()
        if not linea.strip():
            continue

        m_exportado = EXPORTED_RE.match(linea.strip())
        if m_exportado:
            conv.exportado = linea.strip()
            continue

        m_iniciado = STARTED_RE.match(linea.strip())
        if m_iniciado:
            conv.iniciado = linea.strip()
            continue

        m_fecha = DATE_HEADER_RE.match(linea.strip())
        if m_fecha:
            fecha_actual = m_fecha.group(1)
            continue

        m_msg = LINE_RE.match(linea.strip())
        if m_msg:
            remitente_raw = m_msg.group("sender").strip()
            es_staff = "from Dropi Colombia" in remitente_raw or remitente_raw.lower() in BOTS_CONOCIDOS
            remitente = remitente_raw.replace(" from Dropi Colombia", "").strip()
            mensaje_actual = Mensaje(
                fecha=fecha_actual or "",
                hora=m_msg.group("time").strip(),
                remitente=remitente,
                es_staff=es_staff,
                texto=m_msg.group("text").strip(),
            )
            conv.mensajes.append(mensaje_actual)
        else:
            # Línea de continuación del mensaje anterior (texto multilínea)
            if mensaje_actual is not None:
                mensaje_actual.texto += "\n" + linea.strip()

    return conv


def cargar_conversacion_desde_pdf(ruta_pdf: str) -> Conversacion:
    """Atajo: extrae el texto de un PDF y lo parsea en un solo paso."""
    texto = extraer_texto_pdf(ruta_pdf)
    return parsear_conversacion(texto)


# --- Detección automática de metadata (bandeja, ID de caso, país) ---

BANDEJAS_CONOCIDAS = [
    "Garantías", "Wallet", "Logística", "Transportadoras y envíos",
    "Productos y proveedores", "Tecnología", "Facturación",
]

ID_PATTERNS_TEXTO = [
    re.compile(r"ID\s+Garant[íi]a:?\s*(\d+)", re.IGNORECASE),
    re.compile(r"ID\s+Orden\s+Dropi:?\s*(\d+)", re.IGNORECASE),
    re.compile(r"ID\s+de\s+Orden:?\s*(\d+)", re.IGNORECASE),
]

PAISES_POR_PALABRA_CLAVE = {
    "bogota": "Colombia", "bogotá": "Colombia", "colombia": "Colombia",
    "ciudad de méxico": "México", "ciudad de mexico": "México", "méxico": "México",
    "lima": "Perú", "perú": "Perú", "peru": "Perú",
    "santiago": "Chile", "chile": "Chile",
    "buenos aires": "Argentina", "argentina": "Argentina",
    "quito": "Ecuador", "ecuador": "Ecuador",
    "panama": "Panamá", "panamá": "Panamá",
}

# Mapa país -> lista de fragmentos que pueden aparecer en el NOMBRE del archivo
# exportado (ej. "dropi_ecuador_2026_07_20_...pdf" -> Ecuador). Esta es la fuente
# CONFIABLE: el texto del cuerpo del PDF siempre dice "Dropi Colombia" y "Bogota
# time" sin importar el país real del cliente, porque toda la operación corre
# desde un único workspace de Intercom con sede en Colombia — así que buscar
# el país en el cuerpo del texto casi siempre da falsos positivos de "Colombia".
PAISES_POR_NOMBRE_ARCHIVO = {
    "colombia": "Colombia",
    "mexico": "México", "méxico": "México",
    "peru": "Perú", "perú": "Perú",
    "chile": "Chile",
    "argentina": "Argentina",
    "ecuador": "Ecuador",
    "panama": "Panamá", "panamá": "Panamá",
    "guatemala": "Guatemala",
    "venezuela": "Venezuela",
    "costarica": "Costa Rica", "costa_rica": "Costa Rica", "costa-rica": "Costa Rica",
    "honduras": "Honduras",
    "elsalvador": "El Salvador", "el_salvador": "El Salvador",
    "republicadominicana": "República Dominicana", "dominicana": "República Dominicana",
    "bolivia": "Bolivia",
    "paraguay": "Paraguay",
    "uruguay": "Uruguay",
    "nicaragua": "Nicaragua",
}


def _extraer_id_de_nombre_archivo(nombre_archivo: str) -> Optional[str]:
    """El nombre del PDF exportado suele terminar en el ID largo de la conversación
    (ej. dropi_colombia_2026_07_21_215475175505780.pdf -> 215475175505780)."""
    if not nombre_archivo:
        return None
    coincidencias = re.findall(r"\d{8,}", nombre_archivo)
    return coincidencias[-1] if coincidencias else None


def _extraer_pais_de_nombre_archivo(nombre_archivo: str) -> Optional[str]:
    """Busca un país conocido en el nombre del archivo (ej. dropi_ecuador_...pdf
    -> Ecuador). Es la fuente confiable de país; el cuerpo del PDF no lo es."""
    if not nombre_archivo:
        return None
    nombre_lower = nombre_archivo.lower()
    for fragmento, pais in PAISES_POR_NOMBRE_ARCHIVO.items():
        if fragmento in nombre_lower:
            return pais
    return None


def _detectar_bandeja_por_menu(conv: Conversacion) -> Optional[str]:
    """Fallback cuando no hay un patrón 'Bienvenido a X': busca la última opción de
    menú que el cliente eligió al principio del chat (mensajes cortos tipo botón,
    antes de que escriba su primera pregunta/mensaje libre)."""
    candidato = None
    for msg in conv.mensajes:
        if msg.es_staff:
            # Ya empezó a responder el bot/asesor: dejamos de buscar más candidatos
            if candidato:
                break
            continue
        texto = msg.texto.strip()
        if not texto or texto in ("Empezar de nuevo 🔁",):
            continue
        # Heurística: los clics de menú son frases cortas, sin signos de pregunta
        # ni puntos, y sin ser una oración larga en minúsculas (mensaje libre).
        parece_menu = (
            len(texto) <= 45
            and "?" not in texto
            and not texto.endswith(".")
            and texto[0].isupper()
        )
        if parece_menu:
            candidato = texto
        else:
            break  # llegó al primer mensaje libre: ya no sigue en el menú
    return candidato


def detectar_metadata(conv: Conversacion, texto_crudo: str, nombre_archivo: str = "") -> dict:
    """Intenta detectar bandeja, id_caso y país a partir del PDF. Cualquier campo
    que no se pueda determinar con confianza queda en None (el usuario lo completa)."""
    resultado = {"bandeja": None, "id_caso": None, "pais": None, "bandeja_es_sugerencia": False, "pais_es_sugerencia": False}

    # --- Bandeja: mensaje típico del bot "Bienvenido a <Bandeja>" ---
    m = re.search(r"Bienvenido a ([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ ]{2,40})", texto_crudo)
    if m:
        resultado["bandeja"] = m.group(1).strip().rstrip(".").strip()
    else:
        for msg in conv.mensajes[:6]:
            for b in BANDEJAS_CONOCIDAS:
                if b.lower() in msg.texto.lower():
                    resultado["bandeja"] = b
                    break
            if resultado["bandeja"]:
                break

    # --- Si no hubo señal clara, usar la última opción de menú como sugerencia ---
    if not resultado["bandeja"]:
        sugerido = _detectar_bandeja_por_menu(conv)
        if sugerido:
            resultado["bandeja"] = sugerido
            resultado["bandeja_es_sugerencia"] = True

    # --- ID del caso: primero el nombre del archivo (más confiable), luego el texto ---
    resultado["id_caso"] = _extraer_id_de_nombre_archivo(nombre_archivo)
    if not resultado["id_caso"]:
        for pat in ID_PATTERNS_TEXTO:
            m = pat.search(texto_crudo)
            if m:
                resultado["id_caso"] = m.group(1)
                break

    # --- País: primero el nombre del archivo (confiable); el cuerpo del texto
    # NO es confiable porque siempre dice "Dropi Colombia" / "Bogota time" sin
    # importar el país real del cliente, así que solo se usa como último recurso.
    resultado["pais"] = _extraer_pais_de_nombre_archivo(nombre_archivo)
    if not resultado["pais"]:
        texto_lower = texto_crudo.lower()
        for palabra, pais in PAISES_POR_PALABRA_CLAVE.items():
            if palabra in texto_lower:
                resultado["pais"] = pais
                resultado["pais_es_sugerencia"] = True
                break

    return resultado


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python pdf_parser.py <ruta_al_pdf>")
        sys.exit(1)
    conv = cargar_conversacion_desde_pdf(sys.argv[1])
    print("Remitentes staff detectados:", conv.remitentes_staff())
    print("\n--- Conversación estructurada ---")
    print(conv.texto_plano())
