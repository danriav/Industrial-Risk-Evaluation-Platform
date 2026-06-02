# Base de Datos

PostgreSQL se publica en el puerto autorizado `5432` para administracion local controlada.

Variables principales:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

El diseno de esquema, migraciones e implementacion de Row Level Security quedan fuera del alcance del Agente Orquestador Base.

## Migraciones de datos y ML

La migracion inicial del Agente de Datos y ML esta en `src/db/migrations/001_iso14224_assets.sql`.

El esquema implementa la jerarquia ISO 14224 acordada:

1. `plants`
2. `production_lines`
3. `cells`
4. `equipment`

La tabla raiz `tenants` mantiene el aislamiento por empresa y `plants.tenant_id` conecta la jerarquia industrial con ese aislamiento. Las observaciones de sensores (`sensor_observations`) y las bitacoras humanas (`maintenance_logs`) se relacionan a `equipment`, que es el nivel mas granular.

Los campos `last_known_state` y `last_state_updated_at` existen en los niveles operativos para conservar el ultimo estado conocido sin mezclarlo con la prediccion del modelo.

## Discrepancias de maquinaria

Los umbrales logicos no estan codificados en el modelo ni en los scripts. Deben aprobarse y cargarse en `discrepancy_thresholds` por clase de equipo y variable antes de ejecutar validaciones de discrepancias.

Si no existen umbrales aprobados, `src/ml/validation.py` detiene la validacion con `MissingThresholdConsensusError`.

La primera propuesta de umbrales esta documentada en `docs/ml-training-flow.md`; queda pendiente de aprobacion por operaciones/confiabilidad antes de poblar `discrepancy_thresholds`.
