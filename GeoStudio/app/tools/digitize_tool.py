# -*- coding: utf-8 -*-
"""
GeoStudio - Vector Digitizing & Geometry Editing Map Tool
Full-featured interactive tool supporting:
- Point, Line, and Polygon creation
- Vertex Tool / Node Editor (move, insert, and delete vertices)
- Move and Rotate features
- Split polygon/line features with cut lines
- Live vector snapping (vertex, segment, area)
- Multi-step Undo / Redo for vertex digitizing
"""

import math
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsProject, QgsMapLayer, QgsGeometry, QgsPointXY, QgsPoint,
    QgsRectangle, QgsFeature, QgsWkbTypes, QgsCoordinateTransform,
    QgsSnappingConfig
)
from qgis.gui import QgsMapTool, QgsRubberBand


class GeoDigitizeTool(QgsMapTool):
    """Vector digitizing tool supporting point/line/poly creation, vertex editing, move, rotate, and split."""

    feature_added = pyqtSignal(int)

    def __init__(self, canvas, main_window, tool_type="point"):
        super().__init__(canvas)
        self.canvas = canvas
        self.mw = main_window
        self.tool_type = tool_type
        self.setCursor(Qt.CrossCursor)

        self._pts = []
        self._undone_pts = []
        self._rubber_band = None
        self._hover_marker = None
        self._selected_feat = None
        self._drag_start = None
        self._vertex_index = None

        self._init_rubber_bands()

    def set_tool_type(self, tool_type: str):
        self.tool_type = tool_type
        self._reset()

    def _init_rubber_bands(self):
        if self._rubber_band:
            self._rubber_band.reset()
        if self._hover_marker:
            self._hover_marker.reset()

        geom_type = QgsWkbTypes.PolygonGeometry if self.tool_type in ("polygon", "rotate") else QgsWkbTypes.LineGeometry
        self._rubber_band = QgsRubberBand(self.canvas, geom_type)
        self._apply_style()

        self._hover_marker = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self._hover_marker.setColor(QColor(239, 68, 68, 220))
        self._hover_marker.setStrokeColor(QColor(185, 28, 28, 255))
        self._hover_marker.setWidth(8)

    def _apply_style(self):
        if not self._rubber_band:
            return
        if self.tool_type == "vertex":
            self._rubber_band.setColor(QColor(59, 130, 246, 60))        # Blue translucent
            self._rubber_band.setStrokeColor(QColor(37, 99, 235, 230))  # Blue border
        elif self.tool_type in ("move", "rotate"):
            self._rubber_band.setColor(QColor(16, 185, 129, 60))        # Green translucent
            self._rubber_band.setStrokeColor(QColor(5, 150, 105, 230))  # Green border
        elif self.tool_type == "split":
            self._rubber_band.setColor(QColor(239, 68, 68, 70))
            self._rubber_band.setStrokeColor(QColor(220, 38, 38, 240))  # Red cut line
        else:
            self._rubber_band.setColor(QColor(245, 158, 11, 75))        # Amber fill
            self._rubber_band.setStrokeColor(QColor(217, 119, 6, 230))  # Amber border
        self._rubber_band.setWidth(2)

    def _reset(self):
        self._pts = []
        self._undone_pts = []
        self._selected_feat = None
        self._drag_start = None
        self._vertex_index = None
        if self._rubber_band:
            self._rubber_band.reset()
        if self._hover_marker:
            self._hover_marker.reset()

    def _get_editable_layer(self):
        layer = self.mw.layer_panel.get_active_layer() if hasattr(self.mw, "layer_panel") else None
        if not layer or layer.type() != QgsMapLayer.VectorLayer:
            reply = QMessageBox.question(
                self.mw,
                "Create Vector Layer",
                f"Digitizing creates vector features (points, lines, polygons).\n\n"
                f"Would you like to create a new '{self.tool_type.capitalize()}' vector layer to draw on top of your current map/raster?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                return self._create_scratch_layer()
            return None

        if not layer.isEditable():
            reply = QMessageBox.question(
                self.mw,
                "Start Editing",
                f"Layer '{layer.name()}' is not in edit mode.\nWould you like to start editing now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
                self.canvas.refresh()
                self.mw.geo_status.showMessage(f"Editing started for '{layer.name()}'.", 2500)
            else:
                return None
        return layer

    def _create_scratch_layer(self):
        try:
            from qgis.core import QgsVectorLayer, QgsField
            dest_crs = self.canvas.mapSettings().destinationCrs()
            crs_str = dest_crs.authid() if dest_crs.isValid() else "EPSG:4326"
            geom_type = "Polygon" if self.tool_type in ("polygon", "rotate") else ("LineString" if self.tool_type in ("line", "split") else "Point")
            layer_name = f"Digitized {geom_type}s"
            layer = QgsVectorLayer(f"{geom_type}?crs={crs_str}", layer_name, "memory")
            if layer.isValid():
                pr = layer.dataProvider()
                pr.addAttributes([QgsField("name")])
                layer.updateFields()
                QgsProject.instance().addMapLayer(layer)
                layer.startEditing()
                if hasattr(self.mw, "layer_panel"):
                    self.mw.layer_panel.refresh()
                    self.mw.layer_panel.set_active_layer(layer)
                self.mw.geo_status.showMessage(f"Created new vector layer '{layer_name}'. Ready to draw.", 3500)
                return layer
        except Exception as e:
            self.mw.geo_status.showMessage(f"Could not create layer: {e}", 3000)
        return None

    def _snap_point(self, pt, layer):
        """Snaps map coordinate to nearest vertex or segment if snapping is enabled."""
        cfg = QgsProject.instance().snappingConfig()
        if not cfg.enabled():
            return pt

        tol = self.canvas.mapUnitsPerPixel() * 15
        rect = QgsRectangle(pt.x() - tol, pt.y() - tol, pt.x() + tol, pt.y() + tol)

        layers_to_check = [layer] if layer else []
        for l in QgsProject.instance().mapLayers().values():
            if l.type() == QgsMapLayer.VectorLayer and l.isValid() and l not in layers_to_check:
                layers_to_check.append(l)

        best_pt = pt
        min_dist_sq = tol * tol

        for l in layers_to_check:
            for feat in l.getFeatures(rect):
                geom = feat.geometry()
                if not geom or geom.isEmpty():
                    continue

                # Check vertex snap
                if cfg.typeFlag() & QgsSnappingConfig.VertexFlag:
                    closest_pt, vidx, prev_idx, next_idx, dsq = geom.closestVertex(pt)
                    if dsq < min_dist_sq:
                        min_dist_sq = dsq
                        best_pt = closest_pt

                # Check segment snap
                if cfg.typeFlag() & QgsSnappingConfig.SegmentFlag and min_dist_sq == tol * tol:
                    res, seg_pt, after_idx, left_of = geom.closestSegmentWithContext(pt)
                    if res >= 0:
                        dsq = seg_pt.distanceSquared(pt)
                        if dsq < min_dist_sq:
                            min_dist_sq = dsq
                            best_pt = seg_pt

        return best_pt

    def canvasPressEvent(self, event):
        layer = self._get_editable_layer()
        if not layer:
            return

        raw_pt = self.toMapCoordinates(event.pos())
        pt = self._snap_point(raw_pt, layer)

        if event.button() == Qt.LeftButton:
            if self.tool_type == "point":
                self._add_point_feature(layer, pt)

            elif self.tool_type in ("line", "polygon", "split"):
                self._pts.append(pt)
                self._undone_pts.clear()
                self._update_rubber_band()

            elif self.tool_type == "vertex":
                self._drag_start = pt
                feat, vidx, vpt = self._find_vertex_at(layer, pt)
                if feat and vidx >= 0:
                    self._selected_feat = feat
                    self._vertex_index = vidx
                    self._rubber_band.setToGeometry(feat.geometry(), None)
                    self._rubber_band.show()
                else:
                    # Check if user clicked on segment to insert new vertex
                    feat, seg_pt, after_idx = self._find_segment_at(layer, pt)
                    if feat and after_idx >= 0:
                        layer.insertVertex(pt.x(), pt.y(), feat.id(), after_idx)
                        self.canvas.refresh()
                        self.mw.geo_status.showMessage(f"Inserted new vertex in feature #{feat.id()}.", 2500)

            elif self.tool_type in ("move", "rotate"):
                self._drag_start = pt
                self._selected_feat = self._find_feature_at(layer, pt)
                if self._selected_feat:
                    self._rubber_band.setToGeometry(self._selected_feat.geometry(), None)
                    self._rubber_band.show()
                else:
                    self.mw.geo_status.showMessage("Click directly on a feature to move/rotate.", 2000)

        elif event.button() == Qt.RightButton:
            if self.tool_type == "line" and len(self._pts) >= 2:
                self._add_line_feature(layer)
            elif self.tool_type == "polygon" and len(self._pts) >= 3:
                self._add_polygon_feature(layer)
            elif self.tool_type == "split" and len(self._pts) >= 2:
                self._split_feature(layer)
            elif self.tool_type == "vertex" and self._selected_feat and self._vertex_index is not None:
                # Right click on selected vertex deletes it
                layer.deleteVertex(self._selected_feat.id(), self._vertex_index)
                self.canvas.refresh()
                self.mw.geo_status.showMessage(f"Deleted vertex #{self._vertex_index}.", 2500)
            self._reset()

    def canvasMoveEvent(self, event):
        raw_pt = self.toMapCoordinates(event.pos())
        layer = self.mw.layer_panel.get_active_layer() if hasattr(self.mw, "layer_panel") else None
        curr_pt = self._snap_point(raw_pt, layer)

        if self.tool_type in ("line", "polygon", "split") and self._pts:
            preview_pts = self._pts + [curr_pt]
            self._update_rubber_band(preview_pts)

        elif self.tool_type == "vertex":
            if self._drag_start and self._selected_feat and self._vertex_index is not None:
                # Preview moved vertex
                geom = QgsGeometry(self._selected_feat.geometry())
                geom.moveVertex(curr_pt.x(), curr_pt.y(), self._vertex_index)
                self._rubber_band.setToGeometry(geom, None)
                self._rubber_band.show()
            elif layer:
                # Highlight hovered vertex
                _, _, vpt = self._find_vertex_at(layer, curr_pt)
                if vpt and self._hover_marker:
                    self._hover_marker.setToGeometry(QgsGeometry.fromPointXY(vpt), None)
                    self._hover_marker.show()
                elif self._hover_marker:
                    self._hover_marker.reset(QgsWkbTypes.PointGeometry)

        elif self.tool_type == "move" and self._drag_start and self._selected_feat:
            dx = curr_pt.x() - self._drag_start.x()
            dy = curr_pt.y() - self._drag_start.y()
            geom = QgsGeometry(self._selected_feat.geometry())
            geom.translate(dx, dy)
            self._rubber_band.setToGeometry(geom, None)
            self._rubber_band.show()

        elif self.tool_type == "rotate" and self._drag_start and self._selected_feat:
            center = self._selected_feat.geometry().centroid().asPoint()
            angle1 = math.atan2(self._drag_start.y() - center.y(), self._drag_start.x() - center.x())
            angle2 = math.atan2(curr_pt.y() - center.y(), curr_pt.x() - center.x())
            diff_deg = math.degrees(angle2 - angle1)
            geom = QgsGeometry(self._selected_feat.geometry())
            geom.rotate(diff_deg, center)
            self._rubber_band.setToGeometry(geom, None)
            self._rubber_band.show()

    def canvasReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        layer = self.mw.layer_panel.get_active_layer() if hasattr(self.mw, "layer_panel") else None
        if not layer or not layer.isEditable():
            return

        raw_pt = self.toMapCoordinates(event.pos())
        curr_pt = self._snap_point(raw_pt, layer)

        if self.tool_type == "vertex" and self._drag_start and self._selected_feat and self._vertex_index is not None:
            layer.moveVertex(curr_pt.x(), curr_pt.y(), self._selected_feat.id(), self._vertex_index)
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Moved vertex #{self._vertex_index} of feature #{self._selected_feat.id()}.", 2500)
            self._reset()

        elif self.tool_type == "move" and self._drag_start and self._selected_feat:
            dx = curr_pt.x() - self._drag_start.x()
            dy = curr_pt.y() - self._drag_start.y()
            layer.translateFeature(self._selected_feat.id(), dx, dy)
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Moved feature #{self._selected_feat.id()}.", 2500)
            self._reset()

        elif self.tool_type == "rotate" and self._drag_start and self._selected_feat:
            center = self._selected_feat.geometry().centroid().asPoint()
            angle1 = math.atan2(self._drag_start.y() - center.y(), self._drag_start.x() - center.x())
            angle2 = math.atan2(curr_pt.y() - center.y(), curr_pt.x() - center.x())
            diff_deg = math.degrees(angle2 - angle1)
            geom = QgsGeometry(self._selected_feat.geometry())
            geom.rotate(diff_deg, center)
            layer.changeGeometry(self._selected_feat.id(), geom)
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Rotated feature #{self._selected_feat.id()} by {diff_deg:.1f}°.", 2500)
            self._reset()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.undo_last_point()
        elif event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            self.undo_last_point()
        elif event.key() == Qt.Key_Y and (event.modifiers() & Qt.ControlModifier):
            self.redo_last_point()
        elif event.key() == Qt.Key_Escape:
            self._reset()
            self.mw.geo_status.showMessage("Digitizing buffer cleared.", 2000)
        else:
            super().keyPressEvent(event)

    def _find_feature_at(self, layer, pt):
        tol = self.canvas.mapUnitsPerPixel() * 12
        rect = QgsRectangle(pt.x() - tol, pt.y() - tol, pt.x() + tol, pt.y() + tol)
        for feat in layer.getFeatures(rect):
            if feat.geometry() and feat.geometry().intersects(rect):
                return feat
        return None

    def _find_vertex_at(self, layer, pt):
        tol = self.canvas.mapUnitsPerPixel() * 12
        rect = QgsRectangle(pt.x() - tol, pt.y() - tol, pt.x() + tol, pt.y() + tol)
        tol_sq = tol * tol
        for feat in layer.getFeatures(rect):
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue
            closest_pt, vidx, _, _, dsq = geom.closestVertex(pt)
            if dsq <= tol_sq:
                return feat, vidx, closest_pt
        return None, -1, None

    def _find_segment_at(self, layer, pt):
        tol = self.canvas.mapUnitsPerPixel() * 10
        rect = QgsRectangle(pt.x() - tol, pt.y() - tol, pt.x() + tol, pt.y() + tol)
        tol_sq = tol * tol
        for feat in layer.getFeatures(rect):
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue
            res, seg_pt, after_idx, _ = geom.closestSegmentWithContext(pt)
            if res >= 0 and seg_pt.distanceSquared(pt) <= tol_sq:
                return feat, seg_pt, after_idx
        return None, None, -1

    def _add_point_feature(self, layer, pt):
        feat = QgsFeature(layer.fields())
        dest_crs = self.canvas.mapSettings().destinationCrs()
        if dest_crs.isValid() and layer.crs().isValid() and dest_crs != layer.crs():
            tr = QgsCoordinateTransform(dest_crs, layer.crs(), QgsProject.instance())
            pt = tr.transform(pt)
        feat.setGeometry(QgsGeometry.fromPointXY(pt))
        success = layer.addFeature(feat)
        if success:
            layer.updateExtents()
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Added Point to '{layer.name()}'.", 3000)
            self.feature_added.emit(feat.id())

    def _add_line_feature(self, layer):
        pts = list(self._pts)
        dest_crs = self.canvas.mapSettings().destinationCrs()
        if dest_crs.isValid() and layer.crs().isValid() and dest_crs != layer.crs():
            tr = QgsCoordinateTransform(dest_crs, layer.crs(), QgsProject.instance())
            pts = [tr.transform(p) for p in pts]
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromPolylineXY(pts))
        success = layer.addFeature(feat)
        if success:
            layer.updateExtents()
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Added Line ({len(pts)} vertices) to '{layer.name()}'.", 3000)
            self.feature_added.emit(feat.id())

    def _add_polygon_feature(self, layer):
        pts = list(self._pts)
        dest_crs = self.canvas.mapSettings().destinationCrs()
        if dest_crs.isValid() and layer.crs().isValid() and dest_crs != layer.crs():
            tr = QgsCoordinateTransform(dest_crs, layer.crs(), QgsProject.instance())
            pts = [tr.transform(p) for p in pts]
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts + [pts[0]]]))
        success = layer.addFeature(feat)
        if success:
            layer.updateExtents()
            self.canvas.refresh()
            self.mw.geo_status.showMessage(f"Added Polygon ({len(pts)} vertices) to '{layer.name()}'.", 3000)
            self.feature_added.emit(feat.id())

    def _split_feature(self, layer):
        pts = list(self._pts)
        if len(pts) < 2:
            return
        dest_crs = self.canvas.mapSettings().destinationCrs()
        if dest_crs.isValid() and layer.crs().isValid() and dest_crs != layer.crs():
            tr = QgsCoordinateTransform(dest_crs, layer.crs(), QgsProject.instance())
            pts = [tr.transform(p) for p in pts]

        res = layer.splitFeatures(pts, 1)
        self.canvas.refresh()
        self.mw.geo_status.showMessage(f"Split feature completed (Result: {res}).", 3000)

    def _update_rubber_band(self, pts=None):
        if not self._rubber_band:
            return
        target_pts = pts if pts is not None else self._pts
        if not target_pts:
            self._rubber_band.reset()
            return

        if self.tool_type == "polygon":
            if len(target_pts) >= 3:
                self._rubber_band.reset(QgsWkbTypes.PolygonGeometry)
                self._apply_style()
                closed = list(target_pts) + [target_pts[0]]
                self._rubber_band.setToGeometry(QgsGeometry.fromPolygonXY([closed]), None)
            elif len(target_pts) == 2:
                self._rubber_band.reset(QgsWkbTypes.LineGeometry)
                self._apply_style()
                self._rubber_band.setToGeometry(QgsGeometry.fromPolylineXY(target_pts), None)
            elif len(target_pts) == 1:
                self._rubber_band.reset(QgsWkbTypes.PointGeometry)
                self._apply_style()
                self._rubber_band.setWidth(6)
                self._rubber_band.setToGeometry(QgsGeometry.fromPointXY(target_pts[0]), None)
        else: # line or split
            if len(target_pts) >= 2:
                self._rubber_band.reset(QgsWkbTypes.LineGeometry)
                self._apply_style()
                self._rubber_band.setToGeometry(QgsGeometry.fromPolylineXY(target_pts), None)
            elif len(target_pts) == 1:
                self._rubber_band.reset(QgsWkbTypes.PointGeometry)
                self._apply_style()
                self._rubber_band.setWidth(6)
                self._rubber_band.setToGeometry(QgsGeometry.fromPointXY(target_pts[0]), None)

        self._rubber_band.show()

    def undo_last_point(self):
        """Removes the last digitized point and stores it in redo stack."""
        if self._pts:
            popped = self._pts.pop()
            self._undone_pts.append(popped)
            self._update_rubber_band()
            self.mw.geo_status.showMessage("Removed last digitized vertex (Undo).", 2000)
            return True
        return False

    def redo_last_point(self):
        """Restores the last undone point to the digitizing buffer."""
        if self._undone_pts:
            restored = self._undone_pts.pop()
            self._pts.append(restored)
            self._update_rubber_band()
            self.mw.geo_status.showMessage("Restored digitized vertex (Redo).", 2000)
            return True
        return False

    def deactivate(self):
        self._reset()
        super().deactivate()
