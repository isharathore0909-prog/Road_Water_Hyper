# -*- coding: utf-8 -*-
"""
GeoStudio - LiDAR & Point Cloud Styler
Provides high-performance 2D & 3D styling and coloring for QgsPointCloudLayer (.las, .laz, .copc.laz, .e57).
"""

import os
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsPointCloudLayer,
    QgsPointCloudAttributeByRampRenderer,
    QgsPointCloudClassifiedRenderer,
    QgsPointCloudCategory,
    QgsPointCloudRgbRenderer,
    QgsPointCloudExtentRenderer,
    QgsColorRampShader,
    QgsStyle,
    QgsUnitTypes,
    QgsColorRamp
)
from PyQt5.QtGui import QColor


class LidarStyler:
    """Provides automated rendering, color ramps, and symbology for Point Cloud layers."""

    @staticmethod
    def is_point_cloud(layer) -> bool:
        """Check if layer is a QgsPointCloudLayer."""
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
    def auto_style(layer, point_size: float = 3.0) -> bool:
        """
        Automatically select the best renderer for the point cloud:
        1. RGB True Color (drone photogrammetry) if Red, Green, Blue attributes are present.
        2. Elevation Color Ramp (Viridis) for elevation / topographic data.
        """
        if not LidarStyler.is_point_cloud(layer):
            return False

        attrs = [a.lower() for a in LidarStyler.get_attribute_names(layer)]

        # If dataset contains actual RGB channels (e.g. drone photogrammetry LAS)
        if attrs and "red" in attrs and "green" in attrs and "blue" in attrs:
            applied = LidarStyler.apply_rgb(layer, point_size=point_size)
            if applied:
                return True

        # Topographic elevation ramp (Turbo / Viridis)
        return LidarStyler.apply_elevation_ramp(layer, ramp_name="Turbo", point_size=point_size)

    @staticmethod
    def apply_elevation_ramp(layer, ramp_name: str = "Viridis", point_size: float = 3.0, min_val: float = None, max_val: float = None) -> bool:
        """
        Render 2D point cloud colored by elevation (Z attribute) using a color ramp.
        """
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            # Estimate or retrieve Z min and max
            z_min = min_val
            z_max = max_val

            if z_min is None or z_max is None:
                try:
                    stats = layer.statistics()
                    if stats:
                        if hasattr(stats, "minimum") and hasattr(stats, "maximum"):
                            z_min = stats.minimum("Z")
                            z_max = stats.maximum("Z")
                        elif isinstance(stats, dict) and "Z" in stats:
                            z_stat = stats["Z"]
                            z_min = getattr(z_stat, "minimum", 0.0)
                            z_max = getattr(z_stat, "maximum", 100.0)
                except Exception:
                    pass

            if z_min is None or z_max is None or z_min == z_max or (isinstance(z_min, float) and z_min != z_min):
                try:
                    elev_props = layer.elevationProperties()
                    if elev_props:
                        z_min = getattr(elev_props, "zMinimum", None) or getattr(elev_props, "lowerElevationLimit", None) or 0.0
                        z_max = getattr(elev_props, "zMaximum", None) or getattr(elev_props, "upperElevationLimit", None) or 100.0
                except Exception:
                    pass
                if z_min is None or z_max is None or z_min == z_max:
                    z_min = 0.0
                    z_max = 100.0

            # Create Color Ramp Shader
            style = QgsStyle.defaultStyle()
            ramp = style.colorRamp(ramp_name)
            if not ramp:
                ramp = style.colorRamp("Turbo") or style.colorRamp("Spectral")

            shader = QgsColorRampShader(float(z_min), float(z_max), ramp)
            shader.setColorRampType(QgsColorRampShader.Interpolated)

            renderer = QgsPointCloudAttributeByRampRenderer()
            renderer.setAttribute("Z")
            renderer.setColorRampShader(shader)
            try:
                renderer.setPointSymbol(QgsPointCloudAttributeByRampRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.5)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying elevation ramp: {e}")
            return False

    @staticmethod
    def apply_intensity_ramp(layer, point_size: float = 3.0) -> bool:
        """Render point cloud colored by laser return intensity (Grayscale / High Contrast)."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            style = QgsStyle.defaultStyle()
            ramp = style.colorRamp("Greys") or style.colorRamp("Magma")

            shader = QgsColorRampShader(0.0, 65535.0, ramp)
            shader.setColorRampType(QgsColorRampShader.Interpolated)

            renderer = QgsPointCloudAttributeByRampRenderer()
            renderer.setAttribute("Intensity")
            renderer.setColorRampShader(shader)
            try:
                renderer.setPointSymbol(QgsPointCloudAttributeByRampRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.5)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying intensity ramp: {e}")
            return False

    @staticmethod
    def apply_rgb(layer, point_size: float = 3.0) -> bool:
        """Render point cloud using embedded True Color RGB channels (photogrammetry / drone LAS)."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            from qgis.core import QgsContrastEnhancement, Qgis
            renderer = layer.renderer()
            if not isinstance(renderer, QgsPointCloudRgbRenderer):
                renderer = QgsPointCloudRgbRenderer()

            attr_names = LidarStyler.get_attribute_names(layer)
            r_name = next((a for a in attr_names if a.lower() == "red"), "Red")
            g_name = next((a for a in attr_names if a.lower() == "green"), "Green")
            b_name = next((a for a in attr_names if a.lower() == "blue"), "Blue")

            renderer.setRedAttribute(r_name)
            renderer.setGreenAttribute(g_name)
            renderer.setBlueAttribute(b_name)
            try:
                renderer.setPointSymbol(QgsPointCloudRgbRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.5)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            # Ensure valid 16-bit contrast enhancements for RGB color channels
            if not renderer.redContrastEnhancement():
                ce_r = QgsContrastEnhancement(Qgis.DataType.UInt16)
                ce_r.setMinimumValue(0.0)
                ce_r.setMaximumValue(65535.0)
                renderer.setRedContrastEnhancement(ce_r)
            if not renderer.greenContrastEnhancement():
                ce_g = QgsContrastEnhancement(Qgis.DataType.UInt16)
                ce_g.setMinimumValue(0.0)
                ce_g.setMaximumValue(65535.0)
                renderer.setGreenContrastEnhancement(ce_g)
            if not renderer.blueContrastEnhancement():
                ce_b = QgsContrastEnhancement(Qgis.DataType.UInt16)
                ce_b.setMinimumValue(0.0)
                ce_b.setMaximumValue(65535.0)
                renderer.setBlueContrastEnhancement(ce_b)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying RGB renderer: {e}")
            return False

    @staticmethod
    def apply_classification(layer, point_size: float = 3.0) -> bool:
        """Render point cloud using ASPRS LAS standard classification color palette."""
        if not LidarStyler.is_point_cloud(layer):
            return False

        try:
            categories = [
                QgsPointCloudCategory(0, QColor("#94a3b8"), "0: Never Classified"),
                QgsPointCloudCategory(1, QColor("#cbd5e1"), "1: Unassigned"),
                QgsPointCloudCategory(2, QColor("#92400e"), "2: Ground (Bare Earth)"),
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

            renderer = QgsPointCloudClassifiedRenderer("Classification", categories)
            try:
                renderer.setPointSymbol(QgsPointCloudClassifiedRenderer.PointSymbol.Circle)
            except Exception:
                pass
            renderer.setPointSize(point_size)
            renderer.setPointSizeUnit(QgsUnitTypes.RenderPixels)
            renderer.setMaximumScreenError(0.5)
            renderer.setMaximumScreenErrorUnit(QgsUnitTypes.RenderPixels)

            layer.setRenderer(renderer)
            layer.triggerRepaint()
            return True
        except Exception as e:
            print(f"[LidarStyler] Error applying classification renderer: {e}")
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
