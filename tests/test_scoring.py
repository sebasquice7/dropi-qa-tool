"""Pruebas del cálculo de la nota final — la lógica más crítica del programa:
si esto falla silenciosamente, todas las evaluaciones quedan mal calculadas
sin que nadie lo note hasta mucho después.
"""
import json
from pathlib import Path

import pytest

from scoring import calcular_nota, normalizar_evaluacion

RAIZ = Path(__file__).resolve().parent.parent
MATRIZ = json.loads((RAIZ / "config" / "matriz_calidad.json").read_text(encoding="utf-8"))


def _primer_item_id() -> str:
    return MATRIZ["categorias"][0]["items"][0]["id"]


def _primer_critico_id() -> str:
    return MATRIZ["items_criticos"][0]["id"]


def _peso_de(item_id: str) -> float:
    for cat in MATRIZ["categorias"]:
        for it in cat["items"]:
            if it["id"] == item_id:
                return it["peso"]
    raise KeyError(item_id)


class TestCalcularNota:
    def test_suma_los_puntajes_de_todos_los_items(self):
        evaluacion = {
            "items": {"a": {"puntaje": 0.05}, "b": {"puntaje": 0.03}},
            "items_criticos": {},
        }
        resultado = calcular_nota(evaluacion)
        assert resultado["nota_bruta"] == 0.08
        assert resultado["nota_final"] == 0.08
        assert resultado["critico_activado"] is None

    def test_un_item_critico_activado_fuerza_la_nota_a_cero(self):
        """La regla de negocio más importante de todo el sistema: un solo ítem
        crítico en 'Si' anula cualquier puntaje que se haya ganado."""
        evaluacion = {
            "items": {"a": {"puntaje": 0.05}, "b": {"puntaje": 0.03}},
            "items_criticos": {"critico_de_prueba": {"ocurrio": "Si"}},
        }
        resultado = calcular_nota(evaluacion)
        assert resultado["nota_bruta"] == 0.08  # la nota bruta NO cambia
        assert resultado["nota_final"] == 0.0   # pero la final sí queda en cero
        assert resultado["critico_activado"] == "critico_de_prueba"

    def test_no_distingue_mayusculas_en_ocurrio(self):
        """'Si', 'SI', 'si' deben tratarse igual — la IA no siempre es consistente
        con las mayúsculas en su respuesta."""
        for variante in ("Si", "SI", "si", " Si "):
            evaluacion = {"items": {}, "items_criticos": {"x": {"ocurrio": variante}}}
            assert calcular_nota(evaluacion)["critico_activado"] == "x"

    def test_no_activado_cuando_dice_no(self):
        evaluacion = {"items": {"a": {"puntaje": 0.1}}, "items_criticos": {"x": {"ocurrio": "No"}}}
        resultado = calcular_nota(evaluacion)
        assert resultado["critico_activado"] is None
        assert resultado["nota_final"] == 0.1

    def test_evaluacion_vacia_no_revienta(self):
        resultado = calcular_nota({})
        assert resultado["nota_bruta"] == 0.0
        assert resultado["nota_final"] == 0.0
        assert resultado["critico_activado"] is None


class TestNormalizarEvaluacion:
    def test_puntaje_dentro_de_rango_no_se_toca(self):
        item_id = _primer_item_id()
        peso = _peso_de(item_id)
        valor_valido = round(peso * 0.6, 4)
        evaluacion = {"items": {item_id: {"puntaje": valor_valido, "justificacion": "ok"}}}
        resultado = normalizar_evaluacion(evaluacion)
        assert resultado["items"][item_id]["puntaje"] == valor_valido

    def test_reescala_un_puntaje_dado_en_porcentaje_entero(self):
        """Si la IA devuelve '5' queriendo decir '5%' (0.05), el sistema debe
        detectarlo y corregirlo — este es un error real que ya vimos ocurrir."""
        item_id = _primer_item_id()
        peso = _peso_de(item_id)  # ej. 0.05
        valor_mal_escalado = peso * 100  # ej. 5 en vez de 0.05
        evaluacion = {"items": {item_id: {"puntaje": valor_mal_escalado, "justificacion": "x"}}}
        resultado = normalizar_evaluacion(evaluacion)
        assert resultado["items"][item_id]["puntaje"] == pytest.approx(peso, abs=0.001)

    def test_nunca_deja_un_puntaje_negativo(self):
        item_id = _primer_item_id()
        evaluacion = {"items": {item_id: {"puntaje": -5, "justificacion": "x"}}}
        resultado = normalizar_evaluacion(evaluacion)
        assert resultado["items"][item_id]["puntaje"] >= 0

    def test_nunca_deja_un_puntaje_por_encima_del_maximo(self):
        item_id = _primer_item_id()
        peso = _peso_de(item_id)
        evaluacion = {"items": {item_id: {"puntaje": 999999, "justificacion": "x"}}}
        resultado = normalizar_evaluacion(evaluacion)
        assert resultado["items"][item_id]["puntaje"] <= peso

    def test_quita_asteriscos_de_markdown_en_todos_los_campos_de_texto(self):
        item_id = _primer_item_id()
        evaluacion = {
            "items": {item_id: {"puntaje": 0.01, "justificacion": "**Muy bien** hecho"}},
            "items_criticos": {"x": {"justificacion": "*no* ocurrió"}},
            "lo_positivo": ["**Punto fuerte**: excelente"],
            "oportunidades_mejora": ["Mejorar **esto**"],
            "resumen_caso": "**Resumen** del caso",
        }
        resultado = normalizar_evaluacion(evaluacion)
        assert "*" not in resultado["items"][item_id]["justificacion"]
        assert "*" not in resultado["items_criticos"]["x"]["justificacion"]
        assert "*" not in resultado["lo_positivo"][0]
        assert "*" not in resultado["oportunidades_mejora"][0]
        assert "*" not in resultado["resumen_caso"]

    def test_item_desconocido_en_la_matriz_se_ignora_sin_reventar(self):
        """Si la IA inventa un id de ítem que no existe en la matriz, el
        programa no debe caerse — simplemente lo ignora."""
        evaluacion = {"items": {"item_que_no_existe_en_la_matriz": {"puntaje": 1, "justificacion": "x"}}}
        resultado = normalizar_evaluacion(evaluacion)
        assert "item_que_no_existe_en_la_matriz" in resultado["items"]  # se preserva, no se recalcula
