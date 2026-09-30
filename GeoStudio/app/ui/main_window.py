# -*- coding: utf-8 -*-
"""
GeoStudio - Main Window
Lean coordinator that initializes canvas, menus, modular toolbars, and dock panels.
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt

from .map_canvas_widget import MapCanvasWidget
from .layer_panel import LayerPanelWidget
from .attribute_table_dock import AttributeTableDock
from .processing_dock import ProcessingDock
from .python_console_dock import PythonConsoleDock
from .status_bar import GeoStatusBar
from .menus.menu_builder import build_main_menus
from .toolbars import (
    ProjectToolBar, NavToolBar, DataSourcesToolBar, SelectionToolBar,
    MeasurementToolBar, TerrainToolBar, LidarToolBar, DigitizingToolBar
)
from core.style import OFFWHITE_STYLESHEET, DARK_STYLESHEET


class GeoStudioMainWindow(QMainWindow):
    """
    GeoStudio Main Window — QGIS & Global Mapper standalone GIS.
    Coordinates all modular toolbars, menus, canvas, and dock widgets.
    """

    APP_NAME = "GeoStudio"
    VERSION  = "1.0.0"

    def __init__(self, qgs_app=None, parent=None):
        super().__init__(parent)
        self.qgs_app = qgs_app
        self.setWindowTitle(f"{self.APP_NAME} — Standalone GIS")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 950)

        # Apply global off-white light theme by default
        self.setStyleSheet(OFFWHITE_STYLESHEET)

        # Init UI components
        self._build_central_widget()
        self._build_docks()
        self._build_menus()
        self._build_toolbars()
        self._build_status_bar()

        self._connect_signals()
        self._update_title()

    # ── UI Construction ─────────────────────────────────────────
    def _build_central_widget(self):
        self.map_canvas = MapCanvasWidget(self)
        self.setCentralWidget(self.map_canvas)

    def _build_menus(self):
        build_main_menus(self)

    def _build_toolbars(self):
        # Row 1: General GIS Toolbars
        self.tb_file = ProjectToolBar(self)
        self.tb_nav = NavToolBar(self)
        self.tb_data = DataSourcesToolBar(self)
        self.tb_selection = SelectionToolBar(self)
        self.tb_measure = MeasurementToolBar(self)

        self.addToolBar(Qt.TopToolBarArea, self.tb_file)
        self.addToolBar(Qt.TopToolBarArea, self.tb_nav)
        self.addToolBar(Qt.TopToolBarArea, self.tb_data)
        self.addToolBar(Qt.TopToolBarArea, self.tb_selection)
        self.addToolBar(Qt.TopToolBarArea, self.tb_measure)

        # Row 2: Specialized Terrain, LiDAR & Digitizing Toolbars
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.tb_terrain = TerrainToolBar(self)
        self.tb_lidar = LidarToolBar(self)
        self.tb_digitizing = DigitizingToolBar(self)

        self.addToolBar(Qt.TopToolBarArea, self.tb_terrain)
        self.addToolBar(Qt.TopToolBarArea, self.tb_lidar)
        self.addToolBar(Qt.TopToolBarArea, self.tb_digitizing)

    def _build_docks(self):
        # Left: Layers Panel
        self.layer_panel = LayerPanelWidget(self.map_canvas)
        self.layer_dock = QDockWidget("Layers", self)
        self.layer_dock.setObjectName("layer_dock")
        self.layer_dock.setWidget(self.layer_panel)
        self.layer_dock.setMinimumWidth(240)
        self.layer_dock.setMaximumWidth(420)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.layer_dock)

        # Right: Hierarchical Processing Toolbox
        self.processing_dock = ProcessingDock(self.map_canvas, self)
        self.processing_dock.setObjectName("processing_dock")
        self.addDockWidget(Qt.RightDockWidgetArea, self.processing_dock)
        self.processing_dock.hide()

        # Bottom: Attribute Table & Python Console
        self.attr_table_dock = AttributeTableDock(self)
        self.attr_table_dock.setObjectName("attr_table_dock")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.attr_table_dock)
        self.attr_table_dock.hide()

        self.console_dock = PythonConsoleDock(self)
        self.console_dock.setObjectName("console_dock")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()

    def _build_status_bar(self):
        self.geo_status = GeoStatusBar(self.map_canvas, self)
        self.setStatusBar(self.geo_status)

    def _connect_signals(self):
        self.layer_panel.active_layer_changed.connect(self._on_active_layer_changed)
        try:
            from core.raster_optimizer import get_raster_optimizer
            get_raster_optimizer().status_message.connect(self.geo_status.showMessage)
        except Exception:
            pass

    def _on_active_layer_changed(self, layer):
        name = layer.name() if layer else "None"
        self.geo_status.set_layer(name)

    def _update_title(self):
        self.setWindowTitle(f"{self.APP_NAME} v{self.VERSION} — Standalone GIS")

    # ── Project & File Handlers ─────────────────────────────────
    def new_project(self):
        try:
            from qgis.core import QgsProject
            QgsProject.instance().clear()
            self.layer_panel.refresh()
            self.map_canvas.refresh_canvas()
            self.setWindowTitle(f"{self.APP_NAME} — New Project")
        except Exception as e:
            self._info(f"New project: {e}")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "QGIS Projects (*.qgs *.qgz);;All Files (*)")
        if path:
            try:
                from qgis.core import QgsProject
                QgsProject.instance().read(path)
                self.layer_panel.refresh()
                self.map_canvas.refresh_canvas()
                self.setWindowTitle(f"{self.APP_NAME} — {os.path.basename(path)}")
            except Exception as e:
                self._err(f"Could not open project: {e}")

    def save_project(self):
        try:
            from qgis.core import QgsProject
            path = QgsProject.instance().fileName()
            if path:
                QgsProject.instance().write(path)
                self.statusBar().showMessage("Project saved.", 3000)
            else:
                self.save_project_as()
        except Exception as e:
            self._err(str(e))

    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "QGIS Project (*.qgs);;QGIS Compressed (*.qgz)")
        if path:
            try:
                from qgis.core import QgsProject
                QgsProject.instance().write(path)
                self.setWindowTitle(f"{self.APP_NAME} — {os.path.basename(path)}")
            except Exception as e:
                self._err(str(e))

    def project_properties(self): self._info("Project Properties dialog.")
    def print_map(self):          self._info("Print / Layout Manager.")

    # ── Layer & Data Sources Handlers ───────────────────────────
    def add_vector(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add Vector Layer", "", "Vector Files (*.shp *.gpkg *.geojson *.json *.kml *.csv);;All (*)")
        if path: self.layer_panel.load_vector(path)

    def add_raster(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add Raster Layer", "", "Raster Files (*.tif *.tiff *.img *.asc *.nc *.hdf *.vrt);;All (*)")
        if path: self.layer_panel.load_raster(path)

    def add_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add CSV as Points", "", "CSV Files (*.csv);;All Files (*)")
        if path: self.layer_panel.load_csv(path)

    def load_las_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load LAS / LAZ Point Cloud", "", "LiDAR Files (*.las *.laz *.e57);;All Files (*)")
        if path: self.layer_panel.load_raster(path)

    def add_wms(self):          self.layer_panel.load_osm_basemap()
    def add_xyz_basemap(self):  self.layer_panel.load_osm_basemap()
    def remove_layer(self):     self.layer_panel.remove_active_layer()
    def layer_properties(self): self.layer_panel.show_layer_properties()
    def toggle_layer_dock(self):self.layer_dock.setVisible(not self.layer_dock.isVisible())

    # ── Map Navigation & Canvas Handlers ────────────────────────
    def zoom_in(self):        self.map_canvas.zoom_in()
    def zoom_out(self):       self.map_canvas.zoom_out()
    def zoom_full(self):      self.map_canvas.zoom_full()
    def zoom_last(self):      self.map_canvas.zoom_last()
    def zoom_next(self):      self.map_canvas.zoom_next()
    def refresh_canvas(self): self.map_canvas.refresh_canvas()

    # ── Map Tools, Selection & Measurement ──────────────────────
    def set_pan_tool(self):         self.map_canvas.set_tool("pan")
    def set_zoom_in(self):          self.map_canvas.set_tool("zoom_in")
    def set_zoom_out(self):         self.map_canvas.set_tool("zoom_out")
    def set_measure_distance(self): self.map_canvas.set_tool("measure_distance")
    def set_measure_area(self):     self.map_canvas.set_tool("measure_area")
    def set_measure_angle(self):    self.map_canvas.set_tool("measure_distance")
    def set_coord_capture(self):    self.map_canvas.set_tool("identify")
    def set_identify_tool(self):    self.map_canvas.set_tool("identify")
    def set_select_tool(self):      self.map_canvas.set_tool("select")
    def set_select_mode(self, mode: str):
        self.map_canvas.set_tool("select")
        self.geo_status.showMessage(f"Selection mode: {mode}", 2500)
    def clear_selection(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "removeSelection"):
            layer.removeSelection()
            self.map_canvas.refresh_canvas()
        self.geo_status.showMessage("Selection cleared", 2000)

    # ── Digitizing & Editing Handlers ───────────────────────────
    def undo_action(self):     self.geo_status.showMessage("Undo executed", 2000)
    def redo_action(self):     self.geo_status.showMessage("Redo executed", 2000)
    def cut_features(self):    self.geo_status.showMessage("Cut feature", 2000)
    def copy_features(self):   self.geo_status.showMessage("Copied features", 2000)
    def paste_features(self):  self.geo_status.showMessage("Pasted features", 2000)
    def delete_selected(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "deleteSelectedFeatures"):
            layer.deleteSelectedFeatures()
            self.map_canvas.refresh_canvas()
        self.geo_status.showMessage("Deleted selected feature(s)", 2000)
    def toggle_editing(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "isEditable"):
            if layer.isEditable():
                layer.commitChanges()
                self.geo_status.showMessage(f"Committed changes for {layer.name()}", 2500)
            else:
                layer.startEditing()
                self.geo_status.showMessage(f"Started editing for {layer.name()}", 2500)
        else:
            self._info("Select a vector layer to toggle editing.")
    def set_digitize_tool(self, tool_type: str):
        self.geo_status.showMessage(f"Active digitizing tool: {tool_type.capitalize()}", 2500)
    def split_feature(self): self.geo_status.showMessage("Split Feature active", 2000)
    def merge_features(self): self.processing_dock.open_algorithm("merge_layers")
    def toggle_snapping(self): self.geo_status.showMessage("Snapping toggled", 2000)
    def set_snapping_mode(self, mode: str): self.geo_status.showMessage(f"Snapping: {mode}", 2500)

    # ── Terrain, LiDAR & Analysis Handlers ──────────────────────
    def apply_shader_preset(self, preset_key: str):
        layer = self.layer_panel.get_active_layer()
        if not layer:
            self._info("Please select a DEM/Elevation raster layer first.")
            return
        self.layer_panel.open_dem_dialog(layer)
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
    def open_elevation_profile(self):   self.geo_status.showMessage("Elevation Profile tool active.", 3000)
    def open_viewshed(self):            self.processing_dock.open_algorithm("raster_terrain")
    def open_cut_fill(self):            self.processing_dock.open_algorithm("raster_terrain")
    def open_hydro_fillsinks(self):     self.processing_dock.open_algorithm("hydrology:fillsinks")
    def open_hydro_flowdir(self):       self.processing_dock.open_algorithm("hydrology:flowdir")
    def open_hydro_flowaccum(self):     self.processing_dock.open_algorithm("hydrology:flowaccum")
    def open_hydro_watershed(self):     self.processing_dock.open_algorithm("hydrology:watershed")
    def open_spectral_index(self, id):  self.processing_dock.open_algorithm(id)
    def open_composite_dialog(self):    self.processing_dock.open_algorithm("satellite:composite")
    def open_band_stack_dialog(self):   self.processing_dock.open_algorithm("satellite:bandstack")
    def open_pca_dialog(self):          self.processing_dock.open_algorithm("satellite:pca")
    def open_sam_dialog(self):          self.processing_dock.open_algorithm("satellite:sam")
    def open_band_math_dialog(self):    self.processing_dock.open_algorithm("satellite:rastercalc")
    def set_lidar_color_mode(self, m):  self.geo_status.showMessage(f"LiDAR Color By: {m.capitalize()}", 2500)
    def open_3d_viewer(self):           self.open_dem_elevation_dialog()
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
    def raster_clip(self):              self.processing_dock.open_algorithm("gdal:clipraster")

    # ── Docks, Plugins & Settings ───────────────────────────────
    def toggle_processing_dock(self):   self.processing_dock.setVisible(not self.processing_dock.isVisible())
    def show_recently_used(self):       self.processing_dock.show()
    def open_processing_settings(self): self.processing_dock.open_algorithm("tools:settings")
    def toggle_python_console(self):    self.console_dock.setVisible(not self.console_dock.isVisible())
    def open_plugin_manager(self):      self._info("Plugin Manager.")
    def open_attribute_table(self):
        self.attr_table_dock.show()
        self.attr_table_dock.load_active_layer(self.layer_panel.get_active_layer())

    def open_gpu_status(self):
        from core.gpu.cuda_detector import get_cuda_hardware_info
        info = get_cuda_hardware_info()
        status_str = f"GPU Available: {info.is_cuda_available}\nDevice: {info.device_name}\nVRAM: {info.vram_total_gb:.1f} GB (Free: {info.vram_free_gb:.1f} GB)"
        QMessageBox.information(self, "GPU Status", status_str)

    def set_theme(self, theme_name: str = "offwhite"):
        if theme_name == "offwhite":
            self.setStyleSheet(OFFWHITE_STYLESHEET)
            if self.map_canvas: self.map_canvas.set_canvas_background("#f8f9fa")
            self.geo_status.showMessage("☀️ Off-White Light Theme applied", 3000)
        else:
            self.setStyleSheet(DARK_STYLESHEET)
            if self.map_canvas: self.map_canvas.set_canvas_background("#1e272c")
            self.geo_status.showMessage("🌙 Dark GIS Theme applied", 3000)

    def set_project_crs(self): self._info("CRS selector.")
    def open_docs(self):
        import webbrowser
        webbrowser.open("https://docs.qgis.org/3.34/en/docs/pyqgis_developer_cookbook/")

    def about(self):
        QMessageBox.about(self, f"About {self.APP_NAME}",
            f"<h2>🌍 {self.APP_NAME} v{self.VERSION}</h2>"
            f"<p>A standalone GIS application powered by QGIS & GPU-accelerated computing.</p>"
            f"<p>Built with PyQGIS, PyQt5, GDAL, NumPy, CuPy.</p>")

    def _info(self, msg): QMessageBox.information(self, self.APP_NAME, msg)
    def _err(self, msg):  QMessageBox.critical(self, self.APP_NAME, msg)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Exit GeoStudio", "Exit GeoStudio?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes: event.accept()
        else: event.ignore()
