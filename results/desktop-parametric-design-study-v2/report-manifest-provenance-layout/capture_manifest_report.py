"""Render compact/expanded report provenance using synthetic study metadata."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motorsim.desktop.technical_report import render_study_comparison_report


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    out = Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    browser = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not browser.is_file():
        browser = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    if not browser.is_file():
        raise RuntimeError("Chrome o Edge no está instalado en la ruta del sistema esperada")

    studies = []
    for name, digest, project, folder in (
        ("Variante A", "a", "project-A", "Escape principal"),
        ("Variante B", "b", "project-B", "Escape alternativo"),
    ):
        path = (f"C:/Users/Engineer/Documents/Dino 2T/Projects/"
                f"{folder}/Archived parameter sweeps/2026/large-name-study-manifest.json")
        studies.append({
            "study_id": name,
            "source_project_id": project,
            "manifest_path": path,
            "manifest_sha256": digest * 64,
            "baseline_engine_identity_sha256": "9" * 64,
            "parameter": {"label": "Escape", "unit": "mm"},
            "points": [],
        })

    comparison = {
        "schema": "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256": "9" * 64,
        "scientific_validation": "NOT_CLAIMED",
        "notice": "Fixture sintético de presentación; no constituye validación física.",
        "studies": studies,
        "pairs": [],
        "unpaired": [],
    }
    report = render_study_comparison_report(comparison)
    compact_html = out / "manifest-provenance-synthetic.html"
    expanded_html = out / "manifest-provenance-synthetic-expanded.html"
    compact_html.write_text(report, encoding="utf-8")
    expanded_html.write_text(
        report.replace('<details class="manifest-provenance">',
                       '<details class="manifest-provenance" open>'),
        encoding="utf-8")

    captures = {}
    with tempfile.TemporaryDirectory(prefix="dino-manifest-report-chrome-") as profile:
        for html_path, screenshot_name in (
            (compact_html, "manifest-provenance-compact.png"),
            (expanded_html, "manifest-provenance-expanded.png"),
        ):
            screenshot = out / screenshot_name
            command = [str(browser), "--headless=new", "--disable-gpu", "--no-first-run",
                       "--no-default-browser-check", f"--user-data-dir={profile}",
                       "--window-size=1360,1100", f"--screenshot={screenshot}", html_path.as_uri()]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if completed.returncode != 0 or not screenshot.is_file():
                raise RuntimeError(f"Chrome no pudo capturar {html_path.name}: "
                                   f"{completed.stdout}\n{completed.stderr}")
            captures[screenshot_name] = {"sha256": sha256(screenshot), "bytes": screenshot.stat().st_size}

    receipt = {
        "schema": "DINO_SYNTHETIC_MANIFEST_REPORT_LAYOUT_CAPTURE_V1",
        "fixture_origin": "synthetic display only; no solver and no scientific claim",
        "browser": str(browser),
        "viewport": {"width": 1360, "height": 1100},
        "report_sha256": sha256(compact_html),
        "expanded_report_sha256": sha256(expanded_html),
        "captures": captures,
        "manifest_source_paths": [study["manifest_path"] for study in studies],
        "manifest_sha256_values": [study["manifest_sha256"] for study in studies],
    }
    (out / "capture-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
