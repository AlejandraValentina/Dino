# MotorSim

Aplicación de escritorio cuyo objetivo es configurar y simular motores de
combustión interna de dos y cuatro tiempos. Repositorio: `AlejandraValentina/Dino`.

**Estado: documentación y flujo de trabajo preparados. Aplicación no implementada.**

## Primera entrega

La base v0.1 permitirá crear, editar, guardar y recuperar un proyecto de motor.
Solo almacena nombre y tipo 2T/4T; no calcula geometría ni ejecuta un modelo de
funcionamiento del motor. El alcance exacto tiene una única
fuente en [la especificación del cambio](openspec/changes/base-escritorio/specs/gestion-proyectos/spec.md).

La tecnología acordada es Python, PySide6/Qt Widgets, Windows y archivos JSON
locales. No hay servidor ni base de datos. Las versiones se registrarán al probar
la implementación. Bibliotecas numéricas, gráficos y empaquetado quedan fuera.

## Documentación y responsabilidades

| Referencia | Responsabilidad |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Autoridad, Codex principal, revisión puntual y condición de parada. |
| [Propuesta](openspec/changes/base-escritorio/proposal.md) | Motivo, límites y reconciliación de los documentos anteriores. |
| [Especificación](openspec/changes/base-escritorio/specs/gestion-proyectos/spec.md) | Única definición del comportamiento y sus escenarios comprobables. |
| [Diseño](openspec/changes/base-escritorio/design.md) | Decisiones técnicas mínimas, sin arquitectura para el simulador futuro. |
| [Tareas](openspec/changes/base-escritorio/tasks.md) | Avance de implementación; todas pendientes al preparar esta documentación. |

Un Codex principal coordina e implementa; una revisión puntual comprueba el
resultado sin ampliar el alcance. No se agrega un orquestador externo ni un equipo
permanente de agentes. El modelo usado por Codex no es dependencia de MotorSim.

## OpenSpec

Se utiliza el esquema estándar `spec-driven` y un único cambio: `base-escritorio`.
`openspec/config.yaml` contiene el contexto del proyecto. `openspec/specs/` no tiene
todavía capacidades consolidadas: preparar documentos no equivale a terminar código.

Los archivos Markdown/YAML se han preparado directamente en el repositorio. No se
ha instalado OpenSpec en el equipo de la usuaria, ni generado o comprobado allí
su integración con Codex. La CLI oficial no pudo ejecutarse durante esta preparación:
la consulta al registro npm falló por resolución DNS (`EAI_AGAIN`). No se declara
una validación oficial de OpenSpec aprobada.

### Preparación del entorno de Codex

La instalación oficial documentada requiere Node.js 20.19.0 o posterior.
Comprobar primero `node --version` y `openspec --version`. Si la CLI no está
instalada, su instalación debe hacerse con los permisos y autorización del entorno:

```text
npm install -g @fission-ai/openspec@latest
openspec --version
```

Registrar la versión efectivamente instalada; no cambiar versiones globales sin
necesidad. Node y OpenSpec son herramientas de desarrollo, no dependencias para
que el usuario final ejecute la aplicación Python.

Desde la raíz del repositorio, la inicialización de integración documentada es:

```text
openspec init --tools codex --profile core
```

Este paso sigue pendiente en el entorno de Codex. Revisar su diff y conservar
AGENTS.md, config.yaml y el cambio existente; no usar `--force`, regenerar el
alcance ni crear otro cambio equivalente. Las skills oficiales que genere son
instrucciones de flujo de trabajo, no agentes permanentes ni un orquestador.
No hace falta un esquema personalizado ni habilitar todas las herramientas.

Comprobaciones documentadas para ejecutar después:

```text
openspec status --change base-escritorio --json
openspec validate base-escritorio --strict --no-interactive
```

Estos comandos comprueban preparación y estructura documental; no prueban la
aplicación ni autorizan su implementación. Un fallo del entorno se informa, no
se convierte en una cadena indefinida de instalaciones o reintentos.

Documentación técnica consultada el 14 de septiembre de 2026:
[instalación](https://openspec.dev/docs/installation),
[CLI](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md),
[esquema spec-driven](https://openspec.dev/docs/schemas/spec-driven) y
[integración Codex](https://github.com/Fission-AI/OpenSpec/blob/main/docs/supported-tools.md).

## Ejecución de MotorSim

Todavía no hay código ni comandos operativos de instalación, ejecución o pruebas
de MotorSim. Codex los documentará y comprobará al implementar la aplicación.
La carpeta de trabajo indicada es `E:\dino`; no debe quedar codificada como ruta.

## Autorización y cierre

Esta actualización es documental. La implementación requiere una orden explícita.
Completar la base no autoriza a empezar el simulador físico. No se archiva el cambio
como terminado si quedan comprobaciones obligatorias pendientes.

`docs/ALCANCE_INICIAL.md` se conserva como referencia a OpenSpec; su contenido
anterior sigue en el historial Git y no es una segunda especificación. Se respeta
la eliminación previa de `doc/` y se mantiene `redme.txt` sin cambios.
