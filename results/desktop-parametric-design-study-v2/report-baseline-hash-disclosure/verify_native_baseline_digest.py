from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

OUT = Path(__file__).resolve().parent
REPORT = OUT / "synthetic-comparison-report.html"
APP_CAPTURE = OUT / "desktop-export-view.png"
HTML_CAPTURE = OUT / "chrome-report-1360.png"
RECEIPT = OUT / "acceptance-receipt.json"
if any(path.exists() for path in (REPORT, APP_CAPTURE, HTML_CAPTURE, RECEIPT)):
    raise SystemExit("Refusing to replace existing evidence")

baseline = "a" * 64
project = new_design_project("SYNTHETIC baseline digest disclosure")
comparison = {
    "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
    "baseline_engine_identity_sha256": baseline,
    "scientific_validation": "NOT_CLAIMED",
    "notice": "Fixture sintético de presentación; sin cálculo del solver.",
    "studies": [
        {"study_id": "synthetic-A", "source_project_id": project["project_id"],
         "manifest_path": "SYNTHETIC/A.study.json", "manifest_sha256": "b" * 64,
         "baseline_engine_identity_sha256": baseline, "parameter": {"label": "Escape"}, "points": []},
        {"study_id": "synthetic-B", "source_project_id": project["project_id"],
         "manifest_path": "SYNTHETIC/B.study.json", "manifest_sha256": "c" * 64,
         "baseline_engine_identity_sha256": baseline, "parameter": {"label": "Escape"}, "points": []},
    ], "pairs": [], "unpaired": [],
}
app = QApplication.instance() or QApplication([])
print("APP_READY", flush=True)
window = DinoDesktopWindow(project)
window.resize(1360, 900)
window.show()
print("WINDOW_SHOWN", flush=True)
window.analysis_mode.click()
page = window.results
page.result_tabs.setCurrentIndex(3)
page._study_comparison_loaded(comparison)
app.processEvents()
print("COMPARISON_LOADED", flush=True)
with patch("motorsim.desktop.results_page.QFileDialog.getSaveFileName",
           return_value=(str(REPORT), "HTML (*.html)")):
    print("EXPORTING", flush=True)
    if not page.export_study_comparison():
        raise SystemExit("Desktop export action returned false")
app.processEvents()
print("EXPORTED", flush=True)
if not window.grab().save(str(APP_CAPTURE)):
    raise SystemExit("Desktop capture failed")
html = REPORT.read_text(encoding="utf-8")
visible = f'<details class="baseline-digest"><summary>SHA-256 · {baseline[:12]}…</summary>'
if visible not in html or f"<code>{baseline}</code></details>" not in html:
    raise SystemExit("Compact digest/full digest disclosure missing")
if f'"baseline_engine_identity_sha256": "{baseline}"' not in html:
    raise SystemExit("Exact source JSON digest missing")
chrome = shutil.which("chrome.exe")
if not chrome:
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                candidate, _ = winreg.QueryValueEx(key, None)
                if Path(candidate).is_file():
                    chrome = candidate
                    break
        except OSError:
            pass
if not chrome:
    raise RuntimeError("Chrome not found")
with tempfile.TemporaryDirectory(prefix="dino-report-baseline-", ignore_cleanup_errors=True) as profile:
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-first-run", "--no-default-browser-check",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=10000",
                    "--window-size=1360,1400", f"--user-data-dir={profile}",
                    f"--screenshot={HTML_CAPTURE}", REPORT.resolve().as_uri()],
                   check=True, timeout=45, capture_output=True, text=True)
receipt = {
    "schema": "DINO_REPORT_BASELINE_DIGEST_DISCLOSURE_V1",
    "fixture_origin": "synthetic; no solver execution",
    "desktop_visible": window.isVisible(), "desktop_size": [window.width(), window.height()],
    "compact_summary_present": visible in html,
    "full_digest_disclosed": f"<code>{baseline}</code></details>" in html,
    "exact_digest_preserved_in_source_json": f'"baseline_engine_identity_sha256": "{baseline}"' in html,
    "html_sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(),
    "desktop_capture_sha256": hashlib.sha256(APP_CAPTURE.read_bytes()).hexdigest(),
    "chrome_capture_sha256": hashlib.sha256(HTML_CAPTURE.read_bytes()).hexdigest(),
    "browser": "Chrome headless HTML renderer; Desktop generated report",
}
RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if not all((receipt["desktop_visible"], receipt["compact_summary_present"],
            receipt["full_digest_disclosed"], receipt["exact_digest_preserved_in_source_json"])):
    raise SystemExit("Acceptance failed")
print(json.dumps(receipt, ensure_ascii=False))
window.close()
app.quit()
