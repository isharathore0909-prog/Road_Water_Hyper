# -*- coding: utf-8 -*-
"""
GeoStudio - Terrain, LiDAR, Satellite & Geoprocessing Controller Mixin
"""
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from ui.controllers.lidar_controller_handler import LidarControllerHandler


class AnalysisControllerMixin:
    """Handles Terrain, DEM styler, Satellite, LiDAR and geoprocessing algorithm dialogs."""

    def apply_shader_preset(self, preset_key: str):
        layer = self.layer_panel.get_active_layer()
        if not layer:
            self._info("Please select a DEM/Elevation raster layer first.")
            return
        self.layer_panel._apply_elevation_preset(layer, preset_key)
        self.geo_status.showMessage(f"Applied terrain shader: {preset_key}", 2500)

    def open_dem_elevation_dialog(self):
        layer = self.layer_panel.get_active_layer()
        self.layer_panel.open_dem_dialog(layer)

    def open_slope_dialog(self):        self.processing_dock.open_algorithm("native:slope")
    def open_aspect_dialog(self):       self.processing_dock.open_algorithm("native:aspect")
    def open_hillshade_dialog(self):    self.processing_dock.open_algorithm("native:hillshade")
    def open_tri_dialog(self):          self.processing_dock.open_algorithm("native:roughness")
    def open_tpi_dialog(self):          self.processing_dock.open_algorithm("native:tpi")
    def open_twi_dialog(self):          self.processing_dock.open_algorithm("native:twi")
    def open_curvature_dialog(self):    self.processing_dock.open_algorithm("native:curvature")
    def open_contour_dialog(self):      self.processing_dock.open_algorithm("gdal:contour")
    def open_viewshed(self):            self.processing_dock.open_algorithm("spatial:viewshed")

    def open_volumetric_analysis(self, layer=None):
        target = layer or self.layer_panel.get_active_layer()
        try:
            from ui.volumetric_dialog import VolumetricAnalysisDialog
            dlg = VolumetricAnalysisDialog(map_canvas=self.map_canvas, target_layer=target, parent=self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open Volumetric Analysis dialog: {e}")

    def open_cut_fill(self, layer=None):
        target = layer or self.layer_panel.get_active_layer()
        try:
            from ui.cut_fill_dialog import CutFillDialog
            dlg = CutFillDialog(map_canvas=self.map_canvas, target_layer=target, parent=self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open Cut & Fill dialog: {e}")

    def open_hydro_fillsinks(self):     self.processing_dock.open_algorithm("hydrology:fillsinks")
    def open_hydro_flowdir(self):       self.processing_dock.open_algorithm("hydrology:flowdir")
    def open_hydro_flowaccum(self):     self.processing_dock.open_algorithm("hydrology:flowaccum")
    def open_hydro_watershed(self):     self.processing_dock.open_algorithm("hydrology:watershed")
    def open_spectral_index(self, id):  self.processing_dock.open_algorithm(id)
    def open_composite_dialog(self):    self.processing_dock.open_algorithm("landsat:composites")
    def open_band_stack_dialog(self):   self.processing_dock.open_algorithm("satellite:bandstack")
    def open_pca_dialog(self):          self.processing_dock.open_algorithm("satellite:pca")
    def open_sam_dialog(self):          self.processing_dock.open_algorithm("satellite:sam")
    def open_band_math_dialog(self):    self.processing_dock.open_algorithm("satellite:bandmath")

    def open_buffer_dialog(self):       self.processing_dock.open_algorithm("native:buffer")
    def open_clip_dialog(self):         self.processing_dock.open_algorithm("native:clip")
    def open_intersect_dialog(self):    self.processing_dock.open_algorithm("native:intersection")
    def open_union_dialog(self):        self.processing_dock.open_algorithm("native:union")
    def open_diff_dialog(self):         self.processing_dock.open_algorithm("native:difference")
    def open_dissolve_dialog(self):     self.processing_dock.open_algorithm("native:dissolve")
    def run_centroids(self):            self.processing_dock.open_algorithm("native:centroids")
    def run_convex_hull(self):          self.processing_dock.open_algorithm("native:convexhull")
    def run_voronoi(self):              self.processing_dock.open_algorithm("native:voronoi")
    def run_merge(self):                self.processing_dock.open_algorithm("native:merge")
    def raster_stats(self):             self.processing_dock.open_algorithm("native:rasterstats")
    def raster_reproject(self):         self.processing_dock.open_algorithm("native:reproject")
    def raster_clip(self):              self.open_crop_raster_dialog()

    def open_elevation_profile(self):
        from ui.elevation_profile_dialog import ElevationProfileDialog
        if not hasattr(self, "_elev_profile_dialog") or self._elev_profile_dialog is None:
            self._elev_profile_dialog = ElevationProfileDialog(self)
        self._elev_profile_dialog.show()
        self._elev_profile_dialog.raise_()
        self._elev_profile_dialog.activateWindow()

    def open_crop_raster_dialog(self):
        from ui.crop_raster_dialog import CropRasterDialog
        dlg = CropRasterDialog(self)
        dlg.exec_()

    def open_3d_viewer(self, target_layer=None):
        from ui.viewer_3d import GeoStudio3DViewerWindow
        from qgis.core import QgsProject, QgsMapLayer

        layer = target_layer or self.layer_panel.get_active_layer()
        if not layer:
            for l in QgsProject.instance().mapLayers().values():
                if hasattr(QgsMapLayer, "PointCloudLayer") and l.type() == QgsMapLayer.PointCloudLayer:
                    layer = l
                    break
                elif "[LiDAR]" in l.name() or "cloud" in l.name().lower():
                    layer = l
                    break

        if layer:
            src = layer.customProperty("original_las_path") or (layer.source() if hasattr(layer, "source") else None)
            if src and "_surface.tif" in src:
                for cand in [src.replace("_surface.tif", ".las"), src.replace("_surface.tif", ".laz"), src.replace("_surface.tif", ".copc.laz")]:
                    if os.path.exists(cand):
                        src = cand
                        break
            if src and os.path.exists(src):
                dlg = GeoStudio3DViewerWindow(self, layer=layer, file_path=src)
                dlg.exec_()
                return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open 3D Point Cloud", "",
            "Point Cloud Files (*.las *.laz *.copc.laz *.e57 *.ply *.xyz *.pts *.csv *.pcd);;All Files (*)"
        )
        if path:
            dlg = GeoStudio3DViewerWindow(self, file_path=path)
            dlg.exec_()

    def set_lidar_color_mode(self, m: str):
        LidarControllerHandler.set_lidar_color_mode(self, m)

    def adjust_point_cloud_size(self, delta: float):
        layer = self.layer_panel.get_active_layer()
        if not layer:
            from qgis.core import QgsProject, QgsMapLayer
            for l in QgsProject.instance().mapLayers().values():
                if hasattr(QgsMapLayer, "PointCloudLayer") and l.type() == QgsMapLayer.PointCloudLayer:
                    layer = l
                    break
        if layer:
            from core.lidar_styler import LidarStyler
            sz = LidarStyler.set_point_size(layer, delta)
            self.map_canvas.force_refresh_canvas()
            self.geo_status.showMessage(f"Point Size: {sz:.1f}px", 2000)

    def run_lidar_auto_classification(self, layer=None):
        LidarControllerHandler.run_auto_classification(self, layer=layer)
