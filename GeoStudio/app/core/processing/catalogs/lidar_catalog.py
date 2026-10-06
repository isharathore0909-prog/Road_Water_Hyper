# -*- coding: utf-8 -*-
"""
GeoStudio - ☁️ LiDAR & Point Cloud Algorithm Catalog
"""

from typing import Dict, Any
from ..algorithm_definition import AlgorithmDefinition

LIDAR_CATALOG: Dict[str, Any] = {
            "category": "☁️ LiDAR & Point Cloud",
            "subcategories": [
                {
                    "name": "Point Classification",
                    "items": [
                        AlgorithmDefinition(
                            "Classify Ground Points (CSF / TIN)",
                            "lidar:classify_ground",
                            "LiDAR & Point Cloud",
                            "Point Classification",
                            (
                                "Cloth Simulation / Progressive TIN ground filter separating bare-"
                                "earth from above-ground objects."
                            ),
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                        AlgorithmDefinition(
                            "Classify Buildings & Roofs",
                            "lidar:classify_buildings",
                            "LiDAR & Point Cloud",
                            "Point Classification",
                            "Segments planar building roofs and structural footprints.",
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                        AlgorithmDefinition(
                            "Classify Vegetation Canopy",
                            "lidar:classify_veg",
                            "LiDAR & Point Cloud",
                            "Point Classification",
                            "Separates low, medium, and high canopy vegetation returns.",
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                    ]
                },
                {
                    "name": "Surface Extraction & DTM",
                    "items": [
                        AlgorithmDefinition(
                            "Generate Bare-Earth DTM",
                            "lidar:generate_dtm",
                            "LiDAR & Point Cloud",
                            "Surface Extraction & DTM",
                            (
                                "Interpolates bare-earth ground points into high-resolution"
                                "Digital Terrain Model raster."
                            ),
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                        AlgorithmDefinition(
                            "Generate Surface DSM (First Returns)",
                            "lidar:generate_dsm",
                            "LiDAR & Point Cloud",
                            "Surface Extraction & DTM",
                            (
                                "Builds surface model including tree crowns and buildings from"
                                "first returns."
                            ),
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                        AlgorithmDefinition(
                            "Canopy Height Model (CHM = DSM - DTM)",
                            "lidar:chm",
                            "LiDAR & Point Cloud",
                            "Surface Extraction & DTM",
                            (
                                "Calculates Normalized Canopy Height Model for forestry and tree"
                                "height measurements."
                            ),
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                    ]
                },
                {
                    "name": "Point Cloud Filters & 3D Tools",
                    "items": [
                        AlgorithmDefinition(
                            "Statistical Outlier Noise Filter",
                            "lidar:outlier_filter",
                            "LiDAR & Point Cloud",
                            "Point Cloud Filters",
                            (
                                "Removes laser flight noise, birds, and high/low atmospheric point"
                                "anomalies."
                            ),
                            "raster_terrain",
                            supports_gpu=True,
                        ),
                        AlgorithmDefinition(
                            "Point Cloud Density Decimation",
                            "lidar:thinning",
                            "LiDAR & Point Cloud",
                            "Point Cloud Filters",
                            (
                                "Decimates point cloud volume while preserving morphological"
                                "surface edges."
                            ),
                            "raster_terrain",
                            supports_gpu=False,
                        ),
                        AlgorithmDefinition(
                            "Clip Point Cloud to Polygon",
                            "lidar:clip",
                            "LiDAR & Point Cloud",
                            "Point Cloud Filters",
                            "Clips point cloud coordinates to polygon or bounding box.",
                            "raster_terrain",
                            supports_gpu=False,
                        ),
                        AlgorithmDefinition(
                            "Interactive 3D Point Cloud Visualizer",
                            "lidar:3d_viewer",
                            "LiDAR & Point Cloud",
                            "Point Cloud Filters",
                            (
                                "Interactive GPU-accelerated 3D point visualizer colored by"
                                "elevation, intensity, or RGB."
                            ),
                            "dem_dialog",
                            supports_gpu=True,
                        ),
                    ]
                }
            ]
        }
