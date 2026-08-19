"""Calcula la 'calibración' entre lo que propuso la IA y lo que el auditor
humano confirmó al final — esto revela qué tan confiable es la IA, y en qué
categorías tiende a equivocarse sistemáticamente (muy dura o muy blanda).
"""
from collections import defaultdict
from statistics import mean


def calcular_calibracion(evaluacion_ia: dict, evaluacion_final: dict, matriz: dict) -> dict:
    """
    delta = puntaje_final - puntaje_ia
      delta > 0  -> el auditor SUBIÓ el puntaje (la IA fue más dura de lo justo)
      delta < 0  -> el auditor BAJÓ el puntaje (la IA fue más blanda de lo justo)
      delta == 0 -> el auditor estuvo de acuerdo con la IA en ese ítem
    """
    items_ia = evaluacion_ia.get("items", {})
    items_final = evaluacion_final.get("items", {})

    items_ajustados = []
    for iid, v_final in items_final.items():
        v_ia = items_ia.get(iid, {})
        try:
            p_ia = float(v_ia.get("puntaje", 0))
            p_final = float(v_final.get("puntaje", 0))
        except (TypeError, ValueError):
            continue
        delta = round(p_final - p_ia, 4)
        if abs(delta) > 0.0005:  # ignorar diferencias de redondeo insignificantes
            items_ajustados.append({"item_id": iid, "puntaje_ia": p_ia, "puntaje_final": p_final, "delta": delta})

    total_items = len(items_final)
    items_sin_ajustar = total_items - len(items_ajustados)
    porcentaje_acuerdo = round(items_sin_ajustar / total_items, 4) if total_items else 0

    # Ítems críticos que el auditor cambió (la IA dijo Sí/No y el humano lo volteó)
    criticos_ia = evaluacion_ia.get("items_criticos", {})
    criticos_final = evaluacion_final.get("items_criticos", {})
    criticos_cambiados = []
    for cid, v_final in criticos_final.items():
        ocurrio_ia = str(criticos_ia.get(cid, {}).get("ocurrio", "No")).strip().lower()
        ocurrio_final = str(v_final.get("ocurrio", "No")).strip().lower()
        if ocurrio_ia != ocurrio_final:
            criticos_cambiados.append({"item_id": cid, "ia": ocurrio_ia, "final": ocurrio_final})

    # Delta promedio por categoría (para detectar sesgo sistemático de la IA)
    mapa_item_categoria = {
        it["id"]: cat["nombre"] for cat in matriz["categorias"] for it in cat["items"]
    }
    delta_por_categoria = defaultdict(list)
    for aj in items_ajustados:
        cat = mapa_item_categoria.get(aj["item_id"])
        if cat:
            delta_por_categoria[cat].append(aj["delta"])

    return {
        "total_items": total_items,
        "items_ajustados": items_ajustados,
        "porcentaje_acuerdo": porcentaje_acuerdo,
        "criticos_cambiados": criticos_cambiados,
        "delta_por_categoria": {cat: round(mean(v), 4) for cat, v in delta_por_categoria.items()},
    }


def resumen_calibracion(registros: list) -> dict:
    """Agrega la calibración de TODAS las evaluaciones que la tengan registrada
    (las hechas después de esta actualización, vía revisión manual), para
    mostrar qué tan confiable es la IA en conjunto y dónde se equivoca más."""
    con_calibracion = [r for r in registros if r.get("calibracion")]

    if not con_calibracion:
        return {"hay_datos": False, "total_con_calibracion": 0}

    acuerdos = [r["calibracion"]["porcentaje_acuerdo"] for r in con_calibracion]

    delta_por_categoria = defaultdict(list)
    for r in con_calibracion:
        for cat, delta in (r["calibracion"].get("delta_por_categoria") or {}).items():
            delta_por_categoria[cat].append(delta)

    conteo_criticos_cambiados = defaultdict(int)
    for r in con_calibracion:
        for c in r["calibracion"].get("criticos_cambiados", []):
            conteo_criticos_cambiados[c["item_id"]] += 1

    return {
        "hay_datos": True,
        "total_con_calibracion": len(con_calibracion),
        "porcentaje_acuerdo_promedio": round(mean(acuerdos), 4),
        "delta_por_categoria": {cat: round(mean(v), 4) for cat, v in delta_por_categoria.items()},
        "criticos_cambiados_frecuencia": dict(conteo_criticos_cambiados),
    }
