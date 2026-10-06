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

from app.ui.layer_loading_worker import (
    load_point_cloud_layer,
    load_raster_layer,
    load_vector_layer,
    load_csv_layer
)


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
        self.setStyleSheet("QDialog { background: #ffffff; color: #0f172a; font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', sans-serif; }")

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
            icon_str, type_title, type_badge, badge_bg, badge_fg = "☁", "Loading LiDAR Point Cloud", "LiDAR / LAS / LAZ", "#e0e7ff", "#3730a3"
        elif self.layer_type == "raster" or ext in [".tif", ".tiff", ".dem", ".dtm", ".dsm", ".hgt", ".asc", ".img", ".nc", ".hdf", ".vrt", ".jp2"]:
            icon_str, type_title, type_badge, badge_bg, badge_fg = "🏔", "Loading Raster / Elevation Dataset", "Raster / DEM", "#dcfce7", "#166534"
        else:
            icon_str, type_title, type_badge, badge_bg, badge_fg = "🗂", "Loading Vector Layer", "Vector Layer", "#f1f5f9", "#334155"

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
                border: 1px solid #cbd5e1; border-radius: 6px; text-align: center; height: 24px;
                background: #f8fafc; font-weight: 700; font-size: 11px; color: #0f172a;
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
        self.btn_cancel.setStyleSheet("QPushButton { background: #ffffff; color: #334155; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px 18px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: #f1f5f9; color: #0f172a; }")
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
        try:
            if self.layer_type == "point_cloud" or ext in [".las", ".laz", ".copc.laz", ".e57"]:
                self.loaded_layer = load_point_cloud_layer(self.file_path, progress_cb=self._update_progress)
            elif self.layer_type == "raster" or ext in [".tif", ".tiff", ".dem", ".dtm", ".dsm", ".hgt", ".asc", ".img", ".nc", ".hdf", ".vrt", ".jp2"]:
                self.loaded_layer = load_raster_layer(self.file_path, progress_cb=self._update_progress)
            elif ext == ".csv":
                self.loaded_layer = load_csv_layer(self.file_path, self.x_field, self.y_field, progress_cb=self._update_progress)
            else:
                self.loaded_layer = load_vector_layer(self.file_path, progress_cb=self._update_progress)

            self._update_progress(100, "Dataset loaded successfully!")
            self.success = True
            QTimer.singleShot(120, self.accept)

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
