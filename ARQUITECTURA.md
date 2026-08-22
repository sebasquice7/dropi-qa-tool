# Decisiones de arquitectura — Dropi QA

Este documento explica **por qué** el proyecto está construido como está — no solo el *qué*, sino el razonamiento detrás de cada decisión importante. La idea es que cualquier persona (incluido alguien sin experiencia técnica profunda) pueda entender por qué el sistema se armó así, y que cualquier desarrollador que lo revise (como Diego) vea que las decisiones fueron pensadas, no improvisadas.

---

## 1. Por qué Flask (y no Django, FastAPI, u otro)

**Decisión:** Flask como framework web.

**Por qué:**
- Flask es un framework **maduro** (existe desde 2010) y **ampliamente usado en producción** por empresas de todos los tamaños — no es una moda pasajera ni una herramienta experimental.
- Es **minimalista**: da solo lo esencial (rutas web, plantillas, manejo de peticiones) y deja que el desarrollador elija el resto — ideal para un proyecto que necesita crecer de forma controlada, sin cargar con funcionalidad que no se usa.
- Tiene una curva de aprendizaje baja, lo que importa porque este proyecto necesita poder ser mantenido por alguien que no es un ingeniero de software de tiempo completo.

**Alternativas consideradas:**
- *Django*: más completo (trae base de datos, autenticación de usuarios, panel de administración integrados), pero es mucho más pesado de lo que este proyecto necesita hoy. Traería complejidad innecesaria para una herramienta interna de este tamaño.
- *FastAPI*: excelente para APIs puras, pero está más orientado a servicios sin interfaz visual — este proyecto sí necesita páginas web completas (formularios, dashboards), donde Flask encaja mejor.

**Cuándo reconsiderar esto:** si el proyecto crece a necesitar autenticación de usuarios reales (no solo una contraseña compartida), múltiples equipos con permisos distintos, o una base de datos relacional compleja, ahí sí valdría la pena evaluar Django.

---

## 2. Por qué la arquitectura en capas (Blueprints + Servicios)

**Decisión:** Separar el código en 3 capas claras:
- **`templates/`** — lo que se ve (HTML)
- **`blueprints/`** — la traducción entre una petición web y la lógica (HTTP)
- **`services/`** — la lógica de negocio real, sin saber nada de Flask ni de páginas web

**Por qué:**
Al principio, todo el proyecto vivía en un solo archivo (`app.py`) de casi 1,000 líneas, con la lógica de evaluar, generar documentos, y mostrar páginas web todo mezclado. Esto es exactamente el tipo de estructura que "se pudre con el tiempo": cualquier cambio pequeño arriesga romper algo en otro lado, y es casi imposible que dos personas trabajen en el mismo archivo a la vez sin chocar.

Separarlo en capas resuelve 3 problemas reales:
1. **Se puede probar la lógica sin necesitar un navegador** — las 46 pruebas automatizadas prueban `services/` directamente, sin levantar el servidor web.
2. **Se puede integrar a otro sistema** (como "Monitor") **sin pasar por una página web** — cualquier otro programa en Python puede llamar directamente `iniciar_evaluacion(...)` sin necesidad de hacer una petición HTTP.
3. **Es más fácil de leer** — un archivo de 80 líneas que solo arma la aplicación es mucho más fácil de entender que uno de 1,000 líneas que hace de todo.

**Analogía simple:** es como separar, en un restaurante, al mesero (recibe el pedido, lo entrega) del cocinero (prepara la comida). Si el mesero también tuviera que cocinar, cualquier cambio en el menú requeriría reentrenar a todo el personal de sala. Separando los roles, cada uno se puede mejorar por separado.

---

## 3. Por qué JSON en archivos, y no una base de datos (por ahora)

**Decisión:** El historial de evaluaciones vive en un archivo `historial_evaluaciones.json`, no en una base de datos como PostgreSQL o MySQL.

**Por qué:**
- Al volumen actual (decenas o cientos de evaluaciones), un archivo JSON es simple, no requiere infraestructura adicional (no hay que instalar ni mantener un servidor de base de datos), y es fácil de respaldar (literalmente es un archivo que se puede copiar a Google Drive, como ya hace el programa).
- Añadir una base de datos real *hoy* sería complejidad que no se está aprovechando — es una decisión de "no construir lo que no necesitas todavía".

**Esto es la decisión con fecha de vencimiento más clara del proyecto.** A medida que el volumen crece hacia las 5,000 conversaciones/día de las que hablamos, un archivo JSON se vuelve:
- Lento de leer/escribir (hay que cargar todo el archivo en memoria cada vez)
- Riesgoso si dos evaluaciones intentan escribir al mismo tiempo (condición de carrera)

**Cuándo migrar:** cuando el volumen diario supere unas pocas centenas de evaluaciones consistentes, o cuando más de una persona/proceso escriba al historial simultáneamente. En ese punto, migrar a PostgreSQL (o similar) sería el siguiente paso natural — y como la lógica ya está separada en `services/` (ver punto 2), ese cambio se puede hacer sin tocar las rutas web ni las plantillas.

---

## 4. Por qué Gemini como IA principal, con Claude y ChatGPT de respaldo

**Decisión:** Gemini 2.5 Flash-Lite es el modelo por defecto; si falla, el sistema prueba automáticamente otros modelos de Gemini, y solo si el usuario configura las otras API keys, se pueden usar Claude/ChatGPT.

**Por qué:**
- Es gratis mientras el proyecto está en fase de validación — no hay razón de negocio para pagar antes de tener la aprobación.
- Los modelos de IA **cambian de nombre y se retiran con frecuencia** (nos pasó 3 veces durante este proyecto). Por eso el sistema no depende de un solo nombre de modelo fijo, sino de una **cadena de respaldo** — si un modelo deja de existir, el programa prueba el siguiente automáticamente, sin necesitar que alguien lo note y arregle el código a mano.

**Esto es, en sí mismo, una decisión de "resiliencia con el tiempo"**: en vez de asumir que un modelo de IA va a existir para siempre con el mismo nombre (una suposición que ya demostramos que es falsa), el sistema está diseñado para adaptarse solo cuando eso cambie.

---

## 5. Por qué pruebas automatizadas, type hints, y logging (no solo "que funcione")

**Decisión:** El proyecto tiene 46 pruebas automatizadas, cada función indica qué tipo de datos recibe y devuelve, y hay un sistema de logs en vez de solo mensajes en pantalla.

**Por qué — y esto responde directo a tu preocupación:**

Un proyecto de IA hecho "a la carrera" tiende a fallar de 3 formas específicas, y cada una tiene su contramedida aquí:

| Cómo suelen fallar los proyectos de IA sin ingeniería | Qué tiene este proyecto en contra |
|---|---|
| Un cambio pequeño rompe algo en otro lado sin que nadie lo note | 46 pruebas automatizadas — corren en segundos y avisan de inmediato si algo se rompió |
| Nadie puede diagnosticar por qué algo falló en producción | `logs/app.log` guarda cada evento con fecha y hora — no hay que adivinar qué pasó |
| El código es difícil de entender para alguien nuevo, así que nadie se atreve a tocarlo | Cada función documenta qué espera recibir y qué devuelve — reduce la necesidad de "adivinar" leyendo todo el archivo |

---

## 6. Sobre seguridad — qué se decidió y por qué

**Decisión:** Autenticación simple (usuario/contraseña), servidor solo accesible desde tu propia máquina, secretos fuera del código fuente, y validación de archivos subidos.

**Por qué este nivel, y no más:**
El nivel de seguridad de cualquier sistema debe ser proporcional a **su exposición real** — no tiene sentido construir defensas de nivel bancario para una herramienta que hoy solo usa un equipo interno, desde una sola máquina, sin acceso desde internet. Eso sería tiempo mal invertido.

Lo que sí se hizo, se hizo pensando en el escenario real:
- Los secretos (API keys) nunca están en el código — viven en `.env`, que además está excluido de git
- Los nombres de archivos subidos se sanitizan (probado con un ataque real simulado)
- El servidor no acepta conexiones desde fuera de tu propia máquina

**Cuándo subir el nivel:** el día que esto se exponga a internet (en vez de solo tu Mac) — ahí sí hace falta HTTPS, protección contra fuerza bruta en el login, y protección CSRF. No antes, porque sería esfuerzo sin beneficio real hoy.

---

## 7. Sobre las guías operativas — por qué "no penalizar sin evidencia"

**Decisión:** Si no existe una guía documentada para un tipo de caso, el programa simplemente no inyecta contexto de guía en el prompt de la IA — no penaliza al asesor por no seguir un proceso que no estaba documentado.

**Por qué:**
Esta fue una corrección directa a un problema real: la IA no debe inventar un criterio de evaluación sobre algo que no tiene forma de verificar. Es la misma lógica que aplicaría un analista de calidad responsable: si no hay un procedimiento escrito para un caso, no se puede penalizar a alguien por "no seguirlo". Cuando SÍ existe una guía relevante (ver `guias.py`), se inyecta como contexto de referencia para el ítem `precision_tecnica_fondo`, donde la IA compara los pasos técnicos del asesor contra los documentados.

Este es un ejemplo de una decisión de **diseño responsable de IA**, no solo de código — reconocer los límites de lo que el sistema puede evaluar con evidencia real, en vez de dejar que "invente" un juicio.

---

## Resumen — lo que este documento debería transmitirte

Ninguna de estas decisiones fue al azar, y ninguna es "para siempre" — cada una tiene un contexto (por qué se eligió así *ahora*) y una condición de cuándo reconsiderarla (qué señal indicaría que hay que cambiarla). Esa forma de pensar — decisiones explícitas, con razones y con fecha de vencimiento reconocida — es exactamente lo que separa un proyecto de IA que **perdura** de uno que se vuelve difícil de mantener con el tiempo.
