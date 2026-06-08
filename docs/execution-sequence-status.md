# Estado de Secuencia Global de Ejecucion

Fecha de revision: 2026-06-08
Responsable: Agente Auditor Principal / QA Architect

Regla de control: un bloque no puede iniciar si el bloque anterior no fue
auditado y registrado como aprobado o aprobado con condiciones explicitas.

## Resumen Ejecutivo

Estado actual: bloque 8 aprobado localmente para push; release demo final pendiente de GitHub Actions remoto en verde.
Siguiente agente habilitado: Orquestador Base para publicar cambios y verificar CI remoto.
El piloto con modelo predictivo real sigue bloqueado hasta calibracion con datos reales.

## Bloque 1: Fundacion del Repositorio

Responsable: Agente Orquestador Base  
Estado: aprobado con condiciones

Evidencia encontrada:

- Estructura base: `src/`, `docs/`, `scripts/`, `monitoring/`, `backups/`, `.agents/`.
- `docker-compose.yml` con servicios `frontend`, `backend`, `database`,
  `prometheus`, `grafana` y `db-backup`.
- `.env.example` con placeholders `CHANGE_ME`.
- `monitoring/prometheus.yml`.
- Documentacion inicial en `docs/setup.md`, `docs/architecture.md`,
  `docs/security.md` y `docs/agent-memory.md`.

Pendiente antes de produccion:

- Confirmar politicas de red para PostgreSQL publicado en `5432`.
- Inicializar repositorio Git si se requiere flujo formal de merges.

Decision QA: puede pasar a bloque 2.

## Bloque 2: Diseno de Datos y Normativa

Responsable: Agente de Datos  
Estado: aprobado con condiciones

Evidencia encontrada:

- Migracion `src/db/migrations/001_iso14224_assets.sql`.
- Jerarquia ISO 14224: `plants -> production_lines -> cells -> equipment`.
- Tabla raiz `tenants` y `plants.tenant_id` para aislamiento.
- `sensor_observations` y `maintenance_logs` relacionados a `equipment`.
- `failure_catalog` existe y se relaciona con `maintenance_logs`.
- Reporte `docs/iso14224-schema-validation.md`.

Pendiente para el Agente de Datos:

- Poblar catalogo inicial de fallas predefinidas en `failure_catalog`.
- Definir datos semilla o migracion separada para catalogos aprobados.
- Confirmar si se requiere Row Level Security para aislamiento por tenant.
- Poblar `discrepancy_thresholds` con umbrales aprobados por clase de equipo y
  variable antes de activar auditoria automatica de discrepancias.

Decision QA: puede pasar a bloque 3, pero no a produccion sin catalogos y
umbrales aprobados.

## Bloque 3: Pipeline de Inteligencia Artificial

Responsable: Agente Machine Learning  
Estado: aprobado con condiciones

Evidencia encontrada:

- `src/ml/train.py` implementa carga CSV/Parquet, limpieza, separacion de
  features, `KNNImputer`, imputacion categorica, `SMOTE` y
  `RandomForestClassifier`.
- `src/ml/validation.py` bloquea validaciones si no existen umbrales aprobados.
- `src/ml/requirements.txt` existe.
- El entrenamiento serializa modelo y metricas en `artifacts/models/`.

Pendiente para el Agente Machine Learning:

- Agregar opcion XGBoost si el alcance exige Random Forest/XGBoost y no solo
  Random Forest.
- Agregar pruebas unitarias para `split_features_target`,
  `require_thresholds` y validaciones de discrepancias.
- Documentar formato minimo del dataset de entrenamiento.
- Generar un modelo de prueba o fixture no sensible para validar carga desde API.
- Definir criterio de aceptacion de metricas antes de promover un modelo.

Decision QA: puede pasar a bloque 4. La exposicion productiva del modelo queda
condicionada a pruebas y criterios de metricas.

Reevaluacion de calibracion con datos reales (2026-05-23):

- `docs/data-dictionary-real.md` declara pendiente la recepcion del dataset operativo real.
- `docs/ml-calibration-report.md` identifica que el modelo actual fue entrenado con `data/training_seed.csv`.
- `docs/model-validation-report.md` confirma que las metricas actuales son de validacion sintetica y split aleatorio.
- `docs/product-industrial-reliability-agent.md` define al Agente Producto /
  Industrial Reliability SME como responsable de reglas de etiquetado, ventanas
  de riesgo, umbrales por clase de equipo y aprobacion de seguridad operacional.
- Decision ML: no aprobado para piloto hasta contar con dataset real validado,
  revision de etiquetas por personal de mantenimiento y reglas firmadas por el
  Agente Producto / Industrial Reliability SME.

Decision QA actualizada: el bloque 3 sigue aprobado para integracion tecnica, pero queda bloqueado para piloto predictivo real.

## Bloque 4: Desarrollo de Core API

Responsable: Agente Backend  
Estado: aprobado

Evidencia encontrada:

- Aplicacion FastAPI en `src/api/main.py`.
- Routers en `src/api/routers/` para activos, catalogo, sensores,
  mantenimiento, discrepancias y predicciones.
- Modelos Pydantic en `src/api/schemas.py`.
- Conexion SQLAlchemy en `src/api/database.py`.
- Autenticacion Basic en `src/api/security.py`.
- Endpoint `/health` y endpoint `/metrics`.
- Artefacto de modelo en `artifacts/models/random_forest.joblib`.
- Reporte de integracion en `docs/backend-integration.md`.

Hallazgos QA cerrados:

- Manejo controlado de `SQLAlchemyError` mediante `src/api/errors.py`.
- Pruebas automatizadas en `tests/test_api.py`.
- Contrato OpenAPI exportado en `docs/openapi.json`.
- Procedimiento reproducible en `scripts/export-openapi.py`.

Pendientes no bloqueantes para Frontend:

- Poblar catalogo inicial de fallas y umbrales aprobados para habilitar
  auditoria de discrepancias completa.
- Ejecutar pruebas de integracion contra una base PostgreSQL controlada antes de
  produccion.

Decision QA: Backend queda aprobado para liberar el bloque 5.

## Bloque 5: Desarrollo de Interfaz Grafica

Responsable: Agente Frontend / Senior Frontend Engineer  
Estado: aprobado

Evidencia encontrada:

- Aplicacion React/Vite/TypeScript en `src/web`.
- Dashboard operativo en `src/web/src/main.tsx`.
- Cliente HTTP para endpoints documentados en `docs/openapi.json`.
- Mapa de calor predictivo por planta, linea, celula y equipo.
- Vista separada de bitacora humana.
- Dockerfile y README del frontend.
- Build de produccion generado en `src/web/dist`.
- Perfil formal definido en `docs/frontend-agent.md`.

Hallazgos QA cerrados:

- Flujo Frontend -> Backend -> modelo documentado con `PUMP-01` en
  `docs/frontend-block-5.md`.
- Mapa de calor distingue `low`, `medium`, `high`, `Sin sensor` y
  `Modelo no disponible`.
- Credenciales Basic mantenidas solo en memoria React.
- `.gitignore` excluye `src/web/node_modules/` y `src/web/dist/`.
- Smoke test frontend agregado en `src/web/src/main.test.tsx`.
- `npm run test` y `npm run build` aprobados.

Limitacion no bloqueante:

- La base actual solo expone un activo real documentado (`PUMP-01`) para
  verificacion visual. La leyenda y el modelo soportan `low`, `medium`, `high`,
  pero confirmar tres tarjetas reales requiere sembrar mas activos/lecturas.

Decision QA: Frontend queda aprobado para liberar el bloque 6.

## Bloque 6: Integracion de Monitoreo y Respaldos

Responsable: Agente Orquestador Base  
Estado: aprobado

Evidencia encontrada:

- Prometheus configurado en `monitoring/prometheus.yml`.
- Reglas de alerta en `monitoring/alert_rules.yml`.
- `docker-compose.yml` incluye Prometheus, Grafana, `postgres-exporter` y `db-backup`.
- Grafana provisionado con datasource `Prometheus` y dashboard `MERO Platform Overview`.
- `db-backup` ejecuta `scripts/postgres-backup-cron.sh` con reintentos.
- `scripts/postgres-dump.sh` genera respaldo PostgreSQL en formato custom usando archivo temporal atomico.
- Manuales de mantenimiento y recuperacion documentan restauracion.
- Evidencia de cierre registrada en `docs/block-6-observability-backups.md`.

Evidencia ejecutada:

- Prometheus targets `mero-backend`, `mero-postgres` y `prometheus` en estado `up`.
- Grafana API confirma datasource `Prometheus`.
- Grafana API confirma dashboard `MERO Platform Overview`.
- Respaldo manual generado: `mero_20260523T200221Z.dump`.
- Restauracion controlada en base temporal `mero_restore_check` validada con 11 relaciones publicas.
- `pytest` backend: 6 pruebas aprobadas.
- `npm test` frontend: 1 prueba aprobada.
- `npm run build` frontend: aprobado.
- `docker compose build frontend`: aprobado.

Decision QA: Bloque 6 aprobado. Prometheus, Grafana, respaldos y restauracion
quedan validados.

## Bloque 7: Auditoria y Documentacion

Responsable: Agente Auditor Principal  
Estado: listo para dictamen final

Evidencia encontrada:

- `docs/audit-report-2026-05-22.md`.
- `docs/security-checklist.md`.
- `docs/maintenance.md`.
- `docs/disaster-recovery.md`.
- Revision de secretos sin hallazgos de credenciales reales hardcodeadas.

Pendiente del Auditor Principal:

- Emitir aprobacion final o bloqueo de despliegue.

Decision QA: bloques tecnicos 1 a 6 aprobados. El dictamen final debe mantener
como condiciones de produccion TLS/cifrado en reposo segun politica del cliente
y aprobacion de umbrales antes de activar discrepancias automaticas.

## Bloque 8: Bootstrap Demo y Publicacion GitHub

Responsable: Agente Orquestador Base, Agente de Datos y ML, Backend, Frontend y Auditor Principal
Estado: aprobado localmente; release demo publica pendiente de CI remoto

Evidencia encontrada:

- `scripts/bootstrap-demo.py` genera dataset demo, entrena modelo, aplica migraciones,
  inserta datos sinteticos y ejecuta smoke check predictivo.
- `docs/demo-data.md` documenta la jerarquia sintetica y declara que no son datos
  reales de cliente.
- `README.md` documenta el flujo demo desde checkout limpio.
- `.gitignore` excluye `.env`, respaldos, modelos generados, datasets reales y
  artefactos de frontend.
- `tests/test_demo_integration.py` permite validacion live bajo
  `RUN_DEMO_INTEGRATION=1`.
- `tests/test_api.py` cubre respuesta limpia ante modelo faltante.
- `docs/audit-report-2026-06-08-demo-bootstrap-review.md`.
- `docs/audit-report-2026-06-08-release-demo-final.md`.

Evidencia ejecutada en auditoria 2026-06-08:

- Backend: `7 passed`, `1 skipped`.
- Frontend: `1 passed`.
- Frontend build: aprobado.
- `npm ci`: aprobado.
- Bootstrap live con Docker: aprobado.
- Integracion live: `1 passed`.
- Busqueda de secretos en archivos rastreables: sin credenciales reales detectadas.

Hallazgo corregido:

- QA-REL-001 por vulnerabilidad critica `GHSA-5xrq-8626-4rwp` en
  `vitest <3.2.6` fue corregido actualizando `vitest` a `^3.2.6`.
- `npm audit`: `found 0 vulnerabilities`.
- `npm run test`: aprobado.
- `npm run build`: aprobado.

Decision QA: apto para push a GitHub. Queda pendiente confirmar workflows remotos en verde antes de tag/release final.

## Orden Autorizado a Partir de Ahora

1. Orquestador Base publica los cambios en GitHub.
2. Orquestador Base confirma workflows remotos de GitHub Actions en verde.
3. Auditor QA emite cierre final de release demo si los checks remotos pasan.
4. Agente Producto / Industrial Reliability SME define y firma reglas de etiquetado, ventanas de riesgo, umbrales y activos criticos con mantenimiento del cliente.
5. Agente de Datos y ML retoma calibracion cuando exista dataset operativo real y validacion de etiquetas.

## Bloqueos Activos

- Produccion requiere TLS/cifrado en reposo conforme a politica del cliente.
- Validaciones automaticas de discrepancia requieren umbrales aprobados.
- Piloto con uso predictivo del modelo bloqueado hasta entrenar y validar con datos reales, validacion temporal y firma de etiquetas por mantenimiento.
- No se entrena ni aprueba modelo real sin reglas de etiquetado firmadas por el
  Agente Producto / Industrial Reliability SME y por mantenimiento del cliente.
- Release demo publica pendiente de confirmar CI remoto en verde.
