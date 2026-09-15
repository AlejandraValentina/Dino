## Context y estado de autorización
Modelo, caso, aproximaciones y protocolo aprobados expresamente por la usuaria
el 15/09/2026 para implementar y ejecutar el prototipo de consola. Se conserva
debajo la definición y sus tolerancias previas; las menciones a aprobación futura
describen su estado documental original. No se autoriza integración Qt, JSON,
ondas, barridos ni entrega 6. Evidencia de ejecución en tasks.md.
Se recomienda **modelo 0D de cuatro volúmenes homogéneos con restricciones
cuasiestacionarias reversibles**. Solo monocilíndrico 2T atmosférico de encendido por
chispa, admisión al cárter por falda recta, un régimen y una condición sintética.
La chispa se aproxima por un inicio de aporte energético prescrito; no se predice llama.
Diferir ondas/inercia reduce la capacidad sobre el escape y necesita aprobación.
Ninguna validación documental autoriza por sí sola el prototipo ni la integración Qt.

## Decisions: circuito y estados
Circuito fijo, enlaces bidireccionales (flechas indican únicamente signo positivo):

`reservorio exterior I → conducto I → cárter → transferencias → cilindro → conducto E → reservorio exterior E`

Cuatro estados propios: conducto de admisión I, cárter K, cilindro C, conducto de
escape E. Cada uno integra masa m [kg], energía interna sensible U [J] y masa de
carga fresca F [kg]; residual Rm=m−F es derivado. Uniformidad instantánea de p/T/Y
por volumen, sin cantidad de movimiento, energía cinética macroscópica ni potencial.
Reservorios exteriores infinitos: p absoluta [Pa], T [K] y fracción fresca Y fija;
no integran estado ni devuelven automáticamente la mezcla que salió anteriormente.
Los enlaces no almacenan masa/energía. La elección de sistemas abiertos se apoya
en balances de volumen de control [1]; el precedente 2T de [4] sustenta esta división
termodinámica, no sus calibraciones ni el modelo más complejo de aquella publicación.

Gas ideal caloríficamente perfecto, mismas propiedades para fresca/residual:

- Y=F/m; T=U/(m*cv); p=m*R*T/V; u=cv*T; h=cp*T.
- R=287 J/(kg K); gamma=1.35; cv=R/(gamma−1)=820 y cp=1107 J/(kg K).

Estos valores son parámetros sintéticos explícitos, no propiedades de productos
reales a alta temperatura. Sin disociación, reacción química ni variación de cp(T).
Las relaciones caloríficas y pV sustentan el cierre, no la elección numérica [2].

## Balances y signos
Para cada volumen i, evaluando todos los enlaces con el mismo estado de etapa:

```
dm_i/dt = sum_in(q) − sum_out(q)                         [kg/s]
dU_i/dt = sum_in(q*h_donante) − sum_out(q*h_i)
          − p_i*dV_i/dt + Qdot_i                       [J/s]
dF_i/dt = sum_in(q*Y_donante) − sum_out(q*Y_i) − Bdot_i  [kg/s]
```

q es magnitud no negativa; la selección de donante sigue el signo físico del enlace.
Un flujo interno se computa una sola vez: mismo q, h y Y con signos opuestos en
ambos extremos. h es entalpía de remanso del donante homogéneo; el chorro se mezcla
y disipa en el receptor sin sustraer dos veces su energía cinética. No se añade
trabajo de flujo p/rho aparte de h [1]. Bdot solo convierte el marcador fresco en
residual en C; no destruye masa total. Qdot solo aporta energía en C.

Trabajo indicado objetivo: W_C=integral_ciclo(p_C*dV_C) [J/ciclo], positivo si el gas
trabaja sobre el pistón, incluyendo todo el ciclo abierto. Registrar además W_K=
integral(p_K*dV_K) como diagnóstico de bombeo del cárter. W_C no descuenta ese
trabajo ni fricción y **no es trabajo al eje**; no inferir potencia/par al freno.

## Volúmenes variables y geometría reutilizada
En las ecuaciones se convierten mm→m, mm²→m² (1e−6) y cm³→m³ (1e−6).
Con r=S/2, biela l, ángulo theta en radianes para funciones trigonométricas:

```
x = r*(1−cos(theta)) + l − sqrt(l²−r²*sin(theta)²)
dx/dtheta = r*sin(theta) + r²*sin(theta)*cos(theta)/sqrt(l²−r²*sin(theta)²)
A_p = pi*D²/4; V_d=A_p*S; V_clear=V_d/(C_geom−1)
V_C = V_clear + A_p*x
V_K = V_K_PMI + A_p*(S−x)
dV_C/dt = A_p*(dx/dtheta)*omega; dV_K/dt = −dV_C/dt
omega = 2*pi*n/60 [rad/s]; dtheta_deg/dt=6*n [grados/s]
```

Reutilizar `kinematics.piston_position` (forma racionalizada estable) y sus
convenciones; no interpolar la tabla de un grado para integrar. K supone área
inferior del pistón igual a A_p y que el desplazamiento de biela/cigüeñal no agrega
variación angular: queda absorbido en el volumen libre de PMI. Sin fugas, sin
volúmenes de transferencias ni conductos añadidos al valor registrado. Hipótesis
por aprobar, no deducida del JSON. V_C+V_K constante es un control geométrico.

Ventanas: conservar las leyes de `ports.py` y `intake.py`, evaluadas al ángulo actual:
A_escape/transfer=w*max(0,min(h,x−u)); A_adm=w*max(0,min(h,u+h−f−x)), en mm².
La admisión requiere u>=S y 0<d=u+h−f<S para el caso con encendido; ninguna fila
sin función participa por inferencia. Ventanas de igual función son enlaces en
paralelo entre los mismos volúmenes, no un único conducto por cada lumbrera.

## Restricciones y retorno de flujo
En cada enlace de área geométrica A, A_ef=Cd*A. Cd es explícito, constante,
igual en ambos sentidos para este caso; no se supone que A geométrica sea efectiva.
Elegir el extremo de mayor p como aguas arriba (p_u,T_u,Y_u); el otro es p_d.
Reservorios/CV en reposo se tratan como estados de remanso; enlace adiabático,
cuasiestacionario, descarga en volumen bien mezclado. p iguales o A=0 ⇒ q=0.
Con beta=p_d/p_u y beta_crit=(2/(gamma+1))**(gamma/(gamma−1)):

```
q = Cd*A*p_u/sqrt(R*T_u) * Phi(beta)                       [kg/s]
Phi = sqrt(2*gamma/(gamma−1) * (beta**(2/gamma) − beta**((gamma+1)/gamma)))
      si beta_crit < beta <= 1
Phi = sqrt(gamma)*(2/(gamma+1))**((gamma+1)/(2*(gamma−1)))
      si 0 < beta <= beta_crit
```

Se cambia donante, signo, h e Y juntos al invertirse presión, también en
transferencias y ventanas. No hay válvulas antirretorno ficticias. La ley de
estrangulamiento deriva de flujo isentrópico compresible [3]; Cd representa una
corrección empírica propuesta, **sin calibrar**, no una validación de esa ley en
las ventanas reales. No se resuelven recuperación de presión ni choques de chorro.

## Conductos: capacidad que se propone reducir
Cada recorrido del editor se reduce a **un depósito 0D de volumen fijo**:
V_I/E=sum(V_tramo); A_min,I/E=min(pi*D1²/4,pi*D2²/4 de todos los tramos).
Una restricción de A_min conecta I con su reservorio exterior y otra E con el suyo;
son pérdidas concentradas asignadas a los extremos exteriores por convención.
La ventana de falda conecta I↔K y las ventanas de escape C↔E con sus propias áreas.
Las longitudes solo aportan volumen almacenado; diámetros aportan volumen y A_min.
No usar área de lumbrera para inventar un diámetro ni cambiar el JSON o sus sentidos.
Para el prototipo las listas deben ser completas, no vacías y continuas; un editor
puede seguir guardando geometrías que el futuro caso rechace con explicación.

**Sí:** almacenamiento de masa/energía y presión uniforme transitoria en I/E;
respuesta de llenado/vaciado ante cambios de volumen agregado, sección limitante
u otra presión exterior prescrita. **No:** inercia axial, fricción distribuida,
propagación/reflexión, tiempo de viaje acústico, pulsos de retorno de una cámara
sintonizada, resonancia ni RPM óptimas. No es “1D”. Cambios de orden, ubicación de
conos o perfiles con los mismos V/A_min son indistinguibles. Alargar un escape
solo cambia su capacidad 0D, no predice cuándo vuelve una onda ni cuál escape rinde
mejor. Aunque aparezcan oscilaciones temporales, no acreditan sintonía. La separación
entre almacenamiento, inercia y efectos de ondas se contrasta con [5] y [6].

Se recomienda esta reducción **solo para comprobar el primer núcleo acoplado**.
Si no se aprueba explícitamente diferir ondas, este diseño no habilita el prototipo;
no se renombra ni se implementa silenciosamente una alternativa.

Transferencias K↔C: suma de restricciones de las ventanas existentes, con Cd_T
agregado explícito; almacenamiento e inercia del trayecto se **desprecian**, no se
consideran conocidos. V_transferencia=0 es una aproximación del modelo, no una
medición ni un campo dimensional que completar con cero. No se precisa otra
longitud en esta reducción; falta Cd_T y la aceptación de despreciar el volumen
muerto y tránsito. Si eso no es admisible para un motor real, faltan volumen,
sección/longitud y pérdidas del trayecto y habrá que redefinir el modelo antes de
usarlo. No se abre ahora un editor ni se añade ese volumen al cárter.

## Carga fresca, residual, barrido y energía prescrita
Y es la fracción másica de carga fresca aún no procesada por el aporte energético;
1−Y es residual o carga ya procesada. Mismas propiedades para ambos marcadores.
Todo efluente tiene Y del volumen donante: mezcla homogénea perfecta, sin chorros,
capas, cortocircuito calibrado ni mapa de barrido. El escape puede llevar fresca
y el retorno puede contaminar el cárter. Medir flujos de ambos marcadores y Y_C al
cierre, sin llamarlos barrido real validado. Mezcla perfecta es un límite ideal,
distinto de desplazamiento y cortocircuito [5]; no se añade un factor de ajuste.

Aporte prescrito por masa fresca atrapada al inicio theta_s, con ventanas C cerradas
durante todo el aporte. Se captura F_s=F_C(theta_s), q_f=800000 J/kg de carga fresca
y Q_ciclo=q_f*F_s [J]. No hay combustible explícito, relación aire/combustible, PCI,
inyección ni evaporización: q_f es un parámetro sintético energético, no consumo.
Para theta_deg acumulado, inicio theta_s=350°+360k y duración Delta=40°:

```
z=(theta_deg−theta_s)/Delta
b(z)=0 si z<=0; z−sin(2*pi*z)/(2*pi) si 0<z<1; 1 si z>=1
db/dtheta_deg=(1−cos(2*pi*z))/Delta dentro del intervalo, 0 fuera
Qdot_C=Q_ciclo*(db/dtheta_deg)*6*n
Bdot_C=F_s*(db/dtheta_deg)*6*n
```

Así integral Qdot dt=Q_ciclo e integral Bdot dt=F_s; se convierte el marcador
sin salto instantáneo de masa/energía y sin volver a calentar residual como fresca.
F_s=0 ⇒ Q_ciclo=0, registrar ausencia de aporte, no inventar encendido. El caso no
podrá acreditarse como ciclo encendido si queda sin carga fresca/aporte. No es ley
de llama predictiva ni rendimiento de combustión medido. La forma sinusoidal se
elige por integral exacta y derivada continua, no por ajuste experimental.

Paredes adiabáticas en los cuatro CV: Q_pared=0 (sin temperatura de pared o h ocultos).
Sin radiación, blow-by, fricción mecánica, distribución ni calor químico adicional.
Las irreversibilidades de descarga/mezcla no se restan como pérdida de energía:
se conserva entalpía y no se contabilizan dos veces. No modela equilibrio térmico
de piezas ni pérdidas al eje. Todo ello debe aprobarse como alcance de viabilidad.

## Caso único de desarrollo: S2T-0D-01
**Todos los valores de entrada siguientes son supuestos sintéticos**, cero mediciones
y cero calibración experimental. No corresponden a fabricante/modelo real. Nombre
descriptivo de prueba; fabricante/modelo vacíos. No llenar proyectos de la usuaria.

| Entradas geométricas reutilizadas de JSON v5 | Valor |
| --- | --- |
| cycle / cylinder_count | 2T / 1 |
| bore_mm / stroke_mm / rod_length_mm | 54 / 56 / 100 mm |
| compression_ratio (geométrica) | 8:1 |
| crankcase_volume_bdc_cm3 | 250 cm³, libre en PMI, excluye conductos |
| Escape: una ventana, función escape, u/h/w | 32 / 10 / 20 mm |
| Transferencia: dos ventanas individuales, función transfer, u/h/w de cada una | 44 / 10 / 12 mm |
| intake.mode, u/h/w/f | piston_port; 64 / 10 / 20 / 42 mm |
| ducts.intake, un tubo L/D1/D2 | 100 / 20 / 20 mm |
| ducts.exhaust, tubo seguido de cono L/D1/D2 | 100 / 20 / 20; 100 / 20 / 40 mm |

Conservar referencias v3/v4/v5 existentes. Derivados exactos a partir de estas
entradas: V_d=40.824*pi cm³; V_clear=5.832*pi cm³; V_C,PMI=46.656*pi cm³;
V_K,PMS=250+40.824*pi cm³; V_I=10*pi cm³; V_E=(100/3)*pi cm³;
A_min,I=A_min,E=100*pi mm². La relación geométrica no es compresión efectiva
atrapada. Escape abre/cierra 90°/270°; admisión 270°/90°; transferencias derivadas
del cruce x=44 mm. Sin modificar los criterios geométricos ya aprobados.

| Entradas adicionales, fuera del JSON actual | Valor o convención fijada para aprobación |
| --- | --- |
| Régimen / velocidad angular | 3000 rpm constante; omega=100*pi rad/s; ciclo=0.020 s |
| Carga | Condición fija sin mariposa: dos reservorios a 100000 Pa absolutos y energía específica q_f prescrita; no % de carga ni par impuesto |
| Reservorio I: p / T / Y | 100000 Pa abs / 300 K / 1 |
| Reservorio E: p / T / Y | 100000 Pa abs / 500 K / 0; devuelve gas residual sintético si hay retorno |
| Cd admisión por falda / cada escape / cada transferencia | 0.70 / 0.70 / 0.65, ambos sentidos |
| Cd extremo exterior I / extremo exterior E | 0.80 / 0.80, ambos sentidos |
| Gas / calor / pérdidas / aporte | Valores y leyes definidos arriba, sin otros coeficientes |
| Arranque y referencia angular | t=0 en theta=180° (PMI); PMS=0°/360°, siguiente inicio de calor=350°; calor termina=390° |

| Estado inicial propio a theta=180° | p absoluta [Pa] | T [K] | Y fresca | V [cm³] |
| --- | --- | --- | --- | --- |
| I | 100000 | 300 | 1 | 10*pi |
| K | 120000 | 330 | 1 | 250 |
| C | 140000 | 700 | 0 | 46.656*pi |
| E | 100000 | 500 | 0 | (100/3)*pi |

En todos, m0=p0*V0/(R*T0), U0=m0*cv*T0, F0=Y0*m0; se derivan, no se ingresan
por separado. Los estados iniciales no son un ciclo estabilizado; C>K al inicio
fuerza un retorno de transferencia comprobable. No se garantiza convergencia.
El circuito, Cd, régimen, contornos, estados, q_f/ángulos y opciones físicas no
existen en JSON v5: quedan aquí, sin nuevo formato, fixture de proyecto ni controles.

## Prueba de viabilidad — protocolo previo ahora autorizado
Un prototipo pequeño de biblioteca estándar, sin Qt ni importar solver antiguo.
Propuesta numérica única: RK4 explícito en tiempo sobre m/U y F advectada, con
acumuladores de flujo/calor/trabajo y paso máximo expresado en grados. Durante
todo el aporte con C cerrado, F_C se evalúa analíticamente como F_s*(1−b)
en **todas las etapas**, incluidos extremos, en vez de integrar esa componente
por RK4; la conversión acumulada de cada paso es F_s*(b_fin−b_inicio). Al terminar
el aporte se retoma la ecuación de advección. No se espera a que una etapa prediga
F negativa ni se recorta/renormaliza el estado. Alinear pasos con puntos
muertos, aperturas/cierres calculados, inicio/fin de calor y límites de ciclo;
no obtener eventos desde muestras de dibujo. Cada etapa reutiliza geometría y
calcula cada enlace una vez. No hay malla espacial ni plataforma de solvers.

**Comprobaciones elementales independientes antes del ciclo completo** (otros
problemas matemáticos pequeños, no otros motores de desarrollo):

| Comprobación | Referencia y criterio previo |
| --- | --- |
| Geometría y signo de trabajo | V_C+V_K constante; V_I=10*pi y V_E=100*pi/3 cm³, A_min=100*pi mm². Error relativo <=1e−9, sin integración temporal |
| Flujo compresible | Para gamma=1.4, R=287, p_u=200000 Pa, T_u=300 K, A=1e−4 m², Cd=1 y p_d=100000 Pa: beta_crit≈0.5282817877 y q≈0.04667117 kg/s por fórmula analítica independiente; error relativo <=1e−5. A=0 o p iguales: flujo exactamente cero; invertir extremos con T/Y distintos invierte donante y signos; comprobar rama subcrítica beta=0.8, q≈0.03821455284 kg/s por sustitución manual (mismo error relativo), y continuidad a beta_crit ±1e−6 |
| Recipientes aislados conectados, V fijos, sin calor | Masa y energía conjunta conservadas; entalpía/fresca transferidas con igual magnitud y signo opuesto. Error de balance <=1e−7 relativo a inventario inicial; F también constante sin conversión |
| Compresión cerrada adiabática | p*V**gamma constante y W=(p1*V1−p2*V2)/(gamma−1); error relativo <=1e−4 en p y trabajo con escala mínima 1 J. Solo prueba interna; no sustituye motor abierto |
| Calor en masa/volumen fijo | U_fin−U_ini=q_f*F_s y F_fin=0 con la ley propuesta; error <=1e−5 relativo en energía y <=1e−7 de masa inicial en F; sin crear/destruir masa total |
| Mezcla homogénea aislada del motor | Recipiente isotermo de masa constante M, entrada fresca y salida mezclada iguales, F(0)=0: Y=1−exp(−q*t/M). Con q*t/M=1, Y=0.6321205588; error absoluto <=1e−4 |

Las referencias se evalúan por sustitución analítica separada, no llamando a la
función bajo prueba; no se ejecutaron hoy como pruebas de un solver. Solo se comprobó la aritmética de
las referencias del documento, sin importar MotorSim ni integrar estados. Los controles algebraicos son más
estrictos que integración/mezcla, sin exigir precisión de máquina al motor.

**Experimento integrado único:** mismo caso desde los mismos estados iniciales,
resoluciones máximas 0.5°, 0.25° y 0.125°, en ese orden. Tres ejecuciones como
comprobación mínima de resolución, no barrido de regímenes ni campaña de modelos.
Guardar últimas dos vueltas a nodos comunes de 0.5° y resúmenes por ciclo; los
extremos y flujos se monitorizan en cada paso, no solo en la salida muestreada.

En cada vuelta de 180° a 180°+360°, auditar por CV y globalmente:

- Residuo masa: Delta m−integral(in−out). Escala max(m_inicio, integral de flujos
  absolutos, 1e−9 kg); límite relativo 1e−6. Residuo fresca incluye integral Bdot,
  con misma escala y límite. Flujos internos cancelan al sumar CV.
- Residuo energía: Delta U−[H_in−H_out+Q−W_C−W_K], por CV su propio trabajo.
  Escala max(U_inicio, |H_in|+|H_out|+|Q|+|W_C|+|W_K|,1 J); límite 1e−5.
  Auditar también contra cuadratura independiente sobre salida refinada; no basta
  sumar el mismo RHS y declarar independencia. Para esa cuadratura permitir 0.1 %
  de la misma escala por muestreo; no sustituye conservación discreta.
- Toda masa, V, U, p y T positiva/finita; 0<=F<=m sin recortar ni renormalizar
  silenciosamente. Aplicar la solución analítica de F_C durante **todo** el
  intervalo de calor cerrado, según el método anterior, y contabilizar su conversión
  por diferencia analítica. Fuera de ese intervalo, una etapa F no física exige
  rechazo controlado. Con A=0 el flujo debe ser cero; a theta=180° inicial el
  signo de transferencia es C→K y el efluente tiene Y_C=0 y h_C.
- Registrar p_C(theta), pares (V_C,p_C), W_C/W_K, m/U/T/Y/V de cada CV, signos y
  magnitudes de flujos, Q_ciclo, F_s, balances, máximos, resolución y motivo de parada.
  Sin curvas ficticias ni expectativas de un pico/trabajo positivo inventados.

Convergencia propuesta: por tres vueltas consecutivas desde la vuelta 5, diferencias
entre estados al mismo theta=180° de m,U <=0.2 % (denominadores max(|actual|,|previo|,
1e−9 kg o 1 J)), de Y <=0.002 absoluto en todos los CV y de W_C <=0.5 % con escala
max(|W_C actual|,|previo|,1 J). Además cambio máximo de p_C en nodos comunes <=0.5 %
con escala max(p_max actual,p_max previo,100000 Pa), y balances dentro de límites.
F_s y Q_ciclo del ciclo convergido deben ser >0 para acreditar el caso encendido.
No basta converger masa dejando presión o energía derivando.

Sensibilidad: entre las dos resoluciones más finas convergidas, W_C y masas netas
por enlace cambian <=1 % (escalas mínimas 1 J y 1e−7 kg); p_C máximo y norma máxima
de diferencia de curva <=1 % de p_max fino. Diferencia de estado final Y <=0.005.
La discrepancia fina no debe superar la gruesa en magnitudes fuera del piso numérico;
si no cumplen, viabilidad no acreditada y revisión puntual del motivo, sin relajar
estos umbrales tras observar el fallo. Son criterios de estabilidad numérica útil
para comparar iteraciones de desarrollo, no error físico frente a mediciones.

Límites propuestos antes de ejecutar: 30 vueltas por resolución; 60 s de pared por
resolución y 180 s para las tres; proceso completo <=512 MiB de memoria residente.
Medir tiempo monotónico, máximo de memoria del proceso (incluye runtime), CPU,
Windows y versiones en el equipo real; nada medido todavía. Meta de hoja: hasta
un minuto por punto típico y diez minutos por diez puntos; no demostrada, y no se
ensayan esos diez puntos. Si no converge en el presupuesto, terminar como
**no convergido / presupuesto excedido**, no prolongar corridas ni esconder coste.

Rechazo de etapa no física: dividir paso por dos, hasta 8 rechazos seguidos y paso
mínimo 0.001°; cualquiera de esos límites aborta con CV, ángulo y causa. Topes de
2 millones de evaluaciones del RHS por resolución, T fuera de [100,4000] K o
p fuera de [1000,2e7] Pa abortan como fuera del dominio de esta prueba (no límites
universales del gas). No reparar datos ni limitar temperaturas para seguir.
Comprobar cancelación y presupuesto al menos cada 0.5 s; emitir avance por vuelta
y como máximo cada 1 s entre avances; cancelación sale en <=1 s. No reintentos
indefinidos. Un benchmark aislado del orificio no acredita coste del ciclo acoplado.

## Aprobaciones previas — obtenidas por orden explícita del 15/09/2026
1. Reducir explícitamente el primer caso a depósitos 0D sin ondas/inercia ni sintonía,
   incluida pérdida concentrada A_min/Cd y transferencia sin almacenamiento.
2. Aceptar gas caloríficamente perfecto, mezcla perfecta, paredes adiabáticas y
   conversión/energía prescritas en lugar de combustión predictiva; caso y parámetros
   sintéticos de esta definición sin calibración experimental.
3. Aprobar el experimento y límites/tolerancias previos, y autorizar expresamente
   la implementación y ejecución del prototipo. La integración a interfaz y cambios
   de archivo siguen sin autorizarse por esta definición.

## Diagnóstico localizado posterior — decisión numérica pendiente

La orden posterior autoriza diagnóstico y corrección de defectos demostrados,
sin cambiar el método para forzar aceptación. La vuelta reconstruida reproduce
exactamente la evidencia de 54821600: RK4 de paso fijo atraviesa el equilibrio
de presión dentro de sus etapas en los enlaces exteriores I/E. Con E cerrado
al cilindro, sin calor/trabajo y p_E>p_res, el modelo continuo conserva Y_E durante
la descarga; la trayectoria numérica cambia Y_E por retornos entre etapas.
No se encontró un defecto de signos, donante, unidades o cuadratura. Evidencia,
intervalos y controles en tasks.md; las tolerancias anteriores permanecen intactas.

De la ley ya aprobada, cerca de equilibrio q es proporcional a
sign(Delta p)*sqrt(abs(Delta p)); su pendiente no está acotada al acercarse a cero.
Esto explica por qué un paso fijo que conserva inventarios algebraicamente puede
introducir retornos numéricos. Las etapas intermedias RK4 no son una salida densa
independiente: dos de ellas comparten tiempo pero tienen estados distintos.
Reutilizar sus pesos en la auditoría ocultaría la discrepancia sin corregir Y.

**Única modificación propuesta, no implementada:** conservar RK4 y añadir control
local mediante comparación de un paso y dos medios pasos; aceptar la trayectoria
de los medios pasos solo cuando el indicador de error lo permita, o reducir el
paso. Incluir m/U/F y transportes, mantener F_C analítica, alineación con eventos,
auditoría independiente sobre pasos aceptados y todos los topes actuales.
La diferencia sería un indicador, sin extrapolación que presuponga suavidad en
la inversión de flujo. Las tolerancias de ese control local requieren fijación
y aprobación antes de ejecutarlo; no reemplazan ni relajan las de aceptación.

Coste directo sin reutilización: 12 evaluaciones RHS por intento frente a 4,
más intentos/pasos si se necesita reducirlo. No se ha medido ese coste ni probado
que alcance precisión o presupuesto; si alcanza el mínimo de 0,001° o cualquier
tope debe detenerse con diagnóstico. No se propone anular caudales, recortar
estados o alterar Cd/energía/contornos. No se ejecutó otra serie oficial.

## Fuentes primarias consultadas — 15/09/2026
[1] [MIT, Control volume form of the conservation laws](https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node19.html):
balances abiertos y transporte de entalpía; justifica signos, no coeficientes del caso.
[2] [MIT, Specific Heats](https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node18.html):
cierre u(T)/h(T) y adiabática ideal; propiedades constantes son aproximación propuesta.
[3] [NASA Glenn, Mass Flow Choking](https://www.grc.nasa.gov/www/k-12/BGP/mflchk.html):
flujo isentrópico compresible y límite sónico; ramas en razón de presiones obtenidas
por sustitución de relaciones isentrópicas. No proporciona nuestros Cd.
[4] [Krieger, Booy, Myers y Uyehara, SAE 690135](https://doi.org/10.4271/690135):
se consultó únicamente el resumen público del editor, no el texto de pago. Precedente
de sistemas termodinámicos acoplados, flujo por restricciones y repetición de ciclos;
no se copian láminas, ajuste experimental, dos zonas ni contratos de su implementación.
[5] [MIT 2.61, Lecture 8: Intake and exhaust processes](https://ocw.mit.edu/courses/2-61-internal-combustion-engines-spring-2017/6ec38b3fc5493e328115e0a49a565f35_MIT2_61S17_lec8.pdf),
páginas 5–6 y 9 del PDF: distingue inercia/sintonía, retorno/estrangulamiento y
límites de barrido ideal. No se adoptan los ejemplos ni factores de sus figuras.
[6] [Vannik, EngMod2T — Outputs Degree Based](https://vannik.co.za/EngMod2T%20-%20OutputsDegree.htm):
la documentación del fabricante identifica ondas viajeras/reflejadas y pulsos de
retorno; referencia de capacidad que nuestra reducción no representa, no aval del modelo.
Las leyes de calor, topología reducida, parámetros sintéticos y tolerancias son
**decisiones propuestas aquí**, no resultados publicados ni recomendaciones de esas fuentes.
