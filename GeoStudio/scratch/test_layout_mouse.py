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
from qgis.core import QgsApplication, QgsProject, QgsPrintLayout

QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], True)
app.initQgis()

from ui.main_window import GeoStudioMainWindow
from ui.layout.layout_designer_window import GeoStudioLayoutDesignerWindow

win = GeoStudioMainWindow(qgs_app=app)
win.show()

# Create layout and designer window
proj = QgsProject.instance()
layout = QgsPrintLayout(proj)
layout.initializeDefaults()
proj.layoutManager().addLayout(layout)

designer = GeoStudioLayoutDesignerWindow(layout, main_window=win, parent=win)
# Explicitly set layout on tool_select:
designer.tool_select.setLayout(layout)
designer.show()

def test_interaction():
    print("Synthesizing mouse move over designer view...", flush=True)
    view = designer.view
    # Move mouse across view and viewport
    for x in range(10, 400, 20):
        for y in range(10, 400, 20):
            pt = QPoint(x, y)
            ev = QMouseEvent(QEvent.MouseMove, pt, Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            app.sendEvent(view, ev)
            app.sendEvent(view.viewport(), ev)
    print("Mouse move completed SUCCESSFULLY without any crash!", flush=True)
    QTimer.singleShot(500, win.close)

QTimer.singleShot(200, test_interaction)
print("Running app.exec_()...", flush=True)
ret = app.exec_()
print(f"app.exec_() exited with {ret}", flush=True)
app.exitQgis()
print("TEST FULLY PASSED!")
