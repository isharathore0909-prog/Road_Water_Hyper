from PyQt5.QtCore import QStandardPaths, QCoreApplication

app = QCoreApplication([])

for loc_name in ["GenericDataLocation", "AppDataLocation", "ConfigLocation", "GenericConfigLocation"]:
    loc = getattr(QStandardPaths, loc_name)
    paths = QStandardPaths.standardLocations(loc)
    print(f"{loc_name}: {paths}")
