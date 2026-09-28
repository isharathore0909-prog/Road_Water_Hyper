# -*- coding: utf-8 -*-
"""
GeoAnalytica QGIS Plugin - Entry Point
QGIS calls classFactory() to load the plugin.
"""


def classFactory(iface):
    """
    QGIS entry point. Loads GeoAnalytica plugin.

    :param iface: QgisInterface - A QGIS interface instance (the main QGIS app).
    :returns: GeoAnalytica - Plugin main class instance.
    """
    from .geoanalytica import GeoAnalytica
    return GeoAnalytica(iface)
