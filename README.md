# Evaluación de Calidad con IA — Soporte Intercom Dropi

Aplicación web local que automatiza la evaluación de calidad de conversaciones de
soporte: lee el PDF exportado de Intercom, lo evalúa con IA contra la matriz de
calidad CX V2, la política de comunicación, la política de SLA y las guías
operativas reales de cada país, y genera el Excel y el Word finales en el mismo
formato que ya usa el equipo.

No es solo un evaluador — es un panel completo de calidad: dashboard en vivo,
coaching automático por asesor, calibración IA vs. humano, y un simulador de
presupuesto basado en tu uso real.

## Qué hace

- **Evalúa una conversación** (o varias en lote) contra la Matriz de Calidad CX
  V2 (5 categorías, 15 ítems, 6 ítems críticos), con criterio de **analista de
  calidad profesional** — no un checklist superficial. La IA diagnostica causa
  raíz, detecta patrones de comportamiento, y produce hallazgos orientados a
  coaching.
- **Detecta automáticamente** bandeja, ID de caso, país y asesor desde el PDF.
- **Cache de evaluaciones**: si se vuelve a subir una conversación ya evaluada, el
  programa ofrece reutilizar la evaluación anterior (consistencia 100%, sin costo
  de IA) o evaluar de nuevo si se prefiere un análisis fresco.
- **Soporta 3 proveedores de IA** (Gemini gratis por defecto; Claude y ChatGPT
  opcionales) con cadena de modelos de respaldo por si uno falla o se retira.
  Temperatura en 0 en los 3 proveedores para máxima consistencia.
- **Compara entre proveedores** la misma conversación, lado a lado, y deja elegir
  cuál usar como evaluación oficial.
- **Dashboard en vivo**: KPIs, tendencias por asesor, mapa de calor del equipo,
  comparativa por país, temas recurrentes en las oportunidades de mejora.
- **Plan de coaching por asesor**, sintetizado por IA a partir de todo su
  historial (no de una sola conversación), descargable como Word.
- **Calibración IA vs. humano**: mide qué tan seguido corriges a la IA al revisar,
  y en qué categorías tiende a equivocarse.
- **Simulador de presupuesto**: estima el costo mensual con cada modelo de IA,
  basado en el uso real registrado (no en una estimación fija).
- **Alertas por correo** cuando se detecta un ítem crítico, y **respaldo
  automático** en Google Drive.
- **Buscador del historial** por asesor, ID, fecha o texto.

## Matriz de Calidad CX V2

La evaluación se basa en 5 categorías con un total de 15 ítems ponderados que
suman 100%, más 6 ítems críticos que anulan la nota completa si alguno se activa:

| Categoría | Peso |
|---|---|
| Sincronización e Interacción con Gali (IA) | 15% |
| Conexión Empática y Escucha Activa | 20% |
| Resolución de Valor y Esfuerzo del Cliente (CES) | 35% |
| Protocolo de Cierre y Verificación de Satisfacción | 15% |
| Comunicación Escrita, SLA y Trazabilidad Operativa | 15% |

La matriz es configurable desde la interfaz web (`/matriz`) sin tocar código. El
detalle completo de cada ítem y criterio de evaluación está en
`config/matriz_calidad.json`.

## 1. Instalación

Necesitas Python 3.10 o superior.

```bash
cd dropi_qa_tool
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuración (`.env`)

Copia este bloque a un archivo `.env` en la raíz del proyecto y ajusta lo que
necesites. **Solo `GEMINI_API_KEY` es obligatorio** — todo lo demás es opcional.

```bash
# --- Obligatorio: al menos un proveedor de IA. Gemini es gratis. ---
GEMINI_API_KEY=tu-key-aqui          # gratis en https://aistudio.google.com/apikey

# --- Acceso a la app web (recomendado si no es solo para ti) ---
APP_USERNAME=admin
APP_PASSWORD=una-contraseña-segura

# --- Opcional: otros proveedores de IA, para comparar o como respaldo ---
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# --- Opcional: respaldo automático en Google Drive (Drive Desktop instalado) ---
# DRIVE_SYNC_FOLDER=/ruta/a/tu/carpeta/compartida/de/Drive

# --- Opcional: alertas por correo cuando se detecta un ítem crítico ---
# ALERTA_SMTP_HOST=smtp.gmail.com
# ALERTA_SMTP_PORT=587
# ALERTA_SMTP_USER=tu_correo@gmail.com
# ALERTA_SMTP_PASS=tu-contraseña-de-aplicación
# ALERTA_EMAIL_TO=quien-debe-recibir-la-alerta@dropi.co

# --- Opcional: meta de calidad por defecto del dashboard (0.85 = 85%) ---
# META_CALIDAD=0.85
```

Al arrancar, el programa imprime un reporte claro de qué quedó configurado y qué
falta — no hace falta adivinar.

## 3. Correr la aplicación

```bash
python app.py
```

Abre `http://127.0.0.1:5050` en tu navegador.

## 4. Correr las pruebas automatizadas

```bash
pip install -r requirements-dev.txt
python -m pytest tests/
```

## Estructura del proyecto

```
dropi_qa_tool/
├── app.py                  # Arma la app Flask y registra los blueprints (~85 líneas)
├── requirements.txt        # Dependencias de producción (versiones fijadas)
├── requirements-dev.txt    # + pytest, solo para desarrollo
├── config/
│   ├── matriz_calidad.json       # Matriz CX V2: 15 ítems, 6 críticos — editable desde /matriz
│   ├── matriz_calidad_v1_backup.json  # Respaldo de la Matriz V1 (para referencia)
│   ├── mapeo_matriz_v1_a_v2.json      # Tabla de equivalencias V1→V2 (usada por migrar_historial_v2.py)
│   ├── politica_comunicacion.md
│   ├── politica_sla.md
│   ├── faqs_gali/                # Base de conocimiento de Gali por país (233 entradas Colombia)
│   └── guias/                    # Guías operativas reales, por país y logística general
├── src/
│   ├── services/            # Lógica de negocio pura, SIN depender de Flask —
│   │   │                    # llamable directo desde otro sistema (ej. Monitor)
│   │   ├── evaluacion_service.py
│   │   ├── lote_service.py
│   │   ├── comparacion_service.py
│   │   └── coaching_service.py
│   ├── blueprints/          # Rutas web — capa delgada que llama a services/
│   │   ├── evaluacion_bp.py
│   │   ├── dashboard_bp.py
│   │   ├── coaching_bp.py
│   │   ├── calibracion_bp.py
│   │   ├── buscar_bp.py
│   │   ├── matriz_bp.py
│   │   ├── informes_bp.py
│   │   └── presupuesto_bp.py
│   ├── config.py            # Configuración centralizada (todas las variables de entorno)
│   ├── logging_config.py    # Logging a consola + archivo rotativo (logs/app.log)
│   ├── evaluator.py         # Llamadas a la IA (Gemini/Claude/OpenAI) + construcción del prompt
│   ├── scoring.py           # Cálculo de la nota final
│   ├── guias.py             # Encuentra la guía operativa relevante para un caso
│   ├── calibracion.py       # IA vs. humano
│   ├── presupuesto.py       # Estimación de costos
│   ├── historial.py         # Persistencia, búsqueda y cache de evaluaciones completas
│   ├── pdf_parser.py        # Lee y estructura el PDF de Intercom
│   ├── faqs_gali_buscador.py # Busca FAQs relevantes de Gali para inyectar en el prompt
│   ├── excel_writer.py / word_writer.py / coaching_word.py / kpi_report.py
│   └── dashboard_data.py    # Agregaciones para el dashboard en vivo
├── templates/                # HTML (Jinja2), con un layout compartido (_base.html)
├── tests/                    # 46 pruebas automatizadas de la lógica crítica
├── pruebas_validacion_ia/    # Casos de prueba de integración con la IA (requiere API key)
├── migrar_historial_v2.py    # Script de migración V1→V2 del historial de evaluaciones
└── diagnostico_matriz.py     # Validación de que los pesos de la matriz suman 100%
```

## Notas para integrar esto a otro sistema (ej. "Monitor")

Toda la lógica real vive en `src/services/` y no depende de Flask — se puede
importar y llamar directo desde otro programa Python, sin pasar por HTTP. Por
ejemplo, para evaluar una conversación:

```python
from services.evaluacion_service import iniciar_evaluacion

resultado = iniciar_evaluacion(
    ruta_pdf="conversacion.pdf", asesor="Nombre Asesor", token="algun-id-unico",
    bandeja="Anulaciones", pais="Colombia", id_caso="123456", auditor="Auditor",
)
# resultado: {"token", "metadata", "evaluacion", "nota"}
```

Los blueprints (`src/blueprints/`) son solo la capa HTTP — muestran cómo se usa
cada servicio, pero no son necesarios si se integra directamente.

## Guías operativas

El programa detecta automáticamente si existe una guía documentada que aplique al
caso (por país + bandeja) y se la da a la IA como contexto de referencia para
evaluar la precisión técnica del asesor. Si no existe ninguna guía para ese tipo
de caso, simplemente no se agrega contexto adicional — nunca penaliza por no
seguir un proceso que no estaba documentado. Las guías viven en
`config/guias/<país>/` y `config/guias/logistica_general/` (estas últimas aplican
a todos los países).

## Pruebas automatizadas

El proyecto incluye 46 pruebas unitarias que cubren:
- **Scoring** (11 tests): cálculo de nota final, normalización, ítems críticos.
- **Calibración** (9 tests): acuerdo IA vs. humano, detección de ajustes.
- **Guías** (6 tests): búsqueda de guía correcta por país y bandeja.
- **Historial** (11 tests): persistencia, duplicados, búsqueda, tendencias.
- **Presupuesto** (9 tests): estimación de costos basada en uso real.

```bash
python -m pytest tests/ -q          # rápido
python -m pytest tests/ -v          # detallado, con nombre de cada test
python diagnostico_matriz.py        # verifica que la matriz sume 100%
```
