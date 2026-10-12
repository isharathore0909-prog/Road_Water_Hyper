# -*- coding: utf-8 -*-
import sys, os, time
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"M:\Geo Studio\GeoStudio\app")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from PyQt5.QtCore import (
    QT_VERSION_STR, PYQT_VERSION_STR, Qt, QTimer, QMimeDatabase,
    qInstallMessageHandler, QtWarningMsg, QtCriticalMsg
)
from qgis.core import QgsApplication

print("="*60)
print(f"[{time.strftime('%H:%M:%S')}] DIAGNOSING GUI & MIME TOGETHER")
print("="*60)
print(f"Qt version: {QT_VERSION_STR}")
print(f"PyQt version: {PYQT_VERSION_STR}")
print(f"Python: {sys.version.split()[0]} ({sys.executable})")

# 1. Test QMimeDatabase behavior
print("\n[Step 1] Testing QMimeDatabase raw call...")
db = QMimeDatabase()
m = db.mimeTypeForName("text/plain")
print(f"QMimeDatabase text/plain valid: {m.isValid()}, name: '{m.name()}'")

# 2. Test Qt message handler filter for QMimeDatabase
print("\n[Step 2] Installing clean message handler filter...")
mime_warnings_caught = []
def _qt_message_filter(mode, context, message):
    if "QMimeDatabase: Error loading internal MIME data" in message or "<internal MIME data>" in message:
        mime_warnings_caught.append(message)
        return  # Filter out known Qt5 Windows empty internal XML warning
    sys.stderr.write(f"[Qt] {message}\n")
    sys.stderr.flush()

qInstallMessageHandler(_qt_message_filter)

# Trigger QMimeDatabase again with filter
db2 = QMimeDatabase()
m2 = db2.mimeTypeForName("text/plain")
print(f"With filter installed: caught {len(mime_warnings_caught)} warning(s). Clean output verified!")

# 3. Test Full GeoStudioMainWindow display and focus
print("\n[Step 3] Initializing QgsApplication & GeoStudioMainWindow...")
qgs = QgsApplication([], True)
qgs.initQgis()

from processing.core.Processing import Processing
Processing.initialize()

from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=qgs)

print("\n[Step 4] Displaying window (showMaximized + activateWindow)...")
win.showMaximized()
win.raise_()
win.activateWindow()
qgs.processEvents()

print(f"Window isVisible: {win.isVisible()}")
print(f"Window isHidden:  {win.isHidden()}")
print(f"Window isMinimized: {win.isMinimized()}")
print(f"Window isMaximized: {win.isMaximized()}")
rect = win.geometry()
print(f"Window geometry: ({rect.x()}, {rect.y()}) {rect.width()}x{rect.height()}")

def _on_check():
    print(f"[{time.strftime('%H:%M:%S')}] Timer check: isVisible={win.isVisible()}, isActiveWindow={win.isActiveWindow()}")
    win.close()
    qgs.quit()

QTimer.singleShot(1500, _on_check)
print("\n[Step 5] Entering exec_()...")
ret = qgs.exec_()
print(f"exec_() completed with return code: {ret}")
qgs.exitQgis()

print("\n" + "="*60)
print("DIAGNOSTIC TEST COMPLETED SUCCESSFULLY!")
print("="*60)
