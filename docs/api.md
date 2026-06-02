# API

La API Core se publica en `http://localhost:8080`.

Documentacion interactiva:

- OpenAPI JSON: `GET /openapi.json`
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- Contrato exportado para Frontend: `docs/openapi.json`

Exportar contrato versionado:

```powershell
.venv\Scripts\python.exe scripts\export-openapi.py
```

Contrato de plataforma:

- Exponer metricas Prometheus en `GET /metrics`.
- Leer `DATABASE_URL` desde variables de entorno.
- No registrar credenciales ni datos crudos sensibles en logs.
- Usar autenticacion HTTP Basic para endpoints de negocio.
- Habilitar CORS solo para origenes aprobados.
- Forzar redireccion HTTPS cuando `FORCE_HTTPS=true`.

## Seguridad

Todos los endpoints bajo `/api/v1` requieren HTTP Basic.

Variables:

- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`: debe reemplazar el placeholder `CHANGE_ME` antes de usar endpoints de negocio.
- `CORS_ORIGINS`: lista separada por comas. Ejemplo: `http://localhost:3000`
- `FORCE_HTTPS`: `true` o `false`

Respuesta de error estandar:

```json
{
  "detail": "Mensaje de error"
}
```

## Health

### `GET /health`

No requiere autenticacion.

Respuesta `200`:

```json
{
  "status": "ok",
  "service": "mero-api"
}
```

## Activos ISO 14224

### `GET /api/v1/assets/hierarchy`

Devuelve la jerarquia industrial para el dashboard y el mapa de calor.

Query params:

- `tenant_id` opcional, UUID.

Respuesta `200`:

```json
{
  "items": [
    {
      "tenant_id": "00000000-0000-0000-0000-000000000001",
      "plant_id": "00000000-0000-0000-0000-000000000010",
      "plant_code": "PLT-01",
      "line_id": "00000000-0000-0000-0000-000000000020",
      "line_code": "LN-01",
      "cell_id": "00000000-0000-0000-0000-000000000030",
      "cell_code": "CELL-01",
      "equipment_id": "00000000-0000-0000-0000-000000000040",
      "equipment_code": "PUMP-01",
      "equipment_class": "centrifugal_pump",
      "last_known_state": "operational",
      "last_state_updated_at": "2026-05-22T15:00:00Z"
    }
  ]
}
```

### `GET /api/v1/equipment/{equipment_id}`

Devuelve el detalle operativo de un equipo.

Respuesta `200`:

```json
{
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "cell_id": "00000000-0000-0000-0000-000000000030",
  "equipment_code": "PUMP-01",
  "equipment_name": "Bomba principal",
  "equipment_class": "centrifugal_pump",
  "manufacturer": "ACME",
  "model": "XP-100",
  "serial_number": "SN-123",
  "installed_at": "2024-01-15",
  "last_known_state": "operational",
  "last_state_updated_at": "2026-05-22T15:00:00Z"
}
```

## Catalogo de fallas

### `GET /api/v1/failure-catalog`

Devuelve modos de falla activos para formularios de bitacora.

Respuesta `200`:

```json
{
  "items": [
    {
      "failure_code": "BRG_OVERHEAT",
      "failure_category": "mechanical",
      "failure_mode": "bearing_overheating",
      "iso14224_reference": "ISO14224",
      "is_active": true
    }
  ]
}
```

## Observaciones de sensores

### `GET /api/v1/sensor-observations`

Query params:

- `equipment_id` opcional, UUID.
- `limit` opcional, entero entre 1 y 200. Default: 50.

Respuesta `200`:

```json
{
  "items": [
    {
      "observation_id": "00000000-0000-0000-0000-000000000060",
      "equipment_id": "00000000-0000-0000-0000-000000000040",
      "observed_at": "2026-05-22T15:00:00Z",
      "temperature_c": 82.4,
      "vibration_mm_s": 4.7,
      "pressure_bar": 9.1,
      "rpm": 1780,
      "operating_hours": 12043,
      "load_pct": 76.5,
      "sensor_quality": "good",
      "created_at": "2026-05-22T15:00:02Z"
    }
  ]
}
```

### `POST /api/v1/sensor-observations`

Registra una lectura de sensor. Esta salida no se mezcla con la bitacora humana.

Request:

```json
{
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "observed_at": "2026-05-22T15:00:00Z",
  "temperature_c": 82.4,
  "vibration_mm_s": 4.7,
  "pressure_bar": 9.1,
  "rpm": 1780,
  "operating_hours": 12043,
  "load_pct": 76.5,
  "sensor_quality": "good"
}
```

Respuesta `201`: mismo esquema que `SensorObservationItem`.

## Bitacora de mantenimiento

### `GET /api/v1/maintenance-logs`

Query params:

- `equipment_id` opcional, UUID.
- `limit` opcional, entero entre 1 y 200. Default: 50.

Respuesta `200`:

```json
{
  "items": [
    {
      "maintenance_log_id": "00000000-0000-0000-0000-000000000050",
      "equipment_id": "00000000-0000-0000-0000-000000000040",
      "reported_at": "2026-05-22T15:05:00Z",
      "operator_state": "requires_review",
      "failure_code": "BRG_OVERHEAT",
      "free_text_observation": "Ruido anormal en rodamiento",
      "created_at": "2026-05-22T15:06:00Z"
    }
  ]
}
```

### `POST /api/v1/maintenance-logs`

Crea un registro humano de mantenimiento sin mezclarlo con lecturas de sensores.

Request:

```json
{
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "reported_at": "2026-05-22T15:05:00Z",
  "operator_state": "requires_review",
  "failure_code": "BRG_OVERHEAT",
  "free_text_observation": "Ruido anormal en rodamiento"
}
```

Respuesta `201`:

```json
{
  "maintenance_log_id": "00000000-0000-0000-0000-000000000050",
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "reported_at": "2026-05-22T15:05:00Z",
  "operator_state": "requires_review",
  "failure_code": "BRG_OVERHEAT",
  "free_text_observation": "Ruido anormal en rodamiento",
  "created_at": "2026-05-22T15:06:00Z"
}
```

## Auditoria de discrepancias

### `POST /api/v1/discrepancies/audit/{observation_id}`

Valida una observacion contra umbrales aprobados en `discrepancy_thresholds` y
persiste hallazgos en `discrepancy_findings`.

Respuesta `200`:

```json
{
  "observation_id": "00000000-0000-0000-0000-000000000060",
  "findings": [
    {
      "finding_id": "00000000-0000-0000-0000-000000000070",
      "observation_id": "00000000-0000-0000-0000-000000000060",
      "threshold_id": "00000000-0000-0000-0000-000000000080",
      "variable_name": "temperature_c",
      "observed_value": 98.2,
      "expected_min": 0,
      "expected_max": 90,
      "severity": "high",
      "detected_at": "2026-05-22T15:00:03Z"
    }
  ]
}
```

Si faltan umbrales aprobados, la API responde `409`.

## Inferencia predictiva

### `POST /api/v1/predictions/risk`

Ejecuta inferencia de baja latencia usando el modelo serializado configurado en `MODEL_PATH`.

El objeto `features` debe coincidir con las columnas esperadas por el modelo
entrenado:

- `temperature_c`
- `vibration_mm_s`
- `pressure_bar`
- `rpm`
- `operating_hours`
- `load_pct`
- `equipment_class`
- `sensor_quality`

Request:

```json
{
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "observed_at": "2026-05-22T15:00:00Z",
  "features": {
    "equipment_class": "centrifugal_pump",
    "temperature_c": 82.4,
    "vibration_mm_s": 4.7,
    "pressure_bar": 9.1,
    "rpm": 1780,
    "operating_hours": 12043,
    "load_pct": 76.5,
    "sensor_quality": "good"
  }
}
```

Respuesta `200`:

```json
{
  "equipment_id": "00000000-0000-0000-0000-000000000040",
  "observed_at": "2026-05-22T15:00:00Z",
  "risk_label": "high",
  "risk_score": 0.87,
  "model_version": "random_forest",
  "feature_count": 8
}
```

Si el modelo no esta disponible, la API responde `503`.

Si faltan o sobran features respecto al contrato del modelo, la API responde
`422` con `required_features`, `missing_features` y `extra_features`.
