"""Pruebas del historial de evaluaciones: guardar, buscar, detectar
duplicados y calcular tendencias — funciones que usa el buscador, el
dashboard y el detector de duplicados a diario."""
import json

import historial


def _historial_aislado(tmp_path, monkeypatch):
    """Redirige el historial a un archivo temporal, para que las pruebas
    nunca toquen el historial_evaluaciones.json real del usuario."""
    ruta = tmp_path / "historial_prueba.json"
    monkeypatch.setattr(historial, "HISTORIAL_PATH", ruta)
    return ruta


class TestRegistrarYCargar:
    def test_registrar_evaluacion_crea_un_registro_recuperable(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        metadata = {"agente": "Danna", "bandeja": "Garantías", "id_caso": "111", "pais": "Colombia"}
        evaluacion = {"items": {}, "items_criticos": {}}
        nota = {"nota_final": 0.9, "nota_bruta": 0.9, "critico_activado": None}

        historial.registrar_evaluacion(metadata, evaluacion, nota)
        registros = historial.cargar_historial()

        assert len(registros) == 1
        assert registros[0]["agente"] == "Danna"
        assert registros[0]["nota_final"] == 0.9

    def test_varios_registros_se_acumulan_sin_perder_los_anteriores(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        for i in range(3):
            historial.registrar_evaluacion(
                {"agente": f"Asesor{i}", "bandeja": "x", "id_caso": str(i), "pais": "Colombia"},
                {"items": {}, "items_criticos": {}},
                {"nota_final": 0.8, "nota_bruta": 0.8, "critico_activado": None},
            )
        assert len(historial.cargar_historial()) == 3

    def test_historial_inexistente_devuelve_lista_vacia_no_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(historial, "HISTORIAL_PATH", tmp_path / "no_existe.json")
        assert historial.cargar_historial() == []

    def test_archivo_corrupto_devuelve_lista_vacia_no_revienta(self, tmp_path, monkeypatch):
        ruta = _historial_aislado(tmp_path, monkeypatch)
        ruta.write_text("esto no es json valido {{{", encoding="utf-8")
        assert historial.cargar_historial() == []


class TestBuscarDuplicado:
    def test_encuentra_el_mismo_id_caso(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        historial.registrar_evaluacion(
            {"agente": "Danna", "bandeja": "x", "id_caso": "CASO-123", "pais": "Colombia"},
            {"items": {}, "items_criticos": {}},
            {"nota_final": 0.9, "nota_bruta": 0.9, "critico_activado": None},
        )
        duplicado = historial.buscar_duplicado("CASO-123")
        assert duplicado is not None
        assert duplicado["agente"] == "Danna"

    def test_id_caso_sin_evaluar_devuelve_none(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        assert historial.buscar_duplicado("NO-EXISTE") is None

    def test_id_caso_vacio_devuelve_none(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        assert historial.buscar_duplicado("") is None
        assert historial.buscar_duplicado(None) is None


class TestBuscarEvaluaciones:
    def _poblar(self, tmp_path, monkeypatch):
        ruta = _historial_aislado(tmp_path, monkeypatch)
        registros = [
            {"timestamp": "2026-08-01T10:00:00", "fecha": "2026-08-01", "agente": "Danna Trujillo", "bandeja": "x", "id_caso": "1", "pais": "Colombia", "nota_final": 0.9, "oportunidades_mejora": ["Falta personalización"], "lo_positivo": []},
            {"timestamp": "2026-08-02T10:00:00", "fecha": "2026-08-02", "agente": "Dennis", "bandeja": "x", "id_caso": "2", "pais": "Ecuador", "nota_final": 0.6, "oportunidades_mejora": ["Ortografía deficiente"], "lo_positivo": []},
        ]
        ruta.write_text(json.dumps(registros), encoding="utf-8")

    def test_filtra_por_asesor_parcial_sin_distinguir_mayusculas(self, tmp_path, monkeypatch):
        self._poblar(tmp_path, monkeypatch)
        resultado = historial.buscar_evaluaciones(asesor="danna")
        assert len(resultado) == 1
        assert resultado[0]["agente"] == "Danna Trujillo"

    def test_filtra_por_texto_en_oportunidades_de_mejora(self, tmp_path, monkeypatch):
        self._poblar(tmp_path, monkeypatch)
        resultado = historial.buscar_evaluaciones(texto="personalización")
        assert len(resultado) == 1
        assert resultado[0]["agente"] == "Danna Trujillo"

    def test_filtra_por_rango_de_fechas(self, tmp_path, monkeypatch):
        self._poblar(tmp_path, monkeypatch)
        resultado = historial.buscar_evaluaciones(fecha_desde="2026-08-02")
        assert len(resultado) == 1
        assert resultado[0]["agente"] == "Dennis"

    def test_sin_filtros_devuelve_todo(self, tmp_path, monkeypatch):
        self._poblar(tmp_path, monkeypatch)
        assert len(historial.buscar_evaluaciones()) == 2

    def test_filtro_que_no_coincide_con_nada_devuelve_lista_vacia(self, tmp_path, monkeypatch):
        self._poblar(tmp_path, monkeypatch)
        assert historial.buscar_evaluaciones(asesor="Nombre Que No Existe") == []


class TestTendenciaPorAsesor:
    def test_agrupa_por_fecha_y_asesor(self, tmp_path, monkeypatch):
        _historial_aislado(tmp_path, monkeypatch)
        registros = [
            {"fecha": "2026-08-01", "agente": "Danna", "nota_final": 0.8},
            {"fecha": "2026-08-01", "agente": "Danna", "nota_final": 1.0},  # promedio del día: 0.9
            {"fecha": "2026-08-02", "agente": "Danna", "nota_final": 0.5},
        ]
        tendencia = historial.tendencia_por_asesor(registros)
        assert tendencia["2026-08-01"]["Danna"] == 0.9
        assert tendencia["2026-08-02"]["Danna"] == 0.5
