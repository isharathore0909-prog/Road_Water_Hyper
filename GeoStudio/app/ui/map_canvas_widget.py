# -*- coding: utf-8 -*-
"""GeoStudio - Map Canvas Widget (core of the application)."""

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor

from core.elevation_styler import ElevationStyler
from ui.elevation_legend_widget import ElevationLegendWidget


class MapCanvasWidget(QWidget):
    """
    Wraps the QGIS QgsMapCanvas inside a QWidget.
    Maintains synchronization with QgsProject via QgsLayerTreeMapCanvasBridge.
    Provides real-time coordinates and elevation sampling.
    Features an off-white background (#f8f9fa) and on-canvas elevation legend like Global Mapper.
    """

    coordinate_changed = pyqtSignal(float, float)
    elevation_changed = pyqtSignal(object)  # float or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = None
        self.bridge = None
        self.elevation_legend = None
        self._pan_tool = None
        self._zoom_in_tool = None
        self._zoom_out_tool = None
        self._measure_tool = None
        self._identify_tool = None
        self._select_tool = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            from qgis.gui import QgsMapCanvas, QgsLayerTreeMapCanvasBridge
            from qgis.core import QgsProject, QgsCoordinateReferenceSystem

            self.canvas = QgsMapCanvas(self)
            # Off-white map background (#f8f9fa)
            self.canvas.setCanvasColor(QColor("#f8f9fa"))
            self.canvas.enableAntiAliasing(True)
            self.canvas.setWheelFactor(1.2)  # Smooth zoom factor

            # Multi-threaded rendering and layer caching
            try:
                self.canvas.setParallelRenderingEnabled(True)
                self.canvas.setCachingEnabled(True)
                self.canvas.setMapUpdateInterval(100)
            except Exception:
                pass

            # Connect mouse move for coordinates & elevation
            self.canvas.xyCoordinates.connect(self._on_coord_changed)

            # Initialize Default CRS if project is empty
            proj = QgsProject.instance()
            if not proj.crs().isValid() or not proj.crs().authid():
                default_crs = QgsCoordinateReferenceSystem("EPSG:4326")
                proj.setCrs(default_crs)
                self.canvas.setDestinationCrs(default_crs)
            else:
                self.canvas.setDestinationCrs(proj.crs())

            # Connect Project Layer Tree to Canvas Bridge
            self.bridge = QgsLayerTreeMapCanvasBridge(proj.layerTreeRoot(), self.canvas)

            layout.addWidget(self.canvas)
            self._setup_tools()

            # Floating On-Canvas Elevation Legend (like Global Mapper)
            self.elevation_legend = ElevationLegendWidget(self.canvas)
            self.elevation_legend.move(14, 14)

            # Connect project signals
            proj.layersAdded.connect(self._on_layers_added)
            proj.layersRemoved.connect(self._on_layers_changed)
            proj.crsChanged.connect(self._on_project_crs_changed)

        except ImportError as e:
            # Fallback placeholder
            lbl = QLabel(f"⚠ QGIS canvas not available: {e}\nRun via GeoStudio.bat to load QGIS engine.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #dc2626; font-size: 14px; background: #f8fafc;")
            layout.addWidget(lbl)

        self.setLayout(layout)

    def set_canvas_background(self, color_str: str = "#f8f9fa"):
        """Sets the canvas background color (off-white / dark / custom)."""
        if self.canvas:
            self.canvas.setCanvasColor(QColor(color_str))
            self.canvas.refresh()

    def update_elevation_legend(self, layer=None):
        """Updates the on-screen elevation legend for the active layer."""
        if not self.elevation_legend:
            return
        if layer and ElevationStyler.is_dem_or_elevation(layer):
            self.elevation_legend.update_from_layer(layer)
        else:
            # Find any active DEM in project
            try:
                from qgis.core import QgsProject
                dem_layers = [
                    l for l in QgsProject.instance().mapLayers().values()
                    if ElevationStyler.is_dem_or_elevation(l)
                ]
                if dem_layers:
                    self.elevation_legend.update_from_layer(dem_layers[-1])
                else:
                    self.elevation_legend.hide()
            except Exception:
                self.elevation_legend.hide()

    def toggle_elevation_legend(self):
        if self.elevation_legend:
            self.elevation_legend.setVisible(not self.elevation_legend.isVisible())

    def _setup_tools(self):
        if not self.canvas:
            return
        try:
            from qgis.gui import QgsMapToolPan, QgsMapToolZoom
            self._pan_tool = QgsMapToolPan(self.canvas)
            self._zoom_in_tool = QgsMapToolZoom(self.canvas, False)
            self._zoom_out_tool = QgsMapToolZoom(self.canvas, True)
            self.canvas.setMapTool(self._pan_tool)
        except Exception:
            pass

    def _on_coord_changed(self, point):
        self.coordinate_changed.emit(point.x(), point.y())
        elev = self._sample_elevation_at_point(point)
        self.elevation_changed.emit(elev)

    def _sample_elevation_at_point(self, point):
        """Samples the elevation of the highest visible raster/DEM layer under point."""
        try:
            from qgis.core import QgsProject, QgsMapLayer
            map_crs = self.canvas.mapSettings().destinationCrs() if self.canvas else None
            layers = list(QgsProject.instance().mapLayers().values())
            
            for layer in reversed(layers):
                if layer.type() == QgsMapLayer.RasterLayer and layer.isValid():
                    node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
                    if node and not node.isVisible():
                        continue
                    val, _ = ElevationStyler.sample_elevation_at_point(layer, point, map_crs=map_crs, band=1)
                    if val is not None:
                        return val
        except Exception:
            pass
        return None

    def _on_project_crs_changed(self):
        try:
            from qgis.core import QgsProject
            crs = QgsProject.instance().crs()
            if self.canvas and crs.isValid():
                self.canvas.setDestinationCrs(crs)
                self.canvas.refresh()
        except Exception:
            pass

    def _on_layers_added(self, layers):
        try:
            from qgis.core import QgsProject
            proj = QgsProject.instance()
            for layer in layers:
                if layer.isValid() and layer.crs().isValid():
                    valid_others = [l for l in proj.mapLayers().values() if l.isValid() and l.id() != layer.id()]
                    if not valid_others or proj.crs().authid() == "EPSG:4326":
                        proj.setCrs(layer.crs())
                        if self.canvas:
                            self.canvas.setDestinationCrs(layer.crs())
                    self.zoom_to_layer(layer)
                    if ElevationStyler.is_dem_or_elevation(layer):
                        self.update_elevation_legend(layer)
                    break
        except Exception:
            pass
        self.refresh_canvas()

    def _on_layers_changed(self, *args):
        self.update_elevation_legend()
        self.refresh_canvas()

    def set_tool(self, tool_name: str):
        if not self.canvas:
            return
        tool_map = {
            "pan":      self._pan_tool,
            "zoom_in":  self._zoom_in_tool,
            "zoom_out": self._zoom_out_tool,
        }
        tool = tool_map.get(tool_name)
        if tool:
            self.canvas.setMapTool(tool)
        elif tool_name in ("measure_distance", "measure_area", "identify", "select"):
            try:
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
                elif tool_name == "identify":
                    from qgis.gui import QgsMapToolIdentifyFeature
                    t = QgsMapToolIdentifyFeature(self.canvas)
                    self.canvas.setMapTool(t)
            except Exception:
                pass

    def add_layer_to_canvas(self, layer):
        """Add a layer to the map canvas display."""
        if not self.canvas or not layer:
            return
        try:
            from qgis.core import QgsProject
            QgsProject.instance().addMapLayer(layer)
            self.zoom_to_layer(layer)
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
            self.canvas.refresh()

    def zoom_out(self):
        if self.canvas:
            self.canvas.zoomOut()
            self.canvas.refresh()

    def zoom_full(self):
        if self.canvas:
            self.canvas.zoomToFullExtent()
            self.canvas.refresh()

    def zoom_last(self):
        if self.canvas:
            self.canvas.zoomToPreviousExtent()
            self.canvas.refresh()

    def zoom_next(self):
        if self.canvas:
            self.canvas.zoomToNextExtent()
            self.canvas.refresh()

    def zoom_to_layer(self, layer):
        """Zooms and centers the canvas on the given layer extent with padding."""
        if not layer or not layer.isValid() or not self.canvas:
            return
        try:
            from qgis.core import QgsProject, QgsCoordinateTransform
            if layer.crs().isValid():
                dest_crs = layer.crs()
                self.canvas.setDestinationCrs(dest_crs)
                QgsProject.instance().setCrs(dest_crs)
            else:
                dest_crs = self.canvas.mapSettings().destinationCrs()

            extent = layer.extent()
            if extent.isNull() or extent.isEmpty():
                return

            if dest_crs.isValid() and layer.crs().isValid() and dest_crs != layer.crs():
                try:
                    tr = QgsCoordinateTransform(layer.crs(), dest_crs, QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)
                except Exception:
                    pass

            extent.scale(1.05)  # 5% padding
            self.canvas.setExtent(extent)
            self.canvas.refresh()
        except Exception:
            pass

    def zoom_to_active_layer(self, layer=None):
        if layer and layer.isValid():
            self.zoom_to_layer(layer)
            return
        if self.canvas:
            try:
                from qgis.core import QgsProject
                layers = list(QgsProject.instance().mapLayers().values())
                if layers:
                    self.zoom_to_layer(layers[-1])
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
            crs = self.canvas.mapSettings().destinationCrs()
            if crs.isValid() and crs.authid():
                return crs.authid()
        try:
            from qgis.core import QgsProject
            crs = QgsProject.instance().crs()
            if crs.isValid() and crs.authid():
                return crs.authid()
        except Exception:
            pass
        return "EPSG:4326"
