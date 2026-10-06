# -*- coding: utf-8 -*-
"""
GeoStudio - Layer Loading Operations
Handles vector, raster (DEM/imagery), point cloud (LAS/LAZ/COPC), OSM basemaps, and CSV importing.
"""

import os
import shutil
import tempfile
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt

from core.elevation_styler import ElevationStyler
from core.raster_optimizer import get_raster_optimizer


class LayerLoader:
    """Helper class containing all file-loading routines for the layer panel."""

    @staticmethod
    def load_vector(panel, path: str):
        if not path or not os.path.exists(path):
            return
        from qgis.core import QgsVectorLayer, QgsProject
        name = os.path.splitext(os.path.basename(path))[0]
        layer = QgsVectorLayer(path, name, "ogr")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            panel.map_canvas.zoom_to_layer(layer)
        else:
            QMessageBox.critical(panel, "Error", f"Failed to load vector layer:\n{path}")

    @staticmethod
    def load_raster(panel, path: str):
        if not path or not os.path.exists(path):
            return
        from qgis.core import QgsRasterLayer, QgsProject
        name = os.path.splitext(os.path.basename(path))[0]

        # Check if point cloud was opened
        if path.lower().endswith(('.las', '.laz', '.copc.laz', '.e57')):
            panel.load_point_cloud(path)
            return

        # Optimization & overviews
        try:
            from core.raster_optimizer import RasterOptimizer
            opt = RasterOptimizer()
            if opt.needs_optimization(path):
                opt.build_overviews_async(path)
        except Exception:
            pass

        layer = QgsRasterLayer(path, name)
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            if ElevationStyler.is_dem_or_elevation(layer):
                ElevationStyler.auto_style_elevation_if_dem(layer)
            else:
                ElevationStyler.apply_resampling(layer, mode="sharp")
            panel.map_canvas.zoom_to_layer(layer)
        else:
            QMessageBox.critical(panel, "Error", f"Failed to load raster layer:\n{path}")

    @staticmethod
    def load_point_cloud(panel, path: str):
        if not path or not os.path.exists(path):
            return
        from qgis.core import QgsProject, QgsPointCloudLayer, QgsMapLayer
        from core.lidar.lidar_styler import LidarStyler
        from core.lidar.point_cloud_indexer import PointCloudIndexer

        name = os.path.splitext(os.path.basename(path))[0]
        if name.lower().endswith(".copc"):
            name = os.path.splitext(name)[0]

        copc_path = path
        if not path.lower().endswith(".copc.laz"):
            from ui.layer_loading_dialog import LayerLoadingDialog
            dlg = LayerLoadingDialog(
                title="Converting to Cloud-Optimized Point Cloud",
                message=f"Indexing & generating 3D octree for:\n{os.path.basename(path)}",
                cancel_callback=PointCloudIndexer.cancel,
                parent=panel
            )
            dlg.show()
            try:
                copc_path = PointCloudIndexer.ensure_copc_index(
                    path,
                    progress_callback=dlg.set_progress
                )
            finally:
                dlg.close()

            if not copc_path or not os.path.exists(copc_path):
                QMessageBox.warning(
                    panel, "Indexing Cancelled",
                    "COPC point cloud indexing was cancelled or failed."
                )
                return

        pc_layer = QgsPointCloudLayer(copc_path, f"{name} [LiDAR]", "copc")
        if pc_layer.isValid():
            LidarStyler.auto_style(pc_layer, point_size=3.5)
            QgsProject.instance().addMapLayer(pc_layer)
            panel.map_canvas.zoom_to_layer(pc_layer)
        else:
            QMessageBox.critical(panel, "Error", f"Failed to load Point Cloud layer:\n{path}")

    @staticmethod
    def load_osm_basemap(panel):
        from qgis.core import QgsRasterLayer, QgsProject
        url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0"
        layer = QgsRasterLayer(url, "OpenStreetMap Basemap", "wms")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            panel.map_canvas.set_crs(layer.crs())
        else:
            QMessageBox.critical(panel, "Error", "Failed to load OpenStreetMap basemap.")

    @staticmethod
    def load_csv(panel, path: str, x_field: str = "longitude", y_field: str = "latitude"):
        if not path or not os.path.exists(path):
            return
        from qgis.core import QgsVectorLayer, QgsProject
        name = os.path.splitext(os.path.basename(path))[0]
        uri = f"file:///{path}?delimiter=,&xField={x_field}&yField={y_field}&crs=EPSG:4326"
        layer = QgsVectorLayer(uri, name, "delimitedtext")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            panel.map_canvas.zoom_to_layer(layer)
        else:
            QMessageBox.critical(panel, "Error", f"Failed to load CSV layer:\n{path}")
