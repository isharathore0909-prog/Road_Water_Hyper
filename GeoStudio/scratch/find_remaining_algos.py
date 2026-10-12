import os, sys
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
qgs = QgsApplication([], False)
qgs.initQgis()
from processing.core.Processing import Processing
Processing.initialize()

for a in QgsApplication.processingRegistry().algorithms():
    for word in ["delaunay", "spatialjoin", "distancematrix", "nearest", "pointsinpoly"]:
        if word in a.id().lower():
            print(f"Match for {word}:", a.id())

qgs.exitQgis()
