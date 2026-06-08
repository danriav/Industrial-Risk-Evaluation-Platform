# Dataset Demo Sintetico

Estado: datos sinteticos para demostracion tecnica. No son datos reales de cliente.

## Alcance

`scripts/bootstrap-demo.py` siembra una jerarquia ISO 14224 demo con:

- 2 plantas.
- 3 lineas.
- 4 celulas.
- 8 equipos.
- 6 observaciones recientes de sensores.
- 2 equipos sin sensor reciente para probar estados parciales del dashboard.
- Catalogo inicial de fallas predefinidas.
- Bitacoras humanas sinteticas para mantener separada la realidad operativa declarada.

## Jerarquia

| Planta | Linea | Celula | Equipo | Clase | Sensor demo |
| --- | --- | --- | --- | --- | --- |
| PLT-01 | LN-01 | CELL-01 | PUMP-01 | centrifugal_pump | Si |
| PLT-01 | LN-01 | CELL-01 | PUMP-02 | centrifugal_pump | Si |
| PLT-01 | LN-01 | CELL-02 | COMP-01 | compressor | Si |
| PLT-01 | LN-01 | CELL-02 | COMP-02 | compressor | Si |
| PLT-01 | LN-02 | CELL-03 | CONV-01 | conveyor | Si |
| PLT-01 | LN-02 | CELL-03 | CONV-02 | conveyor | No |
| PLT-02 | LN-03 | CELL-04 | MIX-01 | mixer | Si |
| PLT-02 | LN-03 | CELL-04 | MIX-02 | mixer | No |

## Cobertura Esperada Del Mapa

Las observaciones fueron elegidas para que el modelo demo produzca al menos un caso `low`, uno `medium` y uno `high`. La prediccion exacta puede variar si se reentrena el modelo, pero el bootstrap mantiene lecturas claramente separadas:

- `low`: lecturas estables, sensor `good`, carga moderada.
- `medium`: temperatura/carga elevadas o sensor `degraded`.
- `high`: vibracion, presion, temperatura o carga en rango severo.

Verificacion local del bootstrap actual:

| Equipo | Riesgo demo |
| --- | --- |
| COMP-01 | high |
| COMP-02 | low |
| CONV-01 | low |
| MIX-01 | medium |
| PUMP-01 | medium |
| PUMP-02 | low |
| CONV-02 | sin sensor |
| MIX-02 | sin sensor |

## Catalogo De Fallas

| Codigo | Categoria | Modo |
| --- | --- | --- |
| BRG_OVERHEAT | mechanical | bearing_overheating |
| SEAL_LEAK | process | seal_leakage |
| MISALIGNMENT | mechanical | shaft_misalignment |
| HIGH_VIBRATION | mechanical | excessive_vibration |
| MOTOR_OVERLOAD | electrical | motor_overload |
| SENSOR_FAULT | instrumentation | sensor_signal_fault |

## Nota De Uso

Estos datos existen solo para validar integracion, visualizacion, manejo de estados parciales y humo del endpoint predictivo. No deben usarse para aprobar pilotos reales ni para inferir comportamiento de maquinaria real.
