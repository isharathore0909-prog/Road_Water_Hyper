# -*- coding: utf-8 -*-
"""
GeoAnalytica - Satellite & Hyperspectral Imagery Module
NDVI, EVI, SAVI, NDWI, NDBI, Band Math, Spectral Profiles,
False Color Composites, PCA, Hyperspectral band selection.
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QMessageBox, QProgressBar, QTabWidget, QListWidget,
    QListWidgetItem, QCheckBox, QLineEdit, QSplitter
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont
from qgis.core import (
    QgsProject, QgsMapLayer, QgsRasterLayer, QgsRasterCalculator,
    QgsRasterCalculatorEntry, QgsContrastEnhancement,
    QgsRasterBandStats, QgsMultiBandColorRenderer,
    QgsSingleBandPseudoColorRenderer, QgsColorRampShader
)
import processing


STYLE = """
    QGroupBox { font-weight: bold; color: #ce93d8; border: 1px solid #37474f; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
    QGroupBox::title { subcontrol-origin: margin; left: 8px; top: -6px; }
    QPushButton { background: #6a1b9a; color: white; border: none; border-radius: 4px; padding: 6px 12px; }
    QPushButton:hover { background: #7b1fa2; }
    QPushButton:pressed { background: #4a148c; }
    QComboBox, QSpinBox, QDoubleSpinBox { background: #263238; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; padding: 3px; }
    QLabel { color: #b0bec5; }
    QWidget { background: #263238; }
    QProgressBar { border: 1px solid #37474f; border-radius: 3px; background: #1e272c; }
    QProgressBar::chunk { background: #6a1b9a; }
    QTextEdit { background: #1e272c; color: #e0e0e0; border: 1px solid #37474f; font-family: monospace; font-size: 10px; }
    QListWidget { background: #1e272c; color: #cfd8dc; border: 1px solid #37474f; }
    QListWidget::item:selected { background: #6a1b9a; }
    QLineEdit { background: #263238; color: #cfd8dc; border: 1px solid #37474f; border-radius: 3px; padding: 3px; }
    QCheckBox { color: #b0bec5; }
"""


class SatelliteHyperspectralWidget(QWidget):
    """
    Satellite & Hyperspectral Analysis:
    - Spectral indices (NDVI, EVI, SAVI, NDWI, NDBI, NBR)
    - Custom band math (raster calculator)
    - False color composite rendering
    - Spectral profile extraction
    - Band selection for hyperspectral data
    - PCA (via SAGA/GDAL)
    """

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
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Inner tabs
        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet("""
            QTabBar::tab { background: #1e272c; color: #90a4ae; padding: 4px 8px; font-size: 10px; }
            QTabBar::tab:selected { background: #6a1b9a; color: white; font-weight: bold; }
        """)

        inner_tabs.addTab(self._build_indices_tab(),   "📊 Indices")
        inner_tabs.addTab(self._build_bandmath_tab(),   "∑ Band Math")
        inner_tabs.addTab(self._build_composite_tab(), "🎨 Composite")
        inner_tabs.addTab(self._build_hyperspectral_tab(), "🌈 Hyperspectral")

        layout.addWidget(inner_tabs)
        self.setLayout(layout)

    # ================================================================
    # TAB 1: Spectral Indices
    # ================================================================
    def _build_indices_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Raster input
        form = QFormLayout()
        self.idx_raster_combo = QComboBox()
        form.addRow("Raster:", self.idx_raster_combo)
        self.idx_raster_combo.currentIndexChanged.connect(self._update_index_bands)

        self.idx_nir_band = QSpinBox(); self.idx_nir_band.setRange(1, 999); self.idx_nir_band.setValue(4)
        self.idx_red_band = QSpinBox(); self.idx_red_band.setRange(1, 999); self.idx_red_band.setValue(3)
        self.idx_green_band = QSpinBox(); self.idx_green_band.setRange(1, 999); self.idx_green_band.setValue(2)
        self.idx_swir1_band = QSpinBox(); self.idx_swir1_band.setRange(1, 999); self.idx_swir1_band.setValue(5)
        self.idx_swir2_band = QSpinBox(); self.idx_swir2_band.setRange(1, 999); self.idx_swir2_band.setValue(6)

        form.addRow("NIR Band #:", self.idx_nir_band)
        form.addRow("Red Band #:", self.idx_red_band)
        form.addRow("Green Band #:", self.idx_green_band)
        form.addRow("SWIR1 Band #:", self.idx_swir1_band)
        form.addRow("SWIR2 Band #:", self.idx_swir2_band)
        layout.addLayout(form)

        # Soil adj factor for SAVI
        savi_row = QHBoxLayout()
        savi_row.addWidget(QLabel("SAVI L factor:"))
        self.savi_l = QDoubleSpinBox(); self.savi_l.setRange(0, 1); self.savi_l.setValue(0.5); self.savi_l.setSingleStep(0.1)
        savi_row.addWidget(self.savi_l)
        layout.addLayout(savi_row)

        # Index buttons
        indices = [
            ("🌿 NDVI",   "(NIR-Red)/(NIR+Red)", self.run_ndvi),
            ("🌾 EVI",    "2.5*(NIR-Red)/(NIR+6*Red-7.5*Blue+1)", self.run_evi),
            ("🌱 SAVI",   "((NIR-Red)/(NIR+Red+L))*(1+L)", self.run_savi),
            ("💧 NDWI",   "(Green-NIR)/(Green+NIR)", self.run_ndwi),
            ("🏙 NDBI",   "(SWIR1-NIR)/(SWIR1+NIR)", self.run_ndbi),
            ("🔥 NBR",    "(NIR-SWIR2)/(NIR+SWIR2)", self.run_nbr),
            ("❄ NDSI",    "(Green-SWIR1)/(Green+SWIR1)", self.run_ndsi),
        ]

        box = QGroupBox("Spectral Indices")
        box_layout = QVBoxLayout()
        for label, formula, func in indices:
            row = QHBoxLayout()
            btn = QPushButton(label)
            btn.setToolTip(formula)
            btn.clicked.connect(func)
            fl = QLabel(formula)
            fl.setStyleSheet("color: #78909c; font-size: 9px;")
            fl.setWordWrap(True)
            row.addWidget(btn, 1)
            row.addWidget(fl, 2)
            box_layout.addLayout(row)
        box.setLayout(box_layout)
        layout.addWidget(box)

        self.idx_progress = QProgressBar(); self.idx_progress.setRange(0, 100)
        self.idx_progress.setFormat("Ready")
        layout.addWidget(self.idx_progress)

        layout.addStretch()
        return widget

    # ================================================================
    # TAB 2: Band Math
    # ================================================================
    def _build_bandmath_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        hint = QLabel(
            "Enter a formula using QGIS Raster Calculator syntax.\n"
            "Example:  \"layer@1\" / \"layer@2\"  or  (\"dem@1\" - \"dem@1\") / 2"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #78909c; font-size: 10px;")
        layout.addWidget(hint)

        form = QFormLayout()
        self.bm_raster_combo = QComboBox()
        form.addRow("Reference Layer:", self.bm_raster_combo)
        layout.addLayout(form)

        self.formula_edit = QTextEdit()
        self.formula_edit.setPlaceholderText('e.g. ("Landsat@4" - "Landsat@3") / ("Landsat@4" + "Landsat@3")')
        self.formula_edit.setFixedHeight(80)
        layout.addWidget(QLabel("Formula:"))
        layout.addWidget(self.formula_edit)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Output name:"))
        self.bm_output_name = QLineEdit("band_math_result")
        name_row.addWidget(self.bm_output_name)
        layout.addLayout(name_row)

        btn_run = QPushButton("▶ Run Band Math")
        btn_run.clicked.connect(self.run_band_math)
        layout.addWidget(btn_run)

        self.bm_log = QTextEdit()
        self.bm_log.setReadOnly(True)
        self.bm_log.setFixedHeight(100)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.bm_log)

        layout.addStretch()
        return widget

    # ================================================================
    # TAB 3: False Color Composite
    # ================================================================
    def _build_composite_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        form = QFormLayout()
        self.comp_raster_combo = QComboBox()
        form.addRow("Raster:", self.comp_raster_combo)

        self.comp_r = QSpinBox(); self.comp_r.setRange(1, 999); self.comp_r.setValue(4)
        self.comp_g = QSpinBox(); self.comp_g.setRange(1, 999); self.comp_g.setValue(3)
        self.comp_b = QSpinBox(); self.comp_b.setRange(1, 999); self.comp_b.setValue(2)

        form.addRow("Red channel (band #):", self.comp_r)
        form.addRow("Green channel (band #):", self.comp_g)
        form.addRow("Blue channel (band #):", self.comp_b)
        layout.addLayout(form)

        presets_box = QGroupBox("Quick Presets")
        presets_layout = QVBoxLayout()
        presets = [
            ("🌿 Vegetation (NIR/Red/Green)",   4, 3, 2),
            ("🔥 Urban (SWIR2/SWIR1/Red)",       7, 5, 4),
            ("💧 Water (Green/NIR/SWIR1)",        2, 4, 5),
            ("🌾 Agriculture (SWIR1/NIR/Blue)",   5, 4, 1),
            ("🏔 Geology (SWIR2/SWIR1/Blue)",     7, 5, 2),
        ]
        for label, r, g, b in presets:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, rv=r, gv=g, bv=b: self._apply_preset(rv, gv, bv))
            presets_layout.addWidget(btn)
        presets_box.setLayout(presets_layout)
        layout.addWidget(presets_box)

        btn_apply = QPushButton("🎨 Apply Composite")
        btn_apply.clicked.connect(self.apply_composite)
        layout.addWidget(btn_apply)

        layout.addStretch()
        return widget

    # ================================================================
    # TAB 4: Hyperspectral
    # ================================================================
    def _build_hyperspectral_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        form = QFormLayout()
        self.hyp_raster_combo = QComboBox()
        form.addRow("Hyperspectral Raster:", self.hyp_raster_combo)
        layout.addLayout(form)

        info_box = QGroupBox("Band Information")
        info_layout = QVBoxLayout()
        self.band_list = QListWidget()
        self.band_list.setFixedHeight(120)
        btn_refresh_bands = QPushButton("🔄 Refresh Bands")
        btn_refresh_bands.clicked.connect(self._load_band_list)
        info_layout.addWidget(self.band_list)
        info_layout.addWidget(btn_refresh_bands)
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)

        ops_box = QGroupBox("Hyperspectral Operations")
        ops_layout = QVBoxLayout()

        btn_pca = QPushButton("📉 PCA (Principal Component Analysis)")
        btn_pca.clicked.connect(self.run_pca)
        btn_pca.setToolTip("Run PCA on all bands to reduce dimensionality")

        btn_mnf = QPushButton("🔷 MNF Transform (Minimum Noise Fraction)")
        btn_mnf.clicked.connect(self.show_mnf_info)

        btn_profile = QPushButton("📈 Extract Spectral Profile at Point")
        btn_profile.clicked.connect(self.extract_spectral_profile)

        btn_band_stats = QPushButton("📊 All-band Statistics")
        btn_band_stats.clicked.connect(self.show_all_band_stats)

        ops_layout.addWidget(btn_pca)
        ops_layout.addWidget(btn_mnf)
        ops_layout.addWidget(btn_profile)
        ops_layout.addWidget(btn_band_stats)
        ops_box.setLayout(ops_layout)
        layout.addWidget(ops_box)

        self.hyp_log = QTextEdit()
        self.hyp_log.setReadOnly(True)
        self.hyp_log.setFixedHeight(120)
        layout.addWidget(QLabel("Output / Log:"))
        layout.addWidget(self.hyp_log)

        layout.addStretch()
        return widget

    # ================================================================
    # Helper: Refresh layer combos
    # ================================================================
    def _refresh_layers(self):
        rasters = [
            l for l in QgsProject.instance().mapLayers().values()
            if l.type() == QgsMapLayer.RasterLayer
        ]
        for combo in (
            self.idx_raster_combo, self.bm_raster_combo,
            self.comp_raster_combo, self.hyp_raster_combo
        ):
            current = combo.currentText()
            combo.clear()
            combo.addItem("-- None --", None)
            for l in rasters:
                combo.addItem(l.name(), l.id())
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _update_index_bands(self):
        layer = self._get_raster(self.idx_raster_combo)
        if layer:
            n = layer.bandCount()
            for spin in (self.idx_nir_band, self.idx_red_band, self.idx_green_band,
                         self.idx_swir1_band, self.idx_swir2_band):
                spin.setMaximum(n)

    def _get_raster(self, combo):
        layer_id = combo.currentData()
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def _load_band_list(self):
        layer = self._get_raster(self.hyp_raster_combo)
        if not layer:
            return
        self.band_list.clear()
        for b in range(1, layer.bandCount() + 1):
            stats = layer.dataProvider().bandStatistics(b, QgsRasterBandStats.Min | QgsRasterBandStats.Max | QgsRasterBandStats.Mean)
            item = QListWidgetItem(
                f"Band {b:3d}: {layer.bandName(b):<25}  "
                f"Min={stats.minimumValue:.3f}  Max={stats.maximumValue:.3f}  Mean={stats.mean:.3f}"
            )
            self.band_list.addItem(item)

    # ================================================================
    # Spectral Indices Implementation
    # ================================================================
    def _raster_calc(self, formula, layer, output_name, combos=None):
        """Run QGIS Raster Calculator with given formula."""
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return

        entries = []
        for b in range(1, layer.bandCount() + 1):
            entry = QgsRasterCalculatorEntry()
            entry.ref = f"{layer.name()}@{b}"
            entry.raster = layer
            entry.bandNumber = b
            entries.append(entry)

        extent = layer.extent()
        crs = layer.crs()
        cols = layer.width()
        rows = layer.height()

        import tempfile, os
        tmp = tempfile.mktemp(suffix=".tif")

        calc = QgsRasterCalculator(formula, tmp, "GTiff",
                                   extent, crs, cols, rows, entries)
        result_code = calc.processCalculation()

        if result_code == QgsRasterCalculator.Success:
            result_layer = QgsRasterLayer(tmp, output_name)
            if result_layer.isValid():
                # Apply pseudocolor (blue=low, red=high)
                self._apply_pseudocolor(result_layer)
                QgsProject.instance().addMapLayer(result_layer)
                self.iface.messageBar().pushSuccess("GeoAnalytica", f"{output_name} computed!")
                return result_layer
        else:
            QMessageBox.critical(self, "Raster Calc Error",
                                 f"Raster Calculator failed (code {result_code}).\n"
                                 f"Check formula: {formula}")
        return None

    def _apply_pseudocolor(self, layer):
        """Apply a blue-green-yellow-red pseudocolor ramp to a single-band raster."""
        provider = layer.dataProvider()
        stats = provider.bandStatistics(1)
        min_val = stats.minimumValue
        max_val = stats.maximumValue

        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
        items = [
            QgsColorRampShader.ColorRampItem(min_val,         Qt.blue,   "Low"),
            QgsColorRampShader.ColorRampItem((min_val+max_val)/2, Qt.yellow, "Mid"),
            QgsColorRampShader.ColorRampItem(max_val,         Qt.red,    "High"),
        ]
        color_ramp.setColorRampItemList(items)

        renderer = QgsSingleBandPseudoColorRenderer(provider, 1)
        renderer.setClassificationMin(min_val)
        renderer.setClassificationMax(max_val)
        renderer.setShader(color_ramp)
        layer.setRenderer(renderer)

    def run_ndvi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        n = self.idx_nir_band.value()
        r = self.idx_red_band.value()
        name = layer.name()
        formula = f'("{name}@{n}" - "{name}@{r}") / ("{name}@{n}" + "{name}@{r}")'
        self.idx_progress.setValue(30)
        self._raster_calc(formula, layer, f"{name}_NDVI")
        self.idx_progress.setValue(100); self.idx_progress.setFormat("✓ NDVI done")

    def run_evi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        n = self.idx_nir_band.value()
        r = self.idx_red_band.value()
        b = 1  # Blue
        name = layer.name()
        formula = (f'2.5 * ("{name}@{n}" - "{name}@{r}") / '
                   f'("{name}@{n}" + 6 * "{name}@{r}" - 7.5 * "{name}@{b}" + 1)')
        self._raster_calc(formula, layer, f"{name}_EVI")

    def run_savi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        n = self.idx_nir_band.value()
        r = self.idx_red_band.value()
        L = self.savi_l.value()
        name = layer.name()
        formula = (f'(("{name}@{n}" - "{name}@{r}") / '
                   f'("{name}@{n}" + "{name}@{r}" + {L})) * (1 + {L})')
        self._raster_calc(formula, layer, f"{name}_SAVI")

    def run_ndwi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        n = self.idx_nir_band.value()
        g = self.idx_green_band.value()
        name = layer.name()
        formula = f'("{name}@{g}" - "{name}@{n}") / ("{name}@{g}" + "{name}@{n}")'
        self._raster_calc(formula, layer, f"{name}_NDWI")

    def run_ndbi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        s1 = self.idx_swir1_band.value()
        n = self.idx_nir_band.value()
        name = layer.name()
        formula = f'("{name}@{s1}" - "{name}@{n}") / ("{name}@{s1}" + "{name}@{n}")'
        self._raster_calc(formula, layer, f"{name}_NDBI")

    def run_nbr(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        n = self.idx_nir_band.value()
        s2 = self.idx_swir2_band.value()
        name = layer.name()
        formula = f'("{name}@{n}" - "{name}@{s2}") / ("{name}@{n}" + "{name}@{s2}")'
        self._raster_calc(formula, layer, f"{name}_NBR")

    def run_ndsi(self):
        layer = self._get_raster(self.idx_raster_combo)
        if not layer: return
        g = self.idx_green_band.value()
        s1 = self.idx_swir1_band.value()
        name = layer.name()
        formula = f'("{name}@{g}" - "{name}@{s1}") / ("{name}@{g}" + "{name}@{s1}")'
        self._raster_calc(formula, layer, f"{name}_NDSI")

    # ================================================================
    # Band Math
    # ================================================================
    def run_band_math(self):
        layer = self._get_raster(self.bm_raster_combo)
        formula = self.formula_edit.toPlainText().strip()
        name = self.bm_output_name.text().strip() or "band_math_result"

        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a reference raster."); return
        if not formula:
            QMessageBox.warning(self, "No Formula", "Enter a raster calculator formula."); return

        result = self._raster_calc(formula, layer, name)
        if result:
            self.bm_log.append(f"✓ Success: {name}\nFormula: {formula}\n")
        else:
            self.bm_log.append(f"✗ Failed: {name}\nFormula: {formula}\n")

    # ================================================================
    # False Color Composite
    # ================================================================
    def _apply_preset(self, r, g, b):
        self.comp_r.setValue(r)
        self.comp_g.setValue(g)
        self.comp_b.setValue(b)

    def apply_composite(self):
        layer = self._get_raster(self.comp_raster_combo)
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a raster layer."); return

        r_band = self.comp_r.value()
        g_band = self.comp_g.value()
        b_band = self.comp_b.value()
        n_bands = layer.bandCount()

        if max(r_band, g_band, b_band) > n_bands:
            QMessageBox.warning(self, "Band Error",
                f"Layer only has {n_bands} bands. Adjust band numbers."); return

        renderer = QgsMultiBandColorRenderer(layer.dataProvider(), r_band, g_band, b_band)

        def stretch_band(band_no):
            stats = layer.dataProvider().bandStatistics(band_no, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
            ce = QgsContrastEnhancement(layer.dataProvider().dataType(band_no))
            ce.setMinimumValue(stats.minimumValue)
            ce.setMaximumValue(stats.maximumValue)
            ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
            return ce

        renderer.setRedContrastEnhancement(stretch_band(r_band))
        renderer.setGreenContrastEnhancement(stretch_band(g_band))
        renderer.setBlueContrastEnhancement(stretch_band(b_band))

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        self.iface.mapCanvas().refresh()
        self.iface.messageBar().pushSuccess(
            "GeoAnalytica",
            f"False color composite applied: R={r_band} G={g_band} B={b_band}"
        )

    # ================================================================
    # Hyperspectral
    # ================================================================
    def run_pca(self):
        layer = self._get_raster(self.hyp_raster_combo)
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a hyperspectral raster."); return
        try:
            params = {
                "INPUT": layer,
                "COMPONENTS": min(layer.bandCount(), 10),
                "OUTPUT": "TEMPORARY_OUTPUT"
            }
            result = processing.run("gdal:pcaanalysis", params)
            out = result.get("OUTPUT")
            if out:
                pca_layer = QgsRasterLayer(out, f"{layer.name()}_PCA")
                if pca_layer.isValid():
                    QgsProject.instance().addMapLayer(pca_layer)
                    self.hyp_log.append(f"✓ PCA completed: {layer.bandCount()} → 10 components\n")
                    self.iface.messageBar().pushSuccess("GeoAnalytica", "PCA completed!")
        except Exception as e:
            # GDAL PCA not always available, try OTB or fallback
            self.hyp_log.append(
                f"⚠ GDAL PCA not available in this QGIS build.\n"
                f"Error: {e}\n"
                f"Tip: Use OTB (Orfeo Toolbox) plugin for full PCA support on hyperspectral data.\n"
            )

    def show_mnf_info(self):
        QMessageBox.information(
            self, "MNF Transform",
            "Minimum Noise Fraction (MNF) transform requires the Orfeo Toolbox (OTB) plugin.\n\n"
            "To enable:\n"
            "1. Install OTB from https://www.orfeo-toolbox.org/\n"
            "2. Enable the OTB provider in QGIS Processing settings\n"
            "3. Use OTB > Dimensionality Reduction > MNF\n\n"
            "MNF is highly effective for hyperspectral image denoising and dimensionality reduction."
        )

    def extract_spectral_profile(self):
        layer = self._get_raster(self.hyp_raster_combo)
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a hyperspectral raster."); return
        self.hyp_log.append(
            "ℹ Click a point on the map canvas to extract spectral profile.\n"
            "Tip: Use the built-in QGIS 'Identify Features' tool (Ctrl+Shift+I) "
            "and select the raster layer to see all band values at a clicked point.\n"
        )
        self.iface.actionIdentify().trigger()

    def show_all_band_stats(self):
        layer = self._get_raster(self.hyp_raster_combo)
        if not layer:
            QMessageBox.warning(self, "No Raster", "Select a hyperspectral raster."); return
        self.hyp_log.clear()
        self.hyp_log.append(f"Band statistics for: {layer.name()}\n{'='*60}\n")
        for b in range(1, layer.bandCount() + 1):
            stats = layer.dataProvider().bandStatistics(b)
            self.hyp_log.append(
                f"Band {b:3d} | {layer.bandName(b):<20} | "
                f"Min={stats.minimumValue:10.4f} Max={stats.maximumValue:10.4f} "
                f"Mean={stats.mean:10.4f} Std={stats.stdDev:8.4f}\n"
            )
        self.hyp_log.append(f"\nTotal bands: {layer.bandCount()}\n")
