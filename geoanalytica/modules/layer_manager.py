# -*- coding: utf-8 -*-
"""
GeoAnalytica - Layer Manager Module
Load, style, filter, group and inspect layers.
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QComboBox,
    QLineEdit, QGroupBox, QCheckBox, QColorDialog, QMessageBox,
    QDoubleSpinBox, QFormLayout, QSpinBox
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsMapLayer,
    QgsSymbol, QgsRendererRange, QgsGraduatedSymbolRenderer,
    QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer,
    QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsWkbTypes, QgsLayerTreeGroup, QgsLayerTreeLayer
)
import os


STYLE = """
    QGroupBox {
        font-weight: bold; color: #90caf9;
        border: 1px solid #37474f; border-radius: 4px;
        margin-top: 16px; padding-top: 6px;
    }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 4px; }
    QPushButton {
        background: #1565c0; color: white; border: none;
        border-radius: 4px; padding: 5px 10px; font-size: 11px;
    }
    QPushButton:hover { background: #1976d2; }
    QPushButton:pressed { background: #0d47a1; }
    QListWidget { background: #1e272c; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; }
    QListWidget::item:selected { background: #1565c0; color: white; }
    QComboBox { background: #263238; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; padding: 3px; }
    QLineEdit { background: #263238; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; padding: 3px; }
    QLabel { color: #b0bec5; }
    QWidget { background: #263238; }
"""


class LayerManagerWidget(QWidget):
    """Layer Manager: load, remove, zoom, style and filter layers."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setStyleSheet(STYLE)
        self._init_ui()
        self._refresh_layer_list()
        QgsProject.instance().layersAdded.connect(self._refresh_layer_list)
        QgsProject.instance().layersRemoved.connect(self._refresh_layer_list)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- Load Layers ---
        load_box = QGroupBox("Load Layers")
        load_layout = QHBoxLayout()
        btn_vector = QPushButton("📂 Vector")
        btn_vector.setToolTip("Load vector layer (shp, gpkg, geojson, kml...)")
        btn_vector.clicked.connect(self.load_vector)
        btn_raster = QPushButton("🏔 Raster")
        btn_raster.setToolTip("Load raster layer (tif, img, asc...)")
        btn_raster.clicked.connect(self.load_raster)
        btn_wms = QPushButton("🌐 WMS/XYZ")
        btn_wms.setToolTip("Add WMS or XYZ tile layer")
        btn_wms.clicked.connect(self.load_wms)
        load_layout.addWidget(btn_vector)
        load_layout.addWidget(btn_raster)
        load_layout.addWidget(btn_wms)
        load_box.setLayout(load_layout)
        layout.addWidget(load_box)

        # --- Layer List ---
        list_box = QGroupBox("Project Layers")
        list_layout = QVBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Filter layers...")
        self.search_bar.textChanged.connect(self._filter_list)
        list_layout.addWidget(self.search_bar)

        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.SingleSelection)
        self.layer_list.itemSelectionChanged.connect(self._on_layer_selected)
        list_layout.addWidget(self.layer_list)

        btn_row = QHBoxLayout()
        btn_zoom = QPushButton("🔍 Zoom")
        btn_zoom.clicked.connect(self.zoom_to_layer)
        btn_remove = QPushButton("🗑 Remove")
        btn_remove.clicked.connect(self.remove_layer)
        btn_info = QPushButton("ℹ Info")
        btn_info.clicked.connect(self.show_layer_info)
        btn_row.addWidget(btn_zoom)
        btn_row.addWidget(btn_remove)
        btn_row.addWidget(btn_info)
        list_layout.addLayout(btn_row)

        list_box.setLayout(list_layout)
        layout.addWidget(list_box)

        # --- Quick Style ---
        style_box = QGroupBox("Quick Style")
        style_layout = QFormLayout()

        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.0, 1.0)
        self.opacity_spin.setSingleStep(0.05)
        self.opacity_spin.setValue(1.0)
        self.opacity_spin.setDecimals(2)
        self.opacity_spin.valueChanged.connect(self._apply_opacity)
        style_layout.addRow("Opacity:", self.opacity_spin)

        self.color_btn = QPushButton("🎨 Pick Color")
        self.color_btn.clicked.connect(self._pick_color)
        style_layout.addRow("Fill Color:", self.color_btn)

        style_box.setLayout(style_layout)
        layout.addWidget(style_box)

        # --- Attribute Filter ---
        filter_box = QGroupBox("Attribute Filter (SQL)")
        filter_layout = QVBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText('e.g. "population" > 10000')
        btn_apply_filter = QPushButton("Apply Filter")
        btn_apply_filter.clicked.connect(self._apply_filter)
        btn_clear_filter = QPushButton("Clear Filter")
        btn_clear_filter.clicked.connect(self._clear_filter)
        filter_row = QHBoxLayout()
        filter_row.addWidget(btn_apply_filter)
        filter_row.addWidget(btn_clear_filter)
        filter_layout.addWidget(self.filter_edit)
        filter_layout.addLayout(filter_row)
        filter_box.setLayout(filter_layout)
        layout.addWidget(filter_box)

        layout.addStretch()
        self.setLayout(layout)

    # ---- Layer Loading ----

    def load_vector(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Vector Layer", "",
            "Vector Files (*.shp *.gpkg *.geojson *.json *.kml *.gml *.csv *.tab *.gdb);;All Files (*)"
        )
        if path:
            layer_name = os.path.splitext(os.path.basename(path))[0]
            layer = QgsVectorLayer(path, layer_name, "ogr")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.iface.messageBar().pushSuccess("GeoAnalytica", f"Loaded: {layer_name}")
            else:
                QMessageBox.critical(self, "Error", f"Could not load layer:\n{path}")

    def load_raster(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Raster Layer", "",
            "Raster Files (*.tif *.tiff *.img *.asc *.nc *.hdf *.h4 *.h5 *.vrt *.ecw *.jp2);;All Files (*)"
        )
        if path:
            layer_name = os.path.splitext(os.path.basename(path))[0]
            layer = QgsRasterLayer(path, layer_name)
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.iface.messageBar().pushSuccess("GeoAnalytica", f"Loaded: {layer_name}")
            else:
                QMessageBox.critical(self, "Error", f"Could not load raster:\n{path}")

    def load_wms(self):
        """Add an OpenStreetMap XYZ tile layer as a quick example."""
        url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0"
        layer = QgsRasterLayer(url, "OpenStreetMap", "wms")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.iface.messageBar().pushSuccess("GeoAnalytica", "Added OpenStreetMap basemap")
        else:
            QMessageBox.warning(self, "WMS", "Could not load XYZ layer. Check your internet connection.")

    # ---- Layer List ----

    def _refresh_layer_list(self):
        self.layer_list.clear()
        for layer in QgsProject.instance().mapLayers().values():
            icon = "🗂" if layer.type() == QgsMapLayer.VectorLayer else "🏔"
            item = QListWidgetItem(f"{icon}  {layer.name()}")
            item.setData(Qt.UserRole, layer.id())
            self.layer_list.addItem(item)

    def _filter_list(self, text):
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_layer_selected(self):
        layer = self._get_selected_layer()
        if layer:
            self.iface.setActiveLayer(layer)

    def _get_selected_layer(self):
        items = self.layer_list.selectedItems()
        if not items:
            return None
        layer_id = items[0].data(Qt.UserRole)
        return QgsProject.instance().mapLayer(layer_id)

    def zoom_to_layer(self):
        layer = self._get_selected_layer()
        if layer:
            self.iface.zoomToActiveLayer()

    def remove_layer(self):
        layer = self._get_selected_layer()
        if layer:
            reply = QMessageBox.question(
                self, "Remove Layer",
                f"Remove layer '{layer.name()}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                QgsProject.instance().removeMapLayer(layer.id())

    def show_layer_info(self):
        layer = self._get_selected_layer()
        if not layer:
            return
        info = (
            f"Name: {layer.name()}\n"
            f"Type: {'Vector' if layer.type() == QgsMapLayer.VectorLayer else 'Raster'}\n"
            f"CRS: {layer.crs().authid()}\n"
            f"Source: {layer.source()}\n"
        )
        if layer.type() == QgsMapLayer.VectorLayer:
            info += f"Features: {layer.featureCount()}\n"
            info += f"Geometry: {QgsWkbTypes.displayString(layer.wkbType())}\n"
        elif layer.type() == QgsMapLayer.RasterLayer:
            info += f"Bands: {layer.bandCount()}\n"
            info += f"Width x Height: {layer.width()} x {layer.height()}\n"
        QMessageBox.information(self, "Layer Info", info)

    # ---- Style ----

    def _apply_opacity(self, value):
        layer = self._get_selected_layer()
        if layer:
            layer.setOpacity(value)
            self.iface.mapCanvas().refresh()

    def _pick_color(self):
        layer = self._get_selected_layer()
        if not layer or layer.type() != QgsMapLayer.VectorLayer:
            return
        color = QColorDialog.getColor(Qt.green, self, "Select Fill Color")
        if color.isValid():
            renderer = layer.renderer()
            if renderer and renderer.type() == "singleSymbol":
                sym = renderer.symbol()
                if sym:
                    sym.setColor(color)
                    layer.triggerRepaint()
                    self.iface.mapCanvas().refresh()

    # ---- Filter ----

    def _apply_filter(self):
        layer = self._get_selected_layer()
        if not layer or layer.type() != QgsMapLayer.VectorLayer:
            return
        expr = self.filter_edit.text().strip()
        if layer.setSubsetString(expr):
            self.iface.messageBar().pushSuccess("GeoAnalytica", "Filter applied successfully")
        else:
            QMessageBox.warning(self, "Filter Error", "Invalid filter expression. Please check your SQL syntax.")

    def _clear_filter(self):
        layer = self._get_selected_layer()
        if layer and layer.type() == QgsMapLayer.VectorLayer:
            layer.setSubsetString("")
            self.filter_edit.clear()
            self.iface.messageBar().pushInfo("GeoAnalytica", "Filter cleared")
