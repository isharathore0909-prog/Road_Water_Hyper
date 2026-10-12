import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutviewtoolselect.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j, line in enumerate(lines):
    if "mMouseHandles" in line:
        print(f"{j+1}: {line}")
