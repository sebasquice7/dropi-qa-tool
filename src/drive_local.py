"""Guarda copias del Excel y Word generados dentro de la carpeta local de
Google Drive (sincronizada por la app 'Google Drive para escritorio'), organizadas
en subcarpetas por asesor y por caso: <DRIVE_SYNC_FOLDER>/[DRIVE_SUBFOLDER/]<Asesor>/<ID>_<Asesor>/

No usa ninguna API de Google: simplemente copia los archivos a una ruta de disco
que la app de Google Drive vigila y sincroniza sola a la nube.
"""
import os
import re
import shutil
from pathlib import Path

from config import config
from logging_config import obtener_logger

log = obtener_logger("drive_local")


def _sanitizar_nombre(texto: str) -> str:
    """Quita caracteres no válidos para nombres de carpeta/archivo."""
    texto = (texto or "").strip()
    texto = re.sub(r'[\\/:*?"<>|]', "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto or "Sin_nombre"


def _resolver_ruta_tolerante(ruta: Path) -> Path:
    """
    Si 'ruta' no existe tal cual, intenta encontrarla nivel por nivel comparando
    nombres de carpeta SIN importar espacios sobrantes al inicio/final (algo común
    en carpetas de Google Drive, y que además .env recorta al leer la variable).

    Recorre desde la raíz existente conocida hacia abajo, buscando en cada nivel
    una carpeta cuyo nombre coincida ignorando espacios extremos.
    """
    if ruta.exists():
        return ruta

    partes = ruta.parts
    actual = Path(partes[0])
    for parte in partes[1:]:
        candidato = actual / parte
        if candidato.exists():
            actual = candidato
            continue
        # Buscar en el directorio actual una carpeta cuyo nombre, sin espacios
        # extremos, coincida con la parte buscada (también sin espacios extremos)
        encontrado = None
        if actual.exists() and actual.is_dir():
            objetivo = parte.strip()
            for hijo in actual.iterdir():
                if hijo.name.strip() == objetivo:
                    encontrado = hijo
                    break
        if encontrado is None:
            return ruta  # no se pudo resolver; se reporta la ruta original como error
        actual = encontrado
    return actual


def _resolver_base() -> tuple:
    """Devuelve (base_path resuelta, error_o_None)."""
    base = config.drive_sync_folder.strip()
    if not base:
        return None, "DRIVE_SYNC_FOLDER no está configurado en el .env"

    base_path = Path(base).expanduser()
    base_path = _resolver_ruta_tolerante(base_path)
    if not base_path.exists():
        return None, f"La ruta configurada no existe: {base_path}"
    return base_path, None


def guardar_en_drive(ruta_excel: str, ruta_word: str, asesor: str, id_caso: str, pais: str = "") -> dict:
    """
    Copia ruta_excel y ruta_word a:
        <DRIVE_SYNC_FOLDER>/[DRIVE_SUBFOLDER/]<Pais-Asesor>/<id_caso>_<asesor>/

    Lee la carpeta base desde DRIVE_SYNC_FOLDER (.env). Opcionalmente, DRIVE_SUBFOLDER
    agrega una capa intermedia (ej. si DRIVE_SYNC_FOLDER ya es la carpeta específica
    compartida por tu jefe, deja DRIVE_SUBFOLDER vacío o sin definir para guardar
    directo ahí, sin carpeta extra).

    Si DRIVE_SYNC_FOLDER no está configurado, no hace nada (devuelve ok=False sin
    lanzar error, para no romper el flujo principal de generación de documentos).
    """
    base_path, error = _resolver_base()
    if error:
        return {"ok": False, "motivo": error}

    subcarpeta = config.drive_subfolder.strip()

    asesor_limpio = _sanitizar_nombre(asesor)
    id_limpio = _sanitizar_nombre(id_caso or "sin_id")
    pais_limpio = _sanitizar_nombre(pais) if pais else ""

    nombre_carpeta_asesor = f"{pais_limpio}-{asesor_limpio}" if pais_limpio else asesor_limpio

    if subcarpeta:
        carpeta_destino = base_path / subcarpeta / nombre_carpeta_asesor / f"{id_limpio}_{asesor_limpio}"
    else:
        carpeta_destino = base_path / nombre_carpeta_asesor / f"{id_limpio}_{asesor_limpio}"

    carpeta_destino.mkdir(parents=True, exist_ok=True)

    copiados = []
    for ruta_origen in (ruta_excel, ruta_word):
        if ruta_origen and Path(ruta_origen).exists():
            destino = carpeta_destino / Path(ruta_origen).name
            shutil.copy2(ruta_origen, destino)
            copiados.append(str(destino))

    return {"ok": True, "carpeta": str(carpeta_destino), "archivos": copiados}


def guardar_archivo_suelto_en_drive(ruta_archivo: str, subcarpeta_nombre: str = "") -> dict:
    """
    Guarda un único archivo (ej. el informe consolidado de KPIs) directo en la
    carpeta base configurada, sin anidar por asesor/caso. Si subcarpeta_nombre
    se especifica, lo guarda dentro de esa subcarpeta (se crea si no existe).
    """
    base_path, error = _resolver_base()
    if error:
        return {"ok": False, "motivo": error}

    destino_dir = base_path / _sanitizar_nombre(subcarpeta_nombre) if subcarpeta_nombre else base_path
    destino_dir.mkdir(parents=True, exist_ok=True)

    if not ruta_archivo or not Path(ruta_archivo).exists():
        return {"ok": False, "motivo": f"El archivo a guardar no existe: {ruta_archivo}"}

    destino = destino_dir / Path(ruta_archivo).name
    shutil.copy2(ruta_archivo, destino)

    return {"ok": True, "carpeta": str(destino_dir), "archivos": [str(destino)]}


def respaldar_historial_en_drive(ruta_historial: str) -> dict:
    """Copia el historial local a Drive tras cada evaluación registrada, para
    no perderlo si falla el disco local. Nunca lanza una excepción — como
    mucho, devuelve ok=False y queda registrado en el log."""
    try:
        resultado = guardar_archivo_suelto_en_drive(ruta_historial, subcarpeta_nombre="Respaldo Historial")
        if resultado.get("ok"):
            log.info("Respaldo del historial actualizado en Drive: %s", resultado["carpeta"])
        else:
            log.warning("No se pudo respaldar el historial en Drive: %s", resultado.get("motivo"))
        return resultado
    except Exception as e:
        log.warning("No se pudo respaldar el historial en Drive: %s", e)
        return {"ok": False, "motivo": str(e)}
