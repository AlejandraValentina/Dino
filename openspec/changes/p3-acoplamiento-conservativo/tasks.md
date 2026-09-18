## P3 — registro de ejecución
- [x] Registrar aceptación humanaP2 y congelar hashes del núcleo/contratos.
- [x] Leer contrato de interfazP1 y definir energía/signos.
- [x] Implementar interfaz aislada y reproducir preflight con dev_orchestrator.
- [ ] P3A reservoir/tubo completo PASS.
- [ ] P3B volumen constante, C01–C07/C09–C12 PASS.
- [ ] P3C volumen variable C08 PASS.
- [ ] Adaptador mínimo a estados0D existentes, sólo tras gates sintéticos.
- [x] RegresionesP0/P2, OpenSpec y revisión independiente del preflight bloqueado (no acredita integración completa).
- [ ] P3_PASS_0D_1D_COUPLING_VERIFIED; aceptación humana posterior, sinP4.


## Resultado — P3_BLOCKED_BACKFLOW / SCIENTIFIC_CHANGE_REQUIRED

42 evaluaciones de la frontera reservoir congelada, ambas orientaciones.
A p_pipe=p0=100kPa,T0=300K, T_pipe301K y velocidad normal−1e−9m/s:
No consistent reservoir inflow branch. A299K el flujo tiende a−0.037563294kg/s
para área.01m², pero en reposo es0. Límite analítico demuestra salto/ausencia de raíz;
no es ruido de integración. Ver results/p3-coupling-20260918/analysis.md.

Implementado solo estado m/U/F/V y flujo Euler único con incrementos opuestos;
energía entalpía total, donor según signo e impulso separado. No integrador
acoplado ni conexión productiva. No cambiar BC/P1 para pasar sin decisión científica.
C04 BLOCKED; C01–C03/C05–C12 NOT_RUN como gates dinámicos. Pruebas puntuales
de equilibrio/energía/especie no sustituyen C01–C12. P3A no acreditado, P3B/P3C
no iniciados, volumen variable y adaptador pendientes. P4 no iniciado.

74 pruebas PASS en23.983s; P2 T01–T12/58finales y FIRST_ORDER/R4 offline PASS;
siete regresiones P0 offline PASS. Núcleo/contratos congelados exactos.
Preflight+regresiones11.750s, cero integraciones nuevas. No campaña >300s.
AceptaciónP2 registrada en3a19e41; no aceptaciónP3. Sin push ni archivo.
El borrado ajeno redme.txt permanece intacto.

Revisión independiente /root/p3_review confirma STOP,27hashes y42evaluaciones;
6sinrama. Ningún hallazgo adicional en interfaz preparatoria. Dictamen en
results/p3-coupling-20260918/independent-review.json. Autorrevisión separada
de alcance/documentos/hashes. OpenSpec estricto P3 y P2 PASS.

## P3-R1 — orden38a85593
- [ ] C00/C00B, curvas, forward/reverse, energía/especie y revisión independiente.
- [ ] P3B C01–C07 tras R1 PASS.
- [ ] P3C C08–C12 tras P3B PASS.
- [ ] Adaptador0D y cierre sólo tras todos los gates.
