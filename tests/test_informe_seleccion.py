from informe_desempeno import construir_informe, normalizar_nombre, estado_muestra


def _r(asesor, pais, nota, fecha):
    return {
        "agente": asesor, "pais": pais, "bandeja": "Prueba",
        "nota_final": nota, "fecha": fecha, "timestamp": fecha + "T10:00:00",
        "critico_activado": None, "items_detalle": {}, "categorias": {},
    }


def test_grupo_seleccionado_no_excluye_por_minimo():
    registros = [
        _r("Laura", "Colombia", 0.40, "2026-08-01"),
        _r("Danna", "Colombia", 0.70, "2026-08-01"),
        _r("Danna", "Colombia", 0.60, "2026-08-02"),
    ]
    informe = construir_informe(
        registros, minimo_auditorias=10,
        asesores_seleccionados=["Laura", "Danna"], top_n=10
    )
    assert [x["asesor"] for x in informe["ranking"]] == ["Laura", "Danna"]
    assert informe["ranking"][0]["estado_muestra"]["codigo"] == "muy_baja"


def test_seleccion_reporta_asesor_sin_datos():
    registros = [_r("Laura", "Colombia", 0.80, "2026-08-01")]
    informe = construir_informe(
        registros, asesores_seleccionados=["Laura", "Persona externa"], top_n=10
    )
    assert informe["total_solicitados"] == 2
    assert informe["total_encontrados"] == 1
    assert informe["sin_datos"][0]["asesor"] == "Persona externa"


def test_cruce_nombres_tolera_tildes_case_y_espacios():
    registros = [_r("Andrés Pino", "Colombia", 0.75, "2026-08-01")]
    informe = construir_informe(
        registros, asesores_seleccionados=["  ANDRES   PINO  "], top_n=10
    )
    assert informe["total_encontrados"] == 1
    assert informe["ranking"][0]["asesor"] == "Andrés Pino"
    assert normalizar_nombre("ÁÉÍÓÚ") == "aeiou"


def test_top_n_limita_solo_vista_no_poblacion():
    registros = [
        _r("A", "Colombia", 0.40, "2026-08-01"),
        _r("B", "Colombia", 0.50, "2026-08-01"),
        _r("C", "Colombia", 0.60, "2026-08-01"),
    ]
    informe = construir_informe(
        registros, asesores_seleccionados=["A", "B", "C"], top_n=2
    )
    assert len(informe["ranking"]) == 2
    assert len(informe["ranking_completo"]) == 3
    assert [x["asesor"] for x in informe["ranking"]] == ["A", "B"]


def test_estado_muestra_no_finge_suficiencia():
    assert estado_muestra(0)["codigo"] == "sin_datos"
    assert estado_muestra(1)["codigo"] == "muy_baja"
    assert estado_muestra(10)["codigo"] == "moderada"
    assert estado_muestra(20)["codigo"] == "solida"
