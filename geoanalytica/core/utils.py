# -*- coding: utf-8 -*-
"""GeoAnalytica - Core utilities."""

import os


def resource_path(relative_path):
    """
    Get absolute path to a resource file relative to the plugin root.

    :param relative_path: Path relative to plugin directory (e.g. 'resources/icon.png').
    :returns: Absolute path string.
    """
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(plugin_dir, relative_path)


def layer_crs_to_wkt(layer):
    """Return WKT CRS string for a layer."""
    return layer.crs().toWkt()


def format_area(area_m2):
    """Format area in square meters to a human-readable string."""
    if area_m2 >= 1_000_000:
        return f"{area_m2 / 1_000_000:.4f} km²"
    elif area_m2 >= 10_000:
        return f"{area_m2 / 10_000:.4f} ha"
    else:
        return f"{area_m2:.4f} m²"


def format_distance(dist_m):
    """Format distance in meters to a human-readable string."""
    if dist_m >= 1000:
        return f"{dist_m / 1000:.3f} km"
    else:
        return f"{dist_m:.3f} m"


def get_vector_layers(iface):
    """Return list of all vector layers in the current project."""
    from qgis.core import QgsProject, QgsMapLayer
    return [
        layer for layer in QgsProject.instance().mapLayers().values()
        if layer.type() == QgsMapLayer.VectorLayer
    ]


def get_raster_layers(iface):
    """Return list of all raster layers in the current project."""
    from qgis.core import QgsProject, QgsMapLayer
    return [
        layer for layer in QgsProject.instance().mapLayers().values()
        if layer.type() == QgsMapLayer.RasterLayer
    ]


def log_message(message, level="INFO", tag="GeoAnalytica"):
    """Log a message to the QGIS message log."""
    from qgis.core import QgsMessageLog, Qgis
    level_map = {
        "INFO": Qgis.Info,
        "WARNING": Qgis.Warning,
        "CRITICAL": Qgis.Critical,
        "SUCCESS": Qgis.Success,
    }
    QgsMessageLog.logMessage(message, tag, level=level_map.get(level, Qgis.Info))
