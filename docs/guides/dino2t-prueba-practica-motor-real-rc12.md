# Guía práctica de prueba — Dino 2T rc12 TRIAL

Esta guía sirve para definir y comparar un motor real en Desktop. Una prueba
funcional demuestra que la aplicación guarda y ejecuta una configuración; por
sí sola no demuestra que el modelo prediga correctamente el motor.

## Preparar el proyecto

1. Conservá intactos los documentos de referencia del motor: plano, ficha,
   mediciones y condiciones de ensayo. Anotá su procedencia y versión.
2. En `MODELO`, creá un proyecto y cargá únicamente los datos conocidos:
   cilindro y carrera, biela, volúmenes, distribución, admisión, puertos y
   estaciones del escape que el modelo permita representar.
3. No completes un dato desconocido por intuición. Dejalo como desconocido o
   identifica el valor como supuesto sintético. En particular, no deduzcas el
   volumen absoluto del cárter de una relación de compresión si faltan su
   definición, ángulo de referencia y límites geométricos.
4. Guardá, cerrá y volvé a abrir el proyecto. Comprobá unidades, geometría,
   distribución, nombre de variante y cotas del escape.

## Comparar diseños

1. Conservá una variante base sin modificar y duplicala para cada propuesta.
2. Cambiá una familia de parámetros por comparación (por ejemplo, sólo el
   escape). Anotá qué cambió y mantené iguales las condiciones de operación.
3. Revisá en `SIMULAR` el RPM, los límites de tiempo y recursos, y la opción de
   despacho. Para una primera comprobación, usá una ejecución acotada; no la
   presentes como búsqueda de periodicidad.
4. En `RESULTADOS`, compará variantes al mismo RPM. Inspeccioná el estado de
   convergencia, periodicidad, conservación y procedencia antes de interpretar
   potencia o torque. Los transitorios y puntos no convergidos son exploratorios;
   no son curvas definitivas.
5. Conservá el proyecto, los resultados exportados y sus archivos de
   procedencia asociados. No separes un CSV de su JSON cuando ese par contiene
   la definición y procedencia del histórico.

## Qué demuestra cada prueba

| Evidencia | Qué permite afirmar | Qué no permite afirmar |
|---|---|---|
| Crear, editar, guardar y reabrir | El flujo de proyecto conserva los valores introducidos | Que esos valores describen con exactitud el motor físico |
| Preparar A/B y ejecutar un punto acotado | La interfaz conecta variantes, configuración y ejecución | Que el punto es periódico o que predice la potencia medida |
| Resultado marcado periódico y controles numéricos aprobados | El estado cumple los criterios numéricos registrados para ese caso | Validación experimental o exactitud predictiva general |
| Comparación ciega con mediciones completas, condiciones coincidentes, incertidumbres y geometría identificada | Evidencia para evaluar la predicción dentro del alcance preregistrado | Validez fuera de ese motor, combustible, régimen o condiciones |

Hasta completar esa última clase de evidencia, identificá los resultados como
sintéticos, exploratorios o no validados según corresponda. La aceptación
interna de rc12 valida Desktop como TRIAL; no valida físicamente el simulador.
