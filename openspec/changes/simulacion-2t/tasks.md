# Tareas de simulacion-2t

## Definición autorizada en esta tarea
- [x] 1. Comprobar Git/código/documentación pertinente y preservar entrega 4 y evidencias.
- [x] 2. Proponer un solo modelo físico, ecuaciones, conductos/transferencias y fuentes primarias.
- [x] 3. Fijar caso sintético completo, datos reutilizados/adicionales y límites de capacidad.
- [x] 4. Definir controles independientes y prueba futura con tolerancias, convergencia y presupuestos previos.
- [x] 5. Revisar puntualmente consistencia documental, validar OpenSpec y actualizar referencias de estado.
- [x] 6. Preparar commit documental propio y registrar publicación pendiente sin reintento de autenticación.

## Pendiente: requiere aprobación y nueva autorización, no ejecutar ahora
- [ ] 7. Obtener aprobación explícita de reducción 0D sin ondas/inercia, transferencias sin almacenamiento y restantes aproximaciones/caso/protocolo de design.md.
- [ ] 8. Obtener autorización de implementación/ejecución del prototipo acotado; no se infiere de esta definición.
- [ ] 9. Tras autorización, implementar y comprobar balances/enlaces/energía con referencias elementales independientes.
- [ ] 10. Tras autorización, ejecutar el caso completo y comparación de resolución, medir coste y registrar convergencia/fallo.

No se detallan aquí integración Qt, nuevos archivos ni entregas posteriores: no
están autorizados. Aprobar documentos no marca tareas 7–10 automáticamente.

## Evidencia de esta definición — 15/09/2026
Inicio main 545685b, árbol limpio y un commit por delante de origin/main.
Commit de entrega 4 conservado; publicación sigue pendiente por autenticación
conocida. No se repite push ni se consultan credenciales. Solo documentos: no
pruebas anteriores repetidas, solver, simulaciones, nuevas capturas o curvas.
Fuentes, caso y protocolo constan únicamente en design.md. Implementación y
aceptación manual previas permanecen separadas e intactas.

- Revisión documental independiente puntual: detectó posible rechazo sistemático
  de etapas RK4 cerca del fin del aporte al integrar F_C. Corregido en el diseño:
  evaluación analítica de F_C en todas las etapas del intervalo cerrado, conversión
  por diferencia analítica, sin recorte/renormalización. No se implementó ni probó
  ese algoritmo; autorrevisión del principal de la aclaración y del diff documental.
- Sustitución aritmética independiente para revisar referencias del documento:
  beta_crit=0.5282817877171742, q_sónico=0.04667117121212454 kg/s y
  q(beta=0.8)=0.038214552836718804 kg/s; volúmenes sintéticos coherentes.
  Esto no es una prueba del motor ni evidencia de viabilidad del solver.
- OpenSpec status/instructions/validate disponibles, sin reinstalar ni init/update.
  Validación estricta aprobada; status completo describe artefactos documentales,
  no implementación. Aprobaciones y tareas futuras 7–10 permanecen sin marcar.
- Solo archivos documentales propios preparados para commit separado. Sin cambio
  de código/tests/JSON, ejecución de suite previa ni nuevo intento de publicación.
