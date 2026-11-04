from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from PySide6.QtCore import QEventLoop, QPoint, QTimer
from PySide6.QtWidgets import QApplication

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project


repo=Path(__file__).resolve().parents[3]
csv_path=repo/"results/desktop-parametric-design-study-v2/factor-effects-csv/native-smoke-20261104T200320Z/factorial-export.csv"
app=QApplication.instance() or QApplication([])
window=DinoDesktopWindow(new_design_project("synthetic-factorial-csv-import-ui"))
window.resize(1360,900);window.show();app.processEvents();window.set_workspace_mode(1);app.processEvents()
page=window.results
page.load(csv_path)
loop=QEventLoop();poll=QTimer();poll.setInterval(50)
def loaded():
    if page.source_kind=="PARAMETRIC_FACTORIAL_CSV_SNAPSHOT" or page.path_label.text().startswith("No se pudieron cargar"):
        loop.quit()
poll.timeout.connect(loaded);poll.start();QTimer.singleShot(30000,loop.quit);loop.exec();poll.stop();app.processEvents()
if page.source_kind!="PARAMETRIC_FACTORIAL_CSV_SNAPSHOT":
    raise SystemExit("Desktop no abrió el CSV factorial como snapshot: "+page.path_label.text())
if page.factorial_csv_snapshot_points.rowCount()!=4 or page.factorial_csv_snapshot_contrasts.rowCount()!=9:
    raise SystemExit("Desktop no mostró los cuatro puntos y nueve contrastes")
if page.plot.series or page.export_table_button.isVisible():
    raise SystemExit("el snapshot factorial se filtró a curvas o exportación de resultados")
if "NOT_CLAIMED" not in page.factorial_csv_snapshot_notice.text():
    raise SystemExit("falta la clasificación científica original")

page.result_tabs.setCurrentIndex(3)
scroll=page.result_tabs.currentWidget();content=scroll.widget();bar=scroll.verticalScrollBar()
points_y=page.factorial_csv_snapshot_points.mapTo(content,QPoint(0,0)).y()
bar.setValue(max(0,points_y-8));app.processEvents()
out=Path(__file__).resolve().parent
points_capture=out/"factorial-csv-snapshot-native-points.png"
if not window.grab().save(str(points_capture)):raise SystemExit("falló captura de tabla POINT")
contrast_y=page.factorial_csv_snapshot_contrasts.mapTo(content,QPoint(0,0)).y()
bar.setValue(max(0,contrast_y-8));app.processEvents()
contrast_capture=out/"factorial-csv-snapshot-native-contrasts.png"
if not window.grab().save(str(contrast_capture)):raise SystemExit("falló captura de tabla CONTRAST")
snapshot=page.dataset["snapshot"]
receipt={
    "window":"Dino Desktop source · native Windows Qt window",
    "window_size":[window.width(),window.height()],
    "source_csv":str(csv_path),"source_csv_sha256":snapshot["csv_sha256"],
    "csv_schema":snapshot["csv_schema"],"study_id":snapshot["study_id"],
    "manifest_sha256":snapshot["manifest_sha256"],
    "manifest_current_verification":snapshot["manifest_current_verification"],
    "source_verification_time":snapshot["source_verification_time"],
    "current_source_states":[point["current_source_verification"] for point in page.dataset["snapshot_points"]],
    "point_rows":page.factorial_csv_snapshot_points.rowCount(),
    "contrast_rows":page.factorial_csv_snapshot_contrasts.rowCount(),
    "snapshot_notice":page.factorial_csv_snapshot_notice.text(),
    "contrast_source_bindings":snapshot["contrast_source_bindings"],
    "plot_series":page.plot.series,"scientific_validation":snapshot["scientific_validation"],
    "fixture_origin":"previously saved synthetic presentation/export fixture; import only; no solver execution",
    "captures":[{"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in (points_capture,contrast_capture)],
}
(out/"native-window-receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,ensure_ascii=False))
window.close();app.processEvents()
