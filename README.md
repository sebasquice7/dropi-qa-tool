# Dropi QA — Evaluación de Calidad con IA para Soporte

Aplicación web local para automatizar y fortalecer el proceso de **Quality Assurance (QA)** de conversaciones de soporte de Dropi.

El sistema recibe conversaciones exportadas desde Intercom en PDF, identifica el contexto del caso, consulta la matriz de calidad, las políticas internas y las guías operativas aplicables, ejecuta una evaluación con IA y permite que el auditor humano revise, corrija y confirme el resultado antes de convertirlo en una evaluación oficial.

Dropi QA ya no funciona únicamente como un evaluador de conversaciones. Actualmente integra **evaluación, trazabilidad, coaching, análisis operativo, cobertura de auditorías, detección de reincidencias, calibración IA vs. humano, aprendizaje a partir de correcciones, análisis de riesgo y muestreo inteligente**.

---

## Objetivo del aplicativo

El objetivo es ayudar al equipo de calidad a responder cuatro preguntas:

1. **¿Cómo fue atendida esta conversación?**
2. **¿En qué está fallando o destacándose cada asesor?**
3. **¿Qué problemas se repiten en la operación y dónde se están perdiendo puntos de calidad?**
4. **¿En qué criterios podemos confiar más en la IA y cuáles requieren mayor supervisión humana?**

La IA **no tiene la última palabra**. El principio del sistema es:

> **IA propone → auditor revisa → auditor corrige → evaluación final se registra → el sistema aprende del patrón.**

---

# Funcionalidades principales

## 1. Evaluación individual de conversaciones

- Carga de PDF exportado desde Intercom.
- Detección automática de:
  - asesor;
  - bandeja;
  - país;
  - ID del caso;
  - contenido completo de la conversación.
- Lectura del contexto y evidencias incluidas en el PDF.
- Evaluación contra una matriz de calidad configurable.
- Aplicación de política de comunicación y política de SLA.
- Consulta de la guía operativa correspondiente al proceso y país.
- Consulta del contexto disponible de Gali cuando aplica.
- Cálculo de nota ponderada por categoría y subítem.
- Identificación de ítems críticos.
- Revisión humana antes de confirmar la auditoría.
- Generación de Excel y Word con el resultado final.

### Regla de evidencia documental

Si no existe una guía operativa documentada para un caso, el sistema **no penaliza al asesor por no seguir una guía inexistente**. El criterio se resuelve de forma conservadora para evitar que la IA invente procedimientos.

---

## 2. Evaluación por lote

Permite procesar múltiples conversaciones.

Además del procesamiento tradicional, la Fase 3 incorpora **muestreo inteligente** para priorizar casos antes de consumir llamadas de IA.

Composición predeterminada de la muestra:

- **60% aleatoria** — mantiene representatividad.
- **20% riesgo** — prioriza conversaciones con señales de riesgo.
- **10% reincidencias** — prioriza asesores con patrones repetidos.
- **10% complejidad** — prioriza conversaciones complejas.

Antes de evaluar con Gemini, el usuario puede revisar la selección y marcar o desmarcar casos.

---

## 3. Comparación entre proveedores de IA

El programa puede trabajar con:

- **Gemini** — proveedor principal por defecto.
- **Claude / Anthropic** — opcional.
- **OpenAI / ChatGPT** — opcional.

Puede comparar una misma conversación entre proveedores y permitir seleccionar qué resultado utilizar como evaluación base.

Gemini utiliza una cadena de modelos de respaldo para reducir fallas cuando un modelo está temporalmente saturado, deja de estar disponible o cambia de nombre.

---

# Historial de evaluaciones

El historial permite buscar evaluaciones por:

- asesor;
- ID de caso;
- texto;
- rango de fechas.

Cada evaluación conserva información suficiente para revisar posteriormente el caso, descargar sus reportes y analizar la calibración IA vs. auditor.

## Desempeño detallado por categoría

Las categorías se muestran como elementos desplegables.

Ejemplo:

```text
RESOLUCIÓN DE VALOR Y ESFUERZO DEL CLIENTE
25.0 / 35.0 pts
```

Al desplegar una categoría se muestran sus subítems:

```text
Subítem                              Peso máx.    Puntaje obtenido
Efectividad y precisión técnica       10.0          6.0
Gestión proactiva de fallas           10.0         10.0
Minimización del esfuerzo             10.0          6.0
Resolución en primer contacto          5.0          3.0

TOTAL CATEGORÍA                       35.0         25.0
```

Los nombres y pesos se leen desde `config/matriz_calidad.json`; no están escritos manualmente en la plantilla.

---

# Coaching por asesor

El módulo de Coaching analiza **varias auditorías del mismo asesor**, no una sola conversación.

Incluye:

- promedio general;
- desempeño por categoría;
- detalle por subítem;
- puntos promedio obtenidos vs. peso máximo;
- porcentaje de cumplimiento;
- fortalezas;
- oportunidades de mejora;
- plan de coaching generado con IA;
- descarga del plan en Word.

## Desempeño ponderado

Ejemplo:

```text
RESOLUCIÓN DE VALOR Y ESFUERZO DEL CLIENTE
25.0 / 35.0 pts · 71% de cumplimiento
```

Esto permite distinguir entre:

- **impacto real sobre la nota:** 25 de 35 puntos;
- **nivel de cumplimiento de la categoría:** 71%.

Los ítems que no aplican no deben ser interpretados como cero, evitando penalizaciones artificiales.

---

# Fase 2 — Gestión operativa de calidad

La Fase 2 transforma la herramienta de un evaluador individual a un sistema de seguimiento de calidad.

## 1. Reincidencias por asesor

Detecta subítems donde un asesor presenta fallas repetidas.

Un error aislado no se considera automáticamente reincidencia. El módulo permite identificar:

- número de fallas;
- número de evaluaciones analizadas;
- tasa de reincidencia;
- última fecha detectada;
- criterio afectado.

Esto permite separar un error ocasional de un patrón de desempeño.

## 2. Evolución semanal y mensual

Coaching incorpora tendencias de desempeño por asesor:

```text
Semana 1   82%
Semana 2   84%
Semana 3   79%
Semana 4   86%
```

También compara el período actual con el inmediatamente anterior para identificar mejoría, estabilidad o deterioro.

## 3. Ranking de pérdida de puntos

El Dashboard identifica los criterios que más puntos están quitando a la operación.

Ejemplo:

```text
Efectividad y precisión técnica
12 casos afectados
-38.5 puntos acumulados
```

Esto ayuda a responder no solo *qué criterio tiene menor porcentaje*, sino **dónde se está concentrando realmente el impacto sobre la calidad**.

## 4. Cobertura de auditorías

Permite controlar la ejecución de la meta mensual por asesor.

Ejemplo:

```text
Danna Trujillo
31 / 50 auditorías
Pendientes: 19
Cobertura: 62%
```

La meta puede configurarse y no queda fija dentro del código.

Archivo local de configuración:

```text
config/metas_auditoria.json
```

## 5. Bandeja de casos críticos

El Dashboard incluye una bandeja para centralizar casos con ítems críticos.

Puede mostrar:

- fecha;
- asesor;
- ID del caso;
- bandeja;
- motivo del crítico;
- estado de revisión.

Los casos pueden marcarse como revisados sin modificar la auditoría original.

Archivo local de estado:

```text
config/criticos_estado.json
```

---

# Fase 3 — IA supervisada, riesgo y muestreo inteligente

La Fase 3 utiliza las correcciones del auditor como datos para medir y mejorar progresivamente el comportamiento de la IA.

## 1. Calibración avanzada IA vs. humano

La calibración ya no se limita a comparar la nota total.

El sistema puede analizar diferencias por:

- subítem;
- categoría;
- bandeja;
- asesor.

Para cada criterio puede calcular:

- muestra analizada;
- número de correcciones;
- acuerdo IA-humano;
- sesgo promedio;
- error medio.

Ejemplo conceptual:

```text
Precisión técnica
Muestra: 22
Acuerdo: 68%
Error medio: 1.8 pts
```

Esto permite detectar criterios donde la IA tiende a ser demasiado estricta o demasiado permisiva.

---

## 2. Aprendizaje a partir de correcciones humanas

Cuando el auditor cambia un puntaje propuesto por la IA, el sistema puede registrar el evento como aprendizaje.

Ejemplo:

```text
IA:      Cumple
Auditor: No cumple
Motivo:  No tuvo en cuenta la evidencia ya adjuntada por el usuario.
```

Los eventos se almacenan localmente en:

```text
aprendizaje_ia.jsonl
```

Se guardan únicamente diferencias reales entre IA y auditor.

### Aprendizaje conservador

Una sola corrección **no se convierte automáticamente en una nueva regla**.

El flujo es:

```text
Auditor corrige
      ↓
Se almacena el caso
      ↓
El sistema identifica patrones repetidos
      ↓
Solo los patrones repetidos pueden enriquecer el contexto futuro
      ↓
La evidencia del caso actual siempre tiene prioridad
```

Esto reduce el riesgo de sobreajustar el evaluador a una corrección humana aislada.

---

## 3. Biblioteca de errores frecuentes de la IA

La calibración puede agrupar correcciones recurrentes y mostrar:

- criterio;
- cantidad de correcciones;
- error medio;
- dirección principal del error;
- ejemplos de casos;
- motivo registrado por el auditor.

El objetivo es identificar patrones como:

- IA demasiado permisiva;
- IA demasiado estricta;
- interpretación incorrecta de evidencias;
- problemas frecuentes en determinados criterios.

---

## 4. Nivel de confianza de la IA

El sistema calcula confianza histórica por criterio usando:

- acuerdo IA-humano;
- magnitud del error;
- tamaño de la muestra.

Los niveles son:

- **Alta**
- **Media**
- **Baja**

Una muestra pequeña es penalizada para evitar mostrar una falsa confianza alta.

Ejemplo:

```text
Ortografía
Muestra: 24
Acuerdo: 96%
Confianza: 91%
ALTA

Precisión técnica
Muestra: 7
Acuerdo: 57%
Confianza: 52%
BAJA
⚠ Revisión humana recomendada
```

---

## 5. Motor de riesgo de conversación

Antes de ejecutar la evaluación completa con IA, el sistema puede calcular un riesgo preliminar de la conversación.

Clasificación:

- **BAJO**
- **MEDIO**
- **ALTO**

Entre las señales consideradas están:

- conversación extensa;
- frustración o reclamo;
- impacto económico;
- escalamiento;
- manejo de evidencias;
- reapertura o reiteración;
- continuidad durante varios días;
- contexto incompleto, como bandeja no identificada.

Ejemplo:

```text
Riesgo preliminar: MEDIO · 42/100
```

El riesgo **no modifica directamente la nota QA**. Sirve para priorización y supervisión.

---

## 6. Muestreo inteligente

Cuando se cargan múltiples conversaciones, el sistema puede priorizar una muestra antes de llamar a la IA.

El objetivo es equilibrar:

- representatividad;
- riesgo;
- reincidencia;
- complejidad.

La selección puede revisarse manualmente antes de iniciar el consumo de IA.

---

# Dashboard en vivo

El Dashboard consolida información operativa y de calidad.

Incluye, entre otros:

- calidad general;
- evaluaciones realizadas;
- comportamiento por asesor;
- comportamiento por categoría;
- filtros por período, país, bandeja y área;
- ranking de pérdida de puntos;
- cobertura de auditorías;
- casos críticos;
- tendencias y patrones de calidad.

El Dashboard actualiza sus datos periódicamente mientras permanece abierto.

---

# Matriz de calidad

La matriz se encuentra en:

```text
config/matriz_calidad.json
```

Define:

- categorías;
- subítems;
- pesos;
- criterios críticos.

Los módulos de Historial, Coaching, Dashboard, Fase 2 y Fase 3 reutilizan esta configuración para evitar duplicar manualmente nombres o pesos.

---

# Guías operativas

El programa detecta automáticamente si existe una guía documentada para el país y proceso correspondiente.

Las guías viven principalmente en:

```text
config/guias/<pais>/
config/guias/logistica_general/
```

Las guías de logística general pueden aplicar transversalmente a varios países.

---

# Proveedores de IA

## Gemini

Proveedor principal y recomendado durante la etapa actual del proyecto.

El sistema contempla modelos alternativos de Gemini cuando el modelo preferido no está disponible temporalmente.

## Claude y OpenAI

Son proveedores opcionales. Para utilizarlos se debe configurar la API key correspondiente.

---

# Instalación

Se recomienda Python 3.10 o superior.

```bash
cd dropi_qa_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows:

```text
.venv\Scripts\activate
```

---

# Configuración `.env`

Las credenciales y secretos deben permanecer fuera del código fuente.

Ejemplo:

```bash
# Proveedor principal
GEMINI_API_KEY=tu-key-aqui

# Acceso a la aplicación
APP_USERNAME=admin
APP_PASSWORD=una-contraseña-segura

# Proveedores opcionales
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Respaldo en Google Drive Desktop
# DRIVE_SYNC_FOLDER=/ruta/a/carpeta/Drive

# Alertas por correo para ítems críticos
# ALERTA_SMTP_HOST=smtp.gmail.com
# ALERTA_SMTP_PORT=587
# ALERTA_SMTP_USER=tu_correo@gmail.com
# ALERTA_SMTP_PASS=tu-password-de-aplicacion
# ALERTA_EMAIL_TO=destinatario@dropi.co

# Meta de calidad del Dashboard
# META_CALIDAD=0.85
```

El archivo `.env` **no debe subirse a GitHub**.

---

# Ejecutar la aplicación

Con el entorno virtual activo:

```bash
python3 app.py
```

Abrir:

```text
http://127.0.0.1:5050
```

---

# Pruebas automatizadas

Instala las dependencias de desarrollo si todavía no están instaladas:

```bash
pip install -r requirements-dev.txt
```

Ejecuta:

```bash
pytest -q
```

Estado actual de referencia después de Fase 3:

```text
53 passed
```

Las pruebas cubren lógica crítica del aplicativo y nuevas reglas introducidas en Fase 2 y Fase 3.

---

# Estructura principal del proyecto

```text
dropi_qa_tool/
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── .env                         # local, NO subir a Git
├── aprendizaje_ia.jsonl         # generado localmente cuando existen correcciones
│
├── config/
│   ├── matriz_calidad.json
│   ├── politica_comunicacion.md
│   ├── politica_sla.md
│   ├── metas_auditoria.json      # configuración operativa local
│   ├── criticos_estado.json      # estado de revisión de casos críticos
│   └── guias/
│
├── src/
│   ├── services/
│   │   ├── evaluacion_service.py
│   │   ├── lote_service.py
│   │   ├── comparacion_service.py
│   │   └── coaching_service.py
│   │
│   ├── blueprints/
│   │   ├── evaluacion_bp.py
│   │   ├── dashboard_bp.py
│   │   ├── coaching_bp.py
│   │   ├── calibracion_bp.py
│   │   ├── buscar_bp.py
│   │   ├── matriz_bp.py
│   │   ├── informes_bp.py
│   │   └── presupuesto_bp.py
│   │
│   ├── evaluator.py
│   ├── scoring.py
│   ├── guias.py
│   ├── historial.py
│   ├── coaching.py
│   ├── calibracion.py
│   ├── dashboard_data.py
│   ├── fase2.py
│   ├── fase3.py
│   ├── pdf_parser.py
│   ├── presupuesto.py
│   ├── excel_writer.py
│   ├── word_writer.py
│   ├── coaching_word.py
│   └── kpi_report.py
│
├── templates/
│   ├── _base.html
│   ├── index.html
│   ├── revisar.html
│   ├── resultado.html
│   ├── dashboard.html
│   ├── coaching.html
│   ├── revisar_coaching.html
│   ├── calibracion.html
│   ├── historial_detalle.html
│   └── lote_priorizado.html
│
└── tests/
    ├── ...
    ├── test_fase2.py
    └── test_fase3.py
```

---

# Arquitectura

La aplicación sigue una separación por capas:

```text
Plantillas / UI
      ↓
Blueprints Flask
      ↓
Servicios / lógica de negocio
      ↓
Evaluador, scoring, historial y módulos analíticos
```

La lógica principal procura mantenerse fuera de Flask, lo que facilita:

- pruebas automatizadas;
- mantenimiento;
- futuras integraciones con otros sistemas;
- migración a API o base de datos sin rehacer toda la interfaz.

---

# Integración futura con otros sistemas

Gran parte de la lógica vive en `src/services/` y módulos independientes de Flask.

Esto permite que, en una siguiente etapa, Dropi QA pueda integrarse con:

- Intercom;
- Monitor u otros sistemas internos;
- APIs;
- una base de datos centralizada;
- procesos automáticos de selección y auditoría.

Actualmente el proyecto utiliza archivos JSON para varias persistencias locales. Si el volumen crece significativamente o varios usuarios escriben simultáneamente, el siguiente paso arquitectónico natural es migrar a una base de datos relacional como PostgreSQL.

---

# Archivos que no deberían versionarse en Git

Por contener información local, respaldos o datos operativos variables, se recomienda mantener fuera del repositorio:

```text
.env
*.backup
backup_fase*/
aprendizaje_ia.jsonl
config/criticos_estado.json
config/metas_auditoria.json
```

Estos archivos pueden existir normalmente en el computador donde se ejecuta la aplicación, pero no necesitan formar parte del código fuente de GitHub.

---

# Estado actual del proyecto

A la fecha, Dropi QA integra tres capas de evolución funcional:

### Base
Evaluación QA + revisión humana + documentos + historial + Dashboard + Coaching + calibración.

### Fase 2
Reincidencias + tendencias + pérdida de puntos + cobertura de auditorías + casos críticos.

### Fase 3
Calibración avanzada + aprendizaje humano + biblioteca de errores IA + confianza IA + riesgo + muestreo inteligente.

El objetivo de estas fases es que el aplicativo evolucione de:

> **“evaluar conversaciones”**

hacia:

> **“detectar qué está pasando con la calidad, por qué está pasando, dónde intervenir y qué tan confiable es la automatización”.**

---

## Principio de diseño

Dropi QA está diseñado para que la IA aumente la capacidad del equipo de calidad sin reemplazar el criterio humano.

La automatización propone y prioriza; **el auditor conserva el control de la evaluación oficial**.
