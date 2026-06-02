# Bloque 6: Monitoreo y Respaldos

Fecha de cierre tecnico: 2026-05-23  
Responsable: Agente Orquestador Base

## Alcance

El Bloque 6 cierra la integracion operativa de observabilidad y respaldos para la instancia on-premise de MERO.

## Evidencia

- Prometheus expuesto en el puerto autorizado `9090`.
- Grafana expuesto en el puerto autorizado `3001`.
- PostgreSQL expuesto en el puerto autorizado `5432`.
- Backend expuesto en el puerto autorizado `8080`.
- Frontend expuesto en el puerto autorizado `3000`.
- `postgres-exporter` agregado como servicio interno sin puerto publicado al host.
- Prometheus scrapea tres targets en estado `up`:
  - `mero-backend`
  - `mero-postgres`
  - `prometheus`
- Reglas de alerta cargadas desde `monitoring/alert_rules.yml`.
- Grafana provisionado con datasource `Prometheus`.
- Dashboard provisionado: `MERO Platform Overview`.
- Servicio `db-backup` activo con respaldos en `./backups`.
- Respaldo manual validado: `mero_20260523T200221Z.dump`.
- Restauracion controlada validada en base temporal `mero_restore_check`.

## Restauracion

Prueba ejecutada:

1. Seleccion del respaldo mas reciente en `./backups`.
2. Creacion de base temporal `mero_restore_check`.
3. Restauracion con `pg_restore`.
4. Validacion de relaciones restauradas en `information_schema.tables`.
5. Eliminacion de base temporal.

Resultado: restauracion exitosa con `11` relaciones publicas detectadas.

## Notas Operativas

- Los archivos `.dump` de 0 bytes generados por intentos fallidos previos fueron retirados.
- `scripts/postgres-dump.sh` ahora escribe a un archivo temporal y solo publica el `.dump` si `pg_dump` termina correctamente.
- `scripts/postgres-backup-cron.sh` incluye reintentos para tolerar arranques lentos de PostgreSQL.
- `src/web/.dockerignore` evita incluir `node_modules` y `dist` en el contexto Docker del frontend.
