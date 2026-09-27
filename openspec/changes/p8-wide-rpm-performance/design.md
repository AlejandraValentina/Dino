# Diseño

P8 debe reutilizar la configuración y las fórmulas 2T autorizadas existentes:
slider-crank, volúmenes y áreas efectivas de puertos. La integración avanza en
tiempo físico con `omega_deg_s = 6 * rpm`, `t_cycle = 60 / rpm`, CFL de la
topología completa y cortes exactos en eventos/puertos. La ventana mide
exactamente un evento P7 autorizado; debe registrarse el intervalo real usado.

Cada RPM inicia desde un estado determinista documentado. Se registra
`steady_state=false`, `periodic_convergence=NOT_GRANTED_BY_P4`,
`metric_semantics=BOUNDED_TRANSIENT_INDICATED` y `conditional_on_p4=true`.
El trabajo de cilindro es la integral autorizada `W_cycle = integral(p dV)`;
las fórmulas son `P=W*rpm/60` y `T=W/(2*pi)`. Antes de la campaña se prueba
el signo en una cámara cerrada analítica.

No se cambian leyes físicas, tolerancias, P4, ni se agregan ciclos periódicos.
Si no existe una configuración/mecánica 2T autorizada completa, el resultado
es `P8_SCIENTIFIC_CONTRACT_REQUIRED` y no se inventan parámetros.

