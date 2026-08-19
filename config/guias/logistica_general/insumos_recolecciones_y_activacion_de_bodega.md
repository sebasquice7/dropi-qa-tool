# Insumos, recolecciones y activación de bodega

OBJETIVO:
Garantizar la gestión operativa, tramitación técnica y soporte a las solicitudes de insumos, cambios o novedades en recolecciones y activaciones de bodega solicitadas por los usuarios dentro de la plataforma Dropi. El propósito central de esta función es brindar atención oportuna a los requerimientos logísticos complementarios de los clientes (proveedores y dropshippers), asegurando la correcta recolección de paquetes, la habilitación operativa de bodegas y el suministro de insumos necesarios para la operación.
ALCANCE:
La cobertura operativa abarca la recepción y trámite de solicitudes a nivel nacional en Colombia sobre activación de bodegas, ajustes en recolecciones, requerimientos de insumos y cambios de datos operativos a través de Intercom, WhatsApp y aplicativos administrativos de Dropi. Se limita a la gestión digital y administrativa, excluyendo la intervención física en bodegas y el transporte terrestre de paquetes o insumos.
DEFINICIONES:
Intercom: Sistema de mensajería interactiva utilizado para la atención de solicitudes de soporte, distribución de bandejas de entrada y comunicación con los usuarios.
Activación de Bodega: Proceso administrativo mediante el cual se habilita o reactiva una bodega dentro de la plataforma para permitir la gestión de inventario y despacho de mercancía.
Recolección: Solicitud operativa para que la empresa transportadora programe la recogida de paquetes en el punto o bodega indicado por el usuario.
Insumos: Materiales operativos y de empaque requeridos por los usuarios o bodegas para la preparación y despacho de los pedidos.
Gali: Bot automatizado dentro de Intercom encargado del flujo y enrutamiento inicial de conversaciones hacia las distintas bandejas.
RESPONSABLES:
Auxiliar de CAS: Rol responsable de brindar soporte en las bandejas de activaciones, recolecciones e insumos, solicitar la información requerida al usuario y tramitar los cambios en el sistema.
Líder de Área / Helen: Rol supervisor encargada de autorizar la prestación de apoyo en estas bandejas secundarias y coordinar la redistribución de cargas de trabajo.
Personal de Apoyo (Dana): Personal en proceso de formación y recepción de estos flujos operativos para asumir la atención directa de activaciones y recolecciones.
Proveedores y Dropshippers: Usuarios de Dropi que solicitan insumos, reactivación de bodegas o cambios en las rutas de recolección de sus pedidos.
GUÍA DETALLADA (PASO A PASO):
ACTIVIDAD A: Gestión de solicitudes de activación de bodega
Paso A.1: Recepción de la solicitud en Intercom El auxiliar ingresa a su bandeja asignada en Intercom y selecciona los tickets clasificados bajo la categoría de activaciones de bodega.
Paso A.2: Lectura y validación del requerimiento Se analiza el mensaje enviado por el usuario para identificar la bodega específica que requiere ser habilitada dentro de la plataforma.
Paso A.3: Solicitud de información complementaria al usuario Si la solicitud carece de datos indispensables, el auxiliar reacciona a la interacción solicitando nuevamente la información necesaria para el proceso de activación.
Paso A.4: Ejecución del proceso inherente a la activación Una vez recibida la información completa, el auxiliar ejecuta el procedimiento operativo correspondiente dentro del sistema para formalizar la activación de la bodega.
Paso A.5: Confirmación y cierre de la interacción Se envía el mensaje de respuesta al usuario confirmando la activación de la bodega y se procede al cierre del ticket en Intercom.
ACTIVIDAD B: Tramitación de novedades y cambios en recolecciones
Paso B.1: Identificación de tickets en la bandeja de recolecciones El auxiliar consulta la bandeja de recolecciones en Intercom para revisar los requerimientos ingresados por los usuarios.
Paso B.2: Filtrado de requerimientos mal asignados Se realiza la lectura de las conversaciones para verificar que correspondan a recolecciones y no a solicitudes de órdenes sin despacho o anulaciones enviadas por error por el bot Gali.
Paso B.3: Solicitud de cambio de recolección Se toman los datos del usuario y del nuevo punto o ajuste solicitado para tramitar la modificación de la recolección ante la transportadora o el sistema.
Paso B.4: Respuesta y notificación al usuario El auxiliar responde al cliente informando la gestión efectuada sobre la recolección y finaliza la atención en la plataforma.
ACTIVIDAD C: Atención de requerimientos de insumos
Paso C.1: Recepción del requerimiento de insumos El auxiliar selecciona de la bandeja los tickets donde el usuario o bodega solicita el suministro de materiales de empaque u operativos.
Paso C.2: Validación del tipo y cantidad de insumo solicitado Se revisa el detalle de los materiales requeridos y la dirección del destinatario registrada en la interacción.
Paso C.3: Tramitación de la solicitud de insumos El auxiliar procesa la orden de solicitud de insumos mediante el canal o sistema correspondiente para su despacho.
Paso C.4: Confirmación al usuario Se notifica al usuario en Intercom que la solicitud de insumos ha sido radicada para su posterior entrega.
ACTIVIDAD D: Empalme y transferencia de procesos al personal designado
Paso D.1: Preparación del material y casos de transferencia El auxiliar reúne los criterios y metodologías de gestión aplicados a las bandejas de activaciones, recolecciones e insumos.
Paso D.2: Entrega operativa del proceso Se transmiten las pautas de atención a Dana para que asuma la gestión directa de estas solicitudes en la plataforma.
Paso D.3: Reenfoque operativo del rol Una vez transferida la carga operativa, el auxiliar retorna a la atención exclusiva de los procesos inherentes al CAS y actualización de estatus.
ANEXOS:
En la bandeja de recolecciones se gestionan todas las novedades relacionadas con el retiro de mercancía, las cuales incluyen los siguientes escenarios: cuando la transportadora no pasa a recoger los pedidos, cuando la transportadora rechaza los paquetes debido a su tamaño o sobredimensión, y cuando la plataforma Dropi arroja un error o no permite programar una nueva recolección.
Lo primero que se solicita es el id de recolección, el id de bodega y con que transportadora presenta la novedad
Con la información anterior se valida en el panel de recolecciones en dropi se verdaderamente pertenece a una novedad
Si presenta una novedad de recolección se busca la bodega en dropi en el panel de bodegas
Y con la dirección y el id de la bodega se escala a logiapp https://logiapp.dropi.co/consulta
Se le manda el siguiente mensaje, Te confirmo que ya transferimos tu solicitud al equipo de la transportadora, quienes se encargarán de la gestión a partir de ahora. Estaremos monitoreando cualquier novedad para informarte. ( EL SE ACOMODA DEPENDIENDO DE LA NOVEDAD QUE PRESENTE NO SIEMPRE SE MANDA EL MISMO) y se coloca  la nota a espera de respuesta junto al radicado para hacerle el seguimiento
Se Espera que Crisly de la respuesta si se demora más de dos hora se le recomiendo por wpp
Luego de obtener la respuesta se le responde al usuario y se le deja el siguiente mensaje ¡Ha sido un gusto poder ayudarte!
Si tienes otra consulta o hay algo más en lo que te pueda colaborar, por favor indícamelo aquí abajo y con gusto lo validamos.
Bandeja de Activación de Transportadora: En este espacio se gestiona exclusivamente todo lo relacionado con la activación de Inter Rapidísimo. Su objetivo operativo es habilitar a los proveedores en el sistema para que puedan generar guías de envío y solicitar recolecciones de manera correcta con esta transportadora y también se gestiona los cambios o modificaciones que hagan los proveedores a la bodega ya activada con dicha trasnportadora
Se les anda el mensaje, el puede variar depende de como entre el usuario
Lo que nos reporta es debido a que la bodega no cuenta con sucursal ID para esa transportadora.
Por favor confírmanos los datos de la siguiente manera en este mismo formato y en ese orden:
👉 Nombre Proveedor:
👉 Nombre bodega:
👉 Teléfono:
👉 Dirección:
👉 Ciudad:
👉 Departamento:
👉 ID bodega 🚚:
👉 Barrio:
👉 Encargado Bodega:
(si es unidad residencial: número de casa si aplica, torre y apartamento; si es edificio, también el número de apartamento; si es centro comercial, el número de local, bodega u oficina.)
Ellos mandan la información y se valida si la dirección de la bodega está bien organizada en caso de que no lo esté como en la mayoría de los casos se le manda la siguiente plantilla junto con la foto
Una vez nos confirme se escala a logiapp
Por último se les manda el siguiente mensaje
Gracias por la confirmación. Te informo que ya hemos solicitado la activación con Inter Rapidísimo. El cambio se verá reflejado en la plataforma en un plazo de 3 a 5 días hábiles. Por favor, evita realizar modificaciones en la bodega mientras el proceso esté en curso.
Bandeja de Insumos: En esta bandeja se reciben las solicitudes de los proveedores que requieren materiales para la preparación y despacho de su mercancía. Ante este requerimiento, se procede a enviarles siempre un mensaje predeterminado, el cual detalla los únicos insumos que Dropi tiene disponibles en este momento.
Te informamos que actualmente no contamos con guías ni porta guías; solo disponemos
de bolsas de Coordinadora, TCC, Domina y 99 Minutos. Quedo atento a la cantidad
de insumos que requiere y de qué transportadora los necesarios.
Luego de que los usuarios nos confirme lo que desean pedir se escala a logiapp
Y se les envía el siguiente mensaje a los usuarios
REGISTROS:
Anteriormente, este registro se llevaba a cabo mediante el archivo de Excel; sin embargo, para mi Danna Trujillo, este método no resultaba práctico ni eficiente para la gestion https://docs.google.com/spreadsheets/d/1YE8a7EU8cY43maE0dM_8nOgew3FGQryFspQ8IHr_FlI/edit?gid=55379163#gid=55379163
Ahora gestiono el registro directamente en la conversación de Intercom. Una vez que los usuarios realizan sus consultas, reviso el historial de interacciones previas; este método resulta mucho más rápido y práctico para brindar una respuesta oportuna.
ejemplo :
Si el usuario  crea otro ticket para preguntar yo miro en el historial de conversaciones y busco con el radicado asi le podre dar una respuesta mas rapida
