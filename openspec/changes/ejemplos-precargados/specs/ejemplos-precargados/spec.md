## ADDED Requirements
### Requirement: Ejemplos canónicos identificados
El sistema SHALL ofrecer 2T referencia, 2T compresión8.2, 4T referencia y 4T
compresión8.2, derivados de las referencias canónicas. SHALL identificar nombre
y observaciones con “EJEMPLO SINTÉTICO — NO MEDIDO”. La única diferencia física
de cada variante SHALL ser compresión8.0 a8.2, sin modificar referencias.
#### Scenario: Seleccionar variante
- **WHEN** se carga una variante8.2
- **THEN** conserva todos los otros datos de su referencia y no incluye resultados.
### Requirement: Carga protegida y editable
Archivo → Cargar ejemplo SHALL reutilizar Guardar/Descartar/Cancelar ante cambios
pendientes. La carga confirmada SHALL crear proyecto editable dirty=True, path=None;
Guardar SHALL solicitar destino nuevo. SHALL preparar simulación del proyecto real
y navegación del ciclo cargado, sin sobrescribir archivos incluidos.
#### Scenario: Cancelar transición
- **WHEN** se cancela la confirmación o el guardado previo
- **THEN** conserva proyecto, ruta, cambios y selección actuales.
### Requirement: Distribución autónoma
Los ejemplos SHALL generarse determinísticamente sin red, repositorio ni cwd.
rc4 SHALL conservar rc3 y acreditar pruebas, revisión y recorrido Windows,
sin campañas físicas ni aceptación manual atribuida.
#### Scenario: EXE extraído
- **WHEN** se carga un ejemplo desde la aplicación distribuida
- **THEN** permite editar/guardar y consultar resultados existentes independientemente del repositorio.
