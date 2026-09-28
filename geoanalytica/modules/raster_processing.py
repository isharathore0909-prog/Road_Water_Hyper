# -*- coding: utf-8 -*-
"""
GeoAnalytica - Raster & DEM Processing Module
Slope, Aspect, Hillshade, Contours, Reclassify, Focal Statistics.
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QPushButton, QLabel,
    QComboBox, QDoubleSpinBox, QGroupBox, QSpinBox,
    QMessageBox, QProgressBar, QHBoxLayout, QCheckBox
)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer
import processing


STYLE = """
    QGroupBox { font-weight: bold; color: #ffcc80; border: 1px solid #37474f; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
    QGroupBox::title { subcontrol-origin: margin; left: 8px; top: -6px; }
    QPushButton { background: #e65100; color: white; border: none; border-radius: 4px; padding: 6px 12px; }
    QPushButton:hover { background: #f4511e; }
    QPushButton:pressed { background: #bf360c; }
    QComboBox, QSpinBox, QDoubleSpinBox { background: #263238; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; padding: 3px; }
    QLabel { color: #b0bec5; }
    QWidget { background: #263238; }
    QProgressBar { border: 1px solid #37474f; border-radius: 3px; background: #1e272c; }
    QProgressBar::chunk { background: #e65100; }
    QCheckBox { color: #b0bec5; }
"""


class RasterProcessingWidget(QWidget):
    """Raster & DEM Processing: slope, aspect, hillshade, contours, reclassify, focal stats."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setStyleSheet(STYLE)
        self._init_ui()
        self._refresh_layers()
        QgsProject.instance().layersAdded.connect(self._refresh_layers)
        QgsProject.instance().layersRemoved.connect(self._refresh_layers)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- Input Raster ---
        input_box = QGroupBox("Input Raster Layer")
        input_form = QFormLayout()
        self.raster_combo = QComboBox()
        self.band_combo = QComboBox()
        input_form.addRow("Raster:", self.raster_combo)
        input_form.addRow("Band:", self.band_combo)
        self.raster_combo.currentIndexChanged.connect(self._on_raster_changed)
        input_box.setLayout(input_form)
        layout.addWidget(input_box)

        # --- DEM Analysis ---
        dem_box = QGroupBox("DEM Terrain Analysis")
        dem_layout = QVBoxLayout()

        z_form = QFormLayout()
        self.z_factor = QDoubleSpinBox()
        self.z_factor.setRange(0.001, 100.0)
        self.z_factor.setValue(1.0)
        self.z_factor.setDecimals(3)
        z_form.addRow("Z Factor:", self.z_factor)
        dem_layout.addLayout(z_form)

        ops = [
            ("🏔 Slope",      self.run_slope),
            ("🧭 Aspect",     self.run_aspect),
            ("💡 Hillshade",  self.run_hillshade),
            ("📏 Roughness",  self.run_roughness),
            ("🌊 TWI",        self.run_twi),
        ]
        for label, func in ops:
            btn = QPushButton(label)
            btn.clicked.connect(func)
            dem_layout.addWidget(btn)

        dem_box.setLayout(dem_layout)
        layout.addWidget(dem_box)

        # --- Contours ---
        contour_box = QGroupBox("Contour Lines")
        contour_form = QFormLayout()
        self.contour_interval = QDoubleSpinBox()
        self.contour_interval.setRange(1, 1000)
        self.contour_interval.setValue(50)
        self.contour_interval.setSuffix(" m")
        contour_form.addRow("Interval:", self.contour_interval)
        btn_contour = QPushButton("📈 Generate Contours")
        btn_contour.clicked.connect(self.run_contours)
        contour_form.addRow(btn_contour)
        contour_box.setLayout(contour_form)
        layout.addWidget(contour_box)

        # --- Raster Calculator ---
        calc_box = QGroupBox("Raster Utilities")
        calc_layout = QVBoxLayout()
        btn_stats = QPushButton("📊 Raster Statistics")
        btn_stats.clicked.connect(self.show_raster_stats)
        btn_focal = QPushButton("🔵 Focal Mean (Smooth)")
        btn_focal.clicked.connect(self.run_focal_mean)
        btn_reproject = QPushButton("🗺 Reproject Raster")
        btn_reproject.clicked.connect(self.run_reproject)
        calc_layout.addWidget(btn_stats)
        calc_layout.addWidget(btn_focal)
        calc_layout.addWidget(btn_reproject)
        calc_box.setLayout(calc_layout)
        layout.addWidget(calc_box)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Ready")
        layout.addWidget(self.progress)

        layout.addStretch()
        self.setLayout(layout)

    def _refresh_layers(self):
        layers = [
            l for l in QgsProject.instance().mapLayers().values()
            if l.type() == QgsMapLayer.RasterLayer
        ]
        current = self.raster_combo.currentText()
        self.raster_combo.clear()
        self.raster_combo.addItem("-- None --", None)
        for l in layers:
            self.raster_combo.addItem(l.name(), l.id())
        idx = self.raster_combo.findText(current)
        if idx >= 0:
            self.raster_combo.setCurrentIndex(idx)

    def _on_raster_changed(self):
        self.band_combo.clear()
        layer = self._get_raster()
        if layer:
            for b in range(1, layer.bandCount() + 1):
                self.band_combo.addItem(f"Band {b}: {layer.bandName(b)}", b)

    def _get_raster(self):
        layer_id = self.raster_combo.currentData()
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def _run(self, algo, params, name):
        self.progress.setFormat(f"Running {name}...")
        self.progress.setValue(20)
        try:
            result = processing.run(algo, params)
            output = result.get("OUTPUT") or result.get("output")
            if output:
                if isinstance(output, str):
                    from qgis.core import QgsVectorLayer
                    if output.endswith(".shp") or "memory:" in output or "??" in output:
                        l = QgsVectorLayer(output, name, "ogr")
                    else:
                        l = QgsRasterLayer(output, name)
                    if l.isValid():
                        QgsProject.instance().addMapLayer(l)
                elif hasattr(output, "isValid"):
                    output.setName(name)
                    QgsProject.instance().addMapLayer(output)
            self.progress.setValue(100)
            self.progress.setFormat(f"✓ {name} done")
            self.iface.messageBar().pushSuccess("GeoAnalytica", f"{name} completed!")
        except Exception as e:
            self.progress.setFormat("Error")
            QMessageBox.critical(self, "Error", str(e))

    def run_slope(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "SCALE": self.z_factor.value(), "AS_PERCENT": False,
                  "COMPUTE_EDGES": False, "ZEVENBERGEN": False, "OUTPUT": "TEMPORARY_OUTPUT"}
        self._run("native:slope", params, f"{layer.name()}_slope")

    def run_aspect(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "TRIG_ANGLE": False, "ZERO_FLAT": False,
                  "COMPUTE_EDGES": False, "ZEVENBERGEN": False, "OUTPUT": "TEMPORARY_OUTPUT"}
        self._run("native:aspect", params, f"{layer.name()}_aspect")

    def run_hillshade(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "Z_FACTOR": self.z_factor.value(),
                  "SCALE": 1.0, "AZIMUTH": 315, "ALTITUDE": 45,
                  "COMPUTE_EDGES": False, "ZEVENBERGEN": False,
                  "MULTIDIRECTIONAL": False, "OUTPUT": "TEMPORARY_OUTPUT"}
        self._run("native:hillshade", params, f"{layer.name()}_hillshade")

    def run_roughness(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "COMPUTE_EDGES": False, "OUTPUT": "TEMPORARY_OUTPUT"}
        self._run("native:roughness", params, f"{layer.name()}_roughness")

    def run_twi(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        # SAGA TWI if available
        try:
            params = {"DEM": layer, "TWI": "TEMPORARY_OUTPUT"}
            self._run("saga:topographicwetnessindextwi", params, f"{layer.name()}_TWI")
        except Exception:
            QMessageBox.information(self, "TWI", "SAGA provider not available. Please install SAGA in QGIS.")

    def run_contours(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "INTERVAL": self.contour_interval.value(),
                  "FIELD_NAME": "ELEV", "CREATE_3D": False, "IGNORE_NODATA": False,
                  "NODATA": None, "OFFSET": 0, "OUTPUT": "memory:"}
        self._run("gdal:contour", params, f"{layer.name()}_contours")

    def show_raster_stats(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        stats_lines = [f"Raster: {layer.name()}", f"CRS: {layer.crs().authid()}",
                       f"Bands: {layer.bandCount()}", f"Size: {layer.width()} x {layer.height()} px",
                       f"Pixel size: {layer.rasterUnitsPerPixelX():.6f} x {layer.rasterUnitsPerPixelY():.6f}",
                       ""]
        for b in range(1, min(layer.bandCount() + 1, 11)):
            provider = layer.dataProvider()
            stats = provider.bandStatistics(b)
            stats_lines.append(
                f"Band {b} ({layer.bandName(b)}):\n"
                f"  Min: {stats.minimumValue:.4f}  Max: {stats.maximumValue:.4f}\n"
                f"  Mean: {stats.mean:.4f}  StdDev: {stats.stdDev:.4f}"
            )
        QMessageBox.information(self, "Raster Statistics", "\n".join(stats_lines))

    def run_focal_mean(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "BAND": 1, "NEIGHBORHOOD": 0, "NEIGHBORHOOD_SIZE": 3,
                  "KERNEL_RADIUS": 1, "PIXEL_SIZE": 0, "OUTPUT_TYPE": 5,
                  "OUTPUT": "TEMPORARY_OUTPUT"}
        try:
            self._run("native:focalstatistics", params, f"{layer.name()}_focal_mean")
        except Exception:
            QMessageBox.information(self, "Focal Mean", "Focal statistics not available in this QGIS build.")

    def run_reproject(self):
        layer = self._get_raster()
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return
        params = {"INPUT": layer, "TARGET_CRS": "EPSG:4326",
                  "RESAMPLING": 0, "NODATA": None, "TARGET_RESOLUTION": None,
                  "OPTIONS": "", "DATA_TYPE": 0, "TARGET_EXTENT": None,
                  "TARGET_EXTENT_CRS": None, "MULTITHREADING": False,
                  "EXTRA": "", "OUTPUT": "TEMPORARY_OUTPUT"}
        self._run("gdal:warpreproject", params, f"{layer.name()}_WGS84")
