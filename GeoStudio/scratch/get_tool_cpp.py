import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutviewtool.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j, line in enumerate(lines):
    if "layoutSet" in line or "setLayout" in line or "currentLayout" in line:
        print(f"{j+1}: {line}")
