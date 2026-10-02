# -*- coding: utf-8 -*-
"""
GeoStudio - Profile Transect Line Map Tool
Draws on-canvas transect lines for terrain elevation profile extraction.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsRubberBand


class GeoProfileLineTool(QgsMapTool):
    """Draws a transect line across the terrain for elevation profiling."""

    profile_line_drawn = pyqtSignal(list)

    def __init__(self, canvas, main_window):
        super().__init__(canvas)
        self.canvas = canvas
        self.mw = main_window
        self.setCursor(Qt.CrossCursor)

        self._pts = []
        self._rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self._rubber_band.setColor(QColor(16, 185, 129, 90))       # Emerald green
        self._rubber_band.setStrokeColor(QColor(5, 150, 105, 240)) # Emerald green solid
        self._rubber_band.setWidth(3)

    def _reset(self):
        self._pts = []
        if self._rubber_band:
            self._rubber_band.reset()

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pt = self.toMapCoordinates(event.pos())
            self._pts.append(pt)
            self._rubber_band.addPoint(pt, True)
            self._rubber_band.show()
            self.mw.geo_status.showMessage(
                f"Profile Transect: {len(self._pts)} points added. [Right-click to generate profile]", 3000
            )

        elif event.button() == Qt.RightButton:
            if len(self._pts) >= 2:
                self.profile_line_drawn.emit(list(self._pts))
            self._reset()

    def canvasMoveEvent(self, event):
        if not self._pts:
            return
        curr_pt = self.toMapCoordinates(event.pos())
        preview_pts = self._pts + [curr_pt]
        self._rubber_band.setToGeometry(QgsGeometry.fromPolylineXY(preview_pts), None)
        self._rubber_band.show()

    def deactivate(self):
        self._reset()
        super().deactivate()
