## Implementación y construcción
- [x] Leer orden, Git limpio main y preservar 18194d7/da27ee25; registrar único cambio.
- [x] Centralizar comando fuente/paquete, errores, recursos y diagnóstico.
- [x] Acerca de, ayuda breve y ejemplos generados desde referencias.
- [x] Entorno aislado fijado, receta/spec, avisos/licencias y commit fuente.
- [x] Construcción Windows x64 onedir y ZIP desde referencia limpia.
## Comprobación
- [x] Suite pertinente y revisión puntual de contratos de distribución.
- [x] Extraer fuera del repo; verificar rutas reales GUI/worker, cwd/entorno independientes.
- [x] Recorrido del ejecutable: persistencia, inválidos, alternancia, protección y antiguos.
- [x] Referencia/proyecto, proceso único, cancelación/cierre, errores controlados y procedencia.
- [x] Lectores/comparación/barrido/importación/CSV con evidencia histórica.
- [ ] Tres puntos completos comparados con referencias; tiempos/budget acumulados <=300 s.
- [x] Capturas reales 150 % y compacto; inspección separada de pruebas.
- [x] ZIP final/SHA256/tamaño, README/hoja de ruta y commit de evidencia.
## Pendientes separados
- [ ] Equipo Windows sin Python instalado, solo si existe entorno autorizado.
- [ ] Uso realmente sin conexión, solo si existe aislamiento sin afectar sesión.
- [ ] Aceptación manual de la usuaria; no atribuida a automatización.
- [ ] Validación experimental; fuera de este encargo.

## Registro de preparación
16/09/2026: Windows 10 19045 AMD64, Python 3.11.0 x64. Entorno .venv-build
independiente, PySide6 6.11.2 y PyInstaller 6.22.3; versiones completas fijadas.
224 pruebas aprobadas (36,193 s), incluidos cinco controles de distribución sin
integraciones. Revisión independiente puntual review_windows_distribution:
sin defectos reproducibles; no acredita el protocolo final aún pendiente.

Paquete trial explícitamente marcado source_dirty/trial construido desde trabajo
posterior a da27ee25, abierto directamente fuera del repo con recursos y ejemplos.
Detectado y corregido nombre ZIP truncado por with_suffix sobre versión con puntos;
no hubo ejecuciones físicas ni cambios de modelo. Automatización externa UIA usa
HWND del proceso y teclado para diálogos Qt: evita bloqueos de Invoke modal.
Recorrido trial de editor: guardar incompleto/Guardar como Unicode, rechazar texto
inválido, Cancelar/Descartar cambios, alternar ciclos, leer v1 sin reescribirlo.
Evidencia trial: E:/MotorSim distribucion/Prueba á rc1/Comprobación (no final).
Herramientas UIA son solo de prueba, excluidas del paquete. Ayuda y licencias se
incluyen; no se asignó licencia nueva al código MotorSim.

## Evidencia de la candidata final — 16/09/2026
Fuente **f46613e4ae9a82dc394db8b6509e782c2121cc3c**, main limpio antes de construir.
Comando ejecutado: `.\.venv-build\Scripts\python.exe packaging/build_windows.py`.
Build UTC 20260916T140209Z, source_dirty=false, trial=false. El commit posterior
solo registra esta evidencia y ajustes del controlador externo de pruebas.
Versiones fijadas: Python 3.11.0, PySide6/Addons/Essentials/shiboken6 6.11.2,
PyInstaller 6.22.3, hooks 2026.7; resto en requirements-build.txt/build.json.

ZIP `E:/dino/Dino/dist/MotorSim-0.1.0-rc1-windows-x64-f46613e4.zip`:
43.376.903 bytes, SHA256
`19eeec5047c9f9f5eab22d7938b9680539e5660649659cb209060ec8b4486d6b`.
Carpeta onedir 104.867.240 bytes. GUI PE x64/subsystem Windows, worker x64/console;
Authenticode NotSigned. 160 archivos; qwindows/qmodernwindowsstyle y qtbase_es;
sin .git, entornos, resultados históricos, diseños web ni instrumentación UIA.
Los hashes de todos los archivos extraídos coinciden después del recorrido.

Extraído en `E:/MotorSim distribucion/Candidata final á 0.1.0-rc1/MotorSim`.
Evidencia íntegra en `E:/MotorSim distribucion/Comprobación final rc1` (fuera de Git).
Cada etapa del script `tests/verify_distribution_windows.py` abre el EXE directo,
con cwd `Directorio distinto`, PATH limitado a Windows y sin variables Python/Qt
de desarrollo; LOCALAPPDATA solo del proceso apunta a `Datos` de esa evidencia.
No se alteraron instalaciones, configuración global, credenciales ni políticas.
Se verificaron rutas GUI/worker y módulos cargados: ambos usan
`MotorSim/_internal/python311.dll`; el worker no carga Qt. Sin nueva consola visible
mientras estaba activo. La herramienta externa Python/UIA no suministra dependencias.

### Automatización del ejecutable
- `editor-evidence.json`: Nuevo/Abrir/Guardar/Guardar como, acentos, incompleto,
  error de entrada sin sobreescribir, Cancelar/Descartar, 2T→4T con comprobación de
  selección intermedia, igualdad del JSON recuperado, v1 leído sin reescribir y
  conversión explícita a v6. Ejemplos sintéticos y datos de ensayo separados.
- `cancel-evidence.json`: botón Cancelar (0,235 s) y cierre (0,203 s), ambos
  cooperativos, resultado cancelled y ningún worker huérfano.
- `process-modules.json` / `process-evidence.json`: inspección de módulos con una
  tercera cancelación. Esta activó el límite de seguridad de 3 s; sin manifiesto
  final ni éxito ficticio. Se conserva attempts.csv/case.json. No se acredita
  cancelación cooperativa en este intento ni se atribuye una causa no demostrada.
  La operación externa completa duró 9,186 s; se reserva una cota de 10 s en el
  presupuesto, sin presentar esa cota como integración medida. Sin huérfano.
- `Auxiliar ausente/missing-evidence.json`: copia de control sin worker, mensaje
  útil, sin cálculo ficticio. La candidata original permanece intacta.
  FailedToStart y diagnóstico local también cubiertos por las cinco pruebas unitarias.
- `history-evidence.json`: 4T histórico, comparación A/B compatible, exportar CSV,
  abrir/exportar barrido histórico. Copias fuera del repo; ninguna reintegración.
- `external-evidence.json`: importar CSV de prueba **sintético/no medido**, declarar
  4T/720° y J/ciclo, vista previa, guardar/reabrir, contrastar dos RPM exactas y
  exportar contraste. No representa mediciones ni validación experimental.
- `provenance-evidence.json`: aviso de configuración anterior al editar diámetro,
  lector 2T v1, navegación compacta por teclado; cierre con Descartar explícito.
- `about-evidence.json`: versión/commit reales y ayuda incluidos, accesibles sin Git.

Los fallos del controlador UIA se conservan como archivos *failure.txt: selección
Qt popup, espera de diálogos y confirmación de cierre. Se corrigió el controlador,
no la física ni el producto, y no se repitieron integraciones completas.

### Regresión numérica autorizada
`numerical.json`, `numerical-comparison.json` y `budget.json` identifican resultados.
Referencias: `results/simulacion-2t/integracion-ui-20260915/manifest.json` y
`results/simulacion-2t/cuatro-tiempos-20260916/R2/gui-sweep/point-01,point-02/manifest.json`.

| Caso B/100 Pa | Ciclos | Integración s | W_C J | pmax Pa | RHS | Pico MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2T referencia 3000 | 10 | 13,734 | 16,49050751206088 | 1331530,846070603 | 228171 | 26,523 |
| 4T proyecto 2500 | 7 | 14,797 | 52,302884330421655 | 2641806,76632688 | 305572 | 30,336 |
| 4T proyecto 3000 | 7 | 14,860 | 50,52602475854359 | 2618462,4643861516 | 304466 | 48,840 |

Tres convergidos, balances aprobados, misma secuencia de estados/ciclos/muestras,
trabajos, presiones, RHS/pasos/rechazos y condiciones **exactamente iguales** a las
referencias. Las entradas 2T son iguales completas; en 4T solo difieren nombre del
proyecto, ruta de procedencia e ID de serie. No se omiten diferencias físicas.
No se comparan reloj, memoria ni identificadores de ejecución por igualdad.
Los tres summary.json declaran qt_loaded=false; estados iniciales y límites intactos.
Sin A/B/C, bandas alternativas ni compresión adicional.

Tiempos 4T preparación/escritura/total de punto: 2500 = 0,015/0,265/15,234 s;
3000 = 0,000/0,250/15,110 s. Barrido: integración 29,657, proceso 30,922,
percibido 31,797 s. Cero preparación a esa resolución no significa costo nulo.
**Pendiente temporal 2T:** el contrato v1 no persiste los tiempos adicionales que
emite el worker y la GUI no los conserva. No es posible recuperarlos del resultado
ya ejecutado; no se inventan ni se repite un punto solo para obtener evidencia.
Por eso la tarea conjunta de puntos/tiempos permanece sin marcar, aunque igualdad
y convergencia de los tres puntos están acreditadas.
Presupuesto: tres puntos 43,391 s + dos cancelaciones 0,438 s + cota 10 s del
intento forzado = **53,829 s contabilizados de 300**. Sin reiniciar presupuesto.

### Inspección visual y pendientes
Capturas del EXE extraído: `paquete-editor-150.png`, `paquete-compacto-150.png`,
`paquete-barrido-150.png`, `paquete-importacion-150.png`, `paquete-comparacion-150.png`,
`paquete-acerca.png`. Inspeccionadas editor/compacto/barrido/importación/Acerca de:
legibilidad, foco, reflujo y scroll; compacto 1000×740 y factor Qt 1,5, navegación
por teclado a Simulación. No son aceptación manual de la usuaria.
La captura `paquete-2t-150.png` procede del punto efectivamente calculado.
No se acreditan Windows distintos de Windows 10 19045 x64.

**Por verificar:** desglose temporal 2T, equipo sin Python instalado y offline
real aislado. No existe entorno limpio/aislado disponible; no se desconectó red ni
se cambiaron políticas. Aceptación manual y validación experimental siguen separadas.
Se entrega ZIP candidato con recorrido acreditado y estas limitaciones, no cierre
completo de todas las comprobaciones. Sin publicar, etiquetar, archivar ni ampliar física.
