# Memoria de Agentes

MERO es una plataforma predictiva de mantenimiento industrial para despliegues on-premise aislados por cliente.

Decisiones inamovibles:

- Separar visual y conceptualmente datos de sensores y registros humanos de operador.
- Alinear la jerarquia de activos con ISO 14224.
- No registrar datos sensibles ni datos crudos de sensores en logs.
- No compartir datos entre empresas o instalaciones.
- Mantener las credenciales fuera del codigo y del repositorio.
- No entrenar ni aprobar modelo real sin reglas de etiquetado firmadas por el
  Agente Producto / Industrial Reliability SME y por mantenimiento del cliente.

Puertos autorizados por el cliente:

- Frontend: `3000`
- Backend: `8080`
- Base de datos: `5432`
- Prometheus: `9090`
- Grafana: `3001`
