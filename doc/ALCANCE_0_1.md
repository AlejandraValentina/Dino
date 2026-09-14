# MotorSim 0.1 — Base de escritorio

Fecha: 14 de septiembre de 2026.
Estado: alcance inicial para implementar con Codex; aplicación todavía pendiente.

## 1. Objetivo y punto de cierre

Disponer de una aplicación de escritorio que permita completar este recorrido:

**Abrir la aplicación → crear un motor → editar datos → guardar → cerrar →
volver a abrir el archivo y recuperar los mismos datos.**

La etapa termina cuando ese recorrido funciona, las comprobaciones de este
archivo se han realizado y los fallos conocidos quedan indicados. Terminar la
base no autoriza a empezar automáticamente el simulador físico.

## 2. Interfaz y datos

Una ventana principal en español, con el formulario del motor. Acciones:
Nuevo, Abrir, Guardar, Guardar como y Salir. Mostrar el nombre del proyecto y una
indicación de cambios sin guardar. No incorporar paneles de funciones futuras.

| Campo | Regla |
| --- | --- |
| Nombre del motor | Texto obligatorio; no aceptar solamente espacios |
| Tipo de motor | Selector con dos opciones: 2T y 4T |
| Diámetro del cilindro | Milímetros; número finito mayor que cero |
| Carrera | Milímetros; número finito mayor que cero |
| Notas | Texto opcional |

Al crear un proyecto, el tipo inicial será 2T y los demás campos estarán vacíos.
No habrá resultados hasta ingresar dimensiones válidas. Guardar exige completar
los campos obligatorios. Las unidades deben estar visibles en el formulario.

Mostrar la **cilindrada geométrica por cilindro**, calculada a partir de las dos
dimensiones; no es un campo editable. No se configura el número de cilindros.

Con diámetro D y carrera S expresados en milímetros:

`cilindrada_cm3 = (pi / 4) * D**2 * S / 1000`

La expresión procede del volumen de un cilindro. Es un cálculo geométrico, no una
simulación del funcionamiento del motor. Presentarlo con dos decimales, sin
redondear los datos que se guardan. Para D = 54 mm y S = 54 mm, debe mostrar
aproximadamente **123,67 cm³**. Cambiar entre 2T y 4T no cambia esta geometría.

## 3. Archivos y comportamiento básico

Un proyecto por archivo `.json`, codificado en UTF-8. Formato inicial:

```json
{
  "format_version": 1,
  "name": "Motor de ejemplo",
  "cycle": "2T",
  "bore_mm": 54.0,
  "stroke_mm": 54.0,
  "notes": ""
}
```

Guardar solamente los datos de entrada; la cilindrada se recalcula al abrir.
El archivo de ejemplo muestra el formato y no aporta datos experimentales.
`format_version` identifica el formato de archivo, no la versión de la aplicación.
No construir un sistema de migraciones en esta etapa.

Al abrir, comprobar el formato, la versión admitida y los datos antes de sustituir
el proyecto actual. Un archivo inválido o ilegible debe producir un mensaje
comprensible y dejar intacto lo que el usuario estaba editando.

Antes de Nuevo, Abrir o Salir con cambios pendientes, permitir Guardar, Descartar
o Cancelar. Cancelar una operación o fallar al guardar no debe hacer perder la
edición actual. Un error de escritura no debe dejar truncado un archivo anterior.
La aplicación no requiere una cuenta, un servidor ni conexión a Internet para
trabajar con sus archivos locales.

## 4. Implementación acotada

Usar Python, PySide6/Qt Widgets y la biblioteca estándar de Python. No añadir
NumPy, SciPy, Matplotlib, Numba ni una base de datos: esta versión no los necesita.
Registrar las versiones probadas al implementar, sin asumir que ya se verificaron.

Separar el formulario de los datos, el cálculo geométrico y la lectura/escritura
mediante pocos módulos. Estas funciones deben poder probarse sin abrir ventanas.
No introducir una arquitectura de complementos, interfaces para solvers futuros,
servicios web ni infraestructura general de simulación.

El código de proyectos anteriores no se incorpora en esta entrega. Empaquetar
un ejecutable o crear un instalador tampoco forma parte de su cierre.

## 5. Comprobación de la entrega

1. La aplicación abre una ventana en Windows y permite editar todos los campos.
2. Crear y guardar un proyecto 2T y otro 4T; reabrirlos recupera todos sus datos,
   incluidas notas con acentos. Guardar como conserva también el archivo original.
3. La geometría del ejemplo da 123,67 cm³; editar dimensiones actualiza el valor.
   Datos vacíos o inválidos no generan resultados ni se guardan como válidos.
4. Cancelar Nuevo, Abrir o Salir con cambios pendientes conserva la edición.
5. Un archivo malformado, una versión no admitida o un fallo de lectura/escritura
   se comunican sin cerrar la aplicación ni perder el proyecto actual.
6. Hay pruebas breves de geometría, validación y lectura/escritura, y el README
   explica cómo instalar, iniciar y probar la aplicación con comandos comprobados.

No fijar un número obligatorio de tests ni crear una campaña de validación
científica para esta base. Las pruebas de funciones no sustituyen la comprobación
de la ventana; si no pudo hacerse, informar esa limitación expresamente.

## 6. Exclusiones

No se calculan presión, temperatura, combustión, intercambio de gases, ondas,
par, potencia ni barridos de RPM. No habrá gráficas inventadas, resultados de
muestra presentados como simulación ni botones que aparenten ejecutar un motor.
Tampoco se eligen todavía el modelo físico, el método numérico o su precisión.

Cualquier función adicional queda fuera de esta entrega. No ampliar el alcance
para preparar posibilidades futuras ni generar otra planificación antes de
implementar lo aquí descrito.
