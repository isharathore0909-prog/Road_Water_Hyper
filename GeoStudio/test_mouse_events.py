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

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QPoint, QTimer, QEvent
from PyQt5.QtGui import QMouseEvent, QPixmap, QColor, QPainter, QFont, QLinearGradient, QBrush, QPalette
from qgis.core import QgsApplication

print("Step 1: High DPI scaling...", flush=True)
try:
    QgsApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QgsApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    pass

print("Step 2: QgsApplication init...", flush=True)
QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], True)
app.initQgis()
app.setApplicationName("GeoStudio")
app.setOrganizationName("GeoStudio")
app.setStyle("Fusion")

pal = app.palette()
pal.setColor(QPalette.Highlight, QColor("#e2e8f0"))
pal.setColor(QPalette.HighlightedText, QColor("#0f172a"))
app.setPalette(pal)

print("Step 3: Splash Screen creation...", flush=True)
splash_pix = QPixmap(480, 280)
splash_pix.fill(QColor("#0d1b2a"))
painter = QPainter(splash_pix)
painter.fillRect(0, 0, 480, 280, QColor("#1a3a5c"))
painter.end()

splash = QSplashScreen(splash_pix)
splash.show()
splash.showMessage("Initializing...", Qt.AlignBottom | Qt.AlignLeft, QColor("#4fc3f7"))
app.processEvents()

print("Step 4: Processing.initialize()...", flush=True)
import processing
from processing.core.Processing import Processing
Processing.initialize()
splash.showMessage("Building UI...", Qt.AlignBottom | Qt.AlignLeft, QColor("#a5d6a7"))
app.processEvents()

print("Step 5: GeoStudioMainWindow...", flush=True)
from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()

# How main.py closed splash:
_LIFETIME_REFS = [app, win, splash]
splash.close()
win.raise_()
win.activateWindow()

def synthesize_mouse():
    print("Synthesizing mouse events...", flush=True)
    canvas = win.map_canvas.canvas
    for x in range(10, 500, 50):
        for y in range(10, 400, 50):
            pt = QPoint(x, y)
            ev = QMouseEvent(QEvent.MouseMove, pt, Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            app.sendEvent(canvas, ev)
            app.sendEvent(canvas.viewport(), ev)
    print("Synthesizing mouse completed!", flush=True)
    QTimer.singleShot(500, win.close)

QTimer.singleShot(250, synthesize_mouse)
print("Entering app.exec_()...", flush=True)
ret = app.exec_()
print(f"app.exec_() returned: {ret}", flush=True)
app.exitQgis()
print("Done!")
