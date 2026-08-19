# Política de Tiempos de Respuesta (SLA) — Servicio al Cliente Dropi LATAM

## Definiciones de tiempos
- **1ª Respuesta (FRT):** saludo inicial que confirma que el caso ya está siendo atendido.
- **Respuesta Intermedia (IRT):** mensajes de estatus proactivos (ej. "seguimos gestionando con la transportadora") mientras se espera a un tercero. Es el **compromiso innegociable** de cada área, incluso cuando la solución final depende de alguien más (transportadora, banco, pasarela de pago).
- **Cierre o Resolución (RRT):** la solución técnica definitiva que reactiva la operación del usuario.

## Horario de atención humana
Lunes a viernes 8:00 a.m. a 5:00 p.m., y sábados/lunes festivos 8:00 a.m. a 12:00 m. **Los tiempos fuera de este horario NO cuentan como demora del asesor** (ej. un mensaje del cliente a las 6pm que se responde a las 8am del día siguiente hábil está DENTRO del SLA, no es una demora).

## Cierre por inactividad del cliente (regla fija, aplica a TODOS los procesos)
Si el **cliente** deja de responder durante **4 horas de tiempo laboral acumulado** después de la última gestión del asesor (mensaje del asesor con información, solución o instrucción clara), el asesor **puede cerrar la conversación válidamente** por abandono/inactividad del cliente — esto NO es una falla del asesor ni debe marcarse como ítem crítico de "cierra sin resolver", siempre que:
1. El asesor haya dado una gestión clara antes del silencio (no cerró sin haber dicho nada útil), y
2. Haya avisado al cliente antes de cerrar (ej. "veo que te has ausentado, cerraremos por ahora").

Las 4 horas se cuentan en **tiempo laboral** (dentro del horario de atención humana definido arriba) — un silencio nocturno o de fin de semana no cuenta para completar esas 4 horas.

Si el asesor cierra la conversación con MENOS de 4 horas de inactividad del cliente, sin que el caso esté resuelto, eso es una posible falla de proceso (cierre prematuro) — refléjalo en el puntaje de "seguimiento_tiempo" o "cierra_sin_resolver" según qué tan injustificado sea, no lo ignores solo porque hubo un aviso de cierre.

## Tiempos por proceso (1ª Respuesta / Respuesta Intermedia / Cierre Final)

**Gali y Triage (Tier 0/1 — diagnóstico inicial):** 10 min / — / 20 min (para derivar a ticket)

**Logística:**
| Proceso | Criticidad | 1ª Respuesta | Resp. Intermedia | Cierre Final |
|---|---|---|---|---|
| Casos Especiales | Crítico | 15 min | Cada 1 hora | 12-24 h |
| Actualización de Guías | Alto | 30 min | Cada 2 horas | 12-24 h |
| Recolecciones | Alto | 30 min | Cada 2 horas | 12-24 h |
| PQRS - CAS | Alto | 30 min | Cada 2 horas | 12-24 h |
| Prueba de Entrega | Medio | 30 min | Cada 2 horas | 12-24 h |
| Guías sin Movimiento | Medio | 30 min | Cada 2 horas | 12-24 h |
| Devolución Injustificada | Medio | 30 min | Cada 2 horas | 12-24 h |

**Comercial:**
| Proceso | Criticidad | 1ª Respuesta | Resp. Intermedia | Cierre Final |
|---|---|---|---|---|
| Anulaciones | Crítico | 5 min | Cada 10 min | 1 h |
| Órdenes sin despachar | Alto | 5 min | Cada 10 min | 1 h |

**Administrativo:**
| Proceso | Criticidad | 1ª Respuesta | Resp. Intermedia | Cierre Final |
|---|---|---|---|---|
| Recargas | Crítico | 15 min | Cada 30 min | 1 h |
| Retiros (Payouts) | Alto | 15 min | Cada 30 min | 1 h |
| Compliance | Alto | 10 min | Cada 15 min | 30 min |
| Facturación (LATAM) | Bajo | 15 min | Cada 4 horas | 2 h |

**Soporte Técnico:**
| Proceso | Criticidad | 1ª Respuesta | Resp. Intermedia | Cierre Final |
|---|---|---|---|---|
| Plataforma (Bugs) | Crítico | 15 min | Cada 1 hora | Sujeto a TI |
| Integraciones / API | Alto | 30 min | Cada 1 hora | 2 h |

**Garantías (Post-venta):** 1ª Respuesta 1 hora / Respuesta Intermedia cada 4 horas / Cierre Final 24-48 horas.

## Nota importante para evaluar SLA y cierres
Si la bandeja/proceso exacto de la conversación no aparece en esta tabla, usa el tiempo del proceso más parecido como referencia aproximada, y sé razonable: el objetivo es detectar demoras reales, no penalizar por segundos de diferencia.
