import os, sys
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import QgsApplication
qgs = QgsApplication([], False)
qgs.initQgis()
from processing.core.Processing import Processing
Processing.initialize()

for a in QgsApplication.processingRegistry().algorithms():
    if "join" in a.id().lower():
        print("Join algo:", a.id())

qgs.exitQgis()
