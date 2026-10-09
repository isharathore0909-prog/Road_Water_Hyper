# -*- coding: utf-8 -*-
"""
GeoStudio - Map Navigation, Tools, Selection & Measurement Controller Mixin
"""


class NavigationControllerMixin:
    """Handles canvas zooming, panning, interactive tools, selection, and measurements."""

    def zoom_in(self):
        self.map_canvas.zoom_in()

    def zoom_out(self):
        self.map_canvas.zoom_out()

    def zoom_full(self):
        self.map_canvas.zoom_full()

    def zoom_last(self):
        self.map_canvas.zoom_last()

    def zoom_next(self):
        self.map_canvas.zoom_next()

    def refresh_canvas(self):
        self.map_canvas.refresh_canvas()

    def set_pan_tool(self):
        self.map_canvas.set_tool("pan")

    def set_zoom_in(self):
        self.map_canvas.set_tool("zoom_in")

    def set_zoom_out(self):
        self.map_canvas.set_tool("zoom_out")

    def set_identify_tool(self):
        from tools.interactive_tools import GeoIdentifyTool
        tool = GeoIdentifyTool(self.map_canvas.canvas, self)
        self.map_canvas.canvas.setMapTool(tool)
        if hasattr(self, "identify_dock"):
            self.identify_dock.show()
            self.identify_dock.raise_()
        if hasattr(self, "geo_status"):
            self.geo_status.showMessage("Identify Tool: Click on any feature or raster pixel to inspect attributes", 4000)

    def set_select_tool(self):
        self.set_select_mode("single")

    def set_select_mode(self, mode: str):
        from tools.interactive_tools import GeoSelectTool
        tool = GeoSelectTool(self.map_canvas.canvas, self, mode=mode)
        self.map_canvas.canvas.setMapTool(tool)
        self.geo_status.showMessage(
            f"Selection mode: {mode.capitalize()} (Click or drag on vector layer)", 3000
        )

    def clear_selection(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "removeSelection"):
            layer.removeSelection()
            self.map_canvas.refresh_canvas()
        if hasattr(self, "attr_table_dock") and self.attr_table_dock:
            self.attr_table_dock.table.clearSelection()
        if hasattr(self, "geo_status"):
            self.geo_status.set_selection_count(0)
            self.geo_status.showMessage("Selection cleared", 2000)

    def select_all_features(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "selectAll"):
            layer.selectAll()
            self.map_canvas.refresh_canvas()
            if hasattr(self, "geo_status"):
                self.geo_status.set_selection_count(layer.selectedFeatureCount())

    def invert_selection(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "invertSelection"):
            layer.invertSelection()
            self.map_canvas.refresh_canvas()
            if hasattr(self, "geo_status"):
                self.geo_status.set_selection_count(layer.selectedFeatureCount())

    def zoom_to_selection(self):
        layer = self.layer_panel.get_active_layer()
        if layer and hasattr(layer, "selectedFeatureCount") and layer.selectedFeatureCount() > 0:
            box = layer.boundingBoxOfSelected()
            if not box.isEmpty() and self.map_canvas and self.map_canvas.canvas:
                box.scale(1.2)
                self.map_canvas.canvas.setExtent(box)
                self.map_canvas.canvas.refresh()

    def set_measure_distance(self):
        from tools.interactive_tools import GeoMeasureTool
        tool = GeoMeasureTool(self.map_canvas.canvas, self, measure_type="distance")
        self.map_canvas.canvas.setMapTool(tool)
        self.geo_status.showMessage(
            "Measure Distance: Click points on map. Right-click to finish.", 4000
        )

    def set_measure_area(self):
        from tools.interactive_tools import GeoMeasureTool
        tool = GeoMeasureTool(self.map_canvas.canvas, self, measure_type="area")
        self.map_canvas.canvas.setMapTool(tool)
        self.geo_status.showMessage(
            "Measure Area: Click 3+ polygon vertices. Right-click to finish.", 4000
        )

    def set_measure_angle(self):
        from tools.interactive_tools import GeoMeasureTool
        tool = GeoMeasureTool(self.map_canvas.canvas, self, measure_type="angle")
        self.map_canvas.canvas.setMapTool(tool)
        self.geo_status.showMessage(
            "Measure Bearing / Angle: Click 2 points for bearing, 3 points for angle.", 4000
        )

    def set_coord_capture(self):
        from tools.interactive_tools import GeoCoordCaptureTool
        tool = GeoCoordCaptureTool(self.map_canvas.canvas, self)
        self.map_canvas.canvas.setMapTool(tool)
        self.geo_status.showMessage(
            "Coordinate Capture: Click on map to capture coordinates & DEM elevation.", 4000
        )
