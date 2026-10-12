import sys
import os
import glob

candidates = [os.environ.get("QGIS_ROOT", "")]
for pattern in [r"C:\Program Files\QGIS*", r"C:\Program Files (x86)\QGIS*", r"D:\Program Files\QGIS*", r"C:\OSGeo4W*"]:
    candidates.extend(glob.glob(pattern))
candidates.sort(reverse=True)
candidates.extend([r"C:\Program Files\QGIS 3.44.15", r"C:\Program Files\QGIS 3.40.14"])

QGIS_ROOT = next((c for c in candidates if c and os.path.isdir(c)), r"C:\Program Files\QGIS 3.44.15")
QGIS_APP = os.path.join(QGIS_ROOT, "apps", "qgis-ltr") if os.path.isdir(os.path.join(QGIS_ROOT, "apps", "qgis-ltr")) else os.path.join(QGIS_ROOT, "apps", "qgis")
py_dirs = glob.glob(os.path.join(QGIS_ROOT, "apps", "Python3*"))
py_dirs.sort(reverse=True)
QGIS_PY = py_dirs[0] if py_dirs else os.path.join(QGIS_ROOT, "apps", "Python312")

if hasattr(os, 'add_dll_directory'):
    for dll_dir in [
        os.path.join(QGIS_ROOT, "bin"),
        os.path.join(QGIS_APP, "bin"),
        os.path.join(QGIS_ROOT, "apps", "Qt5", "bin"),
        QGIS_PY,
        os.path.join(QGIS_PY, "Scripts"),
    ]:
        if os.path.exists(dll_dir):
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass

for p in [
    os.path.join(QGIS_APP, "python"),
    os.path.join(QGIS_APP, "python", "plugins"),
    os.path.join(QGIS_PY, "Lib", "site-packages"),
    os.path.join(QGIS_PY, "Lib"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"),
    os.path.dirname(os.path.abspath(__file__)),
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

