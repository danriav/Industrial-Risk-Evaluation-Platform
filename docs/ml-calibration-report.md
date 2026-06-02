# Reporte De Calibracion ML

Estado: bloqueado para piloto.

## Resumen

El modelo disponible en `artifacts/models/random_forest.joblib` es funcional para integracion backend/frontend, pero fue entrenado con `data/training_seed.csv`, un dataset sintetico de demostracion. No debe considerarse calibrado con datos operativos reales.

## Datos Reales Requeridos

Para calibracion real se requieren historicos por equipo con:

- Sensores: temperatura, vibracion, presion, RPM, carga, horas de operacion y calidad del sensor.
- Bitacoras reales de mantenimiento.
- Eventos de falla confirmados.
- Fechas de intervencion, reparacion y retorno a operacion.
- Mapeo activo a Planta, Linea, Celula, Equipo y clase de equipo ISO 14224.

## Regla De Etiquetado Historico Propuesta

Esta regla es propuesta y requiere validacion con mantenimiento:

- `high`: ventana previa a una falla confirmada, paro no planeado, intervencion correctiva critica o condicion operativa que mantenimiento confirme como riesgo alto.
- `medium`: ventana con degradacion observada, alarma recurrente, intervencion preventiva urgente o condicion fuera de rango sin falla confirmada.
- `low`: operacion estable sin falla confirmada ni intervencion correctiva asociada en la ventana de observacion.

La ventana temporal exacta debe acordarse por clase de equipo. Punto de partida sugerido: 24 a 72 horas antes del evento para `high`, y 7 dias para degradacion `medium`.

La aprobacion formal corresponde al Agente Producto / Industrial Reliability
SME, documentado en `docs/product-industrial-reliability-agent.md`, junto con
mantenimiento del cliente.

## Cambios Al Pipeline

`src/ml/train.py` ahora soporta:

- Split aleatorio para pruebas de integracion.
- Split temporal con `--split-strategy temporal --time-column observed_at`.
- Baseline `DummyClassifier(strategy="most_frequent")`.
- Matriz de confusion.
- Precision, recall y F1 por clase.
- Versionado opcional con `--model-version`.

## Calibracion De Umbrales

Los cortes `low`, `medium`, `high` no deben fijarse solo por score del modelo. Deben calibrarse con:

- Costo de falso negativo en `high`.
- Costo operativo de falso positivo.
- Tolerancia de mantenimiento a alertas recurrentes.
- Diferencias por clase de equipo.

Umbral minimo propuesto para considerar piloto:

- Recall de `high` >= 0.85 en validacion temporal.
- F1 de `high` >= 0.70 en validacion temporal.
- Revision y firma de etiquetas por mantenimiento.
- Firma de reglas de etiquetado por el Agente Producto / Industrial Reliability
  SME.
- Dataset real trazable o referencia segura auditada.

## Decision

No aprobado para piloto.

Motivo: no existe aun dataset real validado ni revision de etiquetas por personal operativo.

Bloqueo adicional: no se entrena ni aprueba modelo real sin reglas de
etiquetado firmadas por el Agente Producto / Industrial Reliability SME y por
mantenimiento del cliente.
