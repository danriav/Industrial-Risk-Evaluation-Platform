# Setup

1. Copiar `.env.example` a `.env`.
2. Reemplazar todas las credenciales `CHANGE_ME`.
3. Confirmar que los puertos permitidos son `3000`, `8080`, `5432`, `9090` y `3001`.
4. Cargar o construir las imagenes definidas en `FRONTEND_IMAGE` y `BACKEND_IMAGE`.
5. Ejecutar:

```sh
docker compose up -d
```

Accesos locales:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
