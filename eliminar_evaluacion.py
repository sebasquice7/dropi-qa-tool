"""Elimina de forma segura UNA evaluación específica del historial, por su
ID de caso — con respaldo automático antes de tocar nada.

Uso:
    python eliminar_evaluacion.py 215475664765984
"""
import json
import sys
from datetime import datetime
from pathlib import Path

RUTA_HISTORIAL = Path("historial_evaluaciones.json")


def main():
    if len(sys.argv) != 2:
        print("Uso: python eliminar_evaluacion.py <ID_DEL_CASO>")
        sys.exit(1)

    id_caso = sys.argv[1].strip()

    if not RUTA_HISTORIAL.exists():
        print(f"❌ No se encontró {RUTA_HISTORIAL} en esta carpeta. Corre este script desde la raíz del proyecto.")
        sys.exit(1)

    historial = json.load(open(RUTA_HISTORIAL, encoding="utf-8"))
    encontrados = [r for r in historial if r.get("id_caso") == id_caso]

    if not encontrados:
        print(f"❌ No se encontró ninguna evaluación con ID de caso '{id_caso}' en el historial.")
        print(f"   Total de evaluaciones en el historial: {len(historial)}")
        sys.exit(1)

    print(f"✅ Encontrado(s) {len(encontrados)} registro(s) con ID '{id_caso}':")
    for r in encontrados:
        print(f"   Asesor: {r.get('agente')} | Fecha: {r.get('fecha')} | Bandeja: {r.get('bandeja')} | "
              f"País: {r.get('pais')} | Nota: {round((r.get('nota_final') or 0) * 100)}%")

    confirmar = input("\n¿Confirmas que quieres eliminar este/estos registro(s)? (escribe 'si' para confirmar): ")
    if confirmar.strip().lower() != "si":
        print("Cancelado — no se tocó nada.")
        sys.exit(0)

    # Respaldo automático antes de tocar nada
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_respaldo = Path(f"historial_evaluaciones_backup_antes_eliminar_{id_caso}_{fecha_hora}.json")
    json.dump(historial, open(ruta_respaldo, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n📦 Respaldo creado: {ruta_respaldo}")

    nuevo_historial = [r for r in historial if r.get("id_caso") != id_caso]
    json.dump(nuevo_historial, open(RUTA_HISTORIAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"✅ Listo. Historial: {len(historial)} -> {len(nuevo_historial)} registros "
          f"(se quitaron {len(historial) - len(nuevo_historial)}).")


if __name__ == "__main__":
    main()
