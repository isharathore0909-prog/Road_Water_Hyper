# -*- coding: utf-8 -*-
"""
GeoStudio - On-Canvas Elevation Color Legend & Scale Widget
Renders a vertical elevation scale bar with real-time Z-values in meters (like Global Mapper).
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QFont

from core.elevation_styler import ElevationStyler, ELEVATION_PRESETS


class ElevationLegendWidget(QWidget):
    """
    Floating on-canvas vertical elevation legend (like Global Mapper Pro).
    Displays the color ramp gradient with meter values (min to max).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFixedWidth(84)
        self.setMinimumHeight(240)
        self.setMaximumHeight(360)
        
        self.min_val = 0.0
        self.max_val = 100.0
        self.preset_key = "GLOBAL_MAPPER_ATLAS"
        self.unit_str = "m"
        self.is_active = False
        self.layer_name = ""

        # Move to top-left overlay position
        self.move(14, 14)
        self.hide()

    def update_from_layer(self, layer):
        """Updates the legend values and color ramp from the given raster layer."""
        if not layer or not layer.isValid():
            self.is_active = False
            self.hide()
            return

        if not ElevationStyler.is_dem_or_elevation(layer):
            self.is_active = False
            self.hide()
            return

        stats = ElevationStyler.get_valid_elevation_stats(layer, 1)
        if not stats:
            self.is_active = False
            self.hide()
            return

        self.min_val = stats["min"]
        self.max_val = stats["max"]
        self.layer_name = layer.name()
        self.is_active = True
        self.show()
        self.update()

    def set_range_and_preset(self, min_val: float, max_val: float, preset_key: str = "GLOBAL_MAPPER_ATLAS"):
        self.min_val = min_val
        self.max_val = max_val
        self.preset_key = preset_key
        self.is_active = True
        self.show()
        self.update()

    def paintEvent(self, event):
        if not self.is_active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background panel (semi-transparent off-white with crisp border)
        bg_rect = QRect(0, 0, w, h)
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), 6, 6)

        # Gradient bar dimensions
        bar_left = 12
        bar_top = 16
        bar_width = 16
        bar_height = h - 32
        bar_rect = QRect(bar_left, bar_top, bar_width, bar_height)

        # Build gradient from top (max_val) to bottom (min_val)
        preset = ELEVATION_PRESETS.get(self.preset_key, ELEVATION_PRESETS["GLOBAL_MAPPER_ATLAS"])
        stops = preset["stops"]

        gradient = QLinearGradient(bar_left, bar_top, bar_left, bar_top + bar_height)
        # Note: top of bar is max elevation (stop 1.0), bottom is min (stop 0.0)
        for stop_frac, hex_color, _ in stops:
            # Invert vertical position so max elevation is at the top
            gradient.setColorAt(1.0 - stop_frac, QColor(hex_color))

        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setBrush(QBrush(gradient))
        painter.drawRect(bar_rect)

        # Ticks and numeric text labels
        painter.setPen(QColor("#0f172a"))
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)

        num_ticks = 6
        val_range = self.max_val - self.min_val

        for i in range(num_ticks):
            frac = i / float(num_ticks - 1)  # 0.0 (top) to 1.0 (bottom)
            y_pos = int(bar_top + (frac * bar_height))
            val = self.max_val - (frac * val_range)

            # Draw tick line
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawLine(bar_left + bar_width, y_pos, bar_left + bar_width + 4, y_pos)

            # Draw text
            text_str = f"{val:.1f} m"
            painter.setPen(QColor("#1e293b"))
            painter.drawText(bar_left + bar_width + 6, y_pos + 4, text_str)

        painter.end()
