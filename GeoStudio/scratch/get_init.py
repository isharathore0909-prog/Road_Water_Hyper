import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/gui/layout/qgslayoutviewtoolselect.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j in range(30, 100):
    print(f"{j+1}: {lines[j]}")
