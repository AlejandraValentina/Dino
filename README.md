# MotorSim

Editor de proyectos y ficha del motor en Python + PySide6/Qt Widgets. La entrega
actual [configuracion-2t](openspec/changes/configuracion-2t/specs/configuracion-2t/spec.md)
añade lumbreras rectangulares de escape/transferencia y registro de cárter.
La ficha, posición del pistón, volúmenes y curvas geométricas existentes se conservan.
No contiene simulación física ni estimaciones de rendimiento.

Estado de las entregas 1 y 2: **Completadas**. La usuaria comunicó el 14/09/2026
que realizó las comprobaciones manuales pendientes, incluido el uso sin Internet,
y aceptó ambas entregas. No quedan otros criterios obligatorios pendientes según
las tareas existentes. La [hoja de ruta](docs/HOJA_DE_RUTA_MotorSim.md#estado-de-avance)
resume el estado. Esta aceptación es evidencia de la usuaria, separada de las
pruebas automatizadas e inspección visual del agente. Sin archivar. La entrega 3
está **En curso**: este primer tramo está implementado; admisión pendiente de
definición dentro de la misma entrega. No se inicia la entrega 4.

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
No se guardan curvas; el formato actual es JSON versión 3. Ecuaciones y caso admitido en el
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
existentes. No se deduce ni genera presión/compresión. **Admisión: Pendiente de
definición**; no se elige un sistema ni se generan eventos de admisión.

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
de widgets Windows aprobadas**. La colección actual contiene 59 tests. Se conserva
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

**47 pruebas aprobadas** y `pip check` sin dependencias rotas. Cubren JSON v2
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

## Formato JSON versión 3

Conserva todos los campos de ficha de versión 2 (`name`, `cycle`, `manufacturer`,
`model`, `notes`, `cylinder_count`, `bore_mm`, `stroke_mm`, `rod_length_mm`,
`compression_ratio`) y añade `ports`, `crankcase_volume_bdc_cm3` y
`two_stroke_reference`. `format_version` es el entero 3. Cada fila de `ports`
guarda `name`, `function` (`escape`, `transfer` o null), `top_mm`, `height_mm`,
`width_mm`. La lista vacía representa ausencia de lumbreras. Dimensiones/cárter
no informados son null; los textos opcionales, cadenas vacías. No se redondean
entradas para guardarlas ni se incluyen unidades en los valores numéricos.

Referencia fija: `rectangular-peripheral-tdc-developed-bdc-v1`, con las convenciones
explicadas en el [diseño](openspec/changes/configuracion-2t/design.md).
Una referencia diferente se rechaza para no reinterpretar medidas. No se guardan
curvas ni resultados. Se mantienen guardado seguro y confirmación de sobrescritura.

Se leen versiones 1 y 2 conservando sus campos; se inicializan lumbreras vacías
y volumen de cárter null. Abrir no reescribe el archivo: la conversión a v3 solo
se persiste mediante Guardar/Guardar como explícito.

## OpenSpec y estado

Cambio activo: [configuracion-2t](openspec/changes/configuracion-2t/),
con [registro de tareas](openspec/changes/configuracion-2t/tasks.md).
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
openspec instructions apply --change configuracion-2t --json
openspec validate configuracion-2t --strict --no-interactive
```

Validación estricta aprobada. Ningún cambio se archiva ni se sincroniza por esta
entrega. El tramo termina en lumbreras y registro de cárter; admisión queda pendiente.
No se comienza entrega 4 ni simulador.
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
