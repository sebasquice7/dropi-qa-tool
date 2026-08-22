#!/usr/bin/env python3
"""Migra historial_evaluaciones.json de la Matriz V1 a la Matriz V2, para que el
dashboard en vivo pueda leer las evaluaciones antiguas con los nombres de
categoría/ítem NUEVOS y no muestre 0% de eficiencia por un simple desajuste
de nombres.

Qué hace, por cada registro histórico que todavía esté en formato V1:
  1. Recalcula 'items_detalle' con los IDs de ítem de la V2, usando el
     promedio de % de cumplimiento de los ítems viejos que se fusionan en
     cada ítem nuevo (ver config/mapeo_matriz_v1_a_v2.json).
  2. Recalcula 'categorias' sumando esos ítems nuevos agrupados por las
     categorías ACTUALES de config/matriz_calidad.json.
  3. Remapea 'critico_activado' al id nuevo equivalente cuando existe uno;
     si el crítico ya no existe en la V2, se deja tal cual (es una decisión
     de negocio retirar ese crítico, no un error de mapeo).
  4. Marca el registro con 'matriz_version': 'v2' y conserva los datos
     originales sin tocar bajo 'v1_original', para no perder nada.

NO toca 'nota_final' ni 'nota_bruta' — esos números ya eran correctos según
la matriz vigente en el momento de la evaluación y se preservan intactos;
solo se ajustan las estructuras usadas para agrupar/graficar por categoría e
ítem, que es lo que dependía de nombres que cambiaron.

Uso:
    python migrar_historial_v2.py           # migra de una vez
    python migrar_historial_v2.py --dry-run # solo muestra qué haría, no guarda
"""
import json
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
HISTORIAL_PATH = BASE_DIR / "historial_evaluaciones.json"
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
MAPEO_PATH = BASE_DIR / "config" / "mapeo_matriz_v1_a_v2.json"
MATRIZ_V1_PATH = BASE_DIR / "config" / "matriz_calidad_v1_backup.json"


def _cargar_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _pesos_items_v1(matriz_v1: dict) -> dict:
    """id_item_v1 -> peso_max_v1"""
    return {it["id"]: it["peso"] for cat in matriz_v1["categorias"] for it in cat["items"]}


def _pesos_items_v2(matriz_v2: dict) -> dict:
    """id_item_v2 -> {'peso':..., 'categoria':...}"""
    return {
        it["id"]: {"peso": it["peso"], "categoria": cat["nombre"]}
        for cat in matriz_v2["categorias"]
        for it in cat["items"]
    }


def _es_registro_v1(registro: dict, ids_v2_validos: set) -> bool:
    """Un registro está en formato viejo si sus items_detalle usan IDs que no
    existen en la matriz V2 actual (o si ya trae la marca explícita)."""
    if registro.get("matriz_version") == "v2":
        return False
    items = set((registro.get("items_detalle") or {}).keys())
    if not items:
        # Registro sin items_detalle (evaluaciones muy antiguas, antes de
        # ese campo) — se migra igual solo para taggear la versión, sin
        # poder recalcular nada a nivel de ítem.
        return True
    return not items.issubset(ids_v2_validos)


def migrar_registro(registro: dict, grupos_items: dict, mapa_criticos: dict,
                     pesos_v1: dict, pesos_v2: dict) -> dict:
    items_v1 = registro.get("items_detalle") or {}

    nuevos_items = {}
    for id_nuevo, ids_viejos in grupos_items.items():
        info_v2 = pesos_v2.get(id_nuevo)
        if not info_v2:
            continue  # id_nuevo no existe en la matriz actual (no debería pasar)
        peso_nuevo = info_v2["peso"]

        if not ids_viejos:
            # Sin ítem viejo equivalente (ej. despedida_corporativa): no hay
            # evidencia histórica de falla en ese punto -> puntaje máximo.
            nuevos_items[id_nuevo] = round(peso_nuevo, 4)
            continue

        ratios = []
        for id_viejo in ids_viejos:
            if id_viejo not in items_v1:
                continue
            peso_viejo = pesos_v1.get(id_viejo)
            if not peso_viejo:
                continue
            puntaje_viejo = items_v1[id_viejo]
            ratio = max(0.0, min(1.0, puntaje_viejo / peso_viejo))
            ratios.append(ratio)

        if ratios:
            ratio_promedio = sum(ratios) / len(ratios)
        else:
            # El caso viejo no traía ninguno de los ítems mapeados (registro
            # muy antiguo/incompleto) -> no penalizar por falta de dato.
            ratio_promedio = 1.0

        nuevos_items[id_nuevo] = round(peso_nuevo * ratio_promedio, 4)

    nuevas_categorias = {}
    for id_nuevo, puntaje in nuevos_items.items():
        cat_nombre = pesos_v2[id_nuevo]["categoria"]
        nuevas_categorias[cat_nombre] = round(nuevas_categorias.get(cat_nombre, 0.0) + puntaje, 4)

    critico_viejo = registro.get("critico_activado")
    critico_nuevo = critico_viejo
    if critico_viejo and critico_viejo in mapa_criticos:
        equivalente = mapa_criticos[critico_viejo]
        if equivalente:
            critico_nuevo = equivalente
        # si equivalente es None, se deja el id viejo tal cual (crítico retirado en V2)

    registro_migrado = dict(registro)
    registro_migrado["v1_original"] = {
        "categorias": registro.get("categorias"),
        "items_detalle": registro.get("items_detalle"),
        "critico_activado": registro.get("critico_activado"),
    }
    registro_migrado["items_detalle"] = nuevos_items
    registro_migrado["categorias"] = nuevas_categorias
    registro_migrado["critico_activado"] = critico_nuevo
    registro_migrado["matriz_version"] = "v2"
    registro_migrado["migrado_desde_v1_en"] = datetime.now().isoformat(timespec="seconds")

    return registro_migrado


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    matriz_v2 = _cargar_json(MATRIZ_PATH)
    matriz_v1 = _cargar_json(MATRIZ_V1_PATH)
    mapeo = _cargar_json(MAPEO_PATH)

    pesos_v1 = _pesos_items_v1(matriz_v1)
    pesos_v2 = _pesos_items_v2(matriz_v2)
    ids_v2_validos = set(pesos_v2.keys())

    grupos_items = mapeo["grupos_items_nuevos"]
    mapa_criticos = mapeo["items_criticos"]

    historial = _cargar_json(HISTORIAL_PATH)
    print(f"Total de registros en el historial: {len(historial)}")

    migrados = 0
    ya_v2 = 0
    resultado = []
    for registro in historial:
        if _es_registro_v1(registro, ids_v2_validos):
            nuevo = migrar_registro(registro, grupos_items, mapa_criticos, pesos_v1, pesos_v2)
            resultado.append(nuevo)
            migrados += 1
        else:
            ya_v2 += 1
            resultado.append(registro)

    print(f"Registros migrados a V2: {migrados}")
    print(f"Registros que ya estaban en V2 (sin cambios): {ya_v2}")

    if dry_run:
        print("\n--dry-run: no se guardó nada. Mostrando el primer registro migrado como muestra:\n")
        for r in resultado:
            if r.get("matriz_version") == "v2" and r.get("v1_original"):
                print(json.dumps({
                    "agente": r.get("agente"), "fecha": r.get("fecha"),
                    "categorias_nuevas": r["categorias"],
                    "categorias_v1_original": r["v1_original"]["categorias"],
                    "critico_activado_nuevo": r.get("critico_activado"),
                    "critico_activado_v1_original": r["v1_original"]["critico_activado"],
                }, ensure_ascii=False, indent=2))
                break
        return

    backup_path = HISTORIAL_PATH.with_name(
        f"historial_evaluaciones_backup_pre_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    backup_path.write_text(json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Respaldo del historial original guardado en: {backup_path.name}")

    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"historial_evaluaciones.json actualizado con {migrados} registros migrados a V2.")


if __name__ == "__main__":
    main()
