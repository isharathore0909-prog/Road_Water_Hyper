import os, sys, tempfile
from PyQt5.QtCore import QMimeDatabase, QCoreApplication

# Test 1: Without XDG_DATA_DIRS
app = QCoreApplication([])
db1 = QMimeDatabase()
m1 = db1.mimeTypeForName("text/plain")
print("Before fix - text/plain valid:", m1.isValid(), "name:", m1.name())

# Test 2: With valid shared-mime-info directory in XDG_DATA_DIRS
mime_dir = os.path.join(r"M:\Geo Studio\GeoStudio\app\resources", "mime")
pkg_dir = os.path.join(mime_dir, "packages")
os.makedirs(pkg_dir, exist_ok=True)
xml_path = os.path.join(pkg_dir, "freedesktop.org.xml")

sample_mime_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/plain">
    <comment>Plain text</comment>
    <glob pattern="*.txt"/>
  </mime-type>
  <mime-type type="image/png">
    <comment>PNG image</comment>
    <glob pattern="*.png"/>
  </mime-type>
  <mime-type type="application/geo+json">
    <comment>GeoJSON</comment>
    <glob pattern="*.geojson"/>
  </mime-type>
  <mime-type type="application/geopackage+sqlite3">
    <comment>GeoPackage</comment>
    <glob pattern="*.gpkg"/>
  </mime-type>
</mime-info>
"""

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(sample_mime_xml)

os.environ["XDG_DATA_DIRS"] = r"M:\Geo Studio\GeoStudio\app\resources" + (";" + os.environ["XDG_DATA_DIRS"] if "XDG_DATA_DIRS" in os.environ else "")

db2 = QMimeDatabase()
m2 = db2.mimeTypeForName("text/plain")
print("After fix - text/plain valid:", m2.isValid(), "name:", m2.name())
m3 = db2.mimeTypeForName("application/geo+json")
print("After fix - geojson valid:", m3.isValid(), "name:", m3.name())
