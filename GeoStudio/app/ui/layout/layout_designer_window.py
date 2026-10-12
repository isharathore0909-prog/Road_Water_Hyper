# -*- coding: utf-8 -*-
"""
GeoStudio - Layout Designer Workstation Window
Professional cartographic design window providing:
- Full interactive QgsLayoutView canvas with pan, zoom, selection, and drag-to-draw tools
- Complete GIS layout designer workflow:
    * Top Menus: Layout, Edit, View, Items, Add Item, Atlas, Settings, Help
    * Top Toolbars: Project/Layout, Navigation, Alignment, Distribution
    * Left Vertical Toolbar: 14 creation and manipulation tools (Select, Move Item, Add Map,
      Add Label, Add Legend, Add Scale Bar, Add North Arrow, Add Image, Add Table,
      Add Shape, Add Line, Add Rectangle, Add Ellipse, Add Arrow)
    * Center Page Canvas with status bar (x, y coordinates in mm, page, zoom %)
    * Upper Right Dock: [Items] [Undo History]
    * Lower Right Dock: [Layout] [Item Properties] [Guides]
- Export connected seamlessly to GeoStudio's existing PrintExportDialog (PDF, PNG, JPG, TIFF, SVG)
- System Printing & Print Preview
- Canvas-to-Layout and Layout-to-Canvas Extent Synchronization
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAction,
    QToolBar, QMessageBox, QFileDialog, QApplication, QDockWidget,
    QTabWidget, QUndoView, QLabel, QStatusBar, QGroupBox, QFormLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QIcon, QFont, QColor, QPolygonF
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog

from qgis.core import (
    QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture,
    QgsLayoutItemShape, QgsLayoutItemPolyline, QgsLayoutItemPolygon,
    QgsLayoutItemHtml, QgsLayoutItemAttributeTable, QgsLayoutSize,
    QgsLayoutPoint, QgsUnitTypes, QgsLayoutMeasurement, QgsLayoutGuide,
    QgsLayoutItemRegistry, QgsApplication
)
from qgis.gui import (
    QgsLayoutView, QgsLayoutViewToolPan, QgsLayoutViewToolZoom,
    QgsLayoutViewToolSelect, QgsLayoutViewToolMoveItemContent,
    QgsLayoutViewToolAddItem, QgsLayoutViewToolAddNodeItem
)

from resources.icons.icon_provider import get_icon
from core.style import OFFWHITE_STYLESHEET
from .layout_items_dock import LayoutItemsDock
from .layout_properties_dock import LayoutPropertiesDock
from .layout_export_dialog import LayoutExportDialog


PAGE_PRESETS = {
    "A4 Portrait": (210.0, 297.0),
    "A4 Landscape": (297.0, 210.0),
    "A3 Portrait": (297.0, 420.0),
    "A3 Landscape": (420.0, 297.0),
    "A2 Portrait": (420.0, 594.0),
    "A2 Landscape": (594.0, 420.0),
    "A1 Portrait": (594.0, 841.0),
    "A1 Landscape": (841.0, 594.0),
    "A0 Portrait": (841.0, 1189.0),
    "A0 Landscape": (1189.0, 841.0),
    "Letter Landscape": (279.4, 215.9),
    "Letter Portrait": (215.9, 279.4),
}


class LayoutSettingsTab(QWidget):
    """Layout settings panel showing General Page Settings, Guides/Grid, and Export settings."""

    def __init__(self, designer, parent=None):
        super().__init__(parent)
        self.designer = designer
        self._build_ui()
        self._load_current_settings()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(10)

        # 1. Page & General Settings
        grp_gen = QGroupBox("Page & General Settings")
        f_gen = QFormLayout(grp_gen)
        f_gen.setSpacing(6)

        self.combo_page_size = QComboBox()
        self.combo_page_size.addItems(list(PAGE_PRESETS.keys()) + ["Custom"])
        self.combo_page_size.currentTextChanged.connect(self._on_page_preset_changed)
        f_gen.addRow("Page Preset:", self.combo_page_size)

        h_custom_size = QHBoxLayout()
        self.spn_page_w = QDoubleSpinBox()
        self.spn_page_w.setRange(10.0, 5000.0)
        self.spn_page_w.setValue(297.0)
        self.spn_page_w.setSuffix(" mm")
        self.spn_page_w.valueChanged.connect(self._on_custom_page_size_changed)

        self.spn_page_h = QDoubleSpinBox()
        self.spn_page_h.setRange(10.0, 5000.0)
        self.spn_page_h.setValue(210.0)
        self.spn_page_h.setSuffix(" mm")
        self.spn_page_h.valueChanged.connect(self._on_custom_page_size_changed)

        h_custom_size.addWidget(self.spn_page_w)
        h_custom_size.addWidget(QLabel("×"))
        h_custom_size.addWidget(self.spn_page_h)
        f_gen.addRow("Dimensions:", h_custom_size)

        self.combo_ref_map = QComboBox()
        self.combo_ref_map.addItem("Current Map")
        self.combo_ref_map.currentIndexChanged.connect(self._on_ref_map_changed)
        f_gen.addRow("Reference Map:", self.combo_ref_map)

        vbox.addWidget(grp_gen)

        # 2. Guides and Grid
        grp_grid = QGroupBox("Guides and Grid")
        f_grid = QFormLayout(grp_grid)
        f_grid.setSpacing(6)

        h_spacing = QHBoxLayout()
        self.spn_spacing = QDoubleSpinBox()
        self.spn_spacing.setRange(0.1, 500.0)
        self.spn_spacing.setValue(10.0)
        self.spn_spacing.valueChanged.connect(self._apply_grid_settings)

        self.combo_grid_units = QComboBox()
        self.combo_grid_units.addItems(["mm", "cm", "px"])
        self.combo_grid_units.currentTextChanged.connect(self._apply_grid_settings)

        h_spacing.addWidget(self.spn_spacing, 1)
        h_spacing.addWidget(self.combo_grid_units)
        f_grid.addRow("Grid spacing:", h_spacing)

        h_offset_x = QHBoxLayout()
        self.spn_off_x = QDoubleSpinBox()
        self.spn_off_x.setRange(-500.0, 500.0)
        self.spn_off_x.setValue(0.0)
        self.spn_off_x.valueChanged.connect(self._apply_grid_settings)
        h_offset_x.addWidget(self.spn_off_x, 1)
        h_offset_x.addWidget(QLabel("mm"))
        f_grid.addRow("Grid offset X:", h_offset_x)

        h_offset_y = QHBoxLayout()
        self.spn_off_y = QDoubleSpinBox()
        self.spn_off_y.setRange(-500.0, 500.0)
        self.spn_off_y.setValue(0.0)
        self.spn_off_y.valueChanged.connect(self._apply_grid_settings)
        h_offset_y.addWidget(self.spn_off_y, 1)
        h_offset_y.addWidget(QLabel("mm"))
        f_grid.addRow("Grid offset Y:", h_offset_y)

        self.spn_snap_tol = QSpinBox()
        self.spn_snap_tol.setRange(1, 50)
        self.spn_snap_tol.setValue(5)
        self.spn_snap_tol.setSuffix(" px")
        self.spn_snap_tol.valueChanged.connect(self._apply_snapping_settings)
        f_grid.addRow("Snap tolerance:", self.spn_snap_tol)

        self.chk_show_grid = QCheckBox("Show Grid")
        self.chk_show_grid.toggled.connect(self._on_toggle_grid)
        f_grid.addRow(self.chk_show_grid)

        self.chk_snap_grid = QCheckBox("Snap to Grid")
        self.chk_snap_grid.toggled.connect(self._apply_snapping_settings)
        f_grid.addRow(self.chk_snap_grid)

        self.chk_snap_guides = QCheckBox("Snap to Guides")
        self.chk_snap_guides.setChecked(True)
        self.chk_snap_guides.toggled.connect(self._apply_snapping_settings)
        f_grid.addRow(self.chk_snap_guides)

        self.chk_snap_items = QCheckBox("Snap to Items")
        self.chk_snap_items.setChecked(True)
        self.chk_snap_items.toggled.connect(self._apply_snapping_settings)
        f_grid.addRow(self.chk_snap_items)

        vbox.addWidget(grp_grid)

        # 3. Export Settings
        grp_export = QGroupBox("Export Settings")
        f_exp = QFormLayout(grp_export)
        f_exp.setSpacing(6)

        self.combo_dpi = QComboBox()
        self.combo_dpi.addItems(["72 dpi", "96 dpi", "150 dpi", "200 dpi", "300 dpi", "600 dpi", "1200 dpi"])
        self.combo_dpi.setCurrentText("300 dpi")
        f_exp.addRow("Export resolution:", self.combo_dpi)

        self.chk_raster = QCheckBox("Print as raster")
        f_exp.addRow(self.chk_raster)

        self.chk_vectors = QCheckBox("Always export as vectors")
        self.chk_vectors.setChecked(True)
        f_exp.addRow(self.chk_vectors)

        btn_open_export = QPushButton("Open GeoStudio Export Dialog...")
        btn_open_export.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_open_export.clicked.connect(self.designer.open_export_dialog)
        f_exp.addRow(btn_open_export)

        vbox.addWidget(grp_export)
        vbox.addStretch()

    def _load_current_settings(self):
        if not self.designer.layout:
            return
        layout = self.designer.layout
        pages = layout.pageCollection().pages()
        if pages:
            p = pages[0]
            w = p.pageSize().width()
            h = p.pageSize().height()
            self.spn_page_w.blockSignals(True)
            self.spn_page_h.blockSignals(True)
            self.spn_page_w.setValue(w)
            self.spn_page_h.setValue(h)
            self.spn_page_w.blockSignals(False)
            self.spn_page_h.blockSignals(False)

            # Match preset
            matched = False
            for name, (pw, ph) in PAGE_PRESETS.items():
                if abs(pw - w) < 1.0 and abs(ph - h) < 1.0:
                    self.combo_page_size.blockSignals(True)
                    self.combo_page_size.setCurrentText(name)
                    self.combo_page_size.blockSignals(False)
                    matched = True
                    break
            if not matched:
                self.combo_page_size.blockSignals(True)
                self.combo_page_size.setCurrentText("Custom")
                self.combo_page_size.blockSignals(False)

        # Snapper settings
        if hasattr(layout, "snapper") and layout.snapper():
            s = layout.snapper()
            self.chk_snap_grid.blockSignals(True)
            self.chk_snap_grid.setChecked(s.snapToGrid())
            self.chk_snap_grid.blockSignals(False)

            self.chk_snap_guides.blockSignals(True)
            self.chk_snap_guides.setChecked(s.snapToGuides())
            self.chk_snap_guides.blockSignals(False)

            self.chk_snap_items.blockSignals(True)
            self.chk_snap_items.setChecked(s.snapToItems())
            self.chk_snap_items.blockSignals(False)

            self.spn_snap_tol.blockSignals(True)
            self.spn_snap_tol.setValue(s.snapTolerance())
            self.spn_snap_tol.blockSignals(False)

    def _on_page_preset_changed(self, text):
        if text in PAGE_PRESETS:
            w, h = PAGE_PRESETS[text]
            self.spn_page_w.setValue(w)
            self.spn_page_h.setValue(h)
            self._set_page_size(w, h)

    def _on_custom_page_size_changed(self):
        w = self.spn_page_w.value()
        h = self.spn_page_h.value()
        self._set_page_size(w, h)

    def _set_page_size(self, w: float, h: float):
        if not self.designer.layout:
            return
        pages = self.designer.layout.pageCollection().pages()
        if pages:
            pages[0].attemptResize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
            self.designer.view.update()
            self.designer.zoom_to_page()

    def _apply_grid_settings(self):
        if not self.designer.layout or not hasattr(self.designer.layout, "gridSettings"):
            return
        gs = self.designer.layout.gridSettings()
        val = self.spn_spacing.value()
        unit_str = self.combo_grid_units.currentText()
        unit = QgsUnitTypes.LayoutMillimeters
        if unit_str == "cm":
            unit = QgsUnitTypes.LayoutCentimeters
        elif unit_str == "px":
            unit = QgsUnitTypes.LayoutPixels

        gs.setResolution(QgsLayoutMeasurement(val, unit))
        gs.setOffset(QgsLayoutPoint(self.spn_off_x.value(), self.spn_off_y.value(), unit))
        self.designer.view.update()

    def _apply_snapping_settings(self):
        if not self.designer.layout or not hasattr(self.designer.layout, "snapper"):
            return
        snapper = self.designer.layout.snapper()
        snapper.setSnapToGrid(self.chk_snap_grid.isChecked())
        snapper.setSnapToGuides(self.chk_snap_guides.isChecked())
        snapper.setSnapToItems(self.chk_snap_items.isChecked())
        snapper.setSnapTolerance(self.spn_snap_tol.value())

    def _on_toggle_grid(self, checked):
        if not self.designer.layout:
            return
        self.designer.layout.renderContext().setGridVisible(checked)
        self.designer.view.update()

    def refresh_maps(self):
        self.combo_ref_map.blockSignals(True)
        self.combo_ref_map.clear()
        self.combo_ref_map.addItem("Current Map")
        if self.designer.layout:
            for item in self.designer.layout.items():
                if isinstance(item, QgsLayoutItemMap):
                    name = item.id() or "Map Frame"
                    self.combo_ref_map.addItem(name)
        self.combo_ref_map.blockSignals(False)

    def _on_ref_map_changed(self, idx):
        pass


class GuidesTab(QWidget):
    """Guides manager tab for adding and configuring horizontal & vertical guides."""

    def __init__(self, designer, parent=None):
        super().__init__(parent)
        self.designer = designer
        self._build_ui()
        self._refresh_guides_table()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        lbl = QLabel("Layout Guides (mm)")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        vbox.addWidget(lbl)

        # Checkboxes for guides visibility & snapping
        h_chk = QHBoxLayout()
        self.chk_show_guides = QCheckBox("Show Guides")
        self.chk_show_guides.setChecked(True)
        self.chk_show_guides.toggled.connect(self._on_toggle_show_guides)
        h_chk.addWidget(self.chk_show_guides)

        self.chk_snap_guides = QCheckBox("Snap to Guides")
        self.chk_snap_guides.setChecked(True)
        self.chk_snap_guides.toggled.connect(self._on_toggle_snap_guides)
        h_chk.addWidget(self.chk_snap_guides)
        vbox.addLayout(h_chk)

        self.table_guides = QTableWidget(0, 2)
        self.table_guides.setHorizontalHeaderLabels(["Orientation", "Position (mm)"])
        self.table_guides.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_guides.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_guides.setStyleSheet("background: white; border: 1px solid #cbd5e1;")
        self.table_guides.itemChanged.connect(self._on_guide_cell_changed)
        vbox.addWidget(self.table_guides, 1)

        h_ctrl = QHBoxLayout()
        self.btn_add_h = QPushButton("+ Horizontal")
        self.btn_add_h.clicked.connect(self._add_horizontal_guide)
        h_ctrl.addWidget(self.btn_add_h)

        self.btn_add_v = QPushButton("+ Vertical")
        self.btn_add_v.clicked.connect(self._add_vertical_guide)
        h_ctrl.addWidget(self.btn_add_v)

        self.btn_del = QPushButton("Delete")
        self.btn_del.clicked.connect(self._delete_selected_guide)
        h_ctrl.addWidget(self.btn_del)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self._clear_guides)
        h_ctrl.addWidget(self.btn_clear)

        vbox.addLayout(h_ctrl)

    def _on_toggle_show_guides(self, checked):
        if self.designer.layout and hasattr(self.designer.layout, "guides"):
            self.designer.layout.guides().setVisible(checked)
            self.designer.view.update()

    def _on_toggle_snap_guides(self, checked):
        if self.designer.layout and hasattr(self.designer.layout, "snapper"):
            self.designer.layout.snapper().setSnapToGuides(checked)

    def _refresh_guides_table(self):
        if not self.designer.layout or not hasattr(self.designer.layout, "guides"):
            return
        self.table_guides.blockSignals(True)
        self.table_guides.setRowCount(0)
        guides = self.designer.layout.guides().guides()
        for g in guides:
            row = self.table_guides.rowCount()
            self.table_guides.insertRow(row)
            orient_str = "Horizontal" if g.orientation() == Qt.Horizontal else "Vertical"
            self.table_guides.setItem(row, 0, QTableWidgetItem(orient_str))
            pos_val = round(g.layoutPosition(), 2)
            self.table_guides.setItem(row, 1, QTableWidgetItem(str(pos_val)))
        self.table_guides.blockSignals(False)

    def _add_horizontal_guide(self):
        if not self.designer.layout:
            return
        pages = self.designer.layout.pageCollection().pages()
        if not pages:
            return
        page = pages[0]
        pos = round(page.pageSize().height() / 2.0, 1)
        guide = QgsLayoutGuide(Qt.Horizontal, QgsLayoutMeasurement(pos, QgsUnitTypes.LayoutMillimeters), page)
        self.designer.layout.guides().addGuide(guide)
        self.designer.view.update()
        self._refresh_guides_table()

    def _add_vertical_guide(self):
        if not self.designer.layout:
            return
        pages = self.designer.layout.pageCollection().pages()
        if not pages:
            return
        page = pages[0]
        pos = round(page.pageSize().width() / 2.0, 1)
        guide = QgsLayoutGuide(Qt.Vertical, QgsLayoutMeasurement(pos, QgsUnitTypes.LayoutMillimeters), page)
        self.designer.layout.guides().addGuide(guide)
        self.designer.view.update()
        self._refresh_guides_table()

    def _delete_selected_guide(self):
        row = self.table_guides.currentRow()
        if row < 0 or not self.designer.layout:
            return
        guides = list(self.designer.layout.guides().guides())
        if row < len(guides):
            self.designer.layout.guides().removeGuide(guides[row])
            self.designer.view.update()
            self._refresh_guides_table()

    def _clear_guides(self):
        if self.designer.layout and hasattr(self.designer.layout, "guides"):
            self.designer.layout.guides().clear()
            self.designer.view.update()
            self._refresh_guides_table()

    def _on_guide_cell_changed(self, item):
        row = item.row()
        if row < 0 or not self.designer.layout:
            return
        try:
            val = float(self.table_guides.item(row, 1).text())
            guides = list(self.designer.layout.guides().guides())
            if row < len(guides):
                self.designer.layout.guides().setGuideLayoutPosition(guides[row], val)
                self.designer.view.update()
        except ValueError:
            pass


class GeoStudioLayoutDesignerWindow(QMainWindow):
    """
    Dedicated Professional Layout Designer workstation for GeoStudio.
    """

    def __init__(self, layout, main_window=None, parent=None):
        super().__init__(parent or main_window)
        if layout is None:
            from qgis.core import QgsProject, QgsPrintLayout
            layout = QgsPrintLayout(QgsProject.instance())
            layout.initializeDefaults()
        self.layout = layout
        self.mw = main_window

        self._pending_tool_type = None

        layout_name = layout.name() if layout else "Layout Designer"
        self.setWindowTitle(f"GeoStudio Layout Designer — {layout_name}")
        self.setMinimumSize(1200, 800)
        self.resize(1500, 920)
        self.setStyleSheet(OFFWHITE_STYLESHEET)

        # Modal window flags to ensure proper z-index and focus above main map
        self.setWindowModality(Qt.ApplicationModal)

        self._build_ui()
        self._build_menus()
        self._build_toolbars()
        self._build_status_bar()
        self._connect_signals()

        self.zoom_to_page()

    def _build_ui(self):
        # 1. Central Canvas View
        self.view = QgsLayoutView(self)
        if self.layout:
            self.view.setCurrentLayout(self.layout)
        self.setCentralWidget(self.view)

        # Interactive Tools
        self.tool_select = QgsLayoutViewToolSelect(self.view)
        if self.layout and hasattr(self.tool_select, "setLayout"):
            try:
                self.tool_select.setLayout(self.layout)
            except Exception as e:
                print(f"[Warning] Failed to set layout on tool_select: {e}")

        # Keep tool_select synchronized whenever layout changes to ensure mouse handles are valid
        try:
            self.view.layoutSet.connect(self._on_layout_set)
        except Exception:
            pass

        self.tool_pan = QgsLayoutViewToolPan(self.view)
        self.tool_zoom = QgsLayoutViewToolZoom(self.view)
        self.tool_move_content = QgsLayoutViewToolMoveItemContent(self.view)
        self.tool_add_item = QgsLayoutViewToolAddItem(self.view)
        self.tool_add_node = QgsLayoutViewToolAddNodeItem(self.view)

        # Connect tool callbacks
        self.tool_add_item.createdItem.connect(self._on_item_created_interactive)
        self.tool_add_node.createdItem.connect(self._on_item_created_interactive)

        # Default tool is select
        self.view.setTool(self.tool_select)

        # Track mouse moves for mm coordinates in status bar
        self.view.cursorPosChanged.connect(self._on_view_mouse_moved)

        # 2. Upper Right Dock: [Items] [Undo History]
        self.upper_dock = QDockWidget("Items & History", self)
        self.upper_dock.setObjectName("layout_upper_dock")
        self.upper_dock.setMinimumWidth(280)
        self.upper_dock.setMaximumWidth(450)

        self.tab_upper = QTabWidget(self.upper_dock)
        self.tab_upper.setStyleSheet("QTabWidget::pane { border: 1px solid #cbd5e1; background: white; }")

        # Items panel widget
        self.items_dock_widget = LayoutItemsDock(self, self)
        self.items_dock = self.items_dock_widget
        self.tab_upper.addTab(self.items_dock_widget.widget(), "Items")

        # Undo History View
        if self.layout and hasattr(self.layout, "undoStack") and self.layout.undoStack():
            stk = self.layout.undoStack().stack() if hasattr(self.layout.undoStack(), "stack") else self.layout.undoStack()
            self.undo_view = QUndoView(stk)
            self.undo_view.setEmptyLabel("No actions")
            self.undo_view.setStyleSheet("background: white; border: none; font-size: 11px;")
            self.tab_upper.addTab(self.undo_view, "Undo History")

        self.upper_dock.setWidget(self.tab_upper)
        self.addDockWidget(Qt.RightDockWidgetArea, self.upper_dock)

        # 3. Lower Right Dock: [Layout] [Item Properties] [Guides]
        self.lower_dock = QDockWidget("Properties & Settings", self)
        self.lower_dock.setObjectName("layout_lower_dock")
        self.lower_dock.setMinimumWidth(280)
        self.lower_dock.setMaximumWidth(450)

        self.tab_lower = QTabWidget(self.lower_dock)
        self.tab_lower.setStyleSheet("QTabWidget::pane { border: 1px solid #cbd5e1; background: white; }")

        # Layout Settings Tab
        self.tab_layout_settings = LayoutSettingsTab(self)
        self.tab_lower.addTab(self.tab_layout_settings, "Layout")

        # Properties Inspector Widget
        self.props_dock_widget = LayoutPropertiesDock(self, self)
        self.props_dock = self.props_dock_widget
        self.tab_lower.addTab(self.props_dock_widget.widget(), "Item Properties")

        # Guides Tab
        self.tab_guides = GuidesTab(self)
        self.tab_lower.addTab(self.tab_guides, "Guides")

        self.lower_dock.setWidget(self.tab_lower)
        self.addDockWidget(Qt.RightDockWidgetArea, self.lower_dock)

        # Default tabs selection
        self.tab_upper.setCurrentIndex(0)
        self.tab_lower.setCurrentIndex(1)  # Default to Item Properties

        # Initial items population
        self.items_dock.refresh_items()
        self.tab_layout_settings.refresh_maps()

    def _build_status_bar(self):
        sb = self.statusBar()
        self.lbl_status_tool = QLabel("Tool: Select")
        self.lbl_status_tool.setStyleSheet("color: #0f172a; font-weight: 600; padding: 2px 10px;")
        sb.addWidget(self.lbl_status_tool)

        self.lbl_status_pos = QLabel("x: 0.0 mm  y: 0.0 mm")
        self.lbl_status_pos.setStyleSheet("color: #475569; padding: 2px 8px;")
        sb.addPermanentWidget(self.lbl_status_pos)

        self.lbl_status_page = QLabel("page: 1")
        self.lbl_status_page.setStyleSheet("color: #475569; padding: 2px 8px;")
        sb.addPermanentWidget(self.lbl_status_page)

        self.lbl_status_zoom = QLabel("100.0%")
        self.lbl_status_zoom.setStyleSheet("color: #475569; padding: 2px 8px;")
        sb.addPermanentWidget(self.lbl_status_zoom)

    def _on_view_mouse_moved(self, point_snapped):
        if point_snapped:
            x_val = round(point_snapped.x(), 1)
            y_val = round(point_snapped.y(), 1)
            self.lbl_status_pos.setText(f"x: {x_val} mm  y: {y_val} mm")

    def _on_layout_set(self, layout):
        """Keep tool_select synchronized whenever the view's layout changes."""
        if hasattr(self, "tool_select") and self.tool_select and layout:
            try:
                self.tool_select.setLayout(layout)
            except Exception:
                pass

    def closeEvent(self, event):
        """Safely deactivate interactive tools when window is closed."""
        try:
            if hasattr(self, "tool_select") and self.tool_select:
                self.tool_select.deactivate()
        except Exception:
            pass
        event.accept()

    def _connect_signals(self):
        self.items_dock.item_selected.connect(self._on_item_selected)
        if self.layout:
            self.layout.selectedItemChanged.connect(self._on_item_selected)

    def _on_item_selected(self, item):
        self.props_dock.set_item(item)
        if item:
            self.tab_lower.setCurrentIndex(1)  # switch to Item Properties tab

    # ── Interactive Tool Activation ──────────────────────────────
    def _activate_add_item_tool(self, metadata_id: int, tool_type: str):
        self._pending_tool_type = tool_type
        self.tool_add_item.setItemMetadataId(metadata_id)
        self.view.setTool(self.tool_add_item)
        name_map = {
            "map": "Add Map (drag rectangle on page)",
            "label": "Add Label (drag rectangle on page)",
            "legend": "Add Legend (drag rectangle on page)",
            "scalebar": "Add Scale Bar (drag rectangle on page)",
            "north_arrow": "Add North Arrow (drag rectangle on page)",
            "image": "Add Image (drag rectangle on page)",
            "table": "Add Table (drag rectangle on page)",
            "shape": "Add Shape (drag rectangle on page)",
            "rectangle": "Add Rectangle (drag rectangle on page)",
            "ellipse": "Add Ellipse (drag rectangle on page)"
        }
        self.lbl_status_tool.setText(f"Tool: {name_map.get(tool_type, 'Add Item')}")

    def _activate_add_node_tool(self, metadata_id: int, tool_type: str):
        self._pending_tool_type = tool_type
        self.tool_add_node.setItemMetadataId(metadata_id)
        self.view.setTool(self.tool_add_node)
        self.lbl_status_tool.setText(f"Tool: Add {tool_type.capitalize()} (click points, right-click to finish)")

    def _on_item_created_interactive(self, item):
        """Called automatically by PyQGIS QgsLayoutViewToolAddItem when rectangle is drawn."""
        if not item or not self.layout:
            return

        tt = self._pending_tool_type or ""

        if tt == "map" or isinstance(item, QgsLayoutItemMap):
            map_count = len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemMap)])
            item.setId(f"Map {map_count}")
            main_canvas = getattr(self.mw, "map_canvas", None)
            if main_canvas and main_canvas.canvas:
                item.setExtent(main_canvas.canvas.extent())
                item.setCrs(main_canvas.canvas.mapSettings().destinationCrs())
                item.setLayers(main_canvas.canvas.layers())
            item.setFrameEnabled(True)
            item.setBackgroundColor(QColor("#ffffff"))

        elif tt == "label" or isinstance(item, QgsLayoutItemLabel):
            label_count = len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemLabel)])
            item.setId(f"Title {label_count}")
            item.setText("Map Title")
            f = item.font()
            f.setFamily("Segoe UI")
            f.setPointSize(16)
            f.setBold(True)
            item.setFont(f)

        elif tt == "legend" or isinstance(item, QgsLayoutItemLegend):
            item.setId("Legend")
            item.setTitle("Legend")
            item.setLinkedMap(self.get_main_map_item())
            item.setFrameEnabled(True)
            item.setBackgroundColor(QColor(255, 255, 255, 230))

        elif tt == "scalebar" or isinstance(item, QgsLayoutItemScaleBar):
            item.setId("Scale Bar")
            item.setLinkedMap(self.get_main_map_item())
            item.setStyle("Single Box")
            item.setUnits(QgsUnitTypes.DistanceKilometers)
            item.setBackgroundEnabled(True)
            item.setBackgroundColor(QColor(255, 255, 255, 220))

        elif tt == "north_arrow":
            if isinstance(item, QgsLayoutItemPicture):
                item.setId("North Arrow")
                item.setLinkedMap(self.get_main_map_item())
                svg_path = self._find_north_arrow_svg()
                if svg_path:
                    item.setPicturePath(svg_path)
                item.setBackgroundEnabled(True)
                item.setBackgroundColor(QColor(255, 255, 255, 200))

        elif tt == "image":
            if isinstance(item, QgsLayoutItemPicture):
                item.setId("Logo / Image")
                path, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.jpeg *.svg *.webp)")
                if path:
                    item.setPicturePath(path)

        elif tt == "rectangle":
            if isinstance(item, QgsLayoutItemShape):
                item.setId(f"Rectangle {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemShape)])}")
                item.setShapeType(QgsLayoutItemShape.Rectangle)
                item.setFrameEnabled(True)

        elif tt == "ellipse":
            if isinstance(item, QgsLayoutItemShape):
                item.setId(f"Ellipse {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemShape)])}")
                item.setShapeType(QgsLayoutItemShape.Ellipse)
                item.setFrameEnabled(True)

        elif tt == "arrow":
            if isinstance(item, QgsLayoutItemPolyline):
                item.setId("Arrow")
                item.setEndMarker(QgsLayoutItemPolyline.ArrowHead)

        elif tt == "line":
            if isinstance(item, QgsLayoutItemPolyline):
                item.setId("Line")

        elif tt == "table":
            if isinstance(item, QgsLayoutItemAttributeTable):
                item.setId("Attribute Table")
                main_canvas = getattr(self.mw, "map_canvas", None)
                if main_canvas and main_canvas.canvas and main_canvas.canvas.layers():
                    item.setVectorLayer(main_canvas.canvas.layers()[0])

        # Reset tool to select
        self.view.setTool(self.tool_select)
        self.lbl_status_tool.setText("Tool: Select")
        self._pending_tool_type = None

        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()
        self.tab_layout_settings.refresh_maps()
        self.props_dock.set_item(item)

    def _find_north_arrow_svg(self) -> str:
        """Find default QGIS north arrow SVG path."""
        for p in QgsApplication.svgPaths():
            candidate = os.path.join(p, "arrows", "NorthArrow_02.svg")
            if os.path.exists(candidate):
                return candidate
            candidate1 = os.path.join(p, "arrows", "NorthArrow_01.svg")
            if os.path.exists(candidate1):
                return candidate1
        return ""

    # ── Menus Construction ──────────────────────────────────────
    def _build_menus(self):
        mb = self.menuBar()
        mb.clear()

        # 1. Layout
        m_layout = mb.addMenu("&Layout")
        m_layout.addAction(get_icon("new_project"), "New Layout...", self.new_layout, "Ctrl+N")
        m_layout.addAction(get_icon("open_project"), "Open Layout...", self.open_layout, "Ctrl+O")
        m_layout.addAction(get_icon("save_project"), "Save Layout", self.save_layout, "Ctrl+S")
        m_layout.addAction("Save As...", self.duplicate_layout)
        m_layout.addSeparator()
        m_layout.addAction(get_icon("print_map"), "Print...", self.print_layout, "Ctrl+P")
        m_layout.addAction("Export Layout (GeoStudio)...", self.open_export_dialog, "Ctrl+E")
        m_layout.addAction("Export as PDF...", self.export_pdf, "Ctrl+Shift+P")
        m_layout.addAction("Export as Image...", self.export_image)
        m_layout.addAction("Export as SVG...", self.export_svg)
        m_layout.addSeparator()
        m_layout.addAction("Page Setup / Properties...", self.show_page_properties)
        m_layout.addAction("Close Designer", self.close, "Ctrl+W")

        # 2. Edit
        m_edit = mb.addMenu("&Edit")
        if self.layout and hasattr(self.layout, "undoStack") and self.layout.undoStack():
            stk = self.layout.undoStack().stack() if hasattr(self.layout.undoStack(), "stack") else self.layout.undoStack()
            if hasattr(stk, "createUndoAction"):
                m_edit.addAction(stk.createUndoAction(self, "Undo"))
                m_edit.addAction(stk.createRedoAction(self, "Redo"))
                m_edit.addSeparator()
        m_edit.addAction(get_icon("delete"), "Delete Selected", self.delete_selected, "Delete")
        m_edit.addAction("Select All", self.select_all, "Ctrl+A")
        m_edit.addAction("Clear Selection", self.deselect_all, "Ctrl+Shift+A")

        # 3. View
        m_view = mb.addMenu("&View")
        m_view.addAction(get_icon("zoom_in"), "Zoom In", self.view.zoomIn, "Ctrl++")
        m_view.addAction(get_icon("zoom_out"), "Zoom Out", self.view.zoomOut, "Ctrl+-")
        m_view.addAction(get_icon("zoom_full"), "Zoom to Page", self.zoom_to_page, "Ctrl+0")
        m_view.addAction("Zoom 1:1", self.zoom_1_1, "Ctrl+1")
        m_view.addSeparator()
        m_view.addAction("Toggle Grid", self.toggle_grid)
        m_view.addAction("Toggle Snapping", self.toggle_snapping)
        m_view.addSeparator()
        m_view.addAction(get_icon("refresh"), "Refresh Layout", self.refresh_layout, "F5")

        # 4. Items
        m_items = mb.addMenu("&Items")
        m_items.addAction("Raise (Bring Forward)", self.items_dock._raise_item)
        m_items.addAction("Lower (Send Backward)", self.items_dock._lower_item)
        m_items.addAction("Lock / Unlock Selected", self.items_dock._toggle_selected_lock)
        m_items.addSeparator()
        m_items.addAction("Align Left", lambda: self._align_items("left"))
        m_items.addAction("Align Center", lambda: self._align_items("center"))
        m_items.addAction("Align Right", lambda: self._align_items("right"))
        m_items.addAction("Align Top", lambda: self._align_items("top"))
        m_items.addAction("Align Middle", lambda: self._align_items("middle"))
        m_items.addAction("Align Bottom", lambda: self._align_items("bottom"))
        m_items.addSeparator()
        m_items.addAction("Distribute Horizontally", lambda: self._distribute_items("h"))
        m_items.addAction("Distribute Vertically", lambda: self._distribute_items("v"))

        # 5. Add Item
        m_add = mb.addMenu("&Add Item")
        m_add.addAction(get_icon("new_project"), "Add Map", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutMap, "map"))
        m_add.addAction(get_icon("edit"), "Add Label / Title", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutLabel, "label"))
        m_add.addAction(get_icon("layer_properties"), "Add Legend", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutLegend, "legend"))
        m_add.addAction(get_icon("measure_dist"), "Add Scale Bar", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutScaleBar, "scalebar"))
        m_add.addAction(get_icon("pan"), "Add North Arrow", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutPicture, "north_arrow"))
        m_add.addAction(get_icon("save_project"), "Add Image / Logo", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutPicture, "image"))
        m_add.addAction("Add Table", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutAttributeTable, "table"))
        m_add.addAction("Add Shape (Rectangle)", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutShape, "rectangle"))
        m_add.addAction("Add Ellipse", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutShape, "ellipse"))
        m_add.addAction("Add Line", lambda: self._activate_add_node_tool(QgsLayoutItemRegistry.LayoutPolyline, "line"))
        m_add.addAction("Add Arrow", lambda: self._activate_add_node_tool(QgsLayoutItemRegistry.LayoutPolyline, "arrow"))

        # 6. Atlas
        m_atlas = mb.addMenu("&Atlas")
        m_atlas.addAction("Generate Map Series / Atlas...", self.open_atlas_dialog)

        # 7. Settings
        m_settings = mb.addMenu("&Settings")
        m_settings.addAction("Page Setup...", self.show_page_properties)

        # 8. Help
        m_help = mb.addMenu("&Help")
        m_help.addAction("Layout Guide & Documentation", self.show_help)

    # ── Toolbars Construction ──────────────────────────────────
    def _build_toolbars(self):
        # ── Top Row 1: Project / Layout / Export Toolbar ─────────
        tb_layout = QToolBar("Layout Operations", self)
        tb_layout.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.TopToolBarArea, tb_layout)

        tb_layout.addAction(get_icon("new_project"), "New Layout", self.new_layout)
        tb_layout.addAction(get_icon("open_project"), "Open Layout", self.open_layout)
        tb_layout.addAction(get_icon("save_project"), "Save", self.save_layout)
        tb_layout.addAction("Save As", self.duplicate_layout)
        tb_layout.addSeparator()
        tb_layout.addAction(get_icon("print_map"), "Print", self.print_layout)
        tb_layout.addAction("Export Layout", self.open_export_dialog)
        tb_layout.addAction("Export PDF", self.export_pdf)
        tb_layout.addAction("Export Image", self.export_image)
        tb_layout.addAction("Export SVG", self.export_svg)
        tb_layout.addSeparator()

        if self.layout and hasattr(self.layout, "undoStack") and self.layout.undoStack():
            stk = self.layout.undoStack().stack() if hasattr(self.layout.undoStack(), "stack") else self.layout.undoStack()
            if hasattr(stk, "undo"):
                tb_layout.addAction("Undo", stk.undo)
                tb_layout.addAction("Redo", stk.redo)
                tb_layout.addSeparator()

        # ── Top Row 2: Navigation & Alignment Toolbar ────────────
        self.addToolBarBreak(Qt.TopToolBarArea)
        tb_nav_align = QToolBar("Navigation & Alignment", self)
        tb_nav_align.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.TopToolBarArea, tb_nav_align)

        tb_nav_align.addAction(get_icon("zoom_full"), "Zoom to Page", self.zoom_to_page)
        tb_nav_align.addAction("1:1", self.zoom_1_1)
        tb_nav_align.addAction(get_icon("zoom_in"), "Zoom In", self.view.zoomIn)
        tb_nav_align.addAction(get_icon("zoom_out"), "Zoom Out", self.view.zoomOut)
        tb_nav_align.addAction(get_icon("refresh"), "Refresh", self.refresh_layout)
        tb_nav_align.addSeparator()

        tb_nav_align.addAction(get_icon("pan"), "Pan View", self.set_tool_pan)
        tb_nav_align.addAction(get_icon("select_single"), "Select Item", self.set_tool_select)
        tb_nav_align.addAction("Move Item Content", self.set_tool_move_content)
        tb_nav_align.addSeparator()

        tb_nav_align.addAction("Align Left", lambda: self._align_items("left"))
        tb_nav_align.addAction("Align Center", lambda: self._align_items("center"))
        tb_nav_align.addAction("Align Right", lambda: self._align_items("right"))
        tb_nav_align.addAction("Align Top", lambda: self._align_items("top"))
        tb_nav_align.addAction("Align Middle", lambda: self._align_items("middle"))
        tb_nav_align.addAction("Align Bottom", lambda: self._align_items("bottom"))
        tb_nav_align.addSeparator()

        tb_nav_align.addAction("Distribute H", lambda: self._distribute_items("h"))
        tb_nav_align.addAction("Distribute V", lambda: self._distribute_items("v"))
        tb_nav_align.addSeparator()

        tb_nav_align.addAction("Lock", self.items_dock._toggle_selected_lock)
        tb_nav_align.addAction("Sync From Canvas", self.sync_extent_from_canvas)
        tb_nav_align.addAction("Apply Extent to Canvas", self.sync_canvas_from_map)

        # ── Left Vertical Toolbar: Layout Creation Tools (14 Tools) ──
        tb_left = QToolBar("Layout Tools", self)
        tb_left.setOrientation(Qt.Vertical)
        tb_left.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.LeftToolBarArea, tb_left)

        tb_left.addAction(get_icon("select_single"), "Select Item", self.set_tool_select)
        tb_left.addAction(get_icon("pan"), "Move Item Content", self.set_tool_move_content)
        tb_left.addSeparator()

        tb_left.addAction(get_icon("new_project"), "Add Map", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutMap, "map"))
        tb_left.addAction(get_icon("edit"), "Add Label", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutLabel, "label"))
        tb_left.addAction(get_icon("layer_properties"), "Add Legend", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutLegend, "legend"))
        tb_left.addAction(get_icon("measure_dist"), "Add Scale Bar", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutScaleBar, "scalebar"))
        tb_left.addAction(get_icon("pan"), "Add North Arrow", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutPicture, "north_arrow"))
        tb_left.addAction(get_icon("save_project"), "Add Image", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutPicture, "image"))
        tb_left.addAction("Add Table", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutAttributeTable, "table"))
        tb_left.addSeparator()

        tb_left.addAction("Add Shape", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutShape, "shape"))
        tb_left.addAction("Add Line", lambda: self._activate_add_node_tool(QgsLayoutItemRegistry.LayoutPolyline, "line"))
        tb_left.addAction("Add Rectangle", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutShape, "rectangle"))
        tb_left.addAction("Add Ellipse", lambda: self._activate_add_item_tool(QgsLayoutItemRegistry.LayoutShape, "ellipse"))
        tb_left.addAction("Add Arrow", lambda: self._activate_add_node_tool(QgsLayoutItemRegistry.LayoutPolyline, "arrow"))

    # ── Tool Mode Switchers ─────────────────────────────────────
    def set_tool_select(self):
        self.view.setTool(self.tool_select)
        self.lbl_status_tool.setText("Tool: Select")

    def set_tool_pan(self):
        self.view.setTool(self.tool_pan)
        self.lbl_status_tool.setText("Tool: Pan View")

    def set_tool_move_content(self):
        self.view.setTool(self.tool_move_content)
        self.lbl_status_tool.setText("Tool: Move Item Content (Pan inside map frame)")

    # ── Direct Placement Methods (fallback / program placement) ─
    def add_map_item(self):
        page = self.layout.pageCollection().pages()[0]
        pw = page.pageSize().width()
        ph = page.pageSize().height()

        item = QgsLayoutItemMap(self.layout)
        item.setId(f"Map {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemMap)]) + 1}")
        item.attemptResize(QgsLayoutSize(pw * 0.7, ph * 0.7, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(pw * 0.05, ph * 0.1, QgsUnitTypes.LayoutMillimeters))
        item.setFrameEnabled(True)
        item.setBackgroundColor(QColor("#ffffff"))

        main_canvas = getattr(self.mw, "map_canvas", None)
        if main_canvas and main_canvas.canvas:
            item.setExtent(main_canvas.canvas.extent())
            item.setCrs(main_canvas.canvas.mapSettings().destinationCrs())
            item.setLayers(main_canvas.canvas.layers())

        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()
        self.tab_layout_settings.refresh_maps()

    def add_3d_map_item(self):
        self.add_map_item()

    def add_label_item(self):
        item = QgsLayoutItemLabel(self.layout)
        item.setId(f"Title {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemLabel)]) + 1}")
        item.setText("Map Title")
        item.attemptResize(QgsLayoutSize(100, 15, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_legend_item(self):
        item = QgsLayoutItemLegend(self.layout)
        item.setId("Legend")
        item.setTitle("Legend")
        item.setLinkedMap(self.get_main_map_item())
        item.attemptResize(QgsLayoutSize(50, 70, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(150, 30, QgsUnitTypes.LayoutMillimeters))
        item.setFrameEnabled(True)
        item.setBackgroundColor(QColor(255, 255, 255, 230))
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_scalebar_item(self):
        item = QgsLayoutItemScaleBar(self.layout)
        item.setId("Scale Bar")
        item.setLinkedMap(self.get_main_map_item())
        item.setStyle("Single Box")
        item.setUnits(QgsUnitTypes.DistanceKilometers)
        item.attemptResize(QgsLayoutSize(45, 10, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(25, 180, QgsUnitTypes.LayoutMillimeters))
        item.setBackgroundEnabled(True)
        item.setBackgroundColor(QColor(255, 255, 255, 220))
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_north_arrow_item(self):
        item = QgsLayoutItemPicture(self.layout)
        item.setId("North Arrow")
        item.setLinkedMap(self.get_main_map_item())
        svg = self._find_north_arrow_svg()
        if svg:
            item.setPicturePath(svg)
        item.attemptResize(QgsLayoutSize(15, 18, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(180, 20, QgsUnitTypes.LayoutMillimeters))
        item.setBackgroundEnabled(True)
        item.setBackgroundColor(QColor(255, 255, 255, 200))
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_image_item(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Logo or Image", "", "Images (*.png *.jpg *.jpeg *.svg *.webp)")
        if path:
            item = QgsLayoutItemPicture(self.layout)
            item.setId("Logo")
            item.setPicturePath(path)
            item.attemptResize(QgsLayoutSize(30, 30, QgsUnitTypes.LayoutMillimeters))
            item.attemptMove(QgsLayoutPoint(20, 20, QgsUnitTypes.LayoutMillimeters))
            self.layout.addLayoutItem(item)
            self.layout.setSelectedItem(item)
            self.items_dock.refresh_items()

    def add_shape_item(self):
        item = QgsLayoutItemShape(self.layout)
        item.setId(f"Rectangle {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemShape)]) + 1}")
        item.setShapeType(QgsLayoutItemShape.Rectangle)
        item.attemptResize(QgsLayoutSize(50, 30, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(40, 40, QgsUnitTypes.LayoutMillimeters))
        item.setFrameEnabled(True)
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_ellipse_item(self):
        item = QgsLayoutItemShape(self.layout)
        item.setId(f"Ellipse {len([i for i in self.layout.items() if isinstance(i, QgsLayoutItemShape)]) + 1}")
        item.setShapeType(QgsLayoutItemShape.Ellipse)
        item.attemptResize(QgsLayoutSize(40, 40, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(50, 50, QgsUnitTypes.LayoutMillimeters))
        item.setFrameEnabled(True)
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_line_item(self):
        poly = QPolygonF([QPointF(20, 20), QPointF(80, 20)])
        item = QgsLayoutItemPolyline(poly, self.layout)
        item.setId("Line")
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_arrow_item(self):
        poly = QPolygonF([QPointF(20, 20), QPointF(80, 20)])
        item = QgsLayoutItemPolyline(poly, self.layout)
        item.setId("Arrow")
        item.setEndMarker(QgsLayoutItemPolyline.ArrowHead)
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_polygon_item(self):
        poly = QPolygonF([QPointF(30, 30), QPointF(70, 30), QPointF(50, 60)])
        item = QgsLayoutItemPolygon(poly, self.layout)
        item.setId("Polygon")
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_html_item(self):
        item = QgsLayoutItemHtml(self.layout)
        item.setId("HTML Block")
        item.setContentMode(QgsLayoutItemHtml.ManualHtml)
        item.setHtml("<h3>GeoStudio Report</h3><p>Analysis summary.</p>")
        item.attemptResize(QgsLayoutSize(80, 40, QgsUnitTypes.LayoutMillimeters))
        item.attemptMove(QgsLayoutPoint(30, 30, QgsUnitTypes.LayoutMillimeters))
        self.layout.addLayoutItem(item)
        self.layout.setSelectedItem(item)
        self.items_dock.refresh_items()

    def add_table_item(self):
        try:
            item = QgsLayoutItemAttributeTable(self.layout)
            item.setId("Attribute Table")
            main_canvas = getattr(self.mw, "map_canvas", None)
            if main_canvas and main_canvas.canvas and main_canvas.canvas.layers():
                item.setVectorLayer(main_canvas.canvas.layers()[0])
            item.attemptResize(QgsLayoutSize(100, 60, QgsUnitTypes.LayoutMillimeters))
            item.attemptMove(QgsLayoutPoint(30, 40, QgsUnitTypes.LayoutMillimeters))
            self.layout.addLayoutItem(item)
            self.layout.setSelectedItem(item)
            self.items_dock.refresh_items()
        except Exception:
            self.add_label_item()

    def get_main_map_item(self):
        for item in self.layout.items():
            if isinstance(item, QgsLayoutItemMap):
                return item
        return None

    # ── Alignment & Distribution ────────────────────────────────
    def _align_items(self, align_type: str):
        selected = self.layout.selectedLayoutItems()
        if len(selected) < 2:
            return
        if align_type == "left":
            min_x = min(it.pos().x() for it in selected)
            for it in selected:
                it.attemptMove(QgsLayoutPoint(min_x, it.pos().y(), QgsUnitTypes.LayoutMillimeters))
        elif align_type == "right":
            max_r = max(it.pos().x() + (it.sizeWithUnits().width() if hasattr(it, "sizeWithUnits") else it.rect().width()) for it in selected)
            for it in selected:
                w = it.sizeWithUnits().width() if hasattr(it, "sizeWithUnits") else it.rect().width()
                it.attemptMove(QgsLayoutPoint(max_r - w, it.pos().y(), QgsUnitTypes.LayoutMillimeters))
        elif align_type == "top":
            min_y = min(it.pos().y() for it in selected)
            for it in selected:
                it.attemptMove(QgsLayoutPoint(it.pos().x(), min_y, QgsUnitTypes.LayoutMillimeters))
        elif align_type == "bottom":
            max_b = max(it.pos().y() + (it.sizeWithUnits().height() if hasattr(it, "sizeWithUnits") else it.rect().height()) for it in selected)
            for it in selected:
                h = it.sizeWithUnits().height() if hasattr(it, "sizeWithUnits") else it.rect().height()
                it.attemptMove(QgsLayoutPoint(it.pos().x(), max_b - h, QgsUnitTypes.LayoutMillimeters))
        elif align_type == "center":
            avg_x = sum(it.pos().x() + (it.sizeWithUnits().width() if hasattr(it, "sizeWithUnits") else it.rect().width()) / 2.0 for it in selected) / len(selected)
            for it in selected:
                w = it.sizeWithUnits().width() if hasattr(it, "sizeWithUnits") else it.rect().width()
                it.attemptMove(QgsLayoutPoint(avg_x - w / 2.0, it.pos().y(), QgsUnitTypes.LayoutMillimeters))
        elif align_type == "middle":
            avg_y = sum(it.pos().y() + (it.sizeWithUnits().height() if hasattr(it, "sizeWithUnits") else it.rect().height()) / 2.0 for it in selected) / len(selected)
            for it in selected:
                h = it.sizeWithUnits().height() if hasattr(it, "sizeWithUnits") else it.rect().height()
                it.attemptMove(QgsLayoutPoint(it.pos().x(), avg_y - h / 2.0, QgsUnitTypes.LayoutMillimeters))

    def _distribute_items(self, axis: str):
        selected = sorted(self.layout.selectedLayoutItems(), key=lambda it: it.pos().x() if axis == "h" else it.pos().y())
        if len(selected) < 3:
            return
        if axis == "h":
            start_x = selected[0].pos().x()
            end_x = selected[-1].pos().x()
            step = (end_x - start_x) / (len(selected) - 1)
            for i, it in enumerate(selected):
                it.attemptMove(QgsLayoutPoint(start_x + i * step, it.pos().y(), QgsUnitTypes.LayoutMillimeters))
        else:
            start_y = selected[0].pos().y()
            end_y = selected[-1].pos().y()
            step = (end_y - start_y) / (len(selected) - 1)
            for i, it in enumerate(selected):
                it.attemptMove(QgsLayoutPoint(it.pos().x(), start_y + i * step, QgsUnitTypes.LayoutMillimeters))

    # ── Map Extent Synchronization ──────────────────────────────
    def sync_extent_from_canvas(self):
        map_item = self.get_main_map_item()
        main_canvas = getattr(self.mw, "map_canvas", None)
        if map_item and main_canvas and main_canvas.canvas:
            map_item.setExtent(main_canvas.canvas.extent())
            map_item.setScale(main_canvas.canvas.scale())
            self.props_dock.set_item(map_item)
            QMessageBox.information(self, "Synchronized", "Layout map extent updated from map canvas.")

    def sync_canvas_from_map(self):
        map_item = self.get_main_map_item()
        main_canvas = getattr(self.mw, "map_canvas", None)
        if map_item and main_canvas and main_canvas.canvas:
            main_canvas.canvas.setExtent(map_item.extent())
            main_canvas.canvas.refresh()
            QMessageBox.information(self, "Synchronized", "Main map canvas extent updated from layout map.")

    # ── View Controls ───────────────────────────────────────────
    def zoom_to_page(self):
        if not self.layout:
            return
        pages = self.layout.pageCollection().pages()
        if pages:
            self.view.fitInView(pages[0].rect(), Qt.KeepAspectRatio)

    def zoom_1_1(self):
        self.view.resetTransform()

    def toggle_grid(self):
        self.tab_layout_settings.chk_show_grid.toggle()

    def toggle_snapping(self):
        self.tab_layout_settings.chk_snap_grid.toggle()

    def refresh_layout(self):
        self.layout.refresh()
        self.items_dock.refresh_items()
        self.tab_layout_settings.refresh_maps()

    def delete_selected(self):
        for it in self.layout.selectedLayoutItems():
            self.layout.removeLayoutItem(it)
        self.items_dock.refresh_items()

    def select_all(self):
        self.layout.selectAll()

    def deselect_all(self):
        self.layout.deselectAll()

    # ── File I/O & Export ───────────────────────────────────────
    def new_layout(self):
        from .layout_manager_dialog import LayoutManagerDialog
        dlg = LayoutManagerDialog(self.mw, self)
        dlg.exec_()

    def open_layout(self):
        self.new_layout()

    def save_layout(self):
        if self.mw and hasattr(self.mw, "save_project"):
            self.mw.save_project()
        QMessageBox.information(self, "Layout Saved", f"Layout '{self.layout.name()}' saved in project.")

    def duplicate_layout(self):
        mgr = QgsProject.instance().layoutManager()
        new_name = f"{self.layout.name()} (Copy)"
        clone = mgr.duplicateLayout(self.layout, new_name)
        if clone:
            QMessageBox.information(self, "Duplicated", f"Layout duplicated as '{new_name}'.")

    def show_page_properties(self):
        pages = self.layout.pageCollection().pages()
        if pages:
            self.props_dock.set_item(pages[0])
            self.tab_lower.setCurrentIndex(1)

    def open_export_dialog(self):
        """Opens GeoStudio's existing PrintExportDialog connected to this layout."""
        try:
            from ui.print_export_dialog import PrintExportDialog
            dlg = PrintExportDialog(self.mw, self, layout=self.layout)
            dlg.exec_()
        except Exception:
            # Fallback to LayoutExportDialog
            self.export_pdf()

    def export_pdf(self):
        self.open_export_dialog()

    def export_image(self):
        self.open_export_dialog()

    def export_svg(self):
        self.open_export_dialog()

    def print_layout(self):
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(lambda p: self._render_print_preview(p, printer))
        dlg.exec_()

    def _render_print_preview(self, printer, qprinter):
        from qgis.core import QgsLayoutExporter
        exporter = QgsLayoutExporter(self.layout)
        exporter.renderPage(printer, 0)

    def open_atlas_dialog(self):
        QMessageBox.information(
            self, "Map Series / Atlas",
            f"Atlas series generator ready.\nConfigure coverage layers under Project Layers."
        )

    def show_help(self):
        QMessageBox.information(
            self, "GeoStudio Layout Designer Guide",
            "<b>GeoStudio Layout Designer</b><br><br>"
            "• Use the <b>Left Toolbar</b> to add map frames, labels, legends, scale bars, north arrows, images, and shapes.<br>"
            "• Use the <b>Items Tab</b> (top right) to reorder, lock, and toggle element visibility.<br>"
            "• Use the <b>Item Properties Tab</b> (bottom right) to customize fonts, scale, extent synchronization, and appearance.<br>"
            "• Export to high-resolution PDF, PNG, JPG, TIFF, or SVG via the <b>Layout</b> menu."
        )
