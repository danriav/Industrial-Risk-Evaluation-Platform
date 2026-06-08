# Auditoria QA - Release Demo GitHub

Fecha: 2026-06-08
Responsable: Agente Auditor Principal / QA Architect
Alcance: CI, bootstrap live, capturas, secretos y dictamen de release demo para GitHub/portafolio.

## Dictamen

Estado: aprobado localmente; pendiente de validacion remota de CI para release demo publica.

El proyecto esta funcional para demo local y portafolio en rama de trabajo. El bloqueo QA-REL-001 por vulnerabilidad critica en `vitest < 3.2.6` fue corregido por Frontend/Orquestador actualizando `vitest` a `^3.2.6` y validando `npm audit` sin vulnerabilidades.

## Hallazgos

### QA-REL-001: vulnerabilidad critica en Vitest

Estado: corregido por Frontend/Orquestador.

Severidad original: alta para publicacion GitHub.

La auditoria original reporto `GHSA-5xrq-8626-4rwp`, con severidad `critical`, para `vitest` en rango `<3.2.6`. El paquete estaba declarado en `src/web/package.json` como `^3.0.0`.

Riesgo: aunque Vitest se usa para pruebas y no forma parte del runtime del frontend servido por Nginx, un repositorio publico con una vulnerabilidad critica conocida queda marcado por alertas de seguridad y no debe etiquetarse como release demo apta hasta actualizar la dependencia.

Accion requerida:

- `vitest` actualizado a `^3.2.6`.
- `src/web/package-lock.json` regenerado.
- `npm audit`: `found 0 vulnerabilities`.
- `npm run test`: aprobado con Vitest 3.2.6.
- `npm run build`: aprobado.

## Confirmaciones Aprobadas

- Workflows presentes:
  - `.github/workflows/backend-ci.yml`
  - `.github/workflows/frontend-ci.yml`
- Backend local: `7 passed`, `1 skipped`.
- Frontend local:
  - `npm ci`: paso.
  - `npm audit`: `found 0 vulnerabilities`.
  - `npm run test`: `1 passed`.
  - `npm run build`: aprobado.
- Bootstrap live:
  - `docker compose up -d --build`: aprobado.
  - `scripts/bootstrap-demo.py --restart-backend`: aprobado.
  - Smoke check predictivo: `risk_label=medium`, `model_version=random_forest`, `feature_count=8`.
- Integracion live:
  - `RUN_DEMO_INTEGRATION=1 pytest tests/test_demo_integration.py`: `1 passed`.
- Capturas:
  - `docs/assets/dashboard.png`
  - `docs/assets/heatmap.png`
  - `docs/assets/maintenance-log.png`
  - `docs/assets/api-docs.png`
  - `docs/assets/grafana.png`
- Las capturas no muestran passwords, tokens, connection strings ni credenciales crudas.
- `git check-ignore` confirma exclusion de `.env`, modelos generados, metricas generadas, backups, `dist`, `node_modules` y datasets reales/procesados.
- Busqueda de secretos en archivos rastreables: sin credenciales reales detectadas.

## Condiciones Para Aprobar Release Demo

1. Confirmar workflows remotos de GitHub Actions en verde sobre el commit final.
2. Repetir checklist de secretos antes de push/tag.

## Decision QA

QA-REL-001 queda corregido localmente.

La release demo queda aprobada localmente para push a GitHub.

Condicion final: verificar que GitHub Actions remotas queden en verde sobre el
commit publicado antes de crear tag o marcar la release como final.
