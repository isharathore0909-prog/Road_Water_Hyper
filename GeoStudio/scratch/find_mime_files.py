import os, glob

qgis_root = r"C:\Program Files\QGIS 3.44.15"
matches = []
for root, dirs, files in os.walk(qgis_root):
    for f in files:
        if "mime" in f.lower():
            matches.append(os.path.join(root, f))
    if len(matches) > 30:
        break

print("Found MIME files in QGIS installation:")
for m in matches:
    print(" -", m)
