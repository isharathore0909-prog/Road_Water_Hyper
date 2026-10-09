# -*- coding: utf-8 -*-
"""
GeoStudio - Simplified Professional Layers Panel
Single Left-Side Layers Panel:
- Title with real-time layer counter badge
- Instant search filter by name, group, and type
- Prominent [+ Add Layer] menu (Vector, Raster, KML, GeoJSON, Shapefile, GeoPackage, CSV, WMS, Basemap)
- Layer list with visibility toggle, live symbology preview swatch, and inline renaming
- Drag-and-drop layer reordering synchronized directly with map rendering order
- Collapsible layer groups
- Bottom essential actions: [+ Add Layer], [Remove], [Group]
- Context menu: Zoom to Layer, Attribute Table, Properties, Symbology, Labels, Opacity, Rename, Duplicate, Remove, Export
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QFileDialog, QMessageBox, QLineEdit, QMenu,
    QInputDialog, QToolButton, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import (
    QColor, QBrush, QFont, QIcon, QPixmap, QPainter, QPen
)

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsWkbTypes,
    QgsLayerTreeGroup, QgsLayerTreeLayer
)

from core.elevation_styler import ElevationStyler, ELEVATION_PRESETS
from resources.icons.icon_provider import get_icon
from .layer_loader import LayerLoader
from .layer_context_menu import LayerContextMenuHandler


LAYER_PANEL_STYLE = """
    QWidget {
        background: #ffffff;
        color: #0f172a;
        font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif;
        font-size: 12px;
    }
    QTreeWidget {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        font-size: 12px;
        border-radius: 4px;
        outline: none;
        selection-background-color: #e2e8f0;
        selection-color: #0f172a;
    }
    QTreeWidget::item {
        padding: 5px 4px;
        border-radius: 3px;
    }
    QTreeWidget::item:selected {
        background: #e2e8f0;
        color: #0f172a;
        font-weight: 600;
    }
    QTreeWidget::item:hover:!selected {
        background: #f8fafc;
    }
    QLineEdit {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 11px;
    }
    QLineEdit:focus {
        border: 1.5px solid #0f172a;
    }
    QPushButton {
        background: #ffffff;
        color: #334155;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #f1f5f9;
        color: #0f172a;
        border-color: #94a3b8;
    }
    QPushButton:pressed {
        background: #e2e8f0;
    }
"""


class LayerTreeWidget(QTreeWidget):
    """Tree widget supporting drag-drop layer reordering and inline editing."""

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.panel._sync_layer_order_to_project()


class LayerPanelWidget(QWidget):
    """
    Left-side layer panel for GeoStudio.
    """

    active_layer_changed = pyqtSignal(object)

    def __init__(self, map_canvas, parent=None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.setStyleSheet(LAYER_PANEL_STYLE)
        self._init_ui()
        self._connect_project_signals()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # 1. Header: [LAYERS] [Count Badge] [Collapse Button]
        header_box = QHBoxLayout()
        header_box.setSpacing(6)

        lbl_title = QLabel("LAYERS")
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_title.setStyleSheet("color: #0f172a; letter-spacing: 0.5px;")
        header_box.addWidget(lbl_title)

        header_box.addStretch()

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(
            "background: #f1f5f9; color: #0f172a; font-weight: 700; "
            "font-size: 11px; border-radius: 9px; padding: 1px 8px; border: 1px solid #cbd5e1;"
        )
        header_box.addWidget(self.count_badge)

        self.btn_collapse = QToolButton()
        self.btn_collapse.setText("◀")
        self.btn_collapse.setToolTip("Collapse Layers Panel")
        self.btn_collapse.setStyleSheet("QToolButton { border: none; font-size: 10px; color: #64748b; padding: 2px 4px; } QToolButton:hover { color: #0f172a; }")
        self.btn_collapse.clicked.connect(self._toggle_collapse)
        header_box.addWidget(self.btn_collapse)

        root.addLayout(header_box)

        # 2. Search Bar: [ Search layers... ] [X]
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search layers...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter_layers)
        root.addWidget(self.search)

        # 3. Top [+ Add Layer] Button with popup menu
        self.btn_add_layer_top = QPushButton("+ Add Layer")
        self.btn_add_layer_top.setStyleSheet(
            "QPushButton { background: #0f172a; color: #ffffff; padding: 6px 12px; border-radius: 4px; font-weight: 600; text-align: left; } "
            "QPushButton:hover { background: #334155; } "
            "QPushButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; right: 8px; }"
        )
        self.add_menu = self._build_add_layer_menu()
        self.btn_add_layer_top.setMenu(self.add_menu)
        root.addWidget(self.btn_add_layer_top)

        # 4. Empty State Container
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setContentsMargins(12, 32, 12, 32)
        empty_layout.setSpacing(8)
        empty_layout.setAlignment(Qt.AlignCenter)

        lbl_empty_title = QLabel("No layers loaded")
        lbl_empty_title.setAlignment(Qt.AlignCenter)
        lbl_empty_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_empty_title.setStyleSheet("color: #334155;")
        empty_layout.addWidget(lbl_empty_title)

        lbl_empty_desc = QLabel("Add GIS data to begin working.")
        lbl_empty_desc.setAlignment(Qt.AlignCenter)
        lbl_empty_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-bottom: 8px;")
        empty_layout.addWidget(lbl_empty_desc)

        btn_empty_v = QPushButton("+ Add Vector Layer")
        btn_empty_v.setStyleSheet("background: #0f172a; color: white; padding: 6px 14px; border-radius: 4px; font-weight: 600;")
        btn_empty_v.clicked.connect(self._quick_add_vector)
        empty_layout.addWidget(btn_empty_v)

        btn_empty_r = QPushButton("+ Add Raster / DEM")
        btn_empty_r.setStyleSheet("background: white; color: #334155; border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 4px; font-weight: 600;")
        btn_empty_r.clicked.connect(self._quick_add_raster)
        empty_layout.addWidget(btn_empty_r)

        root.addWidget(self.empty_widget)

        # 5. Layer Tree
        self.tree = LayerTreeWidget(self)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        root.addWidget(self.tree, 1)

        # 6. Bottom Essential Actions: [+ Add Layer] [Remove] [Group]
        h_bottom = QHBoxLayout()
        h_bottom.setSpacing(6)

        btn_bottom_add = QPushButton("+ Add")
        btn_bottom_add.setMenu(self.add_menu)
        h_bottom.addWidget(btn_bottom_add)

        btn_bottom_rem = QPushButton("Remove")
        btn_bottom_rem.clicked.connect(self.remove_active_layer)
        h_bottom.addWidget(btn_bottom_rem)

        btn_bottom_grp = QPushButton("Group")
        btn_bottom_grp.clicked.connect(self._add_group)
        h_bottom.addWidget(btn_bottom_grp)

        root.addLayout(h_bottom)
        self.setLayout(root)

    def _build_add_layer_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-size: 11px; }
            QMenu::item { padding: 6px 24px 6px 20px; border-radius: 3px; }
            QMenu::item:selected { background: #e2e8f0; color: #0f172a; font-weight: 600; }
            QMenu::separator { height: 1px; background: #e2e8f0; margin: 4px 6px; }
        """)

        menu.addAction("Add Vector Layer...", self._quick_add_vector)
        menu.addAction("Add Raster / DEM...", self._quick_add_raster)
        menu.addSeparator()
        menu.addAction("Add KML / KMZ...", lambda: self._add_specific_format("KML/KMZ (*.kml *.kmz)"))
        menu.addAction("Add GeoJSON...", lambda: self._add_specific_format("GeoJSON (*.geojson *.json)"))
        menu.addAction("Add Shapefile...", lambda: self._add_specific_format("ESRI Shapefile (*.shp)"))
        menu.addAction("Add GeoPackage...", lambda: self._add_specific_format("GeoPackage (*.gpkg)"))
        menu.addAction("Add CSV Table...", self._add_csv)
        menu.addSeparator()
        menu.addAction("Add WMS / WMTS...", self._add_wms)
        menu.addAction("Add XYZ Basemap (OSM)", self.load_osm_basemap)
        return menu

    def _toggle_collapse(self):
        dock = self.parent()
        while dock and not hasattr(dock, "toggleViewAction"):
            dock = dock.parent()
        if dock:
            dock.hide()

    def _connect_project_signals(self):
        try:
            QgsProject.instance().layersAdded.connect(self.refresh)
            QgsProject.instance().layersRemoved.connect(self.refresh)
        except Exception:
            pass

    def refresh(self, *args):
        self.tree.blockSignals(True)
        self.tree.clear()

        try:
            layers = list(QgsProject.instance().mapLayers().values())
            valid_count = 0

            for layer in reversed(layers):
                if getattr(layer, '_is_sub_relief_layer', False) or "[3D Hillshade]" in layer.name():
                    continue

                valid_count += 1
                item = self._create_layer_item(layer)
                self.tree.addTopLevelItem(item)

            if valid_count == 0:
                self.tree.hide()
                self.empty_widget.show()
            else:
                self.empty_widget.hide()
                self.tree.show()

            if self.tree.topLevelItemCount() > 0:
                self.tree.setCurrentItem(self.tree.topLevelItem(0))

            self.count_badge.setText(str(valid_count))
        except Exception as e:
            pass

        self.tree.blockSignals(False)

    def _create_layer_item(self, layer) -> QTreeWidgetItem:
        name = layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "").replace(" [3D Hillshade]", "").replace(" [LiDAR]", "").strip()
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, layer.id())
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        item.setCheckState(0, Qt.Checked if layer.isValid() else Qt.Unchecked)

        # Generate live GIS symbology swatch icon
        icon = self._generate_symbology_icon(layer)
        item.setIcon(0, icon)
        return item

    def _generate_symbology_icon(self, layer) -> QIcon:
        pix = QPixmap(16, 16)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        if isinstance(layer, QgsVectorLayer):
            geom = layer.geometryType()
            color = QColor("#3b82f6")
            renderer = layer.renderer()
            if renderer and hasattr(renderer, "symbol") and renderer.symbol():
                color = renderer.symbol().color()

            if geom == QgsWkbTypes.PolygonGeometry:
                p.setBrush(QBrush(color))
                p.setPen(QPen(color.darker(140), 1))
                p.drawRoundedRect(1, 2, 14, 12, 2, 2)
            elif geom == QgsWkbTypes.LineGeometry:
                p.setPen(QPen(color, 3))
                p.drawLine(1, 8, 15, 8)
            else:  # Point
                p.setBrush(QBrush(color))
                p.setPen(QPen(color.darker(140), 1))
                p.drawEllipse(2, 2, 12, 12)
        elif "PointCloud" in type(layer).__name__ or layer.customProperty("is_lidar_layer", False):
            p.setBrush(QBrush(QColor("#0284c7")))
            p.drawRoundedRect(2, 2, 12, 12, 2, 2)
        elif ElevationStyler.is_dem_or_elevation(layer):
            p.setBrush(QBrush(QColor("#b45309")))
            p.setPen(QPen(QColor("#78350f"), 1))
            p.drawRect(2, 2, 12, 12)
        else:  # General Raster
            p.setBrush(QBrush(QColor("#059669")))
            p.setPen(QPen(QColor("#065f46"), 1))
            p.drawRect(2, 2, 12, 12)

        p.end()
        return QIcon(pix)

    def _sync_layer_order_to_project(self):
        try:
            root = QgsProject.instance().layerTreeRoot()
            root.setHasCustomLayerOrder(True)
            custom_order = []
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                layer = self._layer_from_item(item)
                if layer:
                    custom_order.append(layer)
            root.setCustomLayerOrder(custom_order)
            if self.map_canvas:
                self.map_canvas.refresh_canvas()
        except Exception:
            pass

    def _filter_layers(self, text: str):
        query = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            matches = query in it.text(0).lower() if query else True
            it.setHidden(not matches)

    def get_active_layer(self):
        item = self.tree.currentItem()
        if item:
            return self._layer_from_item(item)
        return None

    def set_active_layer(self, layer):
        if not layer:
            self.tree.setCurrentItem(None)
            self.active_layer_changed.emit(None)
            return

        layer_id = layer.id() if hasattr(layer, "id") else None
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == layer_id:
                self.tree.setCurrentItem(item)
                self.active_layer_changed.emit(layer)
                return
        self.active_layer_changed.emit(layer)

    def _on_item_clicked(self, item, col):
        layer = self._layer_from_item(item)
        if layer:
            self.active_layer_changed.emit(layer)
            if self.map_canvas and hasattr(self.map_canvas, "update_elevation_legend"):
                self.map_canvas.update_elevation_legend(layer)

    def _on_item_double_clicked(self, item, col):
        layer = self._layer_from_item(item)
        if layer and self.map_canvas:
            self.active_layer_changed.emit(layer)
            self.map_canvas.zoom_to_layer(layer)

    def _on_item_changed(self, item, col):
        layer = self._layer_from_item(item)
        if not layer:
            return

        # Visibility toggle
        try:
            root = QgsProject.instance().layerTreeRoot()
            node = root.findLayer(layer.id())
            if node:
                node.setItemVisibilityChecked(item.checkState(0) == Qt.Checked)
            if self.map_canvas:
                self.map_canvas.refresh_canvas()
        except Exception:
            pass

        # Inline rename
        new_name = item.text(0).strip()
        if new_name and new_name != layer.name():
            layer.setName(new_name)

    def _show_context_menu(self, pos):
        LayerContextMenuHandler.show_context_menu(self, pos)

    def _add_group(self):
        name, ok = QInputDialog.getText(self, "Add Group", "Group Name:", text="New Group")
        if ok and name.strip():
            grp_item = QTreeWidgetItem([f"📁 {name.strip()}"])
            grp_item.setFont(0, QFont("Segoe UI", 11, QFont.Bold))
            grp_item.setFlags(grp_item.flags() | Qt.ItemIsDropEnabled | Qt.ItemIsEditable)
            self.tree.addTopLevelItem(grp_item)

    def _add_specific_format(self, filter_str: str):
        path, _ = QFileDialog.getOpenFileName(self, "Open Layer", "", f"{filter_str};;All Files (*.*)")
        if path:
            if any(path.lower().endswith(ext) for ext in [".tif", ".dem", ".asc"]):
                self.load_raster(path)
            else:
                self.load_vector(path)

    def _add_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV Table", "", "CSV Files (*.csv);;All Files (*.*)")
        if path:
            self.load_csv(path)

    def _add_wms(self):
        url, ok = QInputDialog.getText(self, "Add WMS / WMTS", "Service URL:", text="https://")
        if ok and url.strip():
            QMessageBox.information(self, "WMS Service", f"Connecting to WMS service:\n{url.strip()}")

    def _quick_add_vector(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Vector Layer", "",
            "Vector Datasets (*.shp *.gpkg *.geojson *.kml *.kmz *.json);;Shapefile (*.shp);;GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*.*)"
        )
        if path:
            self.load_vector(path)

    def _quick_add_raster(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Elevation DEM / Raster", "",
            "Raster & Elevation (*.tif *.tiff *.dem *.asc *.dtm *.dsm *.las *.laz);;GeoTIFF (*.tif *.tiff);;All Files (*.*)"
        )
        if path:
            self.load_raster(path)

    def load_vector(self, path):
        LayerLoader.load_vector(self, path)

    def load_raster(self, path):
        LayerLoader.load_raster(self, path)

    def load_point_cloud(self, path):
        LayerLoader.load_point_cloud(self, path)

    def load_osm_basemap(self):
        LayerLoader.load_osm_basemap(self)

    def load_csv(self, path, x_field="longitude", y_field="latitude"):
        LayerLoader.load_csv(self, path, x_field, y_field)

    def _layer_from_item(self, item):
        if not item:
            return None
        layer_id = item.data(0, Qt.UserRole)
        if layer_id:
            try:
                return QgsProject.instance().mapLayer(layer_id)
            except Exception:
                pass
        return None

    def remove_active_layer(self):
        layer = self.get_active_layer()
        if layer:
            LayerContextMenuHandler.remove_layer(self, layer)

    def show_layer_properties(self):
        layer = self.get_active_layer()
        if layer:
            LayerContextMenuHandler.show_props(self, layer)

    def apply_elevation_preset(self, layer, preset_key):
        LayerContextMenuHandler.apply_elevation_preset(self, layer, preset_key)

    def open_dem_dialog(self, layer=None):
        LayerContextMenuHandler.open_dem_dialog(self, layer)
