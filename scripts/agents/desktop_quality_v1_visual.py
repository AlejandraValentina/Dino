"""Run the real Desktop window and capture compact/wide result layouts.

The displayed points are synthetic UI fixtures only; this script never calls
the engine solver or writes a project/artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import atexit
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
_settings_root=tempfile.mkdtemp(prefix="dino-desktop-quality-settings-")
os.environ["DINO_TEST_SETTINGS_ROOT"]=_settings_root
atexit.register(shutil.rmtree,_settings_root,ignore_errors=True)

from PySide6.QtGui import QFontDatabase,QImage
from PySide6.QtWidgets import QApplication

from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_project


def main():
    output=ROOT/"results/desktop-quality-v1"
    capture_dir=output/"captures"
    capture_dir.mkdir(parents=True,exist_ok=True)
    app=QApplication.instance() or QApplication([])
    font=Path(r"C:\Windows\Fonts\segoeui.ttf")
    if font.is_file():QFontDatabase.addApplicationFont(str(font))
    window=DinoDesktopWindow(new_project("desktop-quality-ui-synthetic"))
    window.set_workspace_mode(1)
    results=window.results
    results.source_kind="SYNTHETIC_UI_FIXTURE"
    results.source_notice.setText("Muestra sintética de interfaz · no proviene del solver y no es una predicción.")
    results.run_summary.setText("Datos sintéticos de interfaz · sin valores físicos válidos ni RPM emparejadas.")
    rows=[]
    for variant,rpm in (("Escape A",4000),("Escape B",5000)):
        rows.append(dict(variant_id=variant,rpm=rpm,mode="SYNTHETIC_UI_FIXTURE",
            classification="MAX_CYCLES_NONCONVERGED",periodicity="NOT_CONVERGED",
            brake_power_status="UNDEFINED",brake_torque_status="UNDEFINED",
            solver_identity_sha256="synthetic-ui-only",fuel_id="synthetic-ui-only",
            mechanical_loss_model_sha256="synthetic-ui-only",total_finite_volume_cells=44))
    results.power_curves.set_dataset({"points":rows,"provenance":"SYNTHETIC_UI_FIXTURE",
        "experimental_validation":"NOT_CLAIMED"},{"Escape A","Escape B"})
    results.power_curves.exploratory_toggle.setChecked(True)
    results.power_curves.view_selector.setCurrentIndex(1)
    window.resize(980,680)
    window.show();app.processEvents()
    records=[]
    horizontal_scroll={}
    for width,height in ((980,680),(1360,900)):
        window.resize(width,height);app.processEvents()
        for view,name in ((1,"comparacion"),(0,"curvas")):
            results.power_curves.view_selector.setCurrentIndex(view);app.processEvents()
            scroll=results.result_tabs.currentWidget()
            horizontal_scroll[f"{width}x{height}-{name}"]={
                "results_page":scroll.horizontalScrollBar().maximum(),
                "points_table":results.power_curves.points.horizontalScrollBar().maximum()}
            path=capture_dir/f"desktop-{width}x{height}-{name}.png"
            if not window.grab().save(str(path)):raise RuntimeError(f"No se pudo guardar {path}")
            image=QImage(str(path));raw=path.read_bytes()
            records.append({"path":str(path.relative_to(ROOT)),"width":image.width(),"height":image.height(),
                "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    receipt={"application":"DinoDesktopWindow (fuente actual)",
        "fixture":"SYNTHETIC_UI_FIXTURE; no solver, no project writes, not physical evidence",
        "checks":{"window_visible":window.isVisible(),"no_exact_rpm_pair_notice":
            "no tienen RPM comunes exactos" in results.power_curves.compare_label.text(),
            "exploratory_is_opt_in":results.power_curves.exploratory_toggle.isChecked(),
            "result_horizontal_scroll_maximum":horizontal_scroll,
            "results_fit_without_horizontal_scroll":all(value==0 for pair in horizontal_scroll.values() for value in pair.values())},
        "captures":records}
    (output/"visual-receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))
    window.close();app.processEvents();app.quit()


if __name__=="__main__":main()
