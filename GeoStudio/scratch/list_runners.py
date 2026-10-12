import re

with open(r"M:\Geo Studio\GeoStudio\app\ui\algorithm_runners.py", "r", encoding="utf-8") as f:
    content = f.read()

funcs = re.findall(r"^def\s+([a-zA-Z0-9_]+)\s*\(", content, flags=re.MULTILINE)
print("Functions in algorithm_runners.py:")
for fn in funcs:
    print(" -", fn)
