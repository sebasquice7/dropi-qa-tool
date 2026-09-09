#!/usr/bin/env python3
"""
Conecta los campos "excepciones" y "senales_deteccion" del JSON de la matriz
con el prompt real que recibe la IA. Los campos ya existen en
config/matriz_calidad.json (para transferencia_injustificada e
informacion_falsa_enganosa), pero el código que arma criticos_desc en
src/evaluator.py nunca los leía — así que hasta ahora esas instrucciones
NUNCA le llegaban a la IA, aunque el JSON se viera bien.

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python conectar_senales_criticos.py --confirmar

Corre este script DESDE LA RAÍZ del proyecto (donde está src/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

RUTA = BASE / "src" / "evaluator.py"

CODIGO_ANTES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\"" for c in matriz["items_criticos"]
    )'''

CODIGO_DESPUES = '''    criticos_desc = "\\n".join(
        f"- id: \\"{c['id']}\\" | \\"{c['nombre']}\\""
        + (f"\\n  EXCEPCIÓN (no marcar 'Sí' en estos casos, sin importar la bandeja): {c['excepciones']}" if c.get("excepciones") else "")
        + (f"\\n  CÓMO DETECTARLO: {c['senales_deteccion']}" if c.get("senales_deteccion") else "")
        for c in matriz["items_criticos"]
    )'''


if __name__ == "__main__":
    print("=" * 70)
    print("CONECTAR: excepciones/senales_deteccion al prompt real — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    print("\nsrc/evaluator.py")
    if not RUTA.exists():
        print("   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    codigo = RUTA.read_text(encoding="utf-8")

    if CODIGO_DESPUES.strip() in codigo:
        print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
    elif CODIGO_ANTES.strip() not in codigo:
        print("   ⚠️  No encontré el bloque de código esperado (criticos_desc).")
        print("       Puede que ya lo hayas editado a mano con otro texto.")
        print("       Pégame el resultado de: sed -n '98,112p' src/evaluator.py")
    else:
        print("   Se actualizaría 'criticos_desc' para que incluya las")
        print("   'excepciones' y 'senales_deteccion' de cada ítem crítico")
        print("   en el prompt real que recibe la IA.")
        if CONFIRMAR:
            nuevo = codigo.replace(CODIGO_ANTES.strip(), CODIGO_DESPUES.strip())
            RUTA.write_text(nuevo, encoding="utf-8")
            print("   ✅ Guardado.")
        else:
            print("   [simulación] no se guardó nada todavía.")

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python conectar_senales_criticos.py --confirmar")
        print("\nDespués de aplicar, corre los tests Y la validación con IA real:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
    print("=" * 70)
