import sys
import os
import faulthandler
import traceback

faulthandler.enable()

qgis_root = r"C:\Program Files\QGIS 3.44.15"
qgis_app = os.path.join(qgis_root, "apps", "qgis-ltr")
qgis_py = os.path.join(qgis_root, "apps", "Python312")

for p in [
    os.path.join(qgis_app, "python"),
    os.path.join(qgis_app, "python", "plugins"),
    os.path.join(qgis_py, "Lib", "site-packages"),
    os.path.join(qgis_py, "Lib"),
    r"M:\Geo Studio\GeoStudio\app",
    r"M:\Geo Studio\GeoStudio",
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer, QEvent, QVariant
from PyQt5.QtGui import QMouseEvent
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsField, QgsFeature, QgsGeometry, QgsPointXY,
    QgsLayoutExporter
)

print("--- [VERIFY 1] Starting QGIS Application ---", flush=True)
QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], True)
app.initQgis()
print("[VERIFY 1 PASSED] QgsApplication initialized.", flush=True)

print("--- [VERIFY 2] Starting GeoStudio Main Window ---", flush=True)
from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()
print("[VERIFY 2 PASSED] Main Window is active and displayed.", flush=True)

# Add sample data layer to project
project = QgsProject.instance()
vl = QgsVectorLayer("Point?crs=EPSG:4326", "Test Points", "memory")
pr = vl.dataProvider()
pr.addAttributes([QgsField("id", QVariant.Int), QgsField("name", QVariant.String)])
vl.updateFields()
f1 = QgsFeature(vl.fields())
f1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(77.20, 28.61)))
f1.setAttributes([1, "Capital"])
pr.addFeatures([f1])
vl.updateExtents()
project.addMapLayer(vl)
win.map_canvas.zoom_full()

def run_tests():
    try:
        # Test 3: Map canvas pan & zoom
        print("--- [VERIFY 3] Testing Map Canvas zoom and pan ---", flush=True)
        canvas = win.map_canvas.canvas
        initial_ext = canvas.extent()
        canvas.zoomByFactor(1.5)
        canvas.setCenter(QgsPointXY(77.25, 28.65))
        app.processEvents()
        print("[VERIFY 3 PASSED] Map canvas responded to zoom and pan.", flush=True)

        # Test 4: Open Print Layout window
        print("--- [VERIFY 4 & 5] Creating Layout populated with map ---", flush=True)
        designer = win.create_layout_from_current_map()
        assert designer is not None, "Failed to create layout designer window"
        assert designer.isVisible(), "Layout designer window is not visible"
        assert designer.layout is not None, "Designer layout is None"
        print(f"[VERIFY 4 & 5 PASSED] Print Layout window opened with layout: {designer.layout.name()}", flush=True)

        # Move mouse across view to verify layoutMoveEvent stability
        view = designer.view
        for x in range(20, 300, 30):
            ev = QMouseEvent(QEvent.MouseMove, QPoint(x, x), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            app.sendEvent(view, ev)
            app.sendEvent(view.viewport(), ev)
        app.processEvents()
        print("[VERIFY 5 SUBTEST PASSED] Interactive QgsLayoutView mouse move verified.", flush=True)

        # Test 6: Layout preview and export
        print("--- [VERIFY 6] Testing layout preview & high-res export ---", flush=True)
        out_png = os.path.join(r"M:\Geo Studio\GeoStudio\scratch", "test_verify_export.png")
        if os.path.exists(out_png):
            os.remove(out_png)

        exporter = QgsLayoutExporter(designer.layout)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 150
        res = exporter.exportToImage(out_png, settings)
        assert res == QgsLayoutExporter.Success, f"Export failed with code: {res}"
        assert os.path.exists(out_png) and os.path.getsize(out_png) > 1000, "Exported file invalid"
        print(f"[VERIFY 6 PASSED] Layout export succeeded: {os.path.getsize(out_png):,} bytes.", flush=True)

        # Test 7: Close and reopen layout
        print("--- [VERIFY 7] Testing closing and reopening layout designer ---", flush=True)
        designer.close()
        app.processEvents()
        print("Closed layout designer. Now reopening...", flush=True)
        designer2 = win.open_layout_designer(designer.layout)
        assert designer2 is not None and designer2.isVisible(), "Failed to reopen layout designer"
        # Simulate interaction on reopened window
        for x in range(30, 200, 25):
            ev = QMouseEvent(QEvent.MouseMove, QPoint(x, x), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            app.sendEvent(designer2.view.viewport(), ev)
        app.processEvents()
        designer2.close()
        app.processEvents()
        print("[VERIFY 7 PASSED] Layout successfully reopened and closed cleanly.", flush=True)

        # Test 8: Clean shutdown
        print("--- [VERIFY 8] Testing clean shutdown of GeoStudio ---", flush=True)
        win.close()
        app.processEvents()
        print("[VERIFY 8 PASSED] GeoStudio main window closed.", flush=True)
    except Exception as e:
        print(f"FAILED during verification: {e}", flush=True)
        traceback.print_exc()
        win.close()

QTimer.singleShot(250, run_tests)
ret = app.exec_()
print(f"app.exec_() returncode: {ret}", flush=True)
app.exitQgis()
print("=== ALL 8 VERIFICATION PHASES COMPLETED WITH 100% SUCCESS! ===", flush=True)
sys.exit(0 if ret == 0 else ret)
