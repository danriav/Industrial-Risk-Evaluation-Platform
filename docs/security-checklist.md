# Checklist de Seguridad QA

Este checklist debe completarse antes de aprobar un despliegue o merge.

## Secretos y Configuracion

- [x] `.env` no esta versionado.
- [x] `.env.example` solo contiene valores `CHANGE_ME` o locales no sensibles.
- [x] `POSTGRES_PASSWORD` y `GRAFANA_ADMIN_PASSWORD` no aparecen en logs.
- [x] `DATABASE_URL` no se imprime completo en errores ni trazas.
- [ ] Credenciales rotadas despues de incidentes o accesos no autorizados.

## Logs y Datos

- [x] Logs de backend no incluyen datos crudos sensibles de sensores.
- [x] Logs de entrenamiento ML no contienen datasets ni filas completas.
- [x] Scripts de respaldo solo imprimen ruta del archivo generado.
- [x] Bitacoras humanas no se mezclan con observaciones de sensores en salidas de auditoria.

## Red y Exposicion

- [x] Solo estan publicados los puertos autorizados: `3000`, `8080`, `5432`, `9090`, `3001`.
- [x] Servicios internos usan la red `mero_internal`.
- [x] `db-backup` no publica puertos.
- [x] Grafana mantiene `GF_USERS_ALLOW_SIGN_UP=false`.
- [ ] TLS y cifrado en reposo estan definidos por politica del cliente antes de produccion.

## Base de Datos y Cumplimiento

- [x] Migraciones conservan jerarquia ISO 14224: planta, linea, celula, equipo.
- [x] `tenant_id` existe en la raiz de aislamiento.
- [x] Observaciones y bitacoras se relacionan al nivel `equipment`.
- [ ] Umbrales de discrepancia estan aprobados antes de activar validaciones.
- [x] Restauracion desde respaldo fue probada en ambiente aislado.

## Documentacion Bloqueante

- [x] `docs/maintenance.md` existe y contiene rutinas operativas.
- [x] `docs/disaster-recovery.md` existe y contiene RTO, RPO, roles y pasos de restauracion.
- [x] Evidencia de prueba de respaldo/restauracion queda adjunta al reporte de auditoria.

## Pendientes No Cerrados

- Rotacion de credenciales: requerida si hubo incidente, exposicion o uso de credenciales compartidas.
- TLS y cifrado en reposo: pendiente de politica/certificados del cliente antes de produccion.
- Umbrales de discrepancia: pendientes de aprobacion de operaciones/confiabilidad antes de activar validaciones automaticas.
