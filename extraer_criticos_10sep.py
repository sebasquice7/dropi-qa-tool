#!/usr/bin/env python3
"""
Extrae del historial real (historial_evaluaciones.json) los 12 casos
críticos del corte del 10 de septiembre de 2026, con su justificación
completa (oportunidades_mejora / lo_positivo) — no solo la etiqueta.

Uso:
    python extraer_criticos_10sep.py

Genera: casos_criticos_10sep_detalle.json
Ese archivo es el que debes subir de vuelta al chat para que arme el PDF.

Corre este script DESDE LA RAÍZ del proyecto (donde está historial_evaluaciones.json).
"""
import json
from pathlib import Path

RUTA_HISTORIAL = Path("historial_evaluaciones.json")
RUTA_SALIDA = Path("casos_criticos_10sep_detalle.json")

# IDs confirmados desde el Excel del Dashboard (10 de septiembre)
IDS_ESPERADOS = {
    "215475757459664", "215475745823031", "215475317820651",
    "215475805588149", "215475459555158", "215475315963148",
    "215475449969219", "215475785727956", "215475701304480",
    "215475689368971", "215475589544742", "215475382498314",
}


def main():
    if not RUTA_HISTORIAL.exists():
        print(f"❌ No se encontró {RUTA_HISTORIAL} en esta carpeta. Corre este script desde la raíz del proyecto.")
        return

    with open(RUTA_HISTORIAL, encoding="utf-8") as f:
        historial = json.load(f)

    encontrados = []
    for r in historial:
        if r.get("id_caso") in IDS_ESPERADOS and r.get("fecha") == "2026-09-10":
            encontrados.append({
                "id_caso": r.get("id_caso"),
                "fecha": r.get("fecha"),
                "agente": r.get("agente"),
                "bandeja": r.get("bandeja"),
                "pais": r.get("pais"),
                "critico": r.get("critico_activado"),
                "nota_final": r.get("nota_final", 0),
                "oportunidades_mejora": r.get("oportunidades_mejora", []),
                "lo_positivo": r.get("lo_positivo", []),
            })

    print(f"Se encontraron {len(encontrados)} de los 12 casos esperados.")
    faltantes = IDS_ESPERADOS - {r["id_caso"] for r in encontrados}
    if faltantes:
        print(f"\n⚠️  {len(faltantes)} ID(s) no se encontraron (revisa si el historial local ya tiene el corte del 10 de sep):")
        for id_caso in faltantes:
            print(f"   {id_caso}")

    if not encontrados:
        print("\nNada que exportar.")
        return

    # Mismo orden que en la presentación: por tipo de crítico
    orden_tipos = ["cierre_prematuro_abandono", "omision_respuesta_ignora_inquietudes", "redundancia_con_gali"]
    encontrados.sort(key=lambda r: (orden_tipos.index(r["critico"]) if r["critico"] in orden_tipos else 99, r["id_caso"]))

    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(encontrados, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guardado en: {RUTA_SALIDA}")
    print("Sube ese archivo al chat para que te arme el PDF con el detalle completo.")


if __name__ == "__main__":
    main()
