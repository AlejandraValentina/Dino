"""Capture real Desktop layouts; synthetic curve data is presentation-only."""
from __future__ import annotations
import atexit, hashlib, json, os, shutil, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
settings_root=tempfile.mkdtemp(prefix="dino-desktop-quality-v2-settings-")
os.environ["DINO_TEST_SETTINGS_ROOT"]=settings_root
atexit.register(shutil.rmtree,settings_root,ignore_errors=True)

from PySide6.QtCore import QEventLoop,QTimer
from PySide6.QtGui import QFontDatabase,QImage
from PySide6.QtWidgets import QApplication
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import load_results
from motorsim.engine_project import load_project


def main():
    output=ROOT/"results/desktop-quality-v2"
    captures=output/"captures";captures.mkdir(parents=True,exist_ok=True)
    app=QApplication.instance() or QApplication([])
    font=Path(r"C:\Windows\Fonts\segoeui.ttf")
    if font.is_file():QFontDatabase.addApplicationFont(str(font))
    project=load_project(ROOT/"examples/projects/dino-2t-starter.dino2t.json")
    window=DinoDesktopWindow(project);window.show();app.processEvents()
    receipts=[]
    def capture(name,width,height,mode):
        window.resize(width,height);window.set_workspace_mode(mode);app.processEvents()
        image_path=captures/f"{name}-{width}x{height}.png"
        if not window.grab().save(str(image_path)):raise RuntimeError(f"capture failed: {image_path}")
        image=QImage(str(image_path))
        receipts.append({"path":str(image_path.relative_to(ROOT)),"size":[image.width(),image.height()],
            "sha256":hashlib.sha256(image_path.read_bytes()).hexdigest(),"bytes":image_path.stat().st_size})

    for size in ((980,680),(1360,900)):
        capture("modelo-proyecto-real",*size,0)
        capture("simular-configuracion-real",*size,2)
    legacy=ROOT/"results/engine-physics-v1/campaign-evidence-r3/engine_a_3000/result.json"
    data=load_results(legacy)
    window.set_workspace_mode(1);window.results.dataset=data;window.results.source=legacy
    window.results.source_kind="LEGACY_HISTORICAL"
    window.results.source_notice.setText("Artifact histórico real · sólo resumen almacenado · curva de prestaciones no disponible.")
    window.results.path_label.setText(f"{legacy} · SHA-256 {data['source_sha256']}")
    window.results.variants.clear();window.results.variants.addItem(data["points"][0]["variant_id"])
    window.results._dataset_summary();window.results.redraw();app.processEvents()
    for size in ((980,680),(1360,900)):
        capture("resultados-historico-real",*size,1)

    synthetic=ROOT/"results/desktop-windows-rc10-integrated/packaged-historical.json"
    fixture=load_results(synthetic)
    if len(fixture["points"])!=30:raise RuntimeError("synthetic UI fixture is not the expected 30-point report")
    window.results.dataset=fixture;window.results.source=synthetic
    window.results.source_kind="HISTORICAL_IMPL2"
    window.results.source_notice.setText("MUESTRA SINTÉTICA DE PRESENTACIÓN · 30 puntos · no es una predicción ni evidencia experimental.")
    window.results.path_label.setText(f"{synthetic} · origen sintético · {len(fixture['points'])} puntos")
    window.results.variants.clear()
    for variant in sorted({row["variant_id"] for row in fixture["points"]}):window.results.variants.addItem(variant)
    window.results._dataset_summary();window.results.redraw();app.processEvents()
    for size in ((980,680),(1360,900)):
        capture("resultados-curvas-sinteticas-presentacion",*size,1)
    record={"application":"DinoDesktopWindow; source build",
        "project":{"path":"examples/projects/dino-2t-starter.dino2t.json","project_id":project["project_id"]},
        "real_historical_artifact":{"path":str(legacy.relative_to(ROOT)),"sha256":data["source_sha256"],
            "classification":data["points"][0]["classification"],"periodicity":data["points"][0]["periodicity"],
            "performance_metrics":"absent in legacy artifact; displayed as undefined"},
        "synthetic_curve_fixture":{"path":str(synthetic.relative_to(ROOT)),"sha256":hashlib.sha256(synthetic.read_bytes()).hexdigest(),
            "points":30,"purpose":"presentation only; not scientific evidence"},"captures":receipts,
        "checks":{"sizes":[[980,680],[1360,900]],"legacy_has_no_fabricated_power":data["points"][0]["brake_power"] is None,
            "legacy_is_nonconverged":data["points"][0]["periodicity"]=="NOT_CONVERGED",
            "synthetic_fixture_marked":True}}
    (output/"visual-receipt.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record,ensure_ascii=False))
    window.close();app.processEvents();app.quit()


if __name__=="__main__":main()
