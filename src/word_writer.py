"""Genera el informe Word de evaluación de calidad, en el mismo formato que
los informes que el usuario ya elabora manualmente (ver ejemplo 'Casos...pdf'):
Bandeja / Asesor / ID / País -> Lo positivo -> Oportunidades de mejora -> Nota final.
"""
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NARANJA = RGBColor(0xF2, 0x65, 0x22)
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "dropi_logo.png"


def _shade_cell(cell: Any, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _bullet_con_negrita(doc: Any, texto_completo: str, negrita_hasta_primer_punto: bool = True) -> None:
    """Agrega un bullet donde el concepto inicial va en negrita, imitando el
    estilo del informe de ejemplo ('Diagnóstico correcto y bien fundamentado.
    Reconoció...'). Soporta que la IA separe el concepto con '.' o con ':'
    (ej. 'Concepto: explicación'), usando el que aparezca primero en el texto."""
    p = doc.add_paragraph(style="List Bullet")

    pos_punto = texto_completo.find(". ")
    pos_dospuntos = texto_completo.find(": ")
    candidatos = [pos for pos in (pos_punto, pos_dospuntos) if pos != -1]

    if negrita_hasta_primer_punto and candidatos:
        corte = min(candidatos)
        es_dos_puntos = corte == pos_dospuntos
        primera = texto_completo[:corte].strip()
        resto = texto_completo[corte + 2:].strip()  # +2 salta ". " o ": "
        run1 = p.add_run(primera + (":" if es_dos_puntos else "."))
        run1.bold = True
        if resto:
            p.add_run(" " + resto)
    else:
        p.add_run(texto_completo)
    return p


def generar_informe_word(evaluacion: dict, metadata: dict, nota: dict, ruta_salida: str) -> str:
    """
    evaluacion: dict con 'lo_positivo', 'oportunidades_mejora', 'resumen_caso'
    metadata: dict con 'agente', 'bandeja', 'id_caso', 'pais', 'fecha'
    nota: dict con 'nota_final', 'nota_bruta', 'critico_activado' (de scoring.py)
    """
    doc = Document()

    # Logo Dropi, centrado, al inicio del documento
    if LOGO_PATH.exists():
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.add_run().add_picture(str(LOGO_PATH), width=Inches(1.8))

    # Encabezado con datos del caso
    p = doc.add_paragraph()
    for etiqueta, valor in [
        ("Bandeja: ", metadata.get("bandeja", "")),
        ("Asesor: ", metadata.get("agente", "")),
        ("ID: ", metadata.get("id_caso", "")),
        ("País: ", metadata.get("pais", "")),
    ]:
        r1 = p.add_run(etiqueta)
        r1.bold = True
        p.add_run(valor + "\n" if valor != metadata.get("pais", "") else valor)

    if evaluacion.get("resumen_caso"):
        doc.add_paragraph()
        p_resumen = doc.add_paragraph()
        p_resumen.add_run(evaluacion["resumen_caso"]).italic = True

    # Si hubo crítico activado, aviso destacado
    if nota.get("critico_activado"):
        doc.add_paragraph()
        p_alerta = doc.add_paragraph()
        run = p_alerta.add_run(
            f"⚠ ÍTEM CRÍTICO DETECTADO: {nota['critico_activado']}. "
            f"La nota final se establece automáticamente en 0%, independientemente del puntaje acumulado en las demás categorías."
        )
        run.bold = True
        run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

    # Lo positivo
    doc.add_paragraph()
    h1 = doc.add_heading("Lo positivo", level=2)
    for punto in evaluacion.get("lo_positivo", []):
        _bullet_con_negrita(doc, punto)

    # Oportunidades de mejora
    doc.add_paragraph()
    doc.add_heading("Oportunidades de mejora", level=2)
    for punto in evaluacion.get("oportunidades_mejora", []):
        _bullet_con_negrita(doc, punto)

    # Tabla resumen tipo "matriz" (visual, como el bloque naranja del ejemplo)
    doc.add_paragraph()
    tabla = doc.add_table(rows=5, cols=2)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"

    tabla.cell(0, 0).merge(tabla.cell(0, 1))
    c = tabla.cell(0, 0)
    c.text = "MATRIZ DE CALIDAD - DROPI"
    _shade_cell(c, "F26522")
    run = c.paragraphs[0].runs[0]
    run.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.size = Pt(14)
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    filas = [
        ("Agente", metadata.get("agente", "")),
        ("Fecha", metadata.get("fecha", "")),
        ("ID", f"{metadata.get('id_caso', '')} - {metadata.get('bandeja', '')} - {metadata.get('pais', '')}"),
    ]
    for i, (etiqueta, valor) in enumerate(filas, start=1):
        tabla.cell(i, 0).text = etiqueta
        tabla.cell(i, 0).paragraphs[0].runs[0].bold = True
        tabla.cell(i, 1).text = str(valor)

    nota_pct = f"{nota['nota_final']*100:.0f}%"
    tabla.cell(4, 0).text = "NOTA FINAL"
    tabla.cell(4, 0).paragraphs[0].runs[0].bold = True
    c_nota = tabla.cell(4, 1)
    c_nota.text = nota_pct
    run_nota = c_nota.paragraphs[0].runs[0]
    run_nota.bold = True
    run_nota.font.size = Pt(20)
    run_nota.font.color.rgb = NARANJA if nota["nota_final"] >= 0.7 else RGBColor(0xC0, 0x00, 0x00)

    doc.save(ruta_salida)
    return ruta_salida
