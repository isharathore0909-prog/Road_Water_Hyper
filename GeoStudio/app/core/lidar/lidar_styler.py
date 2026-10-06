# -*- coding: utf-8 -*-
"""
GeoStudio - LiDAR & Point Cloud Styler
Provides high-performance 2D & 3D styling and coloring for QgsPointCloudLayer (.las, .laz, .copc.laz, .e57).
Guarantees explicit ColorRampItem list generation for all ramp-based shaders.
"""

from qgis.core import (
    QgsPointCloudAttributeByRampRenderer,
    QgsUnitTypes
)

from .lidar_attributes import (
    is_point_cloud, get_attribute_names, find_attr, get_attribute_range,
    create_shader, set_point_size
)
from .lidar_renderers import (
    apply_rgb, apply_classification, apply_return_number, apply_height_above_ground,
    apply_scan_angle, apply_point_source_id, apply_source_layer, apply_segment,
    apply_point_index, apply_cir, apply_ndvi, apply_ndwi, apply_point_density,
    apply_withheld_flag, apply_keypoint_flag, apply_overlap_flag, apply_return_height_delta
)


class LidarStyler:
    """Provides automated rendering, color ramps, and symbology for Point Cloud layers."""

    # Attribute and helper exports
    is_point_cloud = staticmethod(is_point_cloud)
    get_attribute_names = staticmethod(get_attribute_names)
    _find_attr = staticmethod(find_attr)
    _get_attribute_range = staticmethod(get_attribute_range)
    _create_shader = staticmethod(create_shader)
    set_point_size = staticmethod(set_point_size)

    # Renderer exports
    apply_rgb = staticmethod(apply_rgb)
    apply_classification = staticmethod(apply_classification)
    apply_return_number = staticmethod(apply_return_number)
    apply_height_above_ground = staticmethod(apply_height_above_ground)
    apply_scan_angle = staticmethod(apply_scan_angle)
    apply_point_source_id = staticmethod(apply_point_source_id)
    apply_source_layer = staticmethod(apply_source_layer)
    apply_segment = staticmethod(apply_segment)
    apply_point_index = staticmethod(apply_point_index)
    apply_cir = staticmethod(apply_cir)
    apply_ndvi = staticmethod(apply_ndvi)
    apply_ndwi = staticmethod(apply_ndwi)
    apply_point_density = staticmethod(apply_point_density)
    apply_withheld_flag = staticmethod(apply_withheld_flag)
    apply_keypoint_flag = staticmethod(apply_keypoint_flag)
    apply_overlap_flag = staticmethod(apply_overlap_flag)
    apply_return_height_delta = staticmethod(apply_return_height_delta)

    @staticmethod
    def auto_style(layer, point_size: float = 3.5) -> bool:
        """Automatically select the best renderer for the point cloud."""
        if not is_point_cloud(layer):
            return False

        attrs = [a.lower() for a in get_attribute_names(layer)]
        if attrs and "red" in attrs and "green" in attrs and "blue" in attrs:
            if apply_rgb(layer, point_size=point_size):
                return True

        return LidarStyler.apply_elevation_ramp(layer, ramp_name="Turbo", point_size=point_size)

    @staticmethod
    def apply_rgb_elev(layer, point_size: float = 3.5) -> bool:
        """Render point cloud with RGB true color if present, otherwise fall back to elevation ramp."""
        if not is_point_cloud(layer):
            return False
        attrs = [a.lower() for a in get_attribute_names(layer)]
        if "red" in attrs and "green" in attrs and "blue" in attrs:
            if apply_rgb(layer, point_size=point_size):
                return True
        return LidarStyler.apply_elevation_ramp(layer, ramp_name="Turbo", point_size=point_size)

    @staticmethod
    def apply_elevation_ramp(layer, ramp_name: str = "Turbo", point_size: float = 3.5) -> bool:
        """Render point cloud colored by elevation (Z attribute)."""
        if not is_point_cloud(layer):
            return False

        try:
            z_attr = find_attr(layer, ["Z", "Elevation", "Height"])
            z_min, z_max = get_attribute_range(layer, z_attr, 0.0, 100.0)

            shader = create_shader(z_min, z_max, ramp_name=ramp_name, num_stops=16)

            renderer = QgsPointCloudAttributeByRampRenderer()
            renderer.setAttribute(z_attr)
            renderer.setColorRampShader(shader)
            try:
                renderer.setPointSymbol(QgsPointCloudAttributeByRampRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.3)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying elevation ramp: {e}")
            return False

    @staticmethod
    def apply_intensity_ramp(layer, point_size: float = 3.5) -> bool:
        """Render point cloud colored by laser return intensity."""
        if not is_point_cloud(layer):
            return False

        try:
            int_attr = find_attr(layer, ["Intensity", "intensity", "reflectance"])
            i_min, i_max = get_attribute_range(layer, int_attr, 0.0, 255.0)
            if i_max <= 1.0:
                i_min, i_max = 0.0, 1.0
            elif i_max > 255.0 and i_max <= 4095.0:
                i_min, i_max = 0.0, 4095.0
            elif i_max > 4095.0:
                i_min, i_max = 0.0, 65535.0

            shader = create_shader(i_min, i_max, ramp_name="Magma", num_stops=16)

            renderer = QgsPointCloudAttributeByRampRenderer()
            renderer.setAttribute(int_attr)
            renderer.setColorRampShader(shader)
            try:
                renderer.setPointSymbol(QgsPointCloudAttributeByRampRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.3)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying intensity ramp: {e}")
            return False
