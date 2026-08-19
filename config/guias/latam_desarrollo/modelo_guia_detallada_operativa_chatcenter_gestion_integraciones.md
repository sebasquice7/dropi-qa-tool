# Modelo_Guia_detallada_Operativa_Chatcenter_Gestion_Integraciones

OBJETIVO
Establecer los lineamientos para la identificación, validación, gestión y escalamiento de incidencias relacionadas con la integración entre ChatCenter, Meta Business y WhatsApp Business API, garantizando una atención uniforme, eficiente y alineada con los procedimientos definidos por el área de Integraciones.
ALCANCE
Aplica para todos los agentes encargados de la atención de casos relacionados con Integraciones ChatCenter.
Incluye la gestión de:
Integraciones ChatCenter.
Configuración de Meta Business.
Creación de plantillas WhatsApp.
Automatizaciones.
Variables dinámicas.
Errores Meta API.
Problemas de envío de mensajes.
Problemas de conversaciones.
Problemas de autenticación.
Problemas de conexión con Dropi.
Errores de plantillas.
Restricciones de Meta.
DEFINICIONES
ChatCenter
Plataforma utilizada para centralizar la gestión de conversaciones provenientes de diferentes canales de comunicación, incluyendo WhatsApp Business.
Meta Business Manager
Herramienta de Meta que permite administrar cuentas comerciales, activos digitales, plantillas y números de WhatsApp Business.
WhatsApp Business API
Interfaz oficial de WhatsApp utilizada para integrar sistemas externos y automatizar conversaciones empresariales.
Plantilla de Mensaje
Mensaje previamente aprobado por Meta que puede utilizarse para iniciar conversaciones o enviar comunicaciones automatizadas.
Variable Dinámica
Campo utilizado dentro de una plantilla para personalizar información como nombres, números de pedido o datos específicos del cliente.
Automatización
Proceso configurado para ejecutar acciones automáticas sin intervención manual.
Conversación de Reenganche
Comunicación iniciada después de superar la ventana de atención de 24 horas establecida por WhatsApp.
Spam Rate Limit
Restricción impuesta por Meta cuando se detecta un volumen excesivo de mensajes o comportamientos considerados riesgosos.
RESPONSABLES
GUIA DETALLADA
5.1 INTEGRACIÓN CHATCENTER
La integración permite conectar ChatCenter con WhatsApp Business para centralizar la atención de conversaciones.
Procedimiento
Acceder a la configuración de ChatCenter.
Seleccionar la opción de integración.
Vincular la cuenta correspondiente.
Autorizar los permisos requeridos.
Confirmar la conexión.
Validar el funcionamiento.
Consideraciones
La cuenta debe contar con permisos administrativos.
Debe existir una cuenta Meta Business activa.
5.2 CREACIÓN DE PLANTILLAS META
Las plantillas permiten iniciar conversaciones o enviar mensajes automatizados aprobados por Meta.
Procedimiento
Acceder al administrador de plantillas.
Crear una nueva plantilla.
Definir categoría y contenido.
Configurar variables dinámicas.
Enviar a aprobación.
Esperar validación por parte de Meta.
Consideraciones
Las plantillas deben cumplir las políticas de Meta.
El contenido puede ser rechazado si incumple lineamientos.
5.3 AUTOMATIZACIÓN DE MENSAJES
Las automatizaciones permiten ejecutar respuestas automáticas bajo condiciones previamente configuradas.
Procedimiento
Ingresar al módulo de automatizaciones.
Crear una nueva regla.
Definir el evento disparador.
Configurar la acción correspondiente.
Guardar la configuración.
Realizar pruebas de funcionamiento.
Consideraciones
Deben validarse todas las variables utilizadas.
Se recomienda realizar pruebas antes de activar la automatización.
5.4 ERROR #131008 REQUIRED PARAMETER IS MISSING
Este error ocurre cuando una solicitud enviada a Meta no contiene un parámetro obligatorio.
Procedimiento
Revisar la configuración del mensaje.
Identificar el parámetro faltante.
Completar la información requerida.
Reintentar el envío.
Consideraciones
Todos los campos obligatorios deben estar diligenciados.
Las variables dinámicas deben contener información válida.
5.5 ERROR #131009 EL VALOR DEL PARÁMETRO NO ES VÁLIDO
Este error se presenta cuando un parámetro contiene información incorrecta o incompatible.
Error de validación de parámetros.
Procedimiento
Identificar el parámetro afectado.
Validar el formato de la información.
Corregir el valor.
Reintentar el proceso.
Consideraciones
Los formatos deben coincidir con los requeridos por Meta.
Deben evitarse caracteres no permitidos.
5.6 ERROR #132012 PARAMETER FORMAT DOES NOT MATCH
Este error indica que la estructura del contenido no coincide con el formato aprobado en la plantilla.
Error de formato en plantillas.
Procedimiento
Revisar la plantilla aprobada.
Comparar el contenido enviado.
Ajustar el formato.
Realizar una nueva prueba.
Consideraciones
El contenido debe coincidir exactamente con la plantilla aprobada.
Las variables deben mantenerse en la misma posición.
5.7 ERROR #132000 NUMBER OF PARAMETERS DOES NOT MATCH
Este error ocurre cuando la cantidad de variables utilizadas no coincide con las variables definidas en la plantilla.
Error por cantidad incorrecta de parámetros.
Procedimiento
Revisar la plantilla.
Contar las variables configuradas.
Validar las variables enviadas.
Corregir la configuración.
Consideraciones
La cantidad debe coincidir exactamente.
No pueden faltar ni sobrar variables.
5.8 ERROR #100 INVALID PARAMETER
Este error indica que uno o varios parámetros no son válidos para la operación solicitada.
Error de parámetro inválido.
Procedimiento
Identificar el parámetro afectado.
Revisar la configuración.
Corregir la información.
Reintentar la acción.
EJEMPLO DE CÓMO NO DEBE IR: Las variables deben ser números.
Consideraciones
Deben utilizarse únicamente parámetros permitidos.
La validación debe realizarse antes de escalar.
5.9 ERROR #132005 TRANSLATED TEXT TOO LONG
Este error se presenta cuando el contenido enviado excede la cantidad de caracteres permitidos por Meta para la plantilla configurada.
Error relacionado con longitud excesiva del texto enviado.
Procedimiento
Revisar el contenido de la plantilla.
Identificar el texto que supera el límite permitido.
Reducir la longitud del mensaje.
Guardar los cambios realizados.
Realizar una nueva prueba de envío.
Consideraciones
Meta establece límites máximos de caracteres para determinados campos.
Los textos extensos pueden provocar rechazos automáticos.
Se recomienda utilizar mensajes cortos y directos.
5.10 ERROR #132001 TEMPLATE NAME DOES NOT EXIST
Este error ocurre cuando el nombre de la plantilla o el idioma configurado no coincide con la información aprobada por Meta.
Error relacionado con nombre o idioma incorrecto de la plantilla.
Procedimiento
Validar el nombre de la plantilla.
Verificar el idioma configurado.
Comparar la información con Meta Business Manager.
Corregir la configuración.
Realizar una nueva prueba.
Consideraciones
El nombre debe coincidir exactamente con la plantilla aprobada.
El idioma debe corresponder al configurado en Meta.
Diferencias mínimas pueden generar el error.
5.11 VARIABLES TRUNCADAS
Este error se presenta cuando las variables dinámicas utilizadas dentro de una plantilla no siguen el orden o la secuencia esperada.
Ejemplo de variables mal configuradas o incompletas.
Procedimiento
Revisar la estructura de la plantilla.
Validar el orden de las variables.
Confirmar que la numeración sea consecutiva.
Corregir las variables faltantes.
Guardar la configuración.
Realizar pruebas de funcionamiento.
Consideraciones
Las variables deben seguir una secuencia lógica.
No deben omitirse posiciones intermedias.
Toda modificación debe validarse antes de publicar.
5.12 ERROR AL TOMAR CONVERSACIÓN
Este inconveniente ocurre cuando un agente intenta asumir una conversación y el sistema no lo permite correctamente.
Error relacionado con la asignación o toma de conversaciones.
Procedimiento
Validar la configuración de la bandeja.
Revisar los permisos del agente.
Confirmar la plantilla predeterminada.
Actualizar la configuración.
Realizar una nueva prueba.
RUTA PARA VERIFICAR EL NÚMERO: BUSINESS MANAGER
Consideraciones
Los permisos incorrectos pueden impedir la asignación.
Debe verificarse la configuración de la cuenta.
5.13 UNSUPPORTED POST REQUEST
Este error se presenta cuando Meta rechaza una solicitud debido a una configuración incorrecta o una referencia inválida.
Error Unsupported Post Request generado por Meta.
Procedimiento
Validar la cuenta conectada.
Revisar los identificadores utilizados.
Confirmar la configuración de Meta Business.
Verificar la vinculación de WhatsApp.
Reintentar la operación.
Consideraciones
Generalmente está relacionado con configuraciones incorrectas.
Deben revisarse permisos y accesos activos.
5.14 ERRORES DE PLANTILLAS
Los errores de plantillas pueden generarse por idioma incorrecto, imágenes no compatibles o archivos adjuntos que incumplen los requisitos definidos por Meta.
Ejemplos de errores relacionados con plantillas y contenido multimedia.
Procedimiento
Validar el idioma configurado.
Revisar el archivo adjunto.
Confirmar que el formato sea compatible.
Comparar la configuración con la plantilla aprobada.
Realizar una nueva prueba.
Consideraciones
El idioma debe coincidir con la plantilla aprobada.
Los archivos deben cumplir los formatos permitidos.
Las imágenes deben encontrarse disponibles públicamente cuando corresponda.
5.15 BUSINESS ACCOUNT LOCKED
Este error indica que la cuenta comercial de Meta se encuentra restringida o bloqueada.
Mensaje de bloqueo de cuenta comercial.
Procedimiento
Validar el estado de la cuenta en Meta Business Manager.
Revisar las notificaciones activas.
Confirmar el motivo de la restricción.
Informar al usuario.
Orientar sobre el proceso de apelación cuando aplique.
Consideraciones
El desbloqueo depende exclusivamente de Meta.
El área de Integraciones no puede retirar restricciones directamente.
Debe verificarse el cumplimiento de políticas comerciales.
5.16 SPAM RATE LIMIT HIT
Este error se genera cuando Meta detecta un volumen elevado de mensajes o una tasa de interacción considerada riesgosa.
Restricción por límite de envío de mensajes.
Procedimiento
Revisar la actividad reciente.
Validar la cantidad de mensajes enviados.
Confirmar el estado de calidad de la cuenta.
Esperar el periodo de liberación establecido por Meta.
Realizar nuevas pruebas posteriormente.
Consideraciones
El restablecimiento depende de Meta.
El exceso de mensajes puede afectar la reputación de la cuenta.
Deben respetarse las políticas de mensajería.
5.17 RE-ENGAGEMENT MESSAGE
Este mensaje se genera cuando se intenta contactar a un usuario después de haber transcurrido más de 24 horas desde la última interacción.
Error relacionado con la ventana de conversación de WhatsApp.
Procedimiento
Validar la fecha y hora de la última interacción.
Confirmar que hayan transcurrido más de 24 horas.
Verificar la existencia de una plantilla aprobada.
Utilizar una plantilla autorizada para reiniciar la conversación.
Realizar una nueva prueba de envío.
Consideraciones
WhatsApp limita las conversaciones después de 24 horas.
Solo pueden utilizarse plantillas aprobadas por Meta.
El mensaje libre no podrá enviarse fuera de la ventana permitida.
5.18 USER'S NUMBER IS PART OF AN EXPERIMENT
Este error indica que el número del destinatario se encuentra dentro de un experimento o validación realizada por WhatsApp.
Error relacionado con restricciones temporales de WhatsApp.
Procedimiento
Validar el número de destino.
Confirmar que la numeración sea correcta.
Realizar una nueva prueba posteriormente.
Informar al usuario sobre la restricción temporal.
Consideraciones
La restricción depende directamente de WhatsApp.
No existe una acción correctiva desde ChatCenter.
Generalmente se resuelve automáticamente.
5.19 SOMETHING WENT WRONG
Este error corresponde a una falla interna generada por Meta durante el procesamiento de la solicitud.
Error genérico de procesamiento.
Procedimiento
Reintentar la operación.
Validar la conectividad de la cuenta.
Confirmar el estado de Meta Business.
Revisar si existen incidencias generales.
Escalar cuando el problema persista.
Consideraciones
Puede tratarse de una falla temporal.
Generalmente se relaciona con servicios de Meta.
Debe validarse antes de escalar.
5.20 RECEIVER IS INCAPABLE OF RECEIVING THIS MESSAGE
Este error indica que el destinatario no puede recibir mensajes mediante WhatsApp Business.
Error relacionado con la recepción de mensajes.
Procedimiento
Verificar el número telefónico.
Confirmar que tenga WhatsApp activo.
Validar el formato internacional.
Realizar una nueva prueba.
Consideraciones
El número puede encontrarse inactivo.
Puede tratarse de un número fijo.
Debe verificarse la información antes de escalar.
5.21 CUENTA NO VINCULADA A FACEBOOK
Este inconveniente ocurre cuando la cuenta de WhatsApp Business no se encuentra correctamente vinculada al entorno de Meta Business.
Error relacionado con la vinculación entre Meta y WhatsApp.
Procedimiento
Acceder a Meta Business Manager.
Revisar las cuentas vinculadas.
Confirmar la asociación de WhatsApp.
Corregir la configuración cuando corresponda.
Realizar una nueva validación.
Consideraciones
La vinculación es obligatoria para el funcionamiento correcto.
Deben existir permisos administrativos suficientes.
5.22 ALERTAS DE NO CONEXIÓN CON DROPI
Estas alertas indican que ChatCenter presenta problemas de comunicación con la plataforma Dropi.
📸
Alerta relacionada con pérdida de conexión entre plataformas.
Procedimiento
Validar la integración activa.
Revisar credenciales configuradas.
Confirmar conectividad.
Actualizar la integración.
Realizar una nueva prueba.
Consideraciones
La sincronización depende de ambas plataformas.
Deben revisarse credenciales y permisos.
5.23 MESSAGE UNDELIVERABLE
Este error indica que el mensaje no pudo ser entregado correctamente al destinatario.
Error de entrega de mensajes.
Procedimiento
Validar el número telefónico.
Revisar el estado del destinatario.
Confirmar que el mensaje cumpla las políticas de Meta.
Realizar una nueva prueba.
Consideraciones
El número puede encontrarse inactivo.
Puede existir una restricción temporal.
Deben verificarse las políticas de mensajería.
5.24 ERROR 135000
Este error corresponde a una validación generada por Meta relacionada con configuraciones internas o restricciones específicas.
Error 135000 reportado por Meta.
Procedimiento
Revisar el detalle del error.
Validar la configuración actual.
Confirmar permisos y accesos.
Realizar pruebas de funcionamiento.
Escalar cuando corresponda.
Consideraciones
El análisis debe realizarse caso por caso.
Puede requerir intervención del equipo de Integraciones.
Debe documentarse completamente la evidencia.
ANEXOS
6.1 Video de Integración ChatCenter
https://drive.google.com/file/d/1jYZApJmlvpIc1fe2dleZYGCmW5PqxGtZ/view?usp=sharing
Descripción:
Video instructivo para realizar la integración entre ChatCenter y WhatsApp Business.
6.2 Video de Automatización de Mensajes
https://drive.google.com/file/d/1bAmaZSlmKQfzgaNbVFXaYChwas-ReS_d/view?usp=sharing
Descripción:
Video explicativo para configurar automatizaciones y plantillas dentro de ChatCenter.
6.3 Meta Business Suite
https://business.facebook.com/
Descripción:
Portal oficial para administrar cuentas comerciales, plantillas, números de WhatsApp Business y activos de Meta.
6.4 Soporte para Desarrolladores Meta
https://developers.facebook.com/support/
Descripción:
Canal oficial de Meta para reportar errores de API, problemas de integración y crear casos de soporte técnico.
6.5 Centro de Ayuda Meta Business
https://business.facebook.com/
Descripción:
Acceso al Centro de Ayuda y opciones de soporte para cuentas comerciales, páginas, Instagram y Facebook.
REGISTROS
Responsable | Función
Equipo Integraciones | Gestión de incidencias ChatCenter
Johan Cortez | Escalamientos de Integraciones
Equipo Desarrollo | Incidencias técnicas avanzadas
Equipo Meta Business | Validaciones de plantillas y cuentas
Registro | Responsable
Casos de Integración ChatCenter | Equipo Integraciones
Casos de Plantillas Meta | Equipo Integraciones
Casos WhatsApp Business API | Equipo Integraciones
Casos de Automatización | Equipo Integraciones
Casos de Conversaciones | Equipo Integraciones
Casos de Restricciones Meta | Equipo Integraciones
Casos Escalados a Desarrollo | Equipo Desarrollo
Escalamientos Avanzados | Johan Cortez
