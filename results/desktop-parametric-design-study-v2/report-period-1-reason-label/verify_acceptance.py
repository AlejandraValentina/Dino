from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = OUT / "cross-study-report-v2.html"
DESKTOP = OUT / "desktop-export-v2.png"
BROWSER = OUT / "chrome-report-v2.png"
NATIVE = OUT / "export-receipt-v2.json"
RUN = OUT / "native-run/period-reason-desktop-v2.summary.json"
TESTS = OUT / "tests-final/period-reason-final-v1.summary.json"
RECEIPT = OUT / "acceptance-receipt.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


html = REPORT.read_text(encoding="utf-8")
exclusions = html.split("Pares excluidos de esta gráfica · Potencia de freno", 1)[1].split("<h2>Contrastes exactos</h2>", 1)[0]
tests = json.loads(TESTS.read_text(encoding="utf-8"))
native = json.loads(NATIVE.read_text(encoding="utf-8"))
run = json.loads(RUN.read_text(encoding="utf-8"))
dimensions = {}
for path in (DESKTOP, BROWSER):
    with Image.open(path) as image:
        dimensions[path.name] = list(image.size)

receipt = {
    "schema": "DINO_REPORT_PERIOD_1_REASON_LABEL_ACCEPTANCE_V1",
    "fixture_origin": "synthetic presentation fixture; no solver execution",
    "eligible_rule_unchanged": "charts still only render exact-context pairs with PERIOD_1 finite defined metrics",
    "display_reasons_translated": (
        "Uno o ambos extremos no tienen periodicidad observada de orden 1." in exclusions
        and "La métrica no está definida y finita en ambos resultados periódicos de orden 1." in exclusions
        and "no están clasificados PERIOD_1" not in exclusions
    ),
    "raw_periodicity_codes_preserved_in_source_json": (
        '"classification": "PERIOD_1"' in html
        and '"periodicity": "PERIOD_1"' in html
        and '"periodicity": "INSUFFICIENT_CYCLES"' in html
    ),
    "evidence": {
        "html_path": REPORT.relative_to(ROOT).as_posix(),
        "html_sha256": digest(REPORT),
        "desktop_capture_path": DESKTOP.relative_to(ROOT).as_posix(),
        "desktop_capture_sha256": digest(DESKTOP),
        "browser_capture_path": BROWSER.relative_to(ROOT).as_posix(),
        "browser_capture_sha256": digest(BROWSER),
        "capture_dimensions_px": dimensions,
        "desktop_window_visible": native["desktop_window_visible"],
        "synthetic_notice": native["synthetic_notice_preserved"],
        "native_runner_exit_code": run["exit_code"],
    },
    "tests": {
        "command": tests["command"],
        "exit_code": tests["exit_code"],
        "tail": tests["tail"],
        "summary_sha256": digest(TESTS),
    },
}
assert receipt["display_reasons_translated"]
assert receipt["raw_periodicity_codes_preserved_in_source_json"]
assert receipt["evidence"]["desktop_window_visible"]
assert receipt["evidence"]["synthetic_notice"]
assert receipt["evidence"]["native_runner_exit_code"] == 0
assert receipt["tests"]["exit_code"] == 0
assert dimensions[DESKTOP.name] == [1440, 837]
assert dimensions[BROWSER.name] == [1360, 3000]
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
