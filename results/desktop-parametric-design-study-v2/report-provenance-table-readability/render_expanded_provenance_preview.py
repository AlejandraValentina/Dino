from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import winreg
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = OUT / "native-cross-study-comparison-v2.html"
PREVIEW = OUT / "expanded-provenance-preview-v1.html"
SCREENSHOT = OUT / "chrome-expanded-provenance-v1.png"
if PREVIEW.exists() or SCREENSHOT.exists():
    raise SystemExit("Refusing to replace existing expanded provenance evidence")


def locate_chrome() -> Path:
    found = shutil.which("chrome.exe")
    if found:
        return Path(found)
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                candidate = Path(winreg.QueryValueEx(key, None)[0])
                if candidate.is_file():
                    return candidate
        except OSError:
            continue
    raise RuntimeError("Chrome not found")


source = REPORT.read_text(encoding="utf-8")
needle = '<details class="point-provenance">'
if source.count(needle) != 5:
    raise RuntimeError("Expected five expandable point provenance rows")
preview = source.replace(needle, '<details class="point-provenance" open>', 1)
PREVIEW.write_text(preview, encoding="utf-8")
with tempfile.TemporaryDirectory(prefix="dino-provenance-preview-", ignore_cleanup_errors=True) as profile:
    subprocess.run(
        [str(locate_chrome()), "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check", "--run-all-compositor-stages-before-draw",
         "--virtual-time-budget=10000", "--window-size=1360,1100", f"--user-data-dir={profile}",
         f"--screenshot={SCREENSHOT}", PREVIEW.resolve().as_uri()],
        check=True, timeout=45, capture_output=True, text=True,
    )
if not SCREENSHOT.is_file():
    raise RuntimeError("Chrome did not produce the expanded provenance preview")
receipt = {
    "synthetic": True,
    "preview_only": True,
    "source_report": REPORT.relative_to(ROOT).as_posix(),
    "open_details_count": preview.count('<details class="point-provenance" open>'),
    "preview_html_sha256": hashlib.sha256(PREVIEW.read_bytes()).hexdigest(),
    "screenshot": SCREENSHOT.relative_to(ROOT).as_posix(),
    "screenshot_sha256": hashlib.sha256(SCREENSHOT.read_bytes()).hexdigest(),
    "browser": "Chrome headless; only the first native details element is pre-opened for visual inspection",
}
print(json.dumps(receipt, ensure_ascii=False))
