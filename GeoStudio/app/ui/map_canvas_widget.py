# -*- coding: utf-8 -*-
"""GeoStudio - Map Canvas Widget (core of the application)."""

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor


class MapCanvasWidget(QWidget):
    """
    Wraps the QGIS QgsMapCanvas inside a QWidget.
    Falls back to a placeholder if QGIS is not available.
    """

    coordinate_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = None
        self._pan_tool = None
        self._zoom_in_tool = None
        self._zoom_out_tool = None
        self._measure_tool = None
        self._identify_tool = None
        self._select_tool = None
        self._rubber_band = None
        self._zoom_history = []
        self._zoom_idx = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            from qgis.gui import QgsMapCanvas
            from qgis.core import QgsProject, QgsCoordinateReferenceSystem

            self.canvas = QgsMapCanvas()
            self.canvas.setCanvasColor(QColor("#1e272c"))
            self.canvas.enableAntiAliasing(True)
            self.canvas.setWheelFactor(2)

            # Connect mouse move for coordinates
            self.canvas.xyCoordinates.connect(self._on_coord_changed)

            layout.addWidget(self.canvas)
            self._setup_tools()

            # Connect to project layer registry
            QgsProject.instance().layersAdded.connect(self._on_layers_changed)
            QgsProject.instance().layersRemoved.connect(self._on_layers_changed)

        except ImportError:
            # Fallback placeholder
            lbl = QLabel("⚠ QGIS canvas not available.\nRun via GeoStudio.bat to load QGIS engine.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #ff8a65; font-size: 14px; background: #1e272c;")
            layout.addWidget(lbl)

        self.setLayout(layout)

    def _setup_tools(self):
        if not self.canvas:
            return
        try:
            from qgis.gui import (
                QgsMapToolPan, QgsMapToolZoom,
                QgsMapToolEmitPoint, QgsMapToolIdentifyFeature,
                QgsMapToolSelect
            )
            self._pan_tool     = QgsMapToolPan(self.canvas)
            self._zoom_in_tool  = QgsMapToolZoom(self.canvas, False)
            self._zoom_out_tool = QgsMapToolZoom(self.canvas, True)
            self.canvas.setMapTool(self._pan_tool)
        except Exception:
            pass

    def _on_coord_changed(self, point):
        self.coordinate_changed.emit(point.x(), point.y())

    def _on_layers_changed(self, *args):
        self.refresh_canvas()

    def set_tool(self, tool_name: str):
        if not self.canvas:
            return
        tool_map = {
            "pan":              self._pan_tool,
            "zoom_in":          self._zoom_in_tool,
            "zoom_out":         self._zoom_out_tool,
        }
        tool = tool_map.get(tool_name)
        if tool:
            self.canvas.setMapTool(tool)
        elif tool_name in ("measure_distance", "measure_area", "identify", "select"):
            # Use QGIS built-in tools if available
            try:
                from qgis.gui import QgsMapToolMeasure, QgsMapToolIdentify
                if tool_name == "measure_distance":
                    from qgis.gui import QgsMapToolMeasure
                    from qgis.core import QgsWkbTypes
                    t = QgsMapToolMeasure(self.canvas, QgsWkbTypes.LineGeometry)
                    self.canvas.setMapTool(t)
                elif tool_name == "measure_area":
                    from qgis.gui import QgsMapToolMeasure
                    from qgis.core import QgsWkbTypes
                    t = QgsMapToolMeasure(self.canvas, QgsWkbTypes.PolygonGeometry)
                    self.canvas.setMapTool(t)
            except Exception:
                pass

    def add_layer_to_canvas(self, layer):
        """Add a layer to the map canvas display."""
        if not self.canvas:
            return
        try:
            from qgis.core import QgsProject
            QgsProject.instance().addMapLayer(layer)
            self.refresh_layers()
        except Exception:
            pass

    def refresh_layers(self):
        """Refresh which layers are shown on canvas."""
        if not self.canvas:
            return
        try:
            from qgis.core import QgsProject
            layers = list(QgsProject.instance().mapLayers().values())
            self.canvas.setLayers(layers)
            self.canvas.refresh()
        except Exception:
            pass

    def refresh_canvas(self):
        if self.canvas:
            self.canvas.refresh()

    def zoom_in(self):
        if self.canvas:
            self.canvas.zoomIn()

    def zoom_out(self):
        if self.canvas:
            self.canvas.zoomOut()

    def zoom_full(self):
        if self.canvas:
            self.canvas.zoomToFullExtent()

    def zoom_last(self):
        if self.canvas:
            self.canvas.zoomToPreviousExtent()

    def zoom_next(self):
        if self.canvas:
            self.canvas.zoomToNextExtent()

    def zoom_to_active_layer(self):
        if self.canvas:
            try:
                from qgis.core import QgsProject
                layers = list(QgsProject.instance().mapLayers().values())
                if layers:
                    self.canvas.setExtent(layers[0].extent())
                    self.canvas.refresh()
            except Exception:
                pass

    def get_canvas(self):
        return self.canvas

    def get_scale(self):
        if self.canvas:
            return self.canvas.scale()
        return 1.0

    def get_crs(self):
        if self.canvas:
            return self.canvas.mapSettings().destinationCrs().authid()
        return "EPSG:4326"
