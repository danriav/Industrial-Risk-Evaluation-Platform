# Guia de Desarrollo

Esta fase define un contrato de plataforma, no implementa codigo de aplicacion.

Reglas operativas:

- No almacenar credenciales reales en el repositorio.
- Mantener `.env.example` como plantilla sin secretos.
- Mantener los puertos publicados dentro de la lista autorizada por el cliente.
- No mezclar datos de sensores con registros humanos en logs ni vistas de auditoria.
- Publicar metricas del backend en `/metrics` para Prometheus.

## Entrenamiento offline

El pipeline de entrenamiento del Agente de Datos y ML vive en `src/ml/train.py`.

Instalar dependencias de datos:

```sh
pip install -r src/ml/requirements.txt
```

Entrenar un modelo Random Forest serializado:

```sh
python src/ml/prepare_seed_dataset.py --output data/training_seed.csv --rows 240
python src/ml/train.py --input data/training_seed.csv --target failure_label --output artifacts/models/random_forest.joblib
```

El script aplica limpieza estructural, `KNNImputer` para variables numericas, imputacion por moda para categoricas, `SMOTE` para balanceo de clases y serializa el paquete del modelo con `joblib`.

La validacion de discrepancias queda bloqueada hasta que existan umbrales aprobados por clase de equipo y variable de maquinaria.
