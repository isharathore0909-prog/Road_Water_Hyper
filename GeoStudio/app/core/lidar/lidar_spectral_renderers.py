# -*- coding: utf-8 -*-
"""
GeoStudio - LiDAR Spectral & QA Symbology Renderers
Vegetation indices (NDVI/NDWI), CIR infrared, density, and QA/QC quality flag renderers.
"""

from PyQt5.QtGui import QColor
from qgis.core import (
    QgsPointCloudAttributeByRampRenderer,
    QgsPointCloudClassifiedRenderer,
    QgsPointCloudCategory,
    QgsPointCloudRgbRenderer,
    QgsUnitTypes
)

from .lidar_attributes import (
    is_point_cloud, get_attribute_names, find_attr, get_attribute_range, create_shader
)


def apply_cir(layer, point_size: float = 3.5, apply_rgb_fallback=None) -> bool:
    """Color Infrared (CIR: NIR -> Red, Red -> Green, Green -> Blue)."""
    if not is_point_cloud(layer):
        return False
    attrs = [a.lower() for a in get_attribute_names(layer)]
    if not ("nir" in attrs or "infrared" in attrs):
        if apply_rgb_fallback:
            return apply_rgb_fallback(layer, point_size=point_size)
        return False
    try:
        renderer = QgsPointCloudRgbRenderer()
        nir_name = find_attr(layer, ["Nir", "NIR", "Infrared", "infrared", "near_infrared"])
        r_name = find_attr(layer, ["Red", "red", "R"])
        g_name = find_attr(layer, ["Green", "green", "G"])

        renderer.setRedAttribute(nir_name)
        renderer.setGreenAttribute(r_name)
        renderer.setBlueAttribute(g_name)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying CIR renderer: {e}")
        return False


def apply_ndvi(layer, point_size: float = 3.5) -> bool:
    """Render point cloud colored by Normalized Difference Vegetation Index (NDVI)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["NDVI", "ndvi", "VegetationIndex", "vegetation_index", "Intensity"])
        s_min, s_max = get_attribute_range(layer, attr, -0.2, 0.8)
        shader = create_shader(s_min, s_max, ramp_name="RdYlGn", num_stops=16)

        renderer = QgsPointCloudAttributeByRampRenderer()
        renderer.setAttribute(attr)
        renderer.setColorRampShader(shader)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying NDVI: {e}")
        return False


def apply_ndwi(layer, point_size: float = 3.5) -> bool:
    """Render point cloud colored by Normalized Difference Water Index (NDWI)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["NDWI", "ndwi", "WaterIndex", "Intensity"])
        s_min, s_max = get_attribute_range(layer, attr, -0.5, 0.5)
        shader = create_shader(s_min, s_max, ramp_name="Blues", num_stops=16)

        renderer = QgsPointCloudAttributeByRampRenderer()
        renderer.setAttribute(attr)
        renderer.setColorRampShader(shader)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying NDWI: {e}")
        return False


def apply_point_density(layer, point_size: float = 3.5) -> bool:
    """Render point cloud colored by local point density (pts/m2)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["PointDensity", "point_density", "Density", "density", "Intensity"])
        s_min, s_max = get_attribute_range(layer, attr, 1.0, 50.0)
        shader = create_shader(s_min, s_max, ramp_name="Plasma", num_stops=16)

        renderer = QgsPointCloudAttributeByRampRenderer()
        renderer.setAttribute(attr)
        renderer.setColorRampShader(shader)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying point density: {e}")
        return False


def apply_withheld_flag(layer, point_size: float = 3.5) -> bool:
    """Highlight withheld points (QA/QC noise flagging)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["Withheld", "withheld", "Classification"])
        categories = [
            QgsPointCloudCategory(0, QColor("#10b981"), "Valid (Not Withheld)"),
            QgsPointCloudCategory(1, QColor("#ef4444"), "Withheld / Outlier Flagged"),
        ]
        renderer = QgsPointCloudClassifiedRenderer(attr, categories)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying withheld flag: {e}")
        return False


def apply_keypoint_flag(layer, point_size: float = 3.5) -> bool:
    """Highlight model keypoints (decimated DTM surface anchors)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["KeyPoint", "keypoint", "Keypoint", "Classification"])
        categories = [
            QgsPointCloudCategory(0, QColor("#94a3b8"), "Standard Point"),
            QgsPointCloudCategory(1, QColor("#f59e0b"), "Keypoint (Model Anchor)"),
        ]
        renderer = QgsPointCloudClassifiedRenderer(attr, categories)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying keypoint flag: {e}")
        return False


def apply_overlap_flag(layer, point_size: float = 3.5) -> bool:
    """Highlight flight strip overlap points."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["Overlap", "overlap", "OverlapFlag", "Classification"])
        categories = [
            QgsPointCloudCategory(0, QColor("#3b82f6"), "Single Flight Swath"),
            QgsPointCloudCategory(1, QColor("#a855f7"), "Overlap Zone Point"),
        ]
        renderer = QgsPointCloudClassifiedRenderer(attr, categories)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying overlap flag: {e}")
        return False


def apply_return_height_delta(layer, point_size: float = 3.5) -> bool:
    """Render point cloud colored by first vs last return height difference (canopy penetration)."""
    if not is_point_cloud(layer):
        return False
    try:
        attr = find_attr(layer, ["ReturnHeightDelta", "return_height_delta", "DeltaZ", "NumberOfReturns", "ReturnNumber", "Z"])
        s_min, s_max = get_attribute_range(layer, attr, 0.0, 25.0)
        shader = create_shader(s_min, s_max, ramp_name="YlGnBu", num_stops=16)

        renderer = QgsPointCloudAttributeByRampRenderer()
        renderer.setAttribute(attr)
        renderer.setColorRampShader(shader)
        renderer.setPointSize(point_size)
        renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
        renderer.setMaximumScreenError(0.3)
        renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return True
    except Exception as e:
        print(f"[LidarStyler] Error applying return height delta: {e}")
        return False
