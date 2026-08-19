# Revision y Reasignacion de Solicitudes

OBJETIVO:
Gestionar las solicitudes, novedades críticas de última milla (siniestros, pérdidas o averías) y tickets erróneamente asignados por el sistema, mediante su centralización, investigación, validación y direccionamiento. Lo anterior garantiza la correcta administración de las bandejas logísticas, la calibración operativa de la primera línea y la radicación formal de reclamaciones económicas ante las transportadoras aliadas.
ALCANCE:
La cobertura operativa abarca la gestión de incidencias logísticas e indemnizaciones dentro del territorio de Dropi Colombia a través de Intercom, el módulo CAS, LogiApp, WhatsApp y herramientas de Google. Incluye la auditoría externa en portales de tracking, la coordinación con transportadoras aliadas, la depuración de casos asignados por el bot Gali y el soporte operativo secundario en activaciones, recolecciones y devoluciones.
DEFINICIONES:
CAS (Centro de Atención / Servicio de Transportadora): Canal y módulo administrativo centralizado donde se recepcionan, monitorean y gestionan las interacciones y respuestas de las transportadoras aliadas respecto a las guías de envío.
• Intercom: Plataforma de omnicanalidad corporativa donde se reciben, clasifican, atienden y redireccionan los tiquets, chats e interacciones con los usuarios finales de Dropi.
• LogiApp / Dropi: Aplicativo core e interfaz integrada donde se consultan los detalles de las órdenes, se diferencian las tipologías de clientes y se parametrizan los formularios de radicación formal de indemnizaciones.
• Gali / Bots: Motor de enrutamiento y automatización inicial encargados del direccionamiento de tiquets, cuyas asignaciones erróneas generan saturación en la bandeja de PQR y requieren depuración manual.
• Siniestro / Pérdida: Tipología técnica de solicitud configurada en el aplicativo core para derivar el expediente a investigación y cobro financiero ante la transportadora por congelamiento o anomalías críticas.
• Inhouse / Controlador: Personal de representación directa de las transportadoras aliadas que actúa en la primera línea operativa para filtrar y trasladar casos con anomalías logísticas.
• ANS / SLA: Acuerdo de Nivel de Servicio preventivo establecido entre 20 y 35 días calendario regulado por las transportadoras para emitir un dictamen final de investigación.
• Matriz Unificada de Seguimiento: Base de datos interna en Google Sheets donde se registran y controlan de forma obligatoria los términos contractuales y estados de los radicados ejecutados.
RESPONSABLES:
Auxiliar CAS: encargado de la revisión de guías con anomalías, la radicación de solicitudes de indemnización por pérdida o deterioro en LogiApp, la carga de evidencias a Google Drive, la notificación del ANS al usuario, la depuración de bandejas en Intercom y el registro en Google Sheets para la operación de Dropi Colombia.
Líder del Área CAS: asume la responsabilidad directa del área, coordinando las prioridades diarias de apoyo entre transportadoras y supervisando la gestión general del proceso.
Inhouses de Transportadoras: Enlaces operativos de los aliados logísticos de primera línea encargados de filtrar e identificar anomalías tempranas en las guías y transferir los expedientes de indemnización al área CAS.
Transportadoras Aliadas: Operadores logísticos externos (Inter Rapidísimo, Envía, Coordinadora, Veloces) responsables de ejecutar las investigaciones físicas de la mercancía y dictaminar la aprobación o rechazo de las indemnizaciones.
GUÍA DETALLADA (PASO A PASO):
ACTIVIDAD A: Gestión de Bandejas, Triangulación y Depuración Dinámica
Paso A.1: Revisión de canales corporativos de coordinación El Auxiliar CAS ingresa diariamente al canal corporativo de WhatsApp y a la plataforma Intercom para revisar reportes urgentes de guías en siniestro o transferencias de inhouses.
Paso A.2: Evaluación de métricas y volumen de colas Se ingresa al módulo administrativo del CAS en Intercom para evaluar la cantidad de solicitudes acumuladas en cola y activas por cada transportadora.
Paso A.3: Definición de prioridades operativas Con base en el volumen de casos por transportadora, el Auxiliar CAS reporta al líder de área y prioriza la bandeja que presente mayor saturación o congestión operacional.
Paso A.4: Detección de casos mal enrutados por el sistema Se examinan la cola general y la bandeja de PQR para identificar tiquets asignados erróneamente por el bot Gali o por selección equivocada de los usuarios.
Paso A.5: Triaje y reasignación de tiquets erróneos Se leen los historiales de los tiquets mal direccionados y se reasignan a las bandejas correspondientes (despachos, recolecciones, activaciones) o se responden de forma directa.
ACTIVIDAD B: Auditoría de Tracking y Verificación de Anomalías Logísticas
Paso B.1: Recepción e identificación de la guía El Auxiliar CAS toma los números de guías transferidos por los inhouses o seleccionados de la bandeja activa que presentan anomalías o solicitudes de indemnización.
Paso B.2: Verificación externa en el portal del aliado Se accede al portal web de la transportadora correspondiente para auditar el estado físico real del envío y confirmar la ausencia de movimiento o congelamiento logístico prolongado.
Paso B.3: Búsqueda de la orden en el aplicativo core En paralelo, se ingresa al aplicativo LogiApp / Dropi y se digita el número de guía u orden para desplegar los detalles completos de la mercancía en el sistema interno.
Paso B.4: Confirmación del requerimiento de investigación Se valida si el estado del envío requiere solicitar una investigación por pérdida ante la transportadora o si procede un cierre logístico según la fecha de último ingreso a bodega.
ACTIVIDAD C: Parametrización y Radicación Formal de Indemnizaciones
Paso C.1: Clasificación de la tipología del solicitante Se verifica en el aplicativo core si el usuario solicitante corresponde a un Proveedor o a un Emprendedor para aplicar las reglas comerciales de cálculo económico.
Paso C.2: Registro de anotación estándar en la orden Se selecciona e inserta en el historial de la orden la plantilla de respuesta predeterminada estandarizada para justificar la solicitud por pérdida o siniestro.
Paso C.3: Inserción obligatoria del ID de conversación Se copia el código numérico de identificación de la conversación de Intercom y se pega en la casilla obligatoria de radicación de LogiApp para garantizar la trazabilidad cruzada.
Paso C.4: Configuración de menús desplegables Se parametrizan las casillas del formulario del aplicativo core seleccionando la opción "Indemnización" como Tipo de Solicitud y "Pérdida" como Subtipo.
Paso C.5: Captura visual de evidencia técnica Se utiliza la herramienta de recortes del sistema operativo para tomar una captura de pantalla del portal de la transportadora donde se evidencia el congelamiento de la guía.
Paso C.6: Carga de evidencias en la nube La imagen capturada se aloja manualmente en la carpeta correspondiente dentro del repositorio corporativo de Google Drive.
Paso C.7: Generación e indexación del enlace público Se extrae el enlace público de la imagen cargada en Google Drive y se pega en la casilla de soportes del formulario de radicación en LogiApp.
Paso C.8: Determinación y registro del valor declarado Se calcula e ingresa manualmente el valor económico a indemnizar, aplicando las cantidades de producto y los criterios según la cartera del perfil del solicitante.
Paso C.9: Generación del radicado en el sistema Se presiona el botón de envío en LogiApp para consolidar la solicitud y generar el código formal de radicado ante el sistema integrado.
ACTIVIDAD D: Notificación al Usuario y Asentamiento en Matriz
Paso D.1: Notificación formal de apertura y ANS El Auxiliar CAS regresa al chat del usuario en Intercom, envía la plantilla de respuesta informando la radicación del caso y notifica el ANS de 20 a 35 días calendario.
Paso D.2: Despedida y cierre inicial de la interacción Se concluye la conversación en Intercom con el mensaje de despedida corporativo, dejando el tiquet parametrizado según la tipología PQRK.
Paso D.3: Transcripción manual a la matriz de seguimiento Se abre la Matriz Unificada de Seguimiento en Google Sheets y se transcriben de forma manual los datos del radicado generado para el control de términos contractuales.
ACTIVIDAD E: Auditoría de Inhouses y Soporte Operativo Complementario
Paso E.1: Auditoría de respuestas brindadas por inhouses Se revisan los historiales e interacciones transferidas por los inhouses en Intercom para verificar que hayan entregado información adecuada y retroalimentar incorrecciones.
Paso E.2: Brindis de soporte en activaciones y recolecciones Cuando la operación presente baja demanda en indemnizaciones, el Auxiliar CAS brinda apoyo en las bandejas de activaciones de usuarios, cambios de recolección y solicitudes de insumos.
Paso E.3: Gestión de devoluciones injustificadas Se analizan guías reportadas con devoluciones prolongadas para determinar si requieren un primer paso por la mesa CAS o si aplican para escalamiento directo.
Paso E.4: Control de métricas diarias de productividad Al finalizar la jornada, el Auxiliar CAS revisa sus métricas individuales de respuestas y radicados tramitados en el sistema para reportar el balance diario a la gerencia.
ANEXOS:
REGISTROS:
