## Why
Actualización del 15/09/2026: la usuaria aprobó el modelo, caso y protocolo y
autorizó implementar/ejecutar el prototipo de consola, conservando sus límites.
El alcance documental original siguiente queda como antecedente. La ampliación
afecta solo núcleo estándar, caso sintético separado, pruebas y evidencia;
no Qt, JSON v5, dependencias, ondas, barridos ni entrega 6.

Definir el primer caso 2T y su prueba de viabilidad antes del núcleo. La entrega 5
está En curso: definición del primer caso; hoy solo se autoriza documentación.
Se preservan el editor de conductos, JSON v5 y commit 545685b aunque no esté publicado.

## What Changes
- Un modelo recomendado, caso sintético y experimento acotado, concentrados en design.md.
- Balances abiertos en cuatro volúmenes homogéneos, flujo reversible por restricciones
  y energía prescrita: no se sustituye el intercambio de gases por un ciclo cerrado.
- Se propone diferir inercia y ondas de conductos. Es una reducción de capacidad
  que requiere aprobación explícita; no permite estudiar sintonía del escape.
- Requisitos observables del futuro prototipo, condicionales a aprobación del modelo
  y autorización de implementación; tareas documentales separadas del prototipo.

## Capabilities
### New Capabilities
- `simulacion-2t`: definición del primer caso termodinámico abierto y de su viabilidad.
### Modified Capabilities
Ninguna consolidada. Las entregas anteriores conservan requisitos y evidencias.

## Impact
Solo documentos de este cambio y referencias de estado en AGENTS/README/hoja/config
local OpenSpec. Sin solver, interfaz, dependencias, versión JSON ni ejecución física.
No se prometen ondas, potencia al eje, consumo, emisiones, detonación ni predicción
experimental. No se importa solver anterior, arquitectura de redes o entrega 6.
