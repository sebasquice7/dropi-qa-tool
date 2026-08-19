"""Configuración compartida para todas las pruebas.

Agrega `src/` al path de Python, replicando exactamente cómo `app.py` importa
sus módulos (`from evaluator import ...`, no `from src.evaluator import ...`),
para que las pruebas usen el código real tal como corre en producción.
"""
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))
sys.path.insert(0, str(RAIZ_PROYECTO))
