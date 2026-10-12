import sys
import os

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
from qgis.core import QgsApplication

QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], True)
app.initQgis()

from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()

# List ALL widgets in QApplication
all_widgets = QApplication.allWidgets()
print(f"Total widgets created in QApplication: {len(all_widgets)}")

layout_widgets = []
for w in all_widgets:
    cls_name = w.metaObject().className()
    if any(k in cls_name.lower() for k in ("layout", "view", "tool", "canvas")):
        layout_widgets.append((cls_name, w.objectName(), w.isVisible(), type(w).__name__))

print("\nWidgets with 'layout', 'view', 'tool', 'canvas' in name:")
for cls_name, obj_name, vis, py_type in sorted(layout_widgets):
    print(f"  {cls_name} (py: {py_type}) - obj: '{obj_name}' - visible: {vis}")

app.exitQgis()
