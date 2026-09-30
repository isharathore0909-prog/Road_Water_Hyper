# -*- coding: utf-8 -*-
"""
GeoStudio - DEM / Elevation Symbology & 3D Relief Dialog
Provides full Global Mapper & ArcGIS style elevation styling controls.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox, QCheckBox,
    QTabWidget, QWidget, QGroupBox, QSlider, QDialogButtonBox,
    QMessageBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient

from qgis.core import QgsProject, QgsRasterLayer, QgsMapLayer
from core.elevation_styler import ElevationStyler, ELEVATION_PRESETS


DIALOG_STYLE = """
    QDialog { background: #f8fafc; color: #1e293b; font-size: 12px; }
    QGroupBox { font-weight: bold; color: #1e40af; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 16px; padding-top: 6px; background: #ffffff; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 4px; background: #ffffff; color: #1e40af; }
    QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; border-radius: 6px; }
    QTabBar::tab { background: #f1f5f9; color: #64748b; padding: 7px 16px; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
    QTabBar::tab:selected { background: #ffffff; color: #2563eb; font-weight: bold; }
    QTabBar::tab:hover:!selected { background: #e2e8f0; color: #1e293b; }
    QPushButton { background: #2563eb; color: white; border: none; border-radius: 4px; padding: 7px 16px; font-weight: bold; }
    QPushButton:hover { background: #1d4ed8; }
    QPushButton:pressed { background: #1e40af; }
    QPushButton#secondaryBtn { background: #e2e8f0; color: #334155; font-weight: normal; border: 1px solid #cbd5e1; }
    QPushButton#secondaryBtn:hover { background: #cbd5e1; }
    QComboBox, QDoubleSpinBox { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 6px; }
    QLabel { color: #334155; }
    QCheckBox { color: #334155; spacing: 5px; }
    QSlider::groove:horizontal { border: 1px solid #cbd5e1; height: 6px; background: #f1f5f9; border-radius: 3px; }
    QSlider::sub-page:horizontal { background: #2563eb; border-radius: 3px; }
    QSlider::handle:horizontal { background: #2563eb; border: 1px solid #1d4ed8; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }
"""


class ColorRampPreviewWidget(QFrame):
    """Draws a smooth graphical preview of the selected elevation color ramp."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset_key = "GLOBAL_MAPPER_ATLAS"
        self.invert = False
        self.setFixedHeight(24)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 4px;")

    def set_preset(self, preset_key: str, invert: bool = False):
        self.preset_key = preset_key
        self.invert = invert
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        preset = ELEVATION_PRESETS.get(self.preset_key, ELEVATION_PRESETS["GLOBAL_MAPPER_ATLAS"])
        stops = preset["stops"]
        if self.invert:
            stops = list(reversed(stops))

        gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
        for stop_frac, hex_color, _ in stops:
            gradient.setColorAt(stop_frac, QColor(hex_color))

        painter.fillRect(rect, QBrush(gradient))
        painter.end()


class DEMElevationDialog(QDialog):
    """
    Dedicated dialog for Global Mapper / ArcGIS style DEM, DTM, and DSM elevation symbology.
    """

    def __init__(self, map_canvas=None, target_layer=None, parent=None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.target_layer = target_layer
        self.setWindowTitle("🏔 DEM / Elevation Symbology & 3D Relief")
        self.setMinimumWidth(560)
        self.setStyleSheet(DIALOG_STYLE)
        self._init_ui()
        self._populate_layers()

        if self.target_layer:
            idx = self.layer_combo.findData(self.target_layer.id())
            if idx >= 0:
                self.layer_combo.setCurrentIndex(idx)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ── Layer Selection & Quick Stats ─────────────────────
        top_group = QGroupBox("Elevation Layer Selection")
        top_form = QFormLayout()
        
        self.layer_combo = QComboBox()
        self.layer_combo.currentIndexChanged.connect(self._on_layer_changed)
        top_form.addRow("Target DEM/DTM/DSM:", self.layer_combo)

        self.stats_label = QLabel("Min: -- | Max: -- | Mean: -- | NoData: --")
        self.stats_label.setStyleSheet("color: #1e40af; font-size: 11px; font-weight: bold;")
        top_form.addRow("Statistics:", self.stats_label)

        top_group.setLayout(top_form)
        main_layout.addWidget(top_group)

        # ── Render Modes (Tabs) ───────────────────────────────
        self.tabs = QTabWidget()

        # Tab 1: Topographic / Elevation Colormap
        tab_topo = QWidget()
        layout_topo = QVBoxLayout(tab_topo)
        
        form_topo = QFormLayout()
        self.preset_combo = QComboBox()
        for key, pinfo in ELEVATION_PRESETS.items():
            self.preset_combo.addItem(pinfo["name"], key)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form_topo.addRow("Elevation Palette:", self.preset_combo)

        # Preview Widget
        self.ramp_preview = ColorRampPreviewWidget()
        form_topo.addRow("Color Ramp:", self.ramp_preview)

        # Range Override
        range_layout = QHBoxLayout()
        self.spin_min_val = QDoubleSpinBox()
        self.spin_min_val.setRange(-20000.0, 20000.0)
        self.spin_min_val.setDecimals(2)
        self.spin_min_val.setSuffix(" m")

        self.spin_max_val = QDoubleSpinBox()
        self.spin_max_val.setRange(-20000.0, 20000.0)
        self.spin_max_val.setDecimals(2)
        self.spin_max_val.setSuffix(" m")

        range_layout.addWidget(QLabel("Min:"))
        range_layout.addWidget(self.spin_min_val)
        range_layout.addWidget(QLabel("Max:"))
        range_layout.addWidget(self.spin_max_val)
        form_topo.addRow("Elevation Range:", range_layout)

        # Reset bounds buttons
        btn_row_bounds = QHBoxLayout()
        btn_cut_reset = QPushButton("Reset to 2%–98% Cut")
        btn_cut_reset.setObjectName("secondaryBtn")
        btn_cut_reset.clicked.connect(self._reset_to_cut)
        btn_full_reset = QPushButton("Reset to Full Min–Max")
        btn_full_reset.setObjectName("secondaryBtn")
        btn_full_reset.clicked.connect(self._reset_to_full)
        btn_row_bounds.addWidget(btn_cut_reset)
        btn_row_bounds.addWidget(btn_full_reset)
        form_topo.addRow("", btn_row_bounds)

        # Options
        self.chk_draped_relief = QCheckBox("💡 Blend with 3D Shaded Relief (Global Mapper 3D terrain shadows)")
        self.chk_draped_relief.setChecked(True)
        self.chk_invert = QCheckBox("Invert Colormap Colors")
        self.chk_invert.toggled.connect(self._on_preset_changed)
        self.chk_bilinear = QCheckBox("Smooth Bilinear Resampling (Anti-aliased terrain)")
        self.chk_bilinear.setChecked(True)
        form_topo.addRow("", self.chk_draped_relief)
        form_topo.addRow("", self.chk_invert)
        form_topo.addRow("", self.chk_bilinear)

        layout_topo.addLayout(form_topo)
        self.tabs.addTab(tab_topo, "🏔 Topographic Color Ramp")

        # Tab 2: 3D Hillshade (Shaded Relief)
        tab_hillshade = QWidget()
        layout_hillshade = QVBoxLayout(tab_hillshade)
        form_hillshade = QFormLayout()

        # Sun Azimuth (0 - 360)
        az_row = QHBoxLayout()
        self.slider_azimuth = QSlider(Qt.Horizontal)
        self.slider_azimuth.setRange(0, 360)
        self.slider_azimuth.setValue(315)
        self.spin_azimuth = QDoubleSpinBox()
        self.spin_azimuth.setRange(0.0, 360.0)
        self.spin_azimuth.setValue(315.0)
        self.spin_azimuth.setSuffix("°")
        self.slider_azimuth.valueChanged.connect(lambda v: self.spin_azimuth.setValue(float(v)))
        self.spin_azimuth.valueChanged.connect(lambda v: self.slider_azimuth.setValue(int(v)))
        az_row.addWidget(self.slider_azimuth, 1)
        az_row.addWidget(self.spin_azimuth)
        form_hillshade.addRow("Sun Azimuth (Lighting Angle):", az_row)

        # Sun Altitude (0 - 90)
        alt_row = QHBoxLayout()
        self.slider_altitude = QSlider(Qt.Horizontal)
        self.slider_altitude.setRange(0, 90)
        self.slider_altitude.setValue(45)
        self.spin_altitude = QDoubleSpinBox()
        self.spin_altitude.setRange(0.0, 90.0)
        self.spin_altitude.setValue(45.0)
        self.spin_altitude.setSuffix("°")
        self.slider_altitude.valueChanged.connect(lambda v: self.spin_altitude.setValue(float(v)))
        self.spin_altitude.valueChanged.connect(lambda v: self.slider_altitude.setValue(int(v)))
        alt_row.addWidget(self.slider_altitude, 1)
        alt_row.addWidget(self.spin_altitude)
        form_hillshade.addRow("Sun Altitude (Elevation Angle):", alt_row)

        # Vertical Exaggeration (Z Factor)
        z_row = QHBoxLayout()
        self.spin_z_factor = QDoubleSpinBox()
        self.spin_z_factor.setRange(0.0001, 100.0)
        self.spin_z_factor.setValue(1.0)
        self.spin_z_factor.setDecimals(4)
        z_row.addWidget(self.spin_z_factor)
        form_hillshade.addRow("Vertical Exaggeration (Z Factor):", z_row)

        self.chk_multidir = QCheckBox("Multi-Directional Hillshade (ArcGIS-style realistic multi-illumination)")
        self.chk_multidir.setChecked(True)
        form_hillshade.addRow("", self.chk_multidir)

        layout_hillshade.addLayout(form_hillshade)
        self.tabs.addTab(tab_hillshade, "💡 3D Hillshade Relief")

        # Tab 3: Grayscale Contrast Stretch
        tab_gray = QWidget()
        layout_gray = QVBoxLayout(tab_gray)
        form_gray = QFormLayout()

        self.gray_mode_combo = QComboBox()
        self.gray_mode_combo.addItem("Cumulative Cut (2% – 98%) [Recommended]", "cumulative_cut")
        self.gray_mode_combo.addItem("Exact Min to Max (Full range)", "min_max")
        form_gray.addRow("Contrast Algorithm:", self.gray_mode_combo)

        layout_gray.addLayout(form_gray)
        self.tabs.addTab(tab_gray, "🌓 High-Contrast Grayscale")

        main_layout.addWidget(self.tabs)

        # ── Buttons ───────────────────────────────────────────
        btn_layout = QHBoxLayout()
        
        btn_apply = QPushButton("⚡ Apply Now")
        btn_apply.clicked.connect(self.apply_style)

        btn_ok = QPushButton("✓ OK")
        btn_ok.clicked.connect(self._on_ok)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

    def _populate_layers(self):
        self.layer_combo.clear()
        layers = [
            l for l in QgsProject.instance().mapLayers().values()
            if l.type() == QgsMapLayer.RasterLayer
        ]
        if not layers:
            self.layer_combo.addItem("-- No Raster Layers in Project --", None)
            return

        for l in layers:
            is_dem = ElevationStyler.is_dem_or_elevation(l)
            prefix = "🏔 [DEM] " if is_dem else "🗺 "
            self.layer_combo.addItem(f"{prefix}{l.name()}", l.id())

    def _get_current_layer(self):
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def _on_layer_changed(self):
        layer = self._get_current_layer()
        if not layer:
            self.stats_label.setText("Min: -- | Max: -- | Mean: -- | NoData: --")
            return

        stats = ElevationStyler.get_valid_elevation_stats(layer, 1)
        if stats:
            nodata_str = f"{stats['nodata_val']}" if stats['has_nodata'] else "None"
            self.stats_label.setText(
                f"Min: {stats['min']:.1f} m | Max: {stats['max']:.1f} m | "
                f"Mean: {stats['mean']:.1f} m | StdDev: {stats['std_dev']:.1f} | NoData: {nodata_str}"
            )
            self.spin_min_val.setValue(stats["p2"])
            self.spin_max_val.setValue(stats["p98"])

    def _on_preset_changed(self):
        preset_key = self.preset_combo.currentData()
        self.ramp_preview.set_preset(preset_key, self.chk_invert.isChecked())

    def _reset_to_cut(self):
        layer = self._get_current_layer()
        if layer:
            stats = ElevationStyler.get_valid_elevation_stats(layer, 1)
            if stats:
                self.spin_min_val.setValue(stats["p2"])
                self.spin_max_val.setValue(stats["p98"])

    def _reset_to_full(self):
        layer = self._get_current_layer()
        if layer:
            stats = ElevationStyler.get_valid_elevation_stats(layer, 1)
            if stats:
                self.spin_min_val.setValue(stats["min"])
                self.spin_max_val.setValue(stats["max"])

    def apply_style(self):
        layer = self._get_current_layer()
        if not layer:
            QMessageBox.warning(self, "No Layer", "Please select a raster layer.")
            return

        curr_tab = self.tabs.currentIndex()

        if curr_tab == 0:
            # Topographic Color Ramp
            preset_key = self.preset_combo.currentData()
            min_val = self.spin_min_val.value()
            max_val = self.spin_max_val.value()
            invert = self.chk_invert.isChecked()
            bilinear = self.chk_bilinear.isChecked()
            use_draped = self.chk_draped_relief.isChecked()

            if use_draped:
                success = ElevationStyler.apply_draped_relief(
                    layer,
                    preset_key=preset_key,
                    band=1,
                    z_factor=1.5,
                    multidirectional=True
                )
            else:
                success = ElevationStyler.apply_elevation_colormap(
                    layer,
                    preset_key=preset_key,
                    band=1,
                    min_val=min_val,
                    max_val=max_val,
                    invert=invert,
                    enable_bilinear=bilinear
                )
        elif curr_tab == 1:
            # Hillshade
            azimuth = self.spin_azimuth.value()
            altitude = self.spin_altitude.value()
            z_factor = self.spin_z_factor.value()
            multidir = self.chk_multidir.isChecked()

            success = ElevationStyler.apply_hillshade(
                layer,
                band=1,
                z_factor=z_factor,
                azimuth=azimuth,
                altitude=altitude,
                multidirectional=multidir
            )
        else:
            # Grayscale Contrast
            mode = self.gray_mode_combo.currentData()
            success = ElevationStyler.apply_grayscale_contrast(
                layer,
                band=1,
                stretch_type=mode
            )

        if success and self.map_canvas:
            if hasattr(self.map_canvas, 'update_elevation_legend'):
                self.map_canvas.update_elevation_legend(layer)
            self.map_canvas.refresh_canvas()

    def _on_ok(self):
        self.apply_style()
        self.accept()
