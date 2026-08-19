"""Pruebas de la calibración IA vs. humano — protege el reporte que le da
credibilidad a la herramienta frente a liderazgo, así que sus números no
pueden estar mal calculados."""
from calibracion import calcular_calibracion, resumen_calibracion

MATRIZ_PRUEBA = {
    "categorias": [
        {"nombre": "CAT_A", "items": [{"id": "item1", "peso": 0.10}, {"id": "item2", "peso": 0.05}]},
        {"nombre": "CAT_B", "items": [{"id": "item3", "peso": 0.08}]},
    ]
}


class TestCalcularCalibracion:
    def test_acuerdo_perfecto_cuando_nada_cambia(self):
        ia = {"items": {"item1": {"puntaje": 0.10}, "item2": {"puntaje": 0.05}}, "items_criticos": {}}
        final = {"items": {"item1": {"puntaje": 0.10}, "item2": {"puntaje": 0.05}}, "items_criticos": {}}
        resultado = calcular_calibracion(ia, final, MATRIZ_PRUEBA)
        assert resultado["porcentaje_acuerdo"] == 1.0
        assert resultado["items_ajustados"] == []

    def test_detecta_un_item_subido_por_el_auditor(self):
        ia = {"items": {"item1": {"puntaje": 0.05}, "item2": {"puntaje": 0.05}}, "items_criticos": {}}
        final = {"items": {"item1": {"puntaje": 0.10}, "item2": {"puntaje": 0.05}}, "items_criticos": {}}
        resultado = calcular_calibracion(ia, final, MATRIZ_PRUEBA)
        assert resultado["porcentaje_acuerdo"] == 0.5  # 1 de 2 items cambió
        assert len(resultado["items_ajustados"]) == 1
        ajuste = resultado["items_ajustados"][0]
        assert ajuste["item_id"] == "item1"
        assert ajuste["delta"] == 0.05  # positivo = el auditor subió el puntaje

    def test_diferencias_de_redondeo_insignificantes_no_cuentan_como_ajuste(self):
        """Diferencias menores a 0.0005 son ruido de punto flotante, no una
        corrección real del auditor — no deben ensuciar el reporte."""
        ia = {"items": {"item1": {"puntaje": 0.0500001}}, "items_criticos": {}}
        final = {"items": {"item1": {"puntaje": 0.0500002}}, "items_criticos": {}}
        resultado = calcular_calibracion(ia, final, MATRIZ_PRUEBA)
        assert resultado["porcentaje_acuerdo"] == 1.0

    def test_detecta_un_critico_que_el_auditor_corrigio(self):
        """Este es el caso real que motivó esta funcionalidad: la IA marca un
        crítico y el auditor lo corrige a 'No' (o viceversa)."""
        ia = {"items": {}, "items_criticos": {"cierra_sin_resolver": {"ocurrio": "Si"}}}
        final = {"items": {}, "items_criticos": {"cierra_sin_resolver": {"ocurrio": "No"}}}
        resultado = calcular_calibracion(ia, final, MATRIZ_PRUEBA)
        assert len(resultado["criticos_cambiados"]) == 1
        assert resultado["criticos_cambiados"][0]["item_id"] == "cierra_sin_resolver"
        assert resultado["criticos_cambiados"][0]["ia"] == "si"
        assert resultado["criticos_cambiados"][0]["final"] == "no"

    def test_delta_por_categoria_agrupa_correctamente(self):
        ia = {"items": {"item1": {"puntaje": 0.00}, "item2": {"puntaje": 0.00}, "item3": {"puntaje": 0.00}}, "items_criticos": {}}
        final = {"items": {"item1": {"puntaje": 0.10}, "item2": {"puntaje": 0.05}, "item3": {"puntaje": 0.00}}, "items_criticos": {}}
        resultado = calcular_calibracion(ia, final, MATRIZ_PRUEBA)
        # item1 e item2 son de CAT_A (delta 0.10 y 0.05 -> promedio 0.075); item3 (CAT_B) no cambió
        assert resultado["delta_por_categoria"]["CAT_A"] == 0.075
        assert "CAT_B" not in resultado["delta_por_categoria"]

    def test_sin_items_no_revienta(self):
        resultado = calcular_calibracion({"items": {}}, {"items": {}}, MATRIZ_PRUEBA)
        assert resultado["porcentaje_acuerdo"] == 0
        assert resultado["items_ajustados"] == []


class TestResumenCalibracion:
    def test_sin_registros_con_calibracion_devuelve_hay_datos_false(self):
        registros = [{"agente": "x", "calibracion": None}, {"agente": "y"}]
        resultado = resumen_calibracion(registros)
        assert resultado["hay_datos"] is False

    def test_promedia_el_porcentaje_de_acuerdo_entre_varias_evaluaciones(self):
        registros = [
            {"calibracion": {"porcentaje_acuerdo": 1.0, "delta_por_categoria": {}, "criticos_cambiados": []}},
            {"calibracion": {"porcentaje_acuerdo": 0.5, "delta_por_categoria": {}, "criticos_cambiados": []}},
        ]
        resultado = resumen_calibracion(registros)
        assert resultado["hay_datos"] is True
        assert resultado["total_con_calibracion"] == 2
        assert resultado["porcentaje_acuerdo_promedio"] == 0.75

    def test_cuenta_la_frecuencia_de_criticos_corregidos(self):
        registros = [
            {"calibracion": {"porcentaje_acuerdo": 1.0, "delta_por_categoria": {}, "criticos_cambiados": [{"item_id": "maltrato_cliente"}]}},
            {"calibracion": {"porcentaje_acuerdo": 1.0, "delta_por_categoria": {}, "criticos_cambiados": [{"item_id": "maltrato_cliente"}]}},
        ]
        resultado = resumen_calibracion(registros)
        assert resultado["criticos_cambiados_frecuencia"]["maltrato_cliente"] == 2
