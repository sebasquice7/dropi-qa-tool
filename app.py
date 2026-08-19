#!/usr/bin/env python3
"""
Interfaz web local para el programa de evaluación de calidad Dropi/Intercom.

Este archivo es deliberadamente pequeño: crea la aplicación Flask, protege
todas las rutas con usuario/contraseña, y registra cada grupo de páginas
(blueprints/) que vive en src/blueprints/. Toda la lógica real del programa
vive en src/services/ y en los módulos de src/ — este archivo no contiene
lógica de negocio, solo arma la aplicación web.

Para iniciarla:
    python app.py

Luego abre en tu navegador: http://127.0.0.1:5050
"""
import sys
from pathlib import Path

from flask import Flask, request, Response
from flask.typing import ResponseReturnValue
from werkzeug.datastructures import Authorization

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from config import config, reporte_configuracion
from logging_config import obtener_logger

from blueprints.evaluacion_bp import evaluacion_bp
from blueprints.dashboard_bp import dashboard_bp
from blueprints.coaching_bp import coaching_bp
from blueprints.calibracion_bp import calibracion_bp
from blueprints.buscar_bp import buscar_bp
from blueprints.matriz_bp import matriz_bp
from blueprints.informes_bp import informes_bp
from blueprints.presupuesto_bp import presupuesto_bp

log = obtener_logger("app")

UPLOADS_DIR = BASE_DIR / "uploads"
SALIDAS_DIR = BASE_DIR / "salidas"
UPLOADS_DIR.mkdir(exist_ok=True)
SALIDAS_DIR.mkdir(exist_ok=True)


def crear_app() -> Flask:
    """Arma la aplicación Flask completa: registra los 8 blueprints y protege todas las rutas con autenticación básica."""
    app = Flask(__name__)
    app.secret_key = config.secret_key  # aleatoria si no se definió SECRET_KEY en el .env

    for bp in (evaluacion_bp, dashboard_bp, coaching_bp, calibracion_bp,
               buscar_bp, matriz_bp, informes_bp, presupuesto_bp):
        app.register_blueprint(bp)

    @app.before_request
    def proteger_todas_las_rutas() -> ResponseReturnValue | None:
        """Se ejecuta antes de cada petición — bloquea con 401 si la autenticación no es válida."""
        if not _autenticado(request.authorization):
            return Response(
                "Acceso restringido. Ingresa el usuario y la contraseña configurados en el archivo .env.",
                401,
                {"WWW-Authenticate": 'Basic realm="Dropi QA Tool"'},
            )

    return app


def _autenticado(auth: Authorization | None) -> bool:
    if not config.app_password:
        # Si no se configuró contraseña, no se exige (uso solo local en la propia máquina)
        return True
    return bool(auth) and auth.username == config.app_username and auth.password == config.app_password


app = crear_app()


if __name__ == "__main__":
    print("\n🚀 Abre en tu navegador: http://127.0.0.1:5050\n")
    print(reporte_configuracion())
    print()
    if not config.app_password:
        print("⚠️  SIN CONTRASEÑA configurada (APP_PASSWORD vacío en .env). "
              "No expongas esta app a internet así.\n")
    log.info("Servidor iniciado en http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False)
