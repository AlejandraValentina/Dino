# Diseño

La referencia selecciona el KT100SP descrito en la publicación oficial Yamaha
de 1998 para el contexto doméstico japonés FP2. La fuente no fija año de serie
ni RPM de operación. Los datos no disponibles permanecen `UNKNOWN`; el fixture
los completa con supuestos sintéticos separados y justificados.

La ejecución usa exclusivamente el camino de aplicación existente: modelo 0D
de cuatro volúmenes y RK4 adaptativo perfil B, con regularización exterior fija
de 100 Pa ya utilizada por el producto. La convergencia disponible es el
contrato nativo de periodo 1 de la aplicación. No equivale al detector E13-R1
de sensores 1D y no detecta periodo 2. No se cambia solver, tolerancia, umbral,
ni configuración después de observar resultados.

El preflight previo de la topología híbrida completa P5-C/P6/P7 terminó con
estado de especie inválido. No se altera esa física en esta entrega. El modelo
0D no representa propagación de ondas en conductos, cuatro especies, entrega
separada de aire fresco, cortocircuito fresco ni restart. La campaña 0D es una
exploración útil y reproducible, pero no puede acreditar esos gates ni se
presenta como sustituto de la calificación E13.

Se ejecuta la malla exploratoria fija 5000/7000/9000/11000/13000 rpm, elegida
antes de inspeccionar resultados. No se encontró un régimen específico para
KT100SP, por lo que no se llama rango operativo Yamaha. Cada punto se repite
desde el mismo estado inicial para comprobar determinismo; esa repetición no es
restart. Una sensibilidad descriptiva, congelada antes de ejecutarse, perturba
±5 % longitud de biela y longitud de escape en el punto medio geométrico de la
malla. No hay calibración contra potencia externa.

P9 v1.0 y sus claims permanecen congelados e intactos.
