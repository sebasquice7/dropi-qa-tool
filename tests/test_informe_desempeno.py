from informe_desempeno import construir_informe


def _r(asesor, pais, nota, fecha, critico=None):
    return {
        "agente": asesor,
        "pais": pais,
        "bandeja": "Prueba",
        "nota_final": nota,
        "fecha": fecha,
        "timestamp": fecha + "T10:00:00",
        "critico_activado": critico,
        "items_detalle": {},
        "categorias": {},
    }


def test_peor_global_respeta_minimo_muestra():
    registros = [
        _r("A", "Colombia", 0.40, "2026-08-01"),
        _r("B", "México", 0.70, "2026-08-01"),
        _r("B", "México", 0.60, "2026-08-02"),
        _r("C", "Colombia", 0.80, "2026-08-01"),
        _r("C", "Colombia", 0.80, "2026-08-02"),
    ]
    informe = construir_informe(registros, minimo_auditorias=2)
    assert informe["peor_global"]["asesor"] == "B"
    assert any(x["asesor"] == "A" for x in informe["muestra_insuficiente"])


def test_region_mas_baja_usa_promedio_por_evaluacion():
    registros = [
        _r("A", "Colombia", 0.90, "2026-08-01"),
        _r("A", "Colombia", 0.90, "2026-08-02"),
        _r("B", "México", 0.60, "2026-08-01"),
        _r("B", "México", 0.70, "2026-08-02"),
    ]
    informe = construir_informe(registros, minimo_auditorias=1)
    assert informe["peor_region"]["region"] == "México"


def test_critico_y_tendencia_se_conservan():
    registros = [
        _r("A", "Colombia", 0.90, "2026-08-01", "crítico"),
        _r("A", "Colombia", 0.85, "2026-08-02"),
        _r("A", "Colombia", 0.70, "2026-08-03"),
        _r("A", "Colombia", 0.60, "2026-08-04"),
    ]
    informe = construir_informe(registros, minimo_auditorias=1)
    a = informe["ranking"][0]
    assert a["criticos"] == 1
    assert a["tendencia"] == "Deterioro"
