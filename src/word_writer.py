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


def _pesos_maximos_categorias() -> dict:
    """{nombre_categoria: peso_máximo_decimal} — para convertir los puntos
    guardados en el historial a porcentajes comparables entre auditorías."""
    import json
    ruta_matriz = Path(__file__).resolve().parent.parent / "config" / "matriz_calidad.json"
    with open(ruta_matriz, encoding="utf-8") as f:
        matriz = json.load(f)
    return {cat["nombre"]: cat["peso_categoria"] for cat in matriz["categorias"]}


MAX_EVALUACIONES_PARA_PROMEDIO = 10


def _base_comparacion_del_asesor(agente: str) -> dict:
    """Trae hasta las últimas MAX_EVALUACIONES_PARA_PROMEDIO evaluaciones que
    YA existían en el historial para este asesor (antes de la que se está
    generando ahora mismo), y calcula el PROMEDIO por categoría entre ellas.

    Por qué promedio y no 'la evaluación anterior' sola: con el volumen real
    (~40 evaluaciones/asesor/mes), comparar contra un solo caso al azar es
    ruido — ese caso puede haber sido un tipo de conversación particularmente
    fácil o difícil, sin reflejar el desempeño real del asesor. El promedio
    de varios casos recientes es una base mucho más estable y justa.

    Devuelve None si es la primera evaluación registrada para este asesor."""
    try:
        from historial import cargar_historial
    except ImportError:
        return None

    registros = [r for r in cargar_historial() if r.get("agente") == agente]
    if not registros:
        return None

    registros.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    ultimos = registros[:MAX_EVALUACIONES_PARA_PROMEDIO]

    pesos_max = _pesos_maximos_categorias()
    suma_por_categoria = {}
    conteo_por_categoria = {}
    for r in ultimos:
        for cat, puntos in (r.get("categorias") or {}).items():
            peso_max = pesos_max.get(cat)
            if peso_max and puntos is not None:
                pct = min(puntos / peso_max, 1.0)
                suma_por_categoria[cat] = suma_por_categoria.get(cat, 0) + pct
                conteo_por_categoria[cat] = conteo_por_categoria.get(cat, 0) + 1

    promedio_por_categoria = {
        cat: suma_por_categoria[cat] / conteo_por_categoria[cat]
        for cat in suma_por_categoria
    }

    return {
        "cantidad": len(ultimos),
        "promedio_categorias": promedio_por_categoria,
    }


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

    # Título del documento — arriba del todo
    p_titulo = doc.add_paragraph()
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_titulo = p_titulo.add_run("DROPI / QA")
    run_titulo.bold = True
    run_titulo.font.size = Pt(16)
    run_titulo.font.color.rgb = NARANJA

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

    # Satisfacción del cliente (si se registró en la revisión)
    if evaluacion.get("satisfaccion"):
        emojis = {"muy_insatisfecho": "😠 Muy insatisfecho", "insatisfecho": "🙁 Insatisfecho", "neutral": "😐 Neutral", "satisfecho": "🙂 Satisfecho", "muy_satisfecho": "😄 Muy satisfecho"}
        doc.add_paragraph()
        p_satisf = doc.add_paragraph()
        p_satisf.add_run("Satisfacción del cliente: ").bold = True
        p_satisf.add_run(emojis.get(evaluacion["satisfaccion"], evaluacion["satisfaccion"]))
        if evaluacion.get("satisfaccion_comentarios"):
            p_satisf_com = doc.add_paragraph()
            p_satisf_com.add_run(evaluacion["satisfaccion_comentarios"]).italic = True

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

    # --- Retroalimentación: comparación contra el PROMEDIO de las últimas
    # evaluaciones de este asesor (una base estable, no un solo caso al azar
    # que puede no ser representativo) ---
    doc.add_paragraph()
    doc.add_heading("Retroalimentación — evolución frente a tu desempeño reciente", level=2)

    base = _base_comparacion_del_asesor(metadata.get("agente", ""))
    if not base:
        p_sin_anterior = doc.add_paragraph()
        p_sin_anterior.add_run(
            "Esta es la primera evaluación registrada para este asesor — no hay evaluaciones "
            "anteriores con las cuales comparar todavía."
        ).italic = True
    else:
        from historial import _subtotales_por_categoria
        cats_actual = _subtotales_por_categoria(evaluacion)
        promedio_reciente = base["promedio_categorias"]

        tabla_comp = doc.add_table(rows=1, cols=4)
        tabla_comp.style = "Table Grid"
        plural = "evaluación" if base["cantidad"] == 1 else f"últimas {base['cantidad']} evaluaciones"
        encabezados = ["Categoría", f"Promedio de tus {plural}", "Esta evaluación", "Cambio"]
        for i, texto in enumerate(encabezados):
            celda = tabla_comp.cell(0, i)
            celda.text = texto
            celda.paragraphs[0].runs[0].bold = True
            _shade_cell(celda, "F2E4DA")

        pesos_max = {cat: peso for cat, peso in _pesos_maximos_categorias().items()}
        for cat, puntos_actual in cats_actual.items():
            peso_max = pesos_max.get(cat)
            if not peso_max:
                continue
            # min(..., 1.0): si la matriz cambió de pesos entre una evaluación y
            # otra, un puntaje guardado con el peso viejo puede superar el
            # máximo actual — nunca debe mostrarse más de 100%.
            pct_actual = min(puntos_actual / peso_max, 1.0)
            pct_promedio = promedio_reciente.get(cat)
            fila = tabla_comp.add_row()
            fila.cells[0].text = cat
            if pct_promedio is None:
                fila.cells[1].text = "—"
                fila.cells[3].text = "—"
            else:
                fila.cells[1].text = f"{pct_promedio*100:.0f}%"
                diferencia = (pct_actual - pct_promedio) * 100
                simbolo = "▲" if diferencia > 0.5 else ("▼" if diferencia < -0.5 else "=")
                fila.cells[3].text = f"{simbolo} {diferencia:+.0f} pts"
                color_cambio = RGBColor(0x1D, 0x7A, 0x4C) if diferencia > 0.5 else (RGBColor(0xC0, 0x00, 0x00) if diferencia < -0.5 else RGBColor(0x6B, 0x67, 0x59))
                fila.cells[3].paragraphs[0].runs[0].font.color.rgb = color_cambio
            fila.cells[2].text = f"{pct_actual*100:.0f}%"

    doc.save(ruta_salida)
    return ruta_salida
