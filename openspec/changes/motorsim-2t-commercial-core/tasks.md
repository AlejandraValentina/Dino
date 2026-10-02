# Programa MOTORSIM_2T_COMMERCIAL_CORE

Estado reconstruido desde `401d8d7`. Las fases son una cola durable única; marcar
solo trabajo comprobado. Mantener P4–P9 y los recibos históricos intactos.

- [ ] Fase 1: harness reusable y evidencia multi-ciclo. Parcial: harness y
      contrato de periodicidad implementados; KT100 r5 falla antes del ciclo 1
      por rama de admisión reservoir sin solución. Se validan self-fixtures,
      period-1/2, auditoría y restart de paso aceptado; el multi-ciclo de un
      motor no queda verificado. No declarar VERIFIED.
- [ ] Fase 2: KT100 V2, cinco puntos exploratorios y provenance. Parcial:
      fixture/configuración generados; 0/5 ciclos completos, sin periodicidad,
      checkpoint de campaña ni performance. Preservar r2–r5. Estado congelado:
      `KT100_HYBRID_V2_BLOCKED_BY_RESERVOIR_BOUNDARY_CAPABILITY`; no más runs,
      retries, ajustes ni sensitivities en esta misión.
- [ ] Fase 3: geometría genérica 2T: transferencias múltiples, escape complejo,
      perfiles de área, piston-port y asociaciones con conductos.
- [x] Fase 3a: API/configuración separada `GENERIC_2T_PORTS_V1`; conserva los
      proyectos históricos, calcula áreas/eventos continuos, perfiles por
      apertura y agregados por conducto, serializa geometry + derived profiles
      con binding SHA-256. 17 pruebas focales y 54 pruebas de geometría,
      admisión, cinemática, proyectos y simulación aprobadas.
- [ ] Fase 3b: integración de esta configuración en un engine case ejecutable,
      topología variable con ledgers globales, schema de proyecto y GUI. El
      adaptador opt-in `motorsim.two_stroke_ports_p5c` ahora resuelve y suma
      aperturas genéricas como áreas de entrada a las interfaces existentes de
      P5-C, sin editar P5; admite varias ventanas por cada una de las dos rutas
      transfer existentes. No descarta silenciosamente una tercera ruta: la
      rechaza. Tres pruebas nuevas verifican RHS geométrico, rechazo de ruta
      extra y datos inválidos; junto con 8 pruebas genéricas, 11 pasaron. Sigue
      parcial: la física histórica P5-C admite solo dos rutas, no hay topología
      variable/full-core, schema persistente ni GUI.
- [ ] Fase 4: métricas de barrido con definiciones matemáticas y ledgers P6.
- [x] Fase 4a: funciones puras `MOTORSIM_2T_SCAVENGING_METRICS_V1`, masas,
      reference charge y nueve ratios con valores undefined explícitos para
      denominadores cero; cinco pruebas analíticas/negativas aprobadas.
- [x] Fase 4b: extraer snapshots de cierre de transfers/escape desde evidencia
      primaria de ciclo, ligarlos a cierres exactos de geometría, exigir span
      completo 360°, ledgers P6 concordantes y agregar auditor offline. Fixtures
      geométricos/primarios y regresiones focales pasan.
- [x] Fase 4b1: adaptador de primary trajectory que exige snapshots únicos en
      ángulos de cierre resueltos, cierre terminal, ledger P6 cumulativo y
      summary concordante; no interpola. Tests de evento ausente, resumen stale
      y bool-as-number cubiertos.
- [ ] Fase 4c: verificar ledgers P6 durante operación periódica y exponer los
      outputs en el esquema de resultados, sin cambiar transporte. La serie
      contigua de primary cycles y el mapeo a outputs ya existen y se prueban
      con fixtures; la verificación de un resultado periódico de campaña queda
      pendiente hasta disponer de ciclos híbridos completos (KT100 no aporta
      ciclos y sus recibos permanecen congelados).
- [ ] Fase 5: reed estática y/o dinámica, según alcance físico derivable.
- [x] Fase 5a: `STATIC_REED_V1` y `DYNAMIC_REED_V1` multi-petal, respuesta,
      contactos, flujo y serialization/replay individual. `motorsim.reed`
      conserva mecánica desacoplada y reutiliza `simulation.restriction`; 16
      pruebas reed más 48 regresiones P6/scavenging/ports, y 64 tests focales
      de harness/evidencia, aprobados. Se corrigió contacto a tope al final de
      un paso con redondeo de una ULP. Sin conexión productiva a P5/P6.
- [ ] Fase 5b: integración del estado reed con el timestep/etapas de P5-C/P6,
      especies, ledgers y casos de operación del engine. Bloqueada localmente:
      P5-C histórico no expone estado de etapa al callback geométrico ni un
      hook SSPRK2 para integrar mecánica reed. Requiere integrador separado.
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
- [x] Fase 9a: volumen de cárter V2 con cinemática/biela existente, dV/dt
      analítico y compresión geométrica, más link 0D bidireccional que reutiliza
      `simulation.restriction`; ocho pruebas analíticas/negativas. Parcial:
      no se integró admisión/transferencia al RHS ni a ledgers P5-C/P6.
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
- [x] Fase 12a: mapa RPM→posición lineal y aplicación geométrica al techo del
      escape principal móvil en `motorsim.powervalve`, reutilizando área/eventos
      de `GENERIC_2T_PORTS_V1`; siete pruebas analíticas/negativas aprobadas.
      Parcial: no hay servo, integración al ciclo del solver ni calibración.
- [ ] Fase 13: plenum, airbox, boost bottle y uniones.
- [x] Fase 13a: schema de volúmenes/conexiones, atmosphere P6, intercambio
      conservativo 0D/1D con Riemann P3 + donor real P6 y estimación Helmholtz
      con longitud efectiva explícita; ocho pruebas. Parcial: topology todavía
      no entra al estado SSPRK2/productivo P5-C ni a ledger global de campaña.
- [ ] Fase 14: esquema unificado de outputs por ángulo y ciclo/RPM.
- [x] Fase 14a: `MOTORSIM_ENGINEERING_OUTPUTS_V1` con unidades, source,
      dependency status, trazas/metrics opcionales, estados undefined y controles
      de no-claim; diez tests incluyendo esquema inválido. Parcial: outputs aún
      no recolectados de un ciclo full-core arbitrario ni ligados a evidence.
- [ ] Fase 15: importación exploratoria generalizada sin cambiar P9.
- [x] Fase 15a: importador separado de presión/dyno con units, incertidumbre,
      provenance, raw+SHA256 y overlay exacto con métricas descriptivas;
      15 pruebas focales. Siempre EXPLORATORY_COMPARISON, nunca P9 elegible.
      Importador + parser/persistence heredados + calificación P9: 56 PASS;
      OpenSpec estricto PASS. Hash congelado P9 reconfirmado:
      `79fbe9b88d26fc4af5083d65d468f59c9208535f0ab389d2f3cb9a7654b88a4d`.
      En un intento de incluir la ventana GUI heredada de `external_data`, Qt
      terminó con access violation en `ExternalWindowTests.test_import_confirm_`
      `roundtrip_unknown_conditions_and_previous_preserved`; parser/persistencia
      se validaron por separado. P9 no se editó ni ejecutó.
- [x] Fase 16a: registrar `HONDA_CR250R_2007_REFERENCE_CASE_PARTIAL_V1` desde
      la ficha oficial Honda, con parámetros publicados como DOCUMENTED y los
      que faltan como null/UNKNOWN; prueba offline de provenance aprobada.
      Queda marcado `NOT_SIMULATION_READY`: la fuente no define biela, cárter,
      timing/geometría de lumbreras, conductos ni estados de frontera. No se
      inventaron especificaciones ni se ejecutó otro motor.
- [ ] Gate final: integración arbitraria 2T, regresiones, auditoría y dos casos;
      declarar readiness solo con todos los requisitos del Commercial Core.

- [ ] Integración end-to-end autorizada (continuación 2026-10-02):
      conservar P4–P9 y convertir los módulos existentes en un único motor.
      La etiqueta `CONDITIONAL_ON_P4` sigue obligatoria para la evidencia nueva.
- [ ] 17a. Integrador gas/especies con stage SSPRK2 común y transferencias N:
      iniciado en `motorsim.integrated_2t`. Reutiliza EOS/HLLC/P3 y donor P6;
      fixture de malla estática con tres transfers prueba conservación local,
      backflow/donor, geometría de celda en CFL, vaciado bruto de cámara 0D,
      flujo con entrada y salida simultáneas, calor prescrito, restart atómico
      y JSON replay. **Parcial**, 13 pruebas focales
      pasan; no incluye combustión ni ciclos de motor. Revisión independiente
      confirma la cota de CFL y originó el gate de coherencia geométrica del
      restart.
- [ ] 17b. Reed/intake/crankcase integrado por etapas, retroflujo, especie y
      ledger global; checkpoint/replay de estado mecánico reed. Parcial: el
      modelo estático existente limita el área de admisión por presión en cada
      stage común y el flujo conserva donor/ledger P6. La dinámica multi-petal
      y su estado de restart siguen pendientes.
- [ ] 17c. Topología generic ports N con piston intake, transfers y exhaust
      expansion-chamber en los mismos stages; scavenging ledger con cierres
      geométricos y flujos con signo.
- [ ] 17d. Combustión P7 autorizada, paredes térmicas, combustible/especies y
      trabajo mecánico integrados con ledger único sin doble conteo.
- [ ] 17e. Periodicidad P1/P2, evidencia primaria, collector engineering,
      checkpoint/restart/replay continuo y fixtures integrados completos.
- [ ] 18. Segundo fixture integrado independiente; validar y correr regresiones
      amplias P4–P8 antes de evaluar el gate Commercial Core.

## Cola autónoma

- `DONE` — Fundación común acotada: estado conservativo gas/especies N-route,
  SSPRK2, ledgers, CFL de ducto/cámara y restart geométricamente consistente;
  revisión read-only puntual completada. Esto no es un ciclo.
- `IN_PROGRESS` — Integración estática reed/intake/crankcase en el stage común;
  faltan dinámica reed, configuración de cárter acoplada y verificación de
  retroflujo con reed dinámica.
- `READY` — Integración de exhaust + expansion chamber y frontera externa.
- `READY` — Bind P7, fuel/P6 y work/brake en ledger por ciclo sin doble conteo.
- `READY` — Evidencia primaria, periodicidad, collector y Fixture A completo.
- `READY` — Fixture B y suite amplia actual P4–P8.
- `BLOCKED_LOCAL` — KT100 V2: boundary reservoir sin resolver; no reintentar
  hasta completar ambos fixtures internos y cumplir la condición de la orden.

Comprobación agrupada del avance autónomo: el 2026-10-02 se ejecutaron 204
pruebas focales de provenance, puertos/P5-C, scavenging, reed, cámara, thermal,
combustion, cárter, mecánica, fuel, powervalve, network, engineering outputs,
importador, harness, P5-B/P5-C y P6; todas pasaron. Esta suite no incluye KT100
ni campañas físicas. Los regresos P4–P8 se acreditan separadamente; los
fixtures unitarios no equivalen a verificación completa de engine.

## Deuda de integración no global

- El P5-C histórico tiene dos conductos transfer fijos y el callback geométrico
  no expone un estado SSPRK2 de etapa a un componente externo. Se dejó intacto.
  `two_stroke_ports_p5c` puede enlazar aperturas a esas dos rutas, pero tercera
  ruta, reed dinámica y volúmenes externos en las mismas etapas requieren una
  extensión integrada nueva y separada.
- El P6 expone ledgers de fresh delivered y short-circuit agregados, pero el
  primary evidence congelado no contiene un acumulador durable de delivered
  fresh_air/fuel por especie. Fuel accounting acepta ledgers de cuatro
  especies explícitos; no se derivan AFR/BSFC desde el contador escalar.
- La fase 1/2 queda localmente bloqueada por la capability de frontera ya
  registrada en `docs/gasdynamic/generalized_reservoir_boundary_v2_debt.md`.
  Las funciones independientes continúan; no repetir ni ajustar KT100.
- El segundo caso Honda solo aporta procedencia documental parcial y no puede
  alimentar una corrida sin reemplazar UNKNOWN por supuestos.

Para cada fase registrar contrato, código, pruebas unitarias/analíticas/negativas,
integración, restart/replay, conservación, regresiones, auditoría, revisión puntual,
OpenSpec estricto y commit. Las campañas con gates numéricos deben preregistrar
thresholds y horizonte antes de ejecutarse.
