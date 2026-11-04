from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BEFORE = OUT / "before-v1.png"
AFTER = OUT / "chrome-report-v1.png"
DESKTOP = OUT / "desktop-export-v1.png"
REPORT = OUT / "cross-study-report-v1.html"
NATIVE = OUT / "export-receipt-v1.json"
RUN = OUT / "native-run/duplicate-state-native-v1.summary.json"
TESTS = OUT / "tests-final/duplicate-state-final-v1.summary.json"
RECEIPT = OUT / "acceptance-receipt.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


html = REPORT.read_text(encoding="utf-8")
summary = html.split('<table class="points-table">', 1)[1].split("</table>", 1)[0]
tests = json.loads(TESTS.read_text(encoding="utf-8"))
native = json.loads(NATIVE.read_text(encoding="utf-8"))
run = json.loads(RUN.read_text(encoding="utf-8"))
dimensions = {}
for path in (BEFORE, AFTER, DESKTOP):
    with Image.open(path) as image:
        dimensions[path.name] = list(image.size)

receipt = {
    "schema": "DINO_REPORT_DUPLICATE_STATE_SUMMARY_ACCEPTANCE_V1",
    "fixture_origin": "same synthetic comparison fixture before and after; no solver execution",
    "before_summary_repeat_count": 8,
    "after_summary_period_one_count": summary.count("Periódica · ciclo 1"),
    "after_has_no_adjacent_duplicate_label": "Periódica · ciclo 1<br>Periódica · ciclo 1" not in summary,
    "distinct_nonconverged_states_retained": "Límite de ciclos · no convergida<br>Ciclos insuficientes" in summary,
    "both_source_state_fields_retained_in_json": (
        '"classification": "PERIOD_1"' in html and '"periodicity": "PERIOD_1"' in html
    ),
    "evidence": {
        "before_sha256": digest(BEFORE),
        "after_sha256": digest(AFTER),
        "native_desktop_capture_sha256": digest(DESKTOP),
        "html_sha256": digest(REPORT),
        "dimensions_px": dimensions,
        "desktop_window_visible": native["desktop_window_visible"],
        "synthetic_notice": native["synthetic_notice_preserved"],
    },
    "tests": {
        "command": tests["command"],
        "exit_code": tests["exit_code"],
        "tail": tests["tail"],
        "summary_sha256": digest(TESTS),
    },
    "native_runner_exit_code": run["exit_code"],
}
assert receipt["before_summary_repeat_count"] == 8
assert receipt["after_summary_period_one_count"] == 4
assert receipt["after_has_no_adjacent_duplicate_label"]
assert receipt["distinct_nonconverged_states_retained"]
assert receipt["both_source_state_fields_retained_in_json"]
assert receipt["evidence"]["desktop_window_visible"]
assert receipt["evidence"]["synthetic_notice"]
assert receipt["tests"]["exit_code"] == 0
assert receipt["native_runner_exit_code"] == 0
assert dimensions[BEFORE.name] == [1360, 3000]
assert dimensions[AFTER.name] == [1360, 3000]
assert dimensions[DESKTOP.name] == [1440, 837]
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
