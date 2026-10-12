# -*- coding: utf-8 -*-
"""
GeoStudio - Comprehensive Test Suite for Road & Transportation Engineering Engines:
1. Road Surface & Pavement Classification (ASPRS Class 11: Road Surface)
2. Road Centerlines, Curbs & Corridor Vector Alignment (GPKG)
3. Road Grade, Roughness & Overhead Vehicle Clearance Analysis (GPKG & Audit Report)
4. Processing Registry & Catalogs Verification
"""

import os
import sys
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
print("GeoStudio: Testing Road & Transportation Corridor LiDAR Engines")
print("=" * 70)

from core.lidar.road_extraction_engine import RoadExtractionEngine
from core.processing.algorithm_registry import AlgorithmRegistry

temp_dir = tempfile.mkdtemp()
print(f"Working temporary directory: {temp_dir}")

# -------------------------------------------------------------
# 1. Create Synthetic Corridor LiDAR Dataset
# -------------------------------------------------------------
# Corridor is along X axis: X from 0 to 200m, Y from -30 to +30m
# Road is located at Y between -4m and +4m (width = 8m)
# Elevation Z: base slope 2%, with steep segment (10%) between X=100 and X=140
print("\n[SETUP] Synthesizing 3D road corridor point cloud...")
np.random.seed(42)

xs = []
ys = []
zs = []
classes = []

# Generate road pavement points (dense, smooth, flat)
for x in np.linspace(0, 200, 300):
    for y in np.linspace(-3.8, 3.8, 12):
        z_base = 100.0 + (x * 0.02)
        if 100 <= x <= 140:
            z_base += (x - 100) * 0.08 # Steep grade segment
        # Very smooth surface (noise < 1.5 cm)
        z = z_base + np.random.normal(0, 0.012)
        xs.append(x)
        ys.append(y)
        zs.append(z)
        classes.append(2) # initially unclassified or ground

# Generate off-road terrain / ditch / grass points (rougher, outside road)
for x in np.linspace(0, 200, 150):
    for y in np.concatenate([np.linspace(-25, -5, 8), np.linspace(5, 25, 8)]):
        z_base = 100.0 + (x * 0.02)
        if 100 <= x <= 140:
            z_base += (x - 100) * 0.08
        # Rough terrain (roughness > 0.15 m)
        z = z_base + np.random.normal(0, 0.18) + (abs(y) * 0.05)
        xs.append(x)
        ys.append(y)
        zs.append(z)
        classes.append(1)

# Generate tree canopy / low-hanging branch points above road (clearance hazard)
# Obstacle 1: Tree limb hanging at 3.5m clearance (CRITICAL collision hazard < 4.0m) at X=50, Y=0
for _ in range(25):
    ox = 50.0 + np.random.uniform(-1.0, 1.0)
    oy = np.random.uniform(-2.0, 2.0)
    oz = 100.0 + (50.0 * 0.02) + 3.5 + np.random.uniform(-0.2, 0.2)
    xs.append(ox)
    ys.append(oy)
    zs.append(oz)
    classes.append(5) # high vegetation

# Obstacle 2: Warning overhead cable / limb at 4.4m clearance (< 4.8m) at X=120, Y=1
for _ in range(20):
    ox = 120.0 + np.random.uniform(-1.0, 1.0)
    oy = np.random.uniform(-1.5, 1.5)
    oz = 100.0 + (120.0 * 0.02) + (20 * 0.08) + 4.4 + np.random.uniform(-0.2, 0.2)
    xs.append(ox)
    ys.append(oy)
    zs.append(oz)
    classes.append(14)

test_las_path = os.path.join(temp_dir, "corridor_input.las")
header = laspy.LasHeader(point_format=3, version="1.4")
header.offsets = [0.0, 0.0, 100.0]
header.scales = [0.001, 0.001, 0.001]
las_synth = laspy.LasData(header)
las_synth.x = np.array(xs, dtype=np.float64)
las_synth.y = np.array(ys, dtype=np.float64)
las_synth.z = np.array(zs, dtype=np.float64)
las_synth.classification = np.array(classes, dtype=np.uint8)
las_synth.write(test_las_path)
print(f"  Synthesized {len(xs):,} points in {test_las_path}")

# -------------------------------------------------------------
# TEST 1: Classify Road Surface & Pavement (ASPRS Class 11)
# -------------------------------------------------------------
print("\n[TEST 1/3] Testing Road Surface & Pavement Classification (ASPRS 11)...")
out_las_path = os.path.join(temp_dir, "road_classified.las")
out_poly_path = os.path.join(temp_dir, "road_boundary.gpkg")

res_surf = RoadExtractionEngine.classify_road_surface(
    input_las_path=test_las_path,
    output_las_path=out_las_path,
    output_vector_path=out_poly_path,
    max_hag_m=0.35,
    min_planarity=0.60,
    max_roughness_m=0.08,
    min_verticality=0.85,
    min_corridor_area_m2=20.0,
    export_footprint_polygon=True
)

assert os.path.exists(out_las_path), "Output classified LAS was not created!"
assert res_surf["road_points_class_11"] > 500, f"Too few road points classified: {res_surf['road_points_class_11']}"
assert res_surf["estimated_pavement_area_m2"] > 500.0, "Pavement area is too small!"
assert os.path.exists(out_poly_path), "Road corridor polygon vector was not created!"

# Verify LAS file actually has Class 11
las_verify = laspy.read(out_las_path)
c11_count = np.sum(np.array(las_verify.classification) == 11)
assert c11_count == res_surf["road_points_class_11"], "Mismatch in Class 11 count in written LAS!"
print(f"  ✓ Road Surface Classification Passed: {c11_count:,} points classified as ASPRS 11 ({res_surf['road_points_pct']}%), Area = {res_surf['estimated_pavement_area_m2']:,.1f} m²")

# -------------------------------------------------------------
# TEST 2: Extract Road Centerlines, Curbs & Corridor Alignment
# -------------------------------------------------------------
print("\n[TEST 2/3] Testing Road Centerline, Curbs & Station Chainage Extraction...")
out_align_path = os.path.join(temp_dir, "road_alignment.gpkg")

res_corridor = RoadExtractionEngine.extract_road_corridor(
    input_source=out_las_path,
    output_vector_path=out_align_path,
    station_interval_m=25.0,
    corridor_search_step_m=5.0,
    detect_curbs=True
)

assert os.path.exists(out_align_path), "Road alignment vector GeoPackage not created!"
assert res_corridor["centerline_length_m"] > 150.0, f"Centerline length too short: {res_corridor['centerline_length_m']}"
assert 6.0 <= res_corridor["average_road_width_m"] <= 10.0, f"Average width unexpected: {res_corridor['average_road_width_m']}"
assert res_corridor["station_markers_count"] >= 7, f"Station count too low: {res_corridor['station_markers_count']}"
assert res_corridor["curb_lines_count"] == 2, f"Curb lines count unexpected: {res_corridor['curb_lines_count']}"

# Inspect GeoPackage layers
ds_chk = ogr.Open(out_align_path)
lyr_names = [ds_chk.GetLayer(i).GetName() for i in range(ds_chk.GetLayerCount())]
ds_chk = None
assert "road_centerline_3d" in lyr_names, "road_centerline_3d layer missing from GPKG!"
assert "road_curbs_3d" in lyr_names, "road_curbs_3d layer missing from GPKG!"
assert "road_stations_3d" in lyr_names, "road_stations_3d layer missing from GPKG!"
print(f"  ✓ Road Alignment Vector Passed: Centerline = {res_corridor['centerline_length_m']:.1f} m, Width = {res_corridor['average_road_width_m']:.1f} m, Stations = {res_corridor['station_markers_count']}, Curbs = {res_corridor['curb_lines_count']}")

# -------------------------------------------------------------
# TEST 3: Road Grade, Roughness & Overhead Clearance Analysis
# -------------------------------------------------------------
print("\n[TEST 3/3] Testing Road Grade, Roughness & Overhead Clearance Audit...")
out_hazards_path = os.path.join(temp_dir, "road_hazards.gpkg")

res_audit = RoadExtractionEngine.analyze_road_condition(
    road_centerline_source=out_align_path,
    lidar_source=test_las_path,
    output_vector_path=out_hazards_path,
    max_design_grade_pct=8.0,
    critical_grade_pct=12.0,
    vehicle_clearance_height_m=4.80,
    critical_clearance_height_m=4.00,
    corridor_width_m=8.0
)

assert os.path.exists(out_hazards_path), "Hazards vector layer not created!"
assert os.path.exists(res_audit["report_path"]), "Audit JSON report not created!"
assert res_audit["critical_clearance_count"] >= 1, "Failed to detect critical overhead collision strike (< 4.0m)!"
assert res_audit["warning_clearance_count"] >= 1, "Failed to detect warning overhead clearance encroachment (< 4.8m)!"
assert res_audit["steep_grade_count"] >= 1 or res_audit["max_grade_pct"] >= 8.0, "Failed to detect steep slope grade!"

print(f"  ✓ Road Condition Audit Passed: Critical Strikes = {res_audit['critical_clearance_count']}, Warning Encroachments = {res_audit['warning_clearance_count']}, Max Grade = {res_audit['max_grade_pct']:.1f}%, IRI Proxy = {res_audit['iri_proxy_m_km']:.2f} m/km")

# -------------------------------------------------------------
# TEST 4: Processing Registry & Catalogs Verification
# -------------------------------------------------------------
print("\n[TEST REGISTRY] Verifying Processing Registry & Catalogs for Road algorithms...")
algo_surf = AlgorithmRegistry.find_algorithm("lidar:classify_roads")
algo_corr = AlgorithmRegistry.find_algorithm("lidar:road_centerline")
algo_cond = AlgorithmRegistry.find_algorithm("lidar:road_condition")

assert algo_surf is not None, "lidar:classify_roads algorithm not found in registry!"
assert algo_corr is not None, "lidar:road_centerline algorithm not found in registry!"
assert algo_cond is not None, "lidar:road_condition algorithm not found in registry!"

# Test aliases
assert AlgorithmRegistry.find_algorithm("lidar:roads") == algo_surf
assert AlgorithmRegistry.find_algorithm("lidar:road") == algo_surf
assert AlgorithmRegistry.find_algorithm("lidar:road_surface") == algo_surf
assert AlgorithmRegistry.find_algorithm("lidar:curbs") == algo_corr
assert AlgorithmRegistry.find_algorithm("lidar:road_corridor") == algo_corr
assert AlgorithmRegistry.find_algorithm("lidar:road_grade") == algo_cond
assert AlgorithmRegistry.find_algorithm("lidar:road_clearance") == algo_cond

print("  ✓ All 3 Road algorithms and 7 aliases successfully registered in AlgorithmRegistry!")

# -------------------------------------------------------------
# TEST 5: Verify Split Modular Engine Classes
# -------------------------------------------------------------
print("\n[TEST MODULAR] Verifying direct imports from split engine files...")
from core.lidar.road_models import StationMarker, CorridorHazard, CorridorGeometryResult, ProcessingContext
from core.lidar.road_io import RoadSpatialReference, RoadVectorWriter, RoadDataLoader
from core.lidar.road_surface_engine import RoadSurfaceEngine, RoadGroundEstimator, RoadPavementClassifier
from core.lidar.road_corridor_engine import RoadCorridorEngine, RoadAlignmentTracer
from core.lidar.road_condition_engine import RoadConditionEngine, RoadCorridorAuditor

assert RoadSurfaceEngine.classify_road_surface is not None
assert RoadCorridorEngine.extract_road_corridor is not None
assert RoadConditionEngine.analyze_road_condition is not None
print("  ✓ All 5 modular files and component classes successfully verified!")

print("\n" + "=" * 70)
print("ALL ROAD & TRANSPORTATION LiDAR ENGINES PASSED 100% OF TESTS!")
print("=" * 70)
