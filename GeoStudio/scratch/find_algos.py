import os, sys
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
qgs = QgsApplication([], False)
qgs.initQgis()

from processing.core.Processing import Processing
Processing.initialize()
import processing
from qgis.core import QgsApplication

for a in QgsApplication.processingRegistry().algorithms():
    if "simplify" in a.id():
        print("Found simplify algo:", a.id())
    if "merge" in a.id():
        print("Found merge algo:", a.id())
    if "voronoi" in a.id():
        print("Found voronoi algo:", a.id())
    if "fix" in a.id():
        print("Found fix algo:", a.id())

qgs.exitQgis()
