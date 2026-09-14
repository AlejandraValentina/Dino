# MotorSim

Aplicación de escritorio para configurar y simular motores de combustión interna de dos y cuatro tiempos.

**Estado actual: documentación inicial. La aplicación y el simulador todavía no están implementados.**

MotorSim es el nombre de trabajo de la aplicación. El repositorio se llama Dino. La implementación se realizará con Codex; esta entrega contiene únicamente documentación.

## Primera etapa

Construir una versión básica de escritorio antes de comenzar el simulador: una ventana, un formulario con nombre de proyecto y tipo de motor 2T/4T, y acciones para crear, abrir y guardar proyectos locales sin perder cambios pendientes.

En esa versión, 2T y 4T son datos del proyecto. No hay simulación, ecuaciones del motor, potencia, par ni resultados físicos.

## Tecnología acordada

- Python.
- PySide6 con Qt Widgets.
- Windows como plataforma inicial.
- Archivos JSON locales, sin servidor ni base de datos.

Las versiones concretas de Python y PySide6 se registrarán al comprobar el entorno de implementación. Las bibliotecas numéricas, los gráficos y el empaquetado quedan para tareas posteriores que los necesiten.

## Documentación

| Archivo | Contenido |
| --- | --- |
| [Alcance inicial](docs/ALCANCE_INICIAL.md) | Objetivo, funciones de la versión básica, exclusiones y criterio de finalización. |
| [Instrucciones para Codex](AGENTS.md) | Reglas de trabajo para implementar sin ampliar la etapa ni anticipar el simulador. |

## Desarrollo y ejecución

Todavía no existen comandos de instalación de la aplicación, ejecución ni pruebas: no se ha creado código. Codex deberá documentarlos aquí cuando implemente la versión básica y comprobarlos en el entorno disponible.

La carpeta de trabajo indicada es `E:\dino`; no es una ruta que deba quedar codificada en la aplicación. Todo acceso a proyectos debe funcionar desde la carpeta que elija la usuaria.

## Límite de esta entrega

El objetivo futuro contempla motores 2T y 4T, pero no define todavía su modelo físico, precisión o coste de ejecución. Terminar la aplicación básica no autoriza a comenzar automáticamente el simulador ni demuestra validez de ningún resultado físico.

No se incorporan código ni obligaciones del proyecto anterior. El archivo `redme.txt` preexistente se conserva sin modificar.
