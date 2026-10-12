from qgis.core import QgsApplication, QgsProject, QgsPrintLayout
from qgis.gui import QgsLayoutView, QgsLayoutViewToolSelect

qgs = QgsApplication([], False)
qgs.initQgis()

proj = QgsProject.instance()
layout = QgsPrintLayout(proj)
layout.initializeDefaults()

view = QgsLayoutView()
view.setCurrentLayout(layout)

tool = QgsLayoutViewToolSelect(view)
print("tool has setLayout?", hasattr(tool, "setLayout"))
if hasattr(tool, "setLayout"):
    tool.setLayout(layout)
    print("setLayout called successfully!")

print("mouseHandles:", hasattr(tool, "mouseHandles"))
if hasattr(tool, "mouseHandles"):
    print("handles:", tool.mouseHandles())

qgs.exitQgis()
print("Done!")
