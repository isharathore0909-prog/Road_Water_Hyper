import sys, os, time
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"M:\Geo Studio\GeoStudio\app")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import QTimer

app = QgsApplication([], True)
app.initQgis()

pix = QPixmap(100, 100)
pix.fill(QColor("black"))
splash = QSplashScreen(pix)
splash.show()
app.processEvents()

from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()

# Current main.py code:
splash.close()
win.raise_()
win.activateWindow()

def on_started():
    print("GeoStudio started successfully.", flush=True)

QTimer.singleShot(250, on_started)

print("Starting app.exec_()...", flush=True)
ret = app.exec_()
print(f"app.exec_() exited immediately with code: {ret}!", flush=True)
app.exitQgis()
