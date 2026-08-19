"""Calcula los datos agregados para el dashboard web en vivo: KPIs generales,
filtros por país/bandeja/periodo, comparación contra el periodo anterior,
"problemas más frecuentes" (categorías e ítems específicos con peor rendimiento
relativo), temas recurrentes en las oportunidades de mejora, y tendencia.

No genera archivos (a diferencia de kpi_report.py, que genera el Excel) — este
módulo alimenta directamente la página /dashboard vía una respuesta JSON.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

from config import config
from historial import cargar_historial, tendencia_por_asesor
from kpi_report import calcular_kpis, rango_nota

BASE_DIR = Path(__file__).resolve().parent.parent
MATRIZ_PATH = BASE_DIR / "config" / "matriz_calidad.json"
META_PATH = BASE_DIR / "config" / "meta_calidad.json"

STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "en", "y", "a", "un", "una", "unos", "unas",
    "que", "con", "para", "por", "su", "sus", "se", "no", "lo", "al", "es", "fue", "ser",
    "muy", "más", "sin", "esta", "este", "estos", "estas", "sobre", "como", "pero",
    "asesor", "asesora", "cliente", "usuario", "caso", "conversación", "conversacion",
    "durante", "sino", "entre", "cuando", "tras", "así", "ya", "le", "les", "o", "u",
}


def _cargar_matriz() -> dict:
    with open(MATRIZ_PATH, encoding="utf-8") as f:
        return json.load(f)


def _pesos_por_categoria() -> dict:
    matriz = _cargar_matriz()
    return {cat["nombre"]: cat["peso_categoria"] for cat in matriz["categorias"]}


def _mapa_items() -> dict:
    """id_item -> {'nombre':..., 'peso':..., 'categoria':...}"""
    matriz = _cargar_matriz()
    mapa = {}
    for cat in matriz["categorias"]:
        for it in cat["items"]:
            mapa[it["id"]] = {"nombre": it["nombre"], "peso": it["peso"], "categoria": cat["nombre"]}
    return mapa


# ---------------- Meta de calidad (configurable desde el dashboard) ----------------

def obtener_meta() -> float:
    """Meta de calidad configurada (archivo local, o META_CALIDAD del .env como respaldo)."""
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8")).get("meta", 0.85)
        except (json.JSONDecodeError, OSError):
            pass
    return config.meta_calidad


def guardar_meta(valor: float) -> None:
    """Guarda la meta de calidad en el archivo local, para que persista entre reinicios."""
    META_PATH.write_text(json.dumps({"meta": valor}, ensure_ascii=False), encoding="utf-8")


# ---------------- Filtros: país, bandeja, periodo ----------------

def _filtrar(registros: list, pais: str = None, bandeja: str = None) -> list:
    if pais:
        registros = [r for r in registros if (r.get("pais") or "") == pais]
    if bandeja:
        registros = [r for r in registros if (r.get("bandeja") or "") == bandeja]
    return registros


def _rango_fechas(periodo: str) -> tuple:
    """Devuelve (fecha_inicio, fecha_fin, fecha_inicio_anterior, fecha_fin_anterior)
    como strings YYYY-MM-DD, o (None, None, None, None) si es 'todo' (sin límite)."""
    hoy = datetime.now().date()

    if periodo == "hoy":
        inicio = fin = hoy
        inicio_ant = fin_ant = hoy - timedelta(days=1)
    elif periodo == "semana":
        inicio = hoy - timedelta(days=hoy.weekday())  # lunes de esta semana
        fin = hoy
        inicio_ant = inicio - timedelta(days=7)
        fin_ant = inicio - timedelta(days=1)
    elif periodo == "mes":
        inicio = hoy.replace(day=1)
        fin = hoy
        ultimo_dia_mes_ant = inicio - timedelta(days=1)
        inicio_ant = ultimo_dia_mes_ant.replace(day=1)
        fin_ant = ultimo_dia_mes_ant
    else:  # "todo"
        return None, None, None, None

    return inicio.isoformat(), fin.isoformat(), inicio_ant.isoformat(), fin_ant.isoformat()


def _en_rango(registros: list, inicio: str, fin: str) -> list:
    if inicio is None:
        return registros
    return [r for r in registros if inicio <= (r.get("fecha") or "") <= fin]


# ---------------- Eficiencia por categoría e ítem (para "problemas frecuentes") ----------------

def _eficiencia_por_categoria(promedio_por_categoria: dict) -> list:
    pesos_max = _pesos_por_categoria()
    filas = []
    for cat, promedio in promedio_por_categoria.items():
        peso_max = pesos_max.get(cat, 0)
        eficiencia = (promedio / peso_max) if peso_max > 0 else 0
        filas.append({"categoria": cat, "eficiencia": round(eficiencia, 4), "promedio_absoluto": round(promedio, 4)})
    filas.sort(key=lambda f: f["eficiencia"])
    return filas


def _eficiencia_por_item(registros: list) -> dict:
    """{categoria: [{item_id, item_nombre, eficiencia}, ...]} ordenado de peor a
    mejor DENTRO de cada categoría, a partir de items_detalle (solo disponible en
    evaluaciones hechas después de esta actualización)."""
    mapa = _mapa_items()
    por_item = defaultdict(list)
    for r in registros:
        detalle = r.get("items_detalle") or {}
        for iid, puntaje in detalle.items():
            por_item[iid].append(puntaje)

    resultado = defaultdict(list)
    for iid, valores in por_item.items():
        info = mapa.get(iid)
        if not info or not info["peso"]:
            continue
        eficiencia = mean(valores) / info["peso"]
        resultado[info["categoria"]].append({
            "item_id": iid,
            "item_nombre": info["nombre"],
            "eficiencia": round(eficiencia, 4),
        })

    for cat in resultado:
        resultado[cat].sort(key=lambda f: f["eficiencia"])
    return dict(resultado)


# ---------------- Temas recurrentes en "oportunidades de mejora" ----------------

def _concepto(texto: str) -> str:
    """Extrae la primera frase corta (antes del primer '.' o ':'), igual que la
    lógica que usa el Word para decidir qué poner en negrita."""
    pos_punto = texto.find(". ")
    pos_dospuntos = texto.find(": ")
    candidatos = [p for p in (pos_punto, pos_dospuntos) if p != -1]
    return texto[:min(candidatos)] if candidatos else texto


def _temas_recurrentes(registros: list, top_n: int = 8) -> list:
    contador = Counter()
    for r in registros:
        for punto in r.get("oportunidades_mejora") or []:
            concepto = _concepto(punto).lower()
            palabras = re.findall(r"[a-záéíóúñ]{4,}", concepto)
            for palabra in palabras:
                if palabra not in STOPWORDS:
                    contador[palabra] += 1
    return [{"palabra": p, "conteo": c} for p, c in contador.most_common(top_n)]


# ---------------- Detalle y tabla por asesor ----------------

def _detalle_por_asesor(registros: list) -> list:
    pesos_max = _pesos_por_categoria()
    agrupado = defaultdict(list)
    for r in registros:
        agrupado[r.get("agente", "Sin nombre")].append(r)

    filas = []
    for asesor, evals in agrupado.items():
        notas = [e["nota_final"] for e in evals]
        criticos = sum(1 for e in evals if e.get("critico_activado"))

        por_cat = defaultdict(list)
        for e in evals:
            for cat, val in (e.get("categorias") or {}).items():
                por_cat[cat].append(val)
        eficiencias_cat = {
            cat: (mean(vals) / pesos_max[cat]) if pesos_max.get(cat) else 0
            for cat, vals in por_cat.items()
        }
        categoria_debil = min(eficiencias_cat, key=eficiencias_cat.get) if eficiencias_cat else None

        filas.append({
            "asesor": asesor,
            "total_evaluaciones": len(evals),
            "nota_promedio": round(mean(notas), 4),
            "mejor_nota": round(max(notas), 4),
            "peor_nota": round(min(notas), 4),
            "criticos": criticos,
            "categoria_debil": categoria_debil,
            "categorias_eficiencia": {k: round(v, 4) for k, v in eficiencias_cat.items()},
            "ultima_fecha": max(e.get("fecha", "") for e in evals),
        })

    filas.sort(key=lambda f: -f["nota_promedio"])
    return filas


# ---------------- Función principal ----------------

def _promedio_por_pais(registros: list) -> dict:
    por_pais = defaultdict(list)
    for r in registros:
        if r.get("pais"):
            por_pais[r["pais"]].append(r["nota_final"])
    return {
        pais: {"nota_promedio": round(mean(notas), 4), "total": len(notas)}
        for pais, notas in por_pais.items()
    }


def obtener_datos_dashboard(periodo: str = "todo", pais: str = None, bandeja: str = None) -> dict:
    """Arma todos los datos que consume el dashboard en vivo: KPIs, comparativas, tendencias, mapa de calor y más — filtrados por periodo/país/bandeja."""
    todos = cargar_historial()

    paises_disponibles = sorted({r.get("pais") for r in todos if r.get("pais")})
    bandejas_disponibles = sorted({r.get("bandeja") for r in todos if r.get("bandeja")})

    base = _filtrar(todos, pais=pais, bandeja=bandeja)
    inicio, fin, inicio_ant, fin_ant = _rango_fechas(periodo)
    registros = _en_rango(base, inicio, fin)
    registros_periodo_anterior = _en_rango(base, inicio_ant, fin_ant) if inicio_ant else []

    # Comparativa por país: se calcula SIN aplicar el filtro de país (para
    # poder comparar siempre entre todos), pero sí respeta el periodo/bandeja.
    base_para_paises = _filtrar(todos, pais=None, bandeja=bandeja)
    registros_para_paises = _en_rango(base_para_paises, inicio, fin)
    promedio_por_pais = _promedio_por_pais(registros_para_paises)

    meta = obtener_meta()

    resultado = {
        "hay_datos": bool(registros),
        "total": len(registros),
        "meta": meta,
        "paises_disponibles": paises_disponibles,
        "bandejas_disponibles": bandejas_disponibles,
        "filtros_activos": {"periodo": periodo, "pais": pais or "", "bandeja": bandeja or ""},
    }
    if not registros:
        return resultado

    kpis = calcular_kpis(registros)
    eficiencia_categorias = _eficiencia_por_categoria(kpis["promedio_por_categoria"])
    eficiencia_items = _eficiencia_por_item(registros)
    por_asesor_detalle = _detalle_por_asesor(registros)
    tendencia = tendencia_por_asesor(registros)
    temas = _temas_recurrentes(registros)

    fechas_ordenadas = sorted(tendencia.keys())
    asesores_ordenados = sorted({a for por_fecha in tendencia.values() for a in por_fecha.keys()})

    # --- Comparación contra el periodo anterior equivalente ---
    comparacion = None
    if registros_periodo_anterior:
        nota_anterior = mean(r["nota_final"] for r in registros_periodo_anterior)
        comparacion = {
            "hay_comparacion": True,
            "total_anterior": len(registros_periodo_anterior),
            "nota_promedio_anterior": round(nota_anterior, 4),
            "delta_nota": round(kpis["nota_promedio"] - nota_anterior, 4),
        }
    else:
        comparacion = {"hay_comparacion": False}

    resultado.update({
        "nota_promedio": kpis["nota_promedio"],
        "pct_con_critico": kpis["pct_con_critico"],
        "mejor_asesor": {"nombre": kpis["mejor_asesor"][0], "nota": kpis["mejor_asesor"][1]},
        "peor_asesor": {"nombre": kpis["peor_asesor"][0], "nota": kpis["peor_asesor"][1]},
        "promedio_por_asesor": kpis["promedio_por_asesor"],
        "eficiencia_categorias": eficiencia_categorias,
        "eficiencia_items": eficiencia_items,
        "hay_detalle_items": bool(eficiencia_items),
        "por_rango": kpis["por_rango"],
        "criticos": kpis["criticos"],
        "por_asesor_detalle": por_asesor_detalle,
        "temas_recurrentes": temas,
        "promedio_por_pais": promedio_por_pais,
        "hay_texto_oportunidades": any(r.get("oportunidades_mejora") for r in registros),
        "comparacion": comparacion,
        "tendencia": {
            "fechas": fechas_ordenadas,
            "asesores": asesores_ordenados,
            "series": {
                asesor: [tendencia.get(fecha, {}).get(asesor) for fecha in fechas_ordenadas]
                for asesor in asesores_ordenados
            },
        },
    })
    return resultado
