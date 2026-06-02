# Manual de Recuperacion de Desastres

Este manual es obligatorio para aprobar despliegues de MERO. Si no esta
actualizado o no existe evidencia de prueba de restauracion, el Auditor QA debe
bloquear el despliegue.

## Objetivo

Restaurar la operacion minima de MERO despues de perdida de servicio,
corrupcion de datos, falla de host, error de despliegue o exposicion de
credenciales.

## Alcance

Incluye:

- Servicios Docker definidos en `docker-compose.yml`.
- Base PostgreSQL y respaldos en `./backups`.
- Volumenes `postgres_data`, `prometheus_data` y `grafana_data`.
- Configuracion local `.env`.
- Documentacion operativa en `docs/`.

No incluye recuperacion de infraestructura fisica del cliente, certificados
corporativos ni sistemas externos que alimenten sensores.

## Objetivos de Recuperacion

- RPO inicial: maximo 24 horas, alineado con `BACKUP_INTERVAL_SECONDS=86400`.
- RTO inicial: 4 horas desde disponibilidad de host Docker y respaldo valido.
- Retencion local inicial: 14 dias, alineada con `BACKUP_RETENTION_DAYS=14`.

Estos valores deben ajustarse por contrato si el cliente exige menor perdida de
datos o menor tiempo de interrupcion.

## Criterios de Activacion

Activar este procedimiento si ocurre cualquiera de estos eventos:

- PostgreSQL no inicia o reporta corrupcion.
- Se pierde el volumen `postgres_data`.
- Un despliegue deja API o frontend fuera de servicio y no puede revertirse.
- Se detecta exposicion de secretos en logs, tickets o artefactos.
- El host Docker queda inutilizable y debe reconstruirse.

## Roles

- Comandante de incidente: coordina decisiones y comunicacion.
- Operador de plataforma: ejecuta Docker Compose y restauraciones.
- Administrador de base de datos: selecciona respaldo y valida integridad.
- Auditor QA: verifica checklist, evidencia y ausencia de secretos en logs.
- Responsable del cliente: aprueba reanudacion del servicio.

## Preparacion Requerida

Antes de produccion debe existir:

1. `.env` custodiado fuera del repositorio.
2. Copia segura de `.env.example` en el repositorio.
3. Respaldo PostgreSQL generado por `scripts/postgres-dump.sh`.
4. Prueba documentada de restauracion en ambiente aislado.
5. Inventario de imagenes usadas por `FRONTEND_IMAGE` y `BACKEND_IMAGE`.
6. Acceso operativo a Docker Compose.

## Procedimiento de Recuperacion

1. Declarar incidente y detener cambios no esenciales.
2. Preservar evidencia antes de limpiar logs o volumenes:

```sh
docker compose ps
docker compose logs --since 24h
```

3. Si hay sospecha de secretos expuestos, rotar `POSTGRES_PASSWORD` y
   `GRAFANA_ADMIN_PASSWORD` antes de reabrir acceso.
4. Preparar host con el mismo `docker-compose.yml`, `.env` valido y directorio
   `./backups`.
5. Arrancar solamente PostgreSQL:

```sh
docker compose up -d database
```

6. Restaurar el respaldo seleccionado:

```sh
docker compose exec database pg_restore --clean --if-exists --dbname "$POSTGRES_DB" /backups/NOMBRE_DEL_RESPALDO.dump
```

7. Levantar el resto de servicios:

```sh
docker compose up -d
```

8. Verificar salud:

```sh
docker compose ps
```

9. Confirmar endpoints locales:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

10. Registrar hora de recuperacion, respaldo utilizado y validaciones realizadas.

## Validacion Posterior

El servicio solo puede declararse recuperado si:

- PostgreSQL acepta conexiones.
- Backend responde y expone `/metrics`.
- Prometheus scrapea `mero-backend`.
- Grafana permite acceso con credenciales rotadas o vigentes.
- No aparecen secretos en `docker compose logs`.
- La jerarquia ISO 14224 sigue disponible en la base restaurada.

## Rollback de Despliegue

Si un cambio de imagen causa falla:

1. Restaurar en `.env` los valores previos de `FRONTEND_IMAGE` y `BACKEND_IMAGE`.
2. Ejecutar:

```sh
docker compose pull
docker compose up -d
```

3. Si la falla afecto datos, seguir el procedimiento de recuperacion desde
   respaldo.

## Checklist de Cierre

- [ ] Incidente clasificado y comunicado.
- [ ] Evidencia preservada.
- [ ] Respaldo seleccionado y validado.
- [ ] Restauracion ejecutada.
- [ ] Servicios saludables.
- [ ] Secretos rotados si hubo exposicion.
- [ ] Logs revisados sin credenciales.
- [ ] Cliente aprueba retorno a operacion.
- [ ] Lecciones aprendidas registradas.
