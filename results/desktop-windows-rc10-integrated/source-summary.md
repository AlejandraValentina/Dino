# rc10 — consolidación previa al único candidato Windows

Fecha: 2026-11-03. Alcance autorizado: cerrar MODELO y aceptar un candidato Windows integrado. rc7/rc9 y datos históricos protegidos.

Cambios de producto desde rc9: CSV histórico reutilizable, tres modos y explorador, resultados centrados en curvas, secciones de MODELO, diagramas/eventos e inversión restringida de apertura. Esta entrega separa admisión y transferencias con la misma tabla (sin doble edición ni pérdida de borradores) y deja guardado de escape fuera de las vistas desplazables. Perfil/cotas A/B, tabla y avanzado conservan los controles existentes. Corrige también la tabla de estaciones que quedaba oculta al abrir el grupo avanzado.

No se cambia schema de proyecto, solver, tolerancias ni valores predeterminados experimentales. Los cambios numéricos ya aceptados desde rc9 (candidato Brent opt-in) permanecen tal como están comprometidos; no se promueven.

Preflight: dependencias fijadas PASS (`dependencies.txt`); almacenamiento PASS, estimación 1,5 GiB de distribución + 1,2 GiB de temporales/copia de fuente y reserva 2 GiB (`storage-preflight.json`). Sin limpieza de históricos.

Pruebas: `source-tests/rc10-source-integration.summary.json`, **66 PASS, 1 SKIP**, 282,96 s. Suites: Desktop, MODELO, integración rc10, distribución/freeze_support, portabilidad/persistencia, RPM y resultados de ingeniería. El omitido requiere la raíz histórica externa en el entorno aislado. `final-focused-tests.txt`: **2 PASS**, incluida visibilidad de estaciones avanzadas.

Se verificó en GUI de fuente el escape a 980×680 con acciones visibles y admisión con un solo conducto. La aceptación restante se realiza sobre el programa empaquetado. Un solo build autorizado; si falla, no se genera otro candidato.

Construcción prevista desde worktree limpio del commit de implementación y entorno .venv-build existente, con destino y temporales externos. Esto excluye cambios locales ajenos. No hay push, publicación ni promoción estable.
