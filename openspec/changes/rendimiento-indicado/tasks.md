## Implementación
- [x] Comprobar estado posterior a rc5; preservar eliminación ajena de redme.txt.
- [x] Función común, históricos/estados y exportaciones derivadas.
- [x] Vista Rendimiento CAE y navegación, gráficos/selección/tabla.
- [x] Resultados individuales y Comparar sin cambiar compatibilidad.
## Comprobación
- [x] Analítica, negativos/invalidación, históricos, fallidos, A/B, CSV y suite.
- [x] Windows real con barridos2T/4T, captura y responsive.
- [x] OpenSpec estricto y revisión puntual.
- [ ] Commit fuente, rc6 limpia, recorrido EXE sin solver y evidencia.
## Pendientes
Aceptación manual final no atribuida. Sin archivar, publicar ni repetir campañas.

17/09/2026: 10 pruebas nuevas aprobadas. Suite inicial269: dos expectativas
desactualizadas (Comparar4T5→7 magnitudes y estado rc5 INACTIVO) corregidas.
Segunda pasada: aserciones aprobadas, un error Windows al eliminar temporal
case.json (WinError5/267) al limpiar test_result_shared_panel_and_project_independence.
Los12tests de workspaces repetidos en aislamiento aprobaron (4,337s), sin cambios
de aplicación por ese incidente. Recorridos Windows visibles automatizados,
no aceptación humana: `E:\MotorSim distribucion\Rendimiento rc6\source-final-100`,
`source-final-125` y `source-final-150`, con gráficos/teclado/tabla/punto/CSV,
fuentes preservadas y ningún worker. Autorrevisión visual de capturas separada;
resumen compactado tras inspección. Sin scroll horizontal global a900×533
lógicos/150 %. Revisión independiente de solo lectura: sin defectos concretos;
10tests aprobados por el revisor. OpenSpec1.3.1 estricto aprobado.
rc6 y su comprobación EXE pendientes al registrar la fuente.

Suite completa final269 aprobada. Corrección visual posterior de contraste de
fila seleccionada y altura del resumen: 10tests afectados aprobados (10,124s),
recorrido Windows125 % repetido en `source-release-125`, sin solver.
