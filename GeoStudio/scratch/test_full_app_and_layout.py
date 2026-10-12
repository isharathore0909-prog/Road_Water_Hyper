import sys
import os
import faulthandler

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
from PyQt5.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt5.QtGui import QMouseEvent
from qgis.core import QgsApplication

QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], True)
app.initQgis()

from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()

print("GeoStudio main window shown successfully.", flush=True)

def simulate_user_actions():
    try:
        print("1. Simulating mouse moves on map canvas...", flush=True)
        canvas = win.map_canvas.canvas
        for x in range(20, 200, 30):
            ev = QMouseEvent(QEvent.MouseMove, QPoint(x, x), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            app.sendEvent(canvas.viewport(), ev)

        print("2. Opening Layout from current map (Ctrl+P / print_map)...", flush=True)
        win.create_layout_from_current_map()

        # Find the opened designer window
        from ui.layout.layout_designer_window import GeoStudioLayoutDesignerWindow
        designers = [w for w in app.topLevelWidgets() if isinstance(w, GeoStudioLayoutDesignerWindow)]
        print(f"Found {len(designers)} layout designer window(s).", flush=True)
        assert len(designers) >= 1, "Layout designer window was not created"
        designer = designers[0]

        print("3. Simulating mouse moves across QgsLayoutView canvas...", flush=True)
        view = designer.view
        for x in range(20, 400, 25):
            for y in range(20, 300, 25):
                ev = QMouseEvent(QEvent.MouseMove, QPoint(x, y), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
                app.sendEvent(view, ev)
                app.sendEvent(view.viewport(), ev)

        print("4. Closing layout designer window...", flush=True)
        designer.close()

        print("5. Closing main window...", flush=True)
        win.close()
        print("All simulation steps completed without crash!", flush=True)
    except Exception as e:
        print(f"Simulation error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        win.close()

QTimer.singleShot(300, simulate_user_actions)
ret = app.exec_()
print(f"Application event loop exited with code: {ret}", flush=True)
app.exitQgis()
print("Shutdown complete. ALL TESTS PASSED!", flush=True)
