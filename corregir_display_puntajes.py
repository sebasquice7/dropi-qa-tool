#!/usr/bin/env python3
"""
Mejora de UX en la pantalla de revisión (revisar.html): el campo donde se
escribe el puntaje de cada ítem mostraba el valor en escala decimal (ej.
"0.0315"), mientras que la etiqueta de al lado muestra el máximo en
porcentaje (ej. "(máx 3.5%)") — dos unidades distintas para el mismo
número, obligando a convertir mentalmente cada vez.

Ahora el campo visible se muestra y se edita en las MISMAS unidades que la
etiqueta (ej. escribes "3.1" en vez de "0.031"), con un "%" al lado para
que quede explícito. Por debajo, un campo oculto sigue enviando al
servidor exactamente el mismo valor decimal que antes (0 cambios en
evaluacion_bp.py ni en ningún otro código del servidor) — se actualiza
solo con JavaScript cada vez que se escribe en el campo visible.

Verificado con Playwright (navegador real) antes de entregar esto: el
campo oculto calcula bien el valor al escribir, y si no se toca nada el
valor por defecto sigue siendo el que ya traía la evaluación.

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_display_puntajes.py --confirmar

Requiere haber aplicado antes corregir_visualizacion_peso.py.

Corre este script DESDE LA RAÍZ del proyecto (donde está templates/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

RUTA = BASE / "templates" / "revisar.html"

CODIGO_ANTES = '<input type="number" step="0.001" min="0" max="{{ it.peso }}" name="puntaje__{{ it.id }}" value="{{ ev.puntaje }}">'

CODIGO_DESPUES = '''<div style="display:flex;align-items:center;gap:3px;justify-content:center;">
          <input type="number" step="0.1" min="0" max="{{ (it.peso*100)|round(2) }}" style="width:62px;"
                 value="{{ ((ev.puntaje or 0)*100)|round(2) }}"
                 oninput="document.getElementById('h_puntaje__{{ it.id }}').value=(parseFloat(this.value||0)/100).toFixed(5)">
          <span style="color:var(--ink-400);font-size:12px;">%</span>
          <input type="hidden" id="h_puntaje__{{ it.id }}" name="puntaje__{{ it.id }}" value="{{ ev.puntaje or 0 }}">
        </div>'''


if __name__ == "__main__":
    print("=" * 70)
    print("MEJORA DE UX: puntaje mostrado en % (igual que el máximo) — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    print("\ntemplates/revisar.html")
    if not RUTA.exists():
        print("   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
        sys.exit(1)

    codigo = RUTA.read_text(encoding="utf-8")

    if CODIGO_DESPUES.strip() in codigo:
        print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
    elif CODIGO_ANTES not in codigo:
        print("   ⚠️  No encontré la línea esperada del input de puntaje.")
        print("       Puede que ya la hayas editado a mano. Revisa manualmente.")
    else:
        print("   Se cambiaría el campo de puntaje para mostrarse en % en vez")
        print("   de decimal (ej. '3.1%' en vez de '0.031'), sin tocar el valor")
        print("   que realmente se envía al servidor.")
        if CONFIRMAR:
            nuevo = codigo.replace(CODIGO_ANTES, CODIGO_DESPUES)
            RUTA.write_text(nuevo, encoding="utf-8")
            print("   ✅ Guardado.")
        else:
            print("   [simulación] no se guardó nada todavía.")

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_display_puntajes.py --confirmar")
    else:
        print("✅ Corrección aplicada. Reinicia 'python app.py', abre una")
        print("   evaluación para revisar y confirma que los campos de puntaje")
        print("   ahora muestran un número pequeño con '%' al lado (ej. '9.0 %'")
        print("   para un ítem con máx 10%), en vez del decimal crudo.")
        print("   El valor que se guarda al final es exactamente el mismo de antes.")
    print("=" * 70)
