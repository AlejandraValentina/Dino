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
- [x] Fase 5a: `STATIC_REED_V1` y `DYNAMIC_REED_V1` multi-petal, respuesta,
      contactos, flujo y serialization/replay individual. `motorsim.reed`
      conserva mecánica desacoplada y reutiliza `simulation.restriction`; 16
      pruebas reed más 48 regresiones P6/scavenging/ports, y 64 tests focales
      de harness/evidencia, aprobados. Se corrigió contacto a tope al final de
      un paso con redondeo de una ULP. Sin conexión productiva a P5/P6.
- [ ] Fase 5b: integración del estado reed con el timestep/etapas de P5-C/P6,
      especies, ledgers y casos de operación del engine.
- [ ] Fase 6: sistema de cámara de expansión sobre ducts quasi-1D existentes.
- [x] Fase 6a: ensamblado geométrico conectado y trazas de solver en
      `motorsim.expansion_chamber`, reutilizando `gas1d.mesh.segments_mesh` y
      `gas1d.solver`. Once pruebas de geometría, esquema, estados inválidos,
      flujo, presión/temperatura/Mach, características, tiempos de llegada y
      mapeo de un estado producido por el solver aprobadas. Se marca parcial:
      pendiente el ciclo híbrido P5 integrado con admisión reed, especie P6 y
      auditoría de onda primaria; sin amplitudes reflejadas sintéticas.
- [ ] Fase 7: transferencia térmica configurable y ledger energético.
- [x] Fase 7a: superficies térmicas direccionables, pared prescrita o mapa
      RPM/carga acotado, correlación explícita `CONSTANT_H_V1`, esquema durable
      y ledger trapezoidal por ciclo en `motorsim.thermal`; nueve pruebas
      analíticas/negativas aprobadas. Parcial: no hay capacidad térmica dinámica
      de paredes ni acoplamiento a energía P5/P6 por etapa.
- [ ] Fase 8: `COMBUSTION_MODEL_V2`, separado de P7 prescrito histórico.
- [x] Fase 8a: single/double Wiebe, ignition, efficiency/map y CA10/50/90 en
      `motorsim.combustion`, con serialization y 11 pruebas. Parcial e
      intencionalmente sin química, conversión de especie ni energía liberada;
      esos balances quedan condicionados a los contratos de combustible y
      energía de fase 11 y a integración de solver.
- [ ] Fase 9: modelo de cárter V2 y acoplamiento de admisión/transferencia.
- [ ] Fase 10: pérdidas mecánicas y rendimiento al freno con provenance.
- [x] Fase 10a: términos FMEP explícitos por fuente, mapas RPM/carga,
      provenance y derivación analítica IMEP/BMEP, potencia y par 2T en
      `motorsim.mechanical`; cuatro pruebas analíticas/negativas. Parcial: no
      se inyectan pérdidas al solver ni hay mapas calibrados/documentados.
- [ ] Fase 11: combustible, AFR y BSFC consistentes con P6.
- [x] Fase 11a: propiedades de combustible explícitas con provenance y cálculo
      de AFR/equivalence, inventario entregado/atrapado/quemado/no quemado,
      short-circuit explícito desde ledger P6 (sin inferirlo de delivered menos
      trapped), energía potencial, fuel flow e ISFC/BSFC de 2T;
      nueve pruebas analíticas/negativas. Parcial: adaptador consume masas
      suministradas, no se acopla a la campaña P6 ni al ledger energético.
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
