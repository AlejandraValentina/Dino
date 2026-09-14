# Tareas de base-escritorio

Estado al 14/09/2026: implementación autorizada y realizada; pruebas automatizadas
aprobadas. Recorrido manual completo Windows pendiente. Integración automática
omitida por decisión explícita de la usuaria; se conservan los prompts globales.
Requisitos: [gestion-proyectos](specs/gestion-proyectos/spec.md).

## 1. Preparación

- [x] 1.1 Comprobar el entorno, registrar versiones de Python y PySide6 y preparar la estructura mínima según design.md.
- [x] 1.2 Comprobar OpenSpec en el entorno de Codex y validar este cambio según el README; informar bloqueos sin reintentos indefinidos.

## 2. Datos y archivos

- [x] 2.1 Implementar datos y validación; probar nombres válidos, vacíos, con espacios y tipos admitidos o inválidos.
- [x] 2.2 Implementar lectura y guardado JSON; probar ida y vuelta 2T/4T, acentos, formato inválido y fallos de escritura que conserven el archivo anterior.

## 3. Ventana

- [x] 3.1 Implementar la ventana, formulario, valores iniciales e indicaciones visibles de acuerdo con la especificación.
- [x] 3.2 Conectar Nuevo, Abrir, Guardar, Guardar como y cierre, incluyendo Guardar/Descartar/Cancelar y preservación del proyecto ante errores.

## 4. Comprobación y entrega

- [x] 4.1 Ejecutar las pruebas focalizadas y corregir los incumplimientos concretos de la especificación.
- [ ] 4.2 Comprobar manualmente el recorrido en Windows, incluidos errores y cambios pendientes. Dejar esta casilla sin marcar si no se ejecutó.
- [x] 4.3 Realizar la revisión puntual definida en AGENTS.md y resolver defectos comprobables sin ampliar el alcance.
- [x] 4.4 Actualizar README con comandos realmente comprobados, versiones, resultados y limitaciones. Entregar y detenerse sin comenzar el simulador.

## Evidencia de ejecución

- Git: raíz `E:\dino\Dino`, rama `main`, base `795d0d1d162ae0ff2c3dd0f8e1035b47d6e5e8f7`.
  Árbol limpio antes de implementar; sin cambios ajenos detectados ni cambios de historia.
- Entorno virtual `.venv` creado con Python 3.11.0; PySide6 y Qt 6.11.2 instalados
  y comprobados. Node.js 24.19.0 y OpenSpec 1.3.1 existentes conservados.
- `openspec instructions apply --change base-escritorio --json`, `status` y
  `validate base-escritorio --strict --no-interactive`: ejecutados y aprobados.
  No se ejecutó init/update ni se cambió configuración global.
- `motorsim/project.py`, `storage.py`, `window.py` y `__main__.py`: datos, archivos,
  ventana y entrada de aplicación. Solo nombre, tipo y archivos locales.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: 22 pruebas aprobadas.
  Incluyen validación, persistencia, fallos que conservan el archivo, transiciones
  y diálogos. `python -m pip check` en `.venv`: sin dependencias rotas.
- Con `QT_QPA_PLATFORM=windows`: 15 pruebas de widgets aprobadas, incluidas
  selección real de archivo, cancelación y botones de confirmación. Comprobación
  automatizada visible, separada de las pruebas offscreen y del recorrido manual.
- Inicio real con `.\.venv\Scripts\python.exe -m motorsim` y captura del escritorio
  Windows 10 (10.0.19045) inspeccionada: ventana y formulario visibles. Comprobación
  visual parcial; no acredita todos los pasos manuales. 4.2 permanece pendiente;
  README contiene el recorrido exacto, incluidos errores y cambios pendientes.
- Revisión independiente de solo lectura por subagente según AGENTS.md: sin
  defectos concretos en código, dependencias y las 20 pruebas disponibles entonces;
  el revisor también ejecutó esas 20 pruebas con resultado aprobado. Autorrevisión
  del principal para el diff completo, documentación y dos pruebas adicionales.
- README actualizado con instalación, ejecución, versiones, resultados y límites.
  No se inició simulación, no se sincronizaron specs ni se archivó el cambio.

## Cierre

Marcar solo lo efectivamente realizado. Una entrega con verificación Windows
pendiente puede compartirse, pero no se declara completamente comprobada ni se
archiva como terminada. La validación de OpenSpec comprueba los documentos,
no el funcionamiento de MotorSim. No sincronizar ni archivar este cambio antes
de cumplir las tareas y recibir autorización de cierre.
