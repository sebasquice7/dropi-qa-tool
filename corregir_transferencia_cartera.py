#!/usr/bin/env python3
"""
Corrige el falso positivo de 'transferencia_injustificada' cuando el asesor
redirige al cliente al WhatsApp oficial de Cartera.

Por defecto corre en modo SIMULACIÓN (no cambia nada, solo muestra qué haría).
Para aplicar de verdad: python corregir_transferencia_cartera.py --confirmar

Qué hace:
1. Agrega un campo "excepciones" al ítem crítico "transferencia_injustificada"
   en config/matriz_calidad.json.
2. Modifica src/evaluator.py para que esa excepción se incluya SIEMPRE en el
   prompt que recibe la IA, sin importar la bandeja del caso (a diferencia de
   las guías operativas, que solo aplican si la bandeja hace match).

Corre este script DESDE LA RAÍZ del proyecto (donde está config/ y src/).
"""
import json
import re
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

MATRIZ_PATH = BASE / "config" / "matriz_calidad.json"
EVALUATOR_PATH = BASE / "src" / "evaluator.py"

TEXTO_EXCEPCION = (
    "NO marcar este crítico cuando el asesor redirige al cliente al canal "
    "oficial de WhatsApp de Cartera para gestionar cualquier solicitud "
    "relacionada con Cartera (por ejemplo, congelación de cartera u otros "
    "trámites que dependen de esa área). Esto aplica sin importar en qué "
    "bandeja llegó el caso: por la alta demanda de estas solicitudes, es "
    "frecuente que el cliente no entre por el canal correcto y termine en "
    "Triage, Retiros, Facturación, Compliance u otra bandeja administrativa. "
    "Identificar que el caso es de Cartera y dirigir al cliente a ese canal "
    "oficial es el proceso correcto, no una transferencia injustificada."
)

CODIGO_ANTES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\"" for c in matriz["items_criticos"]
    )'''

CODIGO_DESPUES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\""
        + (f"\\n  EXCEPCIÓN (no marcar 'Sí' en estos casos, sin importar la bandeja): {c['excepciones']}" if c.get("excepciones") else "")
        for c in matriz["items_criticos"]
    )'''


def paso_1_matriz():
    print("\n1) config/matriz_calidad.json")
    if not MATRIZ_PATH.exists():
        print("   ⚠️  No encontré config/matriz_calidad.json — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    with open(MATRIZ_PATH, encoding="utf-8") as f:
        matriz = json.load(f)

    encontrado = False
    ya_tenia = False
    for c in matriz.get("items_criticos", []):
        if c.get("id") == "transferencia_injustificada":
            encontrado = True
            if c.get("excepciones"):
                ya_tenia = True
            else:
                c["excepciones"] = TEXTO_EXCEPCION

    if not encontrado:
        print("   ⚠️  No encontré el ítem 'transferencia_injustificada' en la matriz. Nada que hacer.")
        return

    if ya_tenia:
        print("   ✅ Ya tiene un campo 'excepciones' — no lo toco (evita duplicar/sobrescribir algo que ya editaste).")
        return

    print("   Se agregaría el campo 'excepciones' al ítem 'transferencia_injustificada'.")
    if CONFIRMAR:
        with open(MATRIZ_PATH, "w", encoding="utf-8") as f:
            json.dump(matriz, f, ensure_ascii=False, indent=2)
        print("   ✅ Guardado.")
    else:
        print("   [simulación] no se guardó nada todavía.")


def paso_2_evaluator():
    print("\n2) src/evaluator.py")
    if not EVALUATOR_PATH.exists():
        print("   ⚠️  No encontré src/evaluator.py — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    codigo = EVALUATOR_PATH.read_text(encoding="utf-8")

    if CODIGO_DESPUES.strip() in codigo:
        print("   ✅ El código ya tiene el cambio aplicado — no hago nada.")
        return

    if CODIGO_ANTES.strip() not in codigo:
        print("   ⚠️  No encontré el bloque de código esperado (criticos_desc).")
        print("       Puede que ya lo hayas editado a mano, o que el archivo cambió.")
        print("       Revisa manualmente la función _construir_prompt en evaluator.py.")
        return

    print("   Se reemplazaría el bloque 'criticos_desc' para incluir las excepciones.")
    if CONFIRMAR:
        nuevo_codigo = codigo.replace(CODIGO_ANTES.strip(), CODIGO_DESPUES.strip())
        EVALUATOR_PATH.write_text(nuevo_codigo, encoding="utf-8")
        print("   ✅ Guardado.")
    else:
        print("   [simulación] no se guardó nada todavía.")


if __name__ == "__main__":
    print("=" * 70)
    print("CORRECCIÓN: transferencia_injustificada / WhatsApp Cartera — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    paso_1_matriz()
    paso_2_evaluator()

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_transferencia_cartera.py --confirmar")
        print("\nDespués de aplicar, corre los tests para confirmar que nada se rompió:")
        print("   python3 -m pytest tests/ -q")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python3 -m pytest tests/ -q")
        print("(deberías seguir viendo '63 passed')")
    print("=" * 70)
