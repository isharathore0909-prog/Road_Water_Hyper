from qgis.core import QgsApplication, QgsProject, QgsPrintLayout
from qgis.gui import (
    QgsLayoutView, QgsLayoutViewToolSelect, QgsLayoutViewToolPan,
    QgsLayoutViewToolZoom, QgsLayoutViewToolMoveItemContent,
    QgsLayoutViewToolAddItem, QgsLayoutViewToolAddNodeItem
)

qgs = QgsApplication([], False)
qgs.initQgis()

view = QgsLayoutView()
tools = [
    ("tool_select", QgsLayoutViewToolSelect(view)),
    ("tool_pan", QgsLayoutViewToolPan(view)),
    ("tool_zoom", QgsLayoutViewToolZoom(view)),
    ("tool_move_content", QgsLayoutViewToolMoveItemContent(view)),
    ("tool_add_item", QgsLayoutViewToolAddItem(view)),
    ("tool_add_node", QgsLayoutViewToolAddNodeItem(view))
]

for name, t in tools:
    methods = [m for m in dir(t) if "layout" in m.lower()]
    print(f"{name}: has setLayout? {hasattr(t, 'setLayout')} | layout-related methods: {methods}")

qgs.exitQgis()
