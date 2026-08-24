"""Fase 3 de Dropi QA: aprendizaje humano, confianza IA, riesgo y muestreo inteligente.

Este módulo evita depender de Flask para que la lógica pueda reutilizarse luego
por una integración con Intercom/Monitor u otro backend.
"""
from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
APRENDIZAJE_PATH = BASE_DIR / "aprendizaje_ia.jsonl"
PRIORIZACION_LOTE_PATH = BASE_DIR / "priorizacion_lote.json"


def _matriz() -> dict:
    return json.loads(MATRIZ_PATH.read_text(encoding="utf-8"))


def _mapa_items() -> dict:
    return {
        it["id"]: {
            "id": it["id"], "nombre": it["nombre"],
            "peso": float(it.get("peso", 0) or 0), "categoria": cat["nombre"],
        }
        for cat in _matriz().get("categorias", []) for it in cat.get("items", [])
    }


def construir_eventos_aprendizaje(evaluacion_ia: dict, evaluacion_final: dict,
                                    metadata: dict, motivos: dict | None = None) -> list:
    """Convierte correcciones humanas reales en ejemplos reutilizables.

    Solo guarda ítems donde el auditor cambió el puntaje o volteó un crítico.
    No inventa una explicación: usa el motivo explícito del auditor si existe y,
    en su defecto, la justificación final que dejó en el ítem.
    """
    motivos = motivos or {}
    mapa = _mapa_items()
    eventos = []
    ahora = datetime.now().isoformat(timespec="seconds")

    ia_items = evaluacion_ia.get("items", {}) or {}
    final_items = evaluacion_final.get("items", {}) or {}
    for iid, fin in final_items.items():
        if iid not in ia_items or iid not in mapa:
            continue
        try:
            p_ia = float((ia_items.get(iid) or {}).get("puntaje", 0))
            p_fin = float((fin or {}).get("puntaje", 0))
        except (TypeError, ValueError):
            continue
        delta = round(p_fin - p_ia, 6)
        if abs(delta) <= 0.0005:
            continue
        info = mapa[iid]
        eventos.append({
            "timestamp": ahora,
            "tipo": "puntaje",
            "item_id": iid,
            "item_nombre": info["nombre"],
            "categoria": info["categoria"],
            "peso": info["peso"],
            "puntaje_ia": p_ia,
            "puntaje_humano": p_fin,
            "delta": delta,
            "direccion": "ia_muy_dura" if delta > 0 else "ia_muy_blanda",
            "justificacion_ia": (ia_items.get(iid) or {}).get("justificacion", ""),
            "justificacion_humano": (fin or {}).get("justificacion", ""),
            "motivo_auditor": (motivos.get(iid) or (fin or {}).get("justificacion", "")).strip(),
            "agente": metadata.get("agente", ""),
            "bandeja": metadata.get("bandeja", ""),
            "pais": metadata.get("pais", ""),
            "id_caso": metadata.get("id_caso", ""),
            "evaluado_por": metadata.get("evaluado_por", ""),
        })

    ia_crit = evaluacion_ia.get("items_criticos", {}) or {}
    fin_crit = evaluacion_final.get("items_criticos", {}) or {}
    for cid, fin in fin_crit.items():
        ia = ia_crit.get(cid) or {}
        a = str(ia.get("ocurrio", "No")).strip().lower()
        b = str((fin or {}).get("ocurrio", "No")).strip().lower()
        if a == b:
            continue
        eventos.append({
            "timestamp": ahora,
            "tipo": "critico",
            "item_id": cid,
            "item_nombre": cid,
            "categoria": "ÍTEM CRÍTICO",
            "ia": a,
            "humano": b,
            "direccion": "critico_corregido",
            "justificacion_ia": ia.get("justificacion", ""),
            "justificacion_humano": (fin or {}).get("justificacion", ""),
            "motivo_auditor": (motivos.get(cid) or (fin or {}).get("justificacion", "")).strip(),
            "agente": metadata.get("agente", ""),
            "bandeja": metadata.get("bandeja", ""),
            "pais": metadata.get("pais", ""),
            "id_caso": metadata.get("id_caso", ""),
            "evaluado_por": metadata.get("evaluado_por", ""),
        })
    return eventos


def guardar_eventos_aprendizaje(eventos: list) -> int:
    if not eventos:
        return 0
    with open(APRENDIZAJE_PATH, "a", encoding="utf-8") as f:
        for e in eventos:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(eventos)


def cargar_aprendizaje() -> list:
    if not APRENDIZAJE_PATH.exists():
        return []
    eventos = []
    try:
        for linea in APRENDIZAJE_PATH.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                eventos.append(json.loads(linea))
    except (OSError, json.JSONDecodeError):
        return []
    return eventos


def biblioteca_errores_ia(limite: int = 12) -> list:
    eventos = cargar_aprendizaje()
    grupos = defaultdict(lambda: {"total": 0, "deltas": [], "direcciones": defaultdict(int), "ejemplos": []})
    for e in eventos:
        key = (e.get("tipo"), e.get("item_id"))
        g = grupos[key]
        g["total"] += 1
        if e.get("tipo") == "puntaje":
            g["deltas"].append(abs(float(e.get("delta", 0) or 0)))
        g["direcciones"][e.get("direccion", "")] += 1
        if len(g["ejemplos"]) < 3:
            g["ejemplos"].append({
                "id_caso": e.get("id_caso"), "fecha": (e.get("timestamp") or "")[:10],
                "motivo": e.get("motivo_auditor") or e.get("justificacion_humano") or "",
                "bandeja": e.get("bandeja", ""),
            })
    filas = []
    mapa = _mapa_items()
    for (tipo, iid), g in grupos.items():
        dir_principal = max(g["direcciones"], key=g["direcciones"].get) if g["direcciones"] else ""
        filas.append({
            "tipo": tipo, "item_id": iid,
            "nombre": mapa.get(iid, {}).get("nombre", iid),
            "categoria": mapa.get(iid, {}).get("categoria", "ÍTEM CRÍTICO" if tipo == "critico" else ""),
            "correcciones": g["total"],
            "error_medio": round(mean(g["deltas"]), 4) if g["deltas"] else None,
            "direccion_principal": dir_principal,
            "ejemplos": g["ejemplos"],
        })
    filas.sort(key=lambda x: (-x["correcciones"], -(x["error_medio"] or 0)))
    return filas[:limite]


def _comparaciones_de_registro(r: dict) -> list:
    cal = r.get("calibracion") or {}
    if cal.get("items_comparados"):
        return cal["items_comparados"]
    # Compatibilidad con historial antiguo: solo conocemos los ítems corregidos,
    # no podemos inventar acuerdos item por item.
    return [dict(x, ajustado=True) for x in (cal.get("items_ajustados") or [])]


def confianza_por_item(registros: list) -> list:
    mapa = _mapa_items()
    stats = defaultdict(lambda: {"n": 0, "acuerdos": 0, "errores_norm": []})
    for r in registros:
        for c in _comparaciones_de_registro(r):
            iid = c.get("item_id")
            info = mapa.get(iid)
            if not info or not info["peso"]:
                continue
            try:
                delta = abs(float(c.get("delta", 0) or 0))
            except (TypeError, ValueError):
                continue
            s = stats[iid]
            s["n"] += 1
            if delta <= 0.0005:
                s["acuerdos"] += 1
            s["errores_norm"].append(min(delta / info["peso"], 1.0))

    filas = []
    for iid, s in stats.items():
        info = mapa[iid]
        acuerdo = s["acuerdos"] / s["n"] if s["n"] else 0
        mae = mean(s["errores_norm"]) if s["errores_norm"] else 1
        exactitud = max(0.0, 1.0 - mae)
        base = (0.65 * acuerdo) + (0.35 * exactitud)
        # Penaliza muestras pequeñas: 1 caso jamás debe verse como "alta confianza".
        factor_muestra = min(s["n"] / 10, 1.0)
        score = base * (0.55 + 0.45 * factor_muestra)
        if s["n"] >= 8 and score >= 0.82:
            nivel = "alta"
        elif s["n"] >= 3 and score >= 0.62:
            nivel = "media"
        else:
            nivel = "baja"
        filas.append({
            **info, "muestra": s["n"], "acuerdo": round(acuerdo, 4),
            "error_absoluto_normalizado": round(mae, 4), "confianza": round(score, 4),
            "nivel": nivel,
        })
    filas.sort(key=lambda x: (x["confianza"], -x["muestra"], x["nombre"]))
    return filas


def confianza_global(registros: list) -> dict:
    filas = confianza_por_item(registros)
    if not filas:
        return {"hay_datos": False, "confianza": 0, "nivel": "sin_datos", "muestra_items": 0}
    ponderados = []
    for f in filas:
        ponderados.extend([f["confianza"]] * max(1, min(f["muestra"], 10)))
    score = mean(ponderados) if ponderados else 0
    nivel = "alta" if score >= .82 else ("media" if score >= .62 else "baja")
    return {"hay_datos": True, "confianza": round(score, 4), "nivel": nivel, "muestra_items": sum(f["muestra"] for f in filas)}


def resumen_calibracion_avanzada(registros: list) -> dict:
    mapa = _mapa_items()
    by_item = defaultdict(lambda: {"n": 0, "ajustes": 0, "deltas": []})
    by_cat = defaultdict(lambda: {"n": 0, "ajustes": 0, "deltas": []})
    by_bandeja = defaultdict(lambda: {"n": 0, "ajustes": 0, "deltas": []})
    by_asesor = defaultdict(lambda: {"n": 0, "ajustes": 0, "deltas": []})

    for r in registros:
        comps = _comparaciones_de_registro(r)
        for c in comps:
            iid = c.get("item_id")
            delta = float(c.get("delta", 0) or 0)
            ajustado = abs(delta) > 0.0005
            info = mapa.get(iid, {})
            for grupo, clave in (
                (by_item, iid), (by_cat, info.get("categoria", "Sin categoría")),
                (by_bandeja, r.get("bandeja") or "Sin bandeja"),
                (by_asesor, r.get("agente") or "Sin asesor"),
            ):
                if not clave:
                    continue
                g = grupo[clave]; g["n"] += 1; g["deltas"].append(delta)
                if ajustado: g["ajustes"] += 1

    def rows(d, nombre_fn=lambda k: k):
        out = []
        for k, g in d.items():
            if not g["n"]: continue
            out.append({
                "id": k, "nombre": nombre_fn(k), "muestra": g["n"],
                "correcciones": g["ajustes"], "acuerdo": round(1 - g["ajustes"] / g["n"], 4),
                "sesgo": round(mean(g["deltas"]), 4),
                "error_medio": round(mean(abs(x) for x in g["deltas"]), 4),
            })
        out.sort(key=lambda x: (x["acuerdo"], -x["muestra"]))
        return out

    return {
        "por_item": rows(by_item, lambda iid: mapa.get(iid, {}).get("nombre", iid)),
        "por_categoria": rows(by_cat), "por_bandeja": rows(by_bandeja), "por_asesor": rows(by_asesor),
        "confianza_items": confianza_por_item(registros), "confianza_global": confianza_global(registros),
        "biblioteca": biblioteca_errores_ia(),
    }


def contexto_aprendizaje_para_prompt(pais: str = "", bandeja: str = "", limite: int = 6) -> str:
    """Ejemplos compactos de correcciones repetidas para enriquecer el prompt.

    Solo usa eventos reales guardados por auditores. Prioriza misma bandeja/país
    y patrones con varias correcciones para no sobreajustar a un único caso.
    """
    eventos = cargar_aprendizaje()
    if not eventos:
        return ""
    conteo = defaultdict(int)
    for e in eventos:
        if e.get("tipo") == "puntaje": conteo[e.get("item_id")] += 1
    candidatos = []
    for e in reversed(eventos):
        if e.get("tipo") != "puntaje" or conteo[e.get("item_id")] < 2:
            continue
        prioridad = 0
        if bandeja and (e.get("bandeja") or "").lower() == bandeja.lower(): prioridad += 2
        if pais and (e.get("pais") or "").lower() == pais.lower(): prioridad += 1
        candidatos.append((prioridad, e))
    candidatos.sort(key=lambda x: x[0], reverse=True)
    vistos = set(); lineas = []
    for _, e in candidatos:
        iid = e.get("item_id")
        if iid in vistos: continue
        vistos.add(iid)
        motivo = (e.get("motivo_auditor") or e.get("justificacion_humano") or "").strip()
        if not motivo: continue
        lineas.append(
            f"- {e.get('item_nombre', iid)}: en calibraciones previas el auditor corrigió a la IA porque {motivo}. "
            f"Usa este antecedente solo como alerta de criterio; decide con la evidencia del caso actual."
        )
        if len(lineas) >= limite: break
    return "\n".join(lineas)


# ------------------------------- Riesgo / priorización -----------------------

_PATRONES = {
    "frustracion": ["molest", "inconforme", "cansad", "pésim", "pesim", "queja", "reclamo", "urgente", "nadie me", "no resuelven"],
    "dinero": ["reembolso", "devolución", "devolucion", "retiro", "dinero", "pago", "wallet", "cartera", "comisión", "comision"],
    "escalamiento": ["escalar", "escalado", "supervisor", "coordinador", "soporte técnico", "soporte tecnico", "ticket", "pqr"],
    "evidencia": ["adjunto", "imagen", "captura", "evidencia", "archivo", "excel", "comprobante", "video"],
    "reapertura": ["reabierto", "reapertura", "nuevamente", "otra vez", "sigo esperando", "aún", "aun"],
}


def analizar_riesgo_conversacion(texto: str, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    t = (texto or "").lower()
    score = 0; senales = []
    mensajes = len(re.findall(r"\[(?:CLIENTE|STAFF)\]", texto or "", flags=re.I))
    if mensajes >= 80: score += 25; senales.append("Conversación muy extensa (80+ mensajes)")
    elif mensajes >= 40: score += 15; senales.append("Conversación extensa (40+ mensajes)")
    elif mensajes >= 20: score += 7; senales.append("Conversación de seguimiento prolongado")

    pesos = {"frustracion": 22, "dinero": 12, "escalamiento": 18, "evidencia": 8, "reapertura": 16}
    etiquetas = {"frustracion":"Señales de frustración/reclamo", "dinero":"Caso con impacto económico", "escalamiento":"Escalamiento o intervención adicional", "evidencia":"Manejo de evidencias/adjuntos", "reapertura":"Posible reapertura o reiteración"}
    for k, palabras in _PATRONES.items():
        hits = sum(1 for p in palabras if p in t)
        if hits:
            score += min(pesos[k], 5 + hits * 4)
            senales.append(etiquetas[k])

    fechas = set(re.findall(r"\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b", texto or ""))
    if len(fechas) >= 3: score += 12; senales.append("Caso distribuido en varios días")
    elif len(fechas) == 2: score += 6; senales.append("Caso con continuidad entre días")

    if not (metadata.get("bandeja") or "").strip(): score += 5; senales.append("Bandeja no identificada")
    score = min(score, 100)
    nivel = "alto" if score >= 60 else ("medio" if score >= 30 else "bajo")
    return {"score": score, "nivel": nivel, "senales": senales[:8], "mensajes_estimados": mensajes}


def _complejidad(riesgo: dict) -> int:
    claves = ("extensa", "varios días", "evidencias", "Escalamiento", "reapertura")
    return sum(1 for s in riesgo.get("senales", []) if any(k.lower() in s.lower() for k in claves))


def priorizar_muestra(candidatos: list, cantidad: int, reincidencias_por_asesor: dict | None = None,
                      semilla: int = 42) -> dict:
    """Selecciona una muestra mixta: 60% aleatoria, 20% riesgo, 10% reincidencia, 10% complejidad."""
    if not candidatos:
        return {"seleccionados": [], "todos": [], "cantidad": 0}
    cantidad = max(1, min(int(cantidad), len(candidatos)))
    reincidencias_por_asesor = reincidencias_por_asesor or {}
    rng = random.Random(semilla)
    ids = {id(c): c for c in candidatos}
    elegidos = []

    def tomar(ordenados, n, motivo):
        for c in ordenados:
            if len([x for x in elegidos if x[0] is c]) or n <= 0: continue
            elegidos.append((c, motivo)); n -= 1

    n_riesgo = round(cantidad * .20)
    n_reinc = round(cantidad * .10)
    n_comp = round(cantidad * .10)
    n_aleat = max(0, cantidad - n_riesgo - n_reinc - n_comp)

    tomar(sorted(candidatos, key=lambda c: c.get("riesgo", {}).get("score", 0), reverse=True), n_riesgo, "Riesgo alto")
    tomar(sorted(candidatos, key=lambda c: reincidencias_por_asesor.get(c.get("asesor", ""), 0), reverse=True), n_reinc, "Reincidencia del asesor")
    tomar(sorted(candidatos, key=lambda c: _complejidad(c.get("riesgo", {})), reverse=True), n_comp, "Complejidad")
    restantes = [c for c in candidatos if not any(x[0] is c for x in elegidos)]
    rng.shuffle(restantes); tomar(restantes, n_aleat, "Aleatoria")
    restantes = [c for c in candidatos if not any(x[0] is c for x in elegidos)]
    tomar(restantes, cantidad - len(elegidos), "Completar muestra")

    seleccionados_ids = {c.get("token") for c, _ in elegidos}
    motivo_por_token = {c.get("token"): m for c, m in elegidos}
    todos = []
    for c in candidatos:
        cc = dict(c)
        cc["seleccionado"] = c.get("token") in seleccionados_ids
        cc["motivo_seleccion"] = motivo_por_token.get(c.get("token"), "")
        todos.append(cc)
    return {"seleccionados": [c for c in todos if c["seleccionado"]], "todos": todos, "cantidad": cantidad}


def guardar_priorizacion(data: dict) -> None:
    PRIORIZACION_LOTE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_priorizacion() -> dict:
    if not PRIORIZACION_LOTE_PATH.exists(): return {}
    try: return json.loads(PRIORIZACION_LOTE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}
