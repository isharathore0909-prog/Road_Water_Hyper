# -*- coding: utf-8 -*-
"""
GeoStudio - Standalone GIS Application
Entry point: bootstraps QGIS engine then launches the main window.
"""

import sys
import os

# ── Bootstrap QGIS environment ──────────────────────────────────────────────
QGIS_ROOT = r"C:\Program Files\QGIS 3.40.14"
QGIS_APP  = os.path.join(QGIS_ROOT, "apps", "qgis-ltr")
QGIS_PY   = os.path.join(QGIS_ROOT, "apps", "Python312")

# Add DLL directories for Windows Python 3.8+
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

# Add QGIS Python bindings and plugins to path
for p in [
    os.path.join(QGIS_APP, "python"),
    os.path.join(QGIS_APP, "python", "plugins"),
    os.path.join(QGIS_PY, "Lib", "site-packages"),
    os.path.join(QGIS_PY, "Lib"),
    os.path.dirname(os.path.abspath(__file__)),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set QGIS prefix path
os.environ["QGIS_PREFIX_PATH"]  = QGIS_APP
os.environ["GDAL_DATA"]         = os.path.join(QGIS_ROOT, "share", "gdal")
os.environ["PROJ_LIB"]          = os.path.join(QGIS_ROOT, "share", "proj")
os.environ["QT_PLUGIN_PATH"]    = os.path.join(QGIS_ROOT, "apps", "Qt5", "plugins")


# ── Qt Application ────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QPainter, QFont

app = QApplication(sys.argv)
app.setApplicationName("GeoStudio")
app.setOrganizationName("GeoStudio")
app.setStyle("Fusion")

# ── Splash Screen ─────────────────────────────────────────────────────────────
splash_pix = QPixmap(480, 280)
splash_pix.fill(QColor("#0d1b2a"))

painter = QPainter(splash_pix)
painter.setRenderHint(QPainter.Antialiasing)

# Background gradient rectangle
from PyQt5.QtGui import QLinearGradient, QBrush
gradient = QLinearGradient(0, 0, 480, 280)
gradient.setColorAt(0.0, QColor("#0d1b2a"))
gradient.setColorAt(1.0, QColor("#1a3a5c"))
painter.fillRect(0, 0, 480, 280, QBrush(gradient))

# Title
font = QFont("Segoe UI", 32, QFont.Bold)
painter.setFont(font)
painter.setPen(QColor("#4fc3f7"))
painter.drawText(40, 110, "🌍 GeoStudio")

# Subtitle
font2 = QFont("Segoe UI", 11)
painter.setFont(font2)
painter.setPen(QColor("#90caf9"))
painter.drawText(44, 140, "Standalone Geospatial Analysis System")

# Version
font3 = QFont("Segoe UI", 9)
painter.setFont(font3)
painter.setPen(QColor("#546e7a"))
painter.drawText(44, 200, "Version 1.0  ·  Powered by QGIS Engine 3.40  ·  PyQGIS")

# Loading bar background
painter.setPen(Qt.NoPen)
painter.setBrush(QColor("#1e3a5f"))
painter.drawRoundedRect(40, 230, 400, 12, 6, 6)

painter.setBrush(QColor("#4fc3f7"))
painter.drawRoundedRect(40, 230, 200, 12, 6, 6)

painter.end()

splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
splash.show()
splash.showMessage("  Initializing QGIS engine...", Qt.AlignBottom | Qt.AlignLeft, QColor("#4fc3f7"))
app.processEvents()

# ── Initialize QGIS ──────────────────────────────────────────────────────────
try:
    from qgis.core import QgsApplication
    qgs = QgsApplication([], True)
    qgs.setPrefixPath(QGIS_APP, True)
    qgs.initQgis()
    splash.showMessage("  Loading processing algorithms...", Qt.AlignBottom | Qt.AlignLeft, QColor("#4fc3f7"))
    app.processEvents()

    import processing
    from processing.core.Processing import Processing
    Processing.initialize()
    splash.showMessage("  Building interface...", Qt.AlignBottom | Qt.AlignLeft, QColor("#a5d6a7"))
    app.processEvents()
except ImportError as e:
    splash.showMessage(f"  Warning: {e}", Qt.AlignBottom | Qt.AlignLeft, QColor("#ff8a65"))
    app.processEvents()
    qgs = None

# ── Launch Main Window ────────────────────────────────────────────────────────
# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import GeoStudioMainWindow

window = GeoStudioMainWindow(qgs_app=qgs)
window.show()

# Close splash after window shows
QTimer.singleShot(1800, splash.close)
QTimer.singleShot(1800, window.raise_)

# ── Run ───────────────────────────────────────────────────────────────────────
exit_code = app.exec_()

if qgs:
    qgs.exitQgis()

sys.exit(exit_code)
