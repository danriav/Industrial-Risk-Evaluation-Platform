---
name: validate-iso14224-schema
description: Valida que el esquema de base de datos propuesto para los activos industriales cumpla con la jerarquía multinivel estándar (Planta, Línea, Célula, Equipo) antes de su implementación.
---

# Propósito

Garantizar que la estructura de datos soporte la escalabilidad en diferentes corporaciones industriales manteniendo consistencia global.

# Cuándo usar esta skill

Debe usarse inmediatamente después de que el Agente de Datos genere el esquema SQL inicial de activos y ubicaciones, y antes de programar la API.

# Entradas requeridas

Archivo de esquema de base de datos (por ejemplo schema.sql o modelos de SQLAlchemy).
Documentación de requerimientos de la Fase 3.

# Instrucciones de ejecución

1. Leer el archivo de definición de tablas de activos.
2. Verificar que existan tablas o relaciones jerárquicas con al menos 4 niveles lógicos.
3. Comprobar que el diseño permite relacionar observaciones y catálogos de falla al nivel más granular de la jerarquía (la máquina o equipo).
4. Validar la existencia de campos para registrar el último estado conocido y fecha de actualización.

# Evidencia esperada

Reporte de validación indicando si el esquema cumple o listando las correcciones necesarias.

# Criterios de aceptación

El esquema refleja una topología industrial anidable.
Cada activo tiene una referencia clara a su ubicación padre.

# Condiciones de bloqueo

Falla si el esquema propuesto es plano o carece de relación jerárquica estricta.

# Seguridad y cumplimiento

Asegurar que los identificadores de empresa (tenant_id) estén presentes en las tablas raíz para mantener aislamiento.