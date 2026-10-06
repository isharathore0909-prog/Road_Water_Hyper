# -*- coding: utf-8 -*-
"""
GeoStudio - Layer Context Menu & Action Dispatchers
Builds context menus for Vector, Point Cloud, and DEM/Raster layers with styling shortcuts.
"""

import os
import re
from PyQt5.QtWidgets import (
    QMenu, QAction, QFileDialog, QMessageBox, QColorDialog, QInputDialog
)
from PyQt5.QtGui import QColor

from core.elevation_styler import ElevationStyler, ELEVATION_PRESETS


class LayerContextMenuHandler:
    """Handles context menus and actions for layers in the layer panel."""

    @classmethod
    def show_context_menu(cls, panel, pos):
        item = panel.tree.itemAt(pos)
        if not item:
            return

        layer = panel._layer_from_item(item)
        if not layer:
            return

        panel.active_layer_changed.emit(layer)
        menu = QMenu(panel)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px; font-size: 11px; }
            QMenu::item { padding: 5px 20px 5px 24px; border-radius: 4px; }
            QMenu::item:selected { background: #e2e8f0; color: #0f172a; font-weight: 600; }
            QMenu::separator { height: 1px; background: #e2e8f0; margin: 4px 6px; }
        """)

        # Common actions
        act_zoom = menu.addAction("🔍  Zoom to Layer")
        act_zoom.triggered.connect(lambda: cls.zoom_to(panel, layer))

        from qgis.core import QgsVectorLayer, QgsRasterLayer
        is_vector = isinstance(layer, QgsVectorLayer)
        is_point_cloud = "PointCloud" in type(layer).__name__
        is_dem = (not is_vector) and (not is_point_cloud) and ElevationStyler.is_dem_or_elevation(layer)

        if is_dem:
            menu.addSeparator()
            act_elev_dlg = menu.addAction("🏔  DEM Elevation & 3D Shaded Relief...")
            act_elev_dlg.triggered.connect(lambda: cls.open_dem_dialog(panel, layer))

            preset_menu = menu.addMenu("🎨  Apply Elevation Color Ramp")
            for key, info in ELEVATION_PRESETS.items():
                act_p = preset_menu.addAction(info["name"])
                act_p.triggered.connect(lambda checked=False, k=key: cls.apply_elevation_preset(panel, layer, k))

            act_hs = menu.addAction("🌓  Apply Grayscale 3D Hillshade")
            act_hs.triggered.connect(lambda: cls.apply_hillshade_quick(panel, layer))

            act_gray = menu.addAction("⚫  Apply Grayscale Stretch (Min/Max)")
            act_gray.triggered.connect(lambda: cls.apply_grayscale_quick(panel, layer))

            menu.addSeparator()
            act_vol = menu.addAction("📦  Calculate Volumetrics (Cut / Fill)...")
            act_vol.triggered.connect(lambda: cls.open_volumetrics(panel, layer))

            act_cutfill = menu.addAction("🚜  Compare Surface Difference (Cut & Fill)...")
            act_cutfill.triggered.connect(lambda: cls.open_cut_fill(panel, layer))

        if not is_vector and not is_point_cloud:
            resamp_menu = menu.addMenu("👁  Pixel Display Mode")
            act_smooth = resamp_menu.addAction("Smooth (Bicubic / Bilinear)")
            act_sharp = resamp_menu.addAction("Sharp Pixels (Nearest Neighbor)")
            act_smooth.triggered.connect(lambda: cls.set_pixel_mode(panel, layer, "smooth"))
            act_sharp.triggered.connect(lambda: cls.set_pixel_mode(panel, layer, "sharp"))

        if is_vector:
            act_table = menu.addAction("📋  Open Attribute Table")
            act_table.triggered.connect(lambda: cls.open_attr_table(panel, layer))
            act_color = menu.addAction("🎨  Change Symbology Color...")
            act_color.triggered.connect(lambda: cls.change_color(panel, layer))

        menu.addSeparator()
        act_3d = menu.addAction("🧊  Open in 3D Point Cloud / Terrain Viewer")
        act_3d.triggered.connect(lambda: cls.open_3d_viewer(panel, layer))

        menu.addSeparator()
        act_rename = menu.addAction("✏️  Rename Layer")
        act_rename.triggered.connect(lambda: cls.rename_layer(panel, item, layer))

        act_export = menu.addAction("💾  Export Layer...")
        act_export.triggered.connect(lambda: cls.export_layer(panel, layer))

        act_props = menu.addAction("ℹ️  Properties / Metadata...")
        act_props.triggered.connect(lambda: cls.show_props(panel, layer))

        menu.addSeparator()
        act_remove = menu.addAction("🗑  Remove Layer")
        act_remove.triggered.connect(lambda: cls.remove_layer(panel, layer))

        menu.exec_(panel.tree.viewport().mapToGlobal(pos))

    @staticmethod
    def open_dem_dialog(panel, layer=None):
        if not layer:
            layer = panel.get_active_layer()
        if not layer:
            return
        from ui.dem_elevation_dialog import DemElevationDialog
        dlg = DemElevationDialog(layer, parent=panel)
        dlg.exec_()
        panel.refresh()

    @staticmethod
    def open_volumetrics(panel, layer=None):
        if not layer:
            layer = panel.get_active_layer()
        if not layer:
            return
        from ui.volumetric_dialog import VolumetricDialog
        dlg = VolumetricDialog(layer, parent=panel)
        dlg.exec_()

    @staticmethod
    def open_cut_fill(panel, layer=None):
        if not layer:
            layer = panel.get_active_layer()
        if not layer:
            return
        from ui.cut_fill_dialog import CutFillDialog
        dlg = CutFillDialog(layer, parent=panel)
        dlg.exec_()

    @staticmethod
    def apply_elevation_preset(panel, layer, preset_key):
        if not layer or not layer.isValid():
            return
        try:
            from core.elevation_styler import ElevationStyler
            raw_source = getattr(layer, "_raw_dem_source", layer.source())
            res = ElevationStyler.apply_draped_relief(layer, preset_key=preset_key)
            if res:
                panel.refresh()
                panel.map_canvas.refresh_canvas()
                if hasattr(panel.map_canvas, "update_elevation_legend"):
                    panel.map_canvas.update_elevation_legend(res if hasattr(res, 'isValid') else layer)
        except Exception as e:
            QMessageBox.critical(panel, "Error", f"Failed to apply preset: {e}")

    @staticmethod
    def apply_hillshade_quick(panel, layer):
        if not layer or not layer.isValid():
            return
        from core.elevation_styler import ElevationStyler
        res = ElevationStyler.apply_hillshade(layer)
        if res:
            panel.refresh()
            panel.map_canvas.refresh_canvas()

    @staticmethod
    def set_pixel_mode(panel, layer, mode: str):
        if not layer or not layer.isValid():
            return
        from core.elevation_styler import ElevationStyler
        ElevationStyler.apply_resampling(layer, mode=mode)
        panel.map_canvas.refresh_canvas()

    @staticmethod
    def apply_grayscale_quick(panel, layer):
        if not layer or not layer.isValid():
            return
        from core.elevation_styler import ElevationStyler
        ElevationStyler.apply_grayscale_contrast(layer)
        panel.map_canvas.refresh_canvas()

    @staticmethod
    def zoom_to(panel, layer):
        if layer:
            panel.map_canvas.zoom_to_layer(layer)

    @staticmethod
    def open_attr_table(panel, layer):
        if layer:
            from ui.attribute_table_dialog import AttributeTableDialog
            dlg = AttributeTableDialog(layer, parent=panel)
            dlg.show()

    @staticmethod
    def show_props(panel, layer):
        if not layer or not layer.isValid():
            return
        info = f"<b>Layer Name:</b> {layer.name()}<br>"
        info += f"<b>Source:</b> {layer.source()}<br>"
        info += f"<b>CRS:</b> {layer.crs().authid()} ({layer.crs().description()})<br>"
        info += f"<b>Type:</b> {'Vector' if isinstance(layer, QgsVectorLayer) else 'Raster / Point Cloud'}<br>"
        ext = layer.extent()
        info += f"<b>Extent:</b> [{ext.xMinimum():.3f}, {ext.yMinimum():.3f}] - [{ext.xMaximum():.3f}, {ext.yMaximum():.3f}]<br>"

        from qgis.core import QgsRasterLayer
        if isinstance(layer, QgsRasterLayer):
            info += f"<b>Dimensions:</b> {layer.width()} x {layer.height()} pixels<br>"
            info += f"<b>Bands:</b> {layer.bandCount()}<br>"
            stats = ElevationStyler.get_valid_elevation_stats(layer)
            if stats:
                info += f"<b>Elevation Min / Max:</b> {stats['min']:.2f} m / {stats['max']:.2f} m<br>"

        QMessageBox.information(panel, f"Properties - {layer.name()}", info)

    @staticmethod
    def open_3d_viewer(panel, layer):
        if not layer or not layer.isValid():
            return
        source_path = getattr(layer, "_raw_dem_source", layer.source())
        if not os.path.exists(source_path):
            source_path = layer.source()
        if os.path.exists(source_path):
            from ui.viewer3d.window import Viewer3DWindow
            v3d = Viewer3DWindow(parent=panel.window() if panel.window() else None)
            v3d.load_point_cloud(source_path)
            v3d.show()

    @staticmethod
    def change_color(panel, layer):
        if not layer:
            return
        col = QColorDialog.getColor(QColor("#2563eb"), panel, "Select Layer Color")
        if col.isValid():
            from qgis.core import QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsSingleSymbolRenderer
            sym_layer = QgsSimpleFillSymbolLayer(col)
            sym = QgsFillSymbol()
            sym.changeSymbolLayer(0, sym_layer)
            layer.setRenderer(QgsSingleSymbolRenderer(sym))
            layer.triggerRepaint()
            panel.map_canvas.refresh_canvas()

    @staticmethod
    def rename_layer(panel, item, layer):
        if not layer:
            return
        new_name, ok = QInputDialog.getText(panel, "Rename Layer", "New Name:", text=layer.name())
        if ok and new_name.strip():
            layer.setName(new_name.strip())
            panel.refresh()

    @staticmethod
    def remove_layer(panel, layer):
        if not layer:
            return
        from qgis.core import QgsProject
        resp = QMessageBox.question(
            panel, "Remove Layer",
            f"Are you sure you want to remove '{layer.name()}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            QgsProject.instance().removeMapLayer(layer.id())
            panel.refresh()

    @staticmethod
    def export_layer(panel, layer):
        if not layer or not layer.isValid():
            return
        from qgis.core import QgsVectorLayer, QgsVectorFileWriter
        if isinstance(layer, QgsVectorLayer):
            path, _ = QFileDialog.getSaveFileName(panel, "Export Vector", f"{layer.name()}.geojson", "GeoJSON (*.geojson);;Shapefile (*.shp);;GeoPackage (*.gpkg)")
            if path:
                err = QgsVectorFileWriter.writeAsVectorFormat(layer, path, "utf-8", layer.crs())
                if err == QgsVectorFileWriter.NoError:
                    QMessageBox.information(panel, "Exported", f"Successfully exported to:\n{path}")
                else:
                    QMessageBox.critical(panel, "Export Failed", f"Export failed with error code: {err}")
        else:
            path, _ = QFileDialog.getSaveFileName(panel, "Export Raster", f"{layer.name()}.tif", "GeoTIFF (*.tif);;All Files (*.*)")
            if path and os.path.exists(layer.source()):
                import shutil
                shutil.copy(layer.source(), path)
                QMessageBox.information(panel, "Exported", f"Successfully exported to:\n{path}")
