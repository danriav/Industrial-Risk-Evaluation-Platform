# Correcciones QA Backend

Fecha: 2026-05-22  
Responsable: Agente Backend

## Alcance

Correcciones realizadas para los hallazgos QA del bloque 4 documentados en
`docs/audit-report-2026-05-22-backend-review.md`.

## QA-BE-001: manejo controlado de errores de base de datos

Estado: corregido.

Cambios:

- Se agrego `src/api/errors.py`.
- `src/api/main.py` registra un handler global para `SQLAlchemyError`.
- `OperationalError` responde `503` con `{"detail":"Database is unavailable"}`.
- Otros errores SQLAlchemy no controlados responden `500` con
  `{"detail":"Database operation failed"}`.
- Las respuestas no incluyen `DATABASE_URL`, credenciales ni detalles internos.

Evidencia:

- `tests/test_api.py::ApiTests::test_database_errors_are_controlled`.
- `python -m pytest` ejecutado con resultado: 4 passed.

## QA-BE-002: pruebas automatizadas Backend

Estado: corregido.

Cambios:

- Se agrego `tests/test_api.py`.
- Se agrego `pytest.ini`.
- Se agrego `pytest==8.2.2` en `src/api/requirements.txt`.

Cobertura inicial:

- `/health`.
- `/metrics`.
- Autenticacion en endpoint protegido.
- Manejo controlado de errores de base de datos.
- Contrato de prediccion con resultado de modelo simulado.

Evidencia:

```text
4 passed, 1 warning in 0.68s
```

## QA-BE-003: contrato OpenAPI exportado para Frontend

Estado: corregido.

Cambios:

- Se agrego `scripts/export-openapi.py`.
- Se genero `docs/openapi.json`.
- `docs/api.md` documenta el contrato exportado y el comando reproducible.

Comando:

```powershell
.venv\Scripts\python.exe scripts\export-openapi.py
```

Evidencia:

- `docs/openapi.json` contiene 8 rutas.
- Incluye `/api/v1/failure-catalog`.
- Incluye `/api/v1/predictions/risk`.

## Evidencia contra PostgreSQL

Con `DATABASE_URL` configurado solo como variable de entorno de proceso, los
endpoints principales respondieron contra PostgreSQL:

- `GET /api/v1/assets/hierarchy`: `200`.
- `GET /api/v1/failure-catalog`: `200`.
- `GET /api/v1/maintenance-logs`: `200`.
- `GET /api/v1/sensor-observations`: `200`.

No se escribieron secretos reales en archivos.

