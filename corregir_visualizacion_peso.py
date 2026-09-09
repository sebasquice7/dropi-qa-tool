#!/usr/bin/env python3
"""
Corrige un bug de visualización en la pantalla de revisión (revisar.html):
la etiqueta "(máx X%)" junto a cada ítem redondeaba el peso a un número
entero, así que un ítem con peso real de 3.5% (0.035) se mostraba como
"(máx 4%)" — pero el campo de puntaje sí valida contra el 3.5% real, por
lo que al intentar poner 0.04 (siguiendo la etiqueta) el sistema lo
rechazaba con "El valor debe ser menor o igual a 0.035", una contradicción
confusa entre lo que se muestra y lo que se valida.

Afecta a 4 ítems de la matriz actual (los que terminan en ",5%"):
- Lectura y Validación de Datos Recopilados por Gali (7.5%, mostraba 8%)
- Continuidad en el Hilo de Conversación (7.5%, mostraba 8%)
- Carga de Evidencias y Soporte Visual (3.5%, mostraba 4%)
- Documentación de Notas Internas y Tipificación (3.5%, mostraba 4%)

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_visualizacion_peso.py --confirmar

Corre este script DESDE LA RAÍZ del proyecto (donde está templates/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

RUTA = BASE / "templates" / "revisar.html"

CODIGO_ANTES = '<div class="item-nombre">{{ it.nombre }} <span class="item-peso">(máx {{ (it.peso*100)|round(0)|int }}%)</span>'
CODIGO_DESPUES = '<div class="item-nombre">{{ it.nombre }} <span class="item-peso">(máx {{ ("%.1f"|format(it.peso*100))|replace(".0", "") }}%)</span>'


if __name__ == "__main__":
    print("=" * 70)
    print("CORRECCIÓN: etiqueta de máximo por ítem redondeaba mal (3.5%→4%) — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    print("\ntemplates/revisar.html")
    if not RUTA.exists():
        print("   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    codigo = RUTA.read_text(encoding="utf-8")

    if CODIGO_DESPUES in codigo:
        print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
    elif CODIGO_ANTES not in codigo:
        print("   ⚠️  No encontré la línea esperada. Puede que ya la hayas editado")
        print("       a mano. Revisa manualmente la línea de '(máx {{ ... }}%)'")
        print("       en templates/revisar.html.")
    else:
        print("   Se corregiría la etiqueta para mostrar decimales cuando aplique")
        print("   (ej. '3.5%' en vez de '4%').")
        if CONFIRMAR:
            nuevo = codigo.replace(CODIGO_ANTES, CODIGO_DESPUES)
            RUTA.write_text(nuevo, encoding="utf-8")
            print("   ✅ Guardado.")
        else:
            print("   [simulación] no se guardó nada todavía.")

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_visualizacion_peso.py --confirmar")
    else:
        print("✅ Corrección aplicada. Refresca la pantalla de revisión en el")
        print("   navegador (puede que necesites reiniciar 'python app.py')")
        print("   y confirma que 'Carga de Evidencias y Soporte Visual' ahora")
        print("   muestra '(máx 3.5%)' en vez de '(máx 4%)'.")
    print("=" * 70)
