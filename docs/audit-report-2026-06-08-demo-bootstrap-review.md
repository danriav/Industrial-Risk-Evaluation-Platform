# Auditoria QA - Bloque 8 Demo Bootstrap Y Publicacion GitHub

Fecha: 2026-06-08
Responsable: Agente Auditor Principal / QA Architect
Alcance: bootstrap demo, documentacion GitHub, datos sinteticos, pruebas y controles de publicacion.

## Dictamen

Estado: aprobado con condicion operativa.

Nota de continuidad: este reporte fue superado por
`docs/audit-report-2026-06-08-release-demo-final.md`, donde ya se verifico
Docker live, CI local equivalente y capturas, y se identifico el bloqueo
`QA-REL-001` por vulnerabilidad critica en Vitest.

El Bloque 8 queda apto para portafolio GitHub. El proyecto tiene README actualizado, bootstrap demo reproducible por script, datos sinteticos documentados, pruebas automatizadas y reglas de exclusion para no publicar secretos, respaldos reales ni artefactos binarios de modelo.

Condicion: en esta corrida Docker Desktop no estuvo disponible, por lo que no se pudo repetir la verificacion live de `docker compose` ni el bootstrap contra contenedores. La evidencia documental previa del 2026-06-03 indica que ese flujo fue verificado; antes de etiquetar una release publica conviene repetirlo con Docker activo.

## Evidencia Revisada

- `README.md`
- `.gitignore`
- `scripts/bootstrap-demo.py`
- `docs/demo-data.md`
- `docs/backend-integration.md`
- `tests/test_api.py`
- `tests/test_demo_integration.py`

## Hallazgos

No se encontraron bloqueos de codigo para publicacion como portafolio.

### QA-B8-001: verificacion live no repetida por Docker no disponible

Severidad: baja para GitHub, media para release demostrable.

`docker compose ps` fallo porque Docker Desktop no estaba activo en esta sesion. Esto impide confirmar hoy el flujo completo `docker compose up -d --build` seguido de `python scripts/bootstrap-demo.py`. No invalida el codigo revisado ni las pruebas locales, pero debe repetirse antes de publicar una etiqueta de release.

## Confirmaciones

- `.gitignore` excluye `.env`, `.venv`, caches, `src/web/node_modules`, `src/web/dist`, respaldos, modelos `.joblib`, metricas generadas y datasets reales/procesados.
- `README.md` documenta el flujo demo con `python scripts/bootstrap-demo.py`.
- `scripts/bootstrap-demo.py` genera dataset demo, entrena modelo, aplica migraciones, siembra jerarquia ISO 14224 sintetica y realiza smoke check predictivo.
- `docs/demo-data.md` declara que los datos son sinteticos y no validan pilotos reales.
- `tests/test_api.py` cubre error limpio cuando falta el artefacto de modelo.
- `tests/test_demo_integration.py` existe para validacion live bajo `RUN_DEMO_INTEGRATION=1`.
- Busqueda de secretos no encontro valores reales en archivos rastreables; solo placeholders, ejemplos o construccion runtime de encabezados.

## Pruebas Ejecutadas

- Backend: `.venv/Scripts/python.exe -m pytest`
  - Resultado: `7 passed`, `1 skipped`.
- Frontend: `npm.cmd run test`
  - Resultado: `1 passed`.
- Frontend build: `npm.cmd run build`
  - Resultado: exitoso.

## Riesgos Residuales

- El bootstrap instala dependencias automaticamente por defecto si faltan. Es conveniente usar `--no-auto-install` en entornos controlados o CI.
- El modelo sigue siendo demo sintetico; no aprobado para piloto predictivo real.
- No existe workflow de GitHub Actions todavia para ejecutar pruebas en cada push.
- No se incluyen capturas de pantalla en el repositorio.

## Decision QA

Aprobado para portafolio GitHub con condicion de repetir la verificacion live de Docker cuando el motor este disponible.

No aprobado para produccion ni piloto predictivo real.
