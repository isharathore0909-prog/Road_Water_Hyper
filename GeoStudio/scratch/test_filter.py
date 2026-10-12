import sys
from PyQt5.QtCore import QMimeDatabase, QCoreApplication, qInstallMessageHandler

app = QCoreApplication([])

# Before filter
print("--- Calling QMimeDatabase before filter ---")
db = QMimeDatabase()
m = db.mimeTypeForName("text/plain")
print("Done before filter.")

# Now install filter
def _qt_message_filter(mode, context, message):
    if "QMimeDatabase" in message or "<internal MIME data>" in message:
        return # Suppress known Qt5 Windows empty internal resource warning
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()

qInstallMessageHandler(_qt_message_filter)

print("--- Calling QMimeDatabase after filter ---")
db2 = QMimeDatabase()
m2 = db2.mimeTypeForName("text/plain")
print("Done after filter. No warning printed!")
