import sys, os, time
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"M:\Geo Studio\GeoStudio\app")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

print(f"[{time.strftime('%H:%M:%S')}] Step 1: Initializing QgsApplication...")
qgs = QgsApplication([], True) # GUI application
qgs.initQgis()

print(f"[{time.strftime('%H:%M:%S')}] Step 2: Processing initialize...")
from processing.core.Processing import Processing
Processing.initialize()

print(f"[{time.strftime('%H:%M:%S')}] Step 3: Constructing GeoStudioMainWindow...")
from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=qgs)
print(f"[{time.strftime('%H:%M:%S')}] Constructed window: {win}")

print(f"[{time.strftime('%H:%M:%S')}] Step 4: Calling win.show()...")
win.show()
qgs.processEvents()

print(f"[{time.strftime('%H:%M:%S')}] Window isVisible: {win.isVisible()}")
print(f"[{time.strftime('%H:%M:%S')}] Window geometry: {win.geometry().x()}, {win.geometry().y()}, {win.geometry().width()}x{win.geometry().height()}")
print(f"[{time.strftime('%H:%M:%S')}] Window windowState: {win.windowState()}")

def check_status():
    print(f"[{time.strftime('%H:%M:%S')}] Timer check: isVisible={win.isVisible()}, isHidden={win.isHidden()}")
    win.close()
    qgs.quit()

QTimer.singleShot(1000, check_status)
print(f"[{time.strftime('%H:%M:%S')}] Entering exec_()...")
ret = qgs.exec_()
print(f"[{time.strftime('%H:%M:%S')}] Exited exec_() with code: {ret}")
qgs.exitQgis()
