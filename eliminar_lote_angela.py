"""Elimina en lote los 7 casos de Angela Ramirez evaluados el 2026-09-07,
antes de la corrección de la salvedad de logística — para volver a
evaluarlos con la lógica ya corregida.

Con respaldo automático antes de tocar nada, y confirmación explícita.

Uso:
    python eliminar_lote_angela.py
"""
import json
from datetime import datetime
from pathlib import Path

RUTA_HISTORIAL = Path("historial_evaluaciones.json")

IDS_A_ELIMINAR = {
    "215475796158916",  # Triage Logistica — 67%
    "215475784086518",  # Ordenes sin despacho — 82%
    "215475779595252",  # Actualizacion de estatus — 56%
    "215475761431116",  # Casos especiales — 68%
    "215475745903646",  # Guia generada sin movimiento — 0%
    "215475729538505",  # PQR CAS — 59%
    "215475669071543",  # Guia generada sin movimiento — 76%
}


def main():
    if not RUTA_HISTORIAL.exists():
        print(f"❌ No se encontró {RUTA_HISTORIAL} en esta carpeta. Corre este script desde la raíz del proyecto.")
        return

    historial = json.load(open(RUTA_HISTORIAL, encoding="utf-8"))
    total_antes = len(historial)

    encontrados = [r for r in historial if r.get("id_caso") in IDS_A_ELIMINAR]

    print(f"Se encontraron {len(encontrados)} de los 7 casos esperados:")
    for r in sorted(encontrados, key=lambda r: r.get("id_caso")):
        print(f"   {r.get('id_caso')} — {r.get('agente')} — {r.get('bandeja')} — "
              f"{round((r.get('nota_final') or 0) * 100)}% — {r.get('fecha')}")

    faltantes = IDS_A_ELIMINAR - {r.get("id_caso") for r in encontrados}
    if faltantes:
        print(f"\n⚠️  {len(faltantes)} ID(s) no se encontraron en el historial (puede que ya se hayan eliminado antes):")
        for id_caso in faltantes:
            print(f"   {id_caso}")

    if not encontrados:
        print("\nNada que eliminar — no se tocó nada.")
        return

    confirmar = input(f"\n¿Confirmas eliminar estos {len(encontrados)} registro(s)? (escribe 'si' para continuar): ")
    if confirmar.strip().lower() != "si":
        print("Cancelado — no se tocó nada.")
        return

    # Respaldo automático antes de tocar nada
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_respaldo = Path(f"historial_evaluaciones_backup_antes_eliminar_lote_angela_{fecha_hora}.json")
    json.dump(historial, open(ruta_respaldo, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n📦 Respaldo creado: {ruta_respaldo}")

    nuevo_historial = [r for r in historial if r.get("id_caso") not in IDS_A_ELIMINAR]
    json.dump(nuevo_historial, open(RUTA_HISTORIAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    total_despues = len(nuevo_historial)
    print(f"\n✅ Listo. Historial: {total_antes} -> {total_despues} registros "
          f"(se eliminaron {total_antes - total_despues}).")
    print("\nAhora puedes volver a subir y evaluar esas mismas 7 conversaciones desde la app.")


if __name__ == "__main__":
    main()
