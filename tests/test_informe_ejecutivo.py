def test_generador_ejecutivo_esta_disponible():
    from informe_desempeno import generar_excel
    assert callable(generar_excel)


def test_plantilla_descarga_desde_formulario_principal():
    from pathlib import Path
    ruta = Path(__file__).resolve().parent.parent / "templates" / "informe_desempeno.html"
    texto = ruta.read_text(encoding="utf-8")
    assert 'formaction="/informe-desempeno/excel"' in texto
    assert "Generar y descargar informe" in texto
