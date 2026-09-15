# MotorSim

Editor de proyectos y ficha del motor en Python + PySide6/Qt Widgets. La última entrega implementada
[conductos-admision-escape](openspec/changes/conductos-admision-escape/specs/conductos-admision-escape/spec.md)
añade recorridos geométricos de conductos circulares de admisión y escape 2T.
La ficha, posición del pistón, volúmenes y curvas geométricas existentes se conservan.
El editor no ejecuta simulación ni estimaciones de rendimiento. El prototipo
experimental de consola descrito abajo está separado de la aplicación gráfica.

Estado de las entregas 1 y 2: **Completadas**. La usuaria comunicó el 14/09/2026
que realizó las comprobaciones manuales pendientes, incluido el uso sin Internet,
y aceptó ambas entregas. No quedan otros criterios obligatorios pendientes según
las tareas existentes. La [hoja de ruta](docs/HOJA_DE_RUTA_MotorSim.md#estado-de-avance)
resume el estado. Esta aceptación es evidencia de la usuaria, separada de las
pruebas automatizadas e inspección visual del agente. Sin archivar. La entrega 3
está **Completada** para la configuración geométrica admitida: lumbreras, cárter
y admisión por falda comprobados. Esto no es aceptación manual de la usuaria
ni validación predictiva. La entrega 4 está **Completada** para el editor geométrico autorizado el 15/09/2026.
La entrega 5 está **En curso: prototipo ejecutado, viabilidad no acreditada**.
La usuaria aprobó el modelo 0D, caso y protocolo de
[simulacion-2t](openspec/changes/simulacion-2t/design.md) para esta prueba de consola.
No hay integración Qt ni cambios en JSON v5. Sin ondas, inercia de conductos,
sintonía, combustión predictiva ni validación experimental.

## Prototipo de viabilidad 2T — entrega 5 abierta

Biblioteca estándar, cuatro volúmenes abiertos (I/K/C/E), flujo reversible,
trabajos de cilindro y cárter separados y energía prescrita por carga fresca.
`motorsim/simulation_case.py` contiene S2T-0D-01 y todos sus parámetros sintéticos;
no se cargan en proyectos de la usuaria. Reutiliza la geometría y áreas del editor.

Desde la raíz del repositorio, comando comprobado:

```powershell
.\.venv\Scripts\python.exe -m motorsim.prototype --output results/simulacion-2t/viabilidad-20260915
```

Ese directorio ya contiene la ejecución del 15/09/2026 y no se sobrescribe. Para
repetirla, omitir `--output`: se crea un directorio nuevo con fecha/hora. No hay
dependencias adicionales, Qt ni cambios globales. Ctrl+C solicita cancelación.
Cada resolución arranca de los mismos estados a 3000 rpm; máximo 30 ciclos/60 s,
serie 180 s, proceso 512 MiB. El programa sale con resultado no satisfactorio
cuando no se acredita viabilidad; no reintenta ni prolonga presupuestos.

**Resultado de la única serie ejecutada:** 30 ciclos en cada resolución, sin
convergencia según el criterio completo. Los estados se estabilizan, pero la
auditoría independiente por trapecios en cada paso aceptado incumple el 0,1 %.
La sensibilidad queda sin acreditar porque exige las tres corridas convergidas.
No se ajustaron método, parámetros ni tolerancias después de observar el fallo.

| Paso máximo | Tiempo de cálculo | Pico residente del proceso | W cilindro, último ciclo | p máxima | Máximo residuo independiente normalizado |
| --- | --- | --- | --- | --- | --- |
| 0,5° | 5,094 s | 24,70 MiB | 16,63469 J | 1,335403 MPa | 11,3369 % |
| 0,25° | 10,016 s | 28,53 MiB | 16,54472 J | 1,332999 MPa | 5,8870 % |
| 0,125° | 19,125 s | 33,43 MiB | 16,48338 J | 1,331369 MPa | 3,0091 % |

Valores diagnósticos **no aceptados como resultado convergido**. No son potencia
al eje ni predicción experimental. Serie: 34,719 s incluyendo escritura entre
resoluciones; Intel Core i5-10400 2,90 GHz, 12 procesadores lógicos, Windows
10.0.19045 AMD64, Python 3.11.0. Memoria = pico residente medido por Windows del
proceso completo, incluido runtime y resultados anteriores de esa misma serie.

Salidas locales en `results/simulacion-2t/viabilidad-20260915/`: `case.json`,
`environment.json`, `summary.json`, resúmenes por resolución/ciclo y CSV con las
últimas dos vueltas (1442 filas por resolución, nodos comunes de 0,5°). Incluyen
p/ángulo, P-V, m/U/F/T/Y/V de los cuatro volúmenes, flujos firmados, trabajo,
calor, conversión y balances. Son resultados separados del formato de proyectos
y están excluidos de Git; el caso, código, pruebas y esta evidencia sí se registran.

**Pruebas automatizadas:** los seis controles elementales aprobaron antes del
motor integrado. Quince controles nuevos cubren también retorno, cancelación
real programada (<1 s), límites, auditoría con defecto inducido y salida sin Qt.
Suite final: **100/100 aprobadas en 8,547 s**, incluidos widgets `offscreen` y
regresiones de persistencia. Una suite aprobada no acredita la viabilidad física.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_simulation_*.py' -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Revisión puntual independiente de solo lectura: corregida la tendencia exigida
por debajo de los pisos numéricos documentados, antes de la serie. Autorrevisión
del principal de la corrección y evidencia. No se repitió inspección visual de
Windows ni se atribuye aceptación manual. El primer impedimento es el balance
independiente, ya fallido desde la primera vuelta. Una decisión posterior sobre
ese impedimento y la futura integración quedan fuera de esta ejecución acotada.

## Interfaz y uso

Título nativo de Windows, menú Archivo, barra compacta con Nuevo, Abrir, Guardar
y Guardar como, y un único encabezado «Motor». Datos generales y Geometría se
organizan en dos columnas o se apilan al reducir el ancho; el desplazamiento
vertical permite acceder al formulario completo. Fondo oscuro liso, acentos
azules, Segoe UI, foco visible y navegación por Tab. El selector compacto 2T/4T
conserva los datos comunes. Una sola barra inferior muestra ruta, estado de
guardado y «Simulación no disponible». La ruta completa está en su ayuda emergente.

Nombre obligatorio al guardar; fabricante, modelo y observaciones opcionales.
Cilindros, diámetro, carrera, biela entre centros y compresión pueden quedar
vacíos. Vacío significa sin informar; un valor inválido se señala y bloquea el
guardado, conservando la edición. Se acepta coma o punto decimal, sin agrupación
de miles (un único separador se interpreta siempre como decimal). También se
admite notación científica en dimensiones y compresión. Cilindros requiere un
entero positivo; dimensiones, números positivos finitos; compresión, finita > 1.
Las unidades se muestran junto a los controles; la compresión se expresa como x:1.

Cilindrada por cilindro = π × diámetro² × carrera / 4000, con mm de entrada y cm³
de salida. La total multiplica por el número de cilindros, suponiendo geometría común
a todos ellos (no es simulación multicilíndrica). Los resultados son
solo lectura, con dos decimales; faltantes o errores en sus entradas muestran
«—», sin conservar resultados anteriores. Biela y compresión se utilizan en la pestaña Geometría, sin simulación física.

Guardar pide destino inicialmente. Guardar como confirma sobrescritura. Nuevo,
Abrir y Salir mantienen Guardar/Descartar/Cancelar. Abrir valida antes de
reemplazar la edición; errores y cancelaciones conservan el trabajo. El guardado
mantiene archivo temporal, sincronización y reemplazo seguro en el mismo directorio.

![MotorSim en Windows: datos exclusivamente de prueba](docs/images/motorsim-motor.png)

Captura real de Windows, con título nativo, de 1080 × 791 píxeles. Los datos
están identificados como prueba y no se precargan en proyectos nuevos. Se
inspeccionó además la ficha apilada al 150 % con ventana de 700 × 480 unidades
lógicas: desplazamiento vertical, campos, foco y barra inferior utilizables,
sin desplazamiento horizontal. El escalado se aplicó solo al proceso Qt.

## Pestaña Geometría — entrega 2

Editar dimensiones en **Ficha** y abrir **Geometría**, junto a ella. Sin campos
duplicados: posición desde PMS en mm, cámara y volumen instantáneo en cm³, para
un cilindro de geometría común. No se multiplican por el número de cilindros.
El esquema 2D y las dos curvas usan el mismo cálculo; el selector de ángulo se
maneja por teclado y no modifica el archivo ni el estado de cambios pendientes.

PMS de referencia = 0°, ángulo horario en el esquema; PMI a 180°. 2T muestra
0–360° y 4T 0–720° con segunda revolución diferenciada. El mecanismo se repite
cada 360°; no se asignan eventos de combustión o distribución. El esquema no es
CAD ni comprueba holguras, interferencias o resistencia.

El mecanismo admite biela > carrera/2. Ausencia o incompatibilidad retira los
resultados afectados y muestra la causa, sin corregir dimensiones. Posición y
esquema solo necesitan carrera/biela; cilindrada, diámetro/carrera; cámara y
extremos, además compresión; curva de volumen, todas estas entradas. La ficha
incompleta o con biela positiva incompatible se puede guardar para corregirla.
No se guardan curvas; el formato actual es JSON versión 5. Ecuaciones y caso admitido en el
[diseño](openspec/changes/geometria-cinematica/design.md).

Comprobación del 14/09/2026 sobre `7ef0628`: escritorio Windows desbloqueado,
recorrido automatizado visible de ficha y geometría, e inspección de capturas
reales. Se verificaron 360°/720°, actualización, retirada selectiva con datos
ausentes e incompatibles, navegación entre pestañas, foco y ventana al 150 %.

![Geometría: captura real de Windows](docs/images/motorsim-geometria.png)

[Ficha actual: captura real](docs/images/motorsim-ficha-verificacion.png).
La imagen anterior de la ficha se conserva como evidencia de su entrega original.
Las capturas nuevas tienen datos de prueba identificados y no son renders aislados.

Las 47 pruebas automáticas y las 27 de widgets Windows volvieron a aprobar.
Un recorrido adicional con diálogos reales comprobó guardado/cierre/reapertura,
sobrescritura, archivos inválidos, versión 1, cambios pendientes y el fallo real
sobre archivo temporal con atributo Solo lectura, en 2T y 4T. No se encontraron
defectos que requirieran modificar la implementación. Evidencia detallada en los
tasks existentes; esta ejecución es actual, no una verificación histórica.

**Aceptación manual de la usuaria:** recorrido existente completado, incluido
el paso 9 sin Internet, según su declaración explícita. No se repitieron pruebas
ni se generó otra revisión para registrar esta aceptación documental.

## Configuración 2T — primer tramo de la entrega 3

Abrir la pestaña **Configuración 2T**, añadir una lumbrera y editar la fila
seleccionada. Cada fila corresponde a una ventana individual del cilindro de
referencia; no se multiplica por N. Se puede eliminar la seleccionada. La lista
conserva borradores incompletos y textos inválidos al cambiar de fila.

Campos: nombre, función Escape/Transferencia (sin elección inicial), distancia
al borde superior, altura y ancho desarrollado, en mm. La distancia se mide hacia
abajo desde el borde superior periférico del pistón en PMS, no desde la cara del
cilindro ni una cúpula. El ancho es desarrollado sobre la pared, no cuerda. La
ventana rectangular es una aproximación, sin puentes, perfiles ni válvula de escape.

Se muestran apertura/cierre/duración y máximo efectivo, con curva 0–360° de área
geométrica descubierta. Los eventos usan cruce acotado del mecanismo existente,
no redondeo a la muestra dibujada. Una ventana puede abrir parcialmente en PMI.
Si no se descubre, se indica «No se abre», duración/área cero y ángulos ausentes.
No es área efectiva de flujo, caudal, barrido o potencia. Eventos necesitan carrera,
biela y borde superior; área, además altura/ancho. Compresión y cárter no se exigen.
Datos insuficientes o incompatibles retiran solo los resultados afectados con causa;
el límite numérico de área se informa sin modificar las dimensiones guardadas.

El volumen libre del cárter con pistón en PMI es opcional, cm³ positivos finitos,
individual y sin conductos externos. Registrar procedencia en las Observaciones
existentes. No se deduce ni genera presión/compresión. La admisión, inicialmente
pendiente, se incorpora en el tramo siguiente del mismo cambio.

Los campos nuevos pueden guardarse sin informar (números null, texto vacío,
función null); los números informados deben ser positivos finitos. Coma o punto
admitidos, sin separadores de miles. Un texto inválido bloquea guardar y permanece
intacto. Añadir/editar/eliminar marca cambios. En 4T se ocultan editor y resultados
2T, conservando los datos al volver y al guardar/reabrir.

![Configuración 2T en Windows: caso sintético](docs/images/motorsim-configuracion-2t.png)

Captura real del escritorio Windows, con caso sintético identificado. Inspeccionada
también la vista apilada al 150 %, sin desplazamiento horizontal, con curva, unidades
y referencias legibles. Automatización e inspección visual no son aceptación manual
de este tramo ni modifican la aceptación de las entregas 1 y 2.

Comprobaciones del tramo: suite de **58 pruebas aprobadas**; después de corregir
un subdesbordamiento numérico detectado en revisión independiente, **9 pruebas
focalizadas de lumbreras aprobadas** (incluida la nueva regresión) y **30 pruebas
de widgets Windows aprobadas**. La colección al finalizar ese tramo contenía 59 tests. Se conserva
la evidencia histórica anterior en sus tareas; no se vuelve a atribuir al agente
el recorrido manual de la usuaria. Comandos focalizados ejecutados:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ports.py -q
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_window.py -v
$env:QT_QPA_PLATFORM = $null
```

Caso independiente de la usuaria: S=56, L=100, u=32, h=10, w=20 mm produce 90°,
270°, 180° y 200 mm². También se comprobaron ventanas parciales/cerradas, datos
incompletos/inválidos, límites numéricos, actualización al editar, varias filas,
eliminación, v1/v2/v3, alternancia 2T/4T y regresiones de guardado/cancelación.

## Admisión por falda — ampliación de la entrega 3

En **Configuración 2T**, desplazarse hasta **Admisión** y elegir **Falda del pistón**.
Por defecto permanece **Sin definir**, también en los proyectos antiguos. Los campos
u (borde superior), h (altura), w (ancho desarrollado) y f (borde inferior de falda)
se expresan en mm, sin valores precargados. Las referencias completas están en
**Referencias de medida** y en la ayuda de los campos. f mide desde el borde superior
periférico del pistón hasta el borde inferior de falda en el lado de admisión.
No es biela, cúpula ni distancia al bulón. w es desarrollado, no cuerda.

Ventana rectangular y borde de falda recto. Se reutiliza la posición x de Geometría:
A(θ)=w×max(0,min(h,u+h−f−x(θ))). El dominio exige biela > carrera/2 y u ≥ carrera.
Con d=u+h−f: d≤0 no abre; d≥carrera queda fuera del modelo por ausencia de cierre
finito alrededor de PMI. Los valores positivos incompatibles se pueden guardar.
Para 0<d<carrera, el cruce x(β)=d determina apertura=360−β, cierre=β y duración=2β.
El intervalo atraviesa PMS: [apertura,360] ∪ [0,cierre]. El máximo es w×max(0,min(h,d)),
que puede ser menor que w×h. No se multiplica por N.

Los eventos necesitan carrera, biela, u, h y f; el área necesita además w. Ni
compresión, diámetro ni cárter bloquean estos resultados. Faltantes, errores de
entrada o rango retiran los resultados afectados con causa. Cambiar modalidad o
2T/4T conserva dimensiones y textos inválidos; estos bloquean el guardado. En 4T
no se calculan ni muestran resultados específicos 2T.

Caso sintético independiente de la usuaria: S=56, L=100, u=64, h=10, w=20, f=42 mm.
Apertura 270°, cierre 90°, duración 180°, máximo 200 mm²; área 200 en 0°/360° y cero
en 90°/180°/270°. Es una prueba geométrica, no un motor experimental seleccionado
ni evidencia predictiva. No se calculan caudal, presión, carburación ni rendimiento.

**Pruebas automatizadas finales:** 72/72 aprobadas en 11,647 s, ejecutadas una vez
con Qt Windows después de la última corrección. Incluyen 34 pruebas de widgets
con ventanas/diálogos reales automatizados y las regresiones de archivos, ficha,
cinemática y lumbreras. Durante implementación pasaron también 9 pruebas numéricas
de admisión y 34 de widgets sin pantalla; esas ejecuciones no sustituyen la suite final.

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
$env:QT_QPA_PLATFORM = $null
```

**Revisión puntual independiente:** sin defectos reproducibles de código; aclarada
la compatibilidad documental v3 (conserva lumbreras/cárter, no los vacía). Autorrevisión
del principal de la integración, corrección de señales, documentación y capturas.
Validación estricta OpenSpec aprobada; integración global intacta.

**Inspección visual:** captura real del escritorio Windows desbloqueado, ventana
1080×791, caso sintético identificado en la ruta del archivo. Curva con dos segmentos
junto a PMS y área cero alrededor de PMI. También inspeccionados formulario y curva
apilados al 150 % en 700×480 unidades lógicas, navegación por Tab, foco, referencias
desplegables y ausencia de desplazamiento horizontal. Escalado solo del proceso Qt.

![Admisión por falda: captura real Windows, caso sintético S56/L100](docs/images/motorsim-admision-2t.png)

**Aceptación manual:** no realizada por la usuaria para entrega 3. Automatización
visible e inspección del agente se registran separadas de la aceptación previa de
entregas 1 y 2. No quedan comprobaciones técnicas obligatorias pendientes de este
tramo; no se atribuye validez experimental ni se selecciona un motor real.

## Conductos de admisión y escape — entrega 4

Pestaña **Conductos**: elegir **Admisión** o **Escape**. Se muestra un único editor
con la lista ordenada del recorrido elegido. **Añadir tramo**, **Eliminar**, **Subir**
y **Bajar** modifican el proyecto; seleccionar fila o cambiar recorrido no lo modifica.
Cada tramo tiene nombre opcional, longitud axial L y diámetros interiores D1/D2, en mm.
Tubo cilíndrico si D1=D2; en otro caso troncocónico de diámetro lineal. Sin geometrías
precargadas, ramificaciones, accesorios, curvas espaciales ni espesores.

El sentido de admisión es entrada exterior → ventana al cárter; escape, salida del
cilindro → extremo exterior. Define orden y dibujo, no condiciones de flujo. Un
recorrido por sistema del cilindro de referencia, sin multiplicación por N. No se
deduce diámetro desde lumbreras ni se suma volumen de conductos al cárter registrado.

Campos vacíos se guardan como null; texto inválido conserva el borrador y bloquea
Guardar, incluso al cambiar fila, recorrido o 2T/4T. Se aceptan números positivos
finitos, coma/punto sin separadores de miles y notación científica como en la ficha.
En 4T se ocultan editor y resultados 2T, conservando todos los datos.

Por pieza: A1=πD1²/4 y A2=πD2²/4 mm²; V=πL(D1²+D1D2+D2²)/12000 cm³.
Los totales requieren las entradas de **todos** los tramos para cada magnitud:
la longitud no depende de diámetros; el volumen no se presenta como suma parcial.
Ausencias e invalidez muestran «—» con causa; lista vacía indica **Sin tramos**.
Se muestran resultados redondeados, manteniendo las entradas originales en JSON.

Uniones continuas requieren igualdad numérica exacta D2 anterior=D1 siguiente,
sin ajustes automáticos ni tolerancia oculta. Las uniones discontinuas se identifican
por números de tramo y marcador en el perfil; quedan fuera del modelo continuo,
pero conservan áreas y suma de volúmenes calculables de las piezas. No se dibujan
adaptadores. Diámetros faltantes dejan la unión sin verificar.

El perfil usa posición axial acumulada y contornos interiores ±D/2, con selección
en azul, uniones marcadas, sentido y unidades. Misma escala en ambos ejes; no CAD
de fabricación. Se retira entero si falta una dimensión necesaria o hay texto
inválido, explicando la causa; no se dibujan medidas supuestas. El rango de dibujo
se comprueba independientemente de los cálculos numéricos. No calcula caudal,
presión, velocidad del gas, temperatura, resonancia, RPM óptimas, potencia ni par.

Caso sintético independiente: tubo L100/D1=20/D2=20 seguido de cono L100/D1=20/D2=40
mm. Volúmenes 10π y (70/3)π cm³; unión20 mm, longitud200 mm y volumen total(100/3)π
≈104,71975512 cm³. No corresponde a un motor real ni acredita validez predictiva.

**Suite final del 15/09/2026:** 85/85 pruebas aprobadas en 22,311 s, ejecutadas una
vez después de la última corrección con Qt Windows. Incluye 39 pruebas de widgets,
archivos y diálogos reales automatizados; 8 pruebas específicas de geometría y
persistencia de conductos, además de regresiones anteriores. Durante implementación
pasaron 8 pruebas numéricas y 39 sin pantalla; no sustituyen la suite final.

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
$env:QT_QPA_PLATFORM = $null
```

**Revisión independiente puntual:** sin defectos reproducibles. Autorrevisión del
principal de integración y capturas; se ajustó el orden de dibujo para mantener
visible el eje central sobre el relleno, antes de la suite final. OpenSpec estricto
aprobado. No se añadieron dependencias ni se modificó configuración global.

**Inspección visual:** ventana real en escritorio Windows disponible, captura
1350×988 píxeles con escalado efectivo 125 %. Se comprobaron perfil continuo,
discontinuidad sin adaptador, selección y retirada del perfil ante texto inválido.
También se inspeccionaron editor/perfil apilados al 150 %, ventana de 700×480 unidades
lógicas, foco por Tab y ausencia de desplazamiento horizontal. El ajuste de escala
se limitó al proceso Qt. Los archivos JSON del recorrido fueron temporales, fuera
de .venv; no se cambian destinos de proyectos de la usuaria.

![Conductos en Windows: caso sintético independiente](docs/images/motorsim-conductos.png)

**Aceptación manual:** no realizada por la usuaria para esta entrega. Las pruebas
visibles automatizadas y la inspección del agente son evidencias separadas. No quedan
comprobaciones técnicas obligatorias pendientes; sin validez predictiva ni entrega 5.

## Instalar, iniciar y probar

Versiones comprobadas: Windows 10 (10.0.19045), Python 3.11.0, PySide6 6.11.2,
Qt 6.11.2, Node.js 24.19.0 y OpenSpec 1.3.1. Se conserva el entorno virtual del
proyecto; esta entrega no añade dependencias. Instalación en una copia limpia:

```powershell
Set-Location E:\dino\Dino
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicio desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m motorsim
```

Pruebas y dependencias:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Evidencia de las entregas anteriores: **47 pruebas aprobadas** y `pip check` sin dependencias rotas. Cubren JSON v2
completo/incompleto, lectura v1 sin escritura automática, valores vacíos/inválidos,
coma/punto, finitud, cilindrada y actualización, conservación al cambiar ciclo,
cambios pendientes de todos los campos, teclado, adaptación de ancho y regresiones
de errores de archivo, guardado seguro, sobrescritura y cancelaciones.

También se ejecutaron **27 pruebas de widgets con plataforma Qt Windows**, todas
aprobadas, incluidos diálogos Qt reales (automatización visible en la comprobación
actual; no aceptación manual). Para repetirlas:

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_window.py -v
$env:QT_QPA_PLATFORM = $null
```

Las pruebas por defecto usan `offscreen`. La automatización visible y la inspección
de capturas Windows son evidencia distinta; no equivalen al recorrido
manual realizado y confirmado posteriormente por la usuaria; ambas evidencias
se mantienen separadas.

En entrega 1 se realizó una revisión independiente de solo lectura conforme a AGENTS.md.
Detectó pérdida de precisión al reabrir un entero dimensional grande; se corrigió
el parseo para conservar enteros y se agregó una prueba de regresión. El principal
comprobó esa corrección, la documentación y las capturas (autorrevisión).
En esta retoma se reutilizó la ficha, se declaró la geometría común y se verificó
además cierre/reapertura en otra ventana y lectura v1 desde el editor. La revisión
puntual de estos ajustes fue autorrevisión; no se abrió otra campaña independiente.

La entrega 2 añade pruebas de puntos muertos, periodicidad, extremos, independencia
de N, datos ausentes/incompatibles y retirada de curvas. Contraste independiente:
r=3 mm, L=5 mm, θ=90° forman triángulo 3-4-5; posición=4 mm. Con D=20 mm y C=3,
Vc=0,3π cm³ y V(90°)=0,7π cm³, sin usar la función probada para el valor esperado.
Revisión independiente puntual: detectó dependencia indebida de cilindrada respecto
a compresión; corregida y cubierta por regresión. Autorrevisión del principal de
la corrección y documentación. La integración OpenSpec global no se modifica.

## Formato JSON versión 5

Conserva todos los campos de ficha de versión 2 (`name`, `cycle`, `manufacturer`,
`model`, `notes`, `cylinder_count`, `bore_mm`, `stroke_mm`, `rod_length_mm`,
`compression_ratio`) y añade `ports`, `crankcase_volume_bdc_cm3` y
`two_stroke_reference`. La versión 4 añade `intake`; `format_version` actual es el entero 5. Cada fila de `ports`
guarda `name`, `function` (`escape`, `transfer` o null), `top_mm`, `height_mm`,
`width_mm`. La lista vacía representa ausencia de lumbreras. Dimensiones/cárter
no informados son null; los textos opcionales, cadenas vacías. No se redondean
entradas para guardarlas ni se incluyen unidades en los valores numéricos.

Referencia fija: `rectangular-peripheral-tdc-developed-bdc-v1`, con las convenciones
explicadas en el [diseño](openspec/changes/configuracion-2t/design.md).
Una referencia diferente se rechaza para no reinterpretar medidas. No se guardan
curvas ni resultados. Se mantienen guardado seguro y confirmación de sobrescritura.

Se leen versiones 1 y 2 conservando sus campos; se inicializan lumbreras vacías
y volumen de cárter null. Se lee también v3 conservando lumbreras y cárter. En
v1/v2/v3, `intake` se inicializa sin definir y con todas las dimensiones null.
Abrir no reescribe: la conversión a v5 solo se persiste con Guardar/Guardar como.

`intake` contiene `mode` (null o `piston_port`), `top_mm`, `height_mm`, `width_mm`,
`skirt_mm` (números positivos finitos o null) y `reference`, obligatoria con valor
`straight-skirt-peripheral-tdc-developed-v1`. No modifica la referencia v3 de
lumbreras/cárter ni guarda resultados. Admite dimensiones con modalidad sin definir;
una modalidad no admitida o referencia diferente se rechaza, sin perder la edición.

v5 añade `ducts`, con `intake` y `exhaust` (listas ordenadas inicialmente vacías) y
`reference`: `ordered-circular-inner-axial-linear-2t-v1`. Cada fila guarda `name`,
`length_mm`, `start_diameter_mm` y `end_diameter_mm`, todas claves obligatorias;
los números ausentes son null. La referencia fija documenta diámetros interiores,
longitud axial, sección circular, variación lineal y los sentidos indicados arriba.
Se rechaza otra referencia para no reinterpretar dimensiones. No se guardan tipo,
áreas, volúmenes ni perfil. Se leen v1–v4 con ambos recorridos vacíos, conservando
cada dato anterior; abrir no escribe hasta Guardar/Guardar como explícito.

## OpenSpec y estado

Cambio activo: [simulacion-2t](openspec/changes/simulacion-2t/),
con [registro de tareas](openspec/changes/simulacion-2t/tasks.md). Las evidencias
de implementación anteriores se conservan en sus respectivos cambios.
Entregas 1 y 2 publicadas en `040e789` y `7ef0628`, respectivamente: pertenencia
a origin/main comprobada tras fetch. No se recrearon esos commits ni se acepta
retrospectivamente el recorrido manual.
AGENTS.md vincula la restricción de nombre/tipo sin geometría a base-escritorio.
No se alteran sus criterios. El recorrido manual se acredita mediante la
declaración posterior de la usuaria, sin atribuirlo a verificaciones históricas.

La integración automática OpenSpec–Codex sigue omitida por decisión explícita
para preservar prompts y configuración global. No se ejecutó init/update ni se
reinstalaron herramientas. Comandos documentales ejecutados:

```powershell
openspec instructions apply --change simulacion-2t --json
openspec validate simulacion-2t --strict --no-interactive
```

Validación estricta aprobada. Ningún cambio se archiva ni se sincroniza por esta
tarea. El prototipo de consola fue autorizado y ejecutado; el JSON v5 permanece
intacto. Entrega 5 abierta, sin iniciar la 6. Los commits anteriores se preservan.
Se preservan la captura previa y el registro histórico de base-escritorio.

## Recorrido manual existente: base-escritorio

Completado según declaración de la usuaria del 14/09/2026. Se conservan los pasos
originales como referencia, sin modificar criterios ni atribuir su ejecución al agente.

Usar una carpeta de prueba y archivos descartables, sin reemplazar proyectos reales.

1. Iniciar con el comando anterior. Verificar «Sin título», 2T, sin archivo,
   sin cambios pendientes y el aviso de simulación no disponible. Redimensionar
   la ventana y comprobar que el formulario sigue siendo utilizable.
2. Escribir «Motor de María», seleccionar 4T y comprobar el indicador pendiente.
   Guardar como `motor-4t.json`. Verificar ruta activa y ausencia de cambios.
   Cerrar y volver a iniciar; Abrir ese archivo y comprobar nombre y tipo.
   Repetir con 2T y `motor-2t.json`.
3. Editar y usar Guardar; reabrir para comprobar la actualización. Editar otra vez
   y usar Guardar como `copia.json`; comprobar que pasa a ser el archivo activo y
   que el original conserva sus datos anteriores.
4. Intentar Guardar como sobre un archivo de prueba existente: primero Cancelar
   la sobrescritura y comprobar que conserva edición, ruta y archivos; luego
   Reemplazar y comprobar el resultado. Cancelar también los diálogos Abrir y
   Guardar como y verificar que no cambia el estado activo.
5. Vaciar el nombre y guardar; repetir con solo espacios. Verificar el error y
   que se conserva la edición. Restaurar un nombre válido.
6. Con el Bloc de notas crear `invalido.json` con el texto `{`, y otra copia con
   `{"format_version":true,"name":"Motor","cycle":"2T"}`. Con cambios pendientes,
   intentar abrir ambos: comprobar error y conservación de nombre, tipo, ruta y
   estado pendiente. Abrir luego un proyecto válido, elegir Descartar y comprobar
   que solo entonces se sustituye el proyecto.
7. Con cambios pendientes, probar Nuevo, Abrir un archivo válido, Salir y la X
   de la ventana. En cada caso elegir Cancelar y verificar conservación. Repetir
   eligiendo Guardar: la transición debe continuar solo al guardar correctamente.
   Con un proyecto nuevo, cancelar el destino del guardado y comprobar que la
   transición se detiene. Repetir con Descartar y verificar Nuevo o cierre.
8. Guardar un proyecto de prueba y marcar su archivo como «Solo lectura» desde
   Propiedades de Windows. Editar e intentar Guardar: comprobar error, archivo
   anterior intacto y cambios pendientes. Intentar cerrar eligiendo Guardar:
   debe permanecer abierto. Quitar «Solo lectura» al terminar y volver a guardar.
9. En la versión base-escritorio, repetir creación, guardado y apertura sin conexión a Internet. Comprobar que
   cambiar 2T/4T no muestra ni ejecuta cálculos o simulación.

La tarea 4.2 se marca con la declaración de comprobación manual de la usuaria,
registrada separadamente en tasks.md. Las entregas permanecen sin archivar.
