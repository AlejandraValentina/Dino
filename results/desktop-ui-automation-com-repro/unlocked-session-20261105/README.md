# Repro UIA/COM en sesión desbloqueada

La sesión Windows local estaba desbloqueada durante esta prueba. Se utilizó un
Desktop sintético y se instalaron `pywinauto 0.6.9`, `comtypes 1.4.16` y
`pywin32 312` únicamente en un directorio temporal fuera del repositorio.

## Resultado acotado

- El proceso hijo mostró una ventana Qt visible; Win32 enumeró exactamente una.
- `pywinauto` UIA no completó su primera espera/consulta visible dentro de 12 s.
  No se obtuvo un objeto UIA ni un HRESULT, así que esta ejecución no llegó al
  acceso a un proveedor después de cerrar la ventana.
- El harness cerró la ventana con `WM_CLOSE`; `IsWindowVisible` confirmó su
  cierre y el proceso hijo terminó con código 0. No quedó un proceso de Dino ni
  del verificador.

La prueba local abierta no reproduce una operación COM de Dino ni contradice
la secuencia histórica del wrapper obsoleto tras cerrar la ventana. Reproduce
un bloqueo anterior: el puente UIA no alcanza la primera consulta en esta
sesión. El diagnóstico histórico sigue siendo del ciclo de vida del harness;
no se justifica un cambio en el producto.

## Evidencia

- Verificador: `verify_uia_com_bounded_unlocked.py` (derivado sin modificar el
  verificador histórico; escribe en este directorio y lee el Desktop sintético
  ya conservado).
- Progreso: `bounded-uia-progress.jsonl`.
- Resultado: `bounded-uia-receipt.json`.
- SHA-256 verificador: `ee964756c815db5d130129e6451a119ee8baec55df089e8fda4e924835e68a83`.
- SHA-256 progreso: `524382279881cf8cc949ae9186a3cacddd7d507d2f6ecd69769e1283a482cea1`.
- SHA-256 receipt: `587ede876fdbb8d9c5e6670f6b21bbbfbde0000bf50df13ee51a29246442885e`.
