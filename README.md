# MotorSim

Editor de proyectos y ficha del motor en Python + PySide6/Qt Widgets. La entrega
actual [geometria-cinematica](openspec/changes/geometria-cinematica/specs/geometria-cinematica/spec.md)
añade posición del pistón, volúmenes y curvas geométricas a la ficha existente.
No contiene simulación física ni estimaciones de rendimiento.

Estado de la entrega 1: **Por verificar**, por el recorrido manual Windows
heredado aún pendiente. La [hoja de ruta](docs/HOJA_DE_RUTA_MotorSim.md#estado-de-avance)
resume el avance; [tasks.md](openspec/changes/caracteristicas-motor/tasks.md)
conserva el detalle histórico. Entrega 2 autorizada y **Por verificar**: falta
la captura e inspección del escritorio Windows desbloqueado. Entrega 3 no autorizada.

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
No se guardan curvas; JSON sigue en versión 2. Ecuaciones y caso admitido en el
[diseño](openspec/changes/geometria-cinematica/design.md).

Comprobación visual real **pendiente**: las capturas del escritorio devolvieron
una imagen azul uniforme, con LogonUI activo. Se inspeccionó únicamente el
renderizado de los widgets Qt Windows a escala normal y 150 %; no se presenta
como captura real ni acredita la sesión visible. Para completar: desbloquear
Windows, cargar datos de prueba identificados (D=80, S=90, L=150 mm, C=10,5),
abrir Geometría, inspeccionar curvas/esquema, cambiar 2T/4T, mover ángulo por
teclado, vaciar C y luego L verificando retirada selectiva; redimensionar y
comprobar escalado. Conservar captura real y registrar evidencia en tasks.md.

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
aprobadas, incluidos diálogos Qt reales (automatización; no acredita escritorio
desbloqueado ni recorrido manual). Para repetirlas:

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_window.py -v
$env:QT_QPA_PLATFORM = $null
```

Las pruebas por defecto usan `offscreen`. La automatización visible y la inspección
de capturas Windows son evidencia distinta; no equivalen al recorrido manual
completo histórico de base-escritorio, que sigue pendiente y sin marcar.

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

## Formato JSON versión 2

Objeto UTF-8 con claves obligatorias: `format_version` (entero 2), `name`, `cycle`
(`2T`/`4T`), `manufacturer`, `model`, `notes` (textos; los opcionales vacíos son `""`),
`cylinder_count` (entero positivo o null), `bore_mm`, `stroke_mm`, `rod_length_mm`
(números positivos finitos o null), `compression_ratio` (número finito > 1 o null).
No se almacenan unidades ni resultados derivados. No se redondean las entradas al
guardar; los decimales usan la precisión numérica de Python, no la precisión de
presentación de resultados. No se utilizan ceros como sustitutos de datos ausentes.

Se leen archivos versión 1 con `name` y `cycle`; las características quedan vacías.
Abrir no modifica el archivo ni marca una conversión como edición. Solo un Guardar
o Guardar como explícito escribe versión 2. No hay sistema general de migraciones.

## OpenSpec y estado

Cambio activo: [geometria-cinematica](openspec/changes/geometria-cinematica/),
con [registro de tareas](openspec/changes/geometria-cinematica/tasks.md).
Entrega 1 ya registrada y publicada en `040e789`; no se rehízo ni se acepta
retrospectivamente su recorrido manual.
AGENTS.md vincula la restricción de nombre/tipo sin geometría a base-escritorio.
No se alteran sus criterios ni se completa su recorrido pendiente retrospectivamente.

La integración automática OpenSpec–Codex sigue omitida por decisión explícita
para preservar prompts y configuración global. No se ejecutó init/update ni se
reinstalaron herramientas. Comandos documentales ejecutados:

```powershell
openspec instructions apply --change geometria-cinematica --json
openspec validate geometria-cinematica --strict --no-interactive
```

Validación estricta aprobada. Ningún cambio se archiva ni se sincroniza por esta
entrega. El alcance termina en geometría/cinemática; entrega 3 y simulador requieren otra autorización.
Se preservan la captura previa y el registro histórico de base-escritorio.

## Recorrido manual histórico pendiente: base-escritorio

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

Registrar lo observado en tasks.md antes de marcar 4.2. La entrega no se declara
completamente comprobada mientras este recorrido obligatorio siga pendiente.
