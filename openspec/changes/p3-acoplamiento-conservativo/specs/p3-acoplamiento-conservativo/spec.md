## ADDED Requirements
### Requirement: Aceptación y núcleo congelado
P3 SHALL registrar P2_HUMAN_ACCEPTED y preservar hashes del núcleo y contratos.
#### Scenario: Cambio del núcleo
- **WHEN** una incompatibilidad exige modificar una frontera verificada
- **THEN** detiene SCIENTIFIC_CHANGE_REQUIRED sin cambiarla silenciosamente.
### Requirement: Flujo compartido y energía compatible
La interfaz SHALL evaluar un único flujoEuler por stage y aplicar signos opuestos
a masa, energía y especie. SHALL registrar impulso sin momentum0D.
#### Scenario: Backflow
- **WHEN** cambia el signo del flujo
- **THEN** usa especie y entalpía total del donante actual, sin deadband ni clipping.
### Requirement: Gates internos y cierre
P3 SHALL ejecutar P3A antes de volumen finito y volumen fijo antes de variable,
con C01–C12, regresionesP0/P2 y revisión independiente.
#### Scenario: Bloqueo científico
- **WHEN** no existe rama consistente bajo el contrato congelado
- **THEN** conserva evidencia, marca gates dependientes pendientes y no iniciaP4.
