# -*- coding: utf-8 -*-
"""
GeoStudio - LiDAR & Point Cloud Styler
Provides high-performance 2D & 3D styling and coloring for QgsPointCloudLayer (.las, .laz, .copc.laz, .e57).
Guarantees explicit ColorRampItem list generation for all ramp-based shaders.
"""

import math
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsPointCloudLayer,
    QgsPointCloudAttributeByRampRenderer,
    QgsPointCloudClassifiedRenderer,
    QgsPointCloudCategory,
    QgsPointCloudRgbRenderer,
    QgsColorRampShader,
    QgsStyle,
    QgsUnitTypes
)


class LidarStyler:
    """Provides automated rendering, color ramps, and symbology for Point Cloud layers."""

    @staticmethod
    def is_point_cloud(layer) -> bool:
        """Check if layer is a valid QgsPointCloudLayer."""
        if not layer or not layer.isValid():
            return False
        return hasattr(QgsMapLayer, "PointCloudLayer") and layer.type() == QgsMapLayer.PointCloudLayer

    @staticmethod
    def get_attribute_names(layer) -> list:
        """Extract available attribute names from point cloud layer."""
        if not LidarStyler.is_point_cloud(layer):
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

    @staticmethod
    def _find_attr(layer, candidates: list) -> str:
        """Finds the actual attribute name matching any of the candidates (case-insensitive)."""
        attrs = LidarStyler.get_attribute_names(layer)
        for c in candidates:
            for a in attrs:
                if a.lower() == c.lower():
                    return a
        return candidates[0]

    @staticmethod
    def _get_attribute_range(layer, attr_name: str, default_min: float = 0.0, default_max: float = 100.0):
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

    @staticmethod
    def _create_shader(min_v: float, max_v: float, ramp_name: str = "Turbo", num_stops: int = 16):
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
            # High-visibility Turbo spectrum fallback
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

    @staticmethod
    def auto_style(layer, point_size: float = 3.5) -> bool:
        """Automatically select the best renderer for the point cloud."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        attrs = [a.lower() for a in LidarStyler.get_attribute_names(layer)]
        if attrs and "red" in attrs and "green" in attrs and "blue" in attrs:
            if LidarStyler.apply_rgb(layer, point_size=point_size):
                return True

        return LidarStyler.apply_elevation_ramp(layer, ramp_name="Turbo", point_size=point_size)

    @staticmethod
    def apply_elevation_ramp(layer, ramp_name: str = "Turbo", point_size: float = 3.5) -> bool:
        """Render point cloud colored by elevation (Z attribute)."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            z_attr = LidarStyler._find_attr(layer, ["Z", "Elevation", "Height"])
            z_min, z_max = LidarStyler._get_attribute_range(layer, z_attr, 0.0, 100.0)

            shader = LidarStyler._create_shader(z_min, z_max, ramp_name=ramp_name, num_stops=16)

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
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            int_attr = LidarStyler._find_attr(layer, ["Intensity", "intensity", "reflectance"])
            i_min, i_max = LidarStyler._get_attribute_range(layer, int_attr, 0.0, 255.0)
            if i_max <= 1.0:
                i_min, i_max = 0.0, 1.0
            elif i_max > 255.0 and i_max <= 4095.0:
                i_min, i_max = 0.0, 4095.0
            elif i_max > 4095.0:
                i_min, i_max = 0.0, 65535.0

            shader = LidarStyler._create_shader(i_min, i_max, ramp_name="Magma", num_stops=16)

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

    @staticmethod
    def apply_rgb(layer, point_size: float = 3.5) -> bool:
        """Render point cloud using embedded True Color RGB channels with auto contrast scaling."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        attrs = [a.lower() for a in LidarStyler.get_attribute_names(layer)]
        if not ("red" in attrs and "green" in attrs and "blue" in attrs):
            return False

        try:
            from qgis.core import QgsContrastEnhancement, Qgis
            renderer = QgsPointCloudRgbRenderer()

            r_name = LidarStyler._find_attr(layer, ["Red", "red", "R"])
            g_name = LidarStyler._find_attr(layer, ["Green", "green", "G"])
            b_name = LidarStyler._find_attr(layer, ["Blue", "blue", "B"])

            renderer.setRedAttribute(r_name)
            renderer.setGreenAttribute(g_name)
            renderer.setBlueAttribute(b_name)
            try:
                renderer.setPointSymbol(QgsPointCloudRgbRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.3)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            # Determine whether color values are 8-bit (0-255) or 16-bit (0-65535)
            r_min, r_max = LidarStyler._get_attribute_range(layer, r_name, 0.0, 65535.0)
            g_min, g_max = LidarStyler._get_attribute_range(layer, g_name, 0.0, 65535.0)
            b_min, b_max = LidarStyler._get_attribute_range(layer, b_name, 0.0, 65535.0)

            max_channel_val = max(r_max, g_max, b_max)
            target_max = 65535.0 if max_channel_val > 255.0 or max_channel_val == 0.0 else 255.0

            ce_r = QgsContrastEnhancement(Qgis.DataType.UInt16)
            ce_r.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
            ce_r.setMinimumValue(0.0)
            ce_r.setMaximumValue(target_max)
            renderer.setRedContrastEnhancement(ce_r)

            ce_g = QgsContrastEnhancement(Qgis.DataType.UInt16)
            ce_g.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
            ce_g.setMinimumValue(0.0)
            ce_g.setMaximumValue(target_max)
            renderer.setGreenContrastEnhancement(ce_g)

            ce_b = QgsContrastEnhancement(Qgis.DataType.UInt16)
            ce_b.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
            ce_b.setMinimumValue(0.0)
            ce_b.setMaximumValue(target_max)
            renderer.setBlueContrastEnhancement(ce_b)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying RGB renderer: {e}")
            return False

    @staticmethod
    def apply_classification(layer, point_size: float = 3.5) -> bool:
        """Render point cloud using ASPRS LAS standard classification color palette."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            class_attr = LidarStyler._find_attr(layer, ["Classification", "classification", "class"])
            categories = [
                QgsPointCloudCategory(0, QColor("#94a3b8"), "0: Never Classified"),
                QgsPointCloudCategory(1, QColor("#cbd5e1"), "1: Unassigned"),
                QgsPointCloudCategory(2, QColor("#d4a373"), "2: Ground (Light Brown / Tan)"),
                QgsPointCloudCategory(3, QColor("#86efac"), "3: Low Vegetation"),
                QgsPointCloudCategory(4, QColor("#22c55e"), "4: Medium Vegetation"),
                QgsPointCloudCategory(5, QColor("#15803d"), "5: High Vegetation / Canopy"),
                QgsPointCloudCategory(6, QColor("#ef4444"), "6: Building / Roof"),
                QgsPointCloudCategory(7, QColor("#64748b"), "7: Low Point / Noise"),
                QgsPointCloudCategory(8, QColor("#f59e0b"), "8: Reserved / Model Key-Point"),
                QgsPointCloudCategory(9, QColor("#0284c7"), "9: Water"),
                QgsPointCloudCategory(10, QColor("#ec4899"), "10: Rail"),
                QgsPointCloudCategory(11, QColor("#334155"), "11: Road Surface"),
            ]

            renderer = QgsPointCloudClassifiedRenderer(class_attr, categories)
            try:
                renderer.setPointSymbol(QgsPointCloudClassifiedRenderer.PointSymbol.Circle)
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
            print(f"[LidarStyler] Error applying classification renderer: {e}")
            return False

    @staticmethod
    def apply_return_number(layer, point_size: float = 3.5) -> bool:
        """Render point cloud colored by pulse return number (1st, 2nd, 3rd, last)."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            ret_attr = LidarStyler._find_attr(layer, ["ReturnNumber", "returnnumber", "return_number", "Return", "return"])

            # Use discrete classified categories for crisp return visualization
            categories = [
                QgsPointCloudCategory(1, QColor("#10b981"), "1: First Return (Canopy/Roof)"),
                QgsPointCloudCategory(2, QColor("#3b82f6"), "2: Intermediate Return"),
                QgsPointCloudCategory(3, QColor("#f59e0b"), "3: Intermediate Return"),
                QgsPointCloudCategory(4, QColor("#ef4444"), "4: Intermediate Return"),
                QgsPointCloudCategory(5, QColor("#8b5cf6"), "5+: Last Return (Ground)"),
            ]

            renderer = QgsPointCloudClassifiedRenderer(ret_attr, categories)
            try:
                renderer.setPointSymbol(QgsPointCloudClassifiedRenderer.PointSymbol.Circle)
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
            print(f"[LidarStyler] Error applying return number renderer: {e}")
            return False

    @staticmethod
    def apply_height_above_ground(layer, point_size: float = 3.5) -> bool:
        """Render point cloud colored by height above ground."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            hag_attr = LidarStyler._find_attr(layer, ["HeightAboveGround", "HAG", "hag", "NormalizedZ", "normalized_z", "Z"])
            h_min, h_max = LidarStyler._get_attribute_range(layer, hag_attr, 0.0, 35.0)
            if h_min < 0.0:
                h_min = 0.0
            if h_max <= h_min:
                h_max = h_min + 35.0

            shader = LidarStyler._create_shader(h_min, h_max, ramp_name="Viridis", num_stops=16)

            renderer = QgsPointCloudAttributeByRampRenderer()
            renderer.setAttribute(hag_attr)
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
            print(f"[LidarStyler] Error applying height above ground renderer: {e}")
            return False

    @staticmethod
    def set_point_size(layer, delta: float) -> float:
        """Increase or decrease point size on active point cloud layer."""
        if not LidarStyler.is_point_cloud(layer):
            return 3.0

        try:
            renderer = layer.renderer()
            if renderer and hasattr(renderer, "pointSize") and hasattr(renderer, "setPointSize"):
                cur_size = renderer.pointSize()
                new_size = max(1.0, min(20.0, cur_size + delta))
                renderer.setPointSize(new_size)
                layer.triggerRepaint()
                return new_size
        except Exception:
            pass
        return 3.0
