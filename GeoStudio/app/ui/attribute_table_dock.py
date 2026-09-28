# -*- coding: utf-8 -*-
"""GeoStudio - Attribute Table Dock (bottom panel)."""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QLineEdit, QComboBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class AttributeTableDock(QDockWidget):
    """Bottom dock showing the attribute table of the active vector layer."""

    def __init__(self, parent=None):
        super().__init__("📊 Attribute Table", parent)
        self.setObjectName("attr_table_dock")
        self.setMinimumHeight(200)
        self.setMaximumHeight(400)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._current_layer = None
        self._build_ui()

    def _build_ui(self):
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget { background: #1a2332; }
            QTableWidget { background: #1e272c; color: #cfd8dc; gridline-color: #37474f;
                           border: none; font-size: 11px; }
            QTableWidget::item { padding: 2px 6px; }
            QTableWidget::item:selected { background: #1565c0; color: white; }
            QHeaderView::section { background: #263238; color: #90caf9; border: 1px solid #37474f;
                                   padding: 4px; font-weight: bold; }
            QPushButton { background: #263238; color: #90caf9; border: 1px solid #37474f;
                          border-radius: 3px; padding: 4px 10px; font-size: 11px; }
            QPushButton:hover { background: #37474f; }
            QLineEdit { background: #263238; color: #cfd8dc; border: 1px solid #37474f;
                        border-radius: 3px; padding: 3px; font-size: 11px; }
            QLabel { color: #78909c; font-size: 11px; }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar row
        toolbar = QHBoxLayout()
        self.layer_label = QLabel("No layer selected")
        self.layer_label.setStyleSheet("color: #90caf9; font-weight: bold;")
        toolbar.addWidget(self.layer_label)
        toolbar.addStretch()

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("🔍 Filter rows...")
        self.filter_edit.setMaximumWidth(200)
        self.filter_edit.textChanged.connect(self._filter_rows)
        toolbar.addWidget(self.filter_edit)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self._refresh_table)
        toolbar.addWidget(btn_refresh)

        btn_export = QPushButton("📋 Copy")
        btn_export.clicked.connect(self._copy_selection)
        toolbar.addWidget(btn_export)

        self.feature_count_label = QLabel("0 features")
        toolbar.addWidget(self.feature_count_label)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setStyleSheet("alternate-background-color: #202b38;")
        layout.addWidget(self.table)

        widget.setLayout(layout)
        self.setWidget(widget)

    def load_active_layer(self, layer=None):
        self._current_layer = layer
        self._refresh_table()

    def _refresh_table(self):
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        layer = self._current_layer
        if not layer:
            self.layer_label.setText("No layer selected")
            return

        try:
            from qgis.core import QgsMapLayer
            if layer.type() != QgsMapLayer.VectorLayer:
                self.layer_label.setText(f"⚠ '{layer.name()}' is a raster layer")
                return

            self.layer_label.setText(f"🗂  {layer.name()}")
            fields = layer.fields()
            field_names = [f.name() for f in fields]
            features = list(layer.getFeatures())

            self.table.setColumnCount(len(field_names))
            self.table.setHorizontalHeaderLabels(field_names)
            self.table.setRowCount(len(features))
            self.feature_count_label.setText(f"{len(features):,} features")

            for row, feat in enumerate(features):
                for col, fname in enumerate(field_names):
                    val = feat[fname]
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    self.table.setItem(row, col, item)

            self.table.resizeColumnsToContents()
        except Exception as e:
            self.layer_label.setText(f"Error: {e}")

    def _filter_rows(self, text):
        for row in range(self.table.rowCount()):
            row_visible = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    row_visible = True
                    break
            self.table.setRowHidden(row, not row_visible)

    def _copy_selection(self):
        from PyQt5.QtWidgets import QApplication
        rows = sorted(set(i.row() for i in self.table.selectedItems()))
        cols = list(range(self.table.columnCount()))
        lines = []
        headers = [self.table.horizontalHeaderItem(c).text() for c in cols]
        lines.append("\t".join(headers))
        for row in rows:
            line = []
            for col in cols:
                item = self.table.item(row, col)
                line.append(item.text() if item else "")
            lines.append("\t".join(line))
        QApplication.clipboard().setText("\n".join(lines))
