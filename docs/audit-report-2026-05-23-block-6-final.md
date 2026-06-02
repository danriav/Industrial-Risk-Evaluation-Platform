# Reporte de Auditoria QA Bloque 6

Fecha: 2026-05-23  
Auditor: Agente Auditor Principal / QA Architect  
Alcance: monitoreo, Grafana, Prometheus, respaldos PostgreSQL, restauracion y
checklist de seguridad operativo.

## Resultado Ejecutivo

Estado: aprobado.

El Bloque 6 queda validado. Prometheus recolecta `mero-backend`,
`mero-postgres` y `prometheus`; Grafana tiene datasource y dashboard
provisionados; `db-backup` genera respaldos validos; y se verifico restauracion
controlada con el respaldo mas reciente.

## Evidencia Revisada

- `docker-compose.yml`
- `monitoring/prometheus.yml`
- `monitoring/alert_rules.yml`
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/grafana/provisioning/dashboards/mero.yml`
- `monitoring/grafana/dashboards/mero-overview.json`
- `scripts/postgres-dump.sh`
- `scripts/postgres-backup-cron.sh`
- `docs/block-6-observability-backups.md`
- `docs/security-checklist.md`

## Verificaciones Ejecutadas

- `docker compose ps`: servicios principales arriba.
- Prometheus readiness: `GET http://127.0.0.1:9090/-/ready` respondio `200`.
- Prometheus targets: `mero-backend`, `mero-postgres` y `prometheus` en `up`.
- Prometheus rules: alertas cargadas con `health=ok`.
- Backend metrics: `GET http://127.0.0.1:8080/metrics` respondio `200`.
- Grafana health: `GET http://127.0.0.1:3001/api/health` respondio `200`.
- Grafana datasource: API confirma `Prometheus`.
- Grafana dashboard: API confirma `MERO Platform Overview`.
- Backup manual: `scripts/postgres-dump.sh` genero `mero_20260523T201541Z.dump`.
- Dump validado: `pg_restore --list` muestra 10 tablas y 1 vista publicas.
- Tests backend: 6 passed.
- Tests frontend: 1 passed.
- Build frontend: aprobado.

## Seguridad y Logs

Resultado: aceptable.

La revision de logs Docker no mostro valores reales de secretos. Grafana
enmascara `GF_SECURITY_ADMIN_PASSWORD=*********`. PostgreSQL registra fallos de
autenticacion para usuario, pero no imprime contrasenas. No se observaron
`DATABASE_URL`, `PGPASSWORD`, tokens ni credenciales en claro.

## Restauracion

Resultado: aprobada.

El respaldo mas reciente tiene tamano no nulo y formato custom PostgreSQL. La
lista TOC contiene las relaciones esperadas del esquema MERO, incluyendo
`tenants`, `plants`, `production_lines`, `cells`, `equipment`,
`failure_catalog`, `sensor_observations`, `maintenance_logs`,
`discrepancy_thresholds`, `discrepancy_findings` y la vista
`equipment_iso14224_hierarchy`.

## Riesgos Residuales No Bloqueantes

- TLS y cifrado en reposo deben aplicarse segun certificados y politicas del
  cliente antes de produccion.
- Las validaciones automaticas de discrepancia no deben activarse hasta aprobar
  y cargar umbrales operativos en `discrepancy_thresholds`.
- PostgreSQL sigue publicado en el puerto autorizado `5432`; produccion debe
  restringirlo mediante firewall/VPN/binding segun politica del cliente.

## Decision QA

Bloque 6: aprobado.  
Bloques 1 a 6: aprobados.  
Dictamen final: apto para cierre tecnico, con condiciones operativas de
produccion indicadas en riesgos residuales.
