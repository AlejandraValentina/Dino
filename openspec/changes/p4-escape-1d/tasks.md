## P4 â€” orden cec0f5b3
- [x] Registrar aceptaciÃ³n humanaP3, congelar baseline y archivar cambio aceptado.
- [x] RevisiÃ³n independiente inicial de contrato de puerto y limitaciÃ³nBCexterior.
- [x] Formalizar fixtures y ejecutar P4A/E01â€“E05 cuantitativos; revisiÃ³n independiente PASS.
- [ ] P4B/E06â€“E11, reflexiones, longitud, RPM, refinamiento y CFL.
- [ ] SÃ³lo trasP4A/P4B PASS: camino hÃ­brido, revoluciÃ³n cronometrada y E12â€“E15.
- [x] RegresionesP0/P2/P3 y revisiÃ³n independiente final (confirma bloqueo, noP4PASS).
- [ ] Gate final y aceptaciÃ³n humana posterior. NoP5.

P3 archivado con14/19 tareas: las5 restantes son casillas histÃ³ricas reservoir,
explÃ­citamente sustituidas porR1; no se marcaron como realizadas. CierreR1 y
aceptaciÃ³n humana acreditados. Se preserva borrado ajeno redme.txt.

## Estado final â€” P4_BLOCKED_WAVE_PHYSICS / SCIENTIFIC_CHANGE_REQUIRED
P3 aceptado por la usuaria y archivado en2026-09-18-p3-acoplamiento-conservativo.
Baseline ec6ec55 y72 evidenciasP3 intactos; aceptaciÃ³n en docs/gasdynamic/p3_human_acceptance.json.
P4 no se archiva. No motor hÃ­brido, convergencia periÃ³dica, potencia indicada ni
comparaciÃ³n entre ciclosmotor: dependen deP4B PASS que no se obtuvo. NoP5.

Implementado sÃ³lo banco experimental aislado: puerto variableideal, cara dividida
P3+pared reflectiva, integrador conjuntoSSPRK2 con eventos/CFL, adaptador de ductos
existentes, sensores/snapshots/ledgers. El camino2T_0D_BASELINE sigueintacto.
P4C/2T_0D1D_EXHAUST de motor no creado; no presentar banco como motorhÃ­brido.

| Gate | Resultado |
|---|---|
| E01â€“E05 cerrado/apertura/descarga/cierre/backflow | PASS, revisiÃ³n independiente |
| E06â€“E09 recto/difusor/convergente/cadena | Casos individuales PASS |
| E10 longitud, incluido control a volumen idÃ©ntico | PASS |
| E11 RPM y eventos (banco, no motor) | PASS |
| Refinamiento difusor | PASS |
| Refinamiento descarga | FAIL en presiÃ³n integrada y masa |
| SensibilidadCFL focal ambos bancos | PASS |
| E12â€“E14 motor/conservaciÃ³n/convergencia/comparaciÃ³n | NOT_RUN, bloqueados porP4B |
| E15 positividad | PASS en19 bancos; motor NOT_RUN |

Criterios congelados antes de ejecutar: no se ajustaron tras resultados.
Mayor residuo global normalizado3.378286968e-15. Puerto cerrado:m/E/F exactamente0.
Backflow al cilindro usaYlocal~.2, noYatmÃ³sfera0. ReacciÃ³n axial sobre abertura
y paredcomplementaria registrada porstage. Cd1, sin calibraciÃ³n/pÃ©rdida aÃ±adida.
Eventos fÃ­sicos90Â°/112.2040961Â°/247.7959039Â°/270Â°, Amax200mmÂ², todos alcanzados.

## Incumplimiento de refinamiento â€” descarga
| N | Integral presiÃ³n (PaÂ·s) | Intercambio masa (kg) | Arrival (s) |
|---|---:|---:|---:|
| 100 | 164.729319651 | -9.70056603322e-05 | 0.00087477247055 |
| 200 | 164.804998778 | -9.70077286939e-05 | 0.000879296215498 |
| 400 | 164.899734482 | -9.70099933774e-05 | 0.000874901407169 |

Diferencias presiÃ³n .0756791278â†’.0947357040 PaÂ·s; masa2.06836170034e-9â†’
2.26468347229e-9kg: ambas aumentan. Revisor recalculÃ³ desdehistory, flujos por
stage y cambio final de masa, descartando bugdelagregador. Sensores reales
.099/.1005/.09975m; fallo de masa independiente de posiciÃ³nsensor. Magnitud
pequeÃ±a no autoriza relajar el criterio. Causa numÃ©rica/fÃ­sica no determinada.
No atribuirla a la BC sin evidencia. No repetir bancos ni iniciarP4C.

Timingblowdown: llegada102kPa sensores .099/.297m en .000873870597/.001438368459s;
delta .000564497862s dentro envolvente .000328402386.. .000615957624s.
Velocidades u+a muestreadas340.9325..544.5545m/s; no trayectoria reconstruida ni
validaciÃ³n de amplitud fuerte. Pulso dÃ©bil100Pa separado para coeficientes.
Longitud/cadena: cambiarheader.2â†’.3m retrasa onda; controlheader+.1/tailâˆ’.1
conserva volumen4.08407045e-4mÂ³ y tambiÃ©n retrasa retorno. No es sÃ³lo volumen.
RPM2500/3000/3500: misma llegada fÃ­sica.000729366873s, Ã¡ngulos190.9405031 /
193.1286037 /195.3167043Â°. No acredita rÃ©gimenperiÃ³dico.

## Casos ejecutados y conservaciÃ³n
19 integraciones nuevas, todas completas;510.907s sumados dentro delsolver,
no tiempo total de orquestaciÃ³n. MÃ¡ximo271.25s, inferior600s; no timeoutfÃ­sico.

| Caso | Tiempo (s) | Residuo global mÃ¡ximo |
|---|---:|---:|
| closed_N100_CFL0.4 | 1.828 | 1.6144e-16 |
| blowdown_N100_CFL0.4 | 17.844 | 1.9855e-15 |
| backflow_N100_CFL0.4 | 5.406 | 6.3219e-16 |
| straight_N100_CFL0.4_RPM3000 | 2.031 | 4.2153e-16 |
| diffuser_N100_CFL0.4_RPM3000 | 2.641 | 4.3901e-16 |
| converger_N100_CFL0.4_RPM3000 | 3.422 | 1.2541e-15 |
| chain_N100_CFL0.4_RPM3000 | 4.000 | 7.3072e-16 |
| long_N100_CFL0.4_RPM3000 | 4.469 | 5.3439e-16 |
| equal_volume_N100_CFL0.4_RPM3000 | 4.281 | 5.6364e-16 |
| chain_N100_CFL0.4_RPM2500 | 3.938 | 7.3072e-16 |
| chain_N100_CFL0.4_RPM3500 | 3.968 | 6.1172e-16 |
| diffuser_N200_CFL0.4_RPM3000 | 13.234 | 2.5985e-16 |
| diffuser_N400_CFL0.4_RPM3000 | 48.531 | 6.0445e-16 |
| diffuser_N100_CFL0.2_RPM3000 | 5.203 | 6.6553e-16 |
| diffuser_N100_CFL0.6_RPM3000 | 1.969 | 3.2333e-16 |
| blowdown_N200_CFL0.4 | 70.360 | 3.3783e-15 |
| blowdown_N400_CFL0.4 | 271.250 | 2.7061e-15 |
| blowdown_N100_CFL0.2 | 34.516 | 3.0037e-15 |
| blowdown_N100_CFL0.6 | 12.016 | 1.5523e-15 |

## Evidencia y revisiÃ³n
- [x] 88 pruebas PASS,23.571s; incluye5 focales puerto/geometrÃ­a y83 histÃ³ricas.
- [x] P2 completo T01â€“T12/58 finales y FIRST_ORDER/R4 reevaluados offline PASS.
- [x] Siete regresiones histÃ³ricasP0 offline PASS; sin nuevas campaÃ±asP0/P2/P3.
- [x] P3 C00/C00B reevaluados; evidenciaC01â€“C12 intacta por72SHA256, siete archivosP3 y27P2 congelados.
- [x] RevisiÃ³n independiente /root/p3_review: P4A PASS, P4B STOP; regresiones confirmadas.
- [x] AutorrevisiÃ³n de alcance/Ã­ndice/hashes/documentaciÃ³n separada; no revisiÃ³n general nueva.
- [x] GrÃ¡ficas de banco inspeccionadas visualmente; no son capturaWindows ni aceptaciÃ³nhumana.

Frontera exterior nonreflectingP2 con estadoexplÃ­cito. Revisor documentÃ³ salto
potencial100000â†’98724.6267Pa al cambiarentropÃ­a donante en un estado tÃ©rmico
artificial. No se cambiÃ³BC; en campaÃ±a no hay evidencia de que ese fenÃ³meno cause
el fallo. Se conserva alcance de truncamiento caracterÃ­stico lineal/local, no
radiaciÃ³n de escape real ni anecoico universal.

Dos fallos de infraestructura preservados: primerP4B se rechazÃ³ por timeoutdel
comando fuera del rango del esquema, antes de integrar; corregido a3500s totales,
600s porcaso intactos. P4_CLOSE completÃ³88tests yregresiones, pero fallÃ³ al fusionar
checkIDhistorical duplicado con nombrecomando. Corregido a baseline_command y
validado por IDsdisjuntos/dry-run, sin repetirtests. No afirmar que ese runnativo
pasÃ³: permaneceFAILED_INFRASTRUCTURE. P4A nativoBLOCKED sÃ³lo reviewerhook;
P4B nativoSCIENTIFIC_CHANGE_REQUIRED por fallo real. DictÃ¡menes adjuntos separados.

Comandos reales desde raÃ­z, Python .venv: `-m dev_orchestrator.runners.run_phase`
P4A/P4B/P4_CLOSE con `--dependency P2=docs/gasdynamic/p2_accepted_dependency.json`.
No relanzar campaÃ±as trasSTOP sin resolver decisiÃ³ncientÃ­fica. Evidencia:
results/p4-exhaust-20260918; grÃ¡ficas port-blowdown.png/svg y waves-refinement.png/svg.
No publicar, no modificarcredenciales/globales, noarchivarP4. Borradoajeno redme.txt
conservado fuera decommits. OpenSpecautomÃ¡tico sigueomitido.

OpenSpec estricto: cambioP4 y specconsolidadaP3 PASS. AtributosGit locales
preservan bytes de los tres mÃ³dulosP4 revisados; sin configuraciÃ³n global.

## P4-R1 â€” diagnÃ³stico autorizado 2026-09-21

- [x] Auditar posiciones histÃ³ricas y fijar observables antes de ejecutar.
- [x] Preparar registro de vecinos sin modificar solver; prueba de paridad exacta.
- [x] Ejecutar nominal y CFL focal, control y N800 sÃ³lo si corresponde.
- [x] Registrar tablas, seÃ±ales, ledger y clasificaciÃ³n sin cambiar gate.
- [x] RevisiÃ³n independiente de resultados y cierre documental.

DefiniciÃ³n previa: docs/gasdynamic/p4_r1_observables.md. HistÃ³ricos intactos.

## Resultado P4-R1 â€” 2026-09-21

**P4_R1_PERFORMANCE_DIAGNOSTIC_REQUIRED**. Defecto de sensor confirmado
(P4_R1_METRIC_IMPLEMENTATION_DEFECT) y corregido exclusivamente en el observable.
P4 sigue abierto/bloqueado; no P4C, P5, cambio de gate, aceptaciÃ³n ni archivo.

Definiciones previas: [p4_r1_observables.md](../../../docs/gasdynamic/p4_r1_observables.md).
CÃ³digo: dev_orchestrator/p4_r1.py, commit previo87851ec. Fuente numÃ©rica y
historias anteriores:120 hashes intactos. Tres nominales reproducen exactamente
celdas, cÃ¡mara, stages, dt, eventos, conteos y ledgers anteriores.

### AuditorÃ­a histÃ³rica (sin reemplazar evidencia)

Qp: rectÃ¡ngulo derecho por paso aceptado, |pâˆ’100000 Pa|, PaÂ·s, sin normalizaciÃ³n.
El sensor pedido0,1 m se desplazaba al centro mÃ¡s cercano. La cuadratura tambiÃ©n
introduce dependencia de dt; no se ha demostrado un cambio arbitrario de logging.
Qm: ledger SSPRK2 dt/2*(mdot1+mdot2), kg, negativo al salir de cÃ¡mara.
Ventana idÃ©ntica0â†’0,012222222222222223 s. Los siguientes Qp con trapecios aÃºn
usan el sensor histÃ³rico desplazado; no son los Qp corregidos a posiciÃ³n fija.

| N | x histÃ³rico m | Qp histÃ³rico PaÂ·s | Qp PL mismo sensor PaÂ·s | Qm kg |
|---|---:|---:|---:|---:|
| 100 | 0.099 | 164.729319650664 | 164.785356822589 | -9.70056603322141e-05 |
| 200 | 0.1005 | 164.804998778420 | 164.833308019080 | -9.70077286939145e-05 |
| 400 | 0.09975 | 164.899734482389 | 164.913887996882 | -9.70099933773868e-05 |

### Q corregidos, misma posiciÃ³n x=0,1 m

InterpolaciÃ³n geomÃ©trica entre dos centros vecinos, t0 mÃ¡s todos los finales de
paso; integral exacta del valor absoluto de la seÃ±al lineal temporal, con cruce
por cero dividido. Sin decimaciÃ³n ni cambio de soluciÃ³n. Masa sin cambios.

| N | Qp completo PaÂ·s | Qm completo kg | Estado |
|---|---:|---:|---|
| 100 | 164.742346961691 | -9.70056603322141e-05 | Completo |
| 200 | 164.854748982338 | -9.70077286939145e-05 | Completo |
| 400 | 164.903227803894 | -9.70099933773868e-05 | Completo |
| 800 | â€” | â€” | Timeout, integral parcial excluida |

| Observable | Mallas | Q_finoâˆ’Q_grueso | Diferencia absoluta |
|---|---|---:|---:|
| Q_pressure | 100â†’200 | 1.12402020647409e-01 | 1.12402020647409e-01 |
| Q_pressure | 200â†’400 | 4.84788215557046e-02 | 4.84788215557046e-02 |
| Q_mass | 100â†’200 | -2.06836170033812e-09 | 2.06836170033812e-09 |
| Q_mass | 200â†’400 | -2.26468347228764e-09 | 2.26468347228764e-09 |

D400â†’800 no disponible para ambos. N800 parcial: Qp=159,317364741868 PaÂ·s,
Qm=âˆ’9,538417249462383eâˆ’5 kg, sÃ³lo0â†’0,008968816321386268 s; **no comparable**
con integrales de ventana completa. Sin Richardson ni extrapolaciÃ³n.

### Eventos y fase

Apertura fÃ­sica90Â°/0,000555555555555556 s alcanzada en todas las descargas.
Cierre programado270Â°/0,010555555555555556 s alcanzado sÃ³lo en100/200/400;
N800 termina241,438693785Â°. No confundir evento programado con alcanzado.
Llegada=primer cruce ascendente interpolado102000 Pa, sin posiciÃ³n analÃ­tica.
Diferencias son entre mallas sucesivas, no errores contra soluciÃ³n exacta.

| N | Llegada s | CA Â° | Diferencia llegada s | Cierre alcanzado |
|---|---:|---:|---:|---|
| 100 | 8.763254918959e-04 | 95.773858854 | â€” | SÃ­ |
| 200 | 8.774345295839e-04 | 95.793821533 | +1.109037687947e-06 | SÃ­ |
| 400 | 8.755830727586e-04 | 95.760495310 | -1.851456825306e-06 | SÃ­ |
| 800 | 8.745722624311e-04 | 95.742300724 | -1.010810327483e-06 | No |

La llegadaN800 ocurriÃ³ antes del timeout y es observable; su integral completa no.
La secuencia de llegadas100/200/400 no es monÃ³tona; la Ãºltima diferencia absoluta
se reduce, pero esto no acredita el gate completo. No se identificÃ³ un candidato
poscierre >=2000 Pa en las descargas completas. EnN800 la ventana poscierre
**no fue observada**. No atribuir causalmente picos a reflexiones con un Ãºnico sensor.
SeÃ±ales y extremos fÃ­sicos conservados; sin mover ventanas tras mirar resultados.
La presiÃ³n final de los completos permanece~100,22 kPa, cola pequeÃ±a no nula;
no prueba por sÃ­ sola independencia de la ventana ni convergencia de fase.

### Sensibilidad temporal focal

Ratio=|Q_CFL0,2âˆ’Q_CFL0,4|/D200â†’400 nominal. Umbrales diagnÃ³sticos definidos
antes: <=0,1 pequeÃ±o; >=0,5 comparable; intermedio inconcluso. No nuevos gatesP4.

| Observable | N | Q CFL0,4 | Q CFL0,2 | Diferencia absoluta | Ratio |
|---|---:|---:|---:|---:|---:|
| Q_pressure | 200 | 164.85474898234 | 164.85463129893 | 1.176834054775e-04 | 0.002427522 |
| Q_pressure | 400 | 164.90322780389 | 164.90318343251 | 4.437138409230e-05 | 0.000915274 |
| Q_mass | 200 | -9.7007728693914e-05 | -9.7007736044853e-05 | 7.350938610530e-12 | 0.003245901 |
| Q_mass | 400 | -9.7009993377387e-05 | -9.7009995946039e-05 | 2.568652240778e-12 | 0.001134221 |

Los cuatro cambios son pequeÃ±os; esto no estima rigurosamente todo el error
 temporal, pero no muestra contaminaciÃ³n comparable en este contraste. CFL
productivo0,4 intacto; no estudio general dx/dt ni campaÃ±as extra.

### Control simple equivalente a E06

Tubo recto0,75 m/20 mm, puerto constante200 mmÂ² durante180â†’234Â°;
0â†’0,003 s. Referencia lineal dÃ©bil y L1 definidos antes de ejecutar, no soluciÃ³n
exacta no lineal ni prueba de ondas fuertes. Ãrea idÃ©ntica en todos los stages.

| N | L1 normalizado | Qp PaÂ·s | Qm kg | Llegada s | Tiempo s |
|---|---:|---:|---:|---:|---:|
| 100 | 0.0062372757199 | 0.00754161710579 | -3.656141330082e-13 | 2.008493799925e-05 | 2.157 |
| 200 | 0.00216432946744 | 0.00758034425026 | -3.479762774394e-13 | 2.069141848764e-05 | 8.563 |
| 400 | 0.000710559647888 | 0.00757161321307 | -3.201751655362e-13 | 2.191874214232e-05 | 34.938 |

Control convergente, sin N800 adicional. Su masa neta casi cero se informa sin
ratio relativo mal condicionado. El contraste dÃ©bil/fuerte no aÃ­sla por sÃ­ solo
el puerto como causa: amplitud y condiciones tambiÃ©n difieren.

### Ledger, conservaciÃ³n, admissibilidad y coste

Residuo de masa=|Qmâˆ’(m_finalâˆ’m_inicial)|/masa_inicial_total. AuditorÃ­a adicional
por suma independiente de stages. ConservaciÃ³n y positividad PASS en todos los
intervalos alcanzados; N800 no aprueba final/eventos porque estÃ¡ incompleto.

| Caso | Pasos | Tiempo solver s | dt mÃ­nimo s | dt mÃ¡ximo s | CFL mÃ¡ximo | Residuo global | Residuo masa |
|---|---:|---:|---:|---:|---:|---:|---:|
| blowdown_N100_CFL0.4 | 2673 | 17.969 | 7.982491720e-07 | 7.039515698e-06 | 0.40000000000000008 | 1.985464998e-15 | 9.307525320e-16 |
| blowdown_N200_CFL0.4 | 5405 | 71.000 | 3.920881915e-07 | 3.519757849e-06 | 0.40000000000000008 | 3.378286968e-15 | 3.412759284e-15 |
| blowdown_N400_CFL0.4 | 10868 | 286.672 | 1.591807538e-08 | 1.759878924e-06 | 0.40000000000000008 | 2.706076806e-15 | 1.068641796e-15 |
| blowdown_N200_CFL0.2 | 10765 | 137.985 | 3.137548774e-07 | 1.759878924e-06 | 0.20000000000000004 | 6.210941787e-15 | 1.895977380e-15 |
| blowdown_N400_CFL0.2 | 21700 | 559.922 | 1.264635145e-07 | 8.799394622e-07 | 0.20000000000000004 | 4.827967923e-15 | 9.307525320e-16 |
| control_N100_CFL0.4 | 342 | 2.157 | 2.554574926e-06 | 8.799394527e-06 | 0.40000000000000002 | 4.578090050e-16 | 9.159964826e-17 |
| control_N200_CFL0.4 | 699 | 8.563 | 6.408287310e-07 | 4.399697286e-06 | 0.40000000000000002 | 6.253467629e-16 | 3.245364873e-16 |
| control_N400_CFL0.4 | 1403 | 34.938 | 9.401554711e-07 | 2.199848634e-06 | 0.40000000000000002 | 7.938648579e-16 | 4.692226554e-17 |
| blowdown_N800_CFL0.4 | 16963 | 900.031 | 2.069854083e-07 | 8.799394622e-07 | 0.40000000000000008 | 6.608845935e-15 | 1.930449696e-15 |

| Caso | RHS | HLLC | HLLE | Rechazos |
|---|---:|---:|---:|---:|
| blowdown_N100_CFL0.4 | 5921 | 597209 | 0 | 575 |
| blowdown_N200_CFL0.4 | 12018 | 2413958 | 0 | 1208 |
| blowdown_N400_CFL0.4 | 24161 | 9685325 | 0 | 2425 |
| blowdown_N200_CFL0.2 | 23860 | 4792712 | 0 | 2330 |
| blowdown_N400_CFL0.2 | 48182 | 19314651 | 0 | 4782 |
| control_N100_CFL0.4 | 684 | 69084 | 0 | 0 |
| control_N200_CFL0.4 | 1429 | 287229 | 0 | 31 |
| control_N400_CFL0.4 | 2882 | 1155682 | 0 | 76 |
| blowdown_N800_CFL0.4 | 38700 | 30997419 | 0 | 4774 |

Suma de nueve tiempos de solver2019,237 s; ocho completos y un parcial.
N800900,031 s: control del lÃ­mite al comienzo de paso, sin extensiÃ³n; exceso
0,031 s corresponde a finalizar el paso antes de comprobarlo de nuevo.
CFL mÃ¡ximo0,4000000000000001 es redondeo; verificaciÃ³n contractual por lÃ­mites
de cada stage PASS, sin tolerancia nueva. Mayor residuo global6,60884593495eâˆ’15.

Perfil N800:16963 pasos,38700 RHS/reconstrucciones/evaluaciones de puerto,
37419 evaluaciones de coupling abierto,30921300 Riemann internos+38700 pared,
30997419 HLLC totales, ceroHLLE.4774 rechazos por stage_CFL.
Coste observado0,0530584802 s/paso aceptado, incluidos rechazos y logging.
Inferencia de cuentas contrastada con characteristic==RHS y2*pasos+rechazos==RHS.
Microperfil offline del estado final:20 repeticiones sin avanzar estado y un
snapshot cProfile. ReconstrucciÃ³n4,648 ms, Riemann internos7,895 ms,
puerto/coupling0,0544 ms, exterior0,0132 ms por snapshot en ese equipo.
No son porcentajes del coste global: excluyen advances, validaciÃ³n, ledgers,
logging y variaciÃ³n de estados. Sin optimizaciÃ³n ni integraciÃ³n adicional.

### VerificaciÃ³n y revisiÃ³n

Tres tests focales PASS (0,074 s en run), reproducciÃ³n offline de nueve mÃ©tricas
PASS, paridad exacta nominal histÃ³rica PASS,120 hashes PASS, OpenSpec estricto
P4 PASS. No repetidas regresiones generalesP0/P2/P3: fuentes congeladas intactas.
AutorrevisiÃ³n del postproceso y visualizaciÃ³n de seÃ±ales separada de revisiÃ³n
independiente read-only por /root/p3_review. Esta Ãºltima confirmÃ³ mÃ©tricas,
CFL/control, conteos, congelaciÃ³n y estado final; pidiÃ³ distinguir cierre
programado del no alcanzadoN800, recogido en diagnostics.json y esta tabla.
Sin aceptaciÃ³n humana deP4. Gate nativo conservaSCIENTIFIC_CHANGE_REQUIRED;
la ejecuciÃ³n del protocoloCOMPLETED no equivale a integraciÃ³nN800 completa.

Evidencia: results/p4-r1-20260921, signals.png/svg, performance.json,
snapshot-profile.txt, diagnostics.json, independent-review.json, decision.json,
run/artifacts/cases (incluye parcial), inventory-all.json. HistÃ³ricos intactos.

Comandos desde raÃ­z:
- `.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P4_R1 --dependency P2=docs/gasdynamic/p2_accepted_dependency.json`
- `.venv\Scripts\python.exe -m dev_orchestrator.p4_r1_profile results/p4-r1-20260921/run/artifacts/cases/blowdown_N800_CFL0.4.json.gz results/p4-r1-20260921`
- `python dev_orchestrator/p4_r1_plot.py results/p4-r1-20260921` (matplotlib sÃ³lo herramienta offline disponible; no dependencia del producto).
- `openspec validate p4-escape-1d --strict --no-interactive`

STOP. Pendientes: Q800 de ventana completa, D400â†’800 y convergencia global de
descarga. Resolver siguiente autorizaciÃ³n sobre rendimiento antes de otra
integraciÃ³n; no ampliar timeout automÃ¡ticamente. No propuesta de cambio del
gate porque no se acreditÃ³ el caso preasintÃ³tico. P4B/P4C siguen pendientes.
No publicaciÃ³n, archivo, nueva candidata ni modificaciÃ³n de producto.

## P4-R1E â€” orden6e7321b2, 2026-09-21

- [x] Congelar solver, observables y evidenciaR1; elecciÃ³n restart desde t=0.
- [x] Ejecutar Ãºnicamente N800/CFL0,4 con lÃ­mite1500s.
- [x] Evaluar todas las condicionesR1 con Q completos y revisiÃ³n independiente.

1500s es lÃ­mite de integraciÃ³n;1650s del comando deja margen de serializaciÃ³n,
no amplÃ­a el solver. EstimaciÃ³n previa900,031/0,734â‰ˆ1226s. No optimizaciÃ³n.
No existe API de resume de tiempo/eventos/ledger: los arrays finales anteriores
no se convierten en checkpoint. Se comprueba paridad exacta del prefijo aceptado.
Mismo prepare/measured/compare deR1 por importaciÃ³n, sin modificar esos archivos.
Mismas condiciones de presiÃ³n, masa, llegada, conservaciÃ³n, positividad,CFL,
control y temporal. Fallo de fase se registra separadamente. Timeoutâ†’
P4_R2_PERFORMANCE_OPTIMIZATION_REQUIRED, sin optimizar ni repetir en esta orden.

## Resultado P4-R1E â€” 2026-09-21

**P4_R1_PREASYMPTOTIC_REFINEMENT_CONFIRMED** bajo todas las condicionesR1.
Una sola integraciÃ³n nueva N800/CFL0,4, reiniciada desde t=0; completÃ³
0â†’0,012222222222222223 s (CA80â†’300) en1139,360 s, lÃ­mite1500s.
No resume ambiguo, optimizaciÃ³n ni cambio cientÃ­fico. No aceptaciÃ³nP4 ni
modificaciÃ³n de su gate; STOP antes deP4C/P5 y sin archivo/publicaciÃ³n.

Reutilizados los ocho completosR1 por hashes (tres nominales, dos CFL y tres
controles). El N800 parcial sÃ³lo se usa para auditar el prefijo registrado:
16963 history/stages idÃ©nticos, no para integrales de convergencia.
Fuentes y evidencia:120+31 hashes intactos. prepare/measured/compare y definiciÃ³n
R1 sin cambios, sensor0,1m, cuadratura lineal y ledgerSSPRK2 originales.

| N | Qp PaÂ·s | Qm kg | Llegada s | Llegada CA Â° |
|---|---:|---:|---:|---:|
| 100 | 164.742346961691 | -9.70056603322141e-05 | 8.763254918959e-04 | 95.773858854 |
| 200 | 164.854748982338 | -9.70077286939145e-05 | 8.774345295839e-04 | 95.793821533 |
| 400 | 164.903227803894 | -9.70099933773868e-05 | 8.755830727586e-04 | 95.760495310 |
| 800 | 164.923093338473 | -9.70116526264108e-05 | 8.745722624311e-04 | 95.742300724 |

| Mallas | D presiÃ³n PaÂ·s | D masa kg | D llegada s |
|---|---:|---:|---:|
| 100â†’200 | 1.124020206474e-01 | 2.068361700338e-09 | 1.109037687947e-06 |
| 200â†’400 | 4.847882155570e-02 | 2.264683472288e-09 | 1.851456825306e-06 |
| 400â†’800 | 1.986553457897e-02 | 1.659249024012e-09 | 1.010810327483e-06 |

D400â†’800 menor queD200â†’400 en presiÃ³n, masa y llegada. Se conservan todas
las condiciones: conservaciÃ³n, admisibilidad, CFL, control convergente y efecto
 temporal pequeÃ±o. El control/CFL no se repitiÃ³. No Richardson, cambio de umbral
ni tolerancia relativa de masa aÃ±adida. relative_mass_difference sÃ³lo diagnÃ³stico:
1.710360538235e-05.

### Registro N800 completo

Pasos21831; RHS48516; HLLC38854978; HLLE0.
Rechazos stage_CFL4854; downgrades0.
dt mÃ­nimo9.154256934776e-08 s; mÃ¡ximo8.799394622473e-07 s.
CFL mÃ¡ximo0.40000000000000008; comparaciÃ³n contractual dt<=lÃ­mites de cada
stage PASS, sin tolerancia nueva. Ledger masa frente inventario:
3.757482443841e-15, normalizado por masa inicial total.

| Balance combinado | Residuo final dimensional | MÃ¡ximo normalizado por paso |
|---|---:|---:|
| Masa kg | -6.505213034913e-19 | 3.860899391836e-15 |
| EnergÃ­a J | -8.313350008393e-13 | 6.608845934951e-15 |
| Especie kg | 1.084202172486e-18 | 3.757482443841e-15 |

NormalizaciÃ³n contractual: masa inicial, energÃ­a inicial, masa inicial para
especie. MÃ¡ximo porstage3.146163579517e-16; conservaciÃ³nPASS al lÃ­mite1eâˆ’10.
MÃ­nimos del dominio1D: rho=0.70632205811636 kg/mÂ³,
p=99999.999999999971 Pa,T=299.99999999999977 K.
Yâˆˆ[0.19999999999992873,0.80000000000002869] dentro de[0,1].
Admisibilidad de cÃ¡mara y tubo comprobada por el solver en sus stages.

### Cierre y seÃ±al poscierre

Cierre270Â° alcanzado a0,010555555555555556s. CÃ¡mara y ledger al cierre son
exactamente iguales a sus valores finales. Hay2489 muestras posteriores:
p mÃ­nimo100227,85042879335Pa, mÃ¡ximo101249,2443580738Pa. SeÃ±al completa
conservada en el artifact y graficada en signals.png/svg; zoom sÃ³lo visual.
No se identificÃ³ candidato poscierre con el detectorR1 ya congelado.

En el instante exacto270Â° la geometrÃ­a congelada devuelve Ã¡rea
1,4210854715202002eâˆ’19mÂ² por aritmÃ©tica flotante; trazas guardadas sin redondear
con flujo~âˆ’9,9848245eâˆ’19kg/s. Para t>t_cierre Ã¡rea/flujo son exactamente cero.
No clamp, tolerancia ni modificaciÃ³n de ley de puerto; no ocultar esta diferencia
entre instante de cierre y estados estrictamente posteriores.

### Incidencia de auditorÃ­a, sin repetir integraciÃ³n

El run nativo conserva summary.state=FAILED_INFRASTRUCTURE y gate
SCIENTIFIC_CHANGE_REQUIRED: comparaba tuplas en memoria con listas JSON.
No es un fallo numÃ©rico; las nueve condiciones cientÃ­ficas calculadas son true.
Se corrigiÃ³ sÃ³lo same_json_value, normalizando tupla/lista vÃ­a JSON, sin redondear
ni aplicar tolerancia. Tres regresiones puras PASS: estructuras equivalentes,
un ULP distinto y stage ausente. No integraciÃ³n tras el fix.

La decisiÃ³n offline exige primero151 hashes intactos, prefijo persistido exacto,
reproducciÃ³n exacta de measured y todas las condiciones originales. Originales
nativos preservados en run/; audit-correction.json explica el diagnÃ³stico y
 decision.json registra el estado cientÃ­fico. No presentar run nativo comoPASS.
Preflight del wrapper con resultado anterior inyectado fue offline, cero
integraciones; sÃ³lo la ejecuciÃ³n formal de1139,360s adquiriÃ³ nueva evidencia.

OpenSpec estrictoP4 PASS. AutorrevisiÃ³n del diff y seÃ±ales separada de revisiÃ³n
independiente read-only. No regresiones fÃ­sicas generales ni campaÃ±as adicionales.
Evidencia: results/p4-r1e-20260921; fuente previa c3ebf1f.
Comando ejecutado: `.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P4_R1E --dependency P2=docs/gasdynamic/p2_accepted_dependency.json`.
Pruebas puras: `.venv\Scripts\python.exe -m unittest discover -s tests -p test_p4_r1e.py -v`.

Pendiente exclusivamente de nueva orden humana: revisiÃ³n del gateP4 y decisiÃ³n
sobre continuarP4. La confirmaciÃ³nR1 no habilitaP4C niP5, no acepta ni archivaP4.

RevisiÃ³n independiente final /root/p3_review: confirma PREASYMPTOTIC, recalcula
Q/diferencias/balances, valida151 hashes y prefijo JSON exacto. Acepta correcciÃ³n
de auditorÃ­a, no aceptaciÃ³n humanaP4. Recibo: independent-review.json.

## P4-R2 â€” orden2df31e6d
- [x] RevisiÃ³n independiente y adopciÃ³n versionada P4_REFINEMENT_R2.
- [x] ReevaluaciÃ³n offline de16 casos/6 agregados restantes: P4B PASS bajoR2.
- [x] Implementar P4C aislado y medir un ciclo antes de multiciclo.
- [x] Evaluar E12/E15 del ciclo medido y ejecutar regresiones; aplicar STOP de coste.
- [ ] E13 periÃ³dico y E14 G1/G2/retorno causal; E12/E15 sobre la campaÃ±a completa.

Delta: docs/gasdynamic/p4_refinement_r2.md; evidencia results/p4-r2-20260921/gate-review.json.
Sin integraciÃ³n nueva para PartesA/B. E11 histÃ³rico es banco, no ciclo motor.

### Resultado P4C â€” P4_BLOCKED_PERFORMANCE

DefiniciÃ³n registrada antes de ejecuciÃ³n en docs/gasdynamic/p4c_hybrid.md,
commit4747eb2. Ruta interna motorsim/hybrid_exhaust.py, sin import UI/JSON;
legacy y kernels congelados intactos. Adaptador I/K/C reutiliza fuentes Model;
puerto usa P3/P4. CombustiÃ³n350â†’390 conserva F analÃ­tica mediante coordenada
transformada, calor SSPRK2 registrado separado de su primitiva. RevisiÃ³n previa
independiente aprobÃ³ esa adaptaciÃ³n; corrigiÃ³ sÃ³lo evaluadorCFL por etapas y
retirÃ³ tolerancia de especie antes de integrar. Ocho pruebas focales PASS.

G1 recto .75m/20mm,N250; G2 cadenaP4B,N251, ambos dxobjetivo3mm.
G2 configurado, **no ejecutado**. Motor, RPM3000 e iniciales canÃ³nicos:
tubo/exterior100kPa/500K/Y0/u0. La justificaciÃ³n cuantitativa de malla y
periodicidad (30mÃ¡ximo,3comparaciones tras ciclo5) precede al coste medido.

| MediciÃ³n G1 | Resultado |
|---|---:|
| Ciclos completos | 1, 180â†’540Â° |
| Solver / ciclo con postproceso | 261,563 / 263,328 s |
| ProyecciÃ³n30 ciclos / presupuesto | 7899,840 / 600 s |
| Pasos aceptados / RHS | 13164 / 35379 |
| HLLC / HLLE | 8861357 / 0 |
| Rechazos stage_CFL | 9051 |
| Balance global normalizado m/E/F | 4,45eâˆ’15 / 4,52eâˆ’15 / 1,37eâˆ’15 |
| MÃ¡ximo residuo etapa / segmento | 3,53eâˆ’16 / 1,15eâˆ’14 |
| Intercambio puerto m/E/F haciaC | âˆ’3,29831227eâˆ’5 kg / âˆ’23,08635686 J / âˆ’3,24525813eâˆ’6 kg |
| rho/p/T mÃ­nimos1D | 0,519827851 kg/mÂ³ / 99983,4422 Pa / 499,997876 K |
| Y mÃ­nimo/mÃ¡ximo1D | 0 / 0,4481253805 |
| Trazas de puerto cerrado | 13634, intercambio exactamente0 |
| Trazas con backflow | 0, no acreditado por este ciclo |

**E12 y E15 PASS Ãºnicamente para el ciclo medido**. EOS valida todas las
etapas1D y Model las0D, sin clipping. Extremos0D de trazas RHS guardadas:
p[91346,1073;1410384,7069]Pa,T[299,004389;1277,892918]K,Y[0;1]. No confundir
estos extremos muestreados con un listado de todos los estados intermedios.
El puerto es interno y no se suma como fuente externa del inventario conjunto.
Audit offline vuelve a sumar inventarios/ledger; diferencias de unos ULP entre
fsum y acumulaciÃ³n secuencial estÃ¡n expuestas, no se retocan los datos.

Calor numÃ©rico0,523078783273J, primitiva0,523078782839J;
diferencia4,3388eâˆ’10J. Especie quemada analÃ­tica6,53848478549eâˆ’7kg.
DiagnÃ³sticos indicados del **primer ciclo transitorio**, no prestaciones periÃ³dicas:
W=âˆ’0,418168664J, P=âˆ’20,9084332W, par=âˆ’0,0665536099Nm.
El signo negativo no se oculta ni se interpreta como potencia al eje.

El historial contiene sÃ³lo ciclo1; periodicidad=null. Guard30Ã—tiempo>600s
obliga STOP antes de G2 o ciclo2. Incluso mÃ­nimo7ciclos costarÃ­a1843,296s con
esta medida; no se cambia el mÃ­nimo ni la malla para forzar continuaciÃ³n.
**E13/E14 pendientes**: sin comparaciÃ³n G1/G2, tiempo/Ã¡ngulo de retorno ni
causalidad demostrada. backflow_local=true nativo es una comprobaciÃ³n vacua
en este ciclo; soporte P3/P4A previo no equivale a evidencia hÃ­brida nueva.

### Evidencia, comandos y regresiones

results/p4-r2-20260921/p4c conserva run nativo completo y arrays gzip;
hybrid-audit.json registra auditorÃ­a, hybrid-traces.png/svg muestran seÃ±ales
reales guardadas. Sensores efectivos0,1005/0,2985/0,4995m: p/u/M/Y cada paso,
p/u/T/Y/M en snapshots completos. Cara de puerto de segunda etapa y flujo
promedioSSPRK2 etiquetados; no se presentan como evaluaciÃ³n puntual idÃ©ntica.
No se guardÃ³ ni afirmÃ³ un checkpoint reanudable.

Comandos reales:

- `.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P4C_PREFLIGHT --dependency P2=docs/gasdynamic/p2_accepted_dependency.json`
- `.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P4_CLOSE --dependency P2=docs/gasdynamic/p2_accepted_dependency.json`
- `python -m dev_orchestrator.p4_hybrid_report results/p4-r2-20260921` (sÃ³lo auditorÃ­a/figuras offline).
- `openspec validate p4-escape-1d --strict --no-interactive`

P4_CLOSE:88 testsPASS(24,292s), mÃ¡s8focalesPASS; histÃ³rico offlineP0/P2/P3
todoPASS,0 nuevas integraciones de campaÃ±a en regresiones. P4A/P4B y151hashes
congelados intactos. El Python del venv no tiene matplotlib; generar figura con
Ã©l fallÃ³ tras guardar auditorÃ­a. Se usÃ³ Python3.11 existente con matplotlib para
postproceso, sin instalar dependencias ni repetir integraciÃ³n.

Ambos runs nativos tienen gateBLOCKED Ãºnicamente por review_not_approved del
hook dummy; no errores ni scopeviolations. Conservarlo, adjuntar revisiÃ³n
independiente separada. Ese bloqueo tÃ©cnico no sustituye al STOP cientÃ­fico/
operativo P4_BLOCKED_PERFORMANCE. AutorrevisiÃ³n de cÃ³digo/diff/figuras separada
de la revisiÃ³n read-only /root/p3_review. Sin aceptaciÃ³nP4, archivo, push niP5.

Dictamen independiente final: **P4_BLOCKED_PERFORMANCE**, R2/P4B aprobados,
96 tests y regresiones confirmadas, sin P4 PASS. Recibos separados:
results/p4-r2-20260921/independent-review.json y decision.json; inventario SHA256
de31 archivos de evidencia en inventory-all.json. OpenSpec estricto final PASS.
Commits previos:84b36b9 deltaR2,4747eb2 fuente previa,a3087ba mediciÃ³n/STOP.

## P4-R3 â€” orden5e36dbe4
- [x] Registrar aceptaciÃ³n humana R2/P4B, sin aceptar P4.
- [x] Perfil estÃ¡ndar y clasificaciÃ³n de coste antes de optimizaciÃ³n.
- [x] Optimizaciones aisladas y equivalencia por bloque.
- [x] Perfil intermedio, benchmark completo, regresiones y reviewer.
- [ ] Performance<=20s/ciclo, proyecciÃ³n30<=600s con margen.
- [ ] Reanudar periodicidad/G2 sÃ³lo con performance PASS.

## P4-C3-R3 â€” correcciÃ³n de auditorÃ­a supervisada (2026-09-28)

- [x] Corregir la captura pre/post: `stage_a` conserva `pre_cells`, `pre_z` y
  `pre_t` antes del commit; `op0/stage_a` aporta primitiva y flujos observados,
  `cells1/z1/op1` aporta `stage_b`, y `cells_new/z_new/ws_new` aporta `after`.
- [x] Alinear `interface_info` con `stage_a/op0`: `p_chamber`, cÃ¡mara,
  primera celda y `sample_time_pre_step` son pre-step; se conserva
  `history_record_time_post_step` para el commit-time del historial.
- [x] AÃ±adir prueba real de un paso: estados pre/post distintos, primitiva
  derivada consistente, presiÃ³n de cÃ¡mara derivada de `stage_a`, cÃ¡mara y
  primera celda alineadas, y ambos tiempos ordenados. Los siete tests focales
  existentes permanecen PASS.
- [x] Alinear la selecciÃ³n causal de retorno con `sample_time_pre_step`, con
  fallback al timestamp externo para compatibilidad.
- [x] Auditar la interfaz con `ExactRiemann` independiente y reconstruir la
  pared como ghost reflectante fÃ­sico `(rho,-u,p,Y)` mediante
  `ExactRiemann(last, ghost, EOS).sample(0)`; conservar `C2_VOLUME` y no usar
  HLLC productivo en el auditor.
- [x] Regenerar `results/p4-c3-r3-20260928` desde el fixture Ãºnico. Los nÃºmeros
  de `174b261` quedan `SUPERSEDED/INVALIDATED` por mezcla de captura pre/post;
  la fÃ­sica y el solver no cambian.
- [x] Resultado vigente: retorno `PASS`, `selected_time` pre-step
  `0.0026532366020821743 s`, flujo `0.0002698587123830558 kg/s`, y registro
  post-step `0.0026543865163682658 s`; ExactRiemann `INCONCLUSIVE`, errores
  relativos `(1.7797458457669132e-07, 3.4548877071827627e-06,
  6.581792616275487e-04, 8.898729228831856e-08)`, mÃ¡ximo
  `6.581792616275487e-04`; momento `max_abs_residual =
  5.840234051652552e-06`, `max_relative_residual = 1.9399428518812518`,
  `median_relative_residual = 0.018615083342715104`. ConservaciÃ³n `PASS`,
  residuo mÃ¡ximo `1.3929103469155642e-15`.
- [x] C3 permanece `P4_SCI_C3_INCONCLUSIVE`: no existe threshold aprobado y
  no se inventÃ³ ninguno; momentum max_abs/max_relative/median_relative son
  diagnÃ³sticos, no gate. E13 `NO EJECUTADO`; P9 `STOPPED`.

### P4_R3_COMPILED_BACKEND_DECISION_REQUIRED

R2/P4B aceptados por la usuaria, recibo docs/gasdynamic/p4_r3_acceptance.json.
NO P4_HUMAN_ACCEPTED. Contratos/physics/meshN250/CFL/eventos/0D intactos.
SCALAR_REFERENCE disponible por motorsim.hybrid_exhaust y selector interno
hybrid_fast.run_cycle(...,backend='SCALAR_REFERENCE'/'STRUCTURAL'/'NUMPY').
No import productivo de estos backends ni cambio UI/JSON/EXE.

| Camino | Wall, s/ciclo | CPU, s | Speedup | 30ciclos, s |
|---|---:|---:|---:|---:|
| ReferenciaR2 | 263,328 | No registrado | 1Ã— | 7899,840 |
| CachÃ©s estructurales | 226,773529 | 226,203125 | 1,161Ã— | 6803,206 |
| NumPy1 | 35,469199 | 35,406250 | 7,424Ã— | 1064,076 |
| NumPy2 | 35,443038 | 35,250000 | 7,430Ã— | 1063,291 |

Tres ventanas100Âµs antes/intermedio/despuÃ©s:17,531/13,709/1,047s con cProfile.
Al ser viable se perfilÃ³ ademÃ¡s el ciclo NumPy completo:63,682498s instrumentados,
**excluidos** de la comparaciÃ³n de performance. Top final inclusivo: RHS55,52%,
HLLC25,15%, evaluaciÃ³n0D24,52%, MUSCL11,27%, primitivas7,50%; no sumar anidados.
Tabla completa self/inclusive/calls, CPU/RAM, clasificaciÃ³nAâ€“F y opcionesAâ€“D:
docs/gasdynamic/p4_r3_performance.md. No se midieron allocations acumuladas ni
se inventan CPU/RAM del baseline histÃ³rico. Mismo Windows10/i5-10400/Python3.11.0.

Bloque1cachea primitivas inmutables, geometrÃ­a y evaluaciÃ³n0D por estado/tiempo;
equivalencia exacta antes del siguiente bloque. Bloque2NumPy2.3.0 aplica las
mismas operaciones float64 a EOS/MUSCL/HLLC/CFL y avances de celdas; BC/P3 y
fallbacks siguen escalares congelados. Fallback/downgrade por cara/celda;
puerto agrega conteo por cara sin subrazÃ³n interna inventada. Dependencia sÃ³lo
requirements-experimental.txt; pip check PASS, sin compilados/globales.

Equivalencia **exacta, mÃ¡ximo absoluto0** para estados0D/1D, pC/pPuerto,
flujosm/E/F, sensores, trabajo, inventarios/ledgers en bloque1, ambas medidas
NumPy y perfil completo. Mismos eventos,13164pasos/26328etapas aceptadas,
35379RHS,8861357HLLC/0HLLE,9051rechazosCFL. Revisor verificÃ³ histories/stages
completos. Balances/admisibilidad y ausencia de backflow coinciden conR2.
Performance mejora sustancialmente, pero NO cumple; no periÃ³dico/G2/E14/P4PASS.

### Regresiones y revisiÃ³n

101 testsPASS(25,178s):88 histÃ³ricos +8 adaptador +5 batch. EOS/MUSCL/HLLC/HLLE,
supersÃ³nico/igualdad/downgrade y dos microintegraciones descarga/backflow contra
referencia. Replay offline adicional:3P4A+16P4B,190 snapshots/finales,27050caras,
igualdad exacta. Gates histÃ³ricos aceptados intactos; P0/P2/P3 offlinePASS,
151hashes histÃ³ricos y cinco referenciasR3 intactos. No repetir campaÃ±as largas.

Primer cierreFAILED_INFRASTRUCTURE: el archivo nuevo gas1d/batch.py alteraba
inventario glob congeladoP2, sin cambiar archivos cientÃ­ficos. Movido a
motorsim/exhaust_batch.py; cuerpo idÃ©ntico exceptoimports, no tocarvalidadores.
Fallo conservado en regression-infrastructure-failure; correcciÃ³n en
namespace-correction.json; regresiÃ³n posteriorPASS. Reviewer confirmÃ³ fix sin
necesidad de repetir benchmark; el perfil completo posterior tambiÃ©n fue exacto.

AutorrevisiÃ³n de fuentes/diff separada de revisiÃ³n independiente read-only
/root/p3_review: confirma perfiles/equivalencia/101tests/replay/bloqueo. No
ejecutÃ³ integraciones; sÃ³lo lecturas y evaluaciones puntuales de kernels.
Runs nativos restantes BLOCKED por review_not_approved del hook dummy,
sin errors/scopeviolations; conservar junto al dictamen externo independiente.
El estado tÃ©cnico del hook no sustituye la decisiÃ³n de performance.

### Evidencia y reproducciÃ³n

results/p4-r3-20260921: artifacts/ contiene perfilbase; structural/ el bloque1;
numpy/ las dos medidas finales y perfilporventanas; full-profile/ perfilcompleto;
regression/ la comprobaciÃ³n final; decision.json e independent-review.json
separan resultado medido, aceptaciÃ³n humana y revisiÃ³n. Mantener originales.

Comandos ejecutados (no relanzar automÃ¡ticamente):

- `.venv\Scripts\python.exe -m pip install -r requirements-experimental.txt`
- `.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P4_R3_PROFILE --dependency P2=docs/gasdynamic/p2_accepted_dependency.json`
- Misma invocaciÃ³n con P4_R3_STRUCTURAL, P4_R3_NUMPY, P4_R3_CLOSE y P4_R3_FULL_PROFILE.
- `.venv\Scripts\python.exe -m unittest discover -s tests -p test_gas1d_batch.py -v`
- `openspec validate p4-escape-1d --strict --no-interactive`

Falta decisiÃ³n humana sobre AcontinuarNumPy/BNumba/CextensiÃ³n/DresoluciÃ³nfutura.
Para20s falta1,77346Ã— adicional,43,613% menos wall. Cotas instrumentadasAmdahl
orientativas en el documento, no promesa de compilaciÃ³n. No implementarB/C,
ampliar600s, aceptarP4, archivar, publicar ni iniciarP5. Borrado ajeno preservado.

OpenSpec estricto final PASS; inventario SHA256 de82 archivos de evidencia.
Commits:75210ad aceptaciÃ³n/perfil,655b9a9 bloqueestructural,5e7680e batching,
2675763 benchmarks,d89dc70 correcciÃ³nnamespace,11ff512 regresiones/perfilcompleto.
## P4-R4 â€” evaluaciÃ³n Numba serial (orden 8f6dbacb)

- [x] Compatibilidad registrada: Windows 10 x64, Python 3.11.0, NumPy 2.3.0, Numba 0.62.1, llvmlite 0.45.1; `pip check` PASS. No se cambiÃ³ Python/NumPy ni packaging.
- [x] HLLC float64 `njit(cache=True, fastmath=False, parallel=False)` y backend seleccionable `NUMBA_EXPERIMENTAL`; SCALAR/NUMPY permanecen disponibles.
- [x] Microbenchmark: equivalencia PASS con tolerancia prefijada; caras G1 480Â° 1,51879Ã— (diagnÃ³stico aleatorio 0,98782Ã— conservado). JIT inicial 4,779 s en el fixture G1.
- [x] Focal: tres ventanas congeladas G1, equivalencia completa de estados, historia, eventos, contadores, balances y observables; 5 tests Numba PASS; speedups 1,665Ã— / 1,864Ã— / 1,335Ã—.
- [x] Dos G1 completos calientes: 37,313 s (primero, JIT fuera del resultado) y 26,599 s; equivalencia exacta, 13.164 pasos, 26.328 RHS aceptados, 35.379 RHS totales, 8.861.357 HLLC, 0 HLLE, 9.051 rechazos. ProyecciÃ³n 30 ciclos 1.119,38 s / 797,98 s.
- [x] OpenSpec estricto PASS y regresiones focales Numba PASS.
- [x] Suite pertinente P0/P1/P2/P3/P4 y Numba: 106 tests PASS (24,100 s). La ejecuciÃ³n amplia de 449 tests conserva cinco fallos preexistentes/ambientales fuera de R4 (P1 habilitada por roadmap, UI CAE, P0 baseline y dos lÃ­mites de memoria/cancelaciÃ³n); no se atribuyen al backend.
- [ ] Gate de rendimiento: **P4_R4_NUMBA_NATIVE_EXTENSION_DECISION_REQUIRED** (>25 s/ciclo; la segunda mediciÃ³n sigue sobre 20â€“25 s). No iniciar periodicidad G1, G2, E14 ni P5.
- [ ] RevisiÃ³n independiente conectada: el runner dummy quedÃ³ BLOCKED por `review_not_approved`; conservar la evidencia y distinguirla de la autorrevisiÃ³n.

Evidencia: `results/p4-r4-20260921/artifacts/benchmark.json`,
`dev_orchestrator/runs/20260921T134738-P4_R4_FOCAL-c72685bc1449/artifacts/focal.json`
y `dev_orchestrator/runs/20260921T134518-P4_R4_MICRO-2fc258aaeab7/artifacts/micro.json`.

## P4-R5 â€” fusiÃ³n del hot path Numba antes de extensiÃ³n nativa (orden fusiÃ³n)

- [x] RevisiÃ³n independiente P4-R4 read-only repetida; dummy BLOCKED conservado; revisiÃ³n real **INDEPENDENT_REVIEW_PENDING** (sin reviewer conectado), checklist float64/fastmath/parallel/equivalencia/benchmark/JIT/tests.
- [x] Ciencia congelada: Euler quasi1D/HLLC/HLLE/MUSCL/minmod/SSP-RK2/CFL/EOS/source/P3/port/geometrÃ­a/eventos/malla G1 250 verificados, fastmath=False parallel=False.
- [x] Perfil backend Numba actual (26.599 s) en 12 categorÃ­as A-L (Python 41.6%, SSP 15.3%, HLLC 12.6%, diagnÃ³sticos 8.8%, etc.) y cProfile top20; sin optimizar antes de identificar hotspots.
- [x] MediciÃ³n de crossings: 106137 Pythonâ†’Numba, 35379 HLLC faces (8.861.357 flujos), 48546 primitives, 176895 face_state, 74874 coupling, ~1.45 GB allocations temporales por ciclo.
- [x] Kernel fusionado `gas1d_rhs_numba` en `motorsim/exhaust_numba.py` + `exhaust_numba_fused.py` (`FUSED_ENABLED=True`): primitive+MUSCL+HLLC en una sola regiÃ³n compilada, sin duplicar fÃ­sica, comparando contra SCALAR/NUMPY/NUMBA_R4.
- [x] Arrays de trabajo prealocados y reutilizados (w, lf, rf, flux, speeds, codes, bad) sin aliasing que cambie estados; in-place autorizado con equivalencia matemÃ¡tica y preservaciÃ³n de q^n/stages/ledgers; 3 tests aliasing PASS.
- [x] Gate focal: 3 ventanas G1 idÃ©nticas a R4, equivalencia exacta 11/11 campos, speedups R5 vs R4 1.136Ã—/1.519Ã—/1.411Ã— agregado 1.33Ã— â‰¥1.2 PASS.
- [x] Microbenchmark 1000 RHS: R4 0.381653 s vs R5 0.069238 s speedup 5.512Ã— â‰¥1.15 PASS.
- [x] Dos G1 completos calientes con JIT fuera: 19.519 s / 19.223 s wall (19.141/19.187 cycle), equivalencia exacta 13 campos, 13.164 pasos, 35.379 RHS, 8.861.357 HLLC, proyecciÃ³n 30Ã— 574.92 s â‰¤600 â†’ **P4_R5_NUMBA_FUSED_PERFORMANCE_PASS** (â‰¤20 s). Segunda medida tambiÃ©n 19.18 <20, mediana 19.16.
- [x] Periodicidad G1: 30 ciclos con NUMBA_FUSED, sin streak 3 PASS (sensor_max ~0.60, work_rel 0.03); G2 15 ciclos diagnÃ³stico similar; E14 requiere G1 PASS, no acreditado. Checkpoints deterministas por ciclo guardados. Estado final **P4_BLOCKED_PERIODIC_CONVERGENCE** (no P4 PASS, no P5).
- [x] Regresiones: 101 tests patrÃ³n P4_R3_CLOSE PASS (26.371 s) + 5 Numba + 3 aliasing fused = 109 (106 pertinentes), OpenSpec estricto PASS, 449 amplios con 5 fallos preexistentes no atribuidos.
- [x] RevisiÃ³n final read-only sobre profile/kernel/equivalencia/fastmath/parallel/allocations/SSP/balances/benchmark/regresiones; dummy BLOCKED conservado.

Evidencia: `results/p4-r5-20260921/artifacts/` (profile_r4/r5, crossings, micro_rhs, focal, benchmark, periodic), `docs/gasdynamic/p4_r5_fused.md`, `results/p4-r5-20260921/decision.json`, `results/p4-r5-20260921/independent-review.json` (INDEPENDENT_REVIEW_PENDING), `motorsim/exhaust_numba_fused.py`.

## P4-R6 â€” diagnÃ³stico de periodicidad / posible Ã³rbita de perÃ­odo 2 (orden diagnÃ³stico)

- [x] D1 exacto 1â€“30 con thresholds contractuales, tablas completas work/cyl/sensor/port/inventarios y sensor_max localizado (sensor 0, fase 123.5â€“124Â°, p~100k vs 30k, denom~100k, metric 0.60).
- [x] D2/diagnÃ³stico lag2 (n vs n-2): work 0.00005â€“0.001, sensor_max 0.006â€“0.02 tras ciclo 24 vs D1 0.60; D3â‰ˆD1, D4â‰ˆD2 â†’ perÃ­odo 2.
- [x] Vector X_n (I/K/C + pipe integrals): ||X_n-X_{n-1}|| max 0.324, ||X_n-X_{n-2}|| max 0.00004â€“0.0007 sostenido â†’ `PERIOD_2_ORBIT_CANDIDATE`.
- [x] Invariancia 360Â°: geometry/port.area/events/volumes/dV idÃ©nticos theta vs theta+360 exacto; HybridSystem heat_start +360 correcto â†’ PASS.
- [x] Handoff nâ†’n+1: state/cells/inventories/angle/composition/ledger exactos, sin reinicializaciÃ³n silenciosa â†’ PASS.
- [x] BÃºsqueda 720Â°: 720 solo en mÃ³dulos 4T, no en camino hÃ­brido 2T â†’ `PERIOD_MAPPING_DEFECT` no encontrado.
- [x] Restart determinism: checkpoint G1-28 â†’ rerun ciclo 29 reproduce exacto (state/cells/work/history 0 diff) â†’ PASS.
- [x] Odd/even: W odd 13.838 vs even 13.331 (diff 3.6%), cada subsecuencia converge (5e-05/0.00014); pipe mass odd 1.48e-04 vs even 1.04e-04, port mass odd -6.54e-05 vs even -4.92e-05; divergencia ya en pipe al inicio del ciclo.
- [x] G2 15 ciclos: D1 sensor_max 0.005 en 4â€“5 luego 0.46â€“0.55, D2 sensor_max 0.004â€“0.009 tras ciclo 7 â†’ mismo patrÃ³n period-2, causa comÃºn.
- [x] ClasificaciÃ³n: **P4_R6_PERIOD_2_ORBIT_CONFIRMED** â€” 360 PASS, handoff PASS, metric no defect, D2/vector convergen, D1 no, odd/even reproducibles. No P4 PASS, `SCIENTIFIC_CHANGE_REQUIRED`, STOP, no P5. No promediar ni relajar thresholds.

Evidencia: `results/p4-r6-20260921/artifacts/diagnosis.json` (D1/D2/D3/D4, vector, odd/even), `results/p4-r6-20260921/artifacts/g1_cycles/` (30), `g2_cycles/` (15), `docs/gasdynamic/p4_r6_diagnosis.md`, `results/p4-r6-20260921/decision.json`.

## P4-R7 â€” robustez numÃ©rica de la Ã³rbita de perÃ­odo 2 (orden diagnÃ³stico)

- [x] A/B = finales ciclo 29/30 (hashes 449a31/3421b6) con N250/CFL0.4/NUMBA_FUSED.
- [x] Cierre PoincarÃ©: Aâ†’B* exact 0.0 PASS, Bâ†’A* work 0.00040 vector 0.000033 PASS, sensor 0.02650 >0.005 pero <<0.60 D1 y consistente con lag2 histÃ³rico 0.015; cross A* vs B sensor 0.60 FAIL confirma period-2.
- [x] ContinuaciÃ³n 6 ciclos desde A: D1 sensor 0.60 FAIL, D2 sensor 0.01â€“0.05 FAIL per 0.005 pero work/vector PASS, sin 3 D2 consecutivos sensor PASS.
- [x] Backend 4 ciclos desde ciclo28: NUMBA_FUSED vs NUMPY_REFERENCE diff 0.0 exact, misma clasificaciÃ³n period-2 â†’ PASS.
- [x] CFL 8 ciclos desde ciclo28: 0.4 vs 0.2 work diff 2e-05 sensor 0.603 vs 0.603, D1/D2 idÃ©nticos â†’ period-2 persiste, no `TIME_SENSITIVE`.
- [x] Espacial G1 canÃ³nico N200(200)/N250(250)/N300(300) 10â€“30 ciclos: N200 amp 0.281 mean 13.595, N250 amp 0.253 mean 13.584, N300 amp 0.128 mean 13.529, todos period-2, amplitud no crece â†’ `SPATIAL` PASS.
- [x] ComparaciÃ³n Ã³rbita: mean 13.5â€“13.6, amplitudes 0.28/0.25/0.12, Delta_AB p_cyl min 56 Pa en 348Â° max 237k Pa en 179.5Â° amplificaciÃ³n desde 81.5Â° (blowdown).
- [x] ConservaciÃ³n/admisibilidad/CFL PASS en todas las variantes.
- [x] ClasificaciÃ³n: **P4_R7_PERIOD_2_ROBUST_NUMERICAL_ORBIT** (Caso A con matiz sensor) â€” robusta numÃ©ricamente como period-2 (backend/CFL/espacial), aunque sensor estricto 0.005 no se alcanza ni en lag2 original; requiere decisiÃ³n cientÃ­fica para E13. No P4 PASS, no P5, no multicore AUTO (workers=1).

Evidencia: `results/p4-r7-20260921/closure.json`, `continuation.json`, `backend.json`, `cfl.json`, `spatial_N*.json`, `orbit_comparison.json`, `docs/gasdynamic/p4_r7_robustness.md`, `results/p4-r7-20260921/decision.json` (multicore no modificado, workers=1).

## P4-R12 â€” cierre por ramas (orden 87e62d1e)

- [x] AuditorÃ­a N400 ciclo54 vÃ¡lida: continuaciÃ³n normal desde `restart_cycle50`; D2 compara 54 contra 52 y reproduce `sensor_max=0.009046195029969764`; conservaciÃ³n/admisibilidad PASS.
- [x] ContinuaciÃ³n Ãºnica N350 desde `restart_cycle50`: sÃ³lo ciclos 51 y 52 ejecutados; ciclo52 PASS, conservaciÃ³n/admisibilidad PASS.
- [x] Seguimientos impar/par independientes: N350 impar 5, par 3; N400 impar 6, par 2 con secuencia par `[PASS,PASS,FAIL]`.
- [x] CorrecciÃ³n de serializaciÃ³n booleana: JSON `true`/`false`, nunca cadenas; tests especÃ­ficos de streak y `numpy.bool_` PASS.
- [x] R11 corregido y separado: `P4_R11_PERIOD2_LAG2_CLOSURE_CONFIRMED` permanece vÃ¡lido bajo su contrato global.
- [x] ClasificaciÃ³n terminal R12: **P4_R12_ONE_BRANCH_NONCLOSURE**.
- [x] OpenSpec estricto PASS; no se ejecutaron N400 56/58/60, E13-R1, P4 PASS ni P5.

## P4-R13 â€” horizonte fijo N400 (orden 235a9a48)

- [x] Restart54 validado: N400, backend NUMBA_FUSED, CFL 0,4, float64, Ã¡ngulo/ciclo 54; continuaciÃ³n fÃ­sica 55â€“60 sin early stop.
- [x] Ciclos 55, 56, 57, 58, 59 y 60 completados con conservaciÃ³n/admisibilidad PASS; checkpoints y FULL_DEBUG guardados.
- [x] Comparaciones disponibles: 58 vs 56 y 60 vs 58 PASS; control impar 57 vs 55 y 59 vs 57 PASS.
- [x] Se conserva el FAIL R12 de 54 (`0.009046195029969764`); 56 vs 54 queda como brecha explÃ­cita porque R12 no guardÃ³ historia angular completa y no se repitiÃ³ R12.
- [x] Horizonte termina en 60; no se ejecutaron 62+, N350/N300/N500, E13-R1, P4 PASS ni P5.
- [x] ClasificaciÃ³n conservadora: **P4_R13_N400_EVEN_INTERMITTENT_NONCLOSURE**; no se acredita cierre eventual sin 56 vs 54.
- [x] Tests R13/R12: 10 PASS; OpenSpec estricto PASS.

## P4-R13A â€” cierre de evidencia 56 vs 54

- [x] Replay sÃ³lo 51â€“54 desde el restart N400 ciclo50; terminal ciclo54 bitwise exacto contra restart R12: `P4_R13A_CYCLE54_REPLAY_EQUIVALENCE_PASS`.
- [x] Reutilizado el `full_cycle56.json.gz` existente; 56 vs 54 PASS, `sensor_max=0.0011905119731371136`, sensor dominante 0, fase 132,5Â°.
- [x] Secuencia par sin gap: 50 PASS, 52 PASS, 54 FAIL, 56 PASS, 58 PASS, 60 PASS.
- [x] ClasificaciÃ³n corregida: **P4_R13_N400_EVEN_EVENTUAL_CLOSURE**; el FAIL de 54 permanece visible.
- [x] Tests R13A/R13/R12: 15 PASS; OpenSpec estricto PASS.
- [x] No se repitieron 55/56 de R13, no se ejecutaron 61+, E13-R1, P4 PASS ni P5.
- [x] 23/09/2026 â€” DecisiÃ³n humana: P4 BLOCKED/NOT_GRANTED y P5 AUTHORIZED_CONDITIONAL; documentaciÃ³n actualizada. No se implementÃ³ P5 ni se reabriÃ³ P4.

## P4-C3-R5 â€” contrato aprobado 2026-09-28 (sin adquisiciÃ³n)

### Correcciones de revisiÃ³n P1/P2

- [x] Exigir `solver_time` y `target_final_time` finitos, con llegada al objetivo;
  conservar `INCONCLUSIVE` para evidencia ausente/truncada y `FAIL` sÃ³lo para
  estados explÃ­citos de fallo del solver.
- [x] Blindar A/B0/B1 frente a caras, fluxes, ondas y razones persistidas
  ausentes, cortas o no numÃ©ricas; mantener `FAIL` para contradicciÃ³n semÃ¡ntica
  vÃ¡lida de `fallback_reason`.
- [x] Ejecutar tests focales P4-C3-R5/R4/return y OpenSpec estricto; no ejecutar
  adquisiciÃ³n, E13/G2 ni P9.

- [x] Congelar recibo aprobado A/B0/B1/B2 en `p4_c3_r5_preregistration_proposal.md`;
  C3 sigue `P4_SCI_C3_INCONCLUSIVE`, E13/G2 `NOT_EXECUTED`, P9 `STOPPED`.
- [x] Capturar diagnÃ³sticamente todas las caras de momentum de stage A/B:
  estados reconstruidos, flux vectorial completo, ondas, fallback y `down`.
- [x] Auditar B0 independiente con identidad exacta de caras y
  `downgraded_cells`; cualquier ausencia/diferencia bloquea B1/B2.
- [x] Auditar B1 independiente HLLC/HLLE con paridad exacta de vector, ondas y
  razÃ³n; no usar ULP ni umbral de magnitud frente a ExactRiemann.
- [x] Auditar B2 con replay bitwise de fuente, RHS, `q1`, `q2` y combinaciÃ³n
  SSPRK2 en checkpoints declarados; conservar residual de volumen como mÃ©trica.
- [x] AÃ±adir pruebas sintÃ©ticas de independencia, mutaciÃ³n, fallback, runtime,
  serializaciÃ³n/hash y un caso analÃ­tico B2 no fabricado por el helper.
- [x] Ejecutar sÃ³lo tests focales y OpenSpec estricto; no ejecutar adquisiciÃ³n
  C3-R5, E13/G2, P9 ni campaÃ±as costosas.

- [ ] RevisiÃ³n independiente final R5 sin hallazgos bloqueantes.
- [ ] Ejecutar exactamente una adquisiciÃ³n focal C3-R5 y persistir evidencia;
  no ejecutar E13/G2 ni P9.

