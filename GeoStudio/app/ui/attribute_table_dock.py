# -*- coding: utf-8 -*-
"""
GeoStudio - Professional GIS Attribute Table Dock
Features:
- Sortable columns, search filter
- Bi-directional selection sync between Attribute Table and Map Canvas
- Zoom to selected feature(s)
- Clear selection
- Copy selection & Export to CSV
- Clean feature count and selected count metrics
"""

import csv
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QLineEdit, QHeaderView, QToolButton, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

from resources.icons.icon_provider import get_icon


class AttributeTableDock(QDockWidget):
    """Bottom dock showing the attribute table of the active vector layer."""

    def __init__(self, parent=None):
        super().__init__("Attribute Table", parent)
        self.setObjectName("attr_table_dock")
        self.mw = parent
        self.setMinimumHeight(220)
        self.setMaximumHeight(450)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        self._current_layer = None
        self._row_fids = []          # Maps row index to QgsFeatureId
        self._fid_to_row = {}        # Maps QgsFeatureId to row index
        self._is_syncing_selection = False

        self._build_ui()

    def _build_ui(self):
        widget = QWidget(self)
        widget.setStyleSheet("""
            QWidget {
                background: #ffffff;
                color: #0f172a;
                font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif;
            }
            QTableWidget {
                background: #ffffff;
                color: #0f172a;
                gridline-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                font-size: 11px;
                border-radius: 4px;
                outline: none;
            }
            QTableWidget::item { padding: 4px 6px; }
            QTableWidget::item:selected { background: #e2e8f0; color: #0f172a; font-weight: 600; }
            QHeaderView::section {
                background: #f8fafc;
                color: #475569;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                border-right: 1px solid #f1f5f9;
                padding: 5px 8px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton, QToolButton {
                background: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover, QToolButton:hover {
                background: #f1f5f9;
                color: #0f172a;
                border-color: #94a3b8;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #e2e8f0;
            }
            QLineEdit {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1.5px solid #0f172a; }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Toolbar row
        toolbar = QHBoxLayout()
        self.layer_label = QLabel("No vector layer selected")
        self.layer_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.layer_label.setStyleSheet("color: #0f172a; padding: 2px 4px;")
        toolbar.addWidget(self.layer_label)

        toolbar.addSpacing(8)

        # Zoom to selected
        self.btn_zoom = QToolButton()
        self.btn_zoom.setText("Zoom to Selected")
        self.btn_zoom.setIcon(get_icon("zoom_in"))
        self.btn_zoom.setToolTip("Zoom canvas to selected feature(s)")
        self.btn_zoom.clicked.connect(self._zoom_to_selected)
        toolbar.addWidget(self.btn_zoom)

        # Clear selection
        self.btn_clear_sel = QToolButton()
        self.btn_clear_sel.setText("Clear Selection")
        self.btn_clear_sel.setIcon(get_icon("delete"))
        self.btn_clear_sel.setToolTip("Deselect all features")
        self.btn_clear_sel.clicked.connect(self._clear_selection)
        toolbar.addWidget(self.btn_clear_sel)

        toolbar.addStretch()

        # Search filter
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter rows...")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setMaximumWidth(220)
        self.filter_edit.textChanged.connect(self._filter_rows)
        toolbar.addWidget(self.filter_edit)

        # Refresh
        btn_refresh = QToolButton()
        btn_refresh.setText("Refresh")
        btn_refresh.setIcon(get_icon("refresh"))
        btn_refresh.clicked.connect(self._refresh_table)
        toolbar.addWidget(btn_refresh)

        # Export CSV
        btn_export = QToolButton()
        btn_export.setText("Export CSV")
        btn_export.setIcon(get_icon("save_project"))
        btn_export.clicked.connect(self._export_csv)
        toolbar.addWidget(btn_export)

        # Copy Table
        btn_copy = QToolButton()
        btn_copy.setText("Copy")
        btn_copy.clicked.connect(self._copy_selection)
        toolbar.addWidget(btn_copy)

        # Metrics label
        self.metrics_label = QLabel("0 features | 0 selected")
        self.metrics_label.setStyleSheet("""
            background: #f8fafc;
            color: #334155;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            padding: 3px 8px;
            border: 1px solid #cbd5e1;
        """)
        toolbar.addWidget(self.metrics_label)

        layout.addLayout(toolbar)

        # Table Widget
        self.table = QTableWidget(widget)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet("alternate-background-color: #f8fafc;")

        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)

        widget.setLayout(layout)
        self.setWidget(widget)

    def load_active_layer(self, layer=None):
        if self._current_layer and hasattr(self._current_layer, "selectionChanged"):
            try:
                self._current_layer.selectionChanged.disconnect(self._on_layer_selection_changed)
            except Exception:
                pass

        self._current_layer = layer
        if self._current_layer and hasattr(self._current_layer, "selectionChanged"):
            try:
                self._current_layer.selectionChanged.connect(self._on_layer_selection_changed)
            except Exception:
                pass

        self._refresh_table()

    def _refresh_table(self):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self._row_fids = []
        self._fid_to_row = {}

        layer = self._current_layer
        if not layer:
            self.layer_label.setText("No vector layer selected")
            self.metrics_label.setText("0 features | 0 selected")
            self.table.blockSignals(False)
            return

        try:
            from qgis.core import QgsMapLayer
            if layer.type() != QgsMapLayer.VectorLayer:
                self.layer_label.setText(f"'{layer.name()}' is a raster layer")
                self.metrics_label.setText("N/A")
                self.table.blockSignals(False)
                return

            self.layer_label.setText(layer.name())
            fields = layer.fields()
            field_names = [f.name() for f in fields]
            features = list(layer.getFeatures())

            self.table.setColumnCount(len(field_names))
            self.table.setHorizontalHeaderLabels(field_names)
            self.table.setRowCount(len(features))

            selected_ids = set(layer.selectedFeatureIds()) if hasattr(layer, "selectedFeatureIds") else set()

            for row, feat in enumerate(features):
                fid = feat.id()
                self._row_fids.append(fid)
                self._fid_to_row[fid] = row

                for col, fname in enumerate(field_names):
                    val = feat[fname]
                    text_val = str(val) if val is not None else ""
                    item = QTableWidgetItem(text_val)
                    item.setData(Qt.UserRole, fid)
                    self.table.setItem(row, col, item)

                if fid in selected_ids:
                    self.table.selectRow(row)

            self.table.resizeColumnsToContents()
            self._update_metrics()
        except Exception as e:
            self.layer_label.setText(f"Error loading attributes: {e}")
        finally:
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)

    def _update_metrics(self):
        total = self.table.rowCount()
        selected_rows = len(set(i.row() for i in self.table.selectedItems()))
        self.metrics_label.setText(f"{total:,} features | {selected_rows:,} selected")

    def _on_table_selection_changed(self):
        if self._is_syncing_selection or not self._current_layer:
            self._update_metrics()
            return

        self._is_syncing_selection = True
        try:
            selected_rows = sorted(set(i.row() for i in self.table.selectedItems()))
            fids = []
            for r in selected_rows:
                if 0 <= r < len(self._row_fids):
                    fids.append(self._row_fids[r])

            if hasattr(self._current_layer, "selectByIds"):
                self._current_layer.selectByIds(fids)
                if self.mw and hasattr(self.mw, "map_canvas") and self.mw.map_canvas:
                    self.mw.map_canvas.refresh_canvas()
            self._update_metrics()
        finally:
            self._is_syncing_selection = False

    def _on_layer_selection_changed(self, selected, deselected, clearAndSelect):
        if self._is_syncing_selection or not self._current_layer:
            return

        self._is_syncing_selection = True
        try:
            self.table.blockSignals(True)
            selected_ids = set(self._current_layer.selectedFeatureIds())

            self.table.clearSelection()
            for fid in selected_ids:
                row = self._fid_to_row.get(fid)
                if row is not None:
                    self.table.selectRow(row)

            self._update_metrics()
        finally:
            self.table.blockSignals(False)
            self._is_syncing_selection = False

    def _on_item_double_clicked(self, item):
        self._zoom_to_selected()

    def _zoom_to_selected(self):
        if not self._current_layer or not self.mw:
            return

        selected_rows = sorted(set(i.row() for i in self.table.selectedItems()))
        if not selected_rows:
            return

        from qgis.core import QgsRectangle
        box = QgsRectangle()
        box.setMinimal()

        for r in selected_rows:
            if 0 <= r < len(self._row_fids):
                fid = self._row_fids[r]
                feat = self._current_layer.getFeature(fid)
                if feat and feat.hasGeometry():
                    box.combineExtentWith(feat.geometry().boundingBox())

        if not box.isEmpty() and hasattr(self.mw, "map_canvas") and self.mw.map_canvas.canvas:
            box.scale(1.2)
            self.mw.map_canvas.canvas.setExtent(box)
            self.mw.map_canvas.canvas.refresh()

    def _clear_selection(self):
        if self._current_layer and hasattr(self._current_layer, "removeSelection"):
            self._current_layer.removeSelection()
            if self.mw and hasattr(self.mw, "map_canvas") and self.mw.map_canvas:
                self.mw.map_canvas.refresh_canvas()
        self.table.clearSelection()
        self._update_metrics()

    def _filter_rows(self, text):
        query = text.strip().lower()
        for row in range(self.table.rowCount()):
            if not query:
                self.table.setRowHidden(row, False)
                continue
            row_visible = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    row_visible = True
                    break
            self.table.setRowHidden(row, not row_visible)

    def _copy_selection(self):
        selected_items = self.table.selectedItems()
        rows = sorted(set(i.row() for i in selected_items)) if selected_items else list(range(self.table.rowCount()))
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
        if self.mw and hasattr(self.mw, "geo_status"):
            self.mw.geo_status.showMessage(f"Copied {len(rows)} rows to clipboard", 2000)

    def _export_csv(self):
        if not self._current_layer:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Attribute Table", f"{self._current_layer.name()}_attributes.csv", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, c).text() if self.table.item(row, c) else "" for c in range(self.table.columnCount())]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Complete", f"Successfully exported attribute table to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export CSV: {e}")
