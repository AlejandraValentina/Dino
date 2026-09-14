# Tareas de configuracion-2t

- [x] 1. Comprobar continuidad y documentar/validar este único cambio y convenciones.
- [x] 2. Implementar filas/cárter opcionales y JSON v3 compatible con v1/v2.
- [x] 3. Implementar cruce acotado, áreas y dependencias reutilizando cinemática.
- [x] 4. Integrar editor 2T, selección, gráfico, edición pendiente y conservación en 4T.
- [x] 5. Probar caso sintético independiente, límites, actualización, persistencia y regresiones.
- [x] 6. Comprobar Windows cuando esté disponible y hacer revisión puntual; registrar evidencia y captura.
- [x] 7. Actualizar README/hoja, preparar commit separado y publicación sin reintentos de autenticación.
- [ ] 8. Definir y autorizar el tramo de admisión dentro de esta entrega (pendiente de decisión de la usuaria; no implementar ahora).

## Evidencia del primer tramo — 14/09/2026

- Inicio en main 5cc7e50, árbol limpio. Aceptación manual de entregas 1/2 y prueba
  sin Internet declaradas por la usuaria conservadas; no se reinterpretan.
- Único cambio configuracion-2t, especificación/diseño y validación estricta
  aprobada. Integración y configuración global intactas; ninguna dependencia nueva.
- Datos incompletos, borradores inválidos, filas individuales, cárter, referencia
  JSON v3 y lectura v1/v2 implementados. Posición del pistón y gráfico reutilizados.
- Suite completa de 58 pruebas aprobada. Revisión independiente de solo lectura:
  detectó subdesbordamiento de área positiva a cero; corregido con error de rango
  que retira áreas conservando eventos. Después, 9 pruebas focalizadas de lumbreras
  (incluida la nueva regresión) y 30 de widgets Windows aprobadas. Colección: 59 tests.
  Autorrevisión del principal de corrección y documentación, sin campaña adicional.
- Caso sintético esperado 90°/270°/180°/200 mm² contrastado con valores dados por
  la usuaria, sin generarlos mediante la función probada. Parcial, nunca abierta,
  ausencia, invalidación, persistencia/eliminación y cambio 2T/4T cubiertos.
- Captura real Windows inspeccionada: docs/images/motorsim-configuracion-2t.png,
  datos identificados como sintéticos, ventana 1080×791. También inspeccionado
  escalado 150 % y disposición apilada, sin desplazamiento horizontal.
  Pruebas automatizadas y captura no constituyen aceptación manual del tramo.
- Pendiente de producto: admisión (tarea 8). Entrega 3 En curso, no completada.
  No se archiva ni se desarrolla entrega 4, conductos o simulador. Archivos propios
  revisados y preparados para commit separado; publicación solo por push normal
  si la autenticación disponible lo permite.
