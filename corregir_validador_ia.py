#!/usr/bin/env python3
"""
Corrige el script de validación (pruebas_validacion_ia/validar_ia.py):
NUNCA pasaba el parámetro texto_gali al evaluar los casos de prueba, así que
la base de conocimiento oficial (FAQs) estuvo completamente desactivada en
TODAS las corridas de validación hechas hasta ahora — sin importar cuántas
veces se corrigiera el mecanismo en evaluator.py / evaluacion_service.py.

Esto explica por qué "Información técnica incorrecta / inventada" seguía
fallando después de 3 correcciones distintas: nunca se estaba probando con
la corrección real activa. La corrección en sí (aplicada por
corregir_faqs_alcance.py) probablemente SÍ funciona en la app real, donde
evaluacion_service.py sí pasa texto_gali correctamente — este script arregla
el instrumento de medición para poder confirmarlo con evidencia real.

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_validador_ia.py --confirmar

Corre este script DESDE LA RAÍZ del proyecto (donde está pruebas_validacion_ia/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

RUTA = BASE / "pruebas_validacion_ia" / "validar_ia.py"

CODIGO_ANTES = '''            evaluacion = evaluar_conversacion(
                caso["texto"], caso["asesor"], pais=caso["pais"], bandeja=caso["bandeja"],
            )'''

CODIGO_DESPUES = '''            evaluacion = evaluar_conversacion(
                caso["texto"], caso["asesor"], pais=caso["pais"], bandeja=caso["bandeja"],
                texto_gali=caso["texto"],
            )'''


if __name__ == "__main__":
    print("=" * 70)
    print("CORRECCIÓN: validar_ia.py no pasaba texto_gali — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    print(f"\npruebas_validacion_ia/validar_ia.py")
    if not RUTA.exists():
        print("   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    codigo = RUTA.read_text(encoding="utf-8")

    if CODIGO_DESPUES.strip() in codigo:
        print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
    elif CODIGO_ANTES.strip() not in codigo:
        print("   ⚠️  No encontré el bloque de código esperado.")
        print("       Puede que ya lo hayas editado a mano. Revisa manualmente")
        print("       que la llamada a evaluar_conversacion() en validar_ia.py")
        print("       incluya texto_gali=caso[\"texto\"].")
    else:
        print("   Se agregaría texto_gali=caso[\"texto\"] a la llamada de evaluar_conversacion.")
        if CONFIRMAR:
            nuevo = codigo.replace(CODIGO_ANTES.strip(), CODIGO_DESPUES.strip())
            RUTA.write_text(nuevo, encoding="utf-8")
            print("   ✅ Guardado.")
        else:
            print("   [simulación] no se guardó nada todavía.")

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_validador_ia.py --confirmar")
        print("\nDespués de aplicar, corre la validación con IA real:")
        print("   python pruebas_validacion_ia/validar_ia.py")
        print("\nEsta vez la base de conocimiento SÍ va a estar activa durante la prueba.")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python pruebas_validacion_ia/validar_ia.py")
        print("\nSi 'Información técnica incorrecta' sigue fallando CON esto activo,")
        print("ahí sí tendríamos evidencia real de un límite del modelo, no del código.")
    print("=" * 70)
