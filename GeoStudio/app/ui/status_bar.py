# -*- coding: utf-8 -*-
"""GeoStudio - Status Bar with coordinates, elevation, CRS, scale, and progress."""

from PyQt5.QtWidgets import (
    QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class GeoStatusBar(QStatusBar):
    """
    Custom workstation status bar showing:
    - Current map coordinates (mouse position)
    - Real-time elevation value at cursor (Z/Elevation)
    - Map scale
    - Project CRS
    - Active layer name
    - Progress indicator
    """

    def __init__(self, map_canvas, parent=None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.setStyleSheet("""
            QStatusBar {
                background: #ffffff;
                color: #475569;
                border-top: 1px solid #e2e8f0;
                padding: 2px 6px;
            }
            QLabel {
                color: #334155;
                font-size: 11px;
                padding: 2px 8px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
            }
            QProgressBar {
                max-width: 140px;
                max-height: 14px;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                background: #f1f5f9;
                text-align: center;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background: #0f172a;
                border-radius: 2px;
            }
        """)
        self._build_widgets()
        self._connect_canvas()

    def _build_widgets(self):
        self.setSizeGripEnabled(False)

        # Coordinate display
        self.coord_label = QLabel("🌐 X: ─────  Y: ─────")
        self.coord_label.setMinimumWidth(240)

        # Elevation display (Real-time cursor elevation)
        self.elev_label = QLabel("🏔 Elev: ─────")
        self.elev_label.setMinimumWidth(120)
        self.elev_label.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 2px 8px; color: #94a3b8;")

        # Scale
        self.scale_label = QLabel("📐 Scale: 1:──────")
        self.scale_label.setMinimumWidth(130)

        # CRS
        self.crs_label = QLabel("🌐 CRS: ──────")
        self.crs_label.setMinimumWidth(130)

        # Active layer
        self.layer_label = QLabel("🗂 Layer: None")
        self.layer_label.setMinimumWidth(160)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        # Status message
        self.msg_label = QLabel("● Ready")
        self.msg_label.setStyleSheet("background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 4px; padding: 2px 10px; color: #16a34a; font-weight: 600;")

        self.addWidget(self.coord_label)
        self.addWidget(self.elev_label)
        self.addWidget(self.scale_label)
        self.addWidget(self.crs_label)
        self.addWidget(self.layer_label)
        self.addWidget(self.progress)
        self.addPermanentWidget(self.msg_label)

    def _connect_canvas(self):
        if self.map_canvas and self.map_canvas.canvas:
            self.map_canvas.coordinate_changed.connect(self._update_coords)
            if hasattr(self.map_canvas, 'elevation_changed'):
                self.map_canvas.elevation_changed.connect(self._update_elevation)
            self.map_canvas.canvas.scaleChanged.connect(self._update_scale)
            self.map_canvas.canvas.destinationCrsChanged.connect(self._update_crs)
            try:
                from qgis.core import QgsProject
                QgsProject.instance().crsChanged.connect(self._update_crs)
            except Exception:
                pass
            self._update_scale(self.map_canvas.get_scale())
            self._update_crs()

    def _update_coords(self, x, y):
        self.coord_label.setText(f"X: {x:>12.4f}  Y: {y:>12.4f}")

    def _update_elevation(self, elev_val):
        if elev_val is not None:
            self.elev_label.setText(f"🏔 {elev_val:,.1f} m")
            self.elev_label.setStyleSheet("color: #b45309; font-weight: bold;")
        else:
            self.elev_label.setText("Elev: ─────")
            self.elev_label.setStyleSheet("color: #94a3b8;")

    def _update_scale(self, scale=None):
        if scale is None:
            scale = self.map_canvas.get_scale()
        self.scale_label.setText(f"Scale: 1:{int(scale):,}")

    def _update_crs(self):
        crs = self.map_canvas.get_crs()
        self.crs_label.setText(f"CRS: {crs}")

    def set_layer(self, name: str):
        self.layer_label.setText(f"Layer: {name}")

    def set_message(self, msg: str, timeout_ms: int = 4000):
        self.msg_label.setText(msg)
        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, lambda: self.msg_label.setText("Ready"))

    def showMessage(self, msg: str, timeout: int = 0):
        self.set_message(msg, timeout)

    def set_progress(self, value: int):
        self.progress.setVisible(value > 0 and value < 100)
        self.progress.setValue(value)
