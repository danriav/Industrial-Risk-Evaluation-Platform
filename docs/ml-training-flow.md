# Flujo de Entrenamiento ML

Este flujo genera el primer modelo predictivo funcional para consumo del backend.

## Dataset inicial

El dataset semilla se genera con:

```sh
python src/ml/prepare_seed_dataset.py --output data/training_seed.csv --rows 240
```

Columnas numericas:

- `temperature_c`
- `vibration_mm_s`
- `pressure_bar`
- `rpm`
- `operating_hours`
- `load_pct`

Columnas categoricas:

- `equipment_class`
- `sensor_quality`

Variable objetivo:

- `failure_label`

El dataset es sintetico, deterministico y no contiene datos sensibles ni lecturas reales de clientes. Sirve como primer artefacto funcional para validar carga del modelo, inferencia y contrato con backend.

## Entrenamiento offline

```sh
python src/ml/train.py \
  --input data/training_seed.csv \
  --target failure_label \
  --output artifacts/models/random_forest.joblib \
  --metrics artifacts/models/random_forest_metrics.json
```

El bundle serializado contiene:

```python
{
    "model": pipeline,
    "target_column": "failure_label",
    "numeric_columns": [...],
    "categorical_columns": [...],
}
```

El backend consume `model`, `numeric_columns` y `categorical_columns` desde `MODEL_PATH`, cuyo valor por defecto es `artifacts/models/random_forest.joblib`.

Artefactos generados:

- `data/training_seed.csv`
- `artifacts/models/random_forest.joblib`
- `artifacts/models/random_forest_metrics.json`

Resultado del primer entrenamiento funcional:

- `accuracy`: 0.9375
- `macro avg f1-score`: 0.9344
- clases cubiertas: `low`, `medium`, `high`

Validacion de contrato del bundle:

- `model`: `imblearn.pipeline.Pipeline`
- `numeric_columns`: `temperature_c`, `vibration_mm_s`, `pressure_bar`, `rpm`, `operating_hours`, `load_pct`
- `categorical_columns`: `equipment_class`, `sensor_quality`

Validacion backend:

```python
POST /api/v1/predictions/risk para PUMP-01 -> risk_label "medium"
```

El payload real de frontend/backend contiene 8 variables: las 6 numericas del modelo y las 2 categoricas. No hay columnas adicionales esperadas por el modelo.

## Umbrales de discrepancia propuestos

No existe aun consenso operativo formal sobre umbrales de maquinaria. Por esa razon no se pobla `discrepancy_thresholds` como dato aprobado.

Propuesta inicial para revision de confiabilidad:

| equipment_class | variable_name | min_value | max_value | max_delta_per_hour | severity |
| --- | --- | ---: | ---: | ---: | --- |
| centrifugal_pump | temperature_c | 5 | 85 | 12 | high |
| centrifugal_pump | vibration_mm_s | 0 | 7.1 | 1.5 | high |
| centrifugal_pump | pressure_bar | 0.5 | 12 | 2.0 | medium |
| compressor | temperature_c | 5 | 92 | 10 | high |
| compressor | vibration_mm_s | 0 | 8.5 | 1.8 | high |
| compressor | pressure_bar | 1 | 14 | 2.5 | high |
| conveyor | temperature_c | 0 | 75 | 10 | medium |
| conveyor | vibration_mm_s | 0 | 6.5 | 1.5 | medium |
| mixer | temperature_c | 0 | 82 | 10 | medium |
| mixer | vibration_mm_s | 0 | 7.2 | 1.6 | medium |

Cuando estos valores sean aprobados por operaciones/confiabilidad, se deben insertar en `discrepancy_thresholds` con `approved_by`, `approved_at` y la justificacion tecnica correspondiente.
