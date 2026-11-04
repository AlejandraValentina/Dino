# Workbench F0 navigation expectation alignment

Updated three obsolete expectations in the F0 workbench tests to match the accepted interface: the current component tab labels, the three-mode workspace stack, and the backend-derived port-schedule explanation in the summary tooltip. No product code changed.

## Verification

- Initial focused run reproduced two failures: old tab labels and a two-view stack. After aligning those, the same test surfaced the moved tooltip text expectation; the current tooltip contains the backend-derived area-transition explanation.
- Final integrated run: `python -m pytest tests/test_dino_workbench_f0.py tests/test_dino_desktop_ux_v2.py -q` — **26 passed in 96.82 s**.
- The behavioral assertions for engine values, transfer port areas, timing rows, execution state, and 980×680 layout remain unchanged.
