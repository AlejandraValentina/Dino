## Why
P2 aceptado por la usuaria; P3 debe conectar un volumen homogéneo con un tubo
mediante un flujo conservativo compartido, primero en banco aislado.
## What Changes
Interfaz aislada, contrato de energía/signos, gates P3A/P3B/P3C y evidencia.
Una incompatibilidad de la frontera congelada detiene los gates dependientes.
## Capabilities
### New Capabilities
- `p3-acoplamiento-conservativo`: banco conservativo 0D/1D, condicionado a sus gates.
### Modified Capabilities
Ninguna función pública.
## Impact
Nuevo módulo aislado, pruebas, adaptador dev_orchestrator y documentación.
Sin modificar núcleo P2, producción0D, UI, JSON, escape completo o P4.
