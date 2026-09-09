#!/usr/bin/env python3
"""
Corrige un vacío real: la base de conocimiento de FAQs (que tiene datos
oficiales como "10 días hábiles para garantías") solo se consultaba con lo
que decía el bot Gali — si el cliente le preguntaba directo al asesor humano
(sin pasar por Gali), la IA nunca tenía referencia para detectar información
falsa o inventada, aunque la respuesta correcta estuviera documentada.

Por defecto corre en modo SIMULACIÓN (no cambia nada).
Para aplicar de verdad: python corregir_faqs_alcance.py --confirmar

Qué hace (3 archivos):
1. src/services/evaluacion_service.py — pasa el texto COMPLETO de la
   conversación a la búsqueda de FAQs, no solo lo que dijo Gali.
2. src/services/lote_service.py — antes ni siquiera enviaba este dato al
   evaluar en lote; ahora sí, igual que la ruta individual.
3. src/faqs_gali_buscador.py y src/evaluator.py — actualiza los textos que
   se le muestran a la IA para reflejar que esta base de conocimiento sirve
   para verificar CUALQUIER afirmación de la conversación, no solo las de Gali.

Corre este script DESDE LA RAÍZ del proyecto (donde está src/).
"""
import sys
from pathlib import Path

CONFIRMAR = "--confirmar" in sys.argv
BASE = Path(__file__).resolve().parent

CAMBIOS = [
    {
        "archivo": "src/services/evaluacion_service.py",
        "antes": 'evaluacion = evaluar_conversacion(texto, asesor, pais=pais, bandeja=bandeja, texto_gali=conv.texto_de_gali(), texto_notas_internas=conv.texto_de_notas_internas())',
        "despues": 'evaluacion = evaluar_conversacion(texto, asesor, pais=pais, bandeja=bandeja, texto_gali=texto, texto_notas_internas=conv.texto_de_notas_internas())',
    },
    {
        "archivo": "src/services/lote_service.py",
        "antes": '''evaluacion = evaluar_conversacion(
        conv.texto_plano(), asesor,
        pais=meta_detectada.get("pais") or "", bandeja=meta_detectada.get("bandeja") or "",
    )''',
        "despues": '''evaluacion = evaluar_conversacion(
        conv.texto_plano(), asesor,
        pais=meta_detectada.get("pais") or "", bandeja=meta_detectada.get("bandeja") or "",
        texto_gali=conv.texto_plano(), texto_notas_internas=conv.texto_de_notas_internas(),
    )''',
    },
    {
        "archivo": "src/faqs_gali_buscador.py",
        "antes": 'partes = ["Preguntas/respuestas OFICIALES de la base de conocimiento de Gali, relevantes a esta conversación (úsalas como referencia para juzgar si Gali dio información correcta):"]',
        "despues": 'partes = ["Preguntas/respuestas OFICIALES de la base de conocimiento de Gali, relevantes a los temas de esta conversación (úsalas como referencia para verificar si la información dada por CUALQUIERA en la conversación —asesor o bot— es correcta):"]',
    },
    {
        "archivo": "src/evaluator.py",
        "antes": '{("=== BASE DE CONOCIMIENTO DE GALI (referencia oficial) ===" + chr(10) + contexto_gali) if contexto_gali else "=== BASE DE CONOCIMIENTO DE GALI: no se encontró ninguna pregunta/respuesta oficial que aplique a lo que Gali dijo en este caso. Los ítems sobre Gali deben calificarse según el criterio general (no penalizar por falta de una referencia específica). ==="}',
        "despues": '{("=== BASE DE CONOCIMIENTO OFICIAL (FAQs de Gali, usada como referencia de hechos) ===" + chr(10) + "Esta es información oficial y verificada de la empresa. Úsala para confirmar si CUALQUIER afirmación de la conversación (del asesor, del bot Gali, o de cualquiera) es correcta — en particular para el ítem \\"informacion_falsa_enganosa\\": si el asesor dio un dato (plazos, políticas, procedimientos) que CONTRADICE lo que dice aquí, es evidencia fuerte de información falsa o engañosa. También úsala para los ítems específicos sobre Gali si aplican." + chr(10) + chr(10) + contexto_gali) if contexto_gali else "=== BASE DE CONOCIMIENTO OFICIAL: no se encontró ninguna pregunta/respuesta oficial que aplique a los temas tratados en este caso. Evalúa los ítems relacionados (incluyendo informacion_falsa_enganosa) según el criterio general — no penalices por falta de una referencia específica, pero sí marca información que suene claramente inventada o inconsistente con el resto de la conversación. ==="}',
    },
]


def aplicar():
    for i, cambio in enumerate(CAMBIOS, start=1):
        ruta = BASE / cambio["archivo"]
        print(f"\n{i}) {cambio['archivo']}")
        if not ruta.exists():
            print(f"   ⚠️  No encontré este archivo — ¿estás en la raíz del proyecto?")
            continue

        codigo = ruta.read_text(encoding="utf-8")

        if cambio["despues"] in codigo:
            print("   ✅ Ya tiene el cambio aplicado — no hago nada.")
            continue

        if cambio["antes"] not in codigo:
            print("   ⚠️  No encontré el bloque de código esperado.")
            print("       Puede que ya lo hayas editado a mano, o que el archivo cambió.")
            print("       Revisa este archivo manualmente.")
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
    print("CORRECCIÓN: alcance de la base de FAQs (información falsa) — modo:",
          "CONFIRMAR (aplica de verdad)" if CONFIRMAR else "SIMULACIÓN (no cambia nada)")
    print("=" * 70)

    aplicar()

    print("\n" + "=" * 70)
    if not CONFIRMAR:
        print("Esto fue solo una simulación. Si todo se ve bien, corre:")
        print("   python corregir_faqs_alcance.py --confirmar")
        print("\nDespués de aplicar, corre los tests:")
        print("   python3 -m pytest tests/ -q")
    else:
        print("✅ Corrección aplicada. Corre ahora:")
        print("   python3 -m pytest tests/ -q")
        print("(deberías seguir viendo '63 passed')")
    print("=" * 70)
