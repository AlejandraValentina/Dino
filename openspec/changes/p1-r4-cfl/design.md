# P1-R4 — protocolo previo a ejecución

## Métrica exacta y origen
Fuente congelada:2143a60; implementación numérica b353e90. T11 repite T03:
Euler quasi-1D, área0,01m² constante, L=1m, N800, gamma1,35, R287,
p0=100000Pa,T0=300K,Y0=0,3; pulso gaussiano derecho centro0,25m,
anchura0,04m, amplitud prescrita1e-4*p0=10Pa; BC no reflectivas BASE explícita.
Tiempo final0,45L/a0. Inicial y referencia son integrales conservadas por celda;
p se obtiene de las primitivas de esos promedios conservados.

A(N,C)=max_i[p_i(t_final)-p0], en Pa. No sensor, promedio espacial, integral,
FFT ni amplitud ajustada. Valores históricos A(800,0,6)=8,832393583405064Pa
 y A(800,0,2)=7,99875531278667Pa. Métrica S=abs(Aa-Ab)/10;
denominador10Pa es el parámetro continuo inicial, no el máximo inicial discreto
ni el pico numérico del run de referencia. S=.0833638270618394>0,08.
Diferencia absoluta=.833638270618394Pa. No reinterpretar esta métrica.

0,08 aparece originalmente en5b6b62f, docs/gasdynamic/1d_verification_plan_v1.md,
T11, y manifestv1. La orden original P1 pidió definir ensayo CFL pero no dio0,08.
No hay derivación ni fuente que produzca ese número en documentos/revisión
conservados: tolerancia práctica contractual, no constante física ni boundteórico.
T11 se denomina sensibilidad, no estabilidad; su fallo histórico es válido.
Sod E1<=.015 y diferencia de velocidad<=.005a0 son gates distintos y se conservan.

## Implementación congelada
No editar motorsim/, ni contratos v1/R2/R3, producción0D o evidencia anterior.
Adaptador dev_orchestrator llama definition/solve/measure existentes; cambia
únicamente parámetros de estudio N/CFL fuera del código productivo. Sin monkeypatch.
Manifest previo de hashes de todos los módulosgas1d y documentos normativos.

## Matriz fijada y coste
Primero repetir exactamente T03N800 CFL0,2/0,4/0,6 y comparar arrays/ledger,
contadores y métricas con p2a-attempt-2 deR3 (excluir únicamente wall_seconds).
Estas tres ejecuciones son también la fila contractual del estudio; no duplicarlas.
Luego N400 y1600 con CFL0,1/0,2/0,4/0,6 y N800CFL0,1:12 runs nuevos en total.
Mismo tiempo físico, IC/BC, EOS, método, source, referencia y métricas.
CFL0,1 es diagnóstico temporal del MISMO esquema espacial, no verdad exacta deEuler:
menor paso puede incrementar difusión neta respecto de la solución continua.
Comparar cadaCFL con0,1 de su misma malla y las parejas.2/.4,.4/.6,.2/.6.

N3200 opcional omitido: con24s paraN800CFL.2 y costeO(N²), cuatroCFL
adicionales requerirían~1470s, frente~483s para la matriz principal.
Límite porcaso320s, conjunto900s de adaptador (timeout fase1020s); sin retries.
Registrar fallos sin modificar solver y clasificar infraestructura si timeout.

Porrun: A, diferenciaabs/10, erroresparentT03, amplitudanalítica discreta,
steps, dtmin/max (ledger), CFLrealm ax, residual4componentes, rho/p/Tmínimos,
Ymin/max, HLLC/HLLE, rechazos, runtime. Arrays/ledger/hash completos.
Estabilidad=admisibilidad/conservación<=1e-10/completitud; sensibilidad=comparación
A. Parentgates aN400 se registran como diagnóstico, no se impone allí elgateN800.
No convertir un parenterror grueso en inestabilidad.

## Hipótesis y referencia independiente
Para rama acústica lineal upwind+FE, Taylor da
q_t+a0*q_x=nu_num*q_xx+O(dx²), nu_num=a0*dx*(1-C)/2.
La gaussiana tiene pico aproximado10/sqrt(1+4*nu_num*t/0,04²).
Predicción sin ajustar coeficientes: mayorCFL amortigua menos; diferencias
entreCFL decaen con dx. No es cota rigurosa de HLLC no lineal ni fija tolerancia.
Fuente primaria: LeVeque, notas ecuación modificada,
https://faculty.washington.edu/rjl/classes/hyperbolic2013/am574w2011/am574lecture6.pdf
Tres mallas pueden respaldar tendencia, no demostrar un límite asintótico.

## Decisión posterior
Sin umbral nuevo previo a evidencia. Revisar estabilidad, errores frente solución
acústica independiente, disminución sistemática de sensibilidad y comportamiento.6.
Si no converge: UNRESOLVED o CFL06_NOT_ACCREDITED; no cambiar contrato.
Si casoA respaldado, diseñar gate con estabilidad, ledger original, refinamiento
y límite cuantitativo de exactitud (mantener al menos gatesT03 originales).
No redondear.08 a.09/.10 ni usar predicción aproximada como cota rigurosa.
Revisión independiente read-only de métrica, datos y eventual criterio antes de
adopciónR4. No aprobarP2A todavía. TrasR4PASS ejecutar soloT11 primero;
regresiones necesarias después. P2B/P3 no se usan para rescatar esteestudio.
