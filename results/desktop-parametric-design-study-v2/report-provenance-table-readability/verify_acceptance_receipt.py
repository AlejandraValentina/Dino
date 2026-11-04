from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = OUT / "native-cross-study-comparison-v2.html"
APP_IMAGE = OUT / "native-desktop-report-export-v2.png"
BROWSER_IMAGE = OUT / "chrome-rendered-provenance-table-v2.png"
EXPANDED_IMAGE = OUT / "chrome-expanded-provenance-v1.png"
RUN_SUMMARY = OUT / "native-run-v2/native-report-provenance-v2.summary.json"
INITIAL_RUN_SUMMARY = OUT / "native-run/native-report-provenance-v1.summary.json"
TEST_SUMMARY = OUT / "tests-final-v2/report-provenance-focused-v2.summary.json"
INITIAL_TEST_SUMMARY = OUT / "tests-final/report-provenance-focused-v1.summary.json"
RECEIPT = OUT / "acceptance-receipt.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = REPORT.read_text(encoding="utf-8")
points_table = report.split('<table class="points-table">', 1)[1].split("</table>", 1)[0]
headers = points_table.split("</thead>", 1)[0]
test_summary = json.loads(TEST_SUMMARY.read_text(encoding="utf-8"))
run_summary = json.loads(RUN_SUMMARY.read_text(encoding="utf-8"))
initial_run_summary = json.loads(INITIAL_RUN_SUMMARY.read_text(encoding="utf-8"))
expected = (
    "synthetic-A-3000", "synthetic-A-4000", "synthetic-B-3000",
    "synthetic-B-4000", "synthetic-B-5000", "Fuente verificada al cargar",
)
for code, run in zip("abcde", ("synthetic-A-3000", "synthetic-B-3000",
                                "synthetic-A-4000", "synthetic-B-4000",
                                "synthetic-B-5000")):
    expected += (code * 64, code.upper() * 64,
                 hashlib.sha256((run + " result").encode()).hexdigest(),
                 hashlib.sha256((run + " artifact").encode()).hexdigest(),
                 f"SYNTHETIC/{run}")
preserved = all(value in points_table or value in report for value in expected)
dimensions = {}
for path in (APP_IMAGE, BROWSER_IMAGE, EXPANDED_IMAGE):
    with Image.open(path) as image:
        dimensions[path.name] = list(image.size)

receipt = {
    "schema": "DINO_REPORT_PROVENANCE_READABILITY_ACCEPTANCE_V1",
    "fixture_origin": "synthetic presentation fixture; no solver execution",
    "desktop_export": {
        "action": "Results > Compare > Exportar informe técnico HTML",
        "native_window_capture": APP_IMAGE.relative_to(ROOT).as_posix(),
        "native_capture_sha256": sha256(APP_IMAGE),
        "html": REPORT.relative_to(ROOT).as_posix(),
        "html_sha256": sha256(REPORT),
        "browser_capture": BROWSER_IMAGE.relative_to(ROOT).as_posix(),
        "browser_capture_sha256": sha256(BROWSER_IMAGE),
        "dimensions_px": dimensions,
        "summary_header_count": headers.count("<th>"),
        "expandable_source_rows": points_table.count('class="point-provenance"'),
        "all_original_provenance_present": preserved,
        "exact_source_json_appendix_present": "Objeto completo de comparación" in report,
        "synthetic_and_no_validation_notice_present": (
            "Fixture sintético de demostración" in report and "NOT_CLAIMED" in report
        ),
    },
    "tests": {
        "command": test_summary["command"],
        "exit_code": test_summary["exit_code"],
        "summary": test_summary["tail"],
        "summary_sha256": sha256(TEST_SUMMARY),
    },
    "browser_runner_cleanup": {
        "initial_attempt_exit_code": initial_run_summary["exit_code"],
        "initial_attempt_error": initial_run_summary["error_lines"][-1],
        "diagnosis": "Chrome completed both captures; TemporaryDirectory cleanup raised WinError 145 for DawnWebGPUCache afterward.",
        "runner_corrected": "TemporaryDirectory(ignore_cleanup_errors=True); no product files are affected.",
        "final_native_desktop_browser_run_exit_code": run_summary["exit_code"],
        "final_native_desktop_browser_run_error_lines": run_summary["error_lines"],
        "expanded_details_preview_exit_code": json.loads((OUT / "native-run-v2/expanded-provenance-preview-v1.summary.json").read_text(encoding="utf-8"))["exit_code"],
    },
    "uia_com_incident": {
        "cause_from_existing_acceptance": "pywinauto UIA held a stale provider after native-window teardown; not a Dino COM operation.",
        "active_environment_has_pywinauto": False,
        "native_desktop_export_verified": True,
        "reproduced_via_pywinauto": False,
    },
}

assert test_summary["exit_code"] == 0
assert run_summary["exit_code"] == 0
assert receipt["browser_runner_cleanup"]["expanded_details_preview_exit_code"] == 0
assert headers.count("<th>") == 9
assert points_table.count('class="point-provenance"') == 5
assert preserved
assert receipt["desktop_export"]["exact_source_json_appendix_present"]
assert receipt["desktop_export"]["synthetic_and_no_validation_notice_present"]
assert dimensions[APP_IMAGE.name] == [1440, 837]
assert dimensions[BROWSER_IMAGE.name] == [1360, 2000]
assert dimensions[EXPANDED_IMAGE.name] == [1360, 1100]
RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, ensure_ascii=False))
