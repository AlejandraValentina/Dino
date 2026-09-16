## Entrega 7 — configuración y persistencia
- [x] 7.1 Válvulas, validaciones, ley de alzada/área y cruce analítico comprobados.
- [x] 7.2 JSON v6, lectura v1–v5 y conductos independientes sin pérdida de borradores.
- [x] 7.3 Editor, curvas, guardar/reabrir, alternancia y Windows/150 % comprobados.

Entrega 7 completada técnicamente para el alcance geométrico. Aceptación manual de
la usuaria pendiente y separada; no se atribuye una aceptación a la automatización.

## Entrega 8 — núcleo y condiciones de continuación
- [x] 8.1 Tres volúmenes/nueve componentes y cuatro enlaces; invariantes independientes,
  norma/RK4, trabajo 720°, calor cerrado una vez por período y ausencia de W_K.
- [x] 8.2.1 A100 desde estados originales: convergencia/balances y presupuesto aprobados.
- [x] 8.2.2 B100/C100 desde estados originales: convergencia/balances/presupuesto y
  tolerancias de sensibilidad aprobados, sin arranque caliente.
- [ ] 8.2.3 Tendencia de refinamiento: FALLA pmax y Y_I. Condición bloqueante vigente.
- [ ] 8.2.4 C50 y aprobación de banda: no ejecutado por condición previa fallida.
- [ ] 8.3 Integración asíncrona 4T, snapshot sin datos 2T exigidos, resultados
  estrictos reabribles de 1441 muestras, comparación y barrido: no habilitados.
- [ ] 8.4 Declaración externa del ciclo 4T sin reinterpretar importaciones históricas:
  pendiente con el contrato de resultados/integración 4T; 2T preservado.
- [ ] 8.5 Protocolo integrado condicionado: B2500/3000/3500, C extremos,
  compresión 8.2 B/C y regresión 2T B: no ejecutado por condición previa.
- [x] 8.6.1 Suite pertinente y revisión puntual del código efectivamente entregado.
- [x] 8.6.2 Capturas reales de configuración/curvas geométricas/conductos y documentación.
- [ ] 8.6.3 Capturas de resultado, comparación y barrido 4T: dependen de integración.

Entrega 8 En curso con bloqueo numérico concreto. No terminada ni archivada.
No se solicita otra autorización para las etapas que ya estaban condicionadas;
resolver el criterio de tendencia requiere una nueva decisión numérica, no una
confirmación genérica para continuar. No se cambiaron física, perfiles ni pisos.

## Evidencia del 16/09/2026

Git inicial limpio, main, 6cbed3609562e291a62858891b63539625a2e145, remoto origin
conservado. Cambios propios en commits locales; sin publicar ni tocar credenciales.
AGENTS actualizado para sustituir la prohibición anterior de iniciar 7. Sin init,
update, integración automática ni modificaciones globales.

### Pruebas automatizadas

Suite final completa pertinente: `python -m unittest discover -s tests -p 'test*.py'`,
203/203 aprobadas (18,506 s). Ocho controles numéricos/geométricos nuevos y cinco
controles Qt nuevos. Referencias independientes: seno en 0/110/220°, áreas 24π y
93,75π, cruce 40° partido en 0–20/700–720; compresión pV^gamma, balance U+W=Q,
trabajo neto cerrado de dos vueltas, nueve componentes reales y prueba de secuencia
sin segundo calor. Los controles comunes de donante/recipientes/invariantes se
conservan. Los controles de proceso usan un hijo doble que NO integra; cero
campañas completas dentro de la suite.

Autorrevisión del principal: el extremo con apertura/duración decimal podía dejar
residuo trigonométrico por representación float. Se reconoce el evento analítico
hasta ocho ULP, sin redondear a muestras. Ocho pruebas afectadas aprobadas (0,508 s).
Se contrastaron 715000 evaluaciones geométricas de las trazas existentes con la
fórmula previa: igualdad exacta para S4T-0D-01; no justifica repetir sus ejecuciones.
La referencia textual de conductos 4T quedó específica en el JSON final; los
case.json originales del protocolo conservan el identificador geométrico común
2T usado al ejecutar, sin alterar ninguna dimensión ni evidencia retrospectiva.

Lectura comprobada de resultados históricos v1 (integracion-ui-20260915), v2
(editor-20260915/A) y v3/barrido (barrido-20260915/gui-sweep); reconstrucción exacta
de contratos anteriores sin alterar archivos/hashes. Migración de proyectos v1–v5,
JSON v6 completo/incompleto, texto inválido, guardado seguro, errores/cancelaciones,
borradores específicos y teclado comprobados. No es nueva aceptación histórica.

### Ejecuciones numéricas completas (separadas de la suite)

Directorio local preservado: `results/simulacion-2t/cuatro-tiempos-20260916/`.
Cada perfil conserva case.json, attempts.csv y result.json; protocol.json contiene
presupuesto, puertas y sensibilidad. environment.json: Windows 10 19045, Intel
Core i5-10400, Python 3.11.0, sin Qt cargado. Un mismo proceso de consola conservó
resultados precedentes; los picos RAM incluyen esa retención.

| Perfil/banda | Ciclos / convergencia | W_C J/720° | pmax Pa | Peor balance independiente normalizado | s integración | Pico MiB | RHS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A100 | 7 / sí | 50.526033958914 | 2618462.697374 | 1.08360976085e-5 | 7.438 | 28.4375 | 160711 |
| B100 | 7 / sí | 50.526024758544 | 2618462.464386 | 7.68337521458e-7 | 14.406 | 45.65625 | 304466 |
| C100 | 7 / sí | 50.526024465131 | 2618464.732577 | 2.59994897697e-7 | 29.281 | 52.37109375 | 607098 |

Balances discretos máximos m/U/F normalizados del último ciclo: A 3.76e-15,
B 1.19e-14, C 5.88e-14. Todos los tres ciclos de cierre de cada ejecución cumplen.
Y finales I/C/E: A [0.9947751982824065, 0, 0],
B [0.9947751875142438, 0, 0], C [0.9947752054491011, 0, 0].
Medios pasos aceptados A/B/C: 21238 / 40472 / 80830;
rechazos error/físicos: 93/6, 59/6, 47/19. Sin recortes de estado.
Presupuesto consumido: **3 ejecuciones, 51.125 s de integración de 720 s**.
No hubo repeticiones numéricas ni C50, ni las ocho ejecuciones integradas dependientes.

Sensibilidad B/C: W 5.8072e-9 relativa, pmax 8.6623e-7 relativa,
curva 1.5602e-8 relativa, máxima diferencia Y 1.7935e-8,
máxima diferencia normalizada de masas por enlace 4.3415e-9. Tolerancias aprobadas.
**Tendencia falla**: pmax A/B 8.8979e-8 < B/C 8.6623e-7;
Y_I A/B 1.0768e-8 < B/C 1.7935e-8. La regla no dispone de pisos adicionales para
estas magnitudes. C encuentra pmax entre nodos comunes (máximo muestreado
2618462.460408 Pa a 376.5°, frente a pmax 2618464.732577 Pa). Explicar la diferencia
no permite dispensar tendencia ni ocultar el fallo de Y_I. No se identificó un
defecto demostrable del modelo/implementación que autorice repetir o corregir física.
Los archivos de diagnóstico de consola NO son resultados GUI aceptados/reabribles.

### Inspección visual Windows (no aceptación manual)

`python tests/verify_four_stroke_windows.py --output results/simulacion-2t/cuatro-tiempos-20260916/windows-150`
ejecutado con escritorio Default desbloqueado y DPR efectivo 1.5, sin cambios de
políticas ni escala global. QProcess.start bloqueado en el recorrido: cero cálculos.
Edición, guardar, cierre/reapertura, cambio de ciclo con datos separados, inválidos,
protección al cerrar y foco/Tab comprobados. Capturas reales en docs/images:
`motorsim-4t-editor-150.png`, `motorsim-4t-alzada-cruce-150.png`,
`motorsim-4t-area-cruce-150.png`, `motorsim-4t-conductos-150.png`,
`motorsim-4t-compacto-150.png`. Inspeccionadas por el principal: grupos adaptables,
scroll vertical para contenido largo, sin scroll horizontal a 700 px lógicos,
foco visible, curvas y cruce legibles. Archivo de prueba claramente sintético;
no representa el caso usado en la prueba numérica (cruce modificado solo para UI).
Registro: windows-150/recorrido.json. Resultado/comparación/barrido 4T no se capturan
porque no fueron habilitados; ninguna imagen ficticia los sustituye.

### Revisión puntual y estado

Subagente de solo lectura review_four_stroke, una única revisión del diff/contratos
y evidencia: sin defectos reproducibles. Recalculó sensibilidad desde resultados,
confirmó el bloqueo y cotejó estado inicial/RHS 2T contra HEAD en diez ángulos con
igualdad exacta, sin otra integración. Autorrevisión del principal de documentación,
compatibilidad, extremo decimal corregido y capturas; no se presenta como revisión
independiente de esas actividades posteriores.

OpenSpec 1.3.1: validación estricta aprobada. status documental completo no es cierre
funcional. Python 3.11.0/PySide6 6.11.2/Node 24.19.0 disponibles, sin instalar nada.
Aceptación manual de la usuaria del bloque 4T: pendiente. Mediciones reales y
validación experimental: pendientes; herramientas de entrega 6 preservadas.
No archivar, empaquetar, publicar ni comenzar otra ampliación física.

### Identificación de resultados preservados (SHA-256 result.json)

- A-100: `429ceae4d3c5885a2db72a49c52b3797c6e9427d7085f9c1ff57077d7a95271e`
- B-100: `f44d8ccac99085318b99859defa06cbc1d276b84d610c9336847e39de005b994`
- C-100: `615f196a99e802cca2c2d58c3c6079744c5a29ead5952f1cd0f88d28f43abd8e`
