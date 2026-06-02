# Diccionario De Datos Real

Estado: pendiente de recepcion de datos operativos reales.

Este documento define el contrato minimo para convertir datos historicos del cliente en un dataset MERO trazable y auditable.

## Sensores

| Campo original | Unidad | Frecuencia | Fuente | Regla de calidad | Campo MERO |
| --- | --- | --- | --- | --- | --- |
| Pendiente cliente | Celsius | Pendiente | Historiador/SCADA/PLC | Valor numerico; no inventar faltantes; revisar rangos por clase de equipo | `sensor_observations.temperature_c` |
| Pendiente cliente | mm/s | Pendiente | Historiador/SCADA/PLC | Valor numerico >= 0; validar outliers con mantenimiento | `sensor_observations.vibration_mm_s` |
| Pendiente cliente | bar | Pendiente | Historiador/SCADA/PLC | Valor numerico; convertir psi/kPa si aplica | `sensor_observations.pressure_bar` |
| Pendiente cliente | rpm | Pendiente | Historiador/SCADA/PLC | Valor numerico >= 0; validar maximo tecnico por equipo | `sensor_observations.rpm` |
| Pendiente cliente | % | Pendiente | Historiador/SCADA/PLC | Rango 0 a 100; marcar fuera de rango | `sensor_observations.load_pct` |
| Pendiente cliente | horas | Pendiente | CMMS/PLC | No decreciente por equipo salvo cambio de contador documentado | `sensor_observations.operating_hours` |
| Pendiente cliente | categoria | Pendiente | Sistema sensor | Normalizar a `good`, `degraded`, `unknown` | `sensor_observations.sensor_quality` |

## Mantenimiento Y Fallas

| Campo original | Unidad | Frecuencia | Fuente | Regla de calidad | Campo MERO |
| --- | --- | --- | --- | --- | --- |
| Pendiente cliente | timestamp | Evento | CMMS/bitacora | Fecha ISO; zona horaria declarada | `maintenance_logs.reported_at` |
| Pendiente cliente | categoria | Evento | CMMS/operador | Normalizar sin sobrescribir texto original | `maintenance_logs.operator_state` |
| Pendiente cliente | codigo | Evento | CMMS/catalogo | Mapear a catalogo ISO 14224 cuando exista | `maintenance_logs.failure_code` |
| Pendiente cliente | texto | Evento | CMMS/operador | No usar como unica etiqueta del modelo sin revision humana | `maintenance_logs.free_text_observation` |
| Pendiente cliente | timestamp | Evento | CMMS | Fecha de intervencion confirmada | Dataset calibracion: `intervention_at` |
| Pendiente cliente | timestamp | Evento | CMMS | Fecha de reparacion confirmada | Dataset calibracion: `repair_completed_at` |
| Pendiente cliente | timestamp | Evento | CMMS/operacion | Fecha de retorno a operacion | Dataset calibracion: `returned_to_operation_at` |

## Activos ISO 14224

| Campo original | Regla | Campo MERO |
| --- | --- | --- |
| Planta cliente | Obligatorio; codigo estable | `plants.plant_code` |
| Linea cliente | Obligatorio; pertenece a planta | `production_lines.line_code` |
| Celula cliente | Obligatorio; pertenece a linea | `cells.cell_code` |
| Equipo cliente | Obligatorio; pertenece a celula | `equipment.equipment_code` |
| Clase equipo | Obligatorio; normalizar con taxonomia acordada | `equipment.equipment_class` |
| Codigo interno cliente | Mantener como referencia cruzada | Campo de staging: `client_equipment_code` |

## Reglas De No Invencion

- Los faltantes se marcan como nulos y se imputan solo dentro del pipeline de entrenamiento.
- Las etiquetas `low`, `medium`, `high` requieren revision de personal operativo.
- Los outliers no se eliminan automaticamente si pueden representar falla real.
- Toda conversion de unidades debe quedar registrada en el log de preparacion del dataset.
