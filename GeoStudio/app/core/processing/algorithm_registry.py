# -*- coding: utf-8 -*-
"""
GeoStudio - Central Algorithm Registry & QGIS Hierarchy Schema
Defines the complete hierarchical categorization and parameter schema for all algorithms.
"""

from typing import List, Dict, Any, Optional


class AlgorithmDefinition:
    """Metadata descriptor for a single processing algorithm."""
    def __init__(
        self,
        name: str,
        algo_id: str,
        category: str,
        subcategory: str,
        description: str,
        dialog_type: str,
        supports_gpu: bool = False,
        requires_halo: bool = False,
        halo_size: int = 0
    ):
        self.name = name
        self.algo_id = algo_id
        self.category = category
        self.subcategory = subcategory
        self.description = description
        self.dialog_type = dialog_type
        self.supports_gpu = supports_gpu
        self.requires_halo = requires_halo
        self.halo_size = halo_size


class AlgorithmRegistry:
    """Central catalog of all processing algorithms organized into hierarchical categories."""

    HIERARCHY: List[Dict[str, Any]] = [
        # ── 1. 🛰️ LANDSAT & SATELLITE SUITE (ENVI & LANDSAT) ───
        {
            "category": "🛰 Landsat & Remote Sensing",
            "subcategories": [
                {
                    "name": "Landsat Workflows",
                    "items": [
                        AlgorithmDefinition("Landsat Metadata & Auto-Calibration (MTL.txt)", "landsat:mtl_ingest", "Landsat & Remote Sensing", "Landsat Workflows", "Parses MTL.txt metadata and performs automated DN to TOA Radiance & Reflectance conversion with sun angle correction.", "landsat_mtl", supports_gpu=True),
                        AlgorithmDefinition("Land Surface Temperature (LST)", "landsat:lst", "Landsat & Remote Sensing", "Landsat Workflows", "Computes Brightness Temperature & LST in Celsius/Kelvin from Landsat thermal bands (B10/B11 or B6) with FVC emissivity correction.", "landsat_lst", supports_gpu=True),
                        AlgorithmDefinition("Landsat 7 SLC-Off Gap Fill", "landsat:slc_off", "Landsat & Remote Sensing", "Landsat Workflows", "Recovers scan line corrector (SLC-off) data gaps using local focal histogram matching.", "landsat_generic", supports_gpu=True),
                        AlgorithmDefinition("Landsat QA Pixel Cloud & Shadow Mask", "landsat:cloud_mask", "Landsat & Remote Sensing", "Landsat Workflows", "Decodes QA_PIXEL bitmask to generate transparent masks for clouds, shadows, cirrus, snow, and water.", "landsat_generic", supports_gpu=True),
                        AlgorithmDefinition("Landsat RGB Composite Presets", "landsat:composites", "Landsat & Remote Sensing", "Landsat Workflows", "One-click presets for Natural Color (4-3-2), Color Infrared (5-4-3), Agriculture (6-5-2), and Geology (7-6-4).", "sat_composite", supports_gpu=True),
                    ]
                },
                {
                    "name": "Spectral Indices Studio",
                    "items": [
                        AlgorithmDefinition("NDVI (Vegetation Index)", "satellite:ndvi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red)", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("NDWI / MNDWI (Water Index)", "satellite:ndwi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Normalized Difference Water Index: (Green - NIR) / (Green + NIR) and Modified NDWI.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("EVI (Enhanced Vegetation)", "satellite:evi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Enhanced Vegetation Index with atmospheric resistance & soil background adjustments.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("SAVI (Soil Adjusted Vegetation)", "satellite:savi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Soil-Adjusted Vegetation Index for arid environments with canopy background factor L.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("NBR (Normalized Burn Ratio)", "satellite:nbr", "Landsat & Remote Sensing", "Spectral Indices Studio", "Burn severity index: (NIR - SWIR2) / (NIR + SWIR2) for wildfire impact assessment.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("NDBI (Built-Up Index)", "satellite:ndbi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Normalized Difference Built-up Index: (SWIR1 - NIR) / (SWIR1 + NIR) for urban mapping.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("NDSI (Snow Index)", "satellite:ndsi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Normalized Difference Snow Index: (Green - SWIR1) / (Green + SWIR1) for cryosphere monitoring.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("BSI (Bare Soil Index)", "satellite:bsi", "Landsat & Remote Sensing", "Spectral Indices Studio", "Bare Soil Index combining Blue, Red, NIR, and SWIR bands for soil exposure analysis.", "spectral_index", supports_gpu=True),
                    ]
                },
                {
                    "name": "Band Math & Operations",
                    "items": [
                        AlgorithmDefinition("Band Math Calculator", "satellite:bandmath", "Landsat & Remote Sensing", "Band Operations", "Multi-band mathematical expression calculator for satellite raster cubes.", "raster_calc", supports_gpu=True),
                        AlgorithmDefinition("Band Stacking (Layer Stacking)", "satellite:bandstack", "Landsat & Remote Sensing", "Band Operations", "Merges single-band GeoTIFFs into a multi-band hyperspectral/multispectral cube.", "sat_composite", supports_gpu=False),
                        AlgorithmDefinition("Pansharpening (Gram-Schmidt / Brovey)", "satellite:pansharpen", "Landsat & Remote Sensing", "Band Operations", "High-resolution panchromatic sharpening fusing 30m bands with 15m Band 8.", "sat_composite", supports_gpu=True),
                        AlgorithmDefinition("Histogram Equalization & Contrast", "satellite:histeq", "Landsat & Remote Sensing", "Band Operations", "Adaptive contrast stretch, linear 2%, and histogram equalization.", "sat_composite", supports_gpu=True),
                    ]
                },
                {
                    "name": "Image Classification & ML",
                    "items": [
                        AlgorithmDefinition("Random Forest Classifier", "satellite:rf_classify", "Landsat & Remote Sensing", "Image Classification & ML", "Supervised land cover classification with ensemble random decision forests.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("Support Vector Machine (SVM)", "satellite:svm", "Landsat & Remote Sensing", "Image Classification & ML", "Supervised kernel-based hyperplane classifier for complex multi-class boundaries.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("K-Means Clustering", "satellite:kmeans", "Landsat & Remote Sensing", "Image Classification & ML", "Unsupervised spectral clustering into N distinct spectral classes.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("ISODATA Clustering", "satellite:isodata", "Landsat & Remote Sensing", "Image Classification & ML", "Self-organizing iterative clustering with automated class split and merge.", "spectral_index", supports_gpu=True),
                        AlgorithmDefinition("SAM (Spectral Angle Mapper)", "satellite:sam", "Landsat & Remote Sensing", "Image Classification & ML", "N-dimensional spectral angle classification against reference endmember signatures.", "spectral_index", supports_gpu=True),
                    ]
                },
                {
                    "name": "Hyperspectral & Spectral Profiling",
                    "items": [
                        AlgorithmDefinition("Interactive Spectral Profile", "satellite:spectral", "Landsat & Remote Sensing", "Hyperspectral", "Drill-down tool plotting pixel reflectance spectrum curves across all wavelengths.", "sat_spectral", supports_gpu=False),
                        AlgorithmDefinition("Principal Component Analysis (PCA)", "satellite:pca", "Landsat & Remote Sensing", "Hyperspectral", "Decorrelates hyperspectral bands to extract principal variance axes.", "sat_pca", supports_gpu=True),
                        AlgorithmDefinition("Endmember Extraction (PPI / N-FINDR)", "satellite:endmember", "Landsat & Remote Sensing", "Hyperspectral", "Finds purest spectral endmembers for linear spectral unmixing.", "sat_pca", supports_gpu=True),
                    ]
                }
            ]
        },

        # ── 2. 🏔️ TERRAIN & EARTHWORKS (GLOBAL MAPPER) ───────────
        {
            "category": "🏔 Terrain & Global Mapper Suite",
            "subcategories": [
                {
                    "name": "Elevation & Profiling",
                    "items": [
                        AlgorithmDefinition("Elevation Profile & Cross-Section", "terrain:elevation_profile", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Interactive polyline terrain slicing with real-time elevation profile, slope, and cross-section graphs.", "terrain_profile", supports_gpu=True),
                        AlgorithmDefinition("Slope", "native:slope", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Calculates terrain steepness (degrees/percent) using Horn's 3x3 algorithm.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("Aspect", "native:aspect", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Calculates compass direction of terrain slopes (0-360 degrees).", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("Hillshade", "native:hillshade", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Generates shaded relief with multi-directional solar azimuth and altitude.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("TRI (Terrain Ruggedness Index)", "native:roughness", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Quantifies topographic roughness based on elevation variance.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("TPI (Topographic Position Index)", "native:tpi", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Measures elevation relative to surrounding neighborhood (ridges vs valleys).", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("TWI (Topographic Wetness Index)", "native:twi", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Predicts soil moisture accumulation and drainage saturation zones.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("Curvature (Profile & Planform)", "native:curvature", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Calculates acceleration/deceleration and convergence of water flow.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("DEM Symbology & 3D Relief", "native:dem_symbology", "Terrain & Global Mapper Suite", "Elevation & Profiling", "Global Mapper and ArcGIS style elevation color ramp styler with hillshade blending.", "dem_dialog", supports_gpu=True),
                    ]
                },
                {
                    "name": "Earthworks & Volumetrics",
                    "items": [
                        AlgorithmDefinition("Cut & Fill Earthwork Volume", "terrain:cut_fill", "Terrain & Global Mapper Suite", "Earthworks & Volumetrics", "Calculates net cut and fill volumes between a DEM and a horizontal plane or between two temporal DEM surfaces.", "terrain_cutfill", supports_gpu=True),
                        AlgorithmDefinition("Flood & Inundation Simulator", "terrain:flood_sim", "Terrain & Global Mapper Suite", "Earthworks & Volumetrics", "Simulates dynamic water level rise over DEMs with catchment area and flooded volume estimation.", "terrain_flood", supports_gpu=True),
                        AlgorithmDefinition("Contours & Isolines", "gdal:contour", "Terrain & Global Mapper Suite", "Earthworks & Volumetrics", "Extracts elevation contour isolines with customizable interval, index lines, and smoothing.", "raster_contours", supports_gpu=False),
                    ]
                },
                {
                    "name": "Georeferencing & Rectification",
                    "items": [
                        AlgorithmDefinition("Image Rectifier & GCP Georeferencer", "terrain:georeference", "Terrain & Global Mapper Suite", "Georeferencing", "Interactive Ground Control Point (GCP) alignment with Affine, Polynomial, and Thin Plate Spline warping.", "terrain_georef", supports_gpu=False),
                        AlgorithmDefinition("Clip Raster by Extent/Polygon", "gdal:clipraster", "Terrain & Global Mapper Suite", "Georeferencing", "Clips elevation rasters using bounding boxes or vector polygon masks.", "raster_terrain", supports_gpu=True),
                    ]
                }
            ]
        },

        # ── 3. 📐 SPATIAL & HYDROLOGY ANALYST (ARCGIS) ─────────
        {
            "category": "📐 Spatial & Hydrology Analyst",
            "subcategories": [
                {
                    "name": "Hydrological Modeling",
                    "items": [
                        AlgorithmDefinition("Fill Sinks (Depressions)", "hydrology:fillsinks", "Spatial & Hydrology Analyst", "Hydrological Modeling", "Fills digital elevation model depressions and sinks to establish continuous flow paths.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Flow Direction (D8 / D-Infinity)", "hydrology:flowdir", "Spatial & Hydrology Analyst", "Hydrological Modeling", "Calculates steepest slope flow direction per cell towards neighbor cells.", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                        AlgorithmDefinition("Flow Accumulation", "hydrology:flowaccum", "Spatial & Hydrology Analyst", "Hydrological Modeling", "Computes total upslope drainage area contributing to each cell.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Stream Network & Order (Strahler)", "hydrology:stream_network", "Spatial & Hydrology Analyst", "Hydrological Modeling", "Extracts hierarchical stream channels from flow accumulation using Strahler and Shreve ordering.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Watershed & Basin Delineation", "hydrology:watershed", "Spatial & Hydrology Analyst", "Hydrological Modeling", "Delineates drainage basins and catchment areas for selected pour points.", "raster_terrain", supports_gpu=True),
                    ]
                },
                {
                    "name": "Spatial Interpolation",
                    "items": [
                        AlgorithmDefinition("Ordinary & Universal Kriging", "spatial:kriging", "Spatial & Hydrology Analyst", "Spatial Interpolation", "Geostatistical point interpolation with semivariogram fitting and prediction error variance.", "spatial_interp", supports_gpu=True),
                        AlgorithmDefinition("Inverse Distance Weighting (IDW)", "spatial:idw", "Spatial & Hydrology Analyst", "Spatial Interpolation", "Calculates cell values using linearly weighted combination of sample points.", "spatial_interp", supports_gpu=True),
                        AlgorithmDefinition("Thin Plate Spline Interpolation", "spatial:spline", "Spatial & Hydrology Analyst", "Spatial Interpolation", "Fits minimum curvature surface passing exactly through sample points.", "spatial_interp", supports_gpu=True),
                    ]
                },
                {
                    "name": "Visibility & Multi-Criteria",
                    "items": [
                        AlgorithmDefinition("3D Viewshed & Line of Sight", "spatial:viewshed", "Spatial & Hydrology Analyst", "Visibility & Multi-Criteria", "Calculates visible terrain areas from observer points accounting for target height, Earth curvature, and refraction.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Multi-Criteria Decision Analysis (AHP)", "spatial:weighted_overlay", "Spatial & Hydrology Analyst", "Visibility & Multi-Criteria", "Weighted overlay suitability modeling combining reclassified factor rasters with Analytic Hierarchy Process.", "raster_calc", supports_gpu=True),
                        AlgorithmDefinition("Zonal Statistics", "native:zonalstats", "Spatial & Hydrology Analyst", "Visibility & Multi-Criteria", "Calculates summary statistics (mean, sum, min, max, std) of raster values within polygon zones.", "raster_stats", supports_gpu=False),
                        AlgorithmDefinition("Focal Statistics (Neighborhood)", "native:focalmean", "Spatial & Hydrology Analyst", "Visibility & Multi-Criteria", "Calculates neighborhood moving window statistics (mean, median, majority).", "raster_terrain", supports_gpu=True, requires_halo=True, halo_size=1),
                    ]
                }
            ]
        },

        # ── 4. 📐 VECTOR & TOPOLOGY SUITE (QGIS) ───────────────
        {
            "category": "📐 Vector Geoprocessing",
            "subcategories": [
                {
                    "name": "Geometry Tools",
                    "items": [
                        AlgorithmDefinition("Buffer", "native:buffer", "Vector Geoprocessing", "Geometry Tools", "Generates fixed or attribute-driven buffer zones around vector features.", "vector_buffer", supports_gpu=False),
                        AlgorithmDefinition("Centroids", "native:centroids", "Vector Geoprocessing", "Geometry Tools", "Calculates geometric center points of polygons and multipoints.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Convex Hull", "native:convexhull", "Vector Geoprocessing", "Geometry Tools", "Calculates the smallest enclosing convex polygon enclosing feature geometries.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Dissolve", "native:dissolve", "Vector Geoprocessing", "Geometry Tools", "Merges adjacent polygons sharing boundaries or matching attribute values.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Voronoi / Thiessen Polygons", "native:voronoi", "Vector Geoprocessing", "Geometry Tools", "Constructs Dirichlet/Voronoi tessellation polygons from point datasets.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Delaunay Triangulation", "native:delaunay", "Vector Geoprocessing", "Geometry Tools", "Generates Delaunay triangular irregular network from point coordinates.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Simplify Geometries (Douglas-Peucker)", "native:simplify", "Vector Geoprocessing", "Geometry Tools", "Generalizes and decimates vertices while preserving shape topology.", "vector_geometry", supports_gpu=False),
                    ]
                },
                {
                    "name": "Overlay & Geoprocessing",
                    "items": [
                        AlgorithmDefinition("Clip Vector", "native:clip", "Vector Geoprocessing", "Overlay & Geoprocessing", "Clips input features using the boundary polygon of an overlay layer.", "vector_overlay", supports_gpu=False),
                        AlgorithmDefinition("Intersection", "native:intersection", "Vector Geoprocessing", "Overlay & Geoprocessing", "Extracts spatial overlap portions of features across two layers.", "vector_overlay", supports_gpu=False),
                        AlgorithmDefinition("Union", "native:union", "Vector Geoprocessing", "Overlay & Geoprocessing", "Combines layers while preserving all geometry boundaries and attributes.", "vector_overlay", supports_gpu=False),
                        AlgorithmDefinition("Difference", "native:difference", "Vector Geoprocessing", "Overlay & Geoprocessing", "Extracts features from input layer that do not overlap the overlay layer.", "vector_overlay", supports_gpu=False),
                    ]
                },
                {
                    "name": "Spatial Analysis & Join",
                    "items": [
                        AlgorithmDefinition("Spatial Join", "native:spatialjoin", "Vector Geoprocessing", "Spatial Analysis & Join", "Transfers attributes between layers based on spatial relationships (intersects, contains, within).", "vector_analysis", supports_gpu=False),
                        AlgorithmDefinition("Distance Matrix", "native:distancematrix", "Vector Geoprocessing", "Spatial Analysis & Join", "Calculates pairwise distances between points in two layers.", "vector_analysis", supports_gpu=False),
                        AlgorithmDefinition("Nearest Neighbor Analysis", "native:nearestneighbor", "Vector Geoprocessing", "Spatial Analysis & Join", "Computes spatial clustering index and expected nearest neighbor distance.", "vector_analysis", supports_gpu=False),
                        AlgorithmDefinition("Count Points in Polygons", "native:pointsinpoly", "Vector Geoprocessing", "Spatial Analysis & Join", "Aggregates point count within each bounding polygon feature.", "vector_analysis", supports_gpu=False),
                    ]
                },
                {
                    "name": "Topology & Data Cleaning",
                    "items": [
                        AlgorithmDefinition("Topology & Geometry Validation", "vector:topology_checker", "Vector Geoprocessing", "Topology & Data Cleaning", "Detects self-intersections, duplicate nodes, slivers, gaps, and invalid geometries.", "tools_geom", supports_gpu=False),
                        AlgorithmDefinition("Fix Geometries & Remove Slivers", "native:fixgeoms", "Vector Geoprocessing", "Topology & Data Cleaning", "Repairs invalid geometries and removes micro-sliver polygons.", "tools_geom", supports_gpu=False),
                        AlgorithmDefinition("Field Calculator & Expressions", "native:fieldcalc", "Vector Geoprocessing", "Topology & Data Cleaning", "Computes and creates new attribute columns using spatial & arithmetic expressions.", "field_calculator", supports_gpu=False),
                    ]
                }
            ]
        },

        # ── 5. ☁️ LIDAR & POINT CLOUD SUITE ────────────────────
        {
            "category": "☁️ LiDAR & Point Cloud",
            "subcategories": [
                {
                    "name": "Point Classification",
                    "items": [
                        AlgorithmDefinition("Classify Ground Points (CSF / TIN)", "lidar:classify_ground", "LiDAR & Point Cloud", "Point Classification", "Cloth Simulation / Progressive TIN ground filter separating bare-earth from above-ground objects.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Classify Buildings & Roofs", "lidar:classify_buildings", "LiDAR & Point Cloud", "Point Classification", "Segments planar building roofs and structural footprints.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Classify Vegetation Canopy", "lidar:classify_veg", "LiDAR & Point Cloud", "Point Classification", "Separates low, medium, and high canopy vegetation returns.", "raster_terrain", supports_gpu=True),
                    ]
                },
                {
                    "name": "Surface Extraction & DTM",
                    "items": [
                        AlgorithmDefinition("Generate Bare-Earth DTM", "lidar:generate_dtm", "LiDAR & Point Cloud", "Surface Extraction & DTM", "Interpolates bare-earth ground points into high-resolution Digital Terrain Model raster.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Generate Surface DSM (First Returns)", "lidar:generate_dsm", "LiDAR & Point Cloud", "Surface Extraction & DTM", "Builds surface model including tree crowns and buildings from first returns.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Canopy Height Model (CHM = DSM - DTM)", "lidar:chm", "LiDAR & Point Cloud", "Surface Extraction & DTM", "Calculates Normalized Canopy Height Model for forestry and tree height measurements.", "raster_terrain", supports_gpu=True),
                    ]
                },
                {
                    "name": "Point Cloud Filters & 3D Tools",
                    "items": [
                        AlgorithmDefinition("Statistical Outlier Noise Filter", "lidar:outlier_filter", "LiDAR & Point Cloud", "Point Cloud Filters", "Removes laser flight noise, birds, and high/low atmospheric point anomalies.", "raster_terrain", supports_gpu=True),
                        AlgorithmDefinition("Point Cloud Density Decimation", "lidar:thinning", "LiDAR & Point Cloud", "Point Cloud Filters", "Decimates point cloud volume while preserving morphological surface edges.", "raster_terrain", supports_gpu=False),
                        AlgorithmDefinition("Interactive 3D Point Cloud Visualizer", "lidar:3d_viewer", "LiDAR & Point Cloud", "Point Cloud Filters", "Interactive GPU-accelerated 3D point visualizer colored by elevation, intensity, or RGB.", "dem_dialog", supports_gpu=True),
                    ]
                }
            ]
        },

        # ── 6. 🗺️ CARTOGRAPHY & INTERACTIVE TOOLS ──────────────
        {
            "category": "🗺 Cartography & Interactive Tools",
            "subcategories": [
                {
                    "name": "Interactive Canvas Tools",
                    "items": [
                        AlgorithmDefinition("Interactive Swipe / Curtain Comparison", "carto:swipe_tool", "Cartography & Interactive Tools", "Interactive Canvas Tools", "Split-screen before/after curtain slider to visually compare stacked raster or vector layers.", "carto_swipe", supports_gpu=False),
                        AlgorithmDefinition("Cloud & XYZ Basemap Integrator", "carto:cloud_basemaps", "Cartography & Interactive Tools", "Interactive Canvas Tools", "One-click addition of OpenStreetMap, Google Satellite, Mapbox, and ESRI World Imagery basemaps.", "carto_basemap", supports_gpu=False),
                        AlgorithmDefinition("Measure Distance & Bearing", "native:measure_dist", "Cartography & Interactive Tools", "Interactive Canvas Tools", "Interactive on-canvas polyline distance and compass bearing measurement tool.", "tools_measure", supports_gpu=False),
                        AlgorithmDefinition("Measure Area & Perimeter", "native:measure_area", "Cartography & Interactive Tools", "Interactive Canvas Tools", "Interactive on-canvas polygon area and perimeter measuring tool.", "tools_measure", supports_gpu=False),
                        AlgorithmDefinition("Coordinate Capture & DMS Inspector", "native:coord", "Cartography & Interactive Tools", "Interactive Canvas Tools", "Captures clicked coordinates with real-time DMS, MGRS, and CRS readouts.", "tools_coord", supports_gpu=False),
                    ]
                },
                {
                    "name": "Print Layout & Atlas",
                    "items": [
                        AlgorithmDefinition("Print Layout & Map Composer", "carto:layout_composer", "Cartography & Interactive Tools", "Print Layout & Atlas", "Professional cartographic layout designer with scale bar, north arrow, legend, and grid frame.", "carto_layout", supports_gpu=False),
                        AlgorithmDefinition("Generate Vector Grid / Mesh", "native:grid", "Cartography & Interactive Tools", "Print Layout & Atlas", "Creates rectangular, hexagonal, or diamond index grids.", "tools_grid", supports_gpu=False),
                    ]
                }
            ]
        },

        # ── 7. 📦 DATA MANAGEMENT & UTILITIES ──────────────────
        {
            "category": "📦 Data Management & Utilities",
            "subcategories": [
                {
                    "name": "Import & Export",
                    "items": [
                        AlgorithmDefinition("Import Vector (SHP, GPKG, GeoJSON, KML)", "native:import_vector", "Data Management & Utilities", "Import & Export", "Loads Shapefile, GeoPackage, GeoJSON, KML, and DXF vector layers.", "io_import_vector", supports_gpu=False),
                        AlgorithmDefinition("Import Raster (GeoTIFF, HDF, NetCDF)", "native:import_raster", "Data Management & Utilities", "Import & Export", "Loads GeoTIFF, DEM, HDF5, NetCDF, and JP2 rasters.", "io_import_raster", supports_gpu=False),
                        AlgorithmDefinition("Import CSV / Delimited Coordinates", "native:import_csv", "Data Management & Utilities", "Import & Export", "Parses delimited text files with coordinates into point geometry layers.", "io_import_csv", supports_gpu=False),
                        AlgorithmDefinition("Export Layer to Format", "native:export_layer", "Data Management & Utilities", "Import & Export", "Converts active layer to Shapefile, GeoTIFF, GeoPackage, or DXF.", "io_export", supports_gpu=False),
                    ]
                },
                {
                    "name": "Conversion & Projections",
                    "items": [
                        AlgorithmDefinition("Raster to Vector (Polygonize)", "gdal:polygonize", "Data Management & Utilities", "Conversion & Projections", "Converts classified raster pixel clusters into vector polygon layers.", "vector_geometry", supports_gpu=False),
                        AlgorithmDefinition("Vector to Raster (Rasterize)", "gdal:rasterize", "Data Management & Utilities", "Conversion & Projections", "Burns vector polygon or line geometries into a raster grid.", "raster_calc", supports_gpu=False),
                        AlgorithmDefinition("Reproject Layer (Warp CRS)", "native:reproject", "Data Management & Utilities", "Conversion & Projections", "Transforms coordinates to a new Coordinate Reference System.", "io_reproject", supports_gpu=False),
                        AlgorithmDefinition("Build Pyramid Overviews", "tools:raster_util", "Data Management & Utilities", "Conversion & Projections", "Builds multi-resolution pyramid overviews for high-speed map zooming.", "tools_raster", supports_gpu=False),
                        AlgorithmDefinition("Processing Settings & GPU Engine", "tools:settings", "Data Management & Utilities", "Conversion & Projections", "Configure GPU memory budgets, RAM thresholds, and CUDA device priority.", "processing_settings", supports_gpu=False),
                    ]
                }
            ]
        }
    ]

    @classmethod
    def get_all_algorithms(cls) -> List[AlgorithmDefinition]:
        all_algos = []
        for cat in cls.HIERARCHY:
            for sub in cat["subcategories"]:
                all_algos.extend(sub["items"])
        return all_algos

    @classmethod
    def find_algorithm(cls, algo_id: str) -> Optional[AlgorithmDefinition]:
        for algo in cls.get_all_algorithms():
            if algo.algo_id == algo_id or algo.dialog_type == algo_id:
                return algo
        return None
