# -*- coding: utf-8 -*-
"""
GeoStudio - Contextual Action Toolbar
Dynamically adapts its toolset based on the currently selected layer and state:
- No layer: Map Navigation & Measurement
- Vector layer: Attributes, Symbology, Selection, Vector Analysis
- Raster / DEM layer: Elevation Symbology, Hillshade, Slope, Aspect, Statistics
- Point Cloud / LiDAR: 3D Viewer, Classification, DTM/CHM
- Editing Active: Add Feature, Delete, Move, Vertex, Save Edits
"""

from PyQt5.QtWidgets import QToolBar, QAction, QLabel, QWidget, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from resources.icons.icon_provider import get_icon


class ContextualToolBar(QToolBar):
    """
    Intelligent Contextual Toolbar that updates dynamically
    to prevent interface overload.
    """

    def __init__(self, main_window, parent=None):
        super().__init__("Context Actions", parent or main_window)
        self.setObjectName("contextual_toolbar")
        self.mw = main_window
        self.setMovable(True)
        self.setFloatable(False)

        self._badge = QLabel("NAVIGATION")
        self._badge.setStyleSheet("""
            background: #0f172a;
            color: #ffffff;
            font-size: 10px;
            font-weight: 700;
            border-radius: 3px;
            padding: 2px 7px;
            margin-right: 6px;
        """)

        self.update_context(None)

    def update_context(self, layer=None):
        """Rebuilds the actions according to the current active layer and state."""
        self.clear()
        self.addWidget(self._badge)

        from qgis.core import QgsVectorLayer, QgsRasterLayer
        from core.elevation_styler import ElevationStyler

        is_editing = layer is not None and isinstance(layer, QgsVectorLayer) and layer.isEditable()
        is_vector = layer is not None and isinstance(layer, QgsVectorLayer)
        is_point_cloud = layer is not None and ("PointCloud" in type(layer).__name__ or bool(layer.customProperty("is_lidar_layer", False)))
        is_raster = layer is not None and (not is_vector) and (not is_point_cloud)

        if is_editing:
            self._badge.setText(f"EDITING: {layer.name()[:20]}")
            self._badge.setStyleSheet("background: #dc2626; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 7px; margin-right: 6px;")

            self._act("Save Edits", self.mw.save_layer_edits, "save_project", "Commit and save vector edits")
            self._act("Add Feature", self.mw.start_add_feature, "add_feature", "Digitize and add new feature")
            self._act("Delete Selected", self.mw.delete_selected, "delete", "Delete selected features")
            self._act("Move Feature", self.mw.start_move_feature, "move_feature", "Move geometry")
            self._act("Vertex Tool", self.mw.start_vertex_tool, "vertex_tool", "Edit polygon / line vertices")
            self.addSeparator()
            self._act("Done Editing", self.mw.toggle_editing, "toggle_edit", "Finish editing session")

        elif is_point_cloud:
            self._badge.setText(f"POINT CLOUD: {layer.name()[:20]}")
            self._badge.setStyleSheet("background: #0284c7; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 7px; margin-right: 6px;")

            self._act("3D Viewer", self.mw.open_3d_viewer, "view_3d", "Open Point Cloud 3D Viewer")
            self._act("Classify Ground", lambda: self.mw.processing_dock.open_algorithm("lidar:classify_ground"), "classify_ground", "SMRF ground classification")
            self._act("Classify Buildings", lambda: self.mw.processing_dock.open_algorithm("lidar:classify_buildings"), "classify_buildings", "Detect building roofs")
            self._act("Generate DTM", lambda: self.mw.processing_dock.open_algorithm("lidar:generate_dtm"), "elevation", "Interpolate bare-earth raster")
            self._act("CHM Canopy", lambda: self.mw.processing_dock.open_algorithm("lidar:chm"), "classify_veg", "Canopy height model")
            self.addSeparator()
            self._act("Properties", self.mw.layer_properties, "identify", "Layer properties")

        elif is_raster:
            self._badge.setText(f"RASTER: {layer.name()[:20]}")
            self._badge.setStyleSheet("background: #b45309; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 7px; margin-right: 6px;")

            self._act("Symbology & 3D Relief", self.mw.open_dem_elevation_dialog, "elevation", "Configure DEM color ramp & hillshade")
            self._act("Hillshade", self.mw.open_hillshade_dialog, "hillshade", "Generate multidirectional hillshade")
            self._act("Slope", self.mw.open_slope_dialog, "slope", "Calculate slope gradient")
            self._act("Aspect", self.mw.open_aspect_dialog, "aspect", "Calculate aspect azimuth")
            self._act("Elevation Profile", self.mw.open_elevation_profile, "profile", "Draw profile cross-section")
            self._act("Crop / Clip", self.mw.open_crop_raster_dialog, "clip", "Clip raster by polygon mask")
            self.addSeparator()
            self._act("Statistics", self.mw.raster_stats, "layer_properties", "Compute min/max/mean stats")
            self._act("Properties", self.mw.layer_properties, "identify", "Layer properties")

        elif is_vector:
            self._badge.setText(f"VECTOR: {layer.name()[:20]}")
            self._badge.setStyleSheet("background: #15803d; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 7px; margin-right: 6px;")

            self._act("Attribute Table", self.mw.open_attribute_table, "layer_properties", "Open Attribute Table (F6)")
            self._act("Toggle Editing", self.mw.toggle_editing, "toggle_edit", "Start/stop editing session (Ctrl+E)")
            self._act("Select Features", self.mw.set_select_tool, "select_single", "Select features on canvas")
            self._act("Clear Selection", self.mw.clear_selection, "clear_selection", "Clear all selections")
            self.addSeparator()
            self._act("Buffer", self.mw.open_buffer_dialog, "buffer", "Generate distance buffer polygon")
            self._act("Clip", self.mw.open_clip_dialog, "clip", "Clip vector features")
            self._act("Centroids", self.mw.run_centroids, "centroids", "Calculate geometric centroids")
            self.addSeparator()
            self._act("Properties", self.mw.layer_properties, "identify", "Layer properties (F3)")

        else:
            self._badge.setText("MAP NAVIGATION")
            self._badge.setStyleSheet("background: #334155; color: #ffffff; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 7px; margin-right: 6px;")

            self._act("Pan", self.mw.set_pan_tool, "pan", "Pan map canvas")
            self._act("Zoom In", self.mw.set_zoom_in, "zoom_in", "Zoom into area")
            self._act("Zoom Out", self.mw.set_zoom_out, "zoom_out", "Zoom out")
            self._act("Full Extent", self.mw.zoom_full, "zoom_full", "Zoom to entire map extent")
            self.addSeparator()
            self._act("Identify", self.mw.set_identify_tool, "identify", "Identify features & pixel values")
            self._act("Measure Distance", self.mw.set_measure_distance, "measure_dist", "Measure distance along line")
            self._act("Measure Area", self.mw.set_measure_area, "measure_area", "Measure polygon area")

    def _act(self, text, slot, icon_key, tooltip=""):
        action = self.addAction(get_icon(icon_key), text)
        action.setToolTip(tooltip)
        action.setStatusTip(tooltip)
        action.triggered.connect(slot)
        return action
