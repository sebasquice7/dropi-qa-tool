"""Genera el plan de coaching de un asesor como documento Word, en el mismo
estilo visual que el resto de informes (logo, naranja Dropi, bullets con
negrita), para poder imprimirlo o adjuntarlo a una conversación de desarrollo.
"""
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NARANJA = RGBColor(0xF2, 0x65, 0x22)
GRIS = RGBColor(0x35, 0x30, 0x2B)
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "dropi_logo.png"


def _shade_cell(cell: Any, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _titulo_seccion(doc: Any, texto: str) -> Any:
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = NARANJA
    p.space_after = Pt(4)
    return p


def _bullet(doc: Any, texto: str) -> None:
    doc.add_paragraph(texto, style="List Bullet")


def generar_word_coaching(asesor: str, datos: dict, plan: dict, ruta_salida: str) -> str:
    """Genera el plan de coaching como documento Word descargable, con el mismo estilo visual que los demás informes."""
    doc = Document()

    if LOGO_PATH.exists():
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.add_run().add_picture(str(LOGO_PATH), width=Pt(110))

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run(f"Plan de Coaching — {asesor}")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = NARANJA

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub.add_run(
        f"Periodo analizado: {datos['primera_fecha']} a {datos['ultima_fecha']} "
        f"· {datos['total']} evaluaciones · Nota promedio: {round(datos['nota_promedio']*100,1)}%"
    )
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = GRIS
    doc.add_paragraph()

    _titulo_seccion(doc, "Resumen general")
    doc.add_paragraph(plan.get("resumen_general", ""))
    p_tend = doc.add_paragraph()
    p_tend.add_run("Tendencia: ").bold = True
    p_tend.add_run(plan.get("tendencia", ""))
    doc.add_paragraph()

    _titulo_seccion(doc, "✅ Fortalezas consistentes")
    for f in plan.get("fortalezas_consistentes", []):
        _bullet(doc, f)
    doc.add_paragraph()

    _titulo_seccion(doc, "⚠ Áreas prioritarias")
    for area in plan.get("areas_prioritarias", []):
        p = doc.add_paragraph()
        run_nombre = p.add_run(f"{area.get('area','')} (impacto {area.get('impacto','')}): ")
        run_nombre.bold = True
        p.add_run(area.get("evidencia", ""))
    doc.add_paragraph()

    _titulo_seccion(doc, "📋 Plan de acción para la próxima conversación de desarrollo")
    for i, accion in enumerate(plan.get("plan_accion", []), start=1):
        doc.add_paragraph(f"{i}. {accion}")
    doc.add_paragraph()

    _titulo_seccion(doc, "Desempeño por categoría (periodo analizado)")
    tabla = doc.add_table(rows=1, cols=2)
    tabla.style = "Light Grid Accent 2"
    hdr = tabla.rows[0].cells
    hdr[0].text, hdr[1].text = "Categoría", "Eficiencia"
    for cell in hdr:
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
        _shade_cell(cell, "404040")
    for cat, val in datos["categorias_ordenadas"]:
        row = tabla.add_row().cells
        row[0].text = cat
        row[1].text = f"{round(val*100,1)}%"

    doc.add_paragraph()
    nota_pie = doc.add_paragraph()
    run_pie = nota_pie.add_run("Generado por IA a partir del historial real de evaluaciones — revísalo antes de usarlo en la conversación con el asesor.")
    run_pie.italic = True
    run_pie.font.size = Pt(8)
    run_pie.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    doc.save(ruta_salida)
    return ruta_salida
