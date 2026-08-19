# Modelo_Guia_detallada_Shopify_Gestion_Integraciones

OBJETIVO
Establecer los lineamientos para la identificación, validación, gestión y escalamiento de incidencias relacionadas con la integración entre Shopify y Dropi, garantizando una atención uniforme, eficiente y alineada con los procedimientos definidos por el área de Integraciones
ALCANCE
Aplica para todos los agentes encargados de la atención de casos relacionados con
Integraciones Shopify.
Incluye la gestión de:
Problemas de sincronización de token.
Errores de configuración general.
Tokens en uso.
Problemas de importación de productos.
Errores de creación de órdenes.
Errores de ciudades y departamentos.
Problemas de autenticación.
Validación de inventario.
Problemas de stock.
Validación de sincronización entre Shopify y Dropi.
DEFINICIONES
Shopify
Plataforma de comercio electrónico que permite la creación y administración de tiendas virtuales, integrándose con Dropi para la gestión automatizada de productos y pedidos.
Token
Código de autenticación utilizado para establecer comunicación segura entre Shopify y Dropi. Permite la sincronización de productos, inventario y órdenes entre ambas plataformas.
Sincronización
Proceso mediante el cual la información registrada en Shopify y Dropi se actualiza automáticamente para mantener consistencia en productos, inventarios y pedidos.
Inventario
Cantidad de unidades disponibles de un producto para su comercialización dentro de la plataforma.
Orden
Registro generado cuando un cliente realiza una compra dentro de la tienda Shopify integrada con Dropi.
Producto Importado
Artículo transferido desde Dropi hacia Shopify para ser comercializado dentro de la tienda virtual
RESPONSABLES
GUIA DETALLADA
ERROR DE SINCRONIZACIÓN DE TOKEN
Este error se presenta cuando Shopify no logra validar correctamente el token configurado para la integración con Dropi.
Mensaje de error relacionado con la sincronización o validación del token de integración.
Procedimiento
Solicitar evidencia del error.
Validar el token configurado.
Confirmar que el token corresponda a la tienda correcta.
Solicitar una nueva sincronización.
Validar nuevamente la conexión.
Escalar al equipo de Integraciones cuando persista el error.
Consideraciones
El token debe encontrarse vigente.
La tienda debe estar correctamente vinculada.
La validación debe realizarse antes de cualquier escalamiento.
ERROR GUARDANDO CONFIGURACIÓN GENERAL
Este error ocurre cuando Shopify no permite almacenar correctamente los parámetros configurados para la integración.
Error presentado durante el guardado de la configuración general de la integración.
Procedimiento
Validar los datos registrados.
Confirmar la conexión activa.
Actualizar la configuración.
Intentar guardar nuevamente.
Validar el resultado.
Escalar si el problema persiste.
Consideraciones
La información debe estar completa.
La conexión con Shopify debe encontrarse activa.
ERROR TOKEN EN USO
Este error ocurre cuando el token ya se encuentra asociado a otra integración activa.
Mensaje indicando que el token ya está siendo utilizado en otra integración.
Procedimiento
Validar el token reportado.
Confirmar si se encuentra asociado a otra tienda.
Solicitar desvinculación cuando corresponda.
Registrar nuevamente el token.
Validar la sincronización.
Consideraciones
Un token no puede utilizarse simultáneamente en múltiples configuraciones.
Debe verificarse la asociación previa.
5.4 ERROR INDETERMINADO AL IMPORTAR PRODUCTO NUEVO
Este error impide la importación inicial de un producto desde Dropi hacia Shopify.
Error presentado durante la importación de un producto nuevo.
Procedimiento
Validar el producto seleccionado.
Verificar disponibilidad.
Confirmar la sincronización.
Reintentar la importación.
Validar el resultado.
Escalar si el problema continúa.
Consideraciones
Debe verificarse la disponibilidad del producto.
El catálogo debe encontrarse actualizado.
5.5 ERROR INDETERMINADO AL IMPORTAR PRODUCTO EXISTENTE
Este error se presenta cuando Shopify no puede actualizar o sincronizar un producto previamente importado.
Error presentado durante la sincronización de un producto existente.
Procedimiento
Validar el ID del producto.
Confirmar que exista en ambas plataformas.
Verificar sincronización.
Reintentar el proceso.
Escalar cuando corresponda.
Consideraciones
Debe existir correspondencia entre los registros.
El producto debe permanecer activo.
5.6 ERROR DE SINCRONIZACIÓN AL CREAR ORDEN
Este error ocurre cuando una venta realizada en Shopify no logra transferirse correctamente hacia Dropi.
Error presentado durante la creación automática de una orden.
Procedimiento
Validar la orden.
Revisar el historial de sincronización.
Confirmar los datos del cliente.
Reintentar la sincronización.
Escalar al área correspondiente.
Consideraciones
La orden debe contener información completa.
Deben validarse los datos de envío.
5.7 ERROR DEPARTAMENTO NO EXISTE
El error se presenta cuando el departamento registrado en Shopify no coincide con los valores reconocidos por Dropi.
Error indicando que el departamento no existe dentro de la configuración permitida.
Procedimiento
Revisar el departamento registrado.
Comparar con los departamentos permitidos.
Corregir la información.
Reintentar la sincronización.
Consideraciones
Los nombres deben coincidir exactamente.
No deben utilizarse abreviaturas no reconocidas.
5.8 ERROR CIUDAD NO EXISTE
Este error ocurre cuando la ciudad registrada no corresponde con los parámetros definidos por el sistema.
Error indicando que la ciudad no se encuentra registrada.
Procedimiento
Validar la ciudad registrada.
Comparar con la base de datos disponible.
Corregir la información.
Reintentar el proceso.
Consideraciones
Debe utilizarse el nombre oficial de la ciudad.
Los errores ortográficos generan fallas de sincronización.
5.9 ERROR TOKEN INVALID
Este error se presenta cuando el token configurado para la integración no es reconocido por Shopify o ha perdido vigencia, impidiendo la comunicación correcta con Dropi.
Mensaje de error indicando que el token registrado no es válido para la integración.
Procedimiento
Solicitar evidencia del error.
Validar el token configurado actualmente.
Confirmar que el token corresponda a la tienda correcta.
Generar un nuevo token cuando aplique.
Actualizar la configuración de integración.
Ejecutar una nueva sincronización.
Validar el resultado.
Consideraciones
Los tokens pueden expirar o ser revocados.
Debe verificarse que el token pertenezca a la misma tienda integrada.
La actualización debe realizarse desde la configuración oficial de Shopify.
5.10 PRODUCTO AGOTADO EN LANDING
Esta situación ocurre cuando un producto aparece sin disponibilidad dentro de la página de ventas o landing page debido a problemas de sincronización de inventario.
Ejemplo de producto visualizado como agotado dentro de la página de ventas.
Procedimiento
Validar el ID del producto.
Revisar el inventario disponible en Dropi.
Verificar el inventario reflejado en Shopify.
Ejecutar una sincronización manual.
Confirmar la actualización del stock.
Validar nuevamente la visualización en la landing.
Consideraciones
El producto puede encontrarse disponible en Dropi pero no actualizado en Shopify.
Las diferencias de inventario pueden generar estados incorrectos.
Debe validarse la sincronización antes de escalar.
5.11 PRODUCTO SIN STOCK EN BODEGAS
Este caso se presenta cuando el inventario físico disponible en las bodegas del proveedor se encuentra agotado.
Validación de inventario agotado en las bodegas asociadas al producto.
Procedimiento
Identificar el producto afectado.
Consultar la disponibilidad en bodega.
Confirmar la cantidad disponible.
Informar el resultado al usuario.
Recomendar productos alternativos cuando sea necesario.
Consideraciones
El inventario depende directamente del proveedor.
La reposición de stock puede variar según el producto.
Debe verificarse la información antes de confirmar disponibilidad.
5.12 PRODUCTO SIN STOCK EN DROPI
Este caso ocurre cuando el producto no dispone de inventario disponible dentro de la plataforma Dropi, impidiendo nuevas ventas o sincronizaciones.
Ejemplo de producto sin disponibilidad dentro del catálogo de Dropi.
Procedimiento
Validar el producto consultado.
Confirmar el inventario disponible en la plataforma.
Revisar la información suministrada por el proveedor.
Informar el resultado al usuario.
Recomendar seguimiento sobre futuras reposiciones.
Consideraciones
El agotamiento puede ser temporal.
La disponibilidad depende de la actualización realizada por el proveedor.
La información debe validarse directamente desde la plataforma.
ANEXOS
Portal Shopify
Plataforma utilizada para la administración de tiendas virtuales e integración con Dropi.
https://www.shopify.com
6.2 Centro de Ayuda Shopify
Documentación oficial para soporte e integraciones.
https://help.shopify.com
REGISTROS
Responsable | Función
Equipo Integraciones | Gestión de incidencias Shopify
Johan Cortez | Escalamientos de Integraciones
Equipo Desarrollo | Incidencias técnicas avanzadas
Registro | Responsable
Casos de Sincronización de Token | Equipo Integraciones
Casos de Configuración General | Equipo Integraciones
Casos de Token en Uso | Equipo Integraciones
Casos de Importación de Productos | Equipo Integraciones
Casos de Sincronización de Órdenes | Equipo Integraciones
Casos de Departamentos y Ciudades | Equipo Integraciones
Casos de Inventario y Stock | Equipo Integraciones
Casos Escalados a Desarrollo | Equipo Desarrollo
Escalamientos Avanzados | Johan Cortes
