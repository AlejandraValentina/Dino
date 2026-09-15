## Alcance
Vista accesible desde Simulación 2T; dos resultados independientes del editor.
`load_result` sigue siendo el único lector. No se inicia QProcess al seleccionar,
comparar o exportar. Resultados inválidos no sustituyen la selección anterior.

## Compatibilidad y datos
Comprobar convergencia/balances y comparar campos explícitos de modelo/configuración
admitida, régimen, gas, contornos, Cd, aporte, referencia angular, receta inicial
p/T/Y, perfil y variante. Metadata ausente impide acreditar compatibilidad y se
identifica. No comparar literalidad de archivos, geometría, m/U/F derivados ni
identidades/nombres/rutas/dirty como condiciones de funcionamiento.
Reutilizar `validated_model` para interpretar geometría canonizada por función.
Resumen por campos de ficha, cárter, lumbreras, falda y tramos; nombres y descripción
separados. Igualdad numérica considera 54 y 54.0 equivalentes; filas de lumbreras
se canonizan por geometría/función, sin confundir orden de presentación con motor.

Tabla del último ciclo convergido validado: W_C, W_K, pmax, Y_I/K/C/E; B−A.
Porcentaje solo trabajos/presión: 100*(B−A)/abs(A), no definido con A=0.
No recalcular trabajo o máximo desde muestras. Gráficas con ejes comunes para
A sólida azul y B discontinua naranja; presión kPa absolutos y volumen cm³.
Ángulo alineado restando 360*(número de ciclo−1), conservando 180–540° y todos los
puntos en orden temporal, incluido P-V. Sin desplazar picos, suavizar ni inventar datos.

## CSV
UTF-8 sin BOM, coma, punto decimal, `csv.writer` con escape de comillas estándar.
Carpeta nueva exclusiva; errores eliminan únicamente archivos propios incompletos
si es posible, nunca anuncian éxito parcial ni modifican fuentes.
`resumen.csv`: magnitude, unit, run_id_A, run_id_B, value_A, value_B, difference_B_minus_A,
relative_difference_percent. Vacío para porcentaje no definido o no aplicable a Y.
`curvas.csv`: configuration, run_id, sample_index, angle_cycle_deg, angle_original_deg,
pressure_absolute_Pa, volume_m3. Formato largo, primero A luego B, puntos originales
sin redondear. No se persiste sesión de comparación ni modifica JSON v5.

## Comprobación y parada
Usar resultados existentes editor-20260915/A y B (ambos perfil B); C sirve únicamente
para probar rechazo de perfil distinto. Unit tests con esperados independientes,
fixtures identificados si se necesitan; ninguna ejecución nueva. Windows visible
al 150 % con captura y CSV reales, separado de aceptación manual. Una revisión
puntual; registro en README/tasks/hoja. Entrega 6 En curso, pendientes barridos e
importación experimental, sin desarrollar esos alcances ni iniciar entrega 7.


## Ampliación autorizada: punto y barrido RPM
La prohibición anterior de nuevos cálculos pertenece al primer tramo A/B.
Ahora solo RPM varía: entero 2500–3500, punto inicial 3000; inicio/final/paso
producen 2–5 puntos ascendentes, exactos, paso positivo, lista previa visible
(inicial 2500/3000/3500). Límites de producto, no certificado de dominio físico.
ProjectCase especializado parametriza rpm sin modificar SyntheticCase ni ecuaciones.
Model.rate=6*rpm gobierna dV/dt, energía/marcador temporal y dt; muestras usan
(angle-initial_angle)/(6*rpm). Aporte angular 350°/40° intacto, vuelta 60/rpm s.

Un QProcess existente ejecuta la serie secuencialmente. Una copia JSON independiente
incluye geometría/dirty/origen y lista; cada execute reconstruye modelo e inventarios
originales, sin warm-start. Fallo/no convergencia/cancelación detienen y conservan
prefijo/diagnóstico, restantes no ejecutados. 30 ciclos/60 s por punto, hasta 300 s
acumulados; presupuestos de memoria/RHS/pasos/rechazos/dominio intactos. Inicio,
escritura, integración y total de cada punto separados en el índice; total de
serie incluye validación/escrituras, tiempo percibido de interfaz incluye proceso.

### Contrato de resultados v3 y serie v1
V1 referencia y v2 proyecto mantienen lectura/reconstrucción fija 3000. V3 añade
operating_point={rpm:int} y escenario S2T-0D-reference-recipe-variable-rpm-v1;
reconstrucción estricta de todo el escenario, no parámetros arbitrarios del archivo.
Para puntos de serie, series_context={series_id:32 hex,point_index:0..4} forma parte
de entradas validadas. Mismos tres archivos con hashes/manifiesto y unidades;
coherencia tiempo/ángulo se valida con RPM efectivas. A/B admite contratos viejos
compatibles a 3000 e impide diferente RPM/perfil. JSON de proyectos v5 no cambia.

series.json (motorsim-rpm-sweep, version 1) guarda series_id, common_inputs, rpms,
points, state, reason, integration_seconds y wall_seconds; interfaz añade
interface_wall_seconds tras terminar. Cada punto guarda rpm/state/reason,
result (point-NN/manifest.json o null), run_id, manifest_sha256 y timings separados.
Carpeta exclusiva, índice actualizado atómicamente por punto y al terminar.
Lector exige prefijo secuencial, estado/identidad/hash/entradas comunes/posición
coincidentes y rutas internas exactas, incluyendo resolución de enlaces. Reabrir
no usa proyecto ni ejecuta. El aviso de configuración anterior conserva procedencia.

Tabla RPM/estado/ciclos/segundos/W_C/W_K/pmax, causa visible al seleccionar fila.
Magnitudes aceptadas vacías salvo convergencia. Consultar punto reutiliza vista
individual. Dos gráficos de puntos sin uniones/ajuste/extrapolación: W_C y pmax
frente RPM, sin potencia/par/óptimos. CSV serie.csv reutiliza escritor exclusivo;
columnas con unidades, ids, estados y motivos incluso no ejecutados. A/B intacto.

### Comprobación de este tramo
Tests focalizados de contrato/control con dobles explícitos, sin evidencia física
fabricada. Solo barrido GUI B 2500/3000/3500 geometría exacta de referencia 8:1;
3000 debe reproducir referencia. Si todos convergen/controlan, dos C extremos.
Contraste B/C con umbrales existentes (incluye Y y masas), sin afirmar tendencia.
Windows 150 % visible/captura separado de aceptación manual; una revisión puntual.
Entrega 6 En curso, importación experimental y entrega 7 fuera del alcance.


El manifiesto v3 producido por execute registra timings con setup_seconds,
writing_seconds (datos/hashes/manifiesto inicial), integration_seconds y wall_seconds
hasta ese registro. El cierre del registro de tiempos se incluye en el total de
serie y de interfaz. En puntos GUI, interface_wall_seconds se añade tras finalizar;
en consola el total corresponde al proceso numérico. Un diagnóstico construido
sin ejecutar puede carecer de tiempos; el lector no los inventa. El índice de
serie conserva los tiempos del punto; nunca modifica manifiestos hijos.
La interfaz exige destino inexistente y el identificador sweep_started confirmado
por el hijo antes de actualizar el índice: un fallo no puede apropiarse de otra serie.
