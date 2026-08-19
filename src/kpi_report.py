"""Genera un Excel consolidado con KPIs, tablas resumen y gráficas, a partir
de una lista de registros del historial de evaluaciones (ver historial.py).
"""
from collections import defaultdict
from pathlib import Path
from typing import Any
from statistics import mean

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "dropi_logo.png"

NARANJA = "F26522"
GRIS = "404040"
GRIS_CLARO = "F2F2F2"
VERDE = "C6E0B4"
ROJO = "F4CCCC"


def rango_nota(nota: float) -> str:
    """Clasifica una nota en un rango legible (ej. 'Excelente', 'Bueno', 'Necesita mejora')."""
    pct = nota * 100
    if pct >= 90:
        return "90-100% (Excelente)"
    if pct >= 80:
        return "80-89% (Bueno)"
    if pct >= 70:
        return "70-79% (Aceptable)"
    return "< 70% (Crítico)"


_rango_nota = rango_nota  # alias interno, por compatibilidad


def calcular_kpis(registros: list) -> dict:
    """Calcula los indicadores agregados (promedios, distribución, por asesor) a partir de una lista de evaluaciones."""
    notas = [r["nota_final"] for r in registros]
    por_asesor = defaultdict(list)
    por_categoria = defaultdict(list)
    por_bandeja = defaultdict(int)
    por_rango = defaultdict(int)
    criticos = defaultdict(int)

    for r in registros:
        por_asesor[r["agente"]].append(r["nota_final"])
        por_bandeja[r.get("bandeja") or "Sin bandeja"] += 1
        por_rango[_rango_nota(r["nota_final"])] += 1
        for cat, val in (r.get("categorias") or {}).items():
            por_categoria[cat].append(val)
        if r.get("critico_activado"):
            criticos[r["critico_activado"]] += 1

    promedio_por_asesor = {a: round(mean(v), 4) for a, v in por_asesor.items()}
    promedio_por_categoria = {c: round(mean(v), 4) for c, v in por_categoria.items()}

    mejor_asesor = max(promedio_por_asesor.items(), key=lambda x: x[1]) if promedio_por_asesor else ("-", 0)
    peor_asesor = min(promedio_por_asesor.items(), key=lambda x: x[1]) if promedio_por_asesor else ("-", 0)

    con_critico = sum(1 for r in registros if r.get("critico_activado"))

    return {
        "total": len(registros),
        "nota_promedio": round(mean(notas), 4) if notas else 0,
        "pct_con_critico": round(con_critico / len(registros), 4) if registros else 0,
        "promedio_por_asesor": promedio_por_asesor,
        "promedio_por_categoria": promedio_por_categoria,
        "por_bandeja": dict(por_bandeja),
        "por_rango": dict(por_rango),
        "criticos": dict(criticos),
        "mejor_asesor": mejor_asesor,
        "peor_asesor": peor_asesor,
    }


def _escribir_titulo(ws: Any, texto: str, fila_inicio: int, fila_fin: int, col_inicio: str = "B", col_fin: str = "F") -> None:
    ws.merge_cells(f"{col_inicio}{fila_inicio}:{col_fin}{fila_fin}")
    c = ws[f"{col_inicio}{fila_inicio}"]
    c.value = texto
    c.font = Font(size=14, bold=True, color="FFFFFF")
    c.alignment = Alignment(horizontal="center", vertical="center")
    for fila in ws[f"{col_inicio}{fila_inicio}:{col_fin}{fila_fin}"]:
        for cell in fila:
            cell.fill = PatternFill("solid", fgColor=NARANJA)


def generar_informe_kpis(registros: list, ruta_salida: str, titulo: str = "Informe de Evaluaciones") -> str:
    """Genera el Excel de KPIs completo (resumen + detalle + tendencia) a partir del historial."""
    wb = Workbook()

    # ============== HOJA 1: RESUMEN / KPIs ==============
    ws = wb.active
    ws.title = "Resumen"
    ws.sheet_view.showGridLines = False
    for col, width in zip("ABCDEFGH", [3, 32, 14, 3, 3, 3, 4, 4]):
        ws.column_dimensions[col].width = width

    if LOGO_PATH.exists():
        ws.row_dimensions[1].height = 32
        logo = XLImage(str(LOGO_PATH))
        logo.width = 95
        logo.height = 32
        ws.add_image(logo, "B1")

    _escribir_titulo(ws, titulo, 2, 3)

    if not registros:
        ws["B5"] = "No hay evaluaciones registradas todavía para este rango."
        ws["B5"].font = Font(italic=True, color="777777")
        wb.save(ruta_salida)
        return ruta_salida

    kpis = calcular_kpis(registros)

    # --- Tarjetas de KPIs generales ---
    fila = 5
    tarjetas = [
        ("Total de evaluaciones", str(kpis["total"])),
        ("Nota promedio general", f"{kpis['nota_promedio']*100:.1f}%"),
        ("% con ítem crítico", f"{kpis['pct_con_critico']*100:.1f}%"),
        ("Mejor asesor", f"{kpis['mejor_asesor'][0]} ({kpis['mejor_asesor'][1]*100:.1f}%)"),
        ("Asesor a reforzar", f"{kpis['peor_asesor'][0]} ({kpis['peor_asesor'][1]*100:.1f}%)"),
    ]
    for etiqueta, valor in tarjetas:
        ws[f"B{fila}"] = etiqueta
        ws[f"B{fila}"].font = Font(bold=True)
        ws[f"C{fila}"] = valor
        ws[f"C{fila}"].font = Font(bold=True, color=NARANJA, size=12)
        fila += 1

    fila += 1

    # Las gráficas usan su PROPIO contador de fila (columna F en adelante),
    # con un salto fijo entre cada una, para que nunca se superpongan sin
    # importar cuántas filas ocupe la tabla de datos correspondiente.
    FILAS_POR_GRAFICA = 17
    fila_grafica = fila
    COL_GRAFICA = "G"

    # --- Tabla: promedio por asesor ---
    ws[f"B{fila}"] = "Nota promedio por asesor"
    ws[f"B{fila}"].font = Font(bold=True)
    fila += 1
    ws[f"B{fila}"] = "Asesor"
    ws[f"C{fila}"] = "Nota"
    for col in "BC":
        ws[f"{col}{fila}"].font = Font(bold=True, color="FFFFFF")
        ws[f"{col}{fila}"].fill = PatternFill("solid", fgColor=GRIS)
    fila_encabezado_asesor = fila
    fila += 1
    fila_datos_asesor_inicio = fila
    for asesor, valor in sorted(kpis["promedio_por_asesor"].items(), key=lambda x: -x[1]):
        ws[f"B{fila}"] = asesor
        ws[f"C{fila}"] = valor
        ws[f"C{fila}"].number_format = "0.0%"
        fila += 1
    fila_datos_asesor_fin = fila - 1

    if fila_datos_asesor_fin >= fila_datos_asesor_inicio:
        chart = BarChart()
        chart.title = "Nota promedio por asesor"
        chart.y_axis.title = "Nota"
        chart.y_axis.numFmt = "0%"
        datos = Reference(ws, min_col=3, min_row=fila_encabezado_asesor, max_row=fila_datos_asesor_fin)
        categorias_ref = Reference(ws, min_col=2, min_row=fila_datos_asesor_inicio, max_row=fila_datos_asesor_fin)
        chart.add_data(datos, titles_from_data=True)
        chart.set_categories(categorias_ref)
        chart.width = 16
        chart.height = 8
        ws.add_chart(chart, f"{COL_GRAFICA}{fila_grafica}")
    fila_grafica += FILAS_POR_GRAFICA

    fila += 2

    # --- Tabla: promedio por categoría de la matriz ---
    ws[f"B{fila}"] = "Nota promedio por categoría de la matriz"
    ws[f"B{fila}"].font = Font(bold=True)
    fila += 1
    ws[f"B{fila}"] = "Categoría"
    ws[f"C{fila}"] = "Nota"
    for col in "BC":
        ws[f"{col}{fila}"].font = Font(bold=True, color="FFFFFF")
        ws[f"{col}{fila}"].fill = PatternFill("solid", fgColor=GRIS)
    fila_encabezado_cat = fila
    fila += 1
    fila_datos_cat_inicio = fila
    for cat, valor in kpis["promedio_por_categoria"].items():
        ws[f"B{fila}"] = cat
        ws[f"C{fila}"] = valor
        ws[f"C{fila}"].number_format = "0.0%"
        fila += 1
    fila_datos_cat_fin = fila - 1

    if fila_datos_cat_fin >= fila_datos_cat_inicio:
        chart2 = BarChart()
        chart2.title = "Nota promedio por categoría"
        chart2.y_axis.numFmt = "0%"
        datos2 = Reference(ws, min_col=3, min_row=fila_encabezado_cat, max_row=fila_datos_cat_fin)
        categorias_ref2 = Reference(ws, min_col=2, min_row=fila_datos_cat_inicio, max_row=fila_datos_cat_fin)
        chart2.add_data(datos2, titles_from_data=True)
        chart2.set_categories(categorias_ref2)
        chart2.width = 16
        chart2.height = 8
        ws.add_chart(chart2, f"{COL_GRAFICA}{fila_grafica}")
    fila_grafica += FILAS_POR_GRAFICA

    fila += 2

    # --- Tabla: distribución de notas por rango ---
    ws[f"B{fila}"] = "Distribución de notas"
    ws[f"B{fila}"].font = Font(bold=True)
    fila += 1
    ws[f"B{fila}"] = "Rango"
    ws[f"C{fila}"] = "Cantidad"
    for col in "BC":
        ws[f"{col}{fila}"].font = Font(bold=True, color="FFFFFF")
        ws[f"{col}{fila}"].fill = PatternFill("solid", fgColor=GRIS)
    fila_datos_rango_inicio = fila + 1
    fila += 1
    orden_rangos = ["90-100% (Excelente)", "80-89% (Bueno)", "70-79% (Aceptable)", "< 70% (Crítico)"]
    for rango in orden_rangos:
        cantidad = kpis["por_rango"].get(rango, 0)
        if cantidad == 0:
            continue
        ws[f"B{fila}"] = rango
        ws[f"C{fila}"] = cantidad
        fila += 1
    fila_datos_rango_fin = fila - 1

    if fila_datos_rango_fin >= fila_datos_rango_inicio:
        pie = PieChart()
        pie.title = "Distribución de notas"
        datos3 = Reference(ws, min_col=3, min_row=fila_datos_rango_inicio, max_row=fila_datos_rango_fin)
        categorias_ref3 = Reference(ws, min_col=2, min_row=fila_datos_rango_inicio, max_row=fila_datos_rango_fin)
        pie.add_data(datos3)
        pie.set_categories(categorias_ref3)
        pie.width = 12
        pie.height = 8
        ws.add_chart(pie, f"{COL_GRAFICA}{fila_grafica}")
    fila_grafica += FILAS_POR_GRAFICA

    fila += 2

    # --- Ítems críticos detectados (si hay) ---
    if kpis["criticos"]:
        ws[f"B{fila}"] = "⚠ Ítems críticos detectados en el periodo"
        ws[f"B{fila}"].font = Font(bold=True, color="C00000")
        fila += 1
        for item, cantidad in sorted(kpis["criticos"].items(), key=lambda x: -x[1]):
            ws[f"B{fila}"] = item
            ws[f"C{fila}"] = cantidad
            ws[f"B{fila}"].fill = PatternFill("solid", fgColor=ROJO)
            ws[f"C{fila}"].fill = PatternFill("solid", fgColor=ROJO)
            fila += 1

    # ============== HOJA 2: DETALLE ==============
    ws2 = wb.create_sheet("Detalle")
    ws2.sheet_view.showGridLines = False
    encabezados = ["Fecha", "Asesor", "Bandeja", "ID Caso", "País", "Nota Final", "Ítem Crítico"]
    for col, width in zip("ABCDEFG", [12, 22, 18, 18, 12, 12, 30]):
        ws2.column_dimensions[col].width = width
    for i, enc in enumerate(encabezados, start=1):
        c = ws2.cell(row=1, column=i, value=enc)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=GRIS)
        c.alignment = Alignment(horizontal="center")

    for i, r in enumerate(sorted(registros, key=lambda x: x["timestamp"], reverse=True), start=2):
        ws2.cell(row=i, column=1, value=r.get("fecha", ""))
        ws2.cell(row=i, column=2, value=r.get("agente", ""))
        ws2.cell(row=i, column=3, value=r.get("bandeja", ""))
        ws2.cell(row=i, column=4, value=r.get("id_caso", ""))
        ws2.cell(row=i, column=5, value=r.get("pais", ""))
        celda_nota = ws2.cell(row=i, column=6, value=r.get("nota_final", 0))
        celda_nota.number_format = "0.0%"
        critico = r.get("critico_activado") or ""
        celda_critico = ws2.cell(row=i, column=7, value=critico)
        if critico:
            for col in range(1, 8):
                ws2.cell(row=i, column=col).fill = PatternFill("solid", fgColor=ROJO)

    # ============== HOJA 3: TENDENCIA (evolución por asesor en el tiempo) ==============
    _agregar_hoja_tendencia(wb, registros)

    wb.save(ruta_salida)
    return ruta_salida


def _agregar_hoja_tendencia(wb: Any, registros: list) -> None:
    """Tabla + gráfica de líneas: nota promedio por asesor, por fecha."""
    datos = defaultdict(lambda: defaultdict(list))
    asesores_set = set()
    for r in registros:
        datos[r.get("fecha", "")][r.get("agente", "")].append(r.get("nota_final", 0))
        if r.get("agente"):
            asesores_set.add(r["agente"])

    fechas = sorted(d for d in datos.keys() if d)
    asesores = sorted(asesores_set)
    if not fechas or not asesores:
        return  # no hay suficiente data todavía para una tendencia

    ws = wb.create_sheet("Tendencia")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 14
    for i in range(len(asesores)):
        ws.column_dimensions[get_column_letter(2 + i)].width = 18

    ws["A1"] = "Fecha"
    ws["A1"].font = Font(bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=GRIS)
    for i, asesor in enumerate(asesores):
        c = ws.cell(row=1, column=2 + i, value=asesor)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=GRIS)

    for r_idx, fecha in enumerate(fechas, start=2):
        ws.cell(row=r_idx, column=1, value=fecha)
        for c_idx, asesor in enumerate(asesores, start=2):
            valores = datos[fecha].get(asesor)
            if valores:
                celda = ws.cell(row=r_idx, column=c_idx, value=round(mean(valores), 4))
                celda.number_format = "0.0%"

    ultima_fila = len(fechas) + 1

    chart = LineChart()
    chart.title = "Tendencia de nota promedio por asesor"
    chart.y_axis.numFmt = "0%"
    chart.width = 26
    chart.height = 11
    datos_ref = Reference(ws, min_col=2, max_col=1 + len(asesores), min_row=1, max_row=ultima_fila)
    categorias_ref = Reference(ws, min_col=1, min_row=2, max_row=ultima_fila)
    chart.add_data(datos_ref, titles_from_data=True)
    chart.set_categories(categorias_ref)
    ws.add_chart(chart, f"A{ultima_fila + 3}")
