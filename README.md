# MotorSim

Base de escritorio para crear, editar, guardar y abrir proyectos locales de motor.
Solo almacena nombre y tipo 2T/4T. **No contiene simulación, geometría ni gráficos.**

**Estado: base implementada y probada automáticamente; recorrido manual completo
Windows pendiente. El cambio permanece abierto y no archivado.**

El comportamiento está definido únicamente en
[la especificación de base-escritorio](openspec/changes/base-escritorio/specs/gestion-proyectos/spec.md).
Se conservan [AGENTS.md](AGENTS.md), la [propuesta](openspec/changes/base-escritorio/proposal.md)
y el [diseño](openspec/changes/base-escritorio/design.md). El registro de avance es
[tasks.md](openspec/changes/base-escritorio/tasks.md).

## Instalar y abrir en Windows

Versiones comprobadas el 14/09/2026: Windows 10 (10.0.19045), Python 3.11.0,
PySide6 6.11.2 y Qt 6.11.2. Se creó un entorno virtual nuevo en el proyecto;
las dependencias Python se instalaron allí. No se requiere activar el entorno.

Desde PowerShell, para instalar en una copia limpia con Python disponible:

```powershell
Set-Location E:\dino\Dino
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para abrir MotorSim desde esa carpeta:

```powershell
.\.venv\Scripts\python.exe -m motorsim
```

Se ejecutaron la creación del entorno, la instalación, el comando de inicio y
la comprobación de dependencias. La ruta anterior es la ubicación local de esta
copia; la aplicación no la tiene codificada. No hay instalador ni servidor.
Internet solo se necesita para descargar las dependencias, no para usar MotorSim.

## Uso

El menú **Archivo** ofrece Nuevo, Abrir, Guardar, Guardar como y Salir. Al iniciar,
el proyecto es «Sin título», 2T y sin archivo asociado. La ventana muestra la ruta,
los cambios pendientes y «Versión básica: simulación no disponible».

El nombre puede editarse libremente; al guardar no puede estar vacío ni contener
solo espacios. Guardar solicita destino la primera vez. Guardar como permite una
copia y confirma la sobrescritura de un destino existente. El archivo JSON UTF-8
contiene únicamente `format_version: 1`, `name` y `cycle`.

Nuevo y cierre ofrecen Guardar, Descartar o Cancelar si hay cambios. Abrir primero
elige y valida el archivo, y después ofrece esas opciones antes de sustituir el
proyecto. Cancelar el diálogo o elegir un archivo inválido conserva la edición,
la ruta y el estado pendiente. Un error de guardado conserva el archivo anterior.

## Pruebas y revisión

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Resultado: **22 pruebas aprobadas**; `pip check` sin dependencias rotas. Cubren
validación de nombres y tipos, versión entera (rechaza booleanos), JSON inválido,
UTF-8 y acentos, ambos tipos de motor, ida y vuelta, fallos de escritura/sincronización/
reemplazo, conservación del archivo anterior, cancelaciones, sobrescritura y
transiciones con cambios pendientes. Se usan archivos temporales de prueba.

Por defecto los tests de widgets usan `offscreen`: no equivalen a una prueba
visual de Windows. También se ejecutaron **15 pruebas de widgets con la plataforma
Qt `windows`, todas aprobadas**, incluidos diálogos reales de selección de archivo,
Guardar/Descartar/Cancelar y confirmación de sobrescritura. Otras pruebas sustituyen
los diálogos para cubrir errores y transiciones de forma determinista.

Para repetir las pruebas de widgets con ventanas visibles en una consola PowerShell
sin una selección previa de plataforma Qt:

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_window.py -v
$env:QT_QPA_PLATFORM = $null
```

Se abrió además la aplicación con su comando real y se inspeccionó una captura
del escritorio Windows: ventana, formulario, selector, indicador de edición y
aviso de simulación no disponible visibles. Esto es una comprobación visual
parcial y automatización visible, **no el recorrido manual completo**.

Se realizó autorrevisión del cambio y una revisión independiente de solo lectura
mediante subagente, conforme a AGENTS.md. El revisor no identificó defectos concretos
en el código y ejecutó las 20 pruebas existentes en ese momento: todas aprobadas.
Las dos pruebas adicionales de diálogos y la documentación final fueron comprobadas
por el principal. No se presenta esa última pasada como revisión independiente.

### Recorrido manual pendiente en Windows

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
9. Repetir creación, guardado y apertura sin conexión a Internet. Comprobar que
   cambiar 2T/4T no muestra ni ejecuta cálculos o simulación.

Registrar lo observado en tasks.md antes de marcar 4.2. La entrega no se declara
completamente comprobada mientras este recorrido obligatorio siga pendiente.

## OpenSpec

Se conserva el cambio existente `base-escritorio`, esquema `spec-driven` y
`openspec/config.yaml`. Versiones disponibles comprobadas: Node.js 24.19.0 y
OpenSpec 1.3.1. Se conservó la instalación existente, sin reinstalar herramientas.

La generación automática de la integración OpenSpec–Codex se **omitió por decisión
explícita de la usuaria**, para conservar intactos los prompts globales existentes.
No se ejecutó `openspec init` ni `openspec update`, ni se modificaron `delivery`,
los prompts o la configuración global de Codex u OpenSpec. No se presenta esa
integración como realizada ni como requisito pendiente para implementar esta base.

Comandos ejecutados satisfactoriamente desde la raíz:

```powershell
openspec instructions apply --change base-escritorio --json
openspec status --change base-escritorio --json
openspec validate base-escritorio --strict --no-interactive
```

La validación documental estricta aprobó. El estado completo de los artefactos
significa documentos preparados, no aplicación terminada. Node y OpenSpec no
son dependencias de ejecución de MotorSim.

No se sincronizan especificaciones ni se archiva el cambio sin autorización.
La base no autoriza comenzar el simulador físico. `docs/ALCANCE_INICIAL.md` sigue
como referencia y `redme.txt` se conserva sin cambios.
