# -*- coding: utf-8 -*-
"""
GeoStudio - Main Window
A full standalone GIS application window modelled after QGIS.
"""

import os
import sys

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QDockWidget, QStatusBar, QToolBar,
    QAction, QSplitter, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QApplication,
    QTabWidget, QSizePolicy, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QColor, QFont, QKeySequence

from .map_canvas_widget import MapCanvasWidget
from .layer_panel import LayerPanelWidget
from .attribute_table_dock import AttributeTableDock
from .processing_dock import ProcessingDock
from .python_console_dock import PythonConsoleDock
from .status_bar import GeoStatusBar
from core.style import DARK_STYLESHEET


class GeoStudioMainWindow(QMainWindow):
    """
    GeoStudio Main Window — full QGIS-like standalone GIS.

    Layout:
    ┌──────────────────────────────────────────────┐
    │  Menu Bar                                     │
    │  Toolbars (File, Map Nav, Analysis, Raster)  │
    ├────────────┬─────────────────────────────────┤
    │  Layer     │   MAP CANVAS                    │
    │  Panel     │                                 │
    │  (left)    │                                 │
    │            ├─────────────────────────────────┤
    │            │  Processing / Analysis Dock     │
    ├────────────┴─────────────────────────────────┤
    │  Attribute Table Dock (bottom)                │
    │  Status Bar                                   │
    └──────────────────────────────────────────────┘
    """

    APP_NAME = "GeoStudio"
    VERSION  = "1.0.0"

    def __init__(self, qgs_app=None, parent=None):
        super().__init__(parent)
        self.qgs_app = qgs_app
        self.setWindowTitle(f"{self.APP_NAME} — Standalone GIS")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 950)

        # Apply global dark stylesheet
        self.setStyleSheet(DARK_STYLESHEET)

        # Init UI components
        self._build_menus()
        self._build_toolbars()
        self._build_central_widget()
        self._build_docks()
        self._build_status_bar()

        self._connect_signals()
        self._update_title()

    # ═══════════════════════════════════════════════════════════
    # MENUS
    # ═══════════════════════════════════════════════════════════
    def _build_menus(self):
        mb = self.menuBar()

        # ── Project ──────────────────────────────────────────
        proj = mb.addMenu("&Project")
        proj.addAction(self._action("🆕 New Project",         self.new_project,      "Ctrl+N"))
        proj.addAction(self._action("📂 Open Project...",     self.open_project,     "Ctrl+O"))
        proj.addSeparator()
        proj.addAction(self._action("💾 Save Project",        self.save_project,     "Ctrl+S"))
        proj.addAction(self._action("💾 Save Project As...",  self.save_project_as,  "Ctrl+Shift+S"))
        proj.addSeparator()
        proj.addAction(self._action("⚙ Project Properties",   self.project_properties))
        proj.addSeparator()
        proj.addAction(self._action("🖨 Print / Export Map",  self.print_map,        "Ctrl+P"))
        proj.addSeparator()
        proj.addAction(self._action("❌ Exit",                 self.close,            "Ctrl+Q"))

        # ── Layer ─────────────────────────────────────────────
        layer = mb.addMenu("&Layer")
        layer.addAction(self._action("📂 Add Vector Layer...",    self.add_vector,   "Ctrl+Shift+V"))
        layer.addAction(self._action("🏔 Add Raster Layer...",    self.add_raster,   "Ctrl+Shift+R"))
        layer.addAction(self._action("🌐 Add WMS/XYZ Layer...",   self.add_wms))
        layer.addAction(self._action("📊 Add Delimited Text (CSV)...", self.add_csv))
        layer.addSeparator()
        layer.addAction(self._action("🗑 Remove Selected Layer",  self.remove_layer, "Delete"))
        layer.addSeparator()
        layer.addAction(self._action("ℹ Layer Properties",        self.layer_properties, "F3"))

        # ── View ──────────────────────────────────────────────
        view = mb.addMenu("&View")
        view.addAction(self._action("🔍 Zoom In",              self.zoom_in,        "Ctrl++"))
        view.addAction(self._action("🔎 Zoom Out",             self.zoom_out,       "Ctrl+-"))
        view.addAction(self._action("🌍 Zoom Full Extent",     self.zoom_full,      "Ctrl+Shift+F"))
        view.addAction(self._action("↩ Zoom Last",             self.zoom_last,      "Ctrl+["))
        view.addAction(self._action("↪ Zoom Next",             self.zoom_next,      "Ctrl+]"))
        view.addSeparator()
        view.addAction(self._action("🔄 Refresh Map",          self.refresh_canvas, "F5"))
        view.addSeparator()
        # Panel toggles added after docks are built
        self._view_menu = view

        # ── Analysis ──────────────────────────────────────────
        analysis = mb.addMenu("&Analysis")
        analysis.addAction(self._action("📐 Buffer...",         self.open_buffer_dialog))
        analysis.addAction(self._action("✂ Clip...",            self.open_clip_dialog))
        analysis.addAction(self._action("∩ Intersect...",       self.open_intersect_dialog))
        analysis.addAction(self._action("◉ Dissolve...",        self.open_dissolve_dialog))
        analysis.addSeparator()
        analysis.addAction(self._action("🏔 Slope...",          self.open_slope_dialog))
        analysis.addAction(self._action("💡 Hillshade...",      self.open_hillshade_dialog))
        analysis.addAction(self._action("📈 Contours...",       self.open_contour_dialog))
        analysis.addSeparator()
        analysis.addAction(self._action("🛰 Spectral Indices (NDVI, EVI...)", self.open_satellite_dialog))
        analysis.addAction(self._action("∑ Band Math (Raster Calculator)", self.open_band_math_dialog))
        analysis.addSeparator()
        analysis.addAction(self._action("⚙ Processing Toolbox", self.toggle_processing_dock))

        # ── Vector ────────────────────────────────────────────
        vector = mb.addMenu("&Vector")
        vector.addAction(self._action("🔵 Centroids",          self.run_centroids))
        vector.addAction(self._action("⌂ Convex Hull",         self.run_convex_hull))
        vector.addAction(self._action("☆ Voronoi Polygons",    self.run_voronoi))
        vector.addAction(self._action("🔗 Merge Layers",        self.run_merge))
        vector.addSeparator()
        vector.addAction(self._action("📊 Open Attribute Table", self.open_attribute_table, "F6"))

        # ── Raster ────────────────────────────────────────────
        raster = mb.addMenu("&Raster")
        raster.addAction(self._action("📊 Raster Statistics",  self.raster_stats))
        raster.addAction(self._action("🎨 Pseudocolor Render", self.raster_pseudocolor))
        raster.addAction(self._action("🗺 Reproject Raster",   self.raster_reproject))
        raster.addAction(self._action("✂ Clip Raster by Extent", self.raster_clip))

        # ── Settings ──────────────────────────────────────────
        settings = mb.addMenu("&Settings")
        settings.addAction(self._action("⚙ Application Settings", self.open_settings))
        settings.addAction(self._action("🎨 Map CRS...",       self.set_project_crs))

        # ── Help ──────────────────────────────────────────────
        help_menu = mb.addMenu("&Help")
        help_menu.addAction(self._action("📖 Documentation",   self.open_docs))
        help_menu.addAction(self._action("ℹ About GeoStudio",  self.about))

    # ═══════════════════════════════════════════════════════════
    # TOOLBARS
    # ═══════════════════════════════════════════════════════════
    def _build_toolbars(self):
        icon_size = QSize(22, 22)

        # ── File Toolbar ─────────────────────────────────────
        self.tb_file = QToolBar("File")
        self.tb_file.setObjectName("tb_file")
        self.tb_file.setIconSize(icon_size)
        for text, slot, tip in [
            ("🆕", self.new_project,   "New Project (Ctrl+N)"),
            ("📂", self.open_project,  "Open Project (Ctrl+O)"),
            ("💾", self.save_project,  "Save Project (Ctrl+S)"),
            ("🖨", self.print_map,     "Print / Export Map"),
        ]:
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            self.tb_file.addAction(a)
        self.addToolBar(Qt.TopToolBarArea, self.tb_file)

        # ── Layer Toolbar ────────────────────────────────────
        self.tb_layer = QToolBar("Layers")
        self.tb_layer.setObjectName("tb_layer")
        self.tb_layer.setIconSize(icon_size)
        for text, slot, tip in [
            ("📂+V", self.add_vector,  "Add Vector Layer"),
            ("🏔+R", self.add_raster,  "Add Raster Layer"),
            ("📊+C", self.add_csv,     "Add CSV as Points"),
            ("🌐",   self.add_wms,     "Add WMS/XYZ Basemap"),
            ("🗑",   self.remove_layer,"Remove Selected Layer"),
        ]:
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            self.tb_layer.addAction(a)
        self.addToolBar(Qt.TopToolBarArea, self.tb_layer)

        # ── Map Navigation Toolbar ──────────────────────────
        self.tb_nav = QToolBar("Map Navigation")
        self.tb_nav.setObjectName("tb_nav")
        self.tb_nav.setIconSize(icon_size)
        for text, slot, tip in [
            ("🖐",    self.set_pan_tool,    "Pan Map (P)"),
            ("🔍",    self.set_zoom_in,     "Zoom In (+)"),
            ("🔎",    self.set_zoom_out,    "Zoom Out (-)"),
            ("🌍",    self.zoom_full,       "Zoom to Full Extent"),
            ("⬜",    self.zoom_layer,      "Zoom to Active Layer"),
            ("↩",    self.zoom_last,       "Zoom Last"),
            ("↪",    self.zoom_next,       "Zoom Next"),
            ("🔄",    self.refresh_canvas, "Refresh Map (F5)"),
        ]:
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            self.tb_nav.addAction(a)
        self.addToolBar(Qt.TopToolBarArea, self.tb_nav)

        # ── Analysis Toolbar ─────────────────────────────────
        self.tb_analysis = QToolBar("Analysis")
        self.tb_analysis.setObjectName("tb_analysis")
        self.tb_analysis.setIconSize(icon_size)
        for text, slot, tip in [
            ("📏",   self.set_measure_distance, "Measure Distance"),
            ("📐",   self.set_measure_area,     "Measure Area"),
            ("📍",   self.set_identify_tool,    "Identify Features"),
            ("✏",    self.set_select_tool,      "Select Features"),
        ]:
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            self.tb_analysis.addAction(a)
        self.addToolBar(Qt.TopToolBarArea, self.tb_analysis)

    # ═══════════════════════════════════════════════════════════
    # CENTRAL WIDGET — Map Canvas
    # ═══════════════════════════════════════════════════════════
    def _build_central_widget(self):
        self.map_canvas = MapCanvasWidget(self)
        self.setCentralWidget(self.map_canvas)

    # ═══════════════════════════════════════════════════════════
    # DOCK WIDGETS
    # ═══════════════════════════════════════════════════════════
    def _build_docks(self):
        # ── Layer Panel (left) ────────────────────────────────
        self.layer_panel = LayerPanelWidget(self.map_canvas)
        self.layer_dock = QDockWidget("Layers", self)
        self.layer_dock.setObjectName("layer_dock")
        self.layer_dock.setWidget(self.layer_panel)
        self.layer_dock.setMinimumWidth(240)
        self.layer_dock.setMaximumWidth(420)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.layer_dock)

        # ── Processing/Analysis Dock (right) ─────────────────
        self.processing_dock = ProcessingDock(self.map_canvas, self)
        self.processing_dock.setObjectName("processing_dock")
        self.addDockWidget(Qt.RightDockWidgetArea, self.processing_dock)
        self.processing_dock.hide()

        # ── Attribute Table Dock (bottom) ─────────────────────
        self.attr_table_dock = AttributeTableDock(self)
        self.attr_table_dock.setObjectName("attr_table_dock")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.attr_table_dock)
        self.attr_table_dock.hide()

        # ── Python Console Dock (bottom) ──────────────────────
        self.console_dock = PythonConsoleDock(self)
        self.console_dock.setObjectName("console_dock")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()

        # Add panel toggles to View menu
        self._view_menu.addAction(self.layer_dock.toggleViewAction())
        self._view_menu.addAction(self.processing_dock.toggleViewAction())
        self._view_menu.addAction(self.attr_table_dock.toggleViewAction())
        self._view_menu.addAction(self.console_dock.toggleViewAction())

    # ═══════════════════════════════════════════════════════════
    # STATUS BAR
    # ═══════════════════════════════════════════════════════════
    def _build_status_bar(self):
        self.geo_status = GeoStatusBar(self.map_canvas, self)
        self.setStatusBar(self.geo_status)

    # ═══════════════════════════════════════════════════════════
    # SIGNALS
    # ═══════════════════════════════════════════════════════════
    def _connect_signals(self):
        self.layer_panel.active_layer_changed.connect(self._on_active_layer_changed)

    def _on_active_layer_changed(self, layer):
        name = layer.name() if layer else "None"
        self.geo_status.set_layer(name)

    # ═══════════════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════════════
    def _action(self, text, slot, shortcut=None):
        a = QAction(text, self)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        return a

    def _update_title(self):
        from PyQt5.QtCore import QDateTime
        self.setWindowTitle(f"{self.APP_NAME} v{self.VERSION} — Standalone GIS")

    # ═══════════════════════════════════════════════════════════
    # PROJECT ACTIONS
    # ═══════════════════════════════════════════════════════════
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
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "",
            "QGIS Projects (*.qgs *.qgz);;All Files (*)")
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
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "",
            "QGIS Project (*.qgs);;QGIS Compressed (*.qgz)")
        if path:
            try:
                from qgis.core import QgsProject
                QgsProject.instance().write(path)
                self.setWindowTitle(f"{self.APP_NAME} — {os.path.basename(path)}")
            except Exception as e:
                self._err(str(e))

    def project_properties(self):
        self._info("Project Properties dialog coming soon.")

    def print_map(self):
        self._info("Print / Layout Manager — coming soon.\nUse QGIS Print Layout for now.")

    # ═══════════════════════════════════════════════════════════
    # LAYER ACTIONS
    # ═══════════════════════════════════════════════════════════
    def add_vector(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add Vector Layer", "",
            "Vector Files (*.shp *.gpkg *.geojson *.json *.kml *.gml *.csv *.tab);;All (*)")
        if path:
            self.layer_panel.load_vector(path)

    def add_raster(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add Raster Layer", "",
            "Raster Files (*.tif *.tiff *.img *.asc *.nc *.hdf *.h5 *.vrt *.jp2 *.ecw);;All (*)")
        if path:
            self.layer_panel.load_raster(path)

    def add_wms(self):
        self.layer_panel.load_osm_basemap()

    def add_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add CSV as Points", "",
            "CSV Files (*.csv);;All Files (*)")
        if path:
            self.layer_panel.load_csv(path)

    def remove_layer(self):
        self.layer_panel.remove_active_layer()

    def layer_properties(self):
        self.layer_panel.show_layer_properties()

    # ═══════════════════════════════════════════════════════════
    # VIEW ACTIONS
    # ═══════════════════════════════════════════════════════════
    def zoom_in(self):        self.map_canvas.zoom_in()
    def zoom_out(self):       self.map_canvas.zoom_out()
    def zoom_full(self):      self.map_canvas.zoom_full()
    def zoom_last(self):      self.map_canvas.zoom_last()
    def zoom_next(self):      self.map_canvas.zoom_next()
    def zoom_layer(self):     self.map_canvas.zoom_to_active_layer()
    def refresh_canvas(self): self.map_canvas.refresh_canvas()

    # ═══════════════════════════════════════════════════════════
    # MAP TOOL ACTIONS
    # ═══════════════════════════════════════════════════════════
    def set_pan_tool(self):              self.map_canvas.set_tool("pan")
    def set_zoom_in(self):               self.map_canvas.set_tool("zoom_in")
    def set_zoom_out(self):              self.map_canvas.set_tool("zoom_out")
    def set_measure_distance(self):      self.map_canvas.set_tool("measure_distance")
    def set_measure_area(self):          self.map_canvas.set_tool("measure_area")
    def set_identify_tool(self):         self.map_canvas.set_tool("identify")
    def set_select_tool(self):           self.map_canvas.set_tool("select")

    # ═══════════════════════════════════════════════════════════
    # ANALYSIS ACTIONS
    # ═══════════════════════════════════════════════════════════
    def open_buffer_dialog(self):   self.processing_dock.show(); self.processing_dock.open_tab("spatial"); self.processing_dock.spatial_widget.focus_buffer()
    def open_clip_dialog(self):     self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def open_intersect_dialog(self):self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def open_dissolve_dialog(self): self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def open_slope_dialog(self):    self.processing_dock.show(); self.processing_dock.open_tab("raster")
    def open_hillshade_dialog(self):self.processing_dock.show(); self.processing_dock.open_tab("raster")
    def open_contour_dialog(self):  self.processing_dock.show(); self.processing_dock.open_tab("raster")
    def open_satellite_dialog(self):self.processing_dock.show(); self.processing_dock.open_tab("satellite")
    def open_band_math_dialog(self):self.processing_dock.show(); self.processing_dock.open_tab("satellite")
    def toggle_processing_dock(self): self.processing_dock.setVisible(not self.processing_dock.isVisible())

    # Vector menu
    def run_centroids(self):    self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def run_convex_hull(self):  self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def run_voronoi(self):      self.processing_dock.show(); self.processing_dock.open_tab("spatial")
    def run_merge(self):        self.processing_dock.show(); self.processing_dock.open_tab("spatial")

    # Raster menu
    def raster_stats(self):     self.processing_dock.show(); self.processing_dock.open_tab("raster")
    def raster_pseudocolor(self): self.processing_dock.show(); self.processing_dock.open_tab("raster")
    def raster_reproject(self): self.processing_dock.show(); self.processing_dock.open_tab("io")
    def raster_clip(self):      self.processing_dock.show(); self.processing_dock.open_tab("raster")

    # Attribute table
    def open_attribute_table(self):
        self.attr_table_dock.show()
        self.attr_table_dock.load_active_layer(self.layer_panel.get_active_layer())

    # Settings
    def open_settings(self):    self._info("Settings dialog — coming soon.")
    def set_project_crs(self):  self._info("CRS selector — use QGIS project for now.")
    def open_docs(self):
        import webbrowser
        webbrowser.open("https://docs.qgis.org/3.34/en/docs/pyqgis_developer_cookbook/")

    def about(self):
        QMessageBox.about(self, f"About {self.APP_NAME}",
            f"<h2>🌍 {self.APP_NAME} v{self.VERSION}</h2>"
            f"<p>A standalone GIS application powered by the QGIS 3.40 engine.</p>"
            f"<p><b>Features:</b><br>"
            f"• Map canvas with pan/zoom/identify<br>"
            f"• Layer management (vector, raster, WMS)<br>"
            f"• Spatial analysis (buffer, clip, dissolve…)<br>"
            f"• DEM/Raster processing (slope, hillshade…)<br>"
            f"• Satellite & hyperspectral analysis (NDVI, EVI…)<br>"
            f"• Import/Export (10+ formats)<br>"
            f"• Attribute table viewer<br>"
            f"• Python console</p>"
            f"<p>Built with PyQGIS, PyQt5, GDAL.</p>")

    # ── Helpers ────────────────────────────────────────────────
    def _info(self, msg):
        QMessageBox.information(self, self.APP_NAME, msg)

    def _err(self, msg):
        QMessageBox.critical(self, self.APP_NAME, msg)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Exit GeoStudio",
            "Exit GeoStudio?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
