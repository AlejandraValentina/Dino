# Tareas — KT100 Reference Case V1

- [x] Verificar baseline local/remoto, árbol previo limpio, hash P9 inicial y
      revisar fuentes de la variante sin mezclar KT100S/SE/SD/SEC.
- [x] Crear inventario de fuentes y manifest documental con estados de
      provenance para documentados, derivados, unknowns y supuestos sintéticos.
- [x] Implementar derivaciones geométricas independientes y validación del
      manifest, sin confundir datos del fixture con especificación Yamaha.
- [x] Generar `KT100_MODEL_FIXTURE_V1` determinístico para el modelo 0D
      existente; su alcance y límites quedan identificados en configuración.
- [x] Agregar pruebas de provenance, derivación, generación, completitud,
      ejecución geométrica y guardas de claims/P9.
- [x] Ejecutar pruebas focales y regresiones de adaptativo/proyecto/P9; validar
      OpenSpec en modo estricto.
- [x] Ejecutar la malla fija 5000/7000/9000/11000/13000 con profile B;
      preservar convergencia, no convergencia, balances y replay exacto.
- [x] Ejecutar sensibilidad preregistrada ±5 % en biela y escape; descriptiva,
      sin ajuste de parámetros.
- [ ] Verificar restart y gates de especie/entrega/short-circuit de la
      topología completa. El camino 0D no los soporta; el preflight híbrido
      previo terminó en estado inválido. No modificar física para forzar PASS.
- [x] Documentar fuentes, límites, resultados y claims permitidos.
- [x] Autorrevisión puntual y revisión independiente del provenance, alcance
      del modelo y artifacts; se corrigieron los desajustes de presiones y
      fracciones frescas antes de la aprobación final.
- [x] Registrar commit local sin push.
- [x] Confirmar el hash preregistrado de la especificación P9 y que no hay
      archivos versionados por LFS en este cambio.

Estado: `KT100_REFERENCE_CASE_V1_READY`; fixture ejecutable y determinista en
el camino 0D, pero no `KT100_MODEL_FIXTURE_V1_VERIFIED` por gates no soportados.
P9 permanece congelado; validación experimental `NOT_PERFORMED`.
