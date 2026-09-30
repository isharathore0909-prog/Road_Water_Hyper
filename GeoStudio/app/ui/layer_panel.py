# -*- coding: utf-8 -*-
"""GeoStudio - Layer Panel (left sidebar, like QGIS / Global Mapper Layers panel)."""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu, QAction, QFileDialog,
    QMessageBox, QLineEdit, QDoubleSpinBox, QDialog,
    QFormLayout, QDialogButtonBox, QColorDialog, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QBrush, QFont

from core.elevation_styler import ElevationStyler, ELEVATION_PRESETS
from core.raster_optimizer import get_raster_optimizer


LAYER_STYLE = """
    QWidget { background: #ffffff; color: #0f172a; font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif; font-size: 12px; }
    QTreeWidget {
        background: #ffffff; color: #0f172a;
        border: 1px solid #e2e8f0; font-size: 12px; border-radius: 5px;
    }
    QTreeWidget::item { padding: 5px 6px; border-radius: 4px; }
    QTreeWidget::item:selected { background: #eff6ff; color: #1d4ed8; font-weight: 600; }
    QTreeWidget::item:hover:!selected { background: #f8fafc; }
    QPushButton {
        background: #ffffff; color: #334155; border: 1px solid #cbd5e1;
        border-radius: 5px; padding: 5px 8px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: #eff6ff; color: #1d4ed8; border-color: #93c5fd; }
    QPushButton:pressed { background: #dbeafe; }
    QLineEdit { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                border-radius: 5px; padding: 5px 8px; font-size: 11px; }
    QLineEdit:focus { border: 1.5px solid #2563eb; }
    QLabel { color: #475569; font-size: 11px; }
"""


class LayerPanelWidget(QWidget):
    """
    Left-side layer panel — shows all project layers with:
    - Visibility toggle (checkbox)
    - Layer icons (vector / raster / DEM elevation)
    - Right-click context menu with Global Mapper & ArcGIS style DEM/Raster tools
    - Search filtering
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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        header_box = QHBoxLayout()
        header = QLabel("🗂  LAYERS")
        header.setStyleSheet("color: #1e40af; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; padding: 2px 2px;")
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet("background: #eff6ff; color: #2563eb; font-weight: 700; font-size: 10px; border-radius: 8px; padding: 1px 7px; border: 1px solid #bfdbfe;")
        header_box.addWidget(header)
        header_box.addStretch()
        header_box.addWidget(self.count_badge)
        layout.addLayout(header_box)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search layers...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter_layers)
        layout.addWidget(self.search)

        # Layer tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        # Quick-add buttons
        btn_row = QHBoxLayout()
        btn_v = QPushButton("📂 Vector")
        btn_v.clicked.connect(self._quick_add_vector)
        btn_r = QPushButton("🏔 Raster / DEM")
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
                if getattr(layer, '_is_sub_relief_layer', False) or "[3D Hillshade]" in layer.name():
                    continue

                is_vector = layer.type() == QgsMapLayer.VectorLayer
                is_dem = (not is_vector) and ElevationStyler.is_dem_or_elevation(layer)
                
                clean_name = layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "").replace(" [3D Hillshade]", "").strip()
                if is_vector:
                    icon = "🗂"
                    label_text = f"  {icon}  {clean_name}"
                elif is_dem:
                    icon = "🏔"
                    label_text = f"  {icon}  {clean_name} [DEM]"
                else:
                    icon = "🗺"
                    label_text = f"  {icon}  {clean_name}"

                item = QTreeWidgetItem([label_text])
                item.setData(0, Qt.UserRole, layer.id())
                item.setCheckState(0, Qt.Checked if layer.isValid() else Qt.Unchecked)

                if is_vector:
                    item.setForeground(0, QBrush(QColor("#15803d")))
                elif is_dem:
                    item.setForeground(0, QBrush(QColor("#b45309")))
                else:
                    item.setForeground(0, QBrush(QColor("#0369a1")))

                self.tree.addTopLevelItem(item)
            
            if self.tree.topLevelItemCount() > 0:
                self.tree.setCurrentItem(self.tree.topLevelItem(0))
            if hasattr(self, 'count_badge'):
                self.count_badge.setText(str(self.tree.topLevelItemCount()))
        except ImportError:
            pass
        self.tree.blockSignals(False)

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

    def _on_item_double_clicked(self, item, col):
        layer = self._layer_from_item(item)
        if layer:
            self.active_layer_changed.emit(layer)
            self.map_canvas.zoom_to_layer(layer)

    def _on_item_changed(self, item, col):
        """Toggle layer visibility when checkbox is toggled."""
        layer = self._layer_from_item(item)
        if layer:
            try:
                from qgis.core import QgsProject
                root = QgsProject.instance().layerTreeRoot()
                node = root.findLayer(layer.id())
                if node:
                    node.setItemVisibilityChecked(item.checkState(0) == Qt.Checked)
                linked_id = getattr(layer, "_linked_hs_layer_id", None)
                if linked_id:
                    hs_node = root.findLayer(linked_id)
                    if hs_node:
                        hs_node.setItemVisibilityChecked(item.checkState(0) == Qt.Checked)
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

        from qgis.core import QgsMapLayer
        is_raster = layer.type() == QgsMapLayer.RasterLayer
        is_dem = is_raster and ElevationStyler.is_dem_or_elevation(layer)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 6px; }
            QMenu::item:selected { background: #2563eb; color: #ffffff; }
            QMenu::separator { height: 1px; background: #e2e8f0; margin: 4px 0px; }
        """)

        menu.addAction("🔍 Zoom to Layer",        lambda: self._zoom_to(layer))
        
        if not is_raster:
            menu.addAction("📊 Open Attribute Table", lambda: self._open_attr_table(layer))
            menu.addAction("🎨 Change Vector Color",  lambda: self._change_color(layer))

        # ── Specialized DEM / Elevation & Raster Tools ─────────
        if is_raster:
            menu.addSeparator()
            menu.addAction("⛰ Elevation Symbology & 3D Relief...", lambda: self.open_dem_dialog(layer))

            # Quick Elevation Shader Presets Submenu
            dem_menu = menu.addMenu("🏔 Quick Elevation Shader")
            dem_menu.setStyleSheet(menu.styleSheet())
            dem_menu.addAction("🏔 Global Mapper Atlas / Terrain", lambda: self._apply_elevation_preset(layer, "GLOBAL_MAPPER_ATLAS"))
            dem_menu.addAction("🌍 ArcGIS Elevation #1 (Earth Tones)", lambda: self._apply_elevation_preset(layer, "ARCGIS_ELEVATION"))
            dem_menu.addAction("🗺 SRTM / USGS Topographic", lambda: self._apply_elevation_preset(layer, "SRTM_TOPO"))
            dem_menu.addAction("🔮 Viridis Scientific", lambda: self._apply_elevation_preset(layer, "VIRIDIS"))
            dem_menu.addAction("🌈 Turbo Vibrant Rainbow", lambda: self._apply_elevation_preset(layer, "TURBO"))
            dem_menu.addAction("🌊 Bathymetry + Topography", lambda: self._apply_elevation_preset(layer, "BATHO_TOPO"))
            dem_menu.addAction("🌿 Modern Emerald & Terracotta", lambda: self._apply_elevation_preset(layer, "TERRAIN_MODERN"))

            menu.addAction("💡 3D Hillshade Relief (Multi-Directional)", lambda: self._apply_hillshade_quick(layer))
            menu.addAction("🌓 Auto High-Contrast Grayscale", lambda: self._apply_grayscale_quick(layer))

            # Pixel Interpolation Mode (Sharp raw pixels vs Smooth anti-aliasing)
            pixel_menu = menu.addMenu("🔍 Pixel Display Mode")
            pixel_menu.setStyleSheet(menu.styleSheet())
            pixel_menu.addAction("⬛ Sharp Pixels (Nearest Neighbor - Raw Sensor)", lambda: self._set_pixel_mode(layer, "sharp"))
            pixel_menu.addAction("✨ Smooth Blending (Bicubic Anti-Aliasing)", lambda: self._set_pixel_mode(layer, "smooth"))

        menu.addSeparator()
        menu.addAction("ℹ Layer Properties",       lambda: self._show_props(layer))
        menu.addAction("👁 Toggle Visibility",      lambda: self._toggle_visibility(item, layer))
        menu.addSeparator()
        menu.addAction("📋 Rename Layer",           lambda: self._rename_layer(item, layer))
        menu.addAction("🗑 Remove Layer",            lambda: self._remove_layer(layer))
        menu.addSeparator()
        menu.addAction("💾 Export Layer...",         lambda: self._export_layer(layer))

        menu.exec_(self.tree.mapToGlobal(pos))

    def open_dem_dialog(self, layer=None):
        """Opens the DEM Elevation Symbology Dialog."""
        target = layer or self.get_active_layer()
        try:
            from ui.dem_elevation_dialog import DEMElevationDialog
            dlg = DEMElevationDialog(map_canvas=self.map_canvas, target_layer=target, parent=self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open DEM styling dialog: {e}")

    def _apply_elevation_preset(self, layer, preset_key):
        if layer and layer.isValid():
            ElevationStyler.apply_draped_relief(layer, preset_key=preset_key)
            if self.map_canvas:
                self.map_canvas.update_elevation_legend(layer)
                self.map_canvas.refresh_canvas()

    def _apply_hillshade_quick(self, layer):
        if layer and layer.isValid():
            ElevationStyler.apply_hillshade(layer, band=1, z_factor=1.0, azimuth=315.0, altitude=45.0, multidirectional=True)
            if self.map_canvas:
                self.map_canvas.refresh_canvas()

    def _set_pixel_mode(self, layer, mode: str):
        if layer and layer.isValid():
            ElevationStyler.apply_resampling(layer, mode=mode)
            linked_id = getattr(layer, "_linked_hs_layer_id", None)
            if linked_id:
                try:
                    from qgis.core import QgsProject
                    hs = QgsProject.instance().mapLayer(linked_id)
                    if hs:
                        ElevationStyler.apply_resampling(hs, mode=mode)
                except Exception:
                    pass
            if self.map_canvas:
                self.map_canvas.refresh_canvas()

    def _apply_grayscale_quick(self, layer):
        if layer and layer.isValid():
            ElevationStyler.apply_grayscale_contrast(layer, band=1, stretch_type="cumulative_cut")
            if self.map_canvas:
                self.map_canvas.refresh_canvas()

    # ──────────────────────────────────────────────────────────
    # Layer Loading
    # ──────────────────────────────────────────────────────────
    def _quick_add_vector(self):
        path, _ = QFileDialog.getOpenFileName(None, "Add Vector Layer", "",
            "Vector (*.shp *.gpkg *.geojson *.json *.kml *.gml *.csv *.tab);;All (*)")
        if path:
            self.load_vector(path)

    def _quick_add_raster(self):
        path, _ = QFileDialog.getOpenFileName(None, "Add Raster / DEM Layer", "",
            "Elevation & Rasters (*.tif *.tiff *.dem *.dtm *.dsm *.hgt *.asc *.img *.nc *.hdf *.vrt *.jp2);;All (*)")
        if path:
            self.load_raster(path)

    def load_vector(self, path):
        try:
            from qgis.core import QgsVectorLayer, QgsProject
            name = os.path.splitext(os.path.basename(path))[0]
            layer = QgsVectorLayer(path, name, "ogr")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.map_canvas.zoom_to_layer(layer)
                self.active_layer_changed.emit(layer)
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
                is_dem = ElevationStyler.is_dem_or_elevation(layer)
                QgsProject.instance().addMapLayer(layer)

                if is_dem:
                    # Apply 100% Native Full-Resolution 3D Shaded Relief with smooth Bicubic Anti-Aliasing
                    ElevationStyler.apply_draped_relief(layer, preset_key="GLOBAL_MAPPER_ATLAS")
                    self.map_canvas.update_elevation_legend(layer)
                else:
                    # Orthomosaics & RGB Drone Imagery default to sharp raw camera pixels (Nearest Neighbor)
                    ElevationStyler.apply_resampling(layer, mode="sharp")

                self.map_canvas.zoom_to_layer(layer)
                self.active_layer_changed.emit(layer)

                # Check and build fast pyramids in background if large
                try:
                    get_raster_optimizer().check_and_optimize(layer, self.map_canvas.canvas)
                except Exception:
                    pass
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
                self.map_canvas.zoom_to_layer(layer)
                self.active_layer_changed.emit(layer)
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
                self.map_canvas.zoom_to_layer(layer)
                self.active_layer_changed.emit(layer)
            else:
                QMessageBox.critical(None, "CSV Error", "Could not load CSV. Check X/Y column names.")
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))

    # ──────────────────────────────────────────────────────────
    # Context Menu Actions
    # ──────────────────────────────────────────────────────────
    def _zoom_to(self, layer):
        if layer:
            self.map_canvas.zoom_to_layer(layer)

    def _open_attr_table(self, layer):
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
                info += f"Dimensions: {layer.width()} x {layer.height()} px\n"
                if ElevationStyler.is_dem_or_elevation(layer):
                    stats = ElevationStyler.get_valid_elevation_stats(layer, 1)
                    if stats:
                        info += (f"\n🏔 Elevation Characteristics:\n"
                                 f"  Min Elevation: {stats['min']:.2f} m\n"
                                 f"  Max Elevation: {stats['max']:.2f} m\n"
                                 f"  Mean Elevation: {stats['mean']:.2f} m\n"
                                 f"  Std Deviation: {stats['std_dev']:.2f}\n"
                                 f"  2%-98% Cut: {stats['p2']:.2f} m – {stats['p98']:.2f} m\n"
                                 f"  NoData Value: {stats['nodata_val']}\n")
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
                linked_id = getattr(layer, "_linked_hs_layer_id", None)
                if linked_id:
                    QgsProject.instance().removeMapLayer(linked_id)
                QgsProject.instance().removeMapLayer(layer.id())
            except Exception:
                pass

    def _export_layer(self, layer):
        try:
            from qgis.core import QgsVectorFileWriter, QgsCoordinateTransformContext, QgsMapLayer
            if layer.type() != QgsMapLayer.VectorLayer:
                QMessageBox.information(None, "Export", "Raster export is available in Raster Processing dock.")
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
