import urllib.request

# Search in qgslayoutview.cpp for setLayout
url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutview.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j, line in enumerate(lines):
    if "setCurrentLayout" in line or "setLayout" in line:
        print(f"{j+1}: {line}")
