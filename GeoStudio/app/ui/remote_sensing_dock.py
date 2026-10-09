# -*- coding: utf-8 -*-
"""
GeoStudio - Remote Sensing & Hyperspectral Analytics Dock
Professional dockable panel providing ENVI-style remote sensing tools:
- Spectral Indices (NDVI, EVI, SAVI, NDWI, NDBI, NBR, NDSI)
- Custom Raster Band Math (Raster Calculator)
- False Color RGB Composites & Band Combinations
- Hyperspectral Band Inspection, All-Band Statistics & PCA
"""

from PyQt5.QtWidgets import QDockWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from modules.satellite_module import SatelliteHyperspectralWidget


class RemoteSensingDock(QDockWidget):
    """
    Professional Remote Sensing & Hyperspectral Dock Widget.
    Provides deep imagery analytics for multispectral & hyperspectral datasets.
    """

    def __init__(self, main_window=None, parent=None):
        super().__init__("Remote Sensing", parent or main_window)
        self.setObjectName("remote_sensing_dock")
        self.mw = main_window
        self.setMinimumWidth(280)
        self.setMaximumWidth(450)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.widget = SatelliteHyperspectralWidget(iface=main_window, parent=self)
        self.setWidget(self.widget)

    def refresh_layers(self):
        """Forces an update of all raster combo boxes."""
        if hasattr(self.widget, "_refresh_layers"):
            self.widget._refresh_layers()
