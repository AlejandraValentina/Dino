from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = OUT / "native-pairing-context-v1.html"
DESKTOP_IMAGE = OUT / "native-desktop-export-v1.png"
BROWSER_IMAGE = OUT / "chrome-pairing-context-v1.png"
NATIVE_RECEIPT = OUT / "native-pairing-context-receipt.json"
TESTS = OUT / "tests-final-pairing-context/pairing-context-labels-final-v1.summary.json"
RUN = OUT / "native-run/pairing-context-native-v1.summary.json"
RECEIPT = OUT / "pairing-context-acceptance-receipt.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = REPORT.read_text(encoding="utf-8")
contrasts = report.split("<h2>Contrastes exactos</h2>", 1)[1].split("</table>", 1)[0]
unpaired = report.split("<h2>Puntos sin contraparte</h2>", 1)[1].split("</table>", 1)[0]
tests = json.loads(TESTS.read_text(encoding="utf-8"))
native = json.loads(NATIVE_RECEIPT.read_text(encoding="utf-8"))
run = json.loads(RUN.read_text(encoding="utf-8"))
dimensions = {}
for path in (DESKTOP_IMAGE, BROWSER_IMAGE):
    with Image.open(path) as image:
        dimensions[path.name] = list(image.size)

receipt = {
    "schema": "DINO_REPORT_PAIRING_CONTEXT_LABELS_ACCEPTANCE_V1",
    "fixture_origin": "synthetic presentation fixture; no solver execution",
    "pair_rule_label_translated": (
        "RPM exacta y contexto operativo coincidente" in contrasts
        and "EXACT_RPM_AND_OPERATING_CONTEXT" not in contrasts
    ),
    "context_reason_field_translated": (
        "Condiciones informadas incompatibles: cantidad de celdas de volumen finito." in unpaired
        and "total_finite_volume_cells" not in unpaired
    ),
    "exact_internal_values_preserved_in_report_json": (
        '"pairing": "EXACT_RPM_AND_OPERATING_CONTEXT"' in report
        and '"reason": "Condiciones informadas incompatibles: total_finite_volume_cells."' in report
    ),
    "native_export": {
        "html_path": REPORT.relative_to(ROOT).as_posix(),
        "html_sha256": digest(REPORT),
        "desktop_capture_path": DESKTOP_IMAGE.relative_to(ROOT).as_posix(),
        "desktop_capture_sha256": digest(DESKTOP_IMAGE),
        "browser_capture_path": BROWSER_IMAGE.relative_to(ROOT).as_posix(),
        "browser_capture_sha256": digest(BROWSER_IMAGE),
        "capture_dimensions_px": dimensions,
        "source_fixture_notice": native["synthetic_notice_preserved"],
        "no_interpolated_lines": native["no_interpolated_lines"],
        "desktop_window_visible": native["desktop_window_visible"],
        "native_runner_exit_code": run["exit_code"],
    },
    "tests": {
        "command": tests["command"],
        "exit_code": tests["exit_code"],
        "tail": tests["tail"],
        "summary_sha256": digest(TESTS),
    },
}
assert receipt["pair_rule_label_translated"]
assert receipt["context_reason_field_translated"]
assert receipt["exact_internal_values_preserved_in_report_json"]
assert receipt["native_export"]["source_fixture_notice"]
assert receipt["native_export"]["desktop_window_visible"]
assert receipt["native_export"]["native_runner_exit_code"] == 0
assert receipt["tests"]["exit_code"] == 0
assert dimensions[DESKTOP_IMAGE.name] == [1440, 837]
assert dimensions[BROWSER_IMAGE.name] == [1360, 3000]
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
