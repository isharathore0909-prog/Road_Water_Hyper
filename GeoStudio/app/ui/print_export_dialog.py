# -*- coding: utf-8 -*-
"""
GeoStudio - Print & Export Map Layout Dialog
Provides high-resolution map image and PDF export with custom DPI,
title, scale bar, and north arrow overlays.
"""

import os
import subprocess
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QRadioButton,
    QButtonGroup, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF
from PyQt5.QtGui import (
    QImage, QPainter, QColor, QFont, QPen, QBrush, QPixmap
)

from qgis.core import (
    QgsProject, QgsMapSettings, QgsMapRendererCustomPainterJob,
    QgsRectangle, QgsDistanceArea
)


class PrintExportDialog(QDialog):
    """High-resolution map export and print dialog."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.mw = main_window
        self.setWindowTitle("Print & Export Map Layout")
        self.resize(560, 480)
        self.setMinimumWidth(480)

        self._init_ui()
        self._update_dimensions_info()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Group 1: Output Format & Dimensions ────────────
        grp_output = QGroupBox("Output Settings")
        form_output = QFormLayout(grp_output)
        form_output.setSpacing(8)

        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG High-Res Image (*.png)", "JPEG Image (*.jpg)", "PDF Document (*.pdf)"])
        form_output.addRow("Format:", self.combo_format)

        self.combo_preset = QComboBox()
        self.combo_preset.addItems([
            "Current Map View (Exact Aspect)",
            "A4 Landscape (297 × 210 mm)",
            "A4 Portrait (210 × 297 mm)",
            "A3 Landscape (420 × 297 mm)",
            "Full HD (1920 × 1080 px)",
            "4K Ultra HD (3840 × 2160 px)",
        ])
        self.combo_preset.currentIndexChanged.connect(self._update_dimensions_info)
        form_output.addRow("Page Preset:", self.combo_preset)

        self.combo_dpi = QComboBox()
        self.combo_dpi.addItems(["96 DPI (Screen / Fast)", "150 DPI (Draft Print)", "300 DPI (High-Res Production)", "600 DPI (Ultra-Fine)"])
        self.combo_dpi.setCurrentIndex(2)  # Default 300 DPI
        self.combo_dpi.currentIndexChanged.connect(self._update_dimensions_info)
        form_output.addRow("Resolution (DPI):", self.combo_dpi)

        self.lbl_dims = QLabel("Output Dimensions: --")
        self.lbl_dims.setStyleSheet("color: #0284c7; font-weight: bold; font-size: 11px;")
        form_output.addRow("Calculated Size:", self.lbl_dims)

        layout.addWidget(grp_output)

        # ── Group 2: Layout & Decoration Elements ─────────
        grp_decor = QGroupBox("Map Elements & Overlays")
        form_decor = QFormLayout(grp_decor)
        form_decor.setSpacing(8)

        self.chk_title = QCheckBox("Include Map Title")
        self.chk_title.setChecked(True)
        self.txt_title = QLineEdit(f"{self.mw.APP_NAME} Map Layout")
        self.chk_title.toggled.connect(self.txt_title.setEnabled)
        form_decor.addRow(self.chk_title, self.txt_title)

        self.chk_scalebar = QCheckBox("Include Scale Bar")
        self.chk_scalebar.setChecked(True)
        form_decor.addRow(self.chk_scalebar)

        self.chk_north_arrow = QCheckBox("Include North Arrow")
        self.chk_north_arrow.setChecked(True)
        form_decor.addRow(self.chk_north_arrow)

        self.chk_border = QCheckBox("Draw Map Border & Coordinate Frame")
        self.chk_border.setChecked(True)
        form_decor.addRow(self.chk_border)

        layout.addWidget(grp_decor)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # ── Buttons ───────────────────────────────────────
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_box.addStretch()

        btn_export = QPushButton("🚀 Export & Save Map")
        btn_export.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 7px 16px; border-radius: 4px;")
        btn_export.clicked.connect(self._do_export)
        btn_box.addWidget(btn_export)

        layout.addLayout(btn_box)

    def _get_dpi(self):
        idx = self.combo_dpi.currentIndex()
        return [96, 150, 300, 600][idx]

    def _get_target_pixel_size(self):
        dpi = self._get_dpi()
        preset = self.combo_preset.currentText()

        if "A4 Landscape" in preset:
            w_in, h_in = 297 / 25.4, 210 / 25.4
            return int(w_in * dpi), int(h_in * dpi)
        elif "A4 Portrait" in preset:
            w_in, h_in = 210 / 25.4, 297 / 25.4
            return int(w_in * dpi), int(h_in * dpi)
        elif "A3 Landscape" in preset:
            w_in, h_in = 420 / 25.4, 297 / 25.4
            return int(w_in * dpi), int(h_in * dpi)
        elif "Full HD" in preset:
            return 1920, 1080
        elif "4K Ultra HD" in preset:
            return 3840, 2160
        else:
            # Current Map View scaled to DPI
            canvas = self.mw.map_canvas.canvas
            base_w = canvas.width() if canvas else 1200
            base_h = canvas.height() if canvas else 800
            scale = dpi / 96.0
            return int(base_w * scale), int(base_h * scale)

    def _update_dimensions_info(self):
        w, h = self._get_target_pixel_size()
        dpi = self._get_dpi()
        mp = (w * h) / 1_000_000
        self.lbl_dims.setText(f"{w} × {h} px  (~{mp:.1f} Megapixels @ {dpi} DPI)")

    def _do_export(self):
        fmt_idx = self.combo_format.currentIndex()
        if fmt_idx == 0:
            filt = "PNG Image (*.png)"
            ext = ".png"
        elif fmt_idx == 1:
            filt = "JPEG Image (*.jpg)"
            ext = ".jpg"
        else:
            filt = "PDF Document (*.pdf)"
            ext = ".pdf"

        path, _ = QFileDialog.getSaveFileName(self, "Export Map Layout", f"GeoStudio_Map{ext}", filt)
        if not path:
            return

        self.progress.show()
        self.progress.setRange(0, 0)
        QApplication.processEvents()

        try:
            w, h = self._get_target_pixel_size()
            dpi = self._get_dpi()

            canvas = self.mw.map_canvas.canvas
            dest_crs = canvas.mapSettings().destinationCrs()
            extent = canvas.extent()
            layers = [l for l in QgsProject.instance().mapLayers().values() if l.isValid()]

            # Configure MapSettings
            settings = QgsMapSettings()
            settings.setLayers(layers)
            settings.setDestinationCrs(dest_crs)
            settings.setExtent(extent)
            settings.setOutputSize(QSize(w, h))
            settings.setOutputDpi(dpi)
            settings.setBackgroundColor(QColor("#ffffff"))

            # Render map to QImage
            image = QImage(QSize(w, h), QImage.Format_ARGB32_Premultiplied)
            image.fill(QColor("#ffffff"))

            p = QPainter(image)
            p.setRenderHint(QPainter.Antialiasing)

            job = QgsMapRendererCustomPainterJob(settings, p)
            job.start()
            job.waitForFinished()

            # ── Draw Overlays (Title, North Arrow, Scale Bar) ──
            if self.chk_title.isChecked() and self.txt_title.text().strip():
                self._draw_title_overlay(p, w, h, self.txt_title.text().strip())

            if self.chk_north_arrow.isChecked():
                self._draw_north_arrow_overlay(p, w, h)

            if self.chk_scalebar.isChecked():
                self._draw_scalebar_overlay(p, w, h, extent, dest_crs)

            if self.chk_border.isChecked():
                p.setPen(QPen(QColor("#0f172a"), max(2, int(w / 1000))))
                p.setBrush(Qt.NoBrush)
                p.drawRect(0, 0, w - 1, h - 1)

            p.end()

            # Save file
            if ext == ".pdf":
                from PyQt5.QtGui import QPdfWriter
                from PyQt5.QtCore import QSizeF
                writer = QPdfWriter(path)
                writer.setResolution(dpi)
                writer.setPageSizeMM(QSizeF(w * 25.4 / dpi, h * 25.4 / dpi))
                pdf_p = QPainter(writer)
                pdf_p.drawImage(0, 0, image)
                pdf_p.end()
            else:
                image.save(path)

            self.progress.hide()
            self.mw.geo_status.showMessage(f"Map successfully exported to {os.path.basename(path)}", 5000)

            reply = QMessageBox.information(
                self,
                "Export Complete",
                f"Map layout successfully exported to:\n{path}\n\nWould you like to open the exported file?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                os.startfile(path)
            self.accept()

        except Exception as e:
            self.progress.hide()
            QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting map:\n{e}")

    def _draw_title_overlay(self, painter, w, h, title):
        title_font_size = max(12, int(h / 36))
        painter.setFont(QFont("Segoe UI", title_font_size, QFont.Bold))
        margin = int(w * 0.02)
        box_h = int(title_font_size * 2.2)

        # Background banner
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawRoundedRect(QRectF(margin, margin, w * 0.45, box_h), 6, 6)

        # Border
        painter.setPen(QPen(QColor("#cbd5e1"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(margin, margin, w * 0.45, box_h), 6, 6)

        # Title text
        painter.setPen(QColor("#0f172a"))
        painter.drawText(QRectF(margin + 12, margin, w * 0.45 - 24, box_h), Qt.AlignVCenter | Qt.AlignLeft, title)

    def _draw_north_arrow_overlay(self, painter, w, h):
        size = max(40, int(w * 0.04))
        margin_x = w - size - int(w * 0.03)
        margin_y = int(h * 0.03)

        # Background circle
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawEllipse(QRectF(margin_x, margin_y, size, size))

        cx = margin_x + size / 2.0
        cy = margin_y + size / 2.0

        # Draw North Star / Arrow
        painter.setPen(Qt.NoPen)
        # North pointer (dark)
        painter.setBrush(QBrush(QColor("#0f172a")))
        poly_n = [QPointF(cx, margin_y + size * 0.15), QPointF(cx, cy), QPointF(cx - size * 0.18, cy + size * 0.1)]
        painter.drawPolygon(poly_n)

        # North pointer right (light)
        painter.setBrush(QBrush(QColor("#64748b")))
        poly_nr = [QPointF(cx, margin_y + size * 0.15), QPointF(cx, cy), QPointF(cx + size * 0.18, cy + size * 0.1)]
        painter.drawPolygon(poly_nr)

        # "N" label
        painter.setFont(QFont("Segoe UI", max(8, int(size * 0.22)), QFont.Bold))
        painter.setPen(QColor("#0f172a"))
        painter.drawText(QRectF(margin_x, margin_y + size * 0.02, size, size * 0.3), Qt.AlignCenter, "N")

    def _draw_scalebar_overlay(self, painter, w, h, extent, crs):
        da = QgsDistanceArea()
        da.setSourceCrs(crs, QgsProject.instance().transformContext())
        da.setEllipsoid("WGS84")

        is_geographic = crs.isGeographic() or (abs(extent.center().x()) <= 180.0 and abs(extent.center().y()) <= 90.0)
        if is_geographic:
            lat = math.radians(extent.center().y())
            meters_per_deg_lon = 111320.0 * math.cos(lat)
            ground_width_m = extent.width() * meters_per_deg_lon
        else:
            from qgis.core import QgsPointXY
            p1 = extent.center()
            p2 = QgsPointXY(p1.x() + extent.width(), p1.y())
            ground_width_m = float(da.measureLine(p1, p2))

        # Estimate scale bar for 20% of map width
        bar_len_px = int(w * 0.20)
        bar_len_m = ground_width_m * 0.20

        if bar_len_m >= 1000:
            val = round(bar_len_m / 1000, 1)
            lbl = f"{val} km"
        else:
            val = round(bar_len_m, -1)
            lbl = f"{int(val)} m"

        margin_x = int(w * 0.03)
        margin_y = h - int(h * 0.06)

        # Background box
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawRoundedRect(QRectF(margin_x - 10, margin_y - 20, bar_len_px + 20, 32), 4, 4)

        # Scale line
        painter.setPen(QPen(QColor("#0f172a"), 3))
        painter.drawLine(margin_x, margin_y, margin_x + bar_len_px, margin_y)
        painter.drawLine(margin_x, margin_y - 5, margin_x, margin_y + 5)
        painter.drawLine(margin_x + bar_len_px, margin_y - 5, margin_x + bar_len_px, margin_y + 5)

        # Scale text
        painter.setFont(QFont("Segoe UI", max(8, int(h / 70)), QFont.Bold))
        painter.setPen(QColor("#0f172a"))
        painter.drawText(QRectF(margin_x, margin_y - 20, bar_len_px, 16), Qt.AlignCenter, lbl)
