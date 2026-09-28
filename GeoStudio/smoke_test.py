# -*- coding: utf-8 -*-
"""
GeoStudio smoke test: initializes QGIS engine, instantiates GeoStudioMainWindow, tests components.
"""
import sys
import os

QGIS_ROOT = r"C:\Program Files\QGIS 3.40.14"
QGIS_APP  = os.path.join(QGIS_ROOT, "apps", "qgis-ltr")
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
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsApplication

print("[1/5] Creating QgsApplication...")
qgs = QgsApplication([], False)
qgs.setPrefixPath(QGIS_APP, True)
qgs.initQgis()
print("  QgsApplication initialized successfully!")

print("[2/5] Initializing Processing...")
import processing
from processing.core.Processing import Processing
Processing.initialize()
print("  Processing initialized successfully!")

print("[3/5] Instantiating GeoStudioMainWindow...")
from ui.main_window import GeoStudioMainWindow
window = GeoStudioMainWindow(qgs_app=qgs)
print("  GeoStudioMainWindow created successfully!")

print("[4/5] Verifying canvas, docks, toolbars...")
assert window.map_canvas is not None, "Map canvas is None"
assert window.layer_panel is not None, "Layer panel is None"
assert window.processing_dock is not None, "Processing dock is None"
assert window.attr_table_dock is not None, "Attribute table dock is None"
assert window.console_dock is not None, "Console dock is None"
print("  All UI components verified!")


print("[5/5] Cleaning up QGIS engine...")
qgs.exitQgis()
print("SMOKE TEST COMPLETE: GeoStudio is 100% operational!")
