Documento Maestro de Planificación: MERO
1. Resumen ejecutivo
MERO, Motor de Evaluación de Riesgo Operacional, es una plataforma de software industrial predictivo diseñada para anticipar fallas críticas y paros de planta. Utiliza modelos de Machine Learning entrenados con datos históricos de cada planta para calcular probabilidades de riesgo. El sistema se entrega bajo un modelo on-premise mediante contenedores, garantizando la soberanía de los datos de cada cliente, integrando telemetría de sensores con bitácoras humanas de mantenimiento.

2. Constitución del proyecto
Identidad: Plataforma predictiva de mantenimiento industrial.
Modelo de despliegue: On-premise aislado por cliente, orquestado con Docker Compose.
Stack backend: Python, FastAPI.
Stack frontend: React, Tailwind CSS, TypeScript.
Stack datos e IA: PostgreSQL, Scikit-learn, XGBoost, LightGBM, Imbalanced-learn.
Normativas de referencia: ISO 14224 para jerarquía de activos, ISO 55001 para gestión, IEC 62443 para ciberseguridad base.
Prácticas prohibidas: Almacenamiento de credenciales en código, acceso compartido de datos entre distintas empresas, registro de datos crudos de sensores en logs de auditoría sin anonimizar, y mezcla de vistas de sensores con reportes humanos.

3. Especificación funcional
El sistema permite la ingesta manual o por base de datos de registros históricos de operación y mantenimiento.
Incluye un módulo de imputación inteligente para datos faltantes usando KNN.
Permite el entrenamiento y reentrenamiento offline del modelo por parte del usuario final.
Expone una API de inferencia de baja latencia.
Ofrece un dashboard en React con mapas de calor de riesgo operacional y un módulo de bitácora de mantenimiento para el registro de intervenciones reales.

4. Preguntas críticas y respuestas
Estructura de ubicación: Se adopta una jerarquía multinivel, Planta, Línea, Célula, Máquina, basada en ISO 14224.
Ausencia de registros humanos: El sistema mantendrá el último estado y fecha conocidos, emitiendo una alerta visual de revisión vencida, sin alterar el semáforo de riesgo predictivo.
Estandarización de fallas: Se implementa un catálogo predefinido de fallas para alimentar el modelo, dejando las observaciones en texto libre como opcionales.
Discrepancia humano contra sensor: Se mantienen vistas separadas. El mapa de calor muestra la predicción algorítmica y la bitácora muestra la realidad operativa declarada. El sistema no sobreescribe ninguna de las dos.

5. Arquitectura técnica
El sistema opera mediante contenedores aislados que se comunican en una red virtual interna.
API Core: Desarrollada en FastAPI, maneja la validación de peticiones, la interacción con la base de datos y la carga del modelo serializado en memoria para inferencia.
Frontend SPA: Servido mediante Nginx, consume exclusivamente la API REST.
Base de datos: PostgreSQL con configuración de Row Level Security.
Monitoreo: Contenedores dedicados de Prometheus para recolección de métricas y Grafana para visualización del estado del servidor.
Procesos en segundo plano: Un contenedor de tipo cron ejecutará respaldos programados de la base de datos hacia volúmenes locales montados.

6. Estructura del repositorio
mero-project/
├── docker-compose.yml
├── README.md
├── CHANGELOG.md
├── .env.example
├── docs/
├── skills/
├── src/
│   ├── api/
│   ├── web/
│   ├── ml/
│   └── db/
└── scripts/

7. Matriz de dependencias
El esquema de base de datos ISO 14224 alimenta al módulo de Machine Learning para estructurar las variables categóricas.
El pipeline de Machine Learning exporta el modelo serializado, el cual es dependencia estricta para que la API Core pueda inicializar el endpoint de inferencia.
Los contratos OpenAPI generados por la API Core son dependencia estricta para el desarrollo de los servicios HTTP en el Frontend React.
El archivo de orquestación base alimenta a todos los módulos al definir los puertos y redes internas.

8. Secuencia de sprints o bloques
Bloque 1: Fundación del repositorio. Setup de Docker y estructura base.
Bloque 2: Diseño de datos y normativa. Migraciones de PostgreSQL basadas en ISO 14224.
Bloque 3: Pipeline de IA. Limpieza, imputación y entrenamiento offline.
Bloque 4: Desarrollo de Core API. Endpoints REST y carga de modelo.
Bloque 5: Desarrollo de Interfaz Gráfica. Dashboard, mapas de calor y bitácora.
Bloque 6: Integración de Monitoreo y Respaldos. Configuración de Prometheus, Grafana y cron.

9. Agentes definidos
Agente Orquestador Base: Staff DevOps Engineer. Responsable de la infraestructura Docker, variables de entorno y orquestación de monitoreo.
Agente de Datos y ML: Senior Data Scientist. Responsable de esquemas relacionales, limpieza de datos y entrenamiento de Random Forest.
Agente Producto / Industrial Reliability SME: Especialista en mantenimiento industrial, confiabilidad, RCM/TPM, operacion de activos y lectura de bitacoras reales. Responsable de definir etiquetas low, medium y high por clase de equipo, validar etiquetas historicas con mantenimiento, decidir ventanas de riesgo, aprobar umbrales por clase de equipo, priorizar activos criticos del piloto y bloquear el entrenamiento o aprobacion de modelos reales si no existen reglas de etiquetado firmadas.
Agente Backend: Senior Python Developer. Responsable de FastAPI, contratos REST y seguridad en tránsito.
Agente Frontend: Senior Frontend Engineer / Industrial UX Developer. Responsable de construir la SPA React en TypeScript, consumir los contratos OpenAPI del Backend, diseñar el dashboard operativo, el mapa de calor de riesgo y la bitácora de mantenimiento sin mezclar predicciones algorítmicas con declaraciones humanas.
Agente Auditor Principal: QA Architect. Responsable de revisar el código transversal, asegurar la documentación y bloquear pases a producción si existen vulnerabilidades.

10. Skills portables
Se define la skill validate-iso14224-schema. Su propósito es auditar que el diseño relacional propuesto contenga al menos cuatro niveles anidables lógicos antes de permitir la programación de la API. Se ubicará en la carpeta skills/validate-iso14224-schema/SKILL.md.

11. Documentación profesional requerida
El proyecto exige la creación y mantenimiento estricto de los siguientes documentos. architecture.md, setup.md, development-guide.md, api.md, database.md, maintenance.md y agent-memory.md. Ningún bloque de desarrollo se considera terminado si su respectiva documentación no ha sido actualizada.

12. README propuesto
Debe contener el título del proyecto MERO, una descripción orientada a la ingeniería de confiabilidad, los prerrequisitos de hardware local, las instrucciones paso a paso para ejecutar docker-compose up, la explicación de las variables del archivo de entorno y una guía rápida para acceder a los tableros de Grafana y al dashboard principal.

13. Estructura de la carpeta docs
docs/
├── architecture.md
├── setup.md
├── development-guide.md
├── api.md
├── database.md
├── security.md
├── maintenance.md
└── agent-memory.md

14. Estrategia de seguridad
Se requiere cifrado TLS para comunicaciones en tránsito y cifrado AES-256 en reposo.
Las contraseñas de usuarios administradores y operadores deben estar hasheadas mediante algoritmos robustos como Argon2.
La API debe validar estrictamente los tipos de datos de entrada mediante Pydantic para prevenir inyecciones.
Las instancias deben desplegarse en redes locales sin exposición a internet público a menos que medie una VPN corporativa.

15. Estrategia de testing
Pruebas unitarias para las funciones de limpieza e imputación de datos.
Pruebas de integración para validar la conexión entre FastAPI y PostgreSQL.
Pruebas de carga preliminares en el endpoint de inferencia para asegurar tiempos de respuesta inferiores a 200 milisegundos.
Ejecución automatizada de pruebas mediante GitHub Actions o GitLab CI en el repositorio fuente.

16. Estrategia de despliegue
Entrega al cliente de un paquete comprimido o acceso a un repositorio que contenga el archivo de orquestación y las imágenes precompiladas. El cliente ejecuta los contenedores en su servidor local o nube privada. No existe arquitectura multi-tenant en servidor central, sino una instancia completa y aislada por empresa.

17. Estrategia de mantenimiento
Los respaldos de base de datos se ejecutan de forma automatizada y se alojan en un volumen local. El manual de mantenimiento detallará el procedimiento para restaurar un respaldo específico usando comandos nativos de PostgreSQL dentro del contenedor. Las actualizaciones del software se realizarán sustituyendo las imágenes de los contenedores por versiones más recientes y reiniciando la orquestación.

18. Documento de memoria para agentes
Debe incluir el resumen del objetivo predictivo, la decisión inamovible de separar visual y conceptualmente los datos del sensor de los registros del operario, la adherencia a la ISO 14224 y la prohibición de registrar datos sensibles en los logs. Servirá de contexto base para cualquier herramienta de IA que asista en futuras implementaciones.

19. Riesgos restantes
Sesgo de confirmación humano al registrar datos en la bitácora estando influenciado por las alertas del sensor.
Escasez inicial de datos históricos en plantas nuevas que pueda provocar un rendimiento predictivo bajo durante los primeros meses de operación.

20. Próximos pasos
El equipo de desarrollo o el sistema de agentes autónomos debe iniciar la ejecución técnica activando al Agente Orquestador Base para construir la Fase 1 del código fuente, estructurando los repositorios y sentando las bases del contenedor de FastAPI.
