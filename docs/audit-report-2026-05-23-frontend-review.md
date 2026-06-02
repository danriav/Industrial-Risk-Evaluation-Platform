# Reporte de Auditoria QA Frontend

Fecha: 2026-05-23  
Auditor: Agente Auditor Principal / QA Architect  
Alcance: revision del Bloque 5 Frontend, contrato Backend/ML, build React y
estado de secuencia.

## Resultado Ejecutivo

Estado: implementado, no aprobado aun para liberar Bloque 6.

El frontend ya existe y cubre la experiencia principal: dashboard, mapa de calor
predictivo, panel algoritmico y bitacora humana separada. El siguiente turno no
es iniciar Frontend, sino que el Agente Frontend cierre hallazgos QA antes de
pasar a integracion operacional.

## Evidencia Revisada

- `src/web/src/main.tsx`
- `src/web/package.json`
- `src/web/README.md`
- `src/web/Dockerfile`
- `src/web/dist/`
- `docs/frontend-block-5.md`
- `docs/backend-integration.md`
- `src/api/ml.py`
- `tests/test_api.py`

## Verificaciones Ejecutadas

- Backend API: `GET http://127.0.0.1:8080/health` respondio `200`.
- Backend tests: `python -m pytest` -> 6 passed, 1 warning.
- Frontend build: `npm run build` -> TypeScript y Vite completaron sin errores.
- Frontend preview: `http://127.0.0.1:4173/` respondio `200`.
- Modelo/API: `src/api/ml.py` normaliza `normal/warning/critical` a
  `low/medium/high`.

## Validacion Contra Checklist Solicitado

### Validar dashboard con PUMP-01 y demas activos

Estado: parcial.

El frontend consume jerarquia, sensores, bitacora y predicciones desde la API.
`docs/backend-integration.md` registra que `PUMP-01` responde `risk_label: low`
en Backend. Falta evidencia de prueba visual/E2E donde el dashboard renderice
`PUMP-01` desde la base real.

### Confirmar mapa de calor low, medium, high

Estado: implementado.

`RiskHeatMap` usa `riskClass` y `riskLabel` para renderizar `low`, `medium`,
`high` y `unknown`.

### Revisar manejo de errores cuando no hay sensores/modelo

Estado: parcial.

El frontend marca `no-sensor` y `prediction-unavailable`, y muestra aviso de
datos parciales. Falta diferenciar visualmente por equipo la causa exacta para
que operaciones entienda si el problema es falta de sensor o modelo no
disponible.

### Ajustar bitacora humana sin mezclarla con riesgo algoritmico

Estado: implementado.

La bitacora humana esta en una pestana separada y el panel algoritmico se
presenta como `Prediccion algoritmica`.

### Probar flujo completo frontend -> backend -> modelo

Estado: pendiente.

Se verificaron backend, build y preview, pero falta una prueba documentada con
credenciales de integracion que cargue el dashboard, consulte activos reales,
ejecute `/api/v1/predictions/risk` y muestre el resultado en UI.

## Hallazgos QA

### QA-FE-001: prueba E2E del flujo completo pendiente

Riesgo: el build puede pasar aunque la experiencia real no muestre activos,
sensores o predicciones por un problema de credenciales, CORS, datos o contrato.

Accion requerida: documentar evidencia de flujo con `PUMP-01` y al menos un
activo por cada nivel de riesgo `low`, `medium`, `high`.

### QA-FE-002: estado de error por equipo poco especifico

Riesgo: equipos sin sensor y equipos con modelo caido se ven demasiado parecidos
para operacion.

Accion requerida: mostrar en cada celda del mapa de calor si esta `sin sensor`,
`modelo no disponible` o `prediccion OK`.

### QA-FE-003: credenciales Basic persistidas en `sessionStorage`

Riesgo: una credencial Basic queda accesible desde almacenamiento del navegador
durante la sesion.

Accion requerida: mantener password en memoria o sustituir por un mecanismo
aprobado por seguridad antes de produccion.

### QA-FE-004: artefactos frontend no ignorados

Riesgo: `src/web/node_modules` y `src/web/dist` pueden terminar en entregables o
control de versiones.

Accion requerida: agregar `src/web/node_modules/` y `src/web/dist/` a
`.gitignore`.

### QA-FE-005: falta prueba automatizada minima del frontend

Riesgo: cambios de UI o cliente HTTP pueden romper el dashboard sin alerta.

Accion requerida: agregar verificacion automatizada minima o script de smoke
test del frontend.

## Decision QA

Bloque 5 Frontend: implementado, auditado con condiciones.  
Siguiente turno: Agente Frontend corrige hallazgos QA-FE-001 a QA-FE-005.  
Bloque 6: bloqueado hasta reauditoria Frontend.
