import json

import fase3
from calibracion import calcular_calibracion


def test_riesgo_clasifica_conversacion_compleja():
    texto = "\n".join(["[CLIENTE] sigo esperando otra vez, necesito reembolso urgente"] * 45)
    r = fase3.analizar_riesgo_conversacion(texto, {"bandeja": "Garantías"})
    assert r["score"] >= 30
    assert r["nivel"] in {"medio", "alto"}
    assert r["mensajes_estimados"] == 45


def test_aprendizaje_solo_guarda_correcciones(monkeypatch, tmp_path):
    monkeypatch.setattr(fase3, "APRENDIZAJE_PATH", tmp_path / "aprendizaje.jsonl")
    monkeypatch.setattr(fase3, "_mapa_items", lambda: {
        "a": {"id": "a", "nombre": "A", "peso": .1, "categoria": "CAT"},
        "b": {"id": "b", "nombre": "B", "peso": .1, "categoria": "CAT"},
    })
    ia = {"items": {"a": {"puntaje": .1, "justificacion": "ok"}, "b": {"puntaje": .1, "justificacion": "ok"}}}
    fin = {"items": {"a": {"puntaje": .05, "justificacion": "faltó validar"}, "b": {"puntaje": .1, "justificacion": "ok"}}}
    ev = fase3.construir_eventos_aprendizaje(ia, fin, {"id_caso": "1"})
    assert len(ev) == 1
    assert ev[0]["item_id"] == "a"
    assert ev[0]["direccion"] == "ia_muy_blanda"
    assert fase3.guardar_eventos_aprendizaje(ev) == 1
    assert len(fase3.cargar_aprendizaje()) == 1


def test_confianza_no_es_alta_con_muestra_pequena(monkeypatch):
    monkeypatch.setattr(fase3, "_mapa_items", lambda: {
        "a": {"id": "a", "nombre": "A", "peso": .1, "categoria": "CAT"},
    })
    registros = [{"calibracion": {"items_comparados": [{"item_id": "a", "delta": 0}]}}]
    fila = fase3.confianza_por_item(registros)[0]
    assert fila["nivel"] == "baja"


def test_muestreo_inteligente_respeta_cantidad():
    candidatos = [
        {"token": str(i), "asesor": "A" if i < 5 else "B", "riesgo": {"score": i * 8, "senales": ["Conversación extensa"] if i % 2 else []}}
        for i in range(10)
    ]
    r = fase3.priorizar_muestra(candidatos, 5, {"A": 3, "B": 0})
    assert len(r["seleccionados"]) == 5
    assert sum(1 for x in r["todos"] if x["seleccionado"]) == 5
    assert any(x["motivo_seleccion"] == "Riesgo alto" for x in r["seleccionados"])


def test_calibracion_nueva_guarda_items_comparados():
    matriz = {"categorias": [{"nombre": "CAT", "items": [{"id": "a"}, {"id": "b"}]}]}
    ia = {"items": {"a": {"puntaje": .1}, "b": {"puntaje": .05}}, "items_criticos": {}}
    fin = {"items": {"a": {"puntaje": .1}, "b": {"puntaje": .03}}, "items_criticos": {}}
    cal = calcular_calibracion(ia, fin, matriz)
    assert len(cal["items_comparados"]) == 2
    assert sum(1 for x in cal["items_comparados"] if x["ajustado"]) == 1
    assert cal["porcentaje_acuerdo"] == .5
