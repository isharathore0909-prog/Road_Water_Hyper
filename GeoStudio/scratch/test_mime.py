import os, sys
from PyQt5.QtCore import QMimeDatabase, QFile, QIODevice, QCoreApplication

app = QCoreApplication([])

f = QFile(":/qt-project.org/qmime/freedesktop.org.xml")
print("Resource exists:", f.exists())
if f.exists():
    print("Resource size:", f.size())
    if f.open(QIODevice.ReadOnly):
        data = f.read(200)
        print("First 200 bytes:", data[:100])
        f.close()

db = QMimeDatabase()
m = db.mimeTypeForName("text/plain")
print("text/plain valid:", m.isValid())
print("text/plain name:", m.name())
print("XDG_DATA_DIRS:", os.environ.get("XDG_DATA_DIRS"))
print("QT_PLUGIN_PATH:", os.environ.get("QT_PLUGIN_PATH"))
