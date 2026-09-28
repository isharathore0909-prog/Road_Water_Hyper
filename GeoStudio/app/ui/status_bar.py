# -*- coding: utf-8 -*-
"""GeoStudio - Status Bar with coordinates, CRS, scale, and progress."""

from PyQt5.QtWidgets import (
    QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class GeoStatusBar(QStatusBar):
    """
    Custom status bar showing:
    - Current map coordinates (mouse position)
    - Map scale
    - Project CRS
    - Active layer name
    - Progress indicator
    """

    def __init__(self, map_canvas, parent=None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.setStyleSheet("""
            QStatusBar { background: #0d1b2a; color: #78909c; border-top: 1px solid #37474f; }
            QLabel { color: #90a4ae; font-size: 11px; padding: 0 8px; }
            QProgressBar { max-width: 120px; max-height: 12px; border: 1px solid #37474f;
                           border-radius: 3px; background: #1e272c; }
            QProgressBar::chunk { background: #1565c0; border-radius: 2px; }
        """)
        self._build_widgets()
        self._connect_canvas()

    def _build_widgets(self):
        self.setSizeGripEnabled(False)

        # Coordinate display
        self.coord_label = QLabel("X: ─────  Y: ─────")
        self.coord_label.setMinimumWidth(260)

        # Scale
        self.scale_label = QLabel("Scale: 1:──────")
        self.scale_label.setMinimumWidth(130)

        # CRS
        self.crs_label = QLabel("CRS: ──────")
        self.crs_label.setMinimumWidth(130)

        # Active layer
        self.layer_label = QLabel("Layer: None")
        self.layer_label.setMinimumWidth(160)

        # Separator
        def sep():
            s = QLabel("│")
            s.setStyleSheet("color: #37474f;")
            return s

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        # Status message
        self.msg_label = QLabel("Ready")
        self.msg_label.setStyleSheet("color: #a5d6a7;")

        self.addWidget(self.coord_label)
        self.addWidget(sep())
        self.addWidget(self.scale_label)
        self.addWidget(sep())
        self.addWidget(self.crs_label)
        self.addWidget(sep())
        self.addWidget(self.layer_label)
        self.addWidget(sep())
        self.addWidget(self.progress)
        self.addPermanentWidget(self.msg_label)

    def _connect_canvas(self):
        if self.map_canvas and self.map_canvas.canvas:
            self.map_canvas.coordinate_changed.connect(self._update_coords)
            self.map_canvas.canvas.scaleChanged.connect(self._update_scale)
            self.map_canvas.canvas.destinationCrsChanged.connect(self._update_crs)
            self._update_scale(self.map_canvas.get_scale())
            self._update_crs()

    def _update_coords(self, x, y):
        self.coord_label.setText(f"X: {x:>14.4f}   Y: {y:>14.4f}")

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

    def set_progress(self, value: int):
        self.progress.setVisible(value > 0 and value < 100)
        self.progress.setValue(value)
