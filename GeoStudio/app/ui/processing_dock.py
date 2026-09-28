# -*- coding: utf-8 -*-
"""GeoStudio - Processing/Analysis Dock (right panel)."""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTabWidget, QLabel
)
from PyQt5.QtCore import Qt

# Use absolute imports (app/ is on sys.path via main.py)
from modules.spatial_analysis import SpatialAnalysisWidget
from modules.raster_processing import RasterProcessingWidget
from modules.satellite_module import SatelliteHyperspectralWidget
from modules.import_export import ImportExportWidget
from modules.map_tools import MapToolsWidget


class ProcessingDock(QDockWidget):
    """Right-side dockable processing & analysis panel with tabs."""

    TAB_MAP = {
        "spatial":   0,
        "raster":    1,
        "satellite": 2,
        "io":        3,
        "tools":     4,
    }

    def __init__(self, map_canvas, parent=None):
        super().__init__("🔬 Processing & Analysis", parent)
        self.setObjectName("processing_dock")
        self.setMinimumWidth(300)
        self.setMaximumWidth(480)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.map_canvas = map_canvas
        self._build_ui()

    def _build_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #1e272c; }
            QTabBar::tab { background: #1a2332; color: #78909c; padding: 6px 10px; font-size: 11px; }
            QTabBar::tab:selected { background: #0d47a1; color: #e3f2fd; font-weight: bold; }
            QTabBar::tab:hover { background: #263238; color: #cfd8dc; }
        """)

        # Build a fake iface wrapper for the modules
        class FakeIface:
            def __init__(self, canvas_widget):
                self._canvas = canvas_widget
            def mapCanvas(self): return self._canvas.canvas
            def messageBar(self):
                class FakeBar:
                    def pushMessage(self, *a, **kw): pass
                    def pushSuccess(self, tag, msg): print(f"[OK] {tag}: {msg}")
                    def pushWarning(self, tag, msg): print(f"[WARN] {tag}: {msg}")
                    def pushInfo(self, tag, msg):    print(f"[INFO] {tag}: {msg}")
                return FakeBar()
            def activeLayer(self): return None
            def setActiveLayer(self, l): pass

        self.iface = FakeIface(self.map_canvas)

        self.spatial_widget   = SpatialAnalysisWidget(self.iface)
        self.raster_widget    = RasterProcessingWidget(self.iface)
        self.satellite_widget = SatelliteHyperspectralWidget(self.iface)
        self.io_widget        = ImportExportWidget(self.iface)
        self.tools_widget     = MapToolsWidget(self.iface)

        self.tabs.addTab(self.spatial_widget,   "📐 Spatial")
        self.tabs.addTab(self.raster_widget,    "🏔 Raster")
        self.tabs.addTab(self.satellite_widget, "🛰 Satellite")
        self.tabs.addTab(self.io_widget,        "📦 I/O")
        self.tabs.addTab(self.tools_widget,     "🗺 Tools")

        layout.addWidget(self.tabs)
        widget.setLayout(layout)
        self.setWidget(widget)

    def open_tab(self, tab_name: str):
        idx = self.TAB_MAP.get(tab_name, 0)
        self.tabs.setCurrentIndex(idx)
