# Tareas de base-escritorio

Estado inicial: ninguna tarea de implementación ejecutada. La presencia de esta
lista no autoriza comenzar; hace falta una solicitud explícita de la usuaria.
Requisitos: [gestion-proyectos](specs/gestion-proyectos/spec.md).

## 1. Preparación

- [ ] 1.1 Comprobar el entorno, registrar versiones de Python y PySide6 y preparar la estructura mínima según design.md.
- [ ] 1.2 Comprobar OpenSpec en el entorno de Codex y validar este cambio según el README; informar bloqueos sin reintentos indefinidos.

## 2. Datos y archivos

- [ ] 2.1 Implementar datos y validación; probar nombres válidos, vacíos, con espacios y tipos admitidos o inválidos.
- [ ] 2.2 Implementar lectura y guardado JSON; probar ida y vuelta 2T/4T, acentos, formato inválido y fallos de escritura que conserven el archivo anterior.

## 3. Ventana

- [ ] 3.1 Implementar la ventana, formulario, valores iniciales e indicaciones visibles de acuerdo con la especificación.
- [ ] 3.2 Conectar Nuevo, Abrir, Guardar, Guardar como y cierre, incluyendo Guardar/Descartar/Cancelar y preservación del proyecto ante errores.

## 4. Comprobación y entrega

- [ ] 4.1 Ejecutar las pruebas focalizadas y corregir los incumplimientos concretos de la especificación.
- [ ] 4.2 Comprobar manualmente el recorrido en Windows, incluidos errores y cambios pendientes. Dejar esta casilla sin marcar si no se ejecutó.
- [ ] 4.3 Realizar la revisión puntual definida en AGENTS.md y resolver defectos comprobables sin ampliar el alcance.
- [ ] 4.4 Actualizar README con comandos realmente comprobados, versiones, resultados y limitaciones. Entregar y detenerse sin comenzar el simulador.

## Cierre

Marcar solo lo efectivamente realizado. Una entrega con verificación Windows
pendiente puede compartirse, pero no se declara completamente comprobada ni se
archiva como terminada. La validación de OpenSpec comprueba los documentos,
no el funcionamiento de MotorSim. No sincronizar ni archivar este cambio antes
de cumplir las tareas y recibir autorización de cierre.
