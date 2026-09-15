## ADDED Requirements

### Requirement: Dos resultados validados independientes del editor
MUST ofrecer Comparar resultados desde Simulación 2T, A/base y B/modificada, mediante
el lector existente de manifest.json. MUST mostrar identidad del proyecto/run_id,
origen, régimen, modelo, variante, perfil y convergencia. MUST conservar selección
anterior ante archivo ilegible. MUST NOT calcular, usar o modificar el proyecto activo.

#### Scenario: Archivo inválido
- **WHEN** se intenta reemplazar A o B con un resultado ilegible
- **THEN** se explica el error y se conservan selección y datos anteriores.

### Requirement: Compatibilidad y diferencias explícitas
MUST exigir convergencia y balances, modelo/configuración física, condiciones
(rpm, gas, contornos, Cd, energía, receta p/T/Y y referencias), perfil y variante
iguales. MUST explicar diferencias o metadata faltante sin comparación cuantitativa.
MUST permitir geometría/m/U/F derivados y metadata/origen distintos. MUST resumir
todas las diferencias geométricas de ficha, cárter, lumbreras, falda y conductos,
separando cambios descriptivos; números equivalentes y orden de filas equivalentes
de lumbreras MUST NOT considerarse cambios físicos. MUST reutilizar correspondencia por función.

#### Scenario: Perfil distinto o diagnóstico
- **WHEN** uno de los resultados tiene otro perfil o no está convergido con balances aprobados
- **THEN** se identifica su estado y la causa que impide comparar/exportar, sin curvas cuantitativas vigentes.

### Requirement: Tabla y superposición fieles
MUST mostrar A, B, B−A de trabajos C/K separados, pmax y Y de los cuatro volúmenes
desde resumen validado. Porcentaje de trabajo/presión MUST ser 100*(B−A)/abs(A),
no definido con A=0; Y solo diferencia absoluta. MUST superponer muestras con
estilos A/B distinguibles, ejes comunes, presión absoluta y unidades. Alineación
MUST restar vueltas completas según referencia de cigüeñal, sin alinear picos ni
ordenar P-V por volumen. MUST NOT suavizar/inventar datos ni declarar motor mejor,
potencia al eje o validez experimental. MUST mantener aviso 0D/energía prescrita/sin ondas.

#### Scenario: Diferentes ciclos de convergencia
- **WHEN** A y B convergieron en distinto número de vueltas
- **THEN** se comparan sus últimas vueltas por la misma fase, preservando muestras originales y orden temporal.

### Requirement: Exportar comparación compatible sin sobrescribir
MUST exportar resumen.csv y curvas.csv a carpeta nueva, UTF-8/coma/punto decimal,
escape correcto, valores sin redondear, unidades e identidades A/B y run_id en ambos.
Curvas MUST incluir ángulo de ciclo, presión absoluta y volumen. MUST informar
fallos sin éxito parcial ni modificar resultados fuente o archivos existentes.

#### Scenario: Escritura fallida o destino existente
- **WHEN** no pueden escribirse los dos CSV o ya existe el destino
- **THEN** se informa el error, se conserva la comparación cargada y no se sobrescriben archivos.
