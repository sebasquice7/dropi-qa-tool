# Modelo Guía Detallada Desarrolo Soporte

OBJETIVO
Establecer los lineamientos para la atención, validación, escalamiento y seguimiento de incidencias técnicas, administrativas y funcionales dentro de la plataforma Dropi, garantizando una correcta gestión entre usuarios, Soporte Funcional, Desarrollo y demás áreas involucradas.
ALCANCE
Aplica para todos los agentes de Soporte Funcional encargados de:
Gestión de Intercom.
Escalamiento a Desarrollo.
Gestión de usuarios.
Gestión de roles.
Cambio de correos.
Seguridad y control de acceso.
Gestión de baneos.
Bloqueos IP.
Gestión de DropiCard.
Integraciones Shopify.
Soporte técnico.
Escalamientos Jira.
Atención de incidencias funcionales.
DEFINICIONES
Soporte Funcional
Área encargada de validar, diagnosticar y direccionar incidencias dentro de la plataforma.
Intercom
Sistema utilizado para la gestión y atención de conversaciones con usuarios.
Jira
Herramienta utilizada para registrar y gestionar incidencias técnicas por parte del equipo de desarrollo.
DropiCard
Tarjeta financiera asociada a los servicios de Dropi.
Baneo
Restricción aplicada a una cuenta por motivos de seguridad o incumplimiento de políticas.
Bloqueo IP
Restricción aplicada a una dirección IP por intentos fallidos de acceso o comportamientos sospechosos.
Token
Credencial utilizada para autenticar integraciones entre plataformas.
Wallet
Billetera virtual utilizada para almacenar saldo dentro de la plataforma.
RESPONSABLES
GUIA DETALLADA
5.1 DIRECCIONAMIENTO DE CASOS (INTERCOM)
Permite clasificar correctamente las solicitudes para que lleguen al área responsable evitando reprocesos.
Tabla de direccionamiento de áreas y responsables.
Procedimiento
Identificar la solicitud.
Validar el área correspondiente.
Transferir el caso.
Registrar observaciones.
Confirmar recepción.
Consideraciones
No transferir casos sin validar.
Utilizar siempre la matriz oficial.
5.2 CASOS DE EMERGENCIA
Los siguientes casos deben remitirse directamente al canal oficial de WhatsApp.
Casos incluidos
Congelación de tarjeta.
Recuperación de cartera.
Descuentos por SIM Card.
Wallets dobles.
Saldos negativos.
LLC.
Restricción de retiros.
Retiros rechazados.
Canal Oficial
WhatsApp: +57 322 6035926
5.3 ESCALAMIENTO A DESARROLLO
Proceso utilizado cuando una incidencia supera las capacidades de Soporte Funcional.
Portal
https://dropi-it.atlassian.net/servicedesk/customer/portals
Información Obligatoria
Correo del usuario.
País.
ID Orden.
ID Producto.
Evidencias.
Videos.
Descripción detallada.
Consideraciones
Nunca enviar correos en imágenes.
Toda la información debe quedar escrita.
5.4 REGLA DE ORO PARA ESCALAR A JIRA
Escalar inmediatamente
Error 500.
Fallas masivas.
Caídas de sistema.
Errores API persistentes.
No escalar
Configuraciones incorrectas.
Problemas de saldo.
Tokens sin validar.
Errores de usuario.
5.5 GESTIÓN DE ROLES
Condición
El usuario debe tener:
0 órdenes.
Cuenta nueva.
Restricción
No se permite cuando existe historial de órdenes.
5.6 CAMBIO DE CORREO
Requisitos
Cédula.
Código Dropi.
Video de validación.
Consideraciones
Validar identidad antes de cualquier modificación.
5.7 GESTIÓN DE BANEOS
Desbanear
Inactividad.
Más de 3 meses sin acceso.
No Desbanear
Fraude.
Amenazas.  q
Robo.
Bloqueos realizados por marca blanca.
Casos generados por lucho.ceo@dropi.co
5.8 BLOQUEO DE IP
Procede desbloqueo
Múltiples intentos fallidos.
No procede
Ataques dirigidos.
Actividad sospechosa.
5.9 MATRIZ DE ÁREAS
Para el resto de las solicitudes, utilizar la siguiente tabla de visualización de Intercom:
Recomendaciones
Análisis antes de la acción: Siempre verifica el historial de mensajes del usuario antes de realizar un cambio de rol o desbaneo.
Documentación: Deja un comentario interno en cada caso donde realices una acción administrativa (por qué se desbaneó o por qué se cambió un correo).
Comunicación Interdepartamental: Mantén una relación fluida con los desarrolladores para entender los tiempos de respuesta ante errores críticos.
5.10 SOLICITUD DE EXTRACTOS DROPICARD
Requisitos
ID Tarjeta.
Mes solicitado.
Consideraciones
Los extractos se generan desde la segunda semana del mes siguiente.
5.11 RECARGA NO VISUALIZADA EN DROPICARD
Asunto: RECARGA NO VISUALIZADA EN LA DROPICARD
“Hola Noe, espero que estés bien! Por favor tu apoyo con el regreso de $[Monto] a la wallet debido a que se recargó al ID: [ID Tarjeta] : ID transacción #[Número de Transacción] pero no ingresó a la tarjeta. Usuario: [Nombre/Email].”
Procedimiento
Solicitar historial cartera.
Validar transacción.
Escalar a Noelia.
Realizar seguimiento.
Se ve en “Historial de Cartera” del usuario que se cargaron $100.000 a la DropiCard el 29/01/2026
Pero en las entradas de la DropiCard, ese mismo dia no se evidencia ningunos $100.000 ingresando
5.12 TRIÁNGULO DEL SOPORTE (SHOPIFY)
Antes de escalar a TI, el 80% de los errores se solucionan con estos tres pasos:
Refrescar Tokens: Eliminar token en Shopify y Dropi $\rightarrow$ Crear nuevo en Dropi $\rightarrow$ Integrar en Shopify.
Importar como Existente: Re-vincular el producto de Shopify con el de Dropi para asegurar que las variables coinciden.
Pedido de Prueba: Siempre pedir al usuario que genere una orden nueva manual tras hacer un cambio.
5.13 ERRORES COMUNES SHOPIFY
5.14 CUÁNDO ESCALAR A JIRA
Aquí podrás ver las solicitudes y el estado en el que se encuentra
Escalar
Error al instalar Dropify: No deja ni empezar la integración. (Enviar URL de la tienda y usuario).
Error de API / Error Desconocido: Si tras resetear tokens el error persiste en más de 5 usuarios.
Falla de Servidor: Intermitencia general de la plataforma.
5.15 HERRAMIENTAS EXTERNAS
Si el error es visual o de la página de aterrizaje (Landing Page), el problema suele ser de Releasit, no de Dropi:
Producto Agotado: Guía de Releasit
Error en la Landing: Remitir directamente al soporte de Releasit o Shopify.
Casos
Landing Page.
Producto agotado.
Releasit.
Shopify.
Consejo:
"Si el error dice 'Sincronización', lo primero que debes mirar es si el producto existe en Dropi y si tiene stock. Si el producto está archivado o desaprobado por el proveedor, no hay nada que TI pueda hacer; el usuario debe hablar con el proveedor."
5.16 PLANTILLAS OPERATIVAS
Incluye:
SIM Card.
Chatea Pro.
Error 500.
Datos personales.
Facturación México.
Error visual reembolsos.
Cambio de comunidad.
Solución de caché.
Mensaje bienvenida.
Mensaje transferencia.
Comunicado DropiCard.
Error 2FA.
Mensaje escalado.
Interrapidísimo.
DropiPay.
Reembolsos.
PLANTILLAS
Sim card
Para adquirir una sim card por favor te debes comunicar por medio de la siguiente linea SIM:+59175037086
Chatea pro
Espero hoy estés teniendo un buen día, te comparto la línea de chatea pro +57 322 6460153 Por ese medio te brindan toda la información que necesites. ¡Que tengas un buen día!
Error 500
Hola,
Como el Error 500 es un inconveniente interno del servidor que afecta la búsqueda de productos y la edición de órdenes, esto confirma que el fallo en tu perfil requiere la intervención directa del equipo de Desarrollo.
He actualizado tu caso informando que los pasos básicos no dieron resultado para que le den prioridad alta. Por el momento, el equipo técnico sigue trabajando en la raíz del problema para restablecer el servicio lo antes posible.
Te notificaré de inmediato en cuanto tengamos una confirmación de que el sistema se ha estabilizado. Agradezco mucho tu paciencia.
Datos personales
Para poder guardar tus datos personales de forma correcta es necesario que tengas en cuenta lo siguiente:
Desde el área de tecnología nos indican que debes validar el peso de la imagen del DNI antes de subirla. Por favor asegúrate de que el archivo no sea muy pesado (idealmente menos de 2 MB) o comprímelo si es necesario.
Además, debes cambiar el nombre del archivo por uno que tenga menos caracteres. Ejemplo:
Si después de hacer estos ajustes aún no te permite guardar los datos, por favor háznoslo saber para escalarlo nuevamente al área técnica. 😊
Adicionalmente debes tener en cuenta que para guardar el número de documento debes tener presente que:
Para el INE, es necesario colocar el número de 13 cifras que aparece en el reverso justo después del primer <<.
Para el Pasaporte y NIT, es necesario un número de 10 cifras.
​
Para una CC, son 13 cifras.
DATOS FACTURACION MEXICO
Según lo validado, tus datos se guardaron correctamente.
Si al finalizar ves mensajes como:
“Asegúrate de ingresar tus datos tal como aparecen en tu documento de identidad. Recuerda choque, una vez guardes, no podrás hacer cambios durante los próximos 6 meses.”
“Asegúrate de completar la información de facturación electrónica; de lo contrario, la factura se generará utilizando tus datos personales.”
Estos son mensajes informativos por defecto del sistema, por lo que puedes hacer caso omiso y continuar con el registro de tu información bancaria sin inconvenientes.
ERROR VISUAL REEMBOLSOS
Hemos detectado un error visual en la plataforma relacionado con la visualización de los reembolsos. Actualmente, estos pueden aparecer reflejados en color rojo y con signo negativo (como si fueran un cobro), pero te confirmamos que el monto se abona correctamente al saldo de tu cuenta.
Para tu total tranquilidad y validación, te sugerimos lo siguiente:
Verificación de movimientos: Revisa si el saldo total de tu tarjeta aumentó tras la fecha del reembolso, a pesar de cómo se visualiza el registro.
Extractos mensuales: Si deseas una confirmación oficial, podrás descargar tu extracto bancario. En este documento legal aparecerán todos los movimientos reales del mes y podrás verificar que el dinero ingresó efectivamente a tu cuenta.
Lamentamos la confusión que este error visual pueda causarte y estamos trabajando para corregir la forma en que se muestran estos registros.
¡Gracias por tu paciencia!
Comunidades
¡Nuevo proceso de cambio de comunidad disponible! Moverte de comunidad ahora es más fácil. Hemos diseñado una herramienta para que tengas el control total de tu solicitud. Sigue este paso a paso: 1.Ingresa al link: Accede a nuestra nueva herramienta oficial. https://script.google.com/a/macros/dropi.co/s/AKfycbywbfC2qvHoXEZNrYoyjI9JlZlN1fxL4Ne_mUSpeSsUxitOkM4sypu1okNN1pvFhGe1bA/exec
2. Completa tus datos: Asegúrate de realizar la solicitud usando el correo vinculado a tu usuario en Dropi. ¡Es vital para que el cambio se refleje correctamente!
3. Envía tu solicitud: Un solo clic y el proceso inicia.
4. Validación Dropi: 🔍 Una vez recibida, nuestro equipo revisará tu solicitud para validar que todo esté en orden y ejecutará el movimiento de forma interna.
5. Confirmación final: ¡Listo! Te enviaremos un correo electrónico confirmando que el cambio se ha realizado con éxito. Importante:
Las solicitudes por correo ya no serán procesadas, solo las tramitadas por medio de nuestra nueva herramienta.
Las solicitudes realizadas previas al corte del 26 de Marzo 2026 se gestionaran por medio del protocolo anterior.
SIM
Hola, esperamos que te encuentres muy bien. Queremos informarte que en este momento no tenemos SIM card disponible. Estamos trabajando para poder ofrecerlas nuevamente lo antes posible y así brindarte el servicio que mereces.
Agradecemos mucho tu paciencia y comprensión
Solucion
¡Hola! Me informan de desarrollo que el error ya quedó arreglado.
Para que el sistema te funcione bien ahora, por favor haz clic en tu perfil (arriba a la derecha) y selecciona 'Forzar eliminación caché'. Después de esto, intenta ingresar o realizar tu gestión de nuevo.
Como el problema ya se resolvió, cerraré este chat por el momento. ¡Quedamos atentos a cualquier otra duda en el futuro!
Mensaje de bienvenida:
Hola, espero que te encuentres muy bien el día de hoy.
Mi nombre es Camilo, asesor de Servicio al Cliente de Dropi, y con gusto estaré acompañándote y brindándote el apoyo que necesites.
Mensaje de transferencia:
Tu caso será remitido al área encargada para su debida gestión. Ten en cuenta que la respuesta se verá reflejada por este mismo medio, y adicionalmente recibirás una notificación en tu correo electrónico para que puedas estar atento(a).
Por favor, reaccionar a este mensaje para confirmar que la información fue recibida y entendida.
Comunicado Importante: Actualización de DropiCard
Estimado cliente,
Nos ponemos en contacto contigo para informarte que, debido a un inconveniente técnico interno en nuestra plataforma, hemos procedido a la cancelación de tu tarjeta actual como medida de seguridad y solución definitiva.
¿Qué debes hacer ahora? Para continuar disfrutando de nuestros servicios, es necesario que realices la solicitud de una nueva tarjeta desde la aplicación.
Sobre tu saldo: Queremos darte total tranquilidad respecto a tus fondos. El dinero que tenías en la tarjeta cancelada será retornado a tu cuenta de forma automática en el transcurso de esta semana.
Lamentamos los inconvenientes que esto pueda causarte y agradecemos tu comprensión mientras optimizamos nuestros procesos para brindarte un mejor servicio.
Atentamente,
Equipo de Soporte
2FA
Solución al error de código 2FA en Dropi
Si al intentar ingresar el código de verificación (2FA) la plataforma te indica que "el código no coincide", por favor sigue estos pasos para restablecer la conexión y sincronizar correctamente tu cuenta:
Elimina el registro actual: En tu aplicación de Authenticator, busca el código de Dropi y desliza hacia la izquierda para eliminarlo.
Cierra la sesión: Asegúrate de cerrar la pestaña o la ventana web de Dropi en tu dispositivo.
Reinicia el proceso: Ingresa nuevamente a la web de Dropi y solicita vincular el Authenticator desde cero para generar un nuevo código QR.
Escanea y vincula: Agrega el nuevo registro en tu app y verifica que el código ahora sea aceptado.
Nota importante: Asegúrate de que la hora de tu celular esté configurada en modo "Automático", ya que si el reloj de tu dispositivo está desfasado, los códigos no coincidirán aunque el proceso se haga correctamente.
Equipo Dropi
MENSAJE ESCALADO
Muchas gracias por contactarnos y por reportar el inconveniente presentado en el sistema. Valoramos mucho su apoyo, ya que nos ayuda a mantener el control y la eficiencia de nuestra herramienta.
Le informo que su caso ya ha sido escalado al área técnica correspondiente para su revisión detallada. En este momento, quedo a la espera de noticias por parte del equipo de desarrollo para brindarle una solución lo antes posible.
Agradecemos su paciencia mientras trabajamos para que pueda continuar con el registro de sus movimientos económicos con normalidad.
Actualización importante sobre tus envíos
Hola, queremos informarte que hemos recibido una actualización por parte de Interrapidisimo. Los inconvenientes presentados con la plataforma quedarán totalmente solventados al finalizar esta semana.
Si tienes una guía que presenta problemas, por favor repórtala de inmediato a nuestra línea de gestión para proceder con el debido proceso:
📲 WhatsApp: +57 322 646 6432
Agradecemos tu paciencia mientras normalizamos la operación.
DROPIPAY
Por favor, te invitamos a comunicarte con ellos a través del siguiente enlace:
🔗 https://wa.me/573336485804
De esta manera podrán revisar tu caso a detalle y brindarte una solución lo antes posible.
Si tienes alguna otra duda relacionada con Dropi, con gusto estamos aquí para ayudarte.
Reembolso
Buen dia, comprendo la situación; este tipo de desfases entre la tarjeta y el comercio suelen ocurrir por procesos de verificación del procesador de pagos.
Te informo que, en estos casos, el comercio tiene un plazo de hasta 8 días hábiles para procesar el reembolso del dinero a tu tarjeta o aplicar el saldo a tu cuenta publicitaria.
Si pasado este tiempo el dinero no se refleja ni el pago se salda en Meta, por favor escríbenos nuevamente para escalar el caso. Por ahora, procederé a cerrar este chat, ya que debemos esperar a que se cumpla ese periodo de tiempo reglamentario.
¡Quedo atento en una próxima ocasión!
CHATEA
Espero hoy estés teniendo un buen día, te comparto la línea de chatea pro +57 322 6460153 Por ese medio te brindan toda la información que necesites. ¡Que tengas un buen día!
ANEXOS
6.1 Directorio de Áreas
https://docs.google.com/spreadsheets/d/1Xe3Z3sXdmWVRDfExhZvijVEOS89-Mvz4/edit?gid=870848599#gid=870848599
6.2 Portal Jira
https://dropi-it.atlassian.net/servicedesk/customer/portals
6.3 Cambio de Comunidad
https://script.google.com/a/macros/dropi.co/s/AKfycbywbfC2qvHoXEZNrYoyjI9JlZlN1fxL4Ne_mUSpeSsUxitOkM4sypu1okNN1pvFhGe1bA/exec
6.4 Contacto DropiPay
https://wa.me/573336485804
REGISTROS
Responsable | Función
Soporte Funcional | Atención inicial y validación
Equipo Desarrollo | Corrección de incidencias técnicas
Jhonatan Díaz | Gestión de Jira
Juan Caicedo | Gestión de Jira
Mono Soporte | Gestión DropiCard
Noelia | Conciliaciones y devoluciones DropiCard
Área | Gestión
Comercial | Anulaciones
Garantías | Reclamos
Logística | Guías y entregas
Onboarding | SAC Tier 1
Tipo de Error | ¿Qué significa? | Solución Rápida
Token Invalid / En uso | La "llave" de conexión venció o está duplicada. | Reset total de Tokens en ambas plataformas.
Variable / Undefined Property | El producto en Shopify no es igual al de Dropi. | Importar como existente. Las variantes (color/talla) deben ser idénticas. Desinstalar e instalar si el producto esta publico
Error Indeterminado | Error en la creación del producto por parte del proveedor. | El proveedor debe corregir las variables en Dropi.
Monto a ganar menor o igual | El Dropshipper configuró el precio muy bajo. | Indicar que debe subir el precio de venta en Shopify.
No posee dinero en Wallet | Orden "Sin Recaudo" que consume saldo. | El usuario debe recargar su Wallet o revisar si es de una Comunidad.
Transportadora no habilitada | La transportadora (ej. Willog) no está activa. | El Dropshipper debe pedir al Proveedor que la habilite.
Registro | Responsable
Casos Intercom | Soporte Funcional
Casos Jira | Desarrollo
Gestión de Roles | Soporte Funcional
Gestión de Correos | Soporte Funcional
Gestión de Baneos | Soporte Funcional
Gestión DropiCard | Mono Soporte
Incidencias Shopify | Soporte Funcional
Escalamientos Técnicos | Desarrollo
