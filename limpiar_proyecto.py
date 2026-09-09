#!/usr/bin/env python3
"""
Limpieza segura del proyecto Dropi QA.

Por defecto corre en modo SIMULACIÓN (no borra nada, solo muestra qué haría).
Para borrar de verdad: python limpiar_proyecto.py --confirmar

Qué hace:
1. Rescata los registros del historial que SOLO existen en archivos de backup
   (no están en historial_evaluaciones.json activo) a un archivo aparte, para
   no perderlos nunca.
2. Borra las carpetas backup_* de código.
3. Borra los archivos .backup sueltos.
4. Borra los historial_evaluaciones_backup_*.json (después de rescatar lo único).

Corre este script DESDE LA RAÍZ del proyecto (donde está historial_evaluaciones.json).
"""
import json
import glob
import shutil
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

CARPETAS_BACKUP = [
    "backup_fase2_20260824",
    "backup_fase3_20260824",
    "backup_informe_desempeno_20260831",
    "backup_informe_ejecutivo_v3_20260831",
    "backup_informe_seleccion_20260831",
]

ARCHIVOS_BACKUP_SUELTOS = [
    "src/blueprints/buscar_bp.py.backup",
    "src/coaching.py.backup",
    "templates/historial_detalle.html.backup",
    "templates/revisar_coaching.html.backup",
    "templates/coaching.html.backup",
    "README.md.backup",
]

HISTORIAL_ACTIVO = BASE / "historial_evaluaciones.json"
PATRON_BACKUPS_HISTORIAL = "historial_evaluaciones_backup*.json"
ARCHIVO_RESCATE = BASE / "historial_evaluaciones_registros_rescatados.json"


def rescatar_registros_huerfanos():
    """Guarda en un archivo aparte cualquier evaluación que exista SOLO en un
    backup y ya no esté en el historial activo, antes de borrar los backups."""
    if not HISTORIAL_ACTIVO.exists():
        print("⚠️  No encontré historial_evaluaciones.json aquí — "
              "¿estás corriendo esto desde la raíz del proyecto?")
        sys.exit(1)

    with open(HISTORIAL_ACTIVO, encoding="utf-8") as f:
        activo = json.load(f)
    ids_activos = {r.get("id_caso") for r in activo}

    rescatados = {}
    backups_historial = sorted(BASE.glob(PATRON_BACKUPS_HISTORIAL))
    for ruta in backups_historial:
        try:
            with open(ruta, encoding="utf-8") as f:
                backup = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"   (no pude leer {ruta.name}: {e})")
            continue
        if not isinstance(backup, list):
            continue
        for r in backup:
            id_caso = r.get("id_caso")
            if id_caso and id_caso not in ids_activos and id_caso not in rescatados:
                rescatados[id_caso] = r

    if rescatados:
        print(f"🛟 {len(rescatados)} evaluación(es) existen SOLO en backups (no en el historial activo):")
        for id_, r in rescatados.items():
            print(f"   - {id_} | {r.get('agente')} | {r.get('fecha')}")
        if CONFIRMAR:
            with open(ARCHIVO_RESCATE, "w", encoding="utf-8") as f:
                json.dump(list(rescatados.values()), f, ensure_ascii=False, indent=2)
            print(f"   ✅ Guardados en: {ARCHIVO_RESCATE.name}")
        else:
            print(f"   (en modo real, esto se guardaría en: {ARCHIVO_RESCATE.name})")
    else:
        print("✅ No hay evaluaciones huérfanas — todo lo de los backups ya está en el historial activo.")

    return backups_historial


def borrar_carpetas():
    print("\n📁 Carpetas backup_* de código:")
    for nombre in CARPETAS_BACKUP:
        ruta = BASE / nombre
        if not ruta.exists():
            print(f"   (no existe: {nombre})")
            continue
        if CONFIRMAR:
            shutil.rmtree(ruta)
            print(f"   🗑️  Borrada: {nombre}")
        else:
            print(f"   [simulación] se borraría: {nombre}")


def borrar_archivos_sueltos():
    print("\n📄 Archivos .backup sueltos:")
    for nombre in ARCHIVOS_BACKUP_SUELTOS:
        ruta = BASE / nombre
        if not ruta.exists():
            print(f"   (no existe: {nombre})")
            continue
        if CONFIRMAR:
            ruta.unlink()
            print(f"   🗑️  Borrado: {nombre}")
        else:
            print(f"   [simulación] se borraría: {nombre}")


def borrar_backups_historial(backups_historial):
    print("\n🗂️  Backups de historial_evaluaciones (ya rescatado lo único):")
    for ruta in backups_historial:
        if CONFIRMAR:
            ruta.unlink()
            print(f"   🗑️  Borrado: {ruta.name}")
        else:
            print(f"   [simulación] se borraría: {ruta.name}")


if __name__ == "__main__":
    print("=" * 70)
    print("LIMPIEZA DEL PROYECTO — modo:", "CONFIRMAR (borra de verdad)" if CONFIRMAR else "SIMULACIÓN (no borra nada)")
    print("=" * 70)

    backups_historial = rescatar_registros_huerfanos()
    borrar_carpetas()
    borrar_archivos_sueltos()
    borrar_backups_historial(backups_historial)

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python limpiar_proyecto.py --confirmar")
    else:
        print("✅ Limpieza completada.")
    print("=" * 70)
