# Reanudar estudio seleccionado desde Resultados

Estado: verificado en fuente con PySide6; no se ejecutó ningún solver ni se reanudó un estudio real.

## Cambio

- Resultados añade **Reanudar estudio…** junto al selector de estudios del proyecto.
- La acción sólo emite una referencia que coincide exactamente con una entrada registrada en el proyecto activo y navega a **Simular**.
- Ejecución revalida pertenencia al proyecto, SHA-256 y la identidad schema/estudio/proyecto antes de cargar el estudio preparado. Después reutiliza el preflight existente: proyecto, variante, baseline, ubicación durable, presupuesto y confirmación, además de las verificaciones de checkpoints/reutilización del runner.
- La selección por diálogo sigue disponible desde el menú de Simular.

## Pruebas

- `python -m pytest tests/test_desktop_design_study.py -q -k 'selected_project_study_routes_to_existing_resume_flow or resume_from_project_reference_rejects_changed_manifest_before_worker or resume_from_selected_project_study_reuses_existing_preflight'` — 3 passed. Fixtures sintéticos; el caso válido confirma la ruta y llamada al runner de reanudación con presupuesto adicional confirmado; el manifiesto alterado se rechaza antes de crear worker.
- `python -m pytest tests/test_desktop_design_study.py -q` — 35 passed.
- `python -m pytest tests/test_engineering_desktop_result.py tests/test_design_study.py -q` — 19 passed.
- `git diff --check` — limpio.

La primera prueba pulsa el botón Qt real en una ventana `DinoDesktopWindow` y verifica navegación y despacho del manifiesto seleccionado. Para evitar iniciar cálculos, el runner de integración se sustituye por un espía de test. No se hizo verificación visual de pantalla física: el dispositivo de escritorio conectado figura offline; no se reintentó automatización UIA/COM.

## Límites

Esto elimina la búsqueda manual del manifiesto desde Resultados; no cambia el protocolo de reanudación ni demuestra convergencia, periodicidad o validez predictiva. La reanudación efectiva continúa condicionada a los hashes, bindings, checkpoints y presupuesto que comprueba el preflight/runner existente.
