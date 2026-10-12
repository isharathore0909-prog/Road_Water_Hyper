import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutviewtoolselect.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for i, line in enumerate(lines):
    if "QgsLayoutViewToolSelect::layoutMoveEvent" in line:
        for j in range(max(0, i - 2), min(len(lines), i + 45)):
            print(f"{j+1}: {lines[j]}")
        break
