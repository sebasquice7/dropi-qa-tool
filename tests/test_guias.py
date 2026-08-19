"""Pruebas de la coincidencia de guías operativas. Esta lógica es la que
resuelve el problema que reportó Marlon en la reunión del 6 de agosto: NO
penalizar por un procedimiento que no aplica. Si esto se rompe, ese problema
podría volver a aparecer sin que nadie lo note."""
import guias


class TestEncontrarGuiaRelevante:
    def test_sin_bandeja_no_busca_nada(self):
        assert guias.encontrar_guia_relevante("Colombia", "") is None
        assert guias.encontrar_guia_relevante("Colombia", None) is None

    def test_bandeja_sin_guia_devuelve_none_no_error(self):
        """Caso central: una bandeja para la que NO existe ninguna guía
        documentada debe devolver None limpiamente — nunca debe intentar
        forzar una coincidencia débil."""
        resultado = guias.encontrar_guia_relevante("Colombia", "Un tipo de caso inventado que no existe XYZ123")
        assert resultado is None

    def test_bandeja_con_coincidencia_exacta_encuentra_la_guia(self, tmp_path, monkeypatch):
        """Prueba aislada con guías de mentira (no depende de que existan las
        guías reales subidas), para que corra igual en cualquier máquina."""
        carpeta_pais = tmp_path / "colombia"
        carpeta_pais.mkdir()
        (carpeta_pais / "modelo_guia_detallada_anulaciones.md").write_text("# Anulaciones\ncontenido de prueba", encoding="utf-8")

        monkeypatch.setattr(guias, "GUIAS_DIR", tmp_path)

        resultado = guias.encontrar_guia_relevante("Colombia", "Anulaciones")
        assert resultado is not None
        assert "anulaciones" in resultado["titulo"].lower()
        assert "contenido de prueba" in resultado["texto"]

    def test_prioriza_guia_especifica_del_pais_sobre_la_general(self, tmp_path, monkeypatch):
        carpeta_pais = tmp_path / "colombia"
        carpeta_pais.mkdir()
        (carpeta_pais / "anulaciones.md").write_text("# Anulaciones\nversión Colombia", encoding="utf-8")

        carpeta_general = tmp_path / "logistica_general"
        carpeta_general.mkdir()
        (carpeta_general / "anulaciones.md").write_text("# Anulaciones\nversión general", encoding="utf-8")

        monkeypatch.setattr(guias, "GUIAS_DIR", tmp_path)

        resultado = guias.encontrar_guia_relevante("Colombia", "Anulaciones")
        assert "versión Colombia" in resultado["texto"]

    def test_pais_sin_guia_propia_cae_a_la_general(self, tmp_path, monkeypatch):
        carpeta_general = tmp_path / "logistica_general"
        carpeta_general.mkdir()
        (carpeta_general / "anulaciones.md").write_text("# Anulaciones\nversión general", encoding="utf-8")

        monkeypatch.setattr(guias, "GUIAS_DIR", tmp_path)

        resultado = guias.encontrar_guia_relevante("Ecuador", "Anulaciones")
        assert resultado is not None
        assert "versión general" in resultado["texto"]


class TestPalabrasClave:
    def test_ignora_palabras_vacias_comunes(self):
        palabras = guias._palabras_clave("Guía de Anulaciones")
        assert "de" not in palabras
        assert "guia" not in palabras  # "guía"/"guia" está en STOPWORDS_MATCH
        assert "anulaciones" in palabras
