"""Pruebas de Nube QA (asistente flotante). Se corren con:  python -m pytest tests/test_asistente_qa.py -q
Usan SIEMPRE el modo demo (datos de ejemplo): no tocan el historial ni la configuración reales."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))

import asistente_qa as A  # noqa: E402


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    app = A.crear_app_demo()
    monkeypatch.setattr(A, "_data_dir", lambda: tmp_path)   # el store y la auditoría van a una carpeta temporal
    A._PENDIENTES.clear()
    return app.test_client()


def chat(c, msg, hist=None):
    r = c.post("/asistente/chat", json={"mensaje": msg, "historial": hist or []})
    assert r.status_code == 200
    return r.get_json()


def test_widget_se_inyecta_en_paginas_html(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "nube-qa-host" in html and "</body>" in html and html.count("nube-qa-host") >= 1


def test_widget_no_se_inyecta_dos_veces_ni_en_la_api(cliente):
    assert cliente.get("/asistente/estado").get_json()["demo"] is True
    assert b"nube-qa-host" not in cliente.get("/asistente/estado").data


def test_script_root_se_escapa():
    h = A._widget_html('/qa"><script>alert(1)</script>')
    assert '"><script>alert(1)' not in h.split("</script>")[0].split("data-base=")[1][:60]


def test_resumen_y_rankings(cliente):
    assert "Resumen" in chat(cliente, "Resumen del equipo")["respuesta"]
    peores = chat(cliente, "Peores 3 asesores")["respuesta"]
    mejores = chat(cliente, "Mejores 3 asesores")["respuesta"]
    assert peores.count("\n") == 3 and mejores.count("\n") == 3 and peores != mejores


def test_detalle_de_asesor_por_nombre_parcial(cliente):
    assert "Camila Torres" in chat(cliente, "cómo va camila torres")["respuesta"]


def test_cambio_de_meta_exige_confirmacion(cliente):
    j = chat(cliente, "Pon la meta en 88")
    assert len(j["propuestas"]) == 1
    assert A._meta() == 0.85                      # aún no cambió nada
    r = cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": True}).get_json()
    assert r["ok"] and A._meta() == 0.88


def test_cancelar_no_cambia_nada(cliente):
    j = chat(cliente, "Pon la meta en 90")
    r = cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": False}).get_json()
    assert r["ok"] and A._meta() == 0.85


def test_meta_fuera_de_rango_se_rechaza(cliente):
    assert chat(cliente, "Pon la meta en 20")["propuestas"] == []


def test_una_propuesta_solo_se_ejecuta_una_vez(cliente):
    pid = chat(cliente, "Pon la meta en 87")["propuestas"][0]["id"]
    assert cliente.post("/asistente/confirmar", json={"id": pid, "aceptar": True}).get_json()["ok"]
    assert not cliente.post("/asistente/confirmar", json={"id": pid, "aceptar": True}).get_json()["ok"]


def test_propuesta_caducada(cliente, monkeypatch):
    pid = chat(cliente, "Pon la meta en 87")["propuestas"][0]["id"]
    A._PENDIENTES[pid]["creado"] -= A.TTL_PROPUESTA + 5
    assert not cliente.post("/asistente/confirmar", json={"id": pid, "aceptar": True}).get_json()["ok"]


def test_coaching_maximo_dos_compromisos(cliente):
    assert chat(cliente, "Sesión de coaching con Camila Torres. Compromisos: a; b; c")["propuestas"] == []
    assert chat(cliente, "Sesión de coaching con Camila Torres. Compromisos:")["propuestas"] == []


def test_ciclo_de_coaching_completo(cliente):
    for i in range(3):
        j = chat(cliente, f"Sesión de coaching con Camila Torres. Compromisos: confirmar dudas {i}; leer historial")
        assert cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": True}).get_json()["ok"]
    estado = chat(cliente, "estado del coaching de Camila Torres")["respuesta"]
    assert "3 ciclo" in estado and "Criterio de plan de mejora" in estado and "Recomendación" in estado
    j = chat(cliente, "compromiso 2 de Camila Torres parcial")
    assert cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": True}).get_json()["ok"]
    assert "Parcial" in chat(cliente, "estado del coaching de Camila Torres")["respuesta"]


def test_criticos_marcar_revisado(cliente):
    antes = chat(cliente, "Casos críticos")["respuesta"].count("\n1.")
    j = chat(cliente, "Marca el crítico 1 como revisado")
    cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": True})
    assert len(A._criticos_lista(True, 50)) == len(A._criticos_lista(False, 50)) - 1 and antes == 1
    assert chat(cliente, "Marca el crítico 99 como revisado")["propuestas"] == []


def test_muestra_semanal_6_por_asesor_y_descarga(cliente, tmp_path):
    j = chat(cliente, A._csv_demo())
    assert "150 conversaciones de 25 asesores" in j["respuesta"] and j["descargas"]
    r = cliente.get(j["descargas"][0]["url"])
    assert r.status_code == 200
    filas = r.get_data(as_text=True).strip().splitlines()[1:]
    por = {}
    for f in filas:
        por.setdefault(f.split(",")[0], []).append(f.split(",")[2])
    assert all(len(v) == 6 for v in por.values())
    assert all(v.count("CSAT negativo") <= 2 and v.count("Reabierta") <= 2 for v in por.values())


def test_muestra_semanal_prioriza_negativos_y_reabiertas():
    csv_txt = "ID,Asesor,Calificación,Reaperturas\n" + "\n".join(
        [f"{i},Ana,Amazing,0" for i in range(10)] + ["100,Ana,Terrible,0", "101,Ana,Bad,0", "102,Ana,Great,3", "103,Ana,Ok,1"])
    out = A.t_armar_muestra_semanal(csv_txt)["texto"]
    assert "CSAT negativo: 2" in out and "Reabierta: 2" in out and "Aleatoria: 2" in out


def test_muestra_semanal_encabezados_invalidos():
    assert "No encontré las columnas" in A.t_armar_muestra_semanal("foo,bar\n1,2\n3,4")["texto"]


def test_descarga_bloquea_rutas_ajenas(cliente):
    assert cliente.get("/asistente/descargar/..%2Fasistente_qa.py").status_code == 404
    assert cliente.get("/asistente/descargar/asistente_store.json").status_code == 404


def test_endpoints_exigen_json(cliente):
    assert cliente.post("/asistente/chat", data={"mensaje": "x"}).status_code == 400
    assert cliente.post("/asistente/confirmar", data={"id": "x"}).status_code == 400


def test_auditoria_registra_cambios(cliente, tmp_path):
    j = chat(cliente, "Pon la meta en 86")
    cliente.post("/asistente/confirmar", json={"id": j["propuestas"][0]["id"], "aceptar": True})
    lineas = (tmp_path / "asistente_auditoria.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lineas[-1])["herramienta"] == "cambiar_meta_calidad"


def test_modo_ia_con_proveedor_simulado(cliente, monkeypatch):
    """La IA pide una lectura, recibe el resultado y propone una escritura; la escritura NO se ejecuta sin confirmar."""
    respuestas = iter([
        json.dumps({"respuesta": "", "llamadas": [{"herramienta": "bottom_25", "args": {}},
                                                   {"herramienta": "cambiar_meta_calidad", "args": {"valor": 0.9}}]}),
        json.dumps({"respuesta": "Estos son los candidatos; propongo subir la meta.", "llamadas": []}),
    ])
    monkeypatch.setattr(A, "_llm_proveedor", lambda: "openai")
    monkeypatch.setattr(A, "_llamar_llm", lambda prompt, prov: next(respuestas))
    j = chat(cliente, "¿a quién le hago coaching y qué meta pondrías?")
    assert j["modo"] == "openai" and j["propuestas"] and "candidatos" in j["respuesta"]
    assert A._meta() == 0.85


def test_modo_ia_ignora_herramientas_inventadas_y_args_malos(cliente, monkeypatch):
    respuestas = iter([
        json.dumps({"respuesta": "", "llamadas": [{"herramienta": "borrar_todo", "args": {}},
                                                   {"herramienta": "detalle_asesor", "args": "no-es-dict"}]}),
        json.dumps({"respuesta": "No puedo hacer eso.", "llamadas": []}),
    ])
    monkeypatch.setattr(A, "_llm_proveedor", lambda: "gemini")
    monkeypatch.setattr(A, "_llamar_llm", lambda prompt, prov: next(respuestas))
    j = chat(cliente, "borra todo")
    assert j["propuestas"] == [] and "No puedo" in j["respuesta"]


def test_si_la_ia_falla_responde_en_modo_local(cliente, monkeypatch):
    monkeypatch.setattr(A, "_llm_proveedor", lambda: "openai")

    def boom(prompt, prov):
        raise RuntimeError("sin crédito")
    monkeypatch.setattr(A, "_llamar_llm", boom)
    j = chat(cliente, "Resumen del equipo")
    assert "Resumen" in j["respuesta"] and "modo local" in j["respuesta"]


def test_ia_no_recibe_el_csv_pegado(cliente, monkeypatch):
    monkeypatch.setattr(A, "_llm_proveedor", lambda: "openai")
    monkeypatch.setattr(A, "_llamar_llm", lambda p, v: pytest.fail("no debe enviar el archivo semanal a la IA"))
    assert "Muestra semanal lista" in chat(cliente, A._csv_demo())["respuesta"]


def test_sin_datos_no_revienta(monkeypatch, cliente):
    monkeypatch.setattr(A, "_DEMO_REGS", [])
    monkeypatch.setattr(A, "_registros", lambda: [])
    for m in ("Resumen del equipo", "Peores asesores", "¿Quiénes van a coaching?", "Casos críticos", "hola"):
        assert chat(cliente, m)["respuesta"]
