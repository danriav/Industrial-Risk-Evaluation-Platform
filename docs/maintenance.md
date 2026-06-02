# Manual de Mantenimiento

Este manual define las tareas minimas para operar MERO en una instalacion
on-premise. Ningun despliegue debe aprobarse si este documento no fue revisado
junto con `docs/disaster-recovery.md`.

## Responsables

- Operador de plataforma: ejecuta respaldos, restauraciones y arranques.
- Administrador de base de datos: valida integridad de PostgreSQL y migraciones.
- Auditor QA: revisa logs, evidencias de respaldo y checklist de seguridad.
- Responsable del cliente: autoriza ventanas de mantenimiento y cambios de puertos.

## Rutina diaria

1. Confirmar que los contenedores esten saludables:

```sh
docker compose ps
```

2. Validar que exista al menos un respaldo reciente en `./backups`.
3. Revisar que los logs no incluyan credenciales, tokens ni datos crudos de sensores
   innecesarios:

```sh
docker compose logs --since 24h
```

4. Confirmar que Prometheus recolecta `mero-backend` en `http://localhost:9090`.
5. Confirmar que Grafana muestra el tablero `MERO Platform Overview` en
   `http://localhost:3001`.

## Rutina semanal

1. Ejecutar un respaldo manual y registrar el nombre del archivo generado:

```sh
docker compose exec db-backup /scripts/postgres-dump.sh
```

2. Probar una restauracion en ambiente aislado antes de eliminar respaldos antiguos.
3. Revisar crecimiento de volumenes Docker:

```sh
docker system df
```

4. Confirmar que `.env` no fue copiado a documentacion, tickets ni artefactos.

## Respaldos

Los respaldos se generan en `./backups` mediante el servicio `db-backup`.

Variables relevantes:

- `BACKUP_INTERVAL_SECONDS`: intervalo entre respaldos. Por defecto, 24 horas.
- `BACKUP_RETENTION_DAYS`: dias de retencion local. Por defecto, 14.
- `BACKUP_RETRY_SECONDS`: espera entre reintentos si PostgreSQL aun no acepta conexiones.
- `BACKUP_MAX_ATTEMPTS`: intentos maximos antes de reportar fallo de respaldo.

El script `scripts/postgres-dump.sh` usa `pg_dump` en formato custom, sin owner y
sin ACL. El log del respaldo solo debe mostrar la ruta del archivo generado; no
debe imprimir `PGPASSWORD`, `DATABASE_URL` ni credenciales de Grafana.

## Observabilidad

Prometheus:

- Configuracion: `monitoring/prometheus.yml`.
- Reglas de alerta: `monitoring/alert_rules.yml`.
- Targets esperados: `mero-backend`, `mero-postgres` y `prometheus`.

Grafana:

- Puerto autorizado: `3001`.
- Datasource provisionado: `Prometheus`.
- Dashboard provisionado: `MERO Platform Overview`.

El exportador `postgres-exporter` no publica puertos al host; solo queda
disponible dentro de `mero_internal` para Prometheus.

## Restauracion Operativa

Usar esta restauracion para pruebas controladas o recuperaciones menores. Para
incidentes mayores, seguir `docs/disaster-recovery.md`.

1. Identificar el respaldo aprobado en `./backups`.
2. Pausar escrituras de aplicacion si el ambiente esta en uso.
3. Ejecutar:

```sh
docker compose exec database pg_restore --clean --if-exists --dbname "$POSTGRES_DB" /backups/NOMBRE_DEL_RESPALDO.dump
```

4. Reiniciar servicios que dependan de la base:

```sh
docker compose restart backend frontend
```

5. Verificar acceso a la API, metricas y tablero operacional.

## Cambios y Parches

- No cambiar imagenes, puertos ni variables sensibles sin ventana aprobada.
- Mantener `.env.example` sin secretos reales.
- Registrar version de imagen, fecha, operador y resultado de verificacion.
- Ejecutar validacion ISO 14224 si se modifican migraciones de activos.

## Evidencia Minima de Mantenimiento

Cada ventana debe dejar:

- Fecha y hora de inicio/cierre.
- Operador responsable.
- Comandos ejecutados.
- Respaldo usado o generado.
- Resultado de `docker compose ps`.
- Incidentes encontrados y acciones correctivas.
