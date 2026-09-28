# -*- coding: utf-8 -*-
"""
GeoAnalytica - Main Panel UI
A tabbed dockable panel housing all modules.
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QSizePolicy
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont

from ..modules.layer_manager import LayerManagerWidget
from ..modules.spatial_analysis import SpatialAnalysisWidget
from ..modules.raster_processing import RasterProcessingWidget
from ..modules.satellite_module import SatelliteHyperspectralWidget
from ..modules.import_export import ImportExportWidget
from ..modules.map_tools import MapToolsWidget


class GeoAnalyticaPanel(QWidget):
    """
    Main tabbed panel for GeoAnalytica.
    Each tab corresponds to a functional module.
    """

    TAB_NAMES = {
        "layer_manager": 0,
        "spatial_analysis": 1,
        "raster_processing": 2,
        "satellite": 3,
        "import_export": 4,
        "map_tools": 5,
    }

    def __init__(self, iface, plugin, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.plugin = plugin
        self._init_ui()

    def _init_ui(self):
        """Build the tabbed panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header label
        header = QLabel("🌍 GeoAnalytica")
        header.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a237e, stop:0.5 #283593, stop:1 #1565c0);
                padding: 8px 4px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet(self._tab_stylesheet())
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Instantiate and add each module tab
        self.layer_manager_widget = LayerManagerWidget(self.iface)
        self.spatial_analysis_widget = SpatialAnalysisWidget(self.iface)
        self.raster_processing_widget = RasterProcessingWidget(self.iface)
        self.satellite_widget = SatelliteHyperspectralWidget(self.iface)
        self.import_export_widget = ImportExportWidget(self.iface)
        self.map_tools_widget = MapToolsWidget(self.iface)

        self.tabs.addTab(self.layer_manager_widget,     "🗂 Layers")
        self.tabs.addTab(self.spatial_analysis_widget,  "📐 Analysis")
        self.tabs.addTab(self.raster_processing_widget, "🏔 Raster")
        self.tabs.addTab(self.satellite_widget,         "🛰 Satellite")
        self.tabs.addTab(self.import_export_widget,     "📦 IO")
        self.tabs.addTab(self.map_tools_widget,         "🗺 Tools")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.setMinimumWidth(340)

    def switch_to_tab(self, tab_name: str):
        """Programmatically switch the active tab by name."""
        idx = self.TAB_NAMES.get(tab_name, 0)
        self.tabs.setCurrentIndex(idx)

    @staticmethod
    def _tab_stylesheet():
        return """
            QTabWidget::pane {
                border: 1px solid #37474f;
                background: #263238;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1e272c;
                color: #b0bec5;
                border: 1px solid #37474f;
                padding: 6px 8px;
                min-width: 60px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #1565c0;
                color: #ffffff;
                font-weight: bold;
                border-color: #1976d2;
            }
            QTabBar::tab:hover:!selected {
                background: #2e3d45;
                color: #e0f2f1;
            }
        """
