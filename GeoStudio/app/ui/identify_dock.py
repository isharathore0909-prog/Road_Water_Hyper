# -*- coding: utf-8 -*-
"""
GeoStudio - Identify Results Dock Widget
Presents identified map features in a clear, formatted key-value attribute inspector.
Supports zooming to feature, copying attributes, and highlighting on canvas.
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QToolButton,
    QApplication, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from resources.icons.icon_provider import get_icon


class IdentifyDock(QDockWidget):
    """
    Professional Identify Results inspector panel.
    Displays layer context, feature attributes, and geometry metrics.
    """

    zoom_to_feature_requested = pyqtSignal(object, object)  # (layer, feature)

    def __init__(self, main_window=None, parent=None):
        super().__init__("Identify Results", parent or main_window)
        self.setObjectName("identify_dock")
        self.mw = main_window
        self.setMinimumWidth(260)
        self.setMaximumWidth(450)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        self._current_layer = None
        self._current_feature = None

        self._build_ui()

    def _build_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header card
        self.header_card = QFrame(container)
        self.header_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        h_layout = QVBoxLayout(self.header_card)
        h_layout.setContentsMargins(4, 4, 4, 4)
        h_layout.setSpacing(4)

        title_row = QHBoxLayout()
        self.layer_label = QLabel("No Feature Selected")
        self.layer_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.layer_label.setStyleSheet("color: #0f172a;")
        title_row.addWidget(self.layer_label, 1)

        self.btn_zoom = QToolButton()
        self.btn_zoom.setToolTip("Zoom to Feature")
        self.btn_zoom.setIcon(get_icon("zoom_in"))
        self.btn_zoom.setStyleSheet("QToolButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px; } QToolButton:hover { background: #e2e8f0; }")
        self.btn_zoom.clicked.connect(self._zoom_to_current)
        self.btn_zoom.setEnabled(False)
        title_row.addWidget(self.btn_zoom)

        self.btn_copy = QToolButton()
        self.btn_copy.setToolTip("Copy Attributes to Clipboard")
        self.btn_copy.setIcon(get_icon("save_project"))
        self.btn_copy.setStyleSheet("QToolButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px; } QToolButton:hover { background: #e2e8f0; }")
        self.btn_copy.clicked.connect(self._copy_attributes)
        self.btn_copy.setEnabled(False)
        title_row.addWidget(self.btn_copy)

        self.btn_clear = QToolButton()
        self.btn_clear.setToolTip("Clear Identify")
        self.btn_clear.setIcon(get_icon("delete"))
        self.btn_clear.setStyleSheet("QToolButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px; } QToolButton:hover { background: #e2e8f0; }")
        self.btn_clear.clicked.connect(self.clear_results)
        title_row.addWidget(self.btn_clear)

        h_layout.addLayout(title_row)

        self.meta_label = QLabel("Click a feature on the map to inspect.")
        self.meta_label.setStyleSheet("color: #64748b; font-size: 11px;")
        h_layout.addWidget(self.meta_label)

        layout.addWidget(self.header_card)

        # Attribute key-value table
        self.table = QTableWidget(container)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                gridline-color: #f1f5f9;
                font-size: 11px;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #475569;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                padding: 4px 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QTableWidget::item { padding: 4px 6px; }
            QTableWidget::item:selected { background: #e2e8f0; color: #0f172a; }
        """)
        layout.addWidget(self.table, 1)

        # Empty state display
        self.empty_label = QLabel("Click any vector or raster feature on the map canvas to view its attributes.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 24px;")
        layout.addWidget(self.empty_label)

        container.setLayout(layout)
        self.setWidget(container)
        self.clear_results()

    def show_feature(self, layer, feature):
        """Displays attributes and geometry information for an identified feature."""
        self._current_layer = layer
        self._current_feature = feature

        if not layer or not feature:
            self.clear_results()
            return

        self.empty_label.hide()
        self.table.show()

        layer_name = layer.name() if hasattr(layer, "name") else "Layer"
        fid = feature.id() if hasattr(feature, "id") else "-"
        self.layer_label.setText(f"{layer_name} (ID: {fid})")

        # Geometry metrics
        geom_info = ""
        if hasattr(feature, "geometry") and feature.geometry():
            geom = feature.geometry()
            geom_type = geom.type()
            from qgis.core import QgsWkbTypes
            if geom_type == QgsWkbTypes.PointGeometry:
                pt = geom.asPoint()
                geom_info = f"Point [{pt.x():.4f}, {pt.y():.4f}]"
            elif geom_type == QgsWkbTypes.LineGeometry:
                length = geom.length()
                if length >= 1000:
                    geom_info = f"Line | Length: {length/1000:.2f} km"
                else:
                    geom_info = f"Line | Length: {length:.1f} m"
            elif geom_type == QgsWkbTypes.PolygonGeometry:
                area = geom.area()
                if area >= 1000000:
                    geom_info = f"Polygon | Area: {area/1000000:.2f} km²"
                elif area >= 10000:
                    geom_info = f"Polygon | Area: {area/10000:.2f} ha"
                else:
                    geom_info = f"Polygon | Area: {area:.1f} m²"

        self.meta_label.setText(geom_info if geom_info else f"Feature ID: {fid}")
        self.btn_zoom.setEnabled(True)
        self.btn_copy.setEnabled(True)

        # Populate attributes
        fields = layer.fields() if hasattr(layer, "fields") else []
        self.table.setRowCount(0)

        row = 0
        # First row: Feature ID
        self._add_row("Feature ID", str(fid))

        for fld in fields:
            fname = fld.name()
            val = feature[fname]
            str_val = "NULL" if val is None else str(val)
            # Format floating numbers cleanly
            if isinstance(val, float):
                str_val = f"{val:.4f}".rstrip("0").rstrip(".") if abs(val) < 10000 else f"{val:,.2f}"
            self._add_row(fname, str_val)

        self.show()
        self.raise_()

    def show_raster_value(self, layer, point, values: dict):
        """Displays raster band pixel values sampled at coordinates."""
        self._current_layer = layer
        self._current_feature = None

        self.empty_label.hide()
        self.table.show()

        layer_name = layer.name() if hasattr(layer, "name") else "Raster"
        self.layer_label.setText(f"{layer_name} [Raster]")
        self.meta_label.setText(f"Coordinates: X={point.x():.4f}, Y={point.y():.4f}")
        self.btn_zoom.setEnabled(False)
        self.btn_copy.setEnabled(True)

        self.table.setRowCount(0)
        for band_name, val in values.items():
            self._add_row(str(band_name), f"{val:.3f}" if isinstance(val, (int, float)) else str(val))

        self.show()
        self.raise_()

    def _add_row(self, key: str, value: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        k_item = QTableWidgetItem(key)
        k_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        k_item.setForeground(QColor("#334155"))

        v_item = QTableWidgetItem(value)
        v_item.setForeground(QColor("#0f172a"))

        self.table.setItem(row, 0, k_item)
        self.table.setItem(row, 1, v_item)

    def _zoom_to_current(self):
        if self._current_layer and self._current_feature and self.mw:
            if hasattr(self._current_feature, "geometry") and self._current_feature.geometry():
                rect = self._current_feature.geometry().boundingBox()
                rect.scale(1.2)
                if hasattr(self.mw, "map_canvas") and self.mw.map_canvas.canvas:
                    self.mw.map_canvas.canvas.setExtent(rect)
                    self.mw.map_canvas.canvas.refresh()

    def _copy_attributes(self):
        lines = []
        for r in range(self.table.rowCount()):
            k = self.table.item(r, 0).text()
            v = self.table.item(r, 1).text()
            lines.append(f"{k}: {v}")
        QApplication.clipboard().setText("\n".join(lines))
        if self.mw and hasattr(self.mw, "geo_status"):
            self.mw.geo_status.showMessage("Attributes copied to clipboard", 2000)

    def clear_results(self):
        self._current_layer = None
        self._current_feature = None
        self.layer_label.setText("No Feature Selected")
        self.meta_label.setText("Click a feature on the map to inspect.")
        self.btn_zoom.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.table.setRowCount(0)
        self.table.hide()
        self.empty_label.show()
