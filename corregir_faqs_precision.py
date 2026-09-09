#!/usr/bin/env python3
"""
Parte 2 de la corrección de FAQs — corrige el ruido que introdujo abrir la
búsqueda a toda la conversación (corregir_faqs_alcance.py): las 'tags' de
muchas preguntas de garantías son idénticas entre sí, así que cualquier
conversación sobre garantías traía casi todas las preguntas del tema por
igual, incluyendo alguna que no aplicaba y podía confundir a la IA (ej. el
plazo de respuesta del PROVEEDOR mezclado con el plazo de cierre por
inactividad del CLIENTE, que son reglas completamente distintas).

Requiere haber aplicado antes corregir_faqs_alcance.py.

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_faqs_precision.py --confirmar

Qué hace (2 archivos):
1. src/faqs_gali_buscador.py — re-balancea el peso de tags/pregunta/
   variaciones (antes las tags, poco específicas, pesaban más que la
   pregunta real) y reduce de 8 a 4 el máximo de resultados devueltos.
2. src/evaluator.py — aclara explícitamente en el prompt que la regla de
   cierre por inactividad se rige ÚNICAMENTE por la política de SLA, y que
   otros plazos que aparezcan en la base de conocimiento (ej. tiempo de
   respuesta del proveedor) no deben confundirse con esa regla.

Corre este script DESDE LA RAÍZ del proyecto (donde está src/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

CAMBIOS = [
    {
        "archivo": "src/faqs_gali_buscador.py",
        "antes": '''    palabras_tags = _palabras_clave(entrada.get("tags", ""))
    if palabras_tags:
        comunes = palabras_conversacion & palabras_tags
        palabras_en_comun |= comunes
        score += 3.0 * len(comunes) / len(palabras_tags)

    palabras_variaciones = _palabras_clave(entrada.get("variaciones", ""))
    if palabras_variaciones:
        comunes = palabras_conversacion & palabras_variaciones
        palabras_en_comun |= comunes
        score += 2.0 * len(comunes) / len(palabras_variaciones)

    palabras_pregunta = _palabras_clave(entrada.get("pregunta", ""))
    if palabras_pregunta:
        comunes = palabras_conversacion & palabras_pregunta
        palabras_en_comun |= comunes
        score += 1.0 * len(comunes) / len(palabras_pregunta)''',
        "despues": '''    palabras_pregunta = _palabras_clave(entrada.get("pregunta", ""))
    if palabras_pregunta:
        comunes = palabras_conversacion & palabras_pregunta
        palabras_en_comun |= comunes
        score += 2.5 * len(comunes) / len(palabras_pregunta)

    palabras_variaciones = _palabras_clave(entrada.get("variaciones", ""))
    if palabras_variaciones:
        comunes = palabras_conversacion & palabras_variaciones
        palabras_en_comun |= comunes
        score += 2.5 * len(comunes) / len(palabras_variaciones)

    palabras_tags = _palabras_clave(entrada.get("tags", ""))
    if palabras_tags:
        comunes = palabras_conversacion & palabras_tags
        palabras_en_comun |= comunes
        score += 1.0 * len(comunes) / len(palabras_tags)''',
    },
    {
        "archivo": "src/faqs_gali_buscador.py",
        "antes": 'def buscar_faqs_relevantes(texto_conversacion: str, entradas_pais: list, top_n: int = 8, umbral_minimo: float = 0.35) -> list:',
        "despues": 'def buscar_faqs_relevantes(texto_conversacion: str, entradas_pais: list, top_n: int = 4, umbral_minimo: float = 0.35) -> list:',
    },
    {
        "archivo": "src/faqs_gali_buscador.py",
        "antes": 'def contexto_faqs_gali(texto_de_gali: str, pais: str, top_n: int = 8) -> str:',
        "despues": 'def contexto_faqs_gali(texto_de_gali: str, pais: str, top_n: int = 4) -> str:',
    },
    {
        "archivo": "src/evaluator.py",
        "antes": '8. CIERRE VÁLIDO vs. ABANDONO ("cierra_sin_resolver"): usa la regla fija de "Cierre por inactividad del cliente" de la política de SLA (arriba): el asesor puede cerrar válidamente tras 4 horas de tiempo LABORAL de silencio del cliente después de una gestión clara, siempre que haya avisado antes de cerrar. Marca este ítem crítico como "Si" ÚNICAMENTE si el asesor cierra sin haber dado una gestión clara, sin avisar antes de cerrar, o cierra con MENOS de esas 4 horas de inactividad sin justificación. NO lo marques como "Si" si el asesor gestionó el caso apropiadamente, esperó el tiempo debido, y avisó antes de cerrar — eso es un cierre válido por inactividad del cliente, marca "No". Si el cierre fue algo prematuro pero no un abandono claro, refléjalo bajando el puntaje de "seguimiento_tiempo" en vez de activar el crítico.',
        "despues": '8. CIERRE VÁLIDO vs. ABANDONO ("cierra_sin_resolver"): usa la regla fija de "Cierre por inactividad del cliente" de la política de SLA (arriba): el asesor puede cerrar válidamente tras 4 horas de tiempo LABORAL de silencio del cliente después de una gestión clara, siempre que haya avisado antes de cerrar. Marca este ítem crítico como "Si" ÚNICAMENTE si el asesor cierra sin haber dado una gestión clara, sin avisar antes de cerrar, o cierra con MENOS de esas 4 horas de inactividad sin justificación. NO lo marques como "Si" si el asesor gestionó el caso apropiadamente, esperó el tiempo debido, y avisó antes de cerrar — eso es un cierre válido por inactividad del cliente, marca "No". Si el cierre fue algo prematuro pero no un abandono claro, refléjalo bajando el puntaje de "seguimiento_tiempo" en vez de activar el crítico. IMPORTANTE: la ÚNICA regla que determina si un cierre es prematuro son estas 4 horas de inactividad del CLIENTE. La base de conocimiento oficial (si aparece más abajo) puede mencionar OTROS plazos que no tienen nada que ver con esto — por ejemplo, cuántas horas tiene el PROVEEDOR para responder una garantía, o la vigencia en días para reportar una garantía. Esos son procesos y actores distintos: NO los confundas ni los apliques a la decisión de si el cierre fue prematuro.',
    },
]


def aplicar():
    for i, cambio in enumerate(CAMBIOS, start=1):
        ruta = BASE / cambio["archivo"]
        print(f"\n{i}) {cambio['archivo']}")
        if not ruta.exists():
            print("   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
            continue

        codigo = ruta.read_text(encoding="utf-8")

        if cambio["despues"] in codigo:
            print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
            continue

        if cambio["antes"] not in codigo:
            print("   ⚠️  No encontré el bloque de código esperado.")
            print("       Puede que ya lo hayas editado a mano, o falte aplicar")
            print("       primero corregir_faqs_alcance.py. Revisa manualmente.")
            continue

        print("   Se aplicaría el cambio.")
        if CONFIRMAR:
            nuevo = codigo.replace(cambio["antes"], cambio["despues"])
            ruta.write_text(nuevo, encoding="utf-8")
            print("   ✅ Guardado.")
        else:
            print("   [simulación] no se guardó nada todavía.")


if __name__ == "__main__":
    print("=" * 70)
    print("CORRECCIÓN: precisión de búsqueda de FAQs — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    aplicar()

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_faqs_precision.py --confirmar")
        print("\nDespués de aplicar, corre los tests Y la validación con IA real:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python3 -m pytest tests/ -q")
        print("   python pruebas_validacion_ia/validar_ia.py")
        print("(los tests deben seguir en '63 passed'; en validar_ia.py")
        print(" esperamos que 'Cierre VÁLIDO por inactividad' vuelva a pasar)")
    print("=" * 70)
