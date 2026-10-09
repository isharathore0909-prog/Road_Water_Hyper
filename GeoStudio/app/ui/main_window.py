# -*- coding: utf-8 -*-
"""
GeoStudio - Main Window Coordinator
Lean coordinator that initializes canvas, menus, modular toolbars, dock panels,
and assembles modular controller mixins.
"""

import os
from PyQt5.QtWidgets import QMainWindow, QDockWidget
from PyQt5.QtCore import Qt

from .map_canvas_widget import MapCanvasWidget
from .layer_panel import LayerPanelWidget
from .browser_dock import BrowserDock
from .identify_dock import IdentifyDock
from .remote_sensing_dock import RemoteSensingDock
from .attribute_table_dock import AttributeTableDock
from .processing_dock import ProcessingDock
from .python_console_dock import PythonConsoleDock
from .status_bar import GeoStatusBar
from .menus.menu_builder import build_main_menus
from .toolbars import (
    ProjectToolBar, NavToolBar, DataSourcesToolBar, SelectionToolBar,
    MeasurementToolBar, EditToolBar, TerrainToolBar, LidarToolBar, DigitizingToolBar,
    ContextualToolBar
)
from core.style import OFFWHITE_STYLESHEET
from .controllers import (
    ProjectControllerMixin,
    NavigationControllerMixin,
    LayerControllerMixin,
    EditingControllerMixin,
    AnalysisControllerMixin,
)


class GeoStudioMainWindow(
    QMainWindow,
    ProjectControllerMixin,
    NavigationControllerMixin,
    LayerControllerMixin,
    EditingControllerMixin,
    AnalysisControllerMixin
):
    """
    GeoStudio Main Window — Standalone Professional Desktop GIS.
    Coordinates all modular toolbars, menus, canvas, docks, and controllers.
    """

    APP_NAME = "GeoStudio"
    VERSION = "1.0.0"

    def __init__(self, qgs_app=None, parent=None):
        super().__init__(parent)
        self.qgs_app = qgs_app
        self.setWindowTitle(f"{self.APP_NAME} — Standalone GIS")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 950)

        # Apply global off-white light theme by default
        self.setStyleSheet(OFFWHITE_STYLESHEET)
        self.setAcceptDrops(True)

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
        # Row 1: Core GIS Navigation & Operations
        self.tb_file = ProjectToolBar(self)
        self.tb_nav = NavToolBar(self)
        self.tb_data = DataSourcesToolBar(self)
        self.tb_selection = SelectionToolBar(self)
        self.tb_measure = MeasurementToolBar(self)
        self.tb_edit = EditToolBar(self)
        self.tb_context = ContextualToolBar(self)

        self.addToolBar(Qt.TopToolBarArea, self.tb_file)
        self.addToolBar(Qt.TopToolBarArea, self.tb_nav)
        self.addToolBar(Qt.TopToolBarArea, self.tb_data)
        self.addToolBar(Qt.TopToolBarArea, self.tb_selection)
        self.addToolBar(Qt.TopToolBarArea, self.tb_measure)
        self.addToolBar(Qt.TopToolBarArea, self.tb_edit)
        self.addToolBar(Qt.TopToolBarArea, self.tb_context)

        # Row 2: Specialized Terrain, LiDAR & Digitizing Toolbars
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.tb_terrain = TerrainToolBar(self)
        self.tb_lidar = LidarToolBar(self)
        self.tb_digitizing = DigitizingToolBar(self)

        self.addToolBar(Qt.TopToolBarArea, self.tb_terrain)
        self.addToolBar(Qt.TopToolBarArea, self.tb_lidar)
        self.addToolBar(Qt.TopToolBarArea, self.tb_digitizing)

    def _build_docks(self):
        # LEFT: Single, Clean Layers Panel
        self.layer_panel = LayerPanelWidget(self.map_canvas, self)
        self.layer_dock = QDockWidget("Layers", self)
        self.layer_dock.setObjectName("layer_dock")
        self.layer_dock.setWidget(self.layer_panel)
        self.layer_dock.setMinimumWidth(240)
        self.layer_dock.setMaximumWidth(450)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.layer_dock)

        # Secondary modules (instantiated for API/test compatibility, but completely hidden with NO right sidebar)
        self.browser_dock = BrowserDock(self, self)
        self.browser_dock.setObjectName("browser_dock")
        self.browser_dock.hide()

        self.processing_dock = ProcessingDock(self.map_canvas, self)
        self.processing_dock.setObjectName("processing_dock")
        self.processing_dock.hide()

        self.identify_dock = IdentifyDock(self, self)
        self.identify_dock.setObjectName("identify_dock")
        self.identify_dock.hide()

        self.remote_sensing_dock = RemoteSensingDock(self, self)
        self.remote_sensing_dock.setObjectName("remote_sensing_dock")
        self.remote_sensing_dock.hide()

        self.attr_table_dock = AttributeTableDock(self)
        self.attr_table_dock.setObjectName("attr_table_dock")
        self.attr_table_dock.hide()

        self.console_dock = PythonConsoleDock(self)
        self.console_dock.setObjectName("console_dock")
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
        if hasattr(self, "tb_context"):
            self.tb_context.update_context(layer)
        if hasattr(self, "attr_table_dock") and self.attr_table_dock.isVisible():
            self.attr_table_dock.load_active_layer(layer)
        if layer and hasattr(layer, "selectionChanged"):
            try:
                layer.selectionChanged.connect(lambda *args: self._update_selection_count(layer))
            except Exception:
                pass
        self._update_selection_count(layer)

    def _update_selection_count(self, layer):
        if layer and hasattr(layer, "selectedFeatureCount"):
            cnt = layer.selectedFeatureCount()
            self.geo_status.set_selected(cnt)
        else:
            self.geo_status.set_selected(0)

    def set_workspace_preset(self, preset: str = "default"):
        """Configures docks and toolbars to match standard GIS task workflows."""
        preset = preset.lower()
        # Always maintain clean two-area workspace: Left Layers Panel + Center Map Canvas
        self.layer_dock.show()
        self.browser_dock.hide()
        self.processing_dock.hide()
        self.identify_dock.hide()
        if hasattr(self, "remote_sensing_dock"):
            self.remote_sensing_dock.hide()
        self.attr_table_dock.hide()
        self.console_dock.hide()

        if preset == "editing":
            if hasattr(self, "tb_digitizing"):
                self.tb_digitizing.show()
            if hasattr(self, "tb_edit"):
                self.tb_edit.show()
        elif preset == "remotesensing":
            if hasattr(self, "tb_terrain"):
                self.tb_terrain.show()
            if hasattr(self, "tb_lidar"):
                self.tb_lidar.show()

        if hasattr(self, "geo_status"):
            self.geo_status.showMessage(f"Applied '{preset.title()}' workspace preset", 3000)

    def _update_title(self):
        self.setWindowTitle(f"{self.APP_NAME} v{self.VERSION} — Standalone GIS")

    def closeEvent(self, event):
        try:
            from qgis.core import QgsProject
            QgsProject.instance().clear()
        except Exception:
            pass
        event.accept()
