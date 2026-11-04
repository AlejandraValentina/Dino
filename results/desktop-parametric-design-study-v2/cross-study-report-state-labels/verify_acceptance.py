from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = OUT / "cross-study-comparison-synthetic-v1.html"
DESKTOP_IMAGE = OUT / "desktop-export-v1.png"
BROWSER_IMAGE = OUT / "chrome-report-v1.png"
TESTS = OUT / "tests-final/report-state-labels-final-v1.summary.json"
RECEIPT = OUT / "acceptance-receipt.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


html = REPORT.read_text(encoding="utf-8")
exclusion_start = html.index('<h4>Pares excluidos de esta gráfica · Potencia de freno</h4>')
exclusion_table = html[exclusion_start:html.index("</table>", exclusion_start)]
tests = json.loads(TESTS.read_text(encoding="utf-8"))
dimensions = {}
for path in (DESKTOP_IMAGE, BROWSER_IMAGE):
    with Image.open(path) as image:
        dimensions[path.name] = list(image.size)

receipt = {
    "schema": "DINO_CROSS_STUDY_REPORT_STATE_LABELS_ACCEPTANCE_V1",
    "fixture_origin": "synthetic presentation fixture; no solver or scientific campaign",
    "visible_exclusion_statuses_translated": (
        "Periódica · ciclo 1 / Periódica · ciclo 1" in exclusion_table
        and "Límite de ciclos · no convergida / Ciclos insuficientes" in exclusion_table
        and "MAX_CYCLES_NONCONVERGED / INSUFFICIENT_CYCLES" not in exclusion_table
    ),
    "raw_source_state_codes_retained_in_full_report_json": (
        '"classification": "MAX_CYCLES_NONCONVERGED"' in html
        and '"periodicity": "INSUFFICIENT_CYCLES"' in html
    ),
    "desktop_native_export": {
        "html_path": REPORT.relative_to(ROOT).as_posix(),
        "html_sha256": digest(REPORT),
        "desktop_capture_path": DESKTOP_IMAGE.relative_to(ROOT).as_posix(),
        "desktop_capture_sha256": digest(DESKTOP_IMAGE),
        "browser_capture_path": BROWSER_IMAGE.relative_to(ROOT).as_posix(),
        "browser_capture_sha256": digest(BROWSER_IMAGE),
        "capture_dimensions_px": dimensions,
        "desktop_window_visible": True,
        "synthetic_notice_and_not_claimed": "Fixture sintético de demostración" in html and "NOT_CLAIMED" in html,
    },
    "tests": {
        "command": tests["command"],
        "exit_code": tests["exit_code"],
        "tail": tests["tail"],
        "summary_sha256": digest(TESTS),
    },
}
assert receipt["visible_exclusion_statuses_translated"]
assert receipt["raw_source_state_codes_retained_in_full_report_json"]
assert receipt["desktop_native_export"]["synthetic_notice_and_not_claimed"]
assert receipt["tests"]["exit_code"] == 0
assert dimensions[DESKTOP_IMAGE.name] == [1440, 837]
assert dimensions[BROWSER_IMAGE.name] == [1360, 2000]
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
