# Instrucciones para Codex

## Contexto y lectura

MotorSim es el nombre de trabajo de la aplicación; Dino es el repositorio. Es una aplicación de escritorio en Python y PySide6/Qt Widgets, con Windows como plataforma inicial.

Leer `README.md` y `docs/ALCANCE_INICIAL.md` antes de cambiar archivos. La etapa inicial es una base de escritorio para gestionar proyectos, no el simulador físico.

Este archivo orienta el trabajo, pero no inicia tareas por sí mismo. Si la solicitud es documental, modificar solo documentación. Implementar cuando la tarea de la usuaria lo solicite y respetar su alcance.

## Límites

- Implementar únicamente la tarea solicitada. No comenzar la etapa siguiente de forma autónoma.
- Para la versión básica, limitarse a ventana, nombre de proyecto, selector 2T/4T, archivos JSON y protección de cambios pendientes.
- No implementar cálculos físicos, simulación ficticia, curvas inventadas ni parámetros físicos todavía indefinidos.
- No importar el proyecto anterior ni sus contratos, fases o infraestructura sin autorización explícita.
- No convertir mejoras opcionales en bloqueos de entrega. Registrar una limitación concreta en lugar de abrir otra campaña de trabajo.
- No ampliar el alcance mediante arquitectura preventiva, microservicios, API web, extensiones, múltiples agentes obligatorios o documentos de proceso adicionales.

## Implementación proporcional

Preferir Python estándar y PySide6 para la aplicación básica. Añadir una dependencia solo cuando la función actual la requiera y explicar su uso. Mantener los datos y los archivos separados de los widgets sin imponer capas innecesarias.

Usar textos de interfaz y documentación en español. Evitar rutas personales codificadas: el repositorio debe funcionar desde otra carpeta además de la ubicación de trabajo indicada por la usuaria.

Conservar los cambios y archivos ajenos a la tarea. No reescribir la historia de Git ni usar operaciones destructivas para resolver diferencias. No subir credenciales, entornos virtuales ni datos personales de prueba.

La elección del modelo de Codex corresponde a la configuración del entorno de la usuaria; no forma parte de las dependencias de MotorSim ni se modifica desde esta tarea.

## Verificación y entrega

Probar lo necesario para el alcance actual: validación de datos, guardado/apertura y protección frente a errores o pérdida de cambios. Complementar con el recorrido de interfaz indicado en `docs/ALCANCE_INICIAL.md`.

No afirmar que una prueba pasó sin ejecutarla. Distinguir comprobaciones automatizadas, comprobaciones manuales y verificaciones pendientes, especialmente en Windows. No crear esperas o reintentos ilimitados ante un bloqueo del entorno; explicar el impedimento y entregar el trabajo verificable.

Actualizar el README con los comandos reales de instalación, ejecución y pruebas cuando existan. Mantenerlo fiel al estado del repositorio. No añadir comandos para archivos o módulos inexistentes.

Al cerrar una tarea, informar brevemente qué cambió, qué se comprobó y qué quedó pendiente. No declarar que el simulador funciona por haber terminado la interfaz. Al completar la versión básica, detenerse: la física requiere otra tarea.

## Referencia del formato

OpenAI documenta `AGENTS.md` como mecanismo de instrucciones de proyecto para Codex: https://developers.openai.com/codex/agent-configuration/agents-md
