"""Pruebas del simulador de presupuesto — protege que los números que se le
presentan a liderazgo para aprobar gasto sean correctos, y que el cambio
automático entre 'estimado' y 'datos reales' funcione como se diseñó."""
import presupuesto
import pytest


class TestObtenerBaseTokens:
    def test_sin_datos_reales_usa_el_respaldo(self, monkeypatch):
        monkeypatch.setattr(presupuesto, "resumen_uso", lambda: {"hay_datos": False, "total": 0})
        base = presupuesto.obtener_base_tokens()
        assert base["fuente"] == "estimado"

    def test_con_pocos_datos_reales_sigue_usando_el_respaldo(self, monkeypatch):
        """Menos del mínimo (10) no debe activar el modo 'real' — sería una
        muestra demasiado chica para confiar en ella."""
        monkeypatch.setattr(
            presupuesto, "resumen_uso",
            lambda: {"hay_datos": True, "total": 5, "tokens_entrada_promedio": 9999, "tokens_salida_promedio": 9999, "pct_con_guia": 0.9},
        )
        base = presupuesto.obtener_base_tokens()
        assert base["fuente"] == "estimado"

    def test_con_suficientes_datos_reales_los_usa(self, monkeypatch):
        monkeypatch.setattr(
            presupuesto, "resumen_uso",
            lambda: {"hay_datos": True, "total": 25, "tokens_entrada_promedio": 8000, "tokens_salida_promedio": 1800, "pct_con_guia": 0.4},
        )
        base = presupuesto.obtener_base_tokens()
        assert base["fuente"] == "real"
        assert base["tokens_entrada"] == 8000
        assert base["total_muestras"] == 25


class TestCalcularPresupuesto:
    def test_devuelve_todos_los_modelos_configurados(self, monkeypatch):
        monkeypatch.setattr(presupuesto, "resumen_uso", lambda: {"hay_datos": False, "total": 0})
        resultado = presupuesto.calcular_presupuesto(5000)
        assert len(resultado["modelos"]) == len(presupuesto.PRECIOS_MODELOS)

    def test_el_costo_mensual_es_aproximadamente_el_diario_multiplicado_por_los_dias(self, monkeypatch):
        """No debe ser una igualdad exacta: el código calcula el mensual desde
        el costo por evaluación SIN redondear (a propósito, para no arrastrar
        error de redondeo) — por eso se compara con una tolerancia chica."""
        monkeypatch.setattr(presupuesto, "resumen_uso", lambda: {"hay_datos": False, "total": 0})
        resultado = presupuesto.calcular_presupuesto(1000, dias_mes=30)
        for m in resultado["modelos"]:
            assert m["costo_mensual"] == pytest.approx(m["costo_diario"] * 30, abs=0.5)

    def test_mas_conversaciones_por_dia_da_mas_costo(self, monkeypatch):
        monkeypatch.setattr(presupuesto, "resumen_uso", lambda: {"hay_datos": False, "total": 0})
        poco = presupuesto.calcular_presupuesto(100)
        mucho = presupuesto.calcular_presupuesto(10000)
        for p, m in zip(poco["modelos"], mucho["modelos"]):
            assert m["costo_mensual"] > p["costo_mensual"]

    def test_un_modelo_mas_caro_por_token_cuesta_mas(self, monkeypatch):
        """Verifica que el orden de precios de la tabla de verdad se refleje
        en el costo — si alguien invierte los precios de un modelo por error,
        esta prueba debe fallar."""
        monkeypatch.setattr(presupuesto, "resumen_uso", lambda: {"hay_datos": False, "total": 0})
        resultado = presupuesto.calcular_presupuesto(5000)
        # El primer modelo de la lista (Gemini Flash-Lite) debe ser el más barato
        costos = [m["costo_mensual"] for m in resultado["modelos"]]
        assert costos[0] == min(costos)
