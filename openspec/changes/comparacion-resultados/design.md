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
