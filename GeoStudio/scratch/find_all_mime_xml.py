import os, glob

# Search for any mime/packages or freedesktop.org.xml
candidates = [
    r"C:\Program Files\QGIS 3.44.15",
    os.environ.get("APPDATA", ""),
    os.environ.get("LOCALAPPDATA", ""),
    os.environ.get("USERPROFILE", ""),
    r"M:\Geo Studio\GeoStudio"
]

print("Searching for mime directories and xml files...")
for base in candidates:
    if not base or not os.path.exists(base): continue
    for root, dirs, files in os.walk(base):
        if "mime" in root.lower():
            for f in files:
                p = os.path.join(root, f)
                sz = os.path.getsize(p)
                print(f"Found: {p} ({sz} bytes)")
