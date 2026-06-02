# Arquitectura

MERO se despliega como una instancia on-premise aislada por cliente mediante Docker Compose.

Servicios base:

- `frontend`: SPA servida en el puerto autorizado `3000`.
- `backend`: API Core expuesta en el puerto autorizado `8080`.
- `database`: PostgreSQL expuesto en el puerto autorizado `5432`.
- `prometheus`: recoleccion de metricas en el puerto autorizado `9090`.
- `grafana`: tablero operacional en el puerto autorizado `3001`.
- `db-backup`: proceso automatizado de respaldo sin exposicion de puerto.
- `postgres-exporter`: exportador interno de metricas PostgreSQL sin puerto publicado al host.

La red `mero_internal` aisla la comunicacion entre servicios. La red `mero_public` solo se asigna a servicios que requieren acceso desde el host local.

Prometheus carga reglas desde `monitoring/alert_rules.yml` y recolecta metricas de `backend:8080`, `prometheus:9090` y `postgres-exporter:9187`. Grafana se provisiona automaticamente con la fuente Prometheus y el tablero `MERO Platform Overview`.
