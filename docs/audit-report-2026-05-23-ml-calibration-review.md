# Auditoria QA - Reevaluacion De Calibracion ML

Fecha: 2026-05-23  
Responsable: Agente Auditor Principal / QA Architect  
Alcance: revision del dictamen del Agente de Datos y ML sobre aprobacion de piloto predictivo.

## Dictamen

Estado: dictamen ML aceptado por QA.

El modelo actual queda aprobado solo para integracion tecnica y demostracion end-to-end. No queda aprobado para piloto predictivo real.

## Evidencia Revisada

- `docs/data-dictionary-real.md`
- `docs/ml-calibration-report.md`
- `docs/model-validation-report.md`
- `artifacts/models/random_forest_metrics.json`
- `src/ml/train.py`

## Hallazgos

### QA-ML-001: ausencia de dataset operativo real

Estado: bloqueo activo.

El diccionario de datos real mantiene campos `Pendiente cliente`, y el reporte de calibracion declara que el modelo actual usa `data/training_seed.csv`. Por tanto, las metricas actuales no son evidencia de desempeno industrial real.

### QA-ML-002: etiquetas sin validacion operativa

Estado: bloqueo activo.

La regla `low`, `medium`, `high` esta propuesta, pero requiere validacion de mantenimiento. Sin esa revision, el modelo puede aprender etiquetas tecnicamente consistentes pero operacionalmente incorrectas.

### QA-ML-003: metricas actuales no validan piloto

Estado: bloqueo activo.

`random_forest_metrics.json` reporta `split_strategy: random` y `model_version: demo_seed_20260523`. Aunque el entrenamiento es reproducible y supera el baseline de demostracion, no existe validacion temporal sobre historico real.

## Confirmaciones Tecnicas

- `src/ml/train.py` soporta split temporal con `--split-strategy temporal --time-column observed_at`.
- El pipeline reporta baseline, matriz de confusion y metricas por clase.
- El bundle serializado contiene columnas, version de modelo y estrategia de split.

## Decision QA

Se acepta el dictamen del Agente de Datos y ML:

No aprobado para piloto.

Condicion para desbloqueo:

- Dataset operativo real trazable.
- Mapeo ISO 14224 validado por equipo.
- Etiquetas revisadas y aprobadas por mantenimiento.
- Validacion temporal con foco en falsos negativos de `high`.
- Umbrales de aceptacion cumplidos y documentados.

