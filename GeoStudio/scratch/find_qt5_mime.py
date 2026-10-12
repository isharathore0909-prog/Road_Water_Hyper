import os

qt5_root = r"C:\Program Files\QGIS 3.44.15\apps\Qt5"
for root, dirs, files in os.walk(qt5_root):
    for f in files:
        if "mime" in f.lower() or "freedesktop" in f.lower():
            print(os.path.join(root, f))
