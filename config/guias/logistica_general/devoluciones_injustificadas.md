# Devoluciones Injustificadas

OBJETIVO:
Garantizar la recepción, auditoría, validación técnica, radicación y seguimiento continuo de las solicitudes de devoluciones injustificadas reportadas por los usuarios en Colombia a través de la plataforma Intercom, evaluando la procedencia técnica del reclamo frente a los criterios y propuestas de valor de las distintas transportadoras aliadas, con el fin de tramitar las solicitudes de indemnización en los aplicativos internos, gestionar los recursos ante el área de operaciones y brindar una respuesta oportuna al cliente.
ALCANCE:
La cobertura operativa abarca la recepción, auditoría técnica y escalamiento de reclamos por devoluciones injustificadas a nivel nacional en Colombia a través de Intercom, la plataforma central de Dropi, LogiApp, Controller de Inter Rapidísimo y herramientas de Google. Se limita a la validación de plazos reglamentarios y tramitación ante transportadoras aliadas, excluyendo la aprobación o desembolso directo de dinero y la gestión sobre transportadoras sin convenio de indemnización.
DEFINICIONES:
Devolución Injustificada: Retorno de un paquete al remitente original sin que exista una causa comercial válida o un incumplimiento real por parte del destinatario o del comercio.
Falla de Integración (API): Desfase tecnológico entre el software propio y el de la transportadora, ocasionando que las soluciones de novedades cargadas por el usuario no se transmitan antes del cierre logístico, ejecutando retornos erróneos.
Intento de Entrega Normativo: Visita física real efectuada por la transportadora al domicilio del destinatario. El estándar contractual exige un mínimo de 2 intentos válidos antes de proceder a la devolución.
Dropshipper / Emprendedor: Usuario de la plataforma Dropi que realiza los envíos y es quien interpone las quejas o reclamaciones por cobros de fletes.
Intercom: software de gestión de clientes (CRM) que sirve como canal primordial de comunicación para recibir tickets y emitir las respuestas formales a los usuarios.
Plataforma Dropi: Sistema centralizado propio de la empresa donde se realiza la revisión del estado de las guías, fletes y el historial local de novedades.
Controller: Software externo y especializado de la transportadora Inter Rapidísimo empleado para supervisar telemercadeos, coordenadas geográficas, fotografías de paquetes y estados logísticos.
Telemercadeo: Proceso mediante el cual la transportadora realiza una llamada telefónica al cliente final para verificar sus datos cuando se reporta una dirección errada o inexistente.
RESPONSABLES:
Analista de Devoluciones Injustificadas: Responsable de realizar el filtro inicial de tiempos, la auditoría visual y el contraste en portales externos.
Área de Operaciones de Logística: Filtro técnico que dictamina si la reclamación procede antes de enviarla formalmente a la transportadora.
Analista de Indemnizaciones / Financiero: Encargado de la descarga masiva de archivos en Excel para validar contadores en cero y ejecutar reembolsos por fallas de plataforma.
Analistas de Soporte General: Roles de soporte pares que se encargan de cargar o gestionar los tickets dentro de la plataforma de comunicación con el cliente
GUÍA DETALLADA (PASO A PASO):
ACTIVIDAD A: Recepción, auditoría y validación técnica de causales en Dropi y plataformas externas
Paso A.1: Recepción de la solicitud en Intercom. El analista ingresa a la bandeja de entrada de Intercom para recepcionar la solicitud de reclamación e identificar el número de guía reportado por el usuario.
Paso A.2: Validación de plazos reglamentarios para el reporte. Se verifica en la guía que la solicitud haya sido radicada por el usuario dentro de los 30 días posteriores a la devolución para la mayoría de transportadoras, o dentro de los 7 días para Inter Rapidísimo.
Paso A.3: Consulta del estado técnico de la guía en Dropi. El analista busca el código del envío en la plataforma Dropi para confirmar que se encuentra efectivamente en estado de devolución y revisar el historial de novedades registradas.
Paso A.4: Evaluación de la causal por error de integración. Se compara la guía en el portal web externo de la transportadora frente al historial de Dropi para verificar si existió una novedad reportada en origen que no fue reflejada en la plataforma.
Paso A.5: Evaluación de la causal por incumplimiento de intentos de entrega. Se audita la trazabilidad externa para confirmar si la empresa transportadora realizó menos de los dos intentos mínimos de entrega garantizados en la propuesta de valor comercial.
Paso A.6: Evaluación de la causal por incumplimiento en tiempos de transporte. Se calcula la diferencia en días hábiles entre la fecha de entrega a la transportadora y la fecha del primer intento, verificando si excede los rangos según el destino (1 a 3 días en principales, 5 a 7 en intermedias y hasta 15 en trayectos especiales).
Paso A.7: Descarga y filtrado masivo de solicitudes. Cuando el usuario adjunta reportes masivos de hasta 500 guías, el analista descarga el informe desde Dropi y filtra por el contador de novedades e intentos de entrega para descartar de forma automatizada las que no aplican.
ACTIVIDAD B: Gestión y auditoría específica de guías de la transportadora Inter Rapidísimo
Paso B.1: Consulta del flujo en la herramienta Controller. El analista accede a Controller e ingresa el número de guía para auditar el flujo del envío, la gestión en la aplicación y los detalles de los intentos realizados.
Paso B.2: Verificación del registro de telemercadeo. Se revisa si existe constancia de llamada o gestión de telemercadeo hacia el cliente final en Controller, lo cual equivale a un intento de entrega válido aunque no haya visita presencial.
Paso B.3: Auditoría de parámetros en solicitudes para reclamo en oficina. Se valida que la dirección registrada por el usuario contenga la sintaxis correcta, las palabras clave estipuladas y corresponda a una oficina expresamente habilitada en la matriz institucional.
Paso B.4: Verificación del tiempo de permanencia en oficina El analista comprueba que el paquete haya permanecido depositado durante al menos 4 días calendario en la oficina autorizada antes de haber sido devuelto al remitente.
ACTIVIDAD C: Auditoría de novedades y protocolo de respuesta para la transportadora Envía
Paso C.1: Consulta detallada en el portal oficial de Envía. Se ingresa la guía en la plataforma oficial de Envía para consultar el motivo exacto de la novedad registrada en la guía.
Paso C.2: Validación de la sintaxis en la solución del usuario. El analista contrasta la respuesta brindada por el dropshipper frente al manual institucional de novedades de Envía para comprobar que cumpla al pie de la letra con los datos exigidos.
Paso C.3: Control del tiempo de reclamo en oficina para Envía. Se confirma que se haya otorgado únicamente un día hábil de permanencia en la oficina de Envía tras la solución de la novedad para que el cliente recogiera el paquete antes del retorno.
ACTIVIDAD D: Radicación de casos en LogiApp y registro en matriz de seguimiento
Paso D.1: Ingreso de datos y radicación en LogiApp. El analista radica la solicitud en el aplicativo LogiApp detallando la guía y adjuntando las evidencias recopiladas para trasladar el estudio al área de operaciones de logística.
Paso D.2: Tipificación especial por error de plataforma. Si la causa radica en una falla de integración en el contador de novedades de Dropi, el analista clasifica el radicado como indemnización por error de plataforma para trámite interno directo.
Paso D.3: Registro de datos en la matriz de Google Sheets. Se inscriben los datos del radicado en el archivo consolidado de Google Sheets para iniciar el control de términos y el monitoreo de estados.
Paso D.4: Comunicación formal de tiempos de respuesta en Intercom El analista responde al usuario en Intercom informando la apertura de la investigación y comunicando el tiempo de respuesta estimado entre 30 y 45 días hábiles.
ACTIVIDAD E: Monitoreo de respuestas, indemnizaciones y trazabilidad final
Paso E.1: Monitoreo recurrente de la matriz unificada. El analista revisa el archivo de Google Sheets dos o tres veces por semana para verificar si el área de operaciones o la transportadora ha actualizado la gestión del caso.
Paso E.2: Notificación periódica de avances al usuario. Ante cualquier cambio de estado registrado en la matriz o LogiApp, el analista ingresa al ticket correspondiente de Intercom para notificar las novedades al usuario.
Paso E.3: Seguimiento al abono de indemnizaciones aprobadas. Cuando una guía es aprobada para indemnización por la transportadora, el analista modifica su estado en la matriz a en proceso de pago para vigilar el desembolso dentro de un plazo de hasta 45 días hábiles.
Paso E.4: Traslado al área de cartera para liquidación final Una vez confirmado el recaudo o la procedencia del pago por error técnico, se traslada la gestión al equipo financiero interno para que realice el abono formal en la plataforma Dropi.
ANEXOS:
Plantillas de Reclamo en Oficina: Guías textuales para realizar reclamaciones de paquetes dirigidos a oficinas.
Controller (Inter Rapidísimo): Plataforma web externa utilizada para examinar bitácoras de llamadas, mapas, fotos y estados de envíos con Inter Rapidísimo. .
Portal Envía: Plataforma externa utilizada para consultar de manera detallada las novedades de la transportadora Envía.
Aplicativo de Escalamiento: Herramienta interna de Dropi para derivar los casos aprobados a logística o al área de indemnizaciones.
Google Chat: Canal de comunicación oficial utilizado para el envío y recepción de documentos complementarios entre analistas y líderes.
REGISTROS:
Google Drive ("Seguimiento de Devoluciones Injustificadas"): Es una hoja de cálculo compartida en la que el analista transcribe manualmente los datos de las guías aprobadas para monitorear el estado de los pagos, negaciones e indemnizaciones financieras
Intercom: Registro del estado del ticket, justificaciones de rechazo y asignación de tiempos de respuesta directamente en la ficha del cliente.
Aplicativo de Escalamiento: Registro digital en la plataforma interna para almacenar y transferir los casos procedentes al área de Operaciones de Logística
