import fase2
from fase2 import ranking_perdida_puntos, _puntaje


def test_puntaje_acepta_numero_y_dict():
    assert _puntaje(0.04) == 0.04
    assert _puntaje({"puntaje": 0.03}) == 0.03
    assert _puntaje({"puntaje": 0.03, "aplica": False}) is None


def test_ranking_perdida_no_cuenta_items_ausentes_como_cero(monkeypatch):
    """La prueba no depende de los IDs reales/configurables de la matriz."""
    monkeypatch.setattr(
        fase2,
        "_matriz_items",
        lambda: {
            "item_prueba": {
                "id": "item_prueba",
                "nombre": "Ítem de prueba",
                "peso": 0.08,
                "categoria": "Categoría de prueba",
            }
        },
    )

    registros = [
        {"items_detalle": {"item_prueba": 0.0}},
        {"items_detalle": {}},
    ]

    filas = ranking_perdida_puntos(registros)
    fila = next(x for x in filas if x["id"] == "item_prueba")

    assert fila["veces_evaluado"] == 1
    assert fila["casos_con_perdida"] == 1
    assert fila["puntos_perdidos"] == 0.08
