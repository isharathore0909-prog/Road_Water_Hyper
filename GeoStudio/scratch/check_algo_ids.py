import sys
import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
qgis_app = os.path.join(qgis_root, "apps", "qgis-ltr")
qgis_py = os.path.join(qgis_root, "apps", "Python312")

for p in [
    os.path.join(qgis_app, "python"),
    os.path.join(qgis_app, "python", "plugins"),
    os.path.join(qgis_py, "Lib", "site-packages"),
    os.path.join(qgis_py, "Lib"),
    r"M:\Geo Studio\GeoStudio\app",
    r"M:\Geo Studio\GeoStudio",
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from qgis.core import QgsApplication
QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], False)
app.initQgis()

from core.processing.algorithm_registry import AlgorithmRegistry

algo_ids = [
    "native:slope", "native:aspect", "native:hillshade", "native:roughness",
    "native:tpi", "native:twi", "native:curvature", "gdal:contour",
    "spatial:viewshed", "hydrology:fillsinks", "hydrology:flowdir",
    "hydrology:flowaccum", "hydrology:watershed", "satellite:ndvi",
    "satellite:evi", "satellite:ndwi", "satellite:ndbi", "satellite:nbr",
    "satellite:ndsi", "landsat:composites", "satellite:bandstack",
    "satellite:pca", "satellite:sam", "satellite:bandmath",
    "native:buffer", "native:clip", "native:intersection", "native:union",
    "native:difference", "native:dissolve", "native:centroids",
    "native:convexhull", "native:voronoi", "native:merge",
    "native:rasterstats", "native:reproject", "lidar:classify_roads",
    "lidar:road_centerline", "lidar:road_condition", "lidar:classify_ground",
    "lidar:classify_buildings", "lidar:extract_roofs", "lidar:classify_veg",
    "lidar:classify_powerlines", "lidar:vegetation_clearance",
    "lidar:thinning", "lidar:clip", "lidar:generate_dtm",
    "lidar:chm", "forestry:carbon_stock"
]

missing = []
found = []
for aid in algo_ids:
    algo = AlgorithmRegistry.find_algorithm(aid)
    if algo:
        found.append((aid, algo.name))
    else:
        missing.append(aid)

print(f"Total checked: {len(algo_ids)}")
print(f"Found in registry: {len(found)}")
print(f"Missing from registry: {len(missing)}")
if missing:
    print("MISSING ALGORITHMS:")
    for m in missing:
        print(f"  - {m}")

app.exitQgis()
