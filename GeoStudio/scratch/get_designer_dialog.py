import urllib.request

url = "https://raw.githubusercontent.com/qgis/QGIS/final-3_34_0/src/app/layout/qgslayoutdesignerdialog.cpp"
content = urllib.request.urlopen(url).read().decode('utf-8')
lines = content.splitlines()

for j in range(1270, 1300):
    if j < len(lines):
        print(f"{j+1}: {lines[j]}")
