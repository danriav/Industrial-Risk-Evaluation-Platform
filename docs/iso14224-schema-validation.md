# Validacion ISO 14224

Archivo revisado: `src/db/migrations/001_iso14224_assets.sql`.

Resultado: cumple.

Evidencia:

- La jerarquia contiene cuatro niveles logicos estrictos: `plants`, `production_lines`, `cells`, `equipment`.
- Cada nivel tiene referencia clara a su padre: lineas a planta, celulas a linea y equipos a celula.
- `plants` incluye `tenant_id` para aislamiento por empresa desde la raiz operativa.
- `sensor_observations`, `maintenance_logs` y `failure_catalog` se relacionan al nivel de maquina/equipo.
- Los niveles operativos registran `last_known_state` y `last_state_updated_at`.

Condicion pendiente:

- La tabla `discrepancy_thresholds` existe, pero debe poblarse con umbrales aprobados antes de activar validaciones de inconsistencias de maquinaria.
