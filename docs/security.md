# Seguridad

Controles base de esta fase:

- Secretos fuera del repositorio mediante `.env`.
- Plantilla `.env.example` sin credenciales reales.
- Red interna Docker para trafico entre servicios.
- Acceso publico limitado a los puertos autorizados por el cliente.
- Deshabilitacion de alta publica de usuarios en Grafana.
- Autenticacion HTTP Basic en endpoints de negocio de la API.
- CORS restringido mediante `CORS_ORIGINS`.
- Redireccion HTTPS configurable mediante `FORCE_HTTPS=true`.

Para produccion on-premise, TLS y cifrado en reposo deben configurarse con certificados y politicas del cliente.
