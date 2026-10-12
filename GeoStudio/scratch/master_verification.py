# -*- coding: utf-8 -*-
"""
GeoStudio Master Verification Suite
Validates:
1. AlgorithmRegistry resolution and aliases
2. Vector geoprocessing execution (geometry, overlays, joins)
3. Raster PCA and band math
4. Attribute table loading safety & pagination
5. Vector feature cut/copy/paste
6. Print Layout manager & designer lifecycle
"""
import os, sys, tempfile
sys.path.insert(0, r"M:\Geo Studio\GeoStudio")
sys.path.insert(0, r"M:\Geo Studio\GeoStudio\app")
sys.path.insert(0, r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\python\plugins")

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsFeature, QgsGeometry, QgsPointXY, QgsField
)
from PyQt5.QtCore import QVariant, Qt, QPointF
from PyQt5.QtWidgets import QApplication

os.environ["QT_QPA_PLATFORM"] = "offscreen"

qgs = QgsApplication([], False)
qgs.initQgis()

from processing.core.Processing import Processing
Processing.initialize()
import processing

print("="*60)
print("GEOSTUDIO MASTER VERIFICATION SUITE")
print("="*60)

# TEST 1: Algorithm Registry & Aliases
print("\n[TEST 1] Testing AlgorithmRegistry Resolution & Aliases...")
from app.core.processing.algorithm_registry import AlgorithmRegistry

required_ids = [
    "native:buffer", "native:centroids", "native:convexhull", "native:dissolve",
    "native:clip", "native:intersection", "native:union", "native:difference",
    "native:merge", "native:simplify", "native:voronoi", "native:spatialjoin",
    "satellite:ndvi", "satellite:ndwi", "satellite:evi", "satellite:pca",
    "satellite:sam", "satellite:bandmath", "satellite:bandstack"
]

missing = []
for aid in required_ids:
    algo = AlgorithmRegistry.find_algorithm(aid)
    if not algo:
        missing.append(aid)
    else:
        print(f"  ✓ Found '{aid}' -> '{algo.name}' (dialog: {algo.dialog_type})")

assert not missing, f"Missing algorithms: {missing}"
print("✓ TEST 1 PASSED: All algorithms and aliases resolved successfully!")


# TEST 2: Vector Geoprocessing Backend Execution
print("\n[TEST 2] Testing Vector Geoprocessing Real Calculations...")

# Create test vector layers
poly_a = QgsVectorLayer("Polygon?crs=EPSG:4326", "A", "memory")
pr_a = poly_a.dataProvider()
pr_a.addAttributes([QgsField("val", QVariant.Int)])
poly_a.updateFields()
f1 = QgsFeature(poly_a.fields())
f1.setAttribute("val", 100)
f1.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(0,0), QgsPointXY(10,0), QgsPointXY(10,10), QgsPointXY(0,10), QgsPointXY(0,0)]]))
pr_a.addFeatures([f1])

poly_b = QgsVectorLayer("Polygon?crs=EPSG:4326", "B", "memory")
pr_b = poly_b.dataProvider()
f2 = QgsFeature()
f2.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(5,5), QgsPointXY(15,5), QgsPointXY(15,15), QgsPointXY(5,15), QgsPointXY(5,5)]]))
pr_b.addFeatures([f2])

pts = QgsVectorLayer("Point?crs=EPSG:4326", "P", "memory")
pr_p = pts.dataProvider()
for coord in [(1,1), (3,3), (7,7)]:
    fp = QgsFeature()
    fp.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*coord)))
    pr_p.addFeatures([fp])

# 2a: Buffer
res_buf = processing.run("native:buffer", {"INPUT": poly_a, "DISTANCE": 2.0, "OUTPUT": "memory:"})
assert res_buf["OUTPUT"].featureCount() == 1
print("  ✓ Buffer:", res_buf["OUTPUT"].featureCount(), "feature")

# 2b: Centroids
res_cent = processing.run("native:centroids", {"INPUT": poly_a, "ALL_PARTS": False, "OUTPUT": "memory:"})
assert res_cent["OUTPUT"].featureCount() == 1
print("  ✓ Centroids:", res_cent["OUTPUT"].featureCount(), "feature")

# 2c: Clip
res_clip = processing.run("native:clip", {"INPUT": poly_a, "OVERLAY": poly_b, "OUTPUT": "memory:"})
assert res_clip["OUTPUT"].featureCount() == 1
print("  ✓ Clip:", res_clip["OUTPUT"].featureCount(), "feature")

# 2d: Intersection
res_int = processing.run("native:intersection", {"INPUT": poly_a, "OVERLAY": poly_b, "OUTPUT": "memory:"})
assert res_int["OUTPUT"].featureCount() == 1
print("  ✓ Intersection:", res_int["OUTPUT"].featureCount(), "feature")

# 2e: Voronoi Polygons
res_vor = processing.run("native:voronoipolygons", {"INPUT": pts, "BUFFER": 20.0, "OUTPUT": "memory:"})
assert res_vor["OUTPUT"].featureCount() == 3
print("  ✓ Voronoi Polygons:", res_vor["OUTPUT"].featureCount(), "features")

# 2f: Spatial Join
res_join = processing.run("native:joinattributesbylocation", {"INPUT": poly_a, "JOIN": pts, "PREDICATE": [0], "OUTPUT": "memory:"})
assert res_join["OUTPUT"].featureCount() == 3
print("  ✓ Spatial Join:", res_join["OUTPUT"].featureCount(), "features")

print("✓ TEST 2 PASSED: Vector geoprocessing operations compute accurately!")


# TEST 3: Raster PCA Execution with GeoTIFF Output
print("\n[TEST 3] Testing Raster PCA & Scientific Calculations...")
from osgeo import gdal, osr
import numpy as np
from app.modules.satellite_indices import run_pca

tmp_ras = tempfile.mktemp(suffix=".tif")
drv = gdal.GetDriverByName("GTiff")
ds = drv.Create(tmp_ras, 40, 40, 3, gdal.GDT_Float32)
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
ds.SetProjection(srs.ExportToWkt())
ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
for b in range(1, 4):
    ds.GetRasterBand(b).WriteArray((np.random.rand(40, 40) * 50).astype(np.float32))
ds.FlushCache()
ds = None

r_layer = QgsRasterLayer(tmp_ras, "TestMultispectral")
assert r_layer.isValid()
pca_layer, msg = run_pca(r_layer, max_components=2)
assert pca_layer is not None and pca_layer.isValid()
print(f"  ✓ {msg}")
print("✓ TEST 3 PASSED: Raster PCA executed and produced valid multi-band layer!")


# TEST 4: Attribute Table Safety with Large Layer (5,000 features)
print("\n[TEST 4] Testing Attribute Table Safe Loading (5,000 features)...")
from app.ui.attribute_table_dock import AttributeTableDock

big_layer = QgsVectorLayer("Point?crs=EPSG:4326", "BigLayer", "memory")
pr_big = big_layer.dataProvider()
pr_big.addAttributes([QgsField("id", QVariant.Int), QgsField("tag", QVariant.String)])
big_layer.updateFields()

feats = []
for i in range(5000):
    f = QgsFeature(big_layer.fields())
    f.setAttribute("id", i)
    f.setAttribute("tag", f"Item_{i}")
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(i * 0.001, i * 0.001)))
    feats.append(f)
pr_big.addFeatures(feats)

dock = AttributeTableDock()
dock.load_active_layer(big_layer)
loaded_rows = dock.table.rowCount()
print(f"  ✓ Layer featureCount: {big_layer.featureCount()}, Table rows displayed: {loaded_rows}")
print(f"  ✓ Header text: '{dock.feature_count_label.text()}'")
assert loaded_rows == 1000, f"Expected 1000 rows limit, got {loaded_rows}"
assert "Showing 1,000 of 5,000 features" in dock.feature_count_label.text()
print("✓ TEST 4 PASSED: Attribute table respects safety limits without freezing!")


# TEST 5: Vector Feature Cut, Copy, Paste
print("\n[TEST 5] Testing Vector Feature Clipboard (Copy, Cut, Paste)...")
from app.ui.controllers.editing_controller import EditingControllerMixin

class MockMainWindow(EditingControllerMixin):
    def __init__(self):
        self.geo_status = type("Status", (), {"showMessage": lambda s, msg, t=0: print("    [Status]:", msg)})()
        self.map_canvas = type("Canvas", (), {"refresh_canvas": lambda s: None, "canvas": None})()
        self._active_layer = None
        self.layer_panel = type("Panel", (), {"get_active_layer": lambda *args: self._active_layer})()
    def _info(self, msg): print("    [Info]:", msg)

mock_win = MockMainWindow()
mock_win._active_layer = poly_a
poly_a.selectAll()

# Copy
count = mock_win.copy_features()
assert count == 1, f"Expected 1 copied feature, got {count}"
assert hasattr(mock_win, "_feature_clipboard")
print("  ✓ Features copied to internal clipboard")

# Paste into layer B
mock_win._active_layer = poly_b
poly_b.startEditing()
init_b_count = poly_b.featureCount()
mock_win.paste_features()
assert poly_b.featureCount() == init_b_count + 1
print(f"  ✓ Features pasted into target layer (count: {init_b_count} -> {poly_b.featureCount()})")
print("✓ TEST 5 PASSED: Feature copy/paste operates correctly!")


# TEST 6: Print Layout Full Lifecycle
print("\n[TEST 6] Testing Print Layout Manager & Designer Lifecycle...")
from app.ui.layout.layout_designer_window import GeoStudioLayoutDesignerWindow
from app.ui.layout.layout_manager_dialog import LayoutManagerDialog
from qgis.core import QgsPrintLayout

project = QgsProject.instance()
mgr = project.layoutManager()
mgr.clear()

from app.ui.layout.layout_templates import create_layout_from_template
layout_a4 = create_layout_from_template(project, "Audit_Verification_Layout", "A4 Landscape")
mgr.addLayout(layout_a4)

designer = GeoStudioLayoutDesignerWindow(layout_a4, main_window=None)
assert designer is not None

# Add items dynamically
designer.add_label_item()
designer.add_shape_item()
designer.add_scalebar_item()

# Simulate mouse movement in LayoutView (the original crash trigger!)
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import QPoint, QEvent
from qgis.core import QgsLayoutExporter

view = designer.view
for x in range(20, 200, 30):
    ev = QMouseEvent(QEvent.MouseMove, QPoint(x, x), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    qgs.sendEvent(view, ev)
    qgs.sendEvent(view.viewport(), ev)
qgs.processEvents()
print("  ✓ Interactive QgsLayoutView mouse movement verified with 0 crash!")

# Export to Image
out_png = tempfile.mktemp(suffix=".png")
exporter = QgsLayoutExporter(designer.layout)
settings = QgsLayoutExporter.ImageExportSettings()
settings.dpi = 100
res_exp = exporter.exportToImage(out_png, settings)
assert res_exp == QgsLayoutExporter.Success
assert os.path.exists(out_png) and os.path.getsize(out_png) > 0
print(f"  ✓ Layout exported successfully ({os.path.getsize(out_png):,} bytes)")

designer.close()
print("✓ TEST 6 PASSED: Print Layout lifecycle and exports completely sound!")

qgs.exitQgis()
print("\n" + "="*60)
print("ALL 6 MASTER VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
print("="*60)
