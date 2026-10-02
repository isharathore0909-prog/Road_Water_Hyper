# -*- coding: utf-8 -*-
"""
GeoStudio - Layer Loading Progress Dialog
Provides a modal progress dialog with a live progress bar and direct
loading for LiDAR point clouds (LAS/LAZ), Rasters/DEMs, and Vector datasets.
"""

import os
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QMessageBox, QFrame, QApplication
)

from core.elevation_styler import ElevationStyler
from core.point_cloud_rasterizer import PointCloudRasterizer


class LayerLoadingProgressDialog(QDialog):
    """
    Modal progress dialog displaying:
    - Layer Name & Formatted File Size
    - Percentage Progress Bar
    - Real-time Stage Status
    """

    def __init__(self, parent, file_path: str, layer_type: str = "auto", x_field: str = "longitude", y_field: str = "latitude"):
        super().__init__(parent)
        self.file_path = os.path.normpath(file_path)
        self.layer_type = layer_type
        self.x_field = x_field
        self.y_field = y_field
        self.loaded_layer = None
        self.error_message = None
        self.success = False
        self._is_cancelled = False

        self._init_window()
        self._build_ui()
        QTimer.singleShot(40, self._run_loading_sequence)

    def _init_window(self):
        self.setWindowTitle("Loading Layer — GeoStudio")
        self.setFixedSize(540, 240)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
                color: #0f172a;
                font-family: "Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif;
            }
        """)

    def _format_size(self, file_path: str) -> str:
        try:
            sz = os.path.getsize(file_path)
            if sz >= 1024 * 1024 * 1024:
                return f"{sz / (1024 * 1024 * 1024):.2f} GB"
            elif sz >= 1024 * 1024:
                return f"{sz / (1024 * 1024):.1f} MB"
            elif sz >= 1024:
                return f"{sz / 1024:.1f} KB"
            return f"{sz} bytes"
        except Exception:
            return ""

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header_box = QHBoxLayout()
        ext = os.path.splitext(self.file_path)[1].lower()

        if self.layer_type == "point_cloud" or ext in [".las", ".laz", ".copc.laz", ".e57"]:
            icon_str = "☁"
            type_title = "Loading LiDAR Point Cloud"
            type_badge = "LiDAR / LAS / LAZ"
            badge_bg = "#e0e7ff"
            badge_fg = "#3730a3"
        elif self.layer_type == "raster" or ext in [".tif", ".tiff", ".dem", ".dtm", ".dsm", ".hgt", ".asc", ".img", ".nc", ".hdf", ".vrt", ".jp2"]:
            icon_str = "🏔"
            type_title = "Loading Raster / Elevation Dataset"
            type_badge = "Raster / DEM"
            badge_bg = "#dcfce7"
            badge_fg = "#166534"
        else:
            icon_str = "🗂"
            type_title = "Loading Vector Layer"
            type_badge = "Vector Layer"
            badge_bg = "#f1f5f9"
            badge_fg = "#334155"

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 26px; margin-right: 4px;")
        header_box.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        lbl_title = QLabel(type_title)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")
        title_col.addWidget(lbl_title)

        fname = os.path.basename(self.file_path)
        sz_str = self._format_size(self.file_path)
        subtitle_text = f"{fname}  •  {sz_str}" if sz_str else fname
        lbl_sub = QLabel(subtitle_text)
        lbl_sub.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        title_col.addWidget(lbl_sub)

        header_box.addLayout(title_col)
        header_box.addStretch()

        badge_lbl = QLabel(f" {type_badge} ")
        badge_lbl.setStyleSheet(f"background: {badge_bg}; color: {badge_fg}; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 4px 8px;")
        header_box.addWidget(badge_lbl)

        layout.addLayout(header_box)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: #f1f5f9; background-color: #f1f5f9; height: 1px; border: none;")
        layout.addWidget(div)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background: #f8fafc;
                font-weight: 700;
                font-size: 11px;
                color: #0f172a;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #334155);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Initializing dataset reader & spatial index...")
        self.lbl_status.setStyleSheet("color: #334155; font-size: 11px; font-weight: 500;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        btn_box = QHBoxLayout()
        self.lbl_hint = QLabel("⚡ High-performance native spatial rendering engine")
        self.lbl_hint.setStyleSheet("color: #94a3b8; font-size: 10px;")
        btn_box.addWidget(self.lbl_hint)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 6px 18px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #f1f5f9;
                color: #0f172a;
            }
        """)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_box.addWidget(self.btn_cancel)

        layout.addLayout(btn_box)

    def _update_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        if msg:
            self.lbl_status.setText(msg)
        QApplication.processEvents()

    def _run_loading_sequence(self):
        if self._is_cancelled:
            self.reject()
            return

        if not os.path.exists(self.file_path):
            self._handle_error(f"File not found: {self.file_path}")
            return

        ext = os.path.splitext(self.file_path)[1].lower()
        if self.layer_type == "point_cloud" or ext in [".las", ".laz", ".copc.laz", ".e57"]:
            self._load_point_cloud()
        elif self.layer_type == "raster" or ext in [".tif", ".tiff", ".dem", ".dtm", ".dsm", ".hgt", ".asc", ".img", ".nc", ".hdf", ".vrt", ".jp2"]:
            self._load_raster()
        elif ext == ".csv":
            self._load_csv()
        else:
            self._load_vector()

    def _load_point_cloud(self):
        try:
            from qgis.core import QgsPointCloudLayer, QgsCoordinateReferenceSystem
            from core.lidar_styler import LidarStyler
            from core.point_cloud_indexer import PointCloudIndexer

            name = os.path.splitext(os.path.basename(self.file_path))[0]
            clean_name = name.replace(".copc", "")

            # 1. If already .copc.laz or an existing pre-built index exists, use it; otherwise build genuine COPC octree
            copc_path = None
            if self.file_path.lower().endswith(".copc.laz"):
                copc_path = self.file_path
            else:
                target_copc = PointCloudIndexer.get_target_copc_path(self.file_path)
                if os.path.exists(target_copc) and os.path.getsize(target_copc) > 1024:
                    copc_path = target_copc
                else:
                    self._update_progress(15, "Generating Cloud-Optimized Point Cloud (.copc.laz) for discrete 3D point sprites...")
                    copc_path = PointCloudIndexer.ensure_copc_index(self.file_path, progress_callback=self._update_progress)

            source_path = copc_path if (copc_path and os.path.exists(copc_path)) else self.file_path
            provider = "copc" if (copc_path and os.path.exists(copc_path)) else "pdal"

            self._update_progress(75, f"Mounting discrete 3D point cloud layer ({provider.upper()})...")
            layer = QgsPointCloudLayer(source_path, f"{clean_name} [LiDAR]", provider)

            if not layer or not layer.isValid():
                alt_provider = "pdal" if provider == "copc" else "copc"
                layer = QgsPointCloudLayer(source_path, f"{clean_name} [LiDAR]", alt_provider)

            if not layer or not layer.isValid():
                self._handle_error(f"Could not initialize discrete 3D point cloud layer for:\n{self.file_path}")
                return

            self._update_progress(85, "Configuring spatial reference system...")
            if not layer.crs().isValid() or not layer.crs().authid():
                ext = layer.extent()
                if abs(ext.xMinimum()) <= 180.0 and abs(ext.yMaximum()) <= 90.0:
                    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
                else:
                    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:32643"))

            self._update_progress(92, "Styling discrete 3D point cloud sprites (True Color & Elevation)...")
            LidarStyler.auto_style(layer, point_size=3.5)

            layer.setCustomProperty("original_las_path", self.file_path)
            layer.setCustomProperty("is_lidar_layer", True)
            if copc_path:
                layer.setCustomProperty("copc_path", copc_path)

            self.loaded_layer = layer
            self._update_progress(100, "LiDAR dataset loaded successfully!")
            self.success = True
            QTimer.singleShot(120, self.accept)

        except Exception as e:
            self._handle_error(str(e))

    def _load_raster(self):
        try:
            from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem

            name = os.path.splitext(os.path.basename(self.file_path))[0]
            self._update_progress(35, "Reading raster dataset bands & extent...")

            layer = QgsRasterLayer(self.file_path, name)
            if not layer or not layer.isValid():
                self._handle_error(f"Invalid raster file: {self.file_path}")
                return

            if not layer.crs().isValid() or not layer.crs().authid():
                ext = layer.extent()
                if ext.xMinimum() > 180.0 or ext.yMinimum() > 90.0:
                    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:32643"))
                else:
                    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

            self._update_progress(75, "Analyzing elevation statistics & shaders...")
            if ElevationStyler.is_dem_or_elevation(layer):
                self._update_progress(90, "Configuring Global Mapper Atlas terrain shader...")
                ElevationStyler.apply_elevation_colormap(layer, preset_key="GLOBAL_MAPPER_ATLAS")
                ElevationStyler.apply_resampling(layer, mode="smooth")
            else:
                self._update_progress(90, "Configuring crisp imagery resampling...")
                ElevationStyler.apply_resampling(layer, mode="sharp")

            self._update_progress(100, "Raster layer ready!")
            self.success = True
            self.loaded_layer = layer
            QTimer.singleShot(120, self.accept)

        except Exception as e:
            self._handle_error(str(e))

    def _load_vector(self):
        try:
            from qgis.core import QgsVectorLayer
            name = os.path.splitext(os.path.basename(self.file_path))[0]
            self._update_progress(40, "Reading vector geometry features & table...")

            layer = QgsVectorLayer(self.file_path, name, "ogr")
            if layer and layer.isValid():
                feat_count = layer.featureCount()
                self._update_progress(85, f"Loaded {feat_count:,} features. Finalizing...")
                self._update_progress(100, "Vector layer ready!")
                self.success = True
                self.loaded_layer = layer
                QTimer.singleShot(120, self.accept)
            else:
                self._handle_error(f"Invalid vector layer: {self.file_path}")
        except Exception as e:
            self._handle_error(str(e))

    def _load_csv(self):
        try:
            from qgis.core import QgsVectorLayer
            name = os.path.splitext(os.path.basename(self.file_path))[0]
            self._update_progress(40, "Parsing CSV points & coordinates...")

            uri = f"file:///{self.file_path.replace(os.sep, '/')}?delimiter=,&xField={self.x_field}&yField={self.y_field}&crs=epsg:4326&useHeader=yes"
            layer = QgsVectorLayer(uri, name, "delimitedtext")
            if layer and layer.isValid():
                self._update_progress(100, "CSV points layer ready!")
                self.success = True
                self.loaded_layer = layer
                QTimer.singleShot(120, self.accept)
            else:
                self._handle_error("Could not parse CSV. Verify X/Y coordinate column names.")
        except Exception as e:
            self._handle_error(str(e))

    def _handle_error(self, err_msg: str):
        self.success = False
        self.error_message = err_msg
        if not self._is_cancelled:
            QMessageBox.critical(self, "Loading Error", f"Failed to load layer:\n{err_msg}")
        self.reject()

    def _on_cancel(self):
        self._is_cancelled = True
        try:
            from core.point_cloud_indexer import PointCloudIndexer
            PointCloudIndexer.cancel()
        except Exception:
            pass
        self.reject()
