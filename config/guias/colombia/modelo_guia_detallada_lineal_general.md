# Modelo Guía Detallada Lineal General

⚠️ ACTUALIZACIÓN DE ALCANCE (vigente desde esta versión — reemplaza el alcance anterior más amplio de este documento)

Línea General SOLO debe atender directamente estos 3 tipos de caso:
1. Publicidad engañosa.
2. Baneos que impiden el ingreso a la plataforma (desbaneo de acceso).
3. Autenticación de doble factor (2FA) — no llega el código, problemas para validar el segundo factor.

CUALQUIER otro tipo de solicitud (anulaciones, devoluciones, Error 500, gestión de comunidades, consultas informativas, bloqueo de IP, cambio de correo, inactivación de cuenta, atención a usuarios finales, etc.) NO le corresponde resolverlo directamente a Línea General — debe redirigir al cliente al botón flotante, que lo dirige al canal correcto según su caso.

INSTRUCCIÓN PARA LA EVALUACIÓN DE CALIDAD (importante, leer antes de calificar):
Si la conversación es sobre un tema que NO es publicidad engañosa, baneo de acceso, ni 2FA — y el asesor redirigió correctamente al cliente al botón flotante (en vez de intentar resolver el caso él mismo, o de escalarlo manualmente por otro medio) — esto es el comportamiento CORRECTO y esperado, no una falla. En ese escenario:
- Los ítems de "Procedimiento y Solución" (precisión técnica, resuelve en primer contacto, etc.) deben calificarse como CUMPLIDOS — redirigir al botón flotante ES la solución correcta para un caso fuera de este alcance, no la ausencia de una solución.
- NO se debe penalizar al asesor por "no resolver el caso" cuando lo correcto era, precisamente, no intentar resolverlo directamente y redirigir.
- Si en cambio el asesor SÍ intentó resolver un caso fuera de este alcance (sin redirigir al botón flotante), ahí sí corresponde señalarlo como una desviación del proceso correcto.

--- El resto de este documento (secciones 5.1 a 5.10) describe el detalle operativo histórico de cuando Línea General sí gestionaba directamente estos temas. Se conserva como referencia de contexto, pero el ALCANCE VIGENTE es el que se define arriba. ---

OBJETIVO
Establecer una guía detallada para la correcta gestión, clasificación y escalamiento de solicitudes recibidas por Línea General dentro de la plataforma Dropi, garantizando una atención adecuada según el tipo de caso reportado por el usuario.
ALCANCE
Esta guía aplica para:
Línea General.
Atención inicial.
Gestión de bloqueos.
Gestión de autenticación.
Gestión de IP.
Gestión de órdenes y guías.
Errores de plataforma.
Gestión de comunidades.
Atención al ciudadano.
Consultas informativas.
Incluye:
Validación de usuarios.
Escalamiento de bloqueos.
Validación OTP.
Cambio de correo.
Bloqueos IP.
Gestión de anulaciones.
Devoluciones injustificadas.
Error 500.
Inactivación de cuentas.
Gestión de comunidades.
Atención usuarios finales.
DEFINICIONES
Línea General
Canal de atención encargado de la recepción y clasificación inicial de solicitudes.
OTP
Código de autenticación enviado al correo del usuario para validación de acceso.
Bloqueo de cuenta
Restricción de acceso aplicada a usuarios por validaciones de seguridad.
Bloqueo IP
Restricción aplicada sobre una dirección IP específica.
Dev. injustificadas
Casos donde una guía retorna en estado devolución sin justificación válida.
Jira
Herramienta utilizada para escalamiento técnico.
Atención al ciudadano
Canal encargado de la atención a usuarios finales.
RESPONSABLES
GUIA DETALLADA
5.1 GESTIÓN DE RECEPCIÓN Y CLASIFICACIÓN INICIAL
Proceso
Se recibe la solicitud por WhatsApp integrado en Intercom.
Se valida:
País.
Tipo usuario.
Rol plataforma.
Se solicita evidencia cuando aplica.
Se registra nota interna para seguimiento.
5.2 GESTIÓN DE BLOQUEOS DE CUENTA (BANEO / DESBANEO)
Validación inicial
Solicitar correo y captura error.
Validar estado en Dropi Administrativo.
Registrar caso en documento control comercial.
Estados posibles
Activo.
Inactivo.
Baneado.
Desbaneado.
Tiempos operativos
Casos antes del mediodía: revisión misma tarde.
Casos posteriores a las 3:00 p.m.: revisión siguiente día.
5.3 GESTIÓN DE AUTENTICACIÓN Y CAMBIO DE CORREO
Casos aplicables
No llega código OTP.
Cambio correo autenticación.
Cambio correo inicio sesión.
Información requerida
Datos personales.
Correos.
País.
Número celular.
Evidencias fotográficas.
Proceso
Registro en documento comercial.
Programación videollamada.
Validación identidad.
Seguimiento estados:
Evidencia.
Revisión.
Aprobado.
5.4 GESTIÓN DE BLOQUEO IP
Información requerida
Número IP.
Captura bloqueo.
Correo asociado.
Gestión
Validar datos.
Registrar caso.
Escalar equipo TI.
Notificar internamente si requiere priorización.
5.5 GESTIÓN DE ÓRDENES Y GUÍAS
Anulación
Se valida que:
Orden esté pendiente.
Guía preparada para transportadora.
Luego se direcciona al área responsable.
Casos sin movimiento
Se valida:
Orden pendiente sin movimiento.
Guía generada sin movimiento.
Guía preparada sin movimiento.
Devoluciones injustificadas
Debe validarse estado DEVOLUCIÓN antes de escalar.
5.6 GESTIÓN DE ERRORES DE PLATAFORMA (ERROR 500)
Checklist inicial
Recargar.
Cerrar sesión.
Modo incógnito.
Otro navegador.
Borrar caché.
Validar conexión.
Otro dispositivo.
Escalamiento
Si persiste:
Solicitar video desde PC.
Escalar por Jira.
Informar recomendaciones técnicas.
5.7 GESTIÓN DE INACTIVACIÓN DE CUENTA
Información requerida
Motivo.
Tipo usuario.
Correo registro.
Consideraciones
Las cuentas no se eliminan.
Solo se inactivan.
El correo no podrá reutilizarse.
5.8 GESTIÓN DE COMUNIDAD
Cambio o ingreso
Se comparte ruta oficial de solicitud.
Validaciones
Validar comunidad perfil usuario.
Consultar internamente cuando no aplique el cambio.
Beneficios
Se informa sobre beneficios estándar de pertenecer a comunidad.
5.9 GESTIÓN DE USUARIOS FINALES
Atención ciudadana
Cuando corresponde a cliente final:
Se remite canal oficial.
Se solicita evidencia mínima.
Se informa tiempo estimado:
10 a 15 días hábiles.
5.10 GESTIÓN DE CONSULTAS INFORMATIVAS
Consultas frecuentes
Cómo operar.
Cómo montar pedidos.
Qué es Dropi.
Roles plataforma.
Países habilitados.
Orientación
Se remite a:
Dropi Academy.
Enlaces oficiales.
Información resumida.
ANEXOS
Evidencias solicitadas durante la gestión de casos
Gestión de bloqueos de cuenta
Captura del error presentado.
Correo asociado a la cuenta.
Gestión de autenticación y cambio de correo
Datos personales del usuario.
Correos electrónicos.
País.
Número celular.
Evidencias fotográficas.
Fotos del documento de identidad.
Fotos del rostro con documento.
Gestión de bloqueo IP
Número de IP.
Captura donde figure el bloqueo.
Correo asociado.
Gestión de errores de plataforma (Error 500)
Video desde PC evidenciando:
Recarga de página.
Cierre de sesión.
Navegación incógnita.
Borrado de caché.
Error presentado.
Herramientas y plataformas utilizadas
WhatsApp integrado en Intercom.
Dropi Administrativo.
Documento de control comercial.
Google Chat.
Jira.
REGISTROS
Área | 
LÍNEA GENERAL | Recepción y clasificación inicial
COMPLIANCE | Validaciones y autenticación
TI | Validación técnica y desbloqueos
ANULACIONES | Gestión de anulaciones
LOGÍSTICA | Gestión de guías y devoluciones
SOPORTE | Seguimiento y escalamiento
Registro | Responsable | Frecuencia
Registro bloqueos | Línea General | Diario
Registro autenticación | Compliance | Diario
Registro IP | TI | Diario
Registro anulaciones | Anulaciones | Diario
Registro devoluciones | Logística | Diario
Registro Error 500 | Soporte | Según solicitud
