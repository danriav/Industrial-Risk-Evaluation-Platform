# CI and Bootstrap Validation

Fecha: 2026-06-08

## Alcance

Se activaron workflows de GitHub Actions para validar backend y frontend por separado:

- `.github/workflows/backend-ci.yml`: instala Python 3.12, instala `src/api/requirements.txt` y ejecuta `python -m pytest`.
- `.github/workflows/frontend-ci.yml`: instala Node 24, ejecuta `npm ci`, `npm run test` y `npm run build` en `src/web`.

## Validacion local equivalente a CI

Backend:

```sh
.\.venv\Scripts\python.exe -m pytest
```

Resultado: PASS, 7 passed, 1 skipped.

Frontend:

```sh
npm ci
npm run test
npm run build
```

Resultado: PASS.

Nota: `npm ci` requirio permisos elevados en Windows para limpiar `src/web/node_modules/.vite-temp`. El comando completo paso despues de liberarlo. `npm audit` reporto 1 vulnerabilidad critica pendiente de triage; no bloquea el workflow actual porque no se ejecuta `npm audit` en CI.

## Bootstrap live

Docker Desktop no estaba activo al inicio de la validacion. Se inicio Docker Desktop, se verifico que el engine respondiera y se levanto el stack:

```sh
docker compose up -d --build
```

Resultado: PASS.

En esta maquina el puerto `3000` esta ocupado por otro proceso, por lo que el `.env` local ignorado por Git usa `FRONTEND_PORT=3002`. Los puertos de backend, PostgreSQL, Prometheus y Grafana quedaron en `8080`, `5432`, `9090` y `3001`.

Se ejecuto el bootstrap live con reinicio real del backend. Comando objetivo para checkout limpio:

```sh
python scripts/bootstrap-demo.py --restart-backend
```

En esta estacion Windows se uso `.\.venv\Scripts\python.exe scripts\bootstrap-demo.py --restart-backend` porque el alias `python` no esta en `PATH`.

Resultado: PASS.

Evidencia observada:

- Genero `data/training_seed.csv`.
- Entreno `artifacts/models/random_forest.joblib`.
- Escribio `artifacts/models/random_forest_metrics.json`.
- Aplico migraciones SQL.
- Inserto jerarquia demo sintetica: 2 plantas, 3 lineas, 4 celulas, 8 equipos y 6 flujos de sensores.
- Reinicio `mero-backend`.
- Smoke check de prediccion paso con `risk_label=medium`, `model_version=random_forest` y `feature_count=8`.

Tambien se ejecuto la prueba live:

```sh
RUN_DEMO_INTEGRATION=1 python -m pytest tests/test_demo_integration.py
```

Resultado: PASS, 1 passed.

## Proteccion de artefactos

Se verifico con `git check-ignore -v` que los siguientes artefactos permanecen fuera de Git:

- `.env`
- `artifacts/models/random_forest.joblib`
- `artifacts/models/random_forest_metrics.json`
- `backups/*.dump`
- `src/web/dist/`
- `src/web/node_modules/`
- `*.log`
- `data/real/*`
- `data/processed/*`

## Cierre QA-REL-001

Se actualizo `vitest` en `src/web/package.json` de `^3.0.0` a `^3.2.6` para corregir el advisory `GHSA-5xrq-8626-4rwp`.

Validacion frontend posterior:

```sh
npm audit
npm run test
npm run build
```

Resultado:

- `npm audit`: PASS, `found 0 vulnerabilities`.
- `npm run test`: PASS, Vitest 3.2.6, 1 test passed.
- `npm run build`: PASS, TypeScript y Vite build aprobados.
- `git check-ignore -v`: PASS para `.env`, `src/web/node_modules/`, `src/web/dist/`, modelos `.joblib`, backups y logs.

## Gate de release

Estado local: PASS para CI equivalente y bootstrap live.

Condicion de release demostrable: QA-REL-001 queda corregido localmente. No aprobar release final hasta que los workflows de GitHub Actions corran en remoto y queden en verde sobre el commit/PR correspondiente.
