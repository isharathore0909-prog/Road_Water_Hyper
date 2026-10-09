# -*- coding: utf-8 -*-
"""
GeoStudio - Professional GIS Layer Properties Dialog
Organized into 7 structured tabs:
1. General
2. Source
3. Symbology
4. Labels
5. Fields
6. Display / Rendering
7. Metadata
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QSlider, QCheckBox, QPushButton, QColorDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from resources.icons.icon_provider import get_icon


class LayerPropertiesDialog(QDialog):
    """
    Standard tabbed desktop GIS Layer Properties Dialog.
    Allows configuring metadata, CRS, symbology, labels, display opacity, and field schemas.
    """

    def __init__(self, layer, map_canvas=None, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.map_canvas = map_canvas

        layer_name = layer.name() if layer else "Layer"
        self.setWindowTitle(f"Layer Properties — {layer_name}")
        self.setMinimumSize(680, 520)
        self.resize(760, 580)
        self.setWindowModality(Qt.ApplicationModal)

        self._fill_color = QColor("#3b82f6")
        self._stroke_color = QColor("#1d4ed8")

        self._init_ui()
        self._load_layer_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                background: #ffffff;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                padding: 6px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0f172a;
                font-weight: 600;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: #e2e8f0;
            }
        """)

        # Add 7 Tabs
        self.tab_general = QWidget()
        self.tab_source = QWidget()
        self.tab_symbology = QWidget()
        self.tab_labels = QWidget()
        self.tab_fields = QWidget()
        self.tab_display = QWidget()
        self.tab_metadata = QWidget()

        self.tabs.addTab(self.tab_general, "General")
        self.tabs.addTab(self.tab_source, "Source")
        self.tabs.addTab(self.tab_symbology, "Symbology")
        self.tabs.addTab(self.tab_labels, "Labels")
        self.tabs.addTab(self.tab_fields, "Fields")
        self.tabs.addTab(self.tab_display, "Display")
        self.tabs.addTab(self.tab_metadata, "Metadata")

        self._build_general_tab()
        self._build_source_tab()
        self._build_symbology_tab()
        self._build_labels_tab()
        self._build_fields_tab()
        self._build_display_tab()
        self._build_metadata_tab()

        layout.addWidget(self.tabs, 1)

        # Dialog Buttons (OK, Cancel, Apply)
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_apply = QPushButton("Apply")
        btn_apply.setStyleSheet("QPushButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 14px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: #e2e8f0; }")
        btn_apply.clicked.connect(self._apply_changes)
        btn_box.addWidget(btn_apply)

        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("QPushButton { background: #0f172a; color: #ffffff; border: 1px solid #0f172a; border-radius: 4px; padding: 6px 16px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: #334155; }")
        btn_ok.clicked.connect(self._on_ok)
        btn_box.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("QPushButton { background: #ffffff; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 14px; font-size: 11px; } QPushButton:hover { background: #f1f5f9; }")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        layout.addLayout(btn_box)

    # ── 1. General Tab ──────────────────────────────────────
    def _build_general_tab(self):
        form = QFormLayout(self.tab_general)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.txt_layer_name = QLineEdit()
        self.txt_layer_name.setStyleSheet("QLineEdit { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 5px; }")
        form.addRow("Layer Name:", self.txt_layer_name)

        self.lbl_type = QLabel("Vector")
        form.addRow("Type:", self.lbl_type)

        self.lbl_crs = QLabel("EPSG:4326")
        form.addRow("Coordinate Reference System:", self.lbl_crs)

        self.lbl_feature_count = QLabel("0")
        form.addRow("Features / Count:", self.lbl_feature_count)

        self.chk_scale_vis = QCheckBox("Enable scale dependent visibility")
        form.addRow("", self.chk_scale_vis)

        scale_row = QHBoxLayout()
        self.spin_min_scale = QDoubleSpinBox()
        self.spin_min_scale.setRange(0, 100000000)
        self.spin_min_scale.setPrefix("1 : ")
        self.spin_max_scale = QDoubleSpinBox()
        self.spin_max_scale.setRange(0, 100000000)
        self.spin_max_scale.setPrefix("1 : ")
        scale_row.addWidget(QLabel("Min Scale:"))
        scale_row.addWidget(self.spin_min_scale)
        scale_row.addWidget(QLabel("Max Scale:"))
        scale_row.addWidget(self.spin_max_scale)
        form.addRow("Scale Range:", scale_row)

    # ── 2. Source Tab ───────────────────────────────────────
    def _build_source_tab(self):
        form = QFormLayout(self.tab_source)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.lbl_provider = QLabel("ogr")
        form.addRow("Data Provider:", self.lbl_provider)

        self.txt_source_path = QTextEdit()
        self.txt_source_path.setReadOnly(True)
        self.txt_source_path.setMaximumHeight(60)
        self.txt_source_path.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; font-family: monospace; font-size: 11px;")
        form.addRow("Data Source:", self.txt_source_path)

        self.lbl_extent = QLabel("[0, 0, 0, 0]")
        self.lbl_extent.setStyleSheet("font-family: monospace; font-size: 11px;")
        form.addRow("Spatial Extent:", self.lbl_extent)

        self.lbl_encoding = QLabel("UTF-8")
        form.addRow("Data Encoding:", self.lbl_encoding)

    # ── 3. Symbology Tab ────────────────────────────────────
    def _build_symbology_tab(self):
        layout = QVBoxLayout(self.tab_symbology)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        # Vector Symbology Controls
        self.color_btn = QPushButton("Select Color")
        self.color_btn.setFixedHeight(26)
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("Fill Color:", self.color_btn)

        self.stroke_btn = QPushButton("Select Outline Color")
        self.stroke_btn.setFixedHeight(26)
        self.stroke_btn.clicked.connect(self._pick_stroke)
        form.addRow("Stroke Color:", self.stroke_btn)

        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(0.1, 10.0)
        self.spin_width.setValue(1.0)
        self.spin_width.setSingleStep(0.2)
        form.addRow("Stroke Width (px):", self.spin_width)

        layout.addLayout(form)
        layout.addStretch()

    # ── 4. Labels Tab ───────────────────────────────────────
    def _build_labels_tab(self):
        form = QFormLayout(self.tab_labels)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self.chk_enable_labels = QCheckBox("Show labels for this layer")
        form.addRow("", self.chk_enable_labels)

        self.combo_label_field = QComboBox()
        self.combo_label_field.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px;")
        form.addRow("Label Field:", self.combo_label_field)

        self.spin_label_size = QSpinBox()
        self.spin_label_size.setRange(6, 48)
        self.spin_label_size.setValue(10)
        form.addRow("Font Size (pt):", self.spin_label_size)

        self.label_color_btn = QPushButton("Select Text Color")
        self.label_color_btn.clicked.connect(self._pick_label_color)
        self._label_color = QColor("#0f172a")
        form.addRow("Text Color:", self.label_color_btn)

    # ── 5. Fields Tab ───────────────────────────────────────
    def _build_fields_tab(self):
        layout = QVBoxLayout(self.tab_fields)
        layout.setContentsMargins(12, 12, 12, 12)

        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(4)
        self.fields_table.setHorizontalHeaderLabels(["#", "Field Name", "Type", "Length"])
        self.fields_table.horizontalHeader().setStretchLastSection(True)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.fields_table.setAlternatingRowColors(True)
        self.fields_table.setStyleSheet("""
            QTableWidget { background: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; font-size: 11px; }
            QHeaderView::section { background: #f8fafc; color: #475569; border: none; border-bottom: 1px solid #cbd5e1; padding: 4px; font-weight: 600; }
        """)
        layout.addWidget(self.fields_table)

    # ── 6. Display Tab ──────────────────────────────────────
    def _build_display_tab(self):
        form = QFormLayout(self.tab_display)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(14)

        opacity_row = QHBoxLayout()
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(100)
        self.lbl_opacity_val = QLabel("100 %")
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity_val.setText(f"{v} %"))
        opacity_row.addWidget(self.slider_opacity, 1)
        opacity_row.addWidget(self.lbl_opacity_val)
        form.addRow("Layer Opacity:", opacity_row)

        self.combo_blend = QComboBox()
        self.combo_blend.addItems(["Normal", "Multiply", "Screen", "Overlay", "Darken", "Lighten"])
        self.combo_blend.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px;")
        form.addRow("Blending Mode:", self.combo_blend)

    # ── 7. Metadata Tab ─────────────────────────────────────
    def _build_metadata_tab(self):
        layout = QVBoxLayout(self.tab_metadata)
        layout.setContentsMargins(12, 12, 12, 12)

        self.txt_metadata = QTextEdit()
        self.txt_metadata.setReadOnly(True)
        self.txt_metadata.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; font-family: monospace; font-size: 11px; padding: 8px;")
        layout.addWidget(self.txt_metadata)

    def _load_layer_data(self):
        if not self.layer:
            return

        self.txt_layer_name.setText(self.layer.name())
        crs = self.layer.crs()
        self.lbl_crs.setText(f"{crs.authid()} — {crs.description()}" if crs.isValid() else "Not set")

        from qgis.core import QgsVectorLayer, QgsRasterLayer
        is_vector = isinstance(self.layer, QgsVectorLayer)
        is_raster = isinstance(self.layer, QgsRasterLayer)

        self.lbl_type.setText("Vector Layer" if is_vector else "Raster Layer" if is_raster else "Point Cloud Layer")
        self.lbl_provider.setText(self.layer.dataProvider().name() if self.layer.dataProvider() else "Unknown")
        self.txt_source_path.setText(self.layer.source())

        ext = self.layer.extent()
        self.lbl_extent.setText(f"[{ext.xMinimum():.3f}, {ext.yMinimum():.3f}] - [{ext.xMaximum():.3f}, {ext.yMaximum():.3f}]")

        # Opacity
        opacity = int(self.layer.opacity() * 100)
        self.slider_opacity.setValue(opacity)
        self.lbl_opacity_val.setText(f"{opacity} %")

        if is_vector:
            self.lbl_feature_count.setText(f"{self.layer.featureCount():,} features")
            fields = self.layer.fields()
            self.combo_label_field.clear()
            self.fields_table.setRowCount(len(fields))

            for row, fld in enumerate(fields):
                self.combo_label_field.addItem(fld.name())
                self.fields_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.fields_table.setItem(row, 1, QTableWidgetItem(fld.name()))
                self.fields_table.setItem(row, 2, QTableWidgetItem(fld.typeName()))
                self.fields_table.setItem(row, 3, QTableWidgetItem(str(fld.length())))

            # Populate current color
            renderer = self.layer.renderer()
            if renderer and hasattr(renderer, "symbol"):
                sym = renderer.symbol()
                if sym:
                    self._fill_color = sym.color()
                    self._update_color_btn(self.color_btn, self._fill_color)

            # Metadata
            meta_text = f"Layer ID: {self.layer.id()}\n"
            meta_text += f"Geometry Type: {self.layer.geometryType()}\n"
            meta_text += f"Fields Count: {len(fields)}\n\n"
            meta_text += f"CRS WKT:\n{crs.toWkt()}"
            self.txt_metadata.setText(meta_text)

        elif is_raster:
            self.lbl_feature_count.setText(f"{self.layer.width()} x {self.layer.height()} pixels (Bands: {self.layer.bandCount()})")
            self.tabs.setTabEnabled(3, False)  # Disable Labels for raster
            self.tabs.setTabEnabled(4, False)  # Disable Fields for raster

            meta_text = f"Raster Dimensions: {self.layer.width()} x {self.layer.height()}\n"
            meta_text += f"Bands: {self.layer.bandCount()}\n\n"
            meta_text += f"CRS WKT:\n{crs.toWkt()}"
            self.txt_metadata.setText(meta_text)

    def _pick_color(self):
        col = QColorDialog.getColor(self._fill_color, self, "Select Fill Color")
        if col.isValid():
            self._fill_color = col
            self._update_color_btn(self.color_btn, col)

    def _pick_stroke(self):
        col = QColorDialog.getColor(self._stroke_color, self, "Select Stroke Color")
        if col.isValid():
            self._stroke_color = col
            self._update_color_btn(self.stroke_btn, col)

    def _pick_label_color(self):
        col = QColorDialog.getColor(self._label_color, self, "Select Label Color")
        if col.isValid():
            self._label_color = col
            self._update_color_btn(self.label_color_btn, col)

    def _update_color_btn(self, btn, color):
        btn.setStyleSheet(f"background-color: {color.name()}; color: {'#ffffff' if color.lightness() < 128 else '#000000'}; border: 1px solid #94a3b8; border-radius: 4px; font-weight: 600;")
        btn.setText(color.name())

    def _apply_changes(self):
        if not self.layer or not self.layer.isValid():
            return

        # Name
        new_name = self.txt_layer_name.text().strip()
        if new_name and new_name != self.layer.name():
            self.layer.setName(new_name)

        # Opacity
        new_opacity = self.slider_opacity.value() / 100.0
        self.layer.setOpacity(new_opacity)

        from qgis.core import QgsVectorLayer
        if isinstance(self.layer, QgsVectorLayer):
            # Apply fill & stroke color
            try:
                from qgis.core import QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsSingleSymbolRenderer
                sym_layer = QgsSimpleFillSymbolLayer(self._fill_color)
                sym_layer.setStrokeColor(self._stroke_color)
                sym_layer.setStrokeWidth(self.spin_width.value())
                sym = QgsFillSymbol()
                sym.changeSymbolLayer(0, sym_layer)
                self.layer.setRenderer(QgsSingleSymbolRenderer(sym))
            except Exception:
                pass

            # Apply labels
            if self.chk_enable_labels.isChecked() and self.combo_label_field.currentText():
                try:
                    from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
                    from PyQt5.QtGui import QFont
                    settings = QgsPalLayerSettings()
                    settings.fieldName = self.combo_label_field.currentText()
                    settings.enabled = True
                    text_format = settings.format()
                    text_format.setFont(QFont("Segoe UI", self.spin_label_size.value()))
                    text_format.setColor(self._label_color)
                    settings.setFormat(text_format)
                    self.layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
                    self.layer.setLabelsEnabled(True)
                except Exception:
                    pass
            else:
                self.layer.setLabelsEnabled(False)

        self.layer.triggerRepaint()
        if self.map_canvas:
            self.map_canvas.refresh_canvas()

    def _on_ok(self):
        self._apply_changes()
        self.accept()
