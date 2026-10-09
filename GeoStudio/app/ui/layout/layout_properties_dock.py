# -*- coding: utf-8 -*-
"""
GeoStudio - Layout Item Properties Dock
Provides property inspectors for layout elements:
- Common geometry: X, Y, Width, Height, Rotation, Frame, Background, Lock
- Specific tabs/editors for Map, Title/Label, Scale Bar, Legend, North Arrow, Shapes
"""

import datetime
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QLabel, QTextEdit, QColorDialog, QFontDialog,
    QScrollArea, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from qgis.core import (
    QgsUnitTypes, QgsLayoutSize, QgsLayoutPoint,
    QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemScaleBar,
    QgsLayoutItemLegend, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutMeasurement
)


class LayoutPropertiesDock(QDockWidget):
    """Properties panel showing context-sensitive properties for selected layout items."""

    def __init__(self, layout_designer, parent=None):
        super().__init__("Item Properties", parent or layout_designer)
        self.designer = layout_designer
        self.setObjectName("layout_properties_dock")
        self.setMinimumWidth(260)
        self.setMaximumWidth(420)

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
        self.lbl_title.setStyleSheet("color: #0f172a; padding: 4px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;")
        self.layout_v.addWidget(self.lbl_title)

        # ── Common Position & Size Group ─────────────────────────
        self.grp_common = QGroupBox("Position and Size (mm)")
        form_pos = QFormLayout(self.grp_common)
        form_pos.setSpacing(6)

        self.spn_x = QDoubleSpinBox(); self.spn_x.setRange(-1000, 5000); self.spn_x.setDecimals(1)
        self.spn_y = QDoubleSpinBox(); self.spn_y.setRange(-1000, 5000); self.spn_y.setDecimals(1)
        self.spn_w = QDoubleSpinBox(); self.spn_w.setRange(1, 5000); self.spn_w.setDecimals(1)
        self.spn_h = QDoubleSpinBox(); self.spn_h.setRange(1, 5000); self.spn_h.setDecimals(1)
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

        self.chk_lock = QCheckBox("Lock Position")
        self.chk_lock.toggled.connect(self._on_lock_toggled)
        form_pos.addRow(self.chk_lock)

        self.layout_v.addWidget(self.grp_common)

        # ── Frame & Background Group ─────────────────────────────
        self.grp_frame = QGroupBox("Appearance & Frame")
        form_frame = QFormLayout(self.grp_frame)
        form_frame.setSpacing(6)

        self.chk_has_frame = QCheckBox("Draw Frame / Border")
        self.chk_has_frame.toggled.connect(self._on_frame_toggled)
        form_frame.addRow(self.chk_has_frame)

        self.chk_has_bg = QCheckBox("Background Color")
        self.chk_has_bg.toggled.connect(self._on_bg_toggled)
        form_frame.addRow(self.chk_has_bg)

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

        name = item.id() or item.displayName() or type(item).__name__
        self.lbl_title.setText(f"{name} ({type(item).__name__.replace('QgsLayoutItem', '')})")

        try:
            # Load Position & Size
            pos = item.pos()
            sz = item.sizeWithUnits() if hasattr(item, "sizeWithUnits") else item.rect()
            self.spn_x.blockSignals(True); self.spn_x.setValue(pos.x()); self.spn_x.blockSignals(False)
            self.spn_y.blockSignals(True); self.spn_y.setValue(pos.y()); self.spn_y.blockSignals(False)
            self.spn_w.blockSignals(True); self.spn_w.setValue(sz.width()); self.spn_w.blockSignals(False)
            self.spn_h.blockSignals(True); self.spn_h.setValue(sz.height()); self.spn_h.blockSignals(False)
            rot = item.itemRotation() if hasattr(item, "itemRotation") else (item.rotation() if hasattr(item, "rotation") else 0.0)
            self.spn_rot.blockSignals(True); self.spn_rot.setValue(rot); self.spn_rot.blockSignals(False)
            self.chk_lock.blockSignals(True); self.chk_lock.setChecked(item.isLocked() if hasattr(item, "isLocked") else False); self.chk_lock.blockSignals(False)

            frame_val = item.frameEnabled() if hasattr(item, "frameEnabled") else (item.hasFrame() if hasattr(item, "hasFrame") else False)
            bg_val = item.hasBackground() if hasattr(item, "hasBackground") else (item.backgroundEnabled() if hasattr(item, "backgroundEnabled") else False)
            self.chk_has_frame.blockSignals(True); self.chk_has_frame.setChecked(frame_val); self.chk_has_frame.blockSignals(False)
            self.chk_has_bg.blockSignals(True); self.chk_has_bg.setChecked(bg_val); self.chk_has_bg.blockSignals(False)

            self._clear_element_ui()

            # Build specific editor
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

        self.spn_scale = QDoubleSpinBox()
        self.spn_scale.setRange(1, 100_000_000)
        self.spn_scale.setDecimals(0)
        self.spn_scale.setValue(map_item.scale())
        self.spn_scale.valueChanged.connect(lambda val: map_item.setScale(val))
        form.addRow("Scale 1 :", self.spn_scale)

        btn_canvas_ext = QPushButton("Sync Extent from Canvas")
        btn_canvas_ext.clicked.connect(lambda: self._sync_extent_from_canvas(map_item))
        form.addRow(btn_canvas_ext)

        btn_apply_to_canvas = QPushButton("Set Canvas Extent from Map")
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

    # ── Label / Title Item Editor ────────────────────────────────
    def _build_label_editor(self, label_item):
        grp = QGroupBox("Text / Title Properties")
        layout = QVBoxLayout(grp)

        self.txt_edit = QTextEdit()
        self.txt_edit.setFixedHeight(80)
        self.txt_edit.setText(label_item.text())
        self.txt_edit.textChanged.connect(lambda: label_item.setText(self.txt_edit.toPlainText()))
        layout.addWidget(self.txt_edit)

        # Dynamic variable helper buttons
        h_vars = QHBoxLayout()
        btn_date = QPushButton("+ Date")
        btn_date.clicked.connect(lambda: self._insert_variable("[% @project_title %] — [% format_date(now(), 'yyyy-MM-dd') %]"))
        h_vars.addWidget(btn_date)

        btn_scale = QPushButton("+ Scale")
        btn_scale.clicked.connect(lambda: self._insert_variable("Scale: 1:[% round(map_scale, 0) %]"))
        h_vars.addWidget(btn_scale)
        layout.addLayout(h_vars)

        btn_font = QPushButton("Select Font...")
        btn_font.clicked.connect(lambda: self._pick_font(label_item))
        layout.addWidget(btn_font)

        self.element_layout.addWidget(grp)

    def _insert_variable(self, var_str):
        self.txt_edit.insertPlainText(var_str)

    def _pick_font(self, label_item):
        font, ok = QFontDialog.getFont(label_item.font(), self, "Choose Label Font")
        if ok:
            label_item.setFont(font)

    # ── Scale Bar Editor ─────────────────────────────────────────
    def _build_scalebar_editor(self, scale_item):
        grp = QGroupBox("Scale Bar Properties")
        form = QFormLayout(grp)

        combo_style = QComboBox()
        combo_style.addItems(["Single Box", "Double Box", "Line Ticks Up", "Line Ticks Down", "Numeric"])
        combo_style.setCurrentText(scale_item.style())
        combo_style.currentTextChanged.connect(lambda s: scale_item.setStyle(s))
        form.addRow("Style:", combo_style)

        spn_seg = QSpinBox()
        spn_seg.setRange(1, 10)
        spn_seg.setValue(scale_item.numberOfSegments())
        spn_seg.valueChanged.connect(lambda val: scale_item.setNumberOfSegments(val))
        form.addRow("Segments:", spn_seg)

        self.element_layout.addWidget(grp)

    # ── Legend Editor ────────────────────────────────────────────
    def _build_legend_editor(self, legend_item):
        grp = QGroupBox("Legend Properties")
        form = QFormLayout(grp)

        txt_leg_title = QLineEdit(legend_item.title())
        txt_leg_title.textChanged.connect(lambda t: legend_item.setTitle(t))
        form.addRow("Title:", txt_leg_title)

        chk_auto = QCheckBox("Auto-update from Map")
        chk_auto.setChecked(legend_item.autoUpdateModel())
        chk_auto.toggled.connect(lambda c: legend_item.setAutoUpdateModel(c))
        form.addRow(chk_auto)

        self.element_layout.addWidget(grp)

    # ── North Arrow / Picture Editor ─────────────────────────────
    def _build_picture_editor(self, pic_item):
        grp = QGroupBox("North Arrow / Picture")
        form = QFormLayout(grp)

        chk_sync = QCheckBox("Sync Rotation with Map")
        chk_sync.setChecked(pic_item.linkedMap() is not None)
        chk_sync.toggled.connect(lambda c: pic_item.setLinkedMap(self.designer.get_main_map_item() if c else None))
        form.addRow(chk_sync)

        self.element_layout.addWidget(grp)

    # ── Common Callbacks ─────────────────────────────────────────
    def _on_pos_changed(self):
        if self._current_item:
            self._current_item.attemptMove(QgsLayoutPoint(self.spn_x.value(), self.spn_y.value(), QgsUnitTypes.LayoutMillimeters))

    def _on_size_changed(self):
        if self._current_item:
            self._current_item.attemptResize(QgsLayoutSize(self.spn_w.value(), self.spn_h.value(), QgsUnitTypes.LayoutMillimeters))

    def _on_rot_changed(self, angle):
        if self._current_item:
            self._current_item.setItemRotation(angle)

    def _on_lock_toggled(self, locked):
        if self._current_item:
            self._current_item.setLocked(locked)

    def _on_frame_toggled(self, frame):
        if self._current_item:
            self._current_item.setFrameEnabled(frame)

    def _on_bg_toggled(self, bg):
        if self._current_item:
            self._current_item.setBackgroundEnabled(bg)
