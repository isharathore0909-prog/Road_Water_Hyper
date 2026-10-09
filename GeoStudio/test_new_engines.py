# -*- coding: utf-8 -*-
"""
GeoStudio - Comprehensive Test Suite for 4 New Engines:
1. Aboveground Biomass (AGB) & Carbon Stock Estimation Engine
2. Powerline and Transmission Tower Classification Engine
3. Vegetation Clearance & Danger Tree Buffer Engine
4. Building Planar Roof Extraction Engine
"""

import os
import sys
import math
import tempfile
import numpy as np
from osgeo import gdal, ogr, osr
import laspy

QGIS_ROOT = r"C:\Program Files\QGIS 3.40.14"
QGIS_APP  = os.path.join(QGIS_ROOT, "apps", "qgis-ltr")
QGIS_PY   = os.path.join(QGIS_ROOT, "apps", "Python312")

os.environ["PROJ_LIB"] = os.path.join(QGIS_ROOT, "share", "proj")
os.environ["PROJ_DATA"] = os.path.join(QGIS_ROOT, "share", "proj")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

for p in [
    os.path.join(QGIS_APP, "python"),
    os.path.join(QGIS_APP, "python", "plugins"),
    os.path.join(QGIS_PY, "Lib", "site-packages"),
    os.path.join(QGIS_PY, "Lib"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

print("=" * 70)
print("GeoStudio: Testing 4 Advanced Engines")
print("=" * 70)

# -------------------------------------------------------------
# 1. Test Aboveground Biomass (AGB) & Carbon Stock Estimation
# -------------------------------------------------------------
print("\n[TEST 1/4] Aboveground Biomass (AGB) & Carbon Stock Engine...")
from core.forestry.agb_carbon_engine import AGBCarbonEngine
from core.forestry.tree_metrics_engine import TreeMetricsEngine

temp_dir = tempfile.mkdtemp()
chm_test_path = os.path.join(temp_dir, "test_chm.tif")
agb_raster_out = os.path.join(temp_dir, "test_agb_carbon.tif")

# Create synthetic CHM GeoTIFF (50x50 pixels, pixel size 1.0m)
drv = gdal.GetDriverByName("GTiff")
ds = drv.Create(chm_test_path, 50, 50, 1, gdal.GDT_Float32)
ds.SetGeoTransform([500000.0, 1.0, 0.0, 4000000.0, 0.0, -1.0])
srs = osr.SpatialReference()
srs.ImportFromEPSG(32632)
ds.SetProjection(srs.ExportToWkt())

chm_data = np.zeros((50, 50), dtype=np.float32)
# Add some tree canopy heights (5m to 25m)
chm_data[10:40, 10:40] = np.random.uniform(8.0, 24.0, size=(30, 30))
band = ds.GetRasterBand(1)
band.WriteArray(chm_data)
band.SetNoDataValue(-9999.0)
ds.FlushCache()
ds = None

print("  Testing CHM Raster AGB & Carbon estimation...")
res_chm = AGBCarbonEngine.estimate_from_chm(
    chm_path=chm_test_path,
    output_raster_path=agb_raster_out,
    preset="temperate_lefsky",
    wood_density=0.52,
    root_to_shoot_ratio=0.235,
    carbon_fraction=0.47,
    carbon_price_usd=25.0
)
assert os.path.exists(agb_raster_out), "Output AGB raster was not created!"
assert res_chm["total_carbon_stock_tonnes_C"] > 0, "Carbon stock is 0!"
assert res_chm["total_co2_equivalent_tonnes_CO2e"] > 0, "CO2e is 0!"
print(f"  ✓ Raster Mode Passed: Total Carbon = {res_chm['total_carbon_stock_tonnes_C']:.2f} tonnes C, Economic Value = ${res_chm['estimated_economic_value_usd']:,.2f}")

# Test Vector Mode for Trees
trees_test_path = os.path.join(temp_dir, "test_trees.gpkg")
trees_out_path = os.path.join(temp_dir, "test_trees_carbon.gpkg")
drv_ogr = ogr.GetDriverByName("GPKG")
ds_v = drv_ogr.CreateDataSource(trees_test_path)
lyr_v = ds_v.CreateLayer("trees", srs, ogr.wkbPoint)
lyr_v.CreateField(ogr.FieldDefn("Tree_ID", ogr.OFTInteger))
lyr_v.CreateField(ogr.FieldDefn("Height_m", ogr.OFTReal))
lyr_v.CreateField(ogr.FieldDefn("Crown_Diam_m", ogr.OFTReal))

for tid in range(1, 21):
    f = ogr.Feature(lyr_v.GetLayerDefn())
    f.SetField("Tree_ID", tid)
    h = 10.0 + tid * 0.8
    f.SetField("Height_m", h)
    f.SetField("Crown_Diam_m", h * 0.3)
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AddPoint_2D(500010.0 + tid * 1.5, 3999980.0 + tid * 1.2)
    f.SetGeometry(pt)
    lyr_v.CreateFeature(f)
ds_v.FlushCache()
ds_v = None

print("  Testing Vector Trees AGB & Carbon estimation...")
res_vec = AGBCarbonEngine.estimate_from_trees_vector(
    trees_vector_path=trees_test_path,
    output_vector_path=trees_out_path,
    forest_preset="conifer",
    carbon_price_usd=30.0
)
assert os.path.exists(trees_out_path), "Output carbon vector was not created!"
assert res_vec["total_carbon_stock_tonnes_C"] > 0
print(f"  ✓ Vector Mode Passed: {res_vec['total_trees']} trees, Total Biomass = {res_vec['total_biomass_Mg']:.2f} Mg")

# -------------------------------------------------------------
# 2. Test Powerline & Transmission Tower Classification
# -------------------------------------------------------------
print("\n[TEST 2/4] Powerline & Transmission Tower Classification Engine...")
from core.lidar.powerline_classifier import PowerlineClassifier

test_las_path = os.path.join(temp_dir, "test_corridor.las")
hdr = laspy.LasHeader(point_format=3, version="1.4")
hdr.offsets = [500000.0, 4000000.0, 100.0]
hdr.scales = [0.01, 0.01, 0.01]
las_obj = laspy.LasData(hdr)

# Synthesize corridor: Ground (Class 2) + Conductors (Linear) + Tower (Vertical)
num_pts = 1200
xs = np.random.uniform(500000.0, 500100.0, num_pts)
ys = np.random.uniform(4000000.0, 4000050.0, num_pts)
zs = np.full(num_pts, 100.0) # ground level
classes = np.full(num_pts, 2, dtype=np.uint8)

# Add conductor wire line (spanning across X from 500010 to 500090 at Y=4000025, Z=120m)
wire_x = np.linspace(500010.0, 500090.0, 150)
wire_y = np.full(150, 4000025.0) + np.random.normal(0, 0.02, 150)
wire_z = 122.0 - 2.0 * np.sin(np.linspace(0, np.pi, 150)) # catenary sag
xs = np.append(xs, wire_x)
ys = np.append(ys, wire_y)
zs = np.append(zs, wire_z)
classes = np.append(classes, np.full(150, 1, dtype=np.uint8)) # unclassified

# Add transmission tower at (500050, 4000025) spanning Z=100 to 125m
tower_z = np.linspace(101.0, 125.0, 80)
tower_x = 500050.0 + np.random.uniform(-1.5, 1.5, 80)
tower_y = 4000025.0 + np.random.uniform(-1.5, 1.5, 80)
xs = np.append(xs, tower_x)
ys = np.append(ys, tower_y)
zs = np.append(zs, tower_z)
classes = np.append(classes, np.full(80, 1, dtype=np.uint8))

las_obj.x = xs
las_obj.y = ys
las_obj.z = zs
las_obj.classification = classes
las_obj.write(test_las_path)

out_las_path = os.path.join(temp_dir, "test_classified_powerline.las")
res_pl = PowerlineClassifier.classify_corridor(
    input_las_path=test_las_path,
    output_las_path=out_las_path,
    min_wire_height_m=4.0,
    min_linearity=0.65,
    min_tower_height_m=10.0,
    export_vectors=True
)

assert os.path.exists(out_las_path), "Classified LAS output was not created!"
assert res_pl["wire_points_class_14"] > 0, "No wire points classified!"
assert res_pl["transmission_towers_count"] > 0, "No transmission towers detected!"
print(f"  ✓ Powerline Classifier Passed: Wire Points (14) = {res_pl['wire_points_class_14']}, Towers (15) = {res_pl['transmission_towers_count']}")

# -------------------------------------------------------------
# 3. Test Vegetation Clearance & Danger Tree Buffer Engine
# -------------------------------------------------------------
print("\n[TEST 3/4] Vegetation Clearance & Danger Tree Buffer Engine...")
from core.lidar.vegetation_clearance_engine import VegetationClearanceEngine

# Wire: vector line at Y=4000025, Z=120m
wire_vec_path = os.path.join(temp_dir, "test_wire_line.gpkg")
ds_w = drv_ogr.CreateDataSource(wire_vec_path)
lyr_w = ds_w.CreateLayer("wire", srs, ogr.wkbLineString25D)
line = ogr.Geometry(ogr.wkbLineString25D)
line.AddPoint(500000.0, 4000025.0, 120.0)
line.AddPoint(500100.0, 4000025.0, 120.0)
f_w = ogr.Feature(lyr_w.GetLayerDefn())
f_w.SetGeometry(line)
lyr_w.CreateFeature(f_w)
ds_w.FlushCache()
ds_w = None

# Trees: Tree 1 is 2m away (CRITICAL flashover), Tree 2 is 10m away with H=15m (DANGER TREE fall hazard)
trees_hazard_path = os.path.join(temp_dir, "test_trees_corridor.gpkg")
ds_th = drv_ogr.CreateDataSource(trees_hazard_path)
lyr_th = ds_th.CreateLayer("trees", srs, ogr.wkbPoint25D)
lyr_th.CreateField(ogr.FieldDefn("Tree_ID", ogr.OFTInteger))
lyr_th.CreateField(ogr.FieldDefn("Height_m", ogr.OFTReal))

# Tree 1: directly encroaching (Y = 4000026.0 -> 1m from wire, apex Z = 119m)
f1 = ogr.Feature(lyr_th.GetLayerDefn())
f1.SetField("Tree_ID", 1)
f1.SetField("Height_m", 19.0)
pt1 = ogr.Geometry(ogr.wkbPoint25D)
pt1.AddPoint(500030.0, 4000026.0, 119.0)
f1.SetGeometry(pt1)
lyr_th.CreateFeature(f1)

# Tree 2: 8m away horizontally, height = 14m -> strikes line if felled (Danger Tree!)
f2 = ogr.Feature(lyr_th.GetLayerDefn())
f2.SetField("Tree_ID", 2)
f2.SetField("Height_m", 14.0)
pt2 = ogr.Geometry(ogr.wkbPoint25D)
pt2.AddPoint(500060.0, 4000033.0, 114.0)
f2.SetGeometry(pt2)
lyr_th.CreateFeature(f2)
ds_th.FlushCache()
ds_th = None

out_hazard_path = os.path.join(temp_dir, "test_danger_trees_out.gpkg")
res_vc = VegetationClearanceEngine.analyze_corridor(
    conductors_source=wire_vec_path,
    vegetation_source=trees_hazard_path,
    output_vector_path=out_hazard_path,
    critical_dist_m=3.0,
    warning_dist_m=5.0,
    generate_corridor_buffers=True
)

assert os.path.exists(out_hazard_path), "Danger tree output vector not created!"
assert res_vc["critical_encroachments_count"] >= 1, "Expected critical encroachment not detected!"
assert res_vc["total_danger_trees_count"] >= 1, "Expected fall-in danger tree not detected!"
print(f"  ✓ Vegetation Clearance Passed: Critical Violations = {res_vc['critical_encroachments_count']}, Fall-In Danger Trees = {res_vc['total_danger_trees_count']}")

# -------------------------------------------------------------
# 4. Test Building Planar Roof Extraction Engine
# -------------------------------------------------------------
print("\n[TEST 4/4] Building Planar Roof Extraction Engine...")
from core.lidar.building_roof_engine import BuildingRoofEngine

test_roof_las = os.path.join(temp_dir, "test_roof.las")
hdr_r = laspy.LasHeader(point_format=3, version="1.4")
hdr_r.offsets = [500000.0, 4000000.0, 100.0]
hdr_r.scales = [0.01, 0.01, 0.01]
las_roof = laspy.LasData(hdr_r)

# Synthesize a building with two pitched roof facets (Gable roof: North slope + South slope)
# Facet 1: Pitch 30°, facing South (ideal solar!)
# Facet 2: Pitch 30°, facing North
gx1, gy1 = np.meshgrid(np.linspace(500020, 500035, 15), np.linspace(4000010, 4000020, 15))
gz1 = 110.0 + (gy1 - 4000010.0) * math.tan(math.radians(30)) # sloping up towards north

gx2, gy2 = np.meshgrid(np.linspace(500020, 500035, 15), np.linspace(4000020, 4000030, 15))
gz2 = 110.0 + (4000030.0 - gy2) * math.tan(math.radians(30))

rx = np.concatenate([gx1.flatten(), gx2.flatten()])
ry = np.concatenate([gy1.flatten(), gy2.flatten()])
rz = np.concatenate([gz1.flatten(), gz2.flatten()])
r_class = np.full(len(rx), 6, dtype=np.uint8) # Class 6 Building

las_roof.x = rx
las_roof.y = ry
las_roof.z = rz
las_roof.classification = r_class
las_roof.write(test_roof_las)

out_roof_vec = os.path.join(temp_dir, "test_roofs_out.gpkg")
res_rf = BuildingRoofEngine.extract_roof_facets(
    input_las_path=test_roof_las,
    output_vector_path=out_roof_vec,
    min_facet_area_m2=2.0,
    distance_threshold_m=0.25,
    max_angle_dev_deg=20.0,
    min_inliers_count=15
)

assert os.path.exists(out_roof_vec), "Roof vector output not created!"
assert res_rf["extracted_facets_count"] >= 1, "No roof facets extracted!"
assert res_rf["total_roof_3d_area_m2"] > 0
print(f"  ✓ Roof Extraction Passed: {res_rf['extracted_facets_count']} facets, Surface Area = {res_rf['total_roof_3d_area_m2']:.1f} m², Solar Viable = {res_rf['optimal_pv_solar_area_m2']:.1f} m²")

# -------------------------------------------------------------
# 5. Test Registry & Catalog Discovery
# -------------------------------------------------------------
print("\n[TEST REGISTRY] Verifying Processing Registry & Catalogs...")
from core.processing.algorithm_registry import AlgorithmRegistry

algo_carbon = AlgorithmRegistry.find_algorithm("forestry:carbon_stock")
algo_pl = AlgorithmRegistry.find_algorithm("lidar:classify_powerlines")
algo_vc = AlgorithmRegistry.find_algorithm("lidar:vegetation_clearance")
algo_rf = AlgorithmRegistry.find_algorithm("lidar:extract_roofs")

assert algo_carbon is not None, "forestry:carbon_stock algorithm not found in registry!"
assert algo_pl is not None, "lidar:classify_powerlines algorithm not found in registry!"
assert algo_vc is not None, "lidar:vegetation_clearance algorithm not found in registry!"
assert algo_rf is not None, "lidar:extract_roofs algorithm not found in registry!"

# Test aliases
assert AlgorithmRegistry.find_algorithm("forestry:agb") is not None
assert AlgorithmRegistry.find_algorithm("lidar:powerlines") is not None
assert AlgorithmRegistry.find_algorithm("lidar:danger_tree") is not None
assert AlgorithmRegistry.find_algorithm("lidar:building_roofs") is not None

print("  ✓ All 4 algorithms and aliases successfully registered in AlgorithmRegistry!")

print("\n" + "=" * 70)
print("ALL 4 ADVANCED ENGINES PASSED 100% OF TESTS AND ARE FULLY OPERATIONAL!")
print("=" * 70)
