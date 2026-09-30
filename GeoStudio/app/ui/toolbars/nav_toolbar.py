# -*- coding: utf-8 -*-
"""
GeoStudio - Navigation Toolbar (Grouped with Title)
"""

from PyQt5.QtWidgets import QToolBar, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton
from PyQt5.QtCore import Qt, QSize

from resources.icons.icon_provider import get_icon


class NavToolBar(QToolBar):
    """Map navigation toolbar with group label."""

    def __init__(self, main_window, parent=None):
        super().__init__("Navigation", parent or main_window)
        self.setObjectName("tb_nav")
        self.mw = main_window
        self._build_ui()

    def _build_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 1)
        layout.setSpacing(1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(2)

        items = [
            ("pan", "Pan Map", self.mw.set_pan_tool, "Pan Map (P)", "P"),
            ("zoom_in", "Zoom In", self.mw.set_zoom_in, "Zoom In (+)", "+"),
            ("zoom_out", "Zoom Out", self.mw.set_zoom_out, "Zoom Out (-)", "-"),
            ("zoom_full", "Zoom Full", self.mw.zoom_full, "Zoom to Full Extent (Ctrl+Shift+F)", "Ctrl+Shift+F"),
            ("zoom_last", "Zoom Last", self.mw.zoom_last, "Zoom Last (Ctrl+[)", "Ctrl+["),
            ("zoom_next", "Zoom Next", self.mw.zoom_next, "Zoom Next (Ctrl+])", "Ctrl+]"),
            ("refresh", "Refresh", self.mw.refresh_canvas, "Refresh Map Canvas (F5)", "F5"),
        ]
        for icon_key, text, slot, tip, shortcut in items:
            btn = QToolButton(container)
            btn.setIcon(get_icon(icon_key))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(tip)
            btn.setStatusTip(tip)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)

        lbl = QLabel("NAVIGATION", container)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #64748b; font-size: 9px; font-weight: 700; letter-spacing: 0.5px; padding-top: 1px;")
        layout.addWidget(lbl)

        self.addWidget(container)
