import sys, os
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"M:\Geo Studio\GeoStudio\app")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
app = QgsApplication([], True)
app.initQgis()

from PyQt5.QtCore import qInstallMessageHandler, QtWarningMsg, QtCriticalMsg

def msg_handler(msg_type, context, message):
    import traceback
    print(f"[QtMsg {msg_type}] {message}")
    if "QMimeDatabase" in message or "MIME" in message:
        print("STACKTRACE TO MIME CALL:")
        traceback.print_stack()

qInstallMessageHandler(msg_handler)

print("Constructing GeoStudioMainWindow...")
from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)
win.show()
app.processEvents()
print("Processed events. Now closing...")
win.close()
app.exitQgis()
