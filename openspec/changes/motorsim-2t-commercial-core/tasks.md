# Programa MOTORSIM_2T_COMMERCIAL_CORE

Estado reconstruido en `9116eb0`. Las fases son una cola durable única; marcar
solo trabajo comprobado. Mantener P4–P9 y los recibos históricos intactos.

- [ ] Fase 1: harness reusable y evidencia multi-ciclo. Parcial: harness y
      contrato de periodicidad implementados; KT100 r5 falla antes del ciclo 1
      por rama de admisión reservoir sin solución. Ver cambio
      `reference-engine-hybrid-harness`; no declarar VERIFIED.
- [ ] Fase 2: KT100 V2, cinco puntos exploratorios y provenance. Parcial:
      fixture/configuración generados; 0/5 ciclos completos, sin periodicidad,
      checkpoint de campaña ni performance. Preservar r2–r5.
- [ ] Fase 3: geometría genérica 2T: transferencias múltiples, escape complejo,
      perfiles de área, piston-port y asociaciones con conductos.
- [x] Fase 3a: API/configuración separada `GENERIC_2T_PORTS_V1`; conserva los
      proyectos históricos, calcula áreas/eventos continuos, perfiles por
      apertura y agregados por conducto, serializa geometry + derived profiles
      con binding SHA-256. 17 pruebas focales y 54 pruebas de geometría,
      admisión, cinemática, proyectos y simulación aprobadas.
- [ ] Fase 3b: integración de esta configuración en un engine case ejecutable,
      topología variable con ledgers globales, schema de proyecto y GUI. El
      módulo 3a aún no altera áreas/flujos de P5 ni declara completa la fase.
- [ ] Fase 4: métricas de barrido con definiciones matemáticas y ledgers P6.
- [x] Fase 4a: funciones puras `MOTORSIM_2T_SCAVENGING_METRICS_V1`, masas,
      reference charge y nueve ratios con valores undefined explícitos para
      denominadores cero; cinco pruebas analíticas/negativas aprobadas.
- [ ] Fase 4b: extraer snapshots de cierre de transfers/escape desde evidencia
      primaria de ciclo, ligarlos a geometry events y agregar auditor offline.
- [x] Fase 4b1: adaptador de primary trajectory que exige snapshots únicos en
      ángulos de cierre resueltos, cierre terminal, ledger P6 cumulativo y
      summary concordante; no interpola. Tests de evento ausente, resumen stale
      y bool-as-number cubiertos.
- [ ] Fase 4c: verificar ledgers P6 durante operación periódica y exponer los
      outputs en el esquema de resultados, sin cambiar transporte.
- [ ] Fase 5: reed estática y/o dinámica, según alcance físico derivable.
- [ ] Fase 6: sistema de cámara de expansión sobre ducts quasi-1D existentes.
- [ ] Fase 7: transferencia térmica configurable y ledger energético.
- [ ] Fase 8: `COMBUSTION_MODEL_V2`, separado de P7 prescrito histórico.
- [ ] Fase 9: modelo de cárter V2 y acoplamiento de admisión/transferencia.
- [ ] Fase 10: pérdidas mecánicas y rendimiento al freno con provenance.
- [ ] Fase 11: combustible, AFR y BSFC consistentes con P6.
- [ ] Fase 12: geometría/actuación de powervalve.
- [ ] Fase 13: plenum, airbox, boost bottle y uniones.
- [ ] Fase 14: esquema unificado de outputs por ángulo y ciclo/RPM.
- [ ] Fase 15: importación exploratoria generalizada sin cambiar P9.
- [ ] Fase 16: segundo reference case con fuentes públicas y provenance.
- [ ] Gate final: integración arbitraria 2T, regresiones, auditoría y dos casos;
      declarar readiness solo con todos los requisitos del Commercial Core.

Para cada fase registrar contrato, código, pruebas unitarias/analíticas/negativas,
integración, restart/replay, conservación, regresiones, auditoría, revisión puntual,
OpenSpec estricto y commit. Las campañas con gates numéricos deben preregistrar
thresholds y horizonte antes de ejecutarse.
