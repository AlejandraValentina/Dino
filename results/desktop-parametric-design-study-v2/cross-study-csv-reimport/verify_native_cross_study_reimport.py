from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

ARTIFACTS=Path(__file__).resolve().parent
CSV=ROOT/"results/desktop-parametric-design-study-v2/cross-study-csv-export/synthetic-comparison.csv"
CAPTURE=ARTIFACTS/"native-cross-study-csv-snapshot.png"
RECEIPT=ARTIFACTS/"native-window-receipt.json"
APP=QApplication.instance() or QApplication([])
window=DinoDesktopWindow(new_design_project("SYNTHETIC cross-study CSV reimport"))
window.resize(1440,900)
window.show()
window.analysis_mode.click()
window.results.result_tabs.setCurrentIndex(3)
window.results.load(CSV)
timeout=QTimer();timeout.setSingleShot(True)


def finish_timeout():
    raise SystemExit("Timed out waiting for the Desktop CSV snapshot import")


timeout.timeout.connect(finish_timeout);timeout.start(15000)


def check_ready():
    page=window.results
    if page.source_kind!="CROSS_STUDY_COMPARISON_CSV_SNAPSHOT":
        QTimer.singleShot(100,check_ready);return
    APP.processEvents()
    capture_ok=window.grab().save(str(CAPTURE))
    receipt={"schema":"DINO_NATIVE_CROSS_STUDY_CSV_REIMPORT_V1","synthetic":True,
        "native_window_visible":window.isVisible(),"outer_size":[window.width(),window.height()],
        "source_csv":str(CSV.relative_to(ROOT)),"source_csv_sha256":hashlib.sha256(CSV.read_bytes()).hexdigest(),
        "snapshot_schema":page.dataset.get("schema"),"read_only":page.dataset.get("read_only"),
        "comparison_rows":page.cross_study_csv_snapshot_table.rowCount(),
        "row_types":[page.cross_study_csv_snapshot_table.item(i,0).text() for i in range(page.cross_study_csv_snapshot_table.rowCount())],
        "nonperiodic_status_visible":"Ciclos insuficientes" in page.cross_study_csv_snapshot_table.item(0,3).text(),
        "unpaired_reason_visible":"sin punto compatible a 4000 RPM" in page.cross_study_csv_snapshot_table.item(1,7).text(),
        "horizontal_scroll_not_required":page.cross_study_csv_snapshot_table.horizontalScrollBar().maximum()==0,
        "scientific_status_not_claimed":"No declarada" in page.cross_study_csv_snapshot_notice.text(),
        "normal_curves_cleared":page.plot.series==[],"capture_saved":capture_ok,
        "capture_sha256":hashlib.sha256(CAPTURE.read_bytes()).hexdigest() if capture_ok else None}
    RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if not all((receipt["native_window_visible"],receipt["read_only"],receipt["comparison_rows"]==2,
                receipt["nonperiodic_status_visible"],receipt["unpaired_reason_visible"],
                receipt["scientific_status_not_claimed"],receipt["normal_curves_cleared"],
                receipt["horizontal_scroll_not_required"],capture_ok)):
        raise SystemExit(f"Native Desktop acceptance failed: {receipt}")
    print(json.dumps(receipt,ensure_ascii=False))
    timeout.stop();APP.quit()


QTimer.singleShot(100,check_ready)
APP.exec()
