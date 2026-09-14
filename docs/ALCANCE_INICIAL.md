# MotorSim: alcance inicial

Fecha: 14 de septiembre de 2026.

Este documento concreta una primera versión básica de escritorio, anterior al desarrollo del simulador. Es una especificación de trabajo, no una declaración de funciones implementadas ni de validación física.

## 1. Dirección del producto

MotorSim será una aplicación de escritorio para configurar y simular motores de combustión interna de dos y cuatro tiempos y consultar sus resultados.

El objetivo inmediato es más pequeño: disponer de una aplicación que permita crear, editar, guardar y volver a abrir un proyecto. En esta etapa, elegir 2T o 4T solo identifica el tipo de motor; no ejecuta modelos diferentes ni demuestra capacidad de simulación.

## 2. Decisiones de partida

| Aspecto | Decisión |
| --- | --- |
| Nombre de trabajo | MotorSim |
| Repositorio | `AlejandraValentina/Dino` |
| Plataforma inicial | Windows, aplicación de escritorio |
| Lenguaje | Python |
| Interfaz | PySide6 con Qt Widgets |
| Persistencia inicial | Archivos JSON locales, sin base de datos |
| Implementación | A cargo de Codex, en tareas solicitadas por la usuaria |

PySide6 es la integración oficial de Qt con Python [1]. Qt Widgets proporciona los componentes de interfaz que se utilizarán en esta aplicación [2].

Codex elegirá una combinación estable y compatible de Python y PySide6 para Windows al implementar, y registrará las versiones efectivamente probadas. No se fija aquí un número de versión sin comprobar el entorno.

NumPy, Matplotlib, Numba y el empaquetado con PyInstaller quedan diferidos. No son dependencias obligatorias de esta versión básica. Su necesidad se evaluará cuando exista una función que los requiera.

## 3. Versión básica v0.1

### Ventana y edición

- Una ventana principal identificada como MotorSim, con textos de interfaz en español.
- Un único proyecto activo. No se requieren pestañas de múltiples proyectos.
- Un formulario con dos datos: nombre del proyecto y tipo de motor, con opciones 2T y 4T.
- Acciones: Nuevo, Abrir, Guardar, Guardar como y Salir.
- Indicación visible del archivo activo y de cambios pendientes de guardar.
- Indicación clara: «Versión básica: simulación no disponible».

El nombre no puede quedar vacío al guardar. El tipo de motor debe ser 2T o 4T. Un proyecto nuevo debe partir de valores explícitos y editables, sin depender de datos ocultos del proyecto anterior.

### Archivos y protección del trabajo

Cada proyecto se guarda en un archivo JSON UTF-8. El contenido mínimo comprende una versión del formato, el nombre del proyecto y el tipo de motor. Codex definirá y documentará una estructura sencilla para esos datos, sin construir un sistema de migraciones para formatos que todavía no existen.

Abrir un archivo debe validar el contenido antes de reemplazar el proyecto activo. Un JSON inválido, un campo obligatorio ausente o un formato no admitido deben producir un mensaje comprensible y conservar el trabajo actual.

Guardar debe informar los errores de escritura y no marcar el proyecto como guardado cuando la escritura falle. La implementación debe evitar truncar un archivo válido si el guardado no se completa.

Nuevo, Abrir y Salir deben proteger los cambios pendientes mediante Guardar, Descartar o Cancelar. Cancelar un diálogo o fallar un guardado no debe descartar el trabajo actual. Guardar como no debe sobrescribir silenciosamente otro archivo existente.

## 4. Fuera de esta versión

No se implementarán ecuaciones del motor, combustión, barrido, gasdinámica, conductos, intercambio térmico, pérdidas, ciclos termodinámicos, barridos de RPM ni cálculos de potencia o par.

Tampoco se añadirán gráficos con resultados inventados, un motor de simulación ficticio, parámetros físicos sin uso definido, CAD, optimización, cuentas de usuario, servicios web, sincronización, base de datos, sistema de extensiones, instalador ni actualizaciones automáticas.

La selección 2T/4T no obliga a diseñar ahora una arquitectura general de simuladores. No se importará código, documentación contractual ni infraestructura de proyectos anteriores sin una tarea explícita y una justificación concreta.

## 5. Organización mínima

Una aplicación y un repositorio. Separar el formulario y sus acciones de la lectura, validación y escritura de archivos. Mantener los datos del proyecto independientes de los widgets cuando resulte sencillo.

No imponer ahora una jerarquía de capas, clases abstractas o servicios para funciones futuras. La estructura exacta de carpetas corresponde a la implementación y debe ser proporcional a esta versión.

## 6. Criterio de finalización

La versión básica estará terminada cuando se compruebe el siguiente recorrido:

1. Instalar las dependencias en un entorno virtual limpio e iniciar la ventana con las instrucciones del README.
2. Crear un proyecto 2T, cambiar su nombre, guardarlo y volver a abrirlo conservando los datos.
3. Repetir el recorrido con un proyecto 4T.
4. Modificar un proyecto y verificar Guardar, Descartar y Cancelar al crear otro, abrir otro o salir.
5. Comprobar que archivos inválidos y errores de guardado se informan sin perder el proyecto activo ni presentar el error como éxito.
6. Confirmar que la interfaz no presenta simulaciones ni resultados físicos como disponibles.

Se requieren pruebas automatizadas focalizadas para datos, validación y persistencia, y una comprobación de interfaz del recorrido principal. No se fija una cantidad arbitraria de pruebas ni un porcentaje de cobertura como objetivo.

Una prueba de interfaz sin pantalla no demuestra por sí sola que la aplicación funcione en Windows. Si el entorno de Codex no permite esa comprobación, debe entregar lo realizado, indicar la limitación y dejar la prueba manual concreta en el README, sin afirmar que Windows está verificado.

El cierre de esta etapa no depende de validar física que todavía no existe. Al completar este recorrido, se detiene la implementación: comenzar el simulador requiere una nueva definición de alcance.

## 7. Decisiones reservadas para el simulador

Antes de añadir cálculo físico se definirán, en una tarea separada, el primer tipo de motor que se simulará, las entradas necesarias, los resultados útiles, el modelo y sus aproximaciones, la evidencia necesaria y un coste de ejecución aceptable.

No se eligen en esta etapa métodos numéricos, tolerancias científicas ni una arquitectura definitiva de cálculo.

## Referencias técnicas

Consultadas el 14 de septiembre de 2026. Fundamentan las herramientas, no constituyen nuevos requisitos del producto.

[1] Qt for Python: https://doc.qt.io/qtforpython-6/index.html

[2] PySide6.QtWidgets: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html
