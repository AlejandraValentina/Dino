## Implementación
- [x] Comprobar estado posterior a rc5; preservar eliminación ajena de redme.txt.
- [x] Función común, históricos/estados y exportaciones derivadas.
- [x] Vista Rendimiento CAE y navegación, gráficos/selección/tabla.
- [x] Resultados individuales y Comparar sin cambiar compatibilidad.
## Comprobación
- [x] Analítica, negativos/invalidación, históricos, fallidos, A/B, CSV y suite.
- [x] Windows real con barridos2T/4T, captura y responsive.
- [x] OpenSpec estricto y revisión puntual.
- [x] Commit fuente, rc6 limpia, recorrido EXE sin solver y evidencia.
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
rc6 y su comprobación EXE estaban pendientes al registrar la fuente; acreditadas abajo.

Suite completa final269 aprobada. Corrección visual posterior de contraste de
fila seleccionada y altura del resumen: 10tests afectados aprobados (10,124s),
recorrido Windows125 % repetido en `source-release-125`, sin solver.

## Evidencia de candidata (17/09/2026)
Fuente `799b7d6f9bf6b0061bd9a1de60af682e8061630a`, checkout limpio separado
para preservar eliminación ajena de redme.txt en main. Suite269/54,860s aprobada.
Receta existente Python3.11.0, Qt6.11.2, PyInstaller6.22.3. rc6 extraída en
`E:\MotorSim distribucion\Candidata Rendimiento 0.1.0-rc6\MotorSim`.
ZIP `dist/MotorSim-0.1.0-rc6-windows-x64-799b7d6f.zip`,43.440.060bytes;
SHA256 `0b5d8eaa46a5c82ff2ae82305ed5846467197c4c53b58ff80ef2198dd93e2db1`.
162archivos/104.938.807bytes idénticos al ZIP después del recorrido.
Hash rc5 permanece `f3159c9dd91ddf64e7b02901a9488e6eea60f4c9346eed768bbf2e4f835c9d18`.

`tests/verify_distribution_windows.py --exe <MotorSim.exe> --work <carpeta nueva>
--scale 1 --stage performance`: comprobación Windows automatizada del EXE,
sin Python en PATH ni depender de cwd; abrir barridos2T/4T, seleccionar gráfico
por teclado, tabla, abrir punto, exportar CSV y contrastar precisión exacta,
reutilizar actual y Comparar4T8.0/8.2 con exportación. Ningún worker ni resultado
nuevo. Fuentes científicas conservan hashes. `results/simulacion-2t` intacto
respecto a rc5, sin cambios físicos/solver ni formatos históricos.

Valores de históricos a3000rpm (sin simular):
- 2T referencia: W_C=16.49050751206088J; P=824.525375603044W;
  T=2.624545784638522N·m; pmax=1331530.846070603Pa.
- 4T compresión8.2: W_C=50.95490295791647J; P=1273.8725739479116W;
  T=4.054862340260122N·m; pmax=2685606.691957945Pa.

Evidencia versionada: `results/rendimiento-rc6-20260917/` (tests, JSON y capturas).
Capturas completas: `E:\MotorSim distribucion\Rendimiento rc6`.
Inspección visual del agente separada de automatización: ejes/leyendas/colores,
selección, tabla, secundarios y resultados inspeccionados. Escalado100/125/150 %
en Windows; monitor1440×900, no atribuir recorrido físico FullHD.
OpenSpec estricto aprobado. Una revisión independiente puntual sin defectos.
Único pendiente de cierre: aceptación manual de la usuaria. No archivar ni publicar.
