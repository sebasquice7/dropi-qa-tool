#!/usr/bin/env python3
"""Corre los casos de pruebas_validacion_ia/casos.py contra la IA REAL
(gasta cuota de tu API key — son solo 8 llamadas, no debería ser un problema
con el tier gratuito de Gemini) y muestra un reporte de qué detectó bien y
qué no.

Uso:
    python pruebas_validacion_ia/validar_ia.py

Esto NO reemplaza a tests/ (que corre gratis, sin IA, y valida la lógica del
programa) — este script valida el CRITERIO de la IA con casos reales.
"""
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluator import evaluar_conversacion
from scoring import calcular_nota, normalizar_evaluacion
from casos import CASOS


def ejecutar_validacion():
    print(f"\n🧪 Corriendo {len(CASOS)} casos de validación contra la IA real...\n")

    resultados = []
    for i, caso in enumerate(CASOS, start=1):
        print(f"[{i}/{len(CASOS)}] {caso['nombre']}...", end=" ", flush=True)
        try:
            evaluacion = evaluar_conversacion(
                caso["texto"], caso["asesor"], pais=caso["pais"], bandeja=caso["bandeja"],
            )
            evaluacion = normalizar_evaluacion(evaluacion)
            nota = calcular_nota(evaluacion)
            ok, mensaje = caso["verificar"](evaluacion, nota)
        except Exception as e:
            ok, mensaje = False, f"Error al evaluar: {e}"

        resultados.append((caso["nombre"], ok, mensaje))
        print("✅" if ok else "❌")
        time.sleep(2)  # margen prudente entre llamadas para no saturar el free tier

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    aciertos = sum(1 for _, ok, _ in resultados if ok)
    for nombre, ok, mensaje in resultados:
        simbolo = "✅" if ok else "❌"
        print(f"{simbolo} {nombre}")
        print(f"   {mensaje}")
    print("=" * 70)
    print(f"\n{aciertos} de {len(resultados)} casos correctos "
          f"({round(aciertos/len(resultados)*100)}%)\n")

    if aciertos < len(resultados):
        print("⚠️  Algunos casos no salieron como se esperaba — revisa la matriz de")
        print("    calidad, la política de comunicación, o el prompt en evaluator.py.")
    else:
        print("🎉 Todos los casos salieron como se esperaba.")


if __name__ == "__main__":
    ejecutar_validacion()
