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


### Requirement: Régimen acotado y lista exacta
En proyecto actual MUST admitir punto RPM entero 2500–3500 inicial 3000, o barrido
2–5 enteros distintos ascendentes del mismo rango, paso positivo y extremo exacto.
MUST mostrar lista antes de ejecutar (inicial 2500/3000/3500) y rechazar inválidos
sin sustituciones. Referencia MUST permanecer 3000; condiciones, perfil B/100 Pa,
leyes y criterios MUST conservarse; JSON v5 MUST NOT cambiar.

#### Scenario: Plan inválido
- **WHEN** se ingresa tipo/rango/paso/cantidad o extremo incompatible
- **THEN** se explica el error y no se inicia cálculo ni se ajusta silenciosamente.

### Requirement: Parametrización y secuencia independiente
MUST propagar RPM a grados/segundos (6*rpm), vuelta (60/rpm), dV/dt, tasas de energía
y marcador, muestras y validación. Aporte angular 350°/40° MUST conservarse.
MUST capturar una única geometría válida incluso sin guardar y lista independiente.
Un solo cálculo activo MUST ejecutar puntos secuenciales desde receta inicial,
sin estado heredado. MUST mostrar punto/total/rpm/ciclos/tiempos reales. Cada punto
MUST respetar 30 ciclos/60 s y límites vigentes; serie máximo 300 s integración.
MUST registrar inicio/escritura separados y total percibido. Cancelar/fallar/no
converger MUST detener sin reintentos, conservar diagnóstico/prefijo y marcar
restantes no ejecutados. Cierre MUST proteger edición y evitar huérfanos.

#### Scenario: Edición y fallo intermedio
- **WHEN** se edita el motor tras iniciar y el segundo punto falla
- **THEN** se conserva la copia inicial para toda la serie, resultado anterior/diagnóstico y restantes sin ejecutar.

### Requirement: Serie persistente y resultados compatibles
MUST guardar resultados individuales v3 reconstruidos estrictamente con RPM,
conservar lectores v1/v2 a 3000 y comprobar tiempo–ángulo efectivo. MUST registrar
índice local con identidad/copia/lista/estados/resultados/motivo, actualizado por
punto/final, sin sobrescrituras. Reabrir MUST validar identidades/entradas/posición,
rechazar rutas externas y cruces de series, no requerir proyecto ni recalcular.
MUST conservar aviso de configuración anterior. A/B MUST admitir versiones
compatibles a igual condición efectiva y rechazar diferentes RPM/perfiles.

#### Scenario: Índice ajeno
- **WHEN** un índice apunta a un punto de otra serie o a una ruta externa
- **THEN** se rechaza y se conserva la selección anterior.

### Requirement: Consulta y CSV del barrido
MUST mostrar RPM/estado/ciclos/tiempo/W_C/W_K/pmax y causas; fallidos/no ejecutados
MUST tener magnitudes aceptadas vacías. Punto convergido MUST abrir vista individual.
MUST dibujar puntos reales W_C/RPM y pmax/RPM sin ajuste, extrapolación ni unión
sobre fallos. MUST mantener aviso 0D prescrito/sin ondas ni sintonía y MUST NOT
mostrar potencia, par u óptimos. CSV MUST conservar unidades/ids/estados, incluidos
no ejecutados, reutilizando exportación exclusiva sin alterar CSV A/B.

#### Scenario: Serie interrumpida
- **WHEN** se reabre y exporta una serie con punto no convergido
- **THEN** se muestran/exportan causa y estado sin ceros como magnitudes aceptadas, ni curvas inventadas.
