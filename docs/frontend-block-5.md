# Frontend Bloque 5

Fecha de verificacion: 2026-05-22

## Alcance implementado

- SPA React/TypeScript en `src/web`.
- Dashboard operativo como primera pantalla.
- Mapa de calor de riesgo predictivo por planta, linea, celula y equipo.
- Panel de prediccion algoritmica separado de la bitacora humana.
- Vista separada de bitacora de mantenimiento humana con formulario de alta.
- Cliente HTTP con autenticacion Basic compatible con `/api/v1`.
- Estados de carga, error, vacio y datos parciales.

## Contrato API utilizado

La implementacion consume exclusivamente endpoints documentados en
`docs/openapi.json`:

- `GET /api/v1/assets/hierarchy`
- `GET /api/v1/sensor-observations`
- `POST /api/v1/predictions/risk`
- `GET /api/v1/maintenance-logs`
- `POST /api/v1/maintenance-logs`
- `GET /api/v1/failure-catalog`

No se crearon endpoints nuevos ni se modificaron contratos Backend.

## Ejecucion local

```powershell
cd src/web
npm install
npm run dev
```

La aplicacion usa el puerto autorizado `3000`. La API por defecto es
`http://localhost:8080`; para otro host usar `VITE_API_BASE_URL`.

## Verificacion minima

```powershell
cd src/web
npm run build
```

Resultado observado:

- TypeScript compila con `tsc --noEmit`.
- Vite genera `dist/` sin errores.
- Verificacion visual en `http://127.0.0.1:3000/` confirma titulo
  `MERO Riesgo Operacional`, dashboard inicial, tab de bitacora humana y estado
  de autenticacion requerida.

## Verificacion 2026-05-23

Cambios adicionales:

- Credenciales Basic mantenidas solo en memoria React; no se persiste password
  en `sessionStorage` ni `localStorage`.
- `.gitignore` excluye `src/web/node_modules/` y `src/web/dist/`.
- Mapa de calor muestra leyenda visual para `low`, `medium`, `high`, `Sin
  sensor` y `Modelo no disponible`.
- Cada equipo distingue estado `Sin sensor` de `Modelo no disponible` sin
  mezclarlo con bitacora humana.
- Smoke test frontend agregado en `src/web/src/main.test.tsx`.

Pruebas ejecutadas:

```powershell
cd src/web
npm run test
npm run build
```

Resultado:

- `npm run test`: 1 archivo, 1 prueba aprobada. Verifica render del dashboard y
  que las credenciales Basic no queden persistidas.
- `npm run build`: `tsc --noEmit && vite build` aprobado.

Flujo real `frontend -> backend -> modelo` con `PUMP-01`:

- `GET /health`: 200.
- `GET /api/v1/assets/hierarchy`: `PUMP-01` encontrado como
  `centrifugal_pump`.
- `GET /api/v1/sensor-observations?equipment_id=<PUMP-01>&limit=1`: lectura
  disponible con `sensor_quality=good`.
- `POST /api/v1/predictions/risk`: respuesta `risk_label=medium`,
  `risk_score=0.5779701323414302`, `model_version=random_forest`,
  `feature_count=8`.

Verificacion visual en `http://127.0.0.1:3000/`:

- El mapa de calor renderiza `PUMP-01` como `58% medium`.
- La leyenda visual muestra `low`, `medium`, `high`, `Sin sensor` y `Modelo no
  disponible`.
- Limitacion encontrada: el backend actual devuelve solo un activo real
  (`PUMP-01`), por lo que no existen activos reales `low` ni `high` para
  confirmar visualmente tres tarjetas de equipo sin crear datos fuera del
  contrato o modificar la base.
