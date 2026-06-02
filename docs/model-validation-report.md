# Reporte De Validacion Del Modelo

Estado: modelo demo funcional; validacion real pendiente.

## Artefactos Revisados

- `artifacts/models/random_forest.joblib`
- `artifacts/models/random_forest_metrics.json`
- `artifacts/models/random_forest_demo_seed_20260523.joblib`
- `data/training_seed.csv`
- `src/ml/train.py`
- `src/ml/prepare_seed_dataset.py`

## Contrato Backend

El bundle contiene:

- `model`
- `numeric_columns`
- `categorical_columns`
- `target_column`
- `model_version`
- `split_strategy`

Columnas actuales:

- Numericas: `temperature_c`, `vibration_mm_s`, `pressure_bar`, `rpm`, `operating_hours`, `load_pct`
- Categoricas: `equipment_class`, `sensor_quality`

Clases actuales:

- `low`
- `medium`
- `high`

## Validacion Actual

El archivo de metricas se genera de forma reproducible desde:

```sh
python src/ml/train.py --input data/training_seed.csv --target failure_label --output artifacts/models/random_forest.joblib --metrics artifacts/models/random_forest_metrics.json --model-version demo_seed_20260523 --split-strategy random
```

La validacion actual usa datos sinteticos. Sirve para probar integracion tecnica, no desempeno operativo.

## Validacion Temporal Requerida

Cuando exista dataset real con `observed_at`:

```sh
python src/ml/train.py --input data/processed/real_training_dataset.csv --target failure_label --split-strategy temporal --time-column observed_at --model-version real_YYYYMMDD_v1 --output artifacts/models/random_forest.joblib --metrics artifacts/models/random_forest_metrics.json
```

La validacion temporal debe reportar:

- Matriz de confusion.
- Precision, recall y F1 por clase.
- Comparacion contra baseline.
- Analisis especial de falsos negativos `high`.

## Riesgos

- Falsos negativos `high` pueden ocultar fallas criticas.
- Datos sinteticos no representan ruido, sesgo humano ni deriva de sensores reales.
- Sin revision humana, las etiquetas pueden codificar decisiones incorrectas.

## Recomendacion

No aprobado para piloto hasta completar validacion con datos reales y revision de etiquetas por personal operativo.
