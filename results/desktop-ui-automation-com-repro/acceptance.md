# UI Automation COM lifecycle reproduction

## Result

The historical failure is a UIA harness lifecycle defect, not a Dino application COM operation. The prior accepted record says the automation completed its work, closed the native Qt window, and then queried the retained pywinauto UIA wrapper for visibility. That query targeted a provider whose native window had already been destroyed. Dino Desktop does not use COM for report export or its solver/UI path.

The original incident receipt does not include an HRESULT or exception string, so that exact value cannot be recovered from the saved evidence.

## Focused reproduction

- Installed `pywinauto 0.6.9`, `comtypes 1.4.16`, and `pywin32 312` in an isolated temporary target; no repository dependency or build environment changed.
- Repeated under both Python 3.11.0 and the registered packaging interpreter Python 3.10.7; a bounded Python 3.10.7 reproduction is recorded in `bounded-uia-receipt.json`.
- In both attempts, a real Dino Qt window reached the ready marker. The first pywinauto UIA visibility wait then stopped returning, before close and before the historical post-close call. It produced no HRESULT. The calls were interrupted after a bounded wait; no Python window or child process remained.
- A separate Win32-only run used the same Qt window: exactly one matching visible window was present; `WM_CLOSE` closed it; `IsWindowVisible` returned false; the process exited with code 0 and no worker remained.

## Classification

No Dino product change is justified. The historical post-close failure is caused by retaining and querying a UIA wrapper after its provider is destroyed. The current session additionally reproduces a UIA bridge hang on the initial visibility query, including under Python 3.10; that blocks reproducing the same post-close exception here. The practical harness correction remains: close by Win32 and verify closure using Win32 window/process state; do not make further COM calls through a retained UIA element after native teardown.

Evidence: `reproduction-receipt.json`, `uia-progress.jsonl`, `bounded-uia-receipt.json`, `bounded-uia-progress.jsonl`, `win32-lifecycle-receipt.json`, `verify_uia_com_bounded.py`, and `verify_win32_lifecycle.py`. No solver, scientific result, Desktop product code, or packaging baseline was changed.
