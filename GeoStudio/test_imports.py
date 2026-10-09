import sys
import os

QGIS_ROOT = os.environ.get("QGIS_ROOT") or r"C:\Program Files\QGIS 3.44.15"
QGIS_APP  = os.environ.get("QGIS_PREFIX_PATH") or os.path.join(QGIS_ROOT, "apps", "qgis-ltr")
QGIS_PY   = os.path.join(QGIS_ROOT, "apps", "Python312")

if hasattr(os, 'add_dll_directory'):
    for dll_dir in [
        os.path.join(QGIS_ROOT, "bin"),
        os.path.join(QGIS_APP, "bin"),
        os.path.join(QGIS_ROOT, "apps", "Qt5", "bin"),
        QGIS_PY,
        os.path.join(QGIS_PY, "Scripts"),
    ]:
        if os.path.exists(dll_dir):
            os.add_dll_directory(dll_dir)

for p in [
    os.path.join(QGIS_APP, "python"),
    os.path.join(QGIS_APP, "python", "plugins"),
    os.path.join(QGIS_PY, "Lib", "site-packages"),
    os.path.join(QGIS_PY, "Lib"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)


from core.style import DARK_STYLESHEET
print('core.style OK')
from ui.processing_dock import ProcessingDock
print('processing_dock OK')
from ui.main_window import GeoStudioMainWindow
print('main_window OK')
print('ALL IMPORTS PASSED')

