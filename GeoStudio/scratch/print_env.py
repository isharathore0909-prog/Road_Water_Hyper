import os

for k, v in sorted(os.environ.items()):
    if any(term in k.lower() for term in ["qt", "qgis", "xdg", "mime", "path", "python"]):
        print(f"{k} = {v}")
