# Frontend MERO

SPA React/TypeScript para el bloque 5 del dashboard de riesgo operacional.

## Ejecutar local

```powershell
cd src/web
npm install
npm run dev
```

El frontend usa el puerto autorizado `3000`. La API por defecto es
`http://localhost:8080`; puede cambiarse con `VITE_API_BASE_URL`.

## Verificacion minima

```powershell
cd src/web
npm run build
npm run test
```

La aplicacion consume solo endpoints documentados en `docs/openapi.json` y
mantiene separadas las vistas de prediccion/sensores y bitacora humana.
