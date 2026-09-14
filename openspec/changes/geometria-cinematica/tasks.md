# Tareas de geometria-cinematica

- [x] 1. Comprobar registro/publicación de entrega 1, preservar pendientes y validar este único cambio.
- [x] 2. Implementar cálculos directos y dependencias por resultado; contrastar caso independiente.
- [x] 3. Añadir pestaña, esquema y curvas Qt con actualización y teclado.
- [x] 4. Ejecutar regresiones de datos, archivos y cambios pendientes, y pruebas de geometría.
- [ ] 5. Inspeccionar pestaña Windows y escalado, conservar captura real y hacer revisión puntual.
- [x] 6. Actualizar README y estado y preparar archivos revisados para registro/publicación separados. Detenerse sin archivar.

## Evidencia

- Entrega 1 encontrada ya registrada y publicada: 040e789, main y origin/main
  iguales tras fetch, árbol limpio. Sin commit vacío ni reescritura. No hay
  entornos, cachés, credenciales o archivos personales en el conjunto versionado.
- Cálculo directo y Qt Widgets sin dependencias nuevas. JSON v2 y lectura v1
  conservados. 47 pruebas automáticas aprobadas; 27 de widgets con plataforma
  Windows aprobadas. pip check correcto. OpenSpec apply disponible y validación
  estricta aprobada. Contraste independiente mediante triángulo 3-4-5 a 90°.
- Revisión independiente puntual: se corrigió que Vd dependiera de compresión;
  nuevo test confirma independencia con compresión vacía e inválida. Autorrevisión
  del principal para la corrección y documentación, sin campaña adicional.
- Tarea 5 incompleta: escritorio devuelve imagen azul uniforme; LogonUI activo.
  Solo se pudo inspeccionar renderizado Qt Windows normal/150 %, que no equivale
  a captura real. Pasos pendientes concretos en README, sección Geometría.
  La automatización no acredita el recorrido manual histórico de entrega 1.
- Estado: Por verificar. No se archiva ningún cambio ni se comienza entrega 3.
