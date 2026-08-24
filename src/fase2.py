"""Analítica de Fase 2 para Dropi QA.

Convierte el historial de auditorías en señales de gestión: reincidencias,
tendencias por asesor, pérdida de puntos por subítem, cobertura contra meta y
bandeja de casos críticos con estado de revisión.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean

from historial import cargar_historial

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
METAS_PATH = BASE_DIR / "config" / "metas_auditoria.json"
CRITICOS_ESTADO_PATH = BASE_DIR / "config" / "criticos_estado.json"

DEFAULT_METAS = {"auditorias_por_asesor_mes": 50}


def _leer_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return default.copy() if isinstance(default, dict) else default


def _guardar_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def obtener_metas_auditoria() -> dict:
    metas = _leer_json(METAS_PATH, DEFAULT_METAS)
    valor = metas.get("auditorias_por_asesor_mes", DEFAULT_METAS["auditorias_por_asesor_mes"])
    try:
        valor = max(1, int(valor))
    except (TypeError, ValueError):
        valor = DEFAULT_METAS["auditorias_por_asesor_mes"]
    return {"auditorias_por_asesor_mes": valor}


def guardar_meta_auditorias_por_asesor(valor: int) -> dict:
    valor = max(1, min(1000, int(valor)))
    metas = obtener_metas_auditoria()
    metas["auditorias_por_asesor_mes"] = valor
    _guardar_json(METAS_PATH, metas)
    return metas


def _matriz_items() -> dict:
    matriz = json.loads(MATRIZ_PATH.read_text(encoding="utf-8"))
    return {
        item["id"]: {
            "id": item["id"],
            "nombre": item["nombre"],
            "peso": float(item.get("peso", 0) or 0),
            "categoria": categoria["nombre"],
        }
        for categoria in matriz.get("categorias", [])
        for item in categoria.get("items", [])
    }


def _puntaje(detalle):
    if isinstance(detalle, dict):
        if detalle.get("aplica") is False:
            return None
        detalle = detalle.get("puntaje")
    try:
        return float(detalle) if detalle is not None else None
    except (TypeError, ValueError):
        return None


def ranking_perdida_puntos(registros: list, top_n: int = 12) -> list:
    """Ranking de subítems por puntos totales perdidos en la muestra.

    Un ítem ausente no cuenta como cero: solo se incluyen evaluaciones donde el
    historial realmente tiene puntaje para ese subítem.
    """
    mapa = _matriz_items()
    acumulado = defaultdict(lambda: {"evaluado": 0, "fallas": 0, "perdida": 0.0, "obtenido": 0.0})
    for r in registros:
        for iid, raw in (r.get("items_detalle") or {}).items():
            info = mapa.get(iid)
            if not info or info["peso"] <= 0:
                continue
            score = _puntaje(raw)
            if score is None:
                continue
            score = min(max(score, 0.0), info["peso"])
            perdida = max(info["peso"] - score, 0.0)
            a = acumulado[iid]
            a["evaluado"] += 1
            a["obtenido"] += score
            a["perdida"] += perdida
            if perdida > 1e-9:
                a["fallas"] += 1

    filas = []
    for iid, a in acumulado.items():
        info = mapa[iid]
        if not a["evaluado"]:
            continue
        max_total = info["peso"] * a["evaluado"]
        eficiencia = a["obtenido"] / max_total if max_total else 0
        filas.append({
            **info,
            "veces_evaluado": a["evaluado"],
            "casos_con_perdida": a["fallas"],
            "puntos_perdidos": round(a["perdida"], 4),
            "puntos_perdidos_pct": round(a["perdida"] * 100, 2),
            "eficiencia": round(min(eficiencia, 1.0), 4),
        })
    filas.sort(key=lambda x: (-x["puntos_perdidos"], -x["casos_con_perdida"], x["nombre"]))
    return filas[:top_n]


def reincidencias_asesor(asesor: str, umbral_cumplimiento: float = 0.80, minimo_fallas: int = 2) -> list:
    """Detecta subítems repetidamente por debajo del umbral en un asesor."""
    mapa = _matriz_items()
    registros = [r for r in cargar_historial() if r.get("agente") == asesor]
    registros.sort(key=lambda r: r.get("timestamp", ""))
    stats = defaultdict(lambda: {"evaluado": 0, "fallas": 0, "fechas": [], "scores": []})

    for r in registros:
        for iid, raw in (r.get("items_detalle") or {}).items():
            info = mapa.get(iid)
            if not info or info["peso"] <= 0:
                continue
            score = _puntaje(raw)
            if score is None:
                continue
            cumplimiento = min(max(score / info["peso"], 0.0), 1.0)
            s = stats[iid]
            s["evaluado"] += 1
            s["scores"].append(cumplimiento)
            if cumplimiento < umbral_cumplimiento:
                s["fallas"] += 1
                s["fechas"].append(r.get("fecha", ""))

    filas = []
    for iid, s in stats.items():
        if s["fallas"] < minimo_fallas:
            continue
        info = mapa[iid]
        filas.append({
            **info,
            "veces_evaluado": s["evaluado"],
            "reincidencias": s["fallas"],
            "tasa_reincidencia": round(s["fallas"] / s["evaluado"], 4) if s["evaluado"] else 0,
            "cumplimiento_promedio": round(mean(s["scores"]), 4),
            "primera_falla": s["fechas"][0] if s["fechas"] else None,
            "ultima_falla": s["fechas"][-1] if s["fechas"] else None,
        })
    filas.sort(key=lambda x: (-x["reincidencias"], -x["tasa_reincidencia"], x["cumplimiento_promedio"]))
    return filas


def tendencia_periodica_asesor(asesor: str) -> dict:
    """Promedios semanales y mensuales del asesor, cronológicos."""
    registros = [r for r in cargar_historial() if r.get("agente") == asesor and r.get("fecha")]
    semanal = defaultdict(list)
    mensual = defaultdict(list)
    for r in registros:
        try:
            d = datetime.strptime(r["fecha"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        iso = d.isocalendar()
        semanal[f"{iso.year}-S{iso.week:02d}"].append(float(r.get("nota_final", 0) or 0))
        mensual[d.strftime("%Y-%m")].append(float(r.get("nota_final", 0) or 0))

    def serie(datos):
        return [{"periodo": k, "promedio": round(mean(v), 4), "evaluaciones": len(v)} for k, v in sorted(datos.items())]

    sem = serie(semanal)
    mes = serie(mensual)
    delta_sem = round(sem[-1]["promedio"] - sem[-2]["promedio"], 4) if len(sem) >= 2 else None
    delta_mes = round(mes[-1]["promedio"] - mes[-2]["promedio"], 4) if len(mes) >= 2 else None
    return {"semanal": sem, "mensual": mes, "delta_semanal": delta_sem, "delta_mensual": delta_mes}


def cobertura_mes_actual(registros_base: list | None = None) -> dict:
    """Cobertura del mes calendario actual por asesor contra la meta configurable."""
    registros_base = cargar_historial() if registros_base is None else registros_base
    hoy = date.today()
    prefijo = hoy.strftime("%Y-%m")
    registros = [r for r in registros_base if (r.get("fecha") or "").startswith(prefijo)]
    meta = obtener_metas_auditoria()["auditorias_por_asesor_mes"]
    por_asesor = defaultdict(int)
    for r in registros:
        if r.get("agente"):
            por_asesor[r["agente"]] += 1

    # Incluye asesores presentes en la base aunque aún lleven 0 este mes.
    asesores = sorted({r.get("agente") for r in registros_base if r.get("agente")})
    filas = []
    for asesor in asesores:
        realizadas = por_asesor.get(asesor, 0)
        filas.append({
            "asesor": asesor,
            "realizadas": realizadas,
            "meta": meta,
            "pendientes": max(meta - realizadas, 0),
            "cobertura": round(min(realizadas / meta, 1.0), 4) if meta else 0,
        })
    filas.sort(key=lambda x: (x["cobertura"], x["asesor"]))
    total_meta = meta * len(asesores)
    total_realizadas = sum(x["realizadas"] for x in filas)
    return {
        "mes": prefijo,
        "meta_por_asesor": meta,
        "asesores": filas,
        "total_realizadas": total_realizadas,
        "total_meta": total_meta,
        "cobertura_global": round(min(total_realizadas / total_meta, 1.0), 4) if total_meta else 0,
    }


def _clave_critico(registro: dict) -> str:
    return registro.get("timestamp") or f"{registro.get('fecha','')}|{registro.get('id_caso','')}|{registro.get('agente','')}"


def obtener_casos_criticos(registros: list | None = None, limite: int = 50) -> list:
    registros = cargar_historial() if registros is None else registros
    estados = _leer_json(CRITICOS_ESTADO_PATH, {})
    filas = []
    for r in registros:
        if not r.get("critico_activado"):
            continue
        clave = _clave_critico(r)
        estado = estados.get(clave, {})
        filas.append({
            "clave": clave,
            "timestamp": r.get("timestamp"),
            "fecha": r.get("fecha"),
            "asesor": r.get("agente"),
            "id_caso": r.get("id_caso"),
            "bandeja": r.get("bandeja"),
            "pais": r.get("pais"),
            "motivo": r.get("critico_activado"),
            "nota_final": r.get("nota_final", 0),
            "revisado": bool(estado.get("revisado")),
            "revisado_en": estado.get("revisado_en"),
        })
    filas.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return filas[:limite]


def marcar_critico_revisado(clave: str, revisado: bool = True) -> dict:
    estados = _leer_json(CRITICOS_ESTADO_PATH, {})
    estados[clave] = {
        "revisado": bool(revisado),
        "revisado_en": datetime.now().isoformat(timespec="seconds") if revisado else None,
    }
    _guardar_json(CRITICOS_ESTADO_PATH, estados)
    return estados[clave]
