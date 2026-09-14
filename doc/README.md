# MotorSim

Aplicación de escritorio cuyo objetivo es configurar y simular motores de
combustión interna de dos y cuatro tiempos.

**Estado actual:** documentación inicial. Este paquete no contiene una aplicación
implementada ni un modelo de simulación.

## Decisiones de partida

| Elemento | Decisión |
| --- | --- |
| Nombre de la aplicación | MotorSim |
| Repositorio | `AlejandraValentina/Dino` |
| Carpeta de trabajo indicada | `E:\dino` |
| Plataforma de la primera versión | Windows |
| Lenguaje | Python |
| Interfaz | PySide6 con Qt Widgets |
| Persistencia inicial | Un archivo JSON por proyecto |
| Desarrollo | Codex |

## Primera entrega: versión 0.1

Construir la base utilizable de la aplicación: una ventana para crear un proyecto
de motor, editar sus datos básicos, guardarlo y volver a abrirlo.

El único cálculo será la cilindrada geométrica por cilindro. Seleccionar 2T o 4T
identifica el proyecto; **todavía no ejecuta modelos de esos motores**.

El alcance y la comprobación de esta entrega están en
[`docs/ALCANCE_0_1.md`](docs/ALCANCE_0_1.md). Ese archivo es la referencia funcional
de esta etapa; no hace falta generar otra especificación para comenzar.

## Límites

No se implementan aún el simulador físico, curvas de rendimiento ni integración
con los proyectos anteriores. La primera entrega se ejecutará desde un entorno
Python local; el instalador queda fuera de esta etapa.

Las instrucciones de instalación, ejecución y pruebas, junto con las versiones
realmente comprobadas, se incorporarán a este README durante la implementación.
No se presentan comandos como operativos antes de que exista el código.
