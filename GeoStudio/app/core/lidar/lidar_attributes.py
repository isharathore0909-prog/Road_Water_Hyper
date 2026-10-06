# -*- coding: utf-8 -*-
"""
GeoStudio - LiDAR Attribute & Shader Utilities
Attribute extraction, statistical range discovery, color ramp shader generation, and point size adjustment.
"""

import math
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsMapLayer, QgsPointCloudLayer, QgsColorRampShader, QgsStyle
)


def is_point_cloud(layer) -> bool:
    """Check if layer is a valid QgsPointCloudLayer."""
    if not layer or not layer.isValid():
        return False
    return hasattr(QgsMapLayer, "PointCloudLayer") and layer.type() == QgsMapLayer.PointCloudLayer


def get_attribute_names(layer) -> list:
    """Extract available attribute names from point cloud layer."""
    if not is_point_cloud(layer):
        return []
    try:
        if hasattr(layer, "attributes"):
            attrs = layer.attributes()
            if hasattr(attrs, "count") and hasattr(attrs, "at"):
                return [attrs.at(i).name() for i in range(attrs.count())]
            elif hasattr(attrs, "attributes"):
                return [a.name() for a in attrs.attributes()]
            elif hasattr(attrs, "__iter__"):
                return [a.name() if hasattr(a, "name") else str(a) for a in attrs]
        dp = layer.dataProvider()
        if dp and hasattr(dp, "attributes"):
            attrs = dp.attributes()
            if hasattr(attrs, "count") and hasattr(attrs, "at"):
                return [attrs.at(i).name() for i in range(attrs.count())]
            elif hasattr(attrs, "__iter__"):
                return [a.name() if hasattr(a, "name") else str(a) for a in attrs]
    except Exception:
        pass
    return []


def find_attr(layer, candidates: list) -> str:
    """Finds the actual attribute name matching any of the candidates (case-insensitive)."""
    attrs = get_attribute_names(layer)
    for c in candidates:
        for a in attrs:
            if a.lower() == c.lower():
                return a
    return candidates[0]


def get_attribute_range(layer, attr_name: str, default_min: float = 0.0, default_max: float = 100.0):
    """Retrieves statistical min/max for an attribute with safe fallbacks."""
    try:
        stats = layer.statistics()
        if stats:
            if hasattr(stats, "minimum") and hasattr(stats, "maximum"):
                mn = stats.minimum(attr_name)
                mx = stats.maximum(attr_name)
                if mn is not None and mx is not None and mn < mx and not math.isnan(mn) and not math.isnan(mx):
                    return float(mn), float(mx)
            elif isinstance(stats, dict) and attr_name in stats:
                z_stat = stats[attr_name]
                mn = getattr(z_stat, "minimum", None)
                mx = getattr(z_stat, "maximum", None)
                if mn is not None and mx is not None and mn < mx:
                    return float(mn), float(mx)
    except Exception:
        pass

    if attr_name.upper() == "Z":
        try:
            elev_props = layer.elevationProperties()
            if elev_props:
                mn = getattr(elev_props, "zMinimum", None) or getattr(elev_props, "lowerElevationLimit", None)
                mx = getattr(elev_props, "zMaximum", None) or getattr(elev_props, "upperElevationLimit", None)
                if mn is not None and mx is not None and mn < mx:
                    return float(mn), float(mx)
        except Exception:
            pass

    return default_min, default_max


def create_shader(min_v: float, max_v: float, ramp_name: str = "Turbo", num_stops: int = 16):
    """Creates a QgsColorRampShader with explicit ColorRampItem stops."""
    if min_v is None or max_v is None or min_v >= max_v:
        min_v, max_v = 0.0, 100.0

    style = QgsStyle.defaultStyle()
    ramp = style.colorRamp(ramp_name)
    if not ramp and ramp_name != "Turbo":
        ramp = style.colorRamp("Turbo")
    if not ramp:
        ramp = style.colorRamp("Spectral") or style.colorRamp("Viridis")

    shader = QgsColorRampShader(float(min_v), float(max_v))
    shader.setColorRampType(QgsColorRampShader.Interpolated)

    items = []
    if ramp:
        shader.setSourceColorRamp(ramp)
        for i in range(num_stops):
            frac = i / (num_stops - 1)
            val = min_v + frac * (max_v - min_v)
            col = ramp.color(frac)
            items.append(QgsColorRampShader.ColorRampItem(val, col, f"{val:.1f}"))
    else:
        turbo_cols = [
            (0.00, "#30123b"), (0.15, "#4662d8"), (0.30, "#28bbec"),
            (0.45, "#40e0d0"), (0.60, "#a2fc3c"), (0.75, "#febc2b"),
            (0.90, "#f86214"), (1.00, "#7a0403")
        ]
        for frac, hex_col in turbo_cols:
            val = min_v + frac * (max_v - min_v)
            items.append(QgsColorRampShader.ColorRampItem(val, QColor(hex_col), f"{val:.1f}"))

    shader.setColorRampItemList(items)
    return shader


def set_point_size(layer, delta: float) -> float:
    """Increase or decrease point size on current renderer."""
    if not is_point_cloud(layer):
        return 0.0
    try:
        renderer = layer.renderer()
        if renderer and hasattr(renderer, "pointSize") and hasattr(renderer, "setPointSize"):
            current = renderer.pointSize()
            new_size = max(0.5, min(20.0, current + delta))
            renderer.setPointSize(new_size)
            layer.triggerRepaint()
            return new_size
    except Exception:
        pass
    return 0.0
