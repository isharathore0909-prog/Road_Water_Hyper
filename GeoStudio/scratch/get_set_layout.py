import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutview.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j in range(85, 150):
    if j < len(lines):
        print(f"{j+1}: {lines[j]}")
