# -*- coding: utf-8 -*-
"""
GeoAnalytica Processing Provider
Exposes GeoAnalytica algorithms to the QGIS Processing Toolbox.
"""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
import os


class GeoAnalyticaProvider(QgsProcessingProvider):
    """Processing provider that registers GeoAnalytica algorithms."""

    def __init__(self):
        super().__init__()

    def id(self):
        return "geoanalytica"

    def name(self):
        return "GeoAnalytica"

    def longName(self):
        return "GeoAnalytica Geospatial Analysis Suite"

    def icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return super().icon()

    def loadAlgorithms(self):
        """Register all GeoAnalytica processing algorithms."""
        # Add algorithms here as they are developed
        # Example:
        # from .algorithms.ndvi_algorithm import NDVIAlgorithm
        # self.addAlgorithm(NDVIAlgorithm())
        pass

    def supportedOutputRasterLayerExtensions(self):
        return ["tif", "tiff"]

    def supportedOutputVectorLayerExtensions(self):
        return ["gpkg", "shp", "geojson"]
