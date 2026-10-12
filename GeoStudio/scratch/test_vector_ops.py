import os, sys
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY
)

qgs = QgsApplication([], False)
qgs.initQgis()
from processing.core.Processing import Processing
Processing.initialize()
import processing

poly = QgsVectorLayer("Polygon?crs=EPSG:4326", "Poly", "memory")
pr = poly.dataProvider()
f = QgsFeature()
f.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(0, 0), QgsPointXY(10, 0), QgsPointXY(10, 10), QgsPointXY(0, 10), QgsPointXY(0, 0)]]))
pr.addFeatures([f])

# Test simplify
res = processing.run("native:simplifygeometries", {"INPUT": poly, "METHOD": 0, "TOLERANCE": 0.5, "OUTPUT": "memory:"})
print("Simplify succeeded:", res["OUTPUT"].featureCount())

# Test voronoi
pts = QgsVectorLayer("Point?crs=EPSG:4326", "Pts", "memory")
pr_p = pts.dataProvider()
f1, f2, f3 = QgsFeature(), QgsFeature(), QgsFeature()
f1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
f2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(5, 5)))
f3.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(8, 2)))
pr_p.addFeatures([f1, f2, f3])

res_v = processing.run("native:voronoipolygons", {"INPUT": pts, "BUFFER": 20.0, "OUTPUT": "memory:"})
print("Voronoi succeeded:", res_v["OUTPUT"].featureCount())

# Test join attributes by location
res_j = processing.run("native:joinattributesbylocation", {"INPUT": poly, "JOIN": pts, "PREDICATE": [0], "OUTPUT": "memory:"})
print("Join succeeded:", res_j["OUTPUT"].featureCount())

qgs.exitQgis()
print("All mapped algorithms succeeded!")
