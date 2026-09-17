## P1 contractual
- [x] Leer orden, preservar cambios ajenos y registrar aceptación P0 separada.
- [x] Definir matemáticas, numérica, BC, interfaces y T01–T12; consultar fuentes.
- [x] Crear manifest y checks contractuales sin solver.
- [x] Revisar contrato independientemente y resolver defectos concretos.
- [ ] Ejecutar P1 mediante orquestador con dependencia aceptada y cero reparaciones.
- [ ] Validar OpenSpec y registrar evidencia/gate/commits sin P2 ni archivo.

T01–T12 permanecen especificados, no ejecutados. La eliminación previa de
redme.txt es ajena y se conserva. No hay campaña 0D ni solver 1D nuevo.

Revisión independiente de solo lectura: PASS contractual; se corrigió la fuente
MUSCL para preservar exactamente p_i ΔA también en área suave y se precisaron
referencias desde conservadas en todos los contactos. Se explicitó p* HLLC.
11 pruebas de contrato aprobaron; no son T01–T12 ni una campaña física.
El recibo de aceptación P0 y su copia derivada conservan datos científicos.
