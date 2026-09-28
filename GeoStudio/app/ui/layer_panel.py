# -*- coding: utf-8 -*-
"""GeoStudio - Layer Panel (left sidebar, like QGIS Layers panel)."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu, QAction, QFileDialog,
    QMessageBox, QLineEdit, QDoubleSpinBox, QDialog,
    QFormLayout, QDialogButtonBox, QColorDialog, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QBrush, QFont


LAYER_STYLE = """
    QWidget { background: #1a2332; }
    QTreeWidget {
        background: #1a2332; color: #cfd8dc;
        border: none; font-size: 12px;
    }
    QTreeWidget::item { padding: 3px 4px; border-radius: 3px; }
    QTreeWidget::item:selected { background: #1565c0; color: white; }
    QTreeWidget::item:hover { background: #263238; }
    QPushButton {
        background: #263238; color: #90caf9; border: 1px solid #37474f;
        border-radius: 3px; padding: 4px 8px; font-size: 11px;
    }
    QPushButton:hover { background: #37474f; }
    QLineEdit { background: #263238; color: #cfd8dc; border: 1px solid #37474f;
                border-radius: 3px; padding: 3px; }
    QLabel { color: #78909c; font-size: 11px; }
"""


class LayerPanelWidget(QWidget):
    """
    Left-side layer panel — shows all project layers with:
    - Visibility toggle (checkbox)
    - Layer icons (vector/raster)
    - Right-click context menu
    - Drag to reorder (future)
    - Layer search
    """

    active_layer_changed = pyqtSignal(object)

    def __init__(self, map_canvas, parent=None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.setStyleSheet(LAYER_STYLE)
        self._init_ui()
        self._connect_project_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QLabel("🗂  LAYERS")
        header.setStyleSheet("color: #90caf9; font-weight: bold; font-size: 12px; padding: 2px 4px;")
        layout.addWidget(header)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search layers...")
        self.search.textChanged.connect(self._filter_layers)
        layout.addWidget(self.search)

        # Layer tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        # Quick-add buttons
        btn_row = QHBoxLayout()
        btn_v = QPushButton("📂 Vector")
        btn_v.clicked.connect(self._quick_add_vector)
        btn_r = QPushButton("🏔 Raster")
        btn_r.clicked.connect(self._quick_add_raster)
        btn_osm = QPushButton("🌐 OSM")
        btn_osm.clicked.connect(self.load_osm_basemap)
        btn_row.addWidget(btn_v)
        btn_row.addWidget(btn_r)
        btn_row.addWidget(btn_osm)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _connect_project_signals(self):
        try:
            from qgis.core import QgsProject
            QgsProject.instance().layersAdded.connect(self.refresh)
            QgsProject.instance().layersRemoved.connect(self.refresh)
        except ImportError:
            pass

    # ──────────────────────────────────────────────────────────
    # Refresh tree from project
    # ──────────────────────────────────────────────────────────
    def refresh(self, *args):
        self.tree.blockSignals(True)
        self.tree.clear()
        try:
            from qgis.core import QgsProject, QgsMapLayer
            layers = list(QgsProject.instance().mapLayers().values())
            for layer in reversed(layers):  # top layer first
                is_vector = layer.type() == QgsMapLayer.VectorLayer
                icon = "🗂" if is_vector else "🏔"
                item = QTreeWidgetItem([f"  {icon}  {layer.name()}"])
                item.setData(0, Qt.UserRole, layer.id())
                item.setCheckState(0, Qt.Checked if layer.isValid() else Qt.Unchecked)
                # Color swatch for vector
                if is_vector:
                    item.setForeground(0, QBrush(QColor("#a5d6a7")))
                else:
                    item.setForeground(0, QBrush(QColor("#ffcc80")))
                self.tree.addTopLevelItem(item)
        except ImportError:
            pass
        self.tree.blockSignals(False)
        self.map_canvas.refresh_layers()

    def _filter_layers(self, text):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setHidden(text.lower() not in item.text(0).lower())

    # ──────────────────────────────────────────────────────────
    # Events
    # ──────────────────────────────────────────────────────────
    def _on_item_clicked(self, item, col):
        layer = self._layer_from_item(item)
        if layer:
            self.active_layer_changed.emit(layer)
            # Zoom to layer on single click (optional — QGIS double-click behavior)

    def _on_item_changed(self, item, col):
        """Toggle layer visibility when checkbox is toggled."""
        layer = self._layer_from_item(item)
        if layer:
            try:
                from qgis.core import QgsProject
                node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
                if node:
                    node.setItemVisibilityChecked(item.checkState(0) == Qt.Checked)
                self.map_canvas.refresh_canvas()
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────
    # Context Menu
    # ──────────────────────────────────────────────────────────
    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        layer = self._layer_from_item(item)
        if not layer:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #263238; color: #cfd8dc; border: 1px solid #37474f; }
            QMenu::item:selected { background: #1565c0; }
        """)

        menu.addAction("🔍 Zoom to Layer",        lambda: self._zoom_to(layer))
        menu.addAction("📊 Open Attribute Table", lambda: self._open_attr_table(layer))
        menu.addAction("ℹ Layer Properties",       lambda: self._show_props(layer))
        menu.addSeparator()
        menu.addAction("🎨 Change Color",          lambda: self._change_color(layer))
        menu.addAction("👁 Toggle Visibility",      lambda: self._toggle_visibility(item, layer))
        menu.addSeparator()
        menu.addAction("📋 Rename Layer",           lambda: self._rename_layer(item, layer))
        menu.addAction("🗑 Remove Layer",            lambda: self._remove_layer(layer))
        menu.addSeparator()
        menu.addAction("💾 Export Layer...",         lambda: self._export_layer(layer))

        menu.exec_(self.tree.mapToGlobal(pos))

    # ──────────────────────────────────────────────────────────
    # Layer Loading
    # ──────────────────────────────────────────────────────────
    def _quick_add_vector(self):
        path, _ = QFileDialog.getOpenFileName(None, "Add Vector Layer", "",
            "Vector (*.shp *.gpkg *.geojson *.json *.kml *.gml *.csv *.tab);;All (*)")
        if path:
            self.load_vector(path)

    def _quick_add_raster(self):
        path, _ = QFileDialog.getOpenFileName(None, "Add Raster Layer", "",
            "Raster (*.tif *.tiff *.img *.asc *.nc *.hdf *.vrt *.jp2);;All (*)")
        if path:
            self.load_raster(path)

    def load_vector(self, path):
        try:
            from qgis.core import QgsVectorLayer, QgsProject
            name = os.path.splitext(os.path.basename(path))[0]
            layer = QgsVectorLayer(path, name, "ogr")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.map_canvas.refresh_layers()
                if self.map_canvas.canvas:
                    self.map_canvas.canvas.setExtent(layer.extent())
                    self.map_canvas.canvas.refresh()
            else:
                QMessageBox.critical(None, "Error", f"Invalid layer: {path}")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def load_raster(self, path):
        try:
            from qgis.core import QgsRasterLayer, QgsProject
            name = os.path.splitext(os.path.basename(path))[0]
            layer = QgsRasterLayer(path, name)
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.map_canvas.refresh_layers()
                if self.map_canvas.canvas:
                    self.map_canvas.canvas.setExtent(layer.extent())
                    self.map_canvas.canvas.refresh()
            else:
                QMessageBox.critical(None, "Error", f"Invalid raster: {path}")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    def load_osm_basemap(self):
        try:
            from qgis.core import QgsRasterLayer, QgsProject
            url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0"
            layer = QgsRasterLayer(url, "OpenStreetMap", "wms")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.map_canvas.refresh_layers()
        except Exception as e:
            QMessageBox.warning(None, "WMS", str(e))

    def load_csv(self, path, x_field="longitude", y_field="latitude"):
        try:
            from qgis.core import QgsVectorLayer, QgsProject
            name = os.path.splitext(os.path.basename(path))[0]
            uri = f"file:///{path}?delimiter=,&xField={x_field}&yField={y_field}&crs=epsg:4326&useHeader=yes"
            layer = QgsVectorLayer(uri, name, "delimitedtext")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.map_canvas.refresh_layers()
            else:
                QMessageBox.critical(None, "CSV Error", "Could not load CSV. Check X/Y column names.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    # ──────────────────────────────────────────────────────────
    # Context Menu Actions
    # ──────────────────────────────────────────────────────────
    def _zoom_to(self, layer):
        if self.map_canvas.canvas:
            self.map_canvas.canvas.setExtent(layer.extent())
            self.map_canvas.canvas.refresh()

    def _open_attr_table(self, layer):
        # Signal to main window to open attr table
        pass  # wired through main window

    def _show_props(self, layer):
        try:
            from qgis.core import QgsMapLayer
            info = (f"Name: {layer.name()}\n"
                    f"CRS: {layer.crs().authid()}\n"
                    f"Source: {layer.source()}\n")
            if layer.type() == QgsMapLayer.VectorLayer:
                info += f"Features: {layer.featureCount()}\n"
            elif layer.type() == QgsMapLayer.RasterLayer:
                info += f"Bands: {layer.bandCount()}\n"
                info += f"Size: {layer.width()} x {layer.height()}\n"
            QMessageBox.information(None, "Layer Properties", info)
        except Exception as e:
            QMessageBox.information(None, "Properties", str(e))

    def _change_color(self, layer):
        try:
            from qgis.core import QgsMapLayer
            if layer.type() != QgsMapLayer.VectorLayer:
                return
            color = QColorDialog.getColor(Qt.green, None, "Select Layer Color")
            if color.isValid():
                renderer = layer.renderer()
                if renderer and renderer.type() == "singleSymbol":
                    renderer.symbol().setColor(color)
                    layer.triggerRepaint()
                    self.map_canvas.refresh_canvas()
        except Exception:
            pass

    def _toggle_visibility(self, item, layer):
        new_state = Qt.Unchecked if item.checkState(0) == Qt.Checked else Qt.Checked
        item.setCheckState(0, new_state)

    def _rename_layer(self, item, layer):
        new_name, ok = QInputDialog.getText(None, "Rename Layer",
            "New layer name:", text=layer.name())
        if ok and new_name:
            layer.setName(new_name)
            self.refresh()

    def _remove_layer(self, layer):
        reply = QMessageBox.question(None, "Remove Layer",
            f"Remove '{layer.name()}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                from qgis.core import QgsProject
                QgsProject.instance().removeMapLayer(layer.id())
            except Exception:
                pass

    def _export_layer(self, layer):
        try:
            from qgis.core import QgsVectorFileWriter, QgsCoordinateTransformContext, QgsMapLayer
            if layer.type() != QgsMapLayer.VectorLayer:
                QMessageBox.information(None, "Export", "Only vector layers can be exported here.")
                return
            path, _ = QFileDialog.getSaveFileName(None, "Export Layer", layer.name(),
                "GeoPackage (*.gpkg);;Shapefile (*.shp);;GeoJSON (*.geojson);;KML (*.kml)")
            if path:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.fileEncoding = "UTF-8"
                QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer, path, QgsCoordinateTransformContext(), options)
                QMessageBox.information(None, "Export", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(None, "Export Error", str(e))

    # ──────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────
    def _layer_from_item(self, item):
        layer_id = item.data(0, Qt.UserRole) if item else None
        if not layer_id:
            return None
        try:
            from qgis.core import QgsProject
            return QgsProject.instance().mapLayer(layer_id)
        except Exception:
            return None

    def get_active_layer(self):
        items = self.tree.selectedItems()
        return self._layer_from_item(items[0]) if items else None

    def remove_active_layer(self):
        layer = self.get_active_layer()
        if layer:
            self._remove_layer(layer)

    def show_layer_properties(self):
        layer = self.get_active_layer()
        if layer:
            self._show_props(layer)
