#!/usr/bin/env python3
"""
Parte 3 de la corrección de detección de información falsa — le da a
"informacion_falsa_enganosa" el mismo nivel de instrucción explícita que ya
tienen "transferencia_injustificada" (excepción) y "cierre_prematuro_
abandono" (regla de horas). Era el único de los 5 críticos sin ninguna guía
específica, solo el criterio general de "sé conservador".

Requiere haber aplicado antes corregir_faqs_alcance.py y
corregir_faqs_precision.py (para que la base de conocimiento realmente
llegue con la referencia correcta).

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_informacion_falsa.py --confirmar

Qué hace (2 archivos):
1. config/matriz_calidad.json — agrega un campo "senales_deteccion" al ítem
   "informacion_falsa_enganosa": si la Base de Conocimiento Oficial
   contradice un dato que dio el asesor, eso ya es evidencia suficiente.
2. src/evaluator.py — generaliza el mecanismo que ya existía para
   "excepciones" (usado por transferencia_injustificada) para que también
   soporte "senales_deteccion", y lo aplica en la construcción del prompt.

Corre este script DESDE LA RAÍZ del proyecto (donde está config/ y src/).
"""
import json
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

MATRIZ_PATH = BASE / "config" / "matriz_calidad.json"
EVALUATOR_PATH = BASE / "src" / "evaluator.py"

TEXTO_SENAL = (
    'Si el bloque "BASE DE CONOCIMIENTO OFICIAL" (más abajo) muestra una '
    "respuesta oficial que CONTRADICE claramente un dato, plazo, política o "
    "procedimiento que el asesor le comunicó al cliente como si fuera "
    "correcto, marca \"Sí\" — esa contradicción es evidencia suficiente por sí "
    "sola, incluso si el resto de la conversación se ve bien manejada y el "
    "tono es correcto. No necesitas otra señal adicional: una afirmación "
    "del asesor que choque con la fuente oficial ya es información falsa o "
    "engañosa, sin importar si parece un error honesto o intencional."
)

CODIGO_ANTES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\""
        + (f"\\n  EXCEPCIÓN (no marcar 'Sí' en estos casos, sin importar la bandeja): {c['excepciones']}" if c.get("excepciones") else "")
        for c in matriz["items_criticos"]
    )'''

CODIGO_DESPUES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\""
        + (f"\\n  EXCEPCIÓN (no marcar 'Sí' en estos casos, sin importar la bandeja): {c['excepciones']}" if c.get("excepciones") else "")
        + (f"\\n  CÓMO DETECTARLO: {c['senales_deteccion']}" if c.get("senales_deteccion") else "")
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
        if c.get("id") == "informacion_falsa_enganosa":
            encontrado = True
            if c.get("senales_deteccion"):
                ya_tenia = True
            else:
                c["senales_deteccion"] = TEXTO_SENAL

    if not encontrado:
        print("   ⚠️  No encontré el ítem 'informacion_falsa_enganosa' en la matriz. Nada que hacer.")
        return

    if ya_tenia:
        print("   ✅ Ya tiene un campo 'senales_deteccion' — no lo toco.")
        return

    print("   Se agregaría el campo 'senales_deteccion' al ítem 'informacion_falsa_enganosa'.")
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
        print("       Puede que ya lo hayas editado a mano, o que falte aplicar")
        print("       primero corregir_transferencia_cartera.py. Revisa manualmente.")
        return

    print("   Se reemplazaría el bloque 'criticos_desc' para soportar también 'senales_deteccion'.")
    if CONFIRMAR:
        nuevo_codigo = codigo.replace(CODIGO_ANTES.strip(), CODIGO_DESPUES.strip())
        EVALUATOR_PATH.write_text(nuevo_codigo, encoding="utf-8")
        print("   ✅ Guardado.")
    else:
        print("   [simulación] no se guardó nada todavía.")


if __name__ == "__main__":
    print("=" * 70)
    print("CORRECCIÓN: guía de detección para informacion_falsa_enganosa — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    paso_1_matriz()
    paso_2_evaluator()

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_informacion_falsa.py --confirmar")
        print("\nDespués de aplicar, corre los tests Y la validación con IA real:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
        print("(esperamos que 'Información técnica incorrecta / inventada' pase a ✅)")
    print("=" * 70)
