# -*- coding: utf-8 -*-
"""
GeoStudio - Interactive Map Identify Tool
Click any vector or raster layer on the map canvas to inspect attributes,
geometry metrics, or raster band pixel values in the Identify Dock.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor
from qgis.core import (
    QgsProject, QgsMapLayer, QgsRectangle, QgsFeatureRequest,
    QgsWkbTypes, QgsPointXY
)
from qgis.gui import QgsMapTool, QgsRubberBand


class GeoIdentifyTool(QgsMapTool):
    """
    Map canvas tool that identifies features and pixel values.
    Supports Vector layers (attributes & geometry) and Raster layers (band sampling).
    """

    feature_identified = pyqtSignal(object, object)  # (layer, feature)
    raster_identified = pyqtSignal(object, object, dict)  # (layer, point, values)

    def __init__(self, canvas, main_window=None):
        super().__init__(canvas)
        self.canvas = canvas
        self.mw = main_window
        self.setCursor(Qt.CrossCursor)

        self._rubber_band = None
        self._init_rubber_band()

    def _init_rubber_band(self):
        if self._rubber_band:
            self._rubber_band.reset()
        self._rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self._rubber_band.setColor(QColor(234, 179, 8, 80))          # Semi-transparent amber
        self._rubber_band.setStrokeColor(QColor(202, 138, 4, 240))   # Deep gold border
        self._rubber_band.setWidth(2)

    def canvasReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self.canvas:
            return

        map_pt = self.toMapCoordinates(event.pos())
        layer = self._get_target_layer()
        if not layer or not layer.isValid():
            return

        if layer.type() == QgsMapLayer.VectorLayer:
            self._identify_vector(layer, map_pt)
        elif layer.type() == QgsMapLayer.RasterLayer:
            self._identify_raster(layer, map_pt)

    def _get_target_layer(self):
        # 1. Prefer currently active layer in Layer Panel
        if self.mw and hasattr(self.mw, "layer_panel"):
            active = self.mw.layer_panel.get_active_layer()
            if active and active.isValid():
                return active

        # 2. Fall back to top visible layer in project
        proj = QgsProject.instance()
        for l in proj.mapLayers().values():
            if l.isValid():
                return l
        return None

    def _identify_vector(self, layer, point):
        # Search radius around click point (10 screen pixels)
        mu_per_px = self.canvas.mapUnitsPerPixel()
        radius = mu_per_px * 10.0
        rect = QgsRectangle(
            point.x() - radius, point.y() - radius,
            point.x() + radius, point.y() + radius
        )

        req = QgsFeatureRequest().setFilterRect(rect)
        features = list(layer.getFeatures(req))

        if not features:
            # Fall back to nearest feature within 30 pixels
            wide_radius = mu_per_px * 30.0
            wide_rect = QgsRectangle(
                point.x() - wide_radius, point.y() - wide_radius,
                point.x() + wide_radius, point.y() + wide_radius
            )
            features = list(layer.getFeatures(QgsFeatureRequest().setFilterRect(wide_rect)))

        if features:
            # Pick first/closest feature
            target_feat = features[0]

            # Highlight with rubber band
            if self._rubber_band:
                self._rubber_band.reset(target_feat.geometry().type())
                self._rubber_band.setToGeometry(target_feat.geometry(), layer)
                self._rubber_band.show()

            self.feature_identified.emit(layer, target_feat)
            if self.mw and hasattr(self.mw, "identify_dock"):
                self.mw.identify_dock.show_feature(layer, target_feat)

    def _identify_raster(self, layer, point):
        dp = layer.dataProvider()
        if not dp:
            return

        values = {}
        for b in range(1, layer.bandCount() + 1):
            b_name = layer.bandName(b) or f"Band {b}"
            val, ok = dp.sample(point, b)
            if ok:
                values[b_name] = val
            else:
                values[b_name] = "NoData"

        self.raster_identified.emit(layer, point, values)
        if self.mw and hasattr(self.mw, "identify_dock"):
            self.mw.identify_dock.show_raster_value(layer, point, values)

    def deactivate(self):
        if self._rubber_band:
            self._rubber_band.reset()
        super().deactivate()
