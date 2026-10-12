# -*- coding: utf-8 -*-
"""
GeoStudio - Layout Item Properties Dock
Provides property inspectors for layout elements:
- Common geometry: X, Y, Width, Height, Rotation, Frame, Background, Opacity, Lock
- Specific tabs/editors for Map, Title/Label, Scale Bar, Legend, North Arrow/Picture, Shapes, Tables
"""

import os
import glob
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QLabel, QTextEdit, QColorDialog, QFontDialog,
    QScrollArea, QHBoxLayout, QSlider, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon

from qgis.core import (
    QgsApplication, QgsUnitTypes, QgsLayoutSize, QgsLayoutPoint,
    QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemScaleBar,
    QgsLayoutItemLegend, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutItemPolyline, QgsLayoutMeasurement, QgsProject
)


class LayoutPropertiesDock(QDockWidget):
    """Properties panel showing context-sensitive properties for selected layout items."""

    def __init__(self, layout_designer, parent=None):
        super().__init__("Item Properties", parent or layout_designer)
        self.designer = layout_designer
        self.setObjectName("layout_properties_dock")
        self.setMinimumWidth(280)
        self.setMaximumWidth(450)

        self._current_item = None
        self._build_ui()

    def _build_ui(self):
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self.container = QWidget()
        self.layout_v = QVBoxLayout(self.container)
        self.layout_v.setContentsMargins(6, 6, 6, 6)
        self.layout_v.setSpacing(6)

        # ── Item Header ──────────────────────────────────────────
        self.lbl_title = QLabel("No Item Selected")
        self.lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #0f172a; padding: 5px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;")
        self.layout_v.addWidget(self.lbl_title)

        # ── Common Position & Size Group ─────────────────────────
        self.grp_common = QGroupBox("Position and Size (mm)")
        form_pos = QFormLayout(self.grp_common)
        form_pos.setSpacing(5)

        self.spn_x = QDoubleSpinBox(); self.spn_x.setRange(-2000, 5000); self.spn_x.setDecimals(1)
        self.spn_y = QDoubleSpinBox(); self.spn_y.setRange(-2000, 5000); self.spn_y.setDecimals(1)
        self.spn_w = QDoubleSpinBox(); self.spn_w.setRange(0.5, 5000); self.spn_w.setDecimals(1)
        self.spn_h = QDoubleSpinBox(); self.spn_h.setRange(0.5, 5000); self.spn_h.setDecimals(1)
        self.spn_rot = QDoubleSpinBox(); self.spn_rot.setRange(-360, 360); self.spn_rot.setDecimals(1)

        self.spn_x.valueChanged.connect(self._on_pos_changed)
        self.spn_y.valueChanged.connect(self._on_pos_changed)
        self.spn_w.valueChanged.connect(self._on_size_changed)
        self.spn_h.valueChanged.connect(self._on_size_changed)
        self.spn_rot.valueChanged.connect(self._on_rot_changed)

        form_pos.addRow("X:", self.spn_x)
        form_pos.addRow("Y:", self.spn_y)
        form_pos.addRow("Width:", self.spn_w)
        form_pos.addRow("Height:", self.spn_h)
        form_pos.addRow("Rotation (°):", self.spn_rot)

        self.chk_lock = QCheckBox("Lock Position and Size")
        self.chk_lock.toggled.connect(self._on_lock_toggled)
        form_pos.addRow(self.chk_lock)

        self.layout_v.addWidget(self.grp_common)

        # ── Frame, Background & Opacity Group ────────────────────
        self.grp_frame = QGroupBox("Rendering & Appearance")
        form_frame = QFormLayout(self.grp_frame)
        form_frame.setSpacing(5)

        h_frame = QHBoxLayout()
        self.chk_has_frame = QCheckBox("Draw Frame")
        self.chk_has_frame.toggled.connect(self._on_frame_toggled)
        h_frame.addWidget(self.chk_has_frame)
        self.btn_frame_color = QPushButton("Color...")
        self.btn_frame_color.clicked.connect(self._pick_frame_color)
        h_frame.addWidget(self.btn_frame_color)
        form_frame.addRow(h_frame)

        h_bg = QHBoxLayout()
        self.chk_has_bg = QCheckBox("Background")
        self.chk_has_bg.toggled.connect(self._on_bg_toggled)
        h_bg.addWidget(self.chk_has_bg)
        self.btn_bg_color = QPushButton("Color...")
        self.btn_bg_color.clicked.connect(self._pick_bg_color)
        h_bg.addWidget(self.btn_bg_color)
        form_frame.addRow(h_bg)

        # Opacity Slider
        h_op = QHBoxLayout()
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(100)
        self.lbl_opacity = QLabel("100%")
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        h_op.addWidget(self.slider_opacity)
        h_op.addWidget(self.lbl_opacity)
        form_frame.addRow("Opacity:", h_op)

        self.layout_v.addWidget(self.grp_frame)

        # ── Element Specific Container ───────────────────────────
        self.element_container = QWidget()
        self.element_layout = QVBoxLayout(self.element_container)
        self.element_layout.setContentsMargins(0, 0, 0, 0)
        self.element_layout.setSpacing(6)
        self.layout_v.addWidget(self.element_container)

        self.layout_v.addStretch()
        self.scroll.setWidget(self.container)
        self.setWidget(self.scroll)

    def set_item(self, item):
        """Loads properties of the given layout item into the inspector."""
        self._current_item = item
        if not item:
            self.lbl_title.setText("No Item Selected")
            self.grp_common.setEnabled(False)
            self.grp_frame.setEnabled(False)
            self._clear_element_ui()
            return

        self.grp_common.setEnabled(True)
        self.grp_frame.setEnabled(True)

        name = item.id() if hasattr(item, "id") and item.id() else (item.displayName() if hasattr(item, "displayName") else type(item).__name__)
        item_type = type(item).__name__.replace("QgsLayoutItem", "")
        self.lbl_title.setText(f"{name} ({item_type})")

        try:
            # Load Position & Size
            pos = item.pos()
            if hasattr(item, "sizeWithUnits"):
                sz = item.sizeWithUnits()
                w_val = sz.width()
                h_val = sz.height()
            elif hasattr(item, "rect"):
                sz = item.rect()
                w_val = sz.width()
                h_val = sz.height()
            elif hasattr(item, "boundingRect"):
                sz = item.boundingRect()
                w_val = sz.width()
                h_val = sz.height()
            else:
                w_val = 10.0
                h_val = 10.0
            self.spn_x.blockSignals(True); self.spn_x.setValue(pos.x()); self.spn_x.blockSignals(False)
            self.spn_y.blockSignals(True); self.spn_y.setValue(pos.y()); self.spn_y.blockSignals(False)
            self.spn_w.blockSignals(True); self.spn_w.setValue(w_val); self.spn_w.blockSignals(False)
            self.spn_h.blockSignals(True); self.spn_h.setValue(h_val); self.spn_h.blockSignals(False)
            rot = item.itemRotation() if hasattr(item, "itemRotation") else (item.rotation() if hasattr(item, "rotation") else 0.0)
            self.spn_rot.blockSignals(True); self.spn_rot.setValue(rot); self.spn_rot.blockSignals(False)
            self.chk_lock.blockSignals(True); self.chk_lock.setChecked(item.isLocked() if hasattr(item, "isLocked") else False); self.chk_lock.blockSignals(False)

            frame_val = item.frameEnabled() if hasattr(item, "frameEnabled") else (item.hasFrame() if hasattr(item, "hasFrame") else False)
            bg_val = item.hasBackground() if hasattr(item, "hasBackground") else (item.backgroundEnabled() if hasattr(item, "backgroundEnabled") else False)
            self.chk_has_frame.blockSignals(True); self.chk_has_frame.setChecked(frame_val); self.chk_has_frame.blockSignals(False)
            self.chk_has_bg.blockSignals(True); self.chk_has_bg.setChecked(bg_val); self.chk_has_bg.blockSignals(False)

            # Opacity
            op = int(item.opacity() * 100) if hasattr(item, "opacity") else 100
            self.slider_opacity.blockSignals(True)
            self.slider_opacity.setValue(op)
            self.lbl_opacity.setText(f"{op}%")
            self.slider_opacity.blockSignals(False)

            self._clear_element_ui()

            # Build element-specific editor
            if isinstance(item, QgsLayoutItemMap):
                self._build_map_editor(item)
            elif isinstance(item, QgsLayoutItemLabel):
                self._build_label_editor(item)
            elif isinstance(item, QgsLayoutItemScaleBar):
                self._build_scalebar_editor(item)
            elif isinstance(item, QgsLayoutItemLegend):
                self._build_legend_editor(item)
            elif isinstance(item, QgsLayoutItemPicture):
                self._build_picture_editor(item)
            elif isinstance(item, QgsLayoutItemShape):
                self._build_shape_editor(item)
            elif hasattr(item, "setVectorLayer"):  # Attribute Table
                self._build_table_editor(item)
        except Exception as e:
            print(f"[LayoutPropertiesDock] Warning loading properties: {e}")

    def _clear_element_ui(self):
        while self.element_layout.count() > 0:
            it = self.element_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    # ── Map Item Editor ──────────────────────────────────────────
    def _build_map_editor(self, map_item):
        grp = QGroupBox("Map Properties")
        form = QFormLayout(grp)
        form.setSpacing(5)

        self.spn_scale = QDoubleSpinBox()
        self.spn_scale.setRange(1, 100_000_000)
        self.spn_scale.setDecimals(0)
        self.spn_scale.setValue(map_item.scale())
        self.spn_scale.valueChanged.connect(lambda val: (map_item.setScale(val), self.designer.view.update()))
        form.addRow("Scale 1 :", self.spn_scale)

        # Extent Info
        ext = map_item.extent()
        lbl_ext = QLabel(f"X: [{ext.xMinimum():.2f}, {ext.xMaximum():.2f}]\nY: [{ext.yMinimum():.2f}, {ext.yMaximum():.2f}]")
        lbl_ext.setStyleSheet("color: #475569; font-size: 10px;")
        form.addRow("Extent:", lbl_ext)

        # CRS
        crs_str = map_item.crs().authid() if map_item.crs().isValid() else "Not set"
        lbl_crs = QLabel(crs_str)
        lbl_crs.setStyleSheet("color: #0284c7; font-weight: 600;")
        form.addRow("CRS:", lbl_crs)

        btn_canvas_ext = QPushButton("Sync Extent from Main Map")
        btn_canvas_ext.clicked.connect(lambda: self._sync_extent_from_canvas(map_item))
        form.addRow(btn_canvas_ext)

        btn_apply_to_canvas = QPushButton("Set Main Map Extent from Layout")
        btn_apply_to_canvas.clicked.connect(lambda: self._sync_canvas_from_map(map_item))
        form.addRow(btn_apply_to_canvas)

        # Coordinate Frame / Grid
        chk_grid = QCheckBox("Draw Coordinate Grid & Ticks")
        chk_grid.setChecked(map_item.grids().size() > 0 and map_item.grids().grid(0).isEnabled())
        chk_grid.toggled.connect(lambda chk: self._toggle_map_grid(map_item, chk))
        form.addRow(chk_grid)

        self.element_layout.addWidget(grp)

    def _sync_extent_from_canvas(self, map_item):
        main_canvas = getattr(self.designer.mw, "map_canvas", None)
        if main_canvas and main_canvas.canvas:
            map_item.setExtent(main_canvas.canvas.extent())
            map_item.setScale(main_canvas.canvas.scale())
            self.spn_scale.setValue(map_item.scale())
            self.designer.view.update()

    def _sync_canvas_from_map(self, map_item):
        main_canvas = getattr(self.designer.mw, "map_canvas", None)
        if main_canvas and main_canvas.canvas:
            main_canvas.canvas.setExtent(map_item.extent())
            main_canvas.canvas.refresh()

    def _toggle_map_grid(self, map_item, enabled):
        from qgis.core import QgsLayoutItemMapGrid
        if map_item.grids().size() == 0:
            grid = QgsLayoutItemMapGrid("Grid 1", map_item)
            grid.setStyle(QgsLayoutItemMapGrid.Cross)
            grid.setIntervalX(0.05)
            grid.setIntervalY(0.05)
            map_item.grids().addGrid(grid)
        map_item.grids().grid(0).setEnabled(enabled)
        self.designer.view.update()

    # ── Label / Title Item Editor ────────────────────────────────
    def _build_label_editor(self, label_item):
        grp = QGroupBox("Text & Font Properties")
        layout = QVBoxLayout(grp)
        layout.setSpacing(5)

        self.txt_edit = QTextEdit()
        self.txt_edit.setFixedHeight(75)
        self.txt_edit.setText(label_item.text())
        self.txt_edit.textChanged.connect(lambda: (label_item.setText(self.txt_edit.toPlainText()), self.designer.view.update()))
        layout.addWidget(self.txt_edit)

        # Dynamic variable helper buttons
        h_vars = QHBoxLayout()
        btn_date = QPushButton("+ Date")
        btn_date.clicked.connect(lambda: self.txt_edit.insertPlainText("[% format_date(now(), 'yyyy-MM-dd') %]"))
        h_vars.addWidget(btn_date)

        btn_scale = QPushButton("+ Scale")
        btn_scale.clicked.connect(lambda: self.txt_edit.insertPlainText("Scale: 1:[% round(map_scale, 0) %]"))
        h_vars.addWidget(btn_scale)
        layout.addLayout(h_vars)

        # Font & Color Controls
        h_font = QHBoxLayout()
        btn_font = QPushButton("Font...")
        btn_font.clicked.connect(lambda: self._pick_font(label_item))
        h_font.addWidget(btn_font)

        btn_col = QPushButton("Color...")
        btn_col.clicked.connect(lambda: self._pick_text_color(label_item))
        h_font.addWidget(btn_col)
        layout.addLayout(h_font)

        # Alignments
        f_align = QFormLayout()
        combo_h = QComboBox()
        combo_h.addItems(["Left", "Center", "Right", "Justify"])
        h_align_val = label_item.hAlign() if hasattr(label_item, "hAlign") else Qt.AlignLeft
        combo_h.setCurrentIndex(1 if h_align_val == Qt.AlignHCenter else (2 if h_align_val == Qt.AlignRight else 0))
        combo_h.currentIndexChanged.connect(lambda idx: self._set_h_align(label_item, idx))
        f_align.addRow("H-Align:", combo_h)

        combo_v = QComboBox()
        combo_v.addItems(["Top", "Middle", "Bottom"])
        v_align_val = label_item.vAlign() if hasattr(label_item, "vAlign") else Qt.AlignTop
        combo_v.setCurrentIndex(1 if v_align_val == Qt.AlignVCenter else (2 if v_align_val == Qt.AlignBottom else 0))
        combo_v.currentIndexChanged.connect(lambda idx: self._set_v_align(label_item, idx))
        f_align.addRow("V-Align:", combo_v)
        layout.addLayout(f_align)

        self.element_layout.addWidget(grp)

    def _set_h_align(self, label_item, idx):
        aligns = [Qt.AlignLeft, Qt.AlignHCenter, Qt.AlignRight, Qt.AlignJustify]
        label_item.setHAlign(aligns[idx])
        self.designer.view.update()

    def _set_v_align(self, label_item, idx):
        aligns = [Qt.AlignTop, Qt.AlignVCenter, Qt.AlignBottom]
        label_item.setVAlign(aligns[idx])
        self.designer.view.update()

    def _pick_font(self, label_item):
        font, ok = QFontDialog.getFont(label_item.font(), self, "Choose Label Font")
        if ok:
            label_item.setFont(font)
            self.designer.view.update()

    def _pick_text_color(self, label_item):
        col = QColorDialog.getColor(label_item.fontColor() if hasattr(label_item, "fontColor") else QColor("#000000"), self, "Choose Text Color")
        if col.isValid():
            label_item.setFontColor(col)
            self.designer.view.update()

    # ── Scale Bar Editor ─────────────────────────────────────────
    def _build_scalebar_editor(self, scale_item):
        grp = QGroupBox("Scale Bar Properties")
        form = QFormLayout(grp)
        form.setSpacing(5)

        combo_style = QComboBox()
        combo_style.addItems(["Single Box", "Double Box", "Line Ticks Up", "Line Ticks Down", "Numeric"])
        combo_style.setCurrentText(scale_item.style())
        combo_style.currentTextChanged.connect(lambda s: (scale_item.setStyle(s), self.designer.view.update()))
        form.addRow("Style:", combo_style)

        combo_units = QComboBox()
        combo_units.addItems(["Kilometers", "Meters", "Miles", "Feet"])
        combo_units.currentIndexChanged.connect(lambda idx: self._set_scalebar_units(scale_item, idx))
        form.addRow("Units:", combo_units)

        spn_seg = QSpinBox()
        spn_seg.setRange(1, 10)
        spn_seg.setValue(scale_item.numberOfSegments())
        spn_seg.valueChanged.connect(lambda val: (scale_item.setNumberOfSegments(val), self.designer.view.update()))
        form.addRow("Segments:", spn_seg)

        self.element_layout.addWidget(grp)

    def _set_scalebar_units(self, scale_item, idx):
        units = [
            QgsUnitTypes.DistanceKilometers,
            QgsUnitTypes.DistanceMeters,
            QgsUnitTypes.DistanceMiles,
            QgsUnitTypes.DistanceFeet,
        ]
        scale_item.setUnits(units[idx])
        self.designer.view.update()

    # ── Legend Editor ────────────────────────────────────────────
    def _build_legend_editor(self, legend_item):
        grp = QGroupBox("Legend Properties")
        form = QFormLayout(grp)
        form.setSpacing(5)

        txt_leg_title = QLineEdit(legend_item.title())
        txt_leg_title.textChanged.connect(lambda t: (legend_item.setTitle(t), self.designer.view.update()))
        form.addRow("Title:", txt_leg_title)

        chk_auto = QCheckBox("Auto-update from Map Layers")
        chk_auto.setChecked(legend_item.autoUpdateModel())
        chk_auto.toggled.connect(lambda c: (legend_item.setAutoUpdateModel(c), self.designer.view.update()))
        form.addRow(chk_auto)

        spn_cols = QSpinBox()
        spn_cols.setRange(1, 10)
        spn_cols.setValue(legend_item.columnCount())
        spn_cols.valueChanged.connect(lambda c: (legend_item.setColumnCount(c), self.designer.view.update()))
        form.addRow("Columns:", spn_cols)

        self.element_layout.addWidget(grp)

    # ── North Arrow / Picture Editor ─────────────────────────────
    def _build_picture_editor(self, pic_item):
        grp = QGroupBox("North Arrow & Picture")
        form = QFormLayout(grp)
        form.setSpacing(5)

        chk_sync = QCheckBox("Sync Rotation with Map")
        chk_sync.setChecked(pic_item.linkedMap() is not None)
        chk_sync.toggled.connect(lambda c: (pic_item.setLinkedMap(self.designer.get_main_map_item() if c else None), self.designer.view.update()))
        form.addRow(chk_sync)

        # Built-in North Arrow SVG Selector
        arrow_paths = [m for d in QgsApplication.svgPaths() for m in glob.glob(os.path.join(d, 'arrows', 'NorthArrow_*.svg'))]
        if arrow_paths:
            arrow_paths.sort()
            combo_arrows = QComboBox()
            for p in arrow_paths:
                combo_arrows.addItem(os.path.basename(p), p)
            current_path = pic_item.picturePath()
            idx = combo_arrows.findData(current_path)
            if idx >= 0:
                combo_arrows.setCurrentIndex(idx)
            combo_arrows.currentIndexChanged.connect(lambda i: (pic_item.setPicturePath(combo_arrows.itemData(i)), self.designer.view.update()))
            form.addRow("North Arrow Style:", combo_arrows)

        # Custom Image Browser
        btn_img = QPushButton("Browse Image...")
        btn_img.clicked.connect(lambda: self._browse_image(pic_item))
        form.addRow("Custom File:", btn_img)

        self.element_layout.addWidget(grp)

    def _browse_image(self, pic_item):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image or SVG", "", "Images (*.png *.jpg *.jpeg *.svg *.webp)")
        if path:
            pic_item.setPicturePath(path)
            self.designer.view.update()

    # ── Shape Editor ─────────────────────────────────────────────
    def _build_shape_editor(self, shape_item):
        grp = QGroupBox("Shape Geometry & Style")
        form = QFormLayout(grp)
        form.setSpacing(5)

        combo_type = QComboBox()
        combo_type.addItems(["Rectangle", "Ellipse", "Triangle"])
        shape_type = shape_item.shapeType() if hasattr(shape_item, "shapeType") else 0
        combo_type.setCurrentIndex(min(2, int(shape_type)))
        combo_type.currentIndexChanged.connect(lambda idx: (shape_item.setShapeType(idx), self.designer.view.update()))
        form.addRow("Shape Type:", combo_type)

        btn_fill = QPushButton("Fill Color...")
        btn_fill.clicked.connect(lambda: self._pick_shape_fill(shape_item))
        form.addRow("Fill:", btn_fill)

        self.element_layout.addWidget(grp)

    def _pick_shape_fill(self, shape_item):
        col = QColorDialog.getColor(QColor("#ffffff"), self, "Select Shape Fill Color")
        if col.isValid() and hasattr(shape_item, "symbol") and shape_item.symbol():
            shape_item.symbol().setColor(col)
            self.designer.view.update()

    # ── Table Editor ─────────────────────────────────────────────
    def _build_table_editor(self, table_item):
        grp = QGroupBox("Attribute Table Properties")
        form = QFormLayout(grp)
        form.setSpacing(5)

        combo_layers = QComboBox()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == 0:  # VectorLayer
                combo_layers.addItem(layer.name(), layer)
        combo_layers.currentIndexChanged.connect(lambda idx: (table_item.setVectorLayer(combo_layers.itemData(idx)), self.designer.view.update()))
        form.addRow("Vector Layer:", combo_layers)

        spn_max = QSpinBox()
        spn_max.setRange(1, 1000)
        spn_max.setValue(table_item.maximumNumberOfFeatures() if hasattr(table_item, "maximumNumberOfFeatures") else 20)
        spn_max.valueChanged.connect(lambda val: (table_item.setMaximumNumberOfFeatures(val), self.designer.view.update()) if hasattr(table_item, "setMaximumNumberOfFeatures") else None)
        form.addRow("Max Features:", spn_max)

        self.element_layout.addWidget(grp)

    # ── Common Geometry & Appearance Callbacks ────────────────────
    def _on_pos_changed(self):
        if self._current_item:
            self._current_item.attemptMove(QgsLayoutPoint(self.spn_x.value(), self.spn_y.value(), QgsUnitTypes.LayoutMillimeters))
            self.designer.view.update()

    def _on_size_changed(self):
        if self._current_item:
            self._current_item.attemptResize(QgsLayoutSize(self.spn_w.value(), self.spn_h.value(), QgsUnitTypes.LayoutMillimeters))
            self.designer.view.update()

    def _on_rot_changed(self, angle):
        if self._current_item:
            self._current_item.setItemRotation(angle)
            self.designer.view.update()

    def _on_lock_toggled(self, locked):
        if self._current_item:
            self._current_item.setLocked(locked)
            self.designer.items_dock.refresh_items()

    def _on_frame_toggled(self, frame):
        if self._current_item:
            self._current_item.setFrameEnabled(frame)
            self.designer.view.update()

    def _on_bg_toggled(self, bg):
        if self._current_item:
            self._current_item.setBackgroundEnabled(bg)
            self.designer.view.update()

    def _on_opacity_changed(self, val):
        if self._current_item and hasattr(self._current_item, "setOpacity"):
            self._current_item.setOpacity(val / 100.0)
            self.lbl_opacity.setText(f"{val}%")
            self.designer.view.update()

    def _pick_frame_color(self):
        if self._current_item and hasattr(self._current_item, "setFrameStrokeColor"):
            col = QColorDialog.getColor(QColor("#000000"), self, "Select Frame Color")
            if col.isValid():
                self._current_item.setFrameStrokeColor(col)
                self.designer.view.update()

    def _pick_bg_color(self):
        if self._current_item and hasattr(self._current_item, "setBackgroundColor"):
            col = QColorDialog.getColor(QColor("#ffffff"), self, "Select Background Color")
            if col.isValid():
                self._current_item.setBackgroundColor(col)
                self.designer.view.update()
