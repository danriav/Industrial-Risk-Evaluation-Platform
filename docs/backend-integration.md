# Integracion Backend

Fecha de verificacion: 2026-05-22

## Alcance

Este documento registra la primera integracion real del Agente Backend:

- Verificar que `src/api/main.py` expone `/health` y `/metrics`.
- Confirmar que el backend arranca con `.venv`.
- Validar conexion a PostgreSQL usando `DATABASE_URL`.
- Aplicar o documentar como aplicar `src/db/migrations/001_iso14224_assets.sql`.
- Probar endpoints basicos contra la base de datos.

No se modifican frontend, puertos autorizados ni secretos reales.

## Arranque local con `.venv`

Comando:

```powershell
.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8080
```

Verificaciones ejecutadas:

- `GET http://127.0.0.1:8080/health` respondio `200`.
- `GET http://127.0.0.1:8080/metrics` respondio `200` con metricas Prometheus.

## Migracion de base de datos

La migracion principal esta en:

```text
src/db/migrations/001_iso14224_assets.sql
```

Aplicacion recomendada desde `.venv`, sin depender de `psql` local:

```powershell
$env:DATABASE_URL="postgresql+psycopg://USUARIO:PASSWORD@127.0.0.1:5432/BASE"
.venv\Scripts\python.exe scripts\apply-db-migrations.py
```

Tambien puede aplicarse desde un contenedor PostgreSQL con `psql` si el entorno
operativo lo prefiere:

```sh
psql "$DATABASE_URL" -f src/db/migrations/001_iso14224_assets.sql
```

## Prueba de conexion PostgreSQL

Comando de verificacion:

```powershell
$env:DATABASE_URL="postgresql+psycopg://USUARIO:PASSWORD@127.0.0.1:5432/BASE"
.venv\Scripts\python.exe -c "from sqlalchemy import create_engine, text; import os; engine=create_engine(os.environ['DATABASE_URL']); print(engine.connect().execute(text('select 1')).scalar())"
```

Resultado esperado:

```text
1
```

## Endpoints basicos contra BD

Con la base arriba, migrada y con credenciales Basic configuradas:

```powershell
$pair = "USUARIO_BASIC:PASSWORD_BASIC"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $auth" }

Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v1/assets/hierarchy -Headers $headers
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v1/failure-catalog -Headers $headers
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v1/maintenance-logs -Headers $headers
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v1/sensor-observations -Headers $headers
```

## Resultado ejecutado

Estado: completado para primera integracion backend.

Evidencia:

- Conexion PostgreSQL con `DATABASE_URL` validada con `select 1`.
- `src/db/migrations/001_iso14224_assets.sql` aplicada correctamente.
- Tablas/vista principales encontradas: `tenants`, `plants`,
  `production_lines`, `cells`, `equipment`, `sensor_observations`,
  `maintenance_logs` y `equipment_iso14224_hierarchy`.
- Backend levantado con `.venv` en `127.0.0.1:8080`.
- `GET /health` respondio `200`.
- `GET /metrics` respondio `200`.
- `GET /api/v1/assets/hierarchy` respondio `200` contra BD.
- `GET /api/v1/failure-catalog` respondio `200` contra BD.
- `POST /api/v1/sensor-observations` respondio `201` contra BD.
- `POST /api/v1/maintenance-logs` respondio `201` contra BD.

Observacion: se usaron credenciales Basic temporales de integracion solo como
variables de entorno de proceso. No se escribieron secretos reales en archivos.

## Correcciones QA posteriores

Las correcciones de hallazgos QA del bloque 4 quedaron registradas en
`docs/backend-qa-fixes.md`.

## Verificacion de prediccion ML

Fecha de verificacion: 2026-05-23

Artefacto cargado:

```text
artifacts/models/random_forest.joblib
```

Contrato de features del modelo:

- `temperature_c`
- `vibration_mm_s`
- `pressure_bar`
- `rpm`
- `operating_hours`
- `load_pct`
- `equipment_class`
- `sensor_quality`

Clases del modelo:

- `high`
- `low`
- `medium`

Resultado PUMP-01:

- `POST /api/v1/predictions/risk` respondio `200`.
- `risk_label`: `low`.
- `model_version`: `random_forest`.
- `feature_count`: `8`.

Validacion de errores:

- Una peticion con features faltantes respondio `422`.
- La respuesta incluye `required_features`, `missing_features` y
  `extra_features`.
- Los errores del modelo se convierten en respuestas limpias, sin `500` crudo.
