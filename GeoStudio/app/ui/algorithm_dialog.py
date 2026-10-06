# -*- coding: utf-8 -*-
"""
GeoStudio - Universal QGIS Algorithm Execution Dialog
Clean parameter dialog with input parameters, output path, execution log, and help.
"""

import os
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QRadioButton, QButtonGroup, QTextEdit, QProgressBar,
    QPushButton, QTabWidget, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt

from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer

from core.gpu.cuda_detector import CudaDetector
from core.processing.algorithm_registry import AlgorithmDefinition
from core.style import MODULE_STYLE
from .algorithm_forms import build_parameters_form
from .algorithm_executor import AlgorithmExecutor


class QgisAlgorithmDialog(QDialog):
    """
    Universal QGIS Algorithm Parameter Dialog:
    - Real-time parameter forms
    - Optional processing engine selection for supported algorithms
    - [Parameters], [Log], [Help] tabs
    """

    def __init__(self, algo_def: AlgorithmDefinition, map_canvas=None, parent=None):
        super().__init__(parent)
        self.algo = algo_def
        self.map_canvas = map_canvas

        self.setWindowTitle(f"{self.algo.name}")
        self.setMinimumSize(560, 480)
        self.resize(600, 520)
        self.setStyleSheet(MODULE_STYLE)

        self._init_ui()
        self._refresh_layers()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Tabs (Parameters, Log, Help)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; background: #ffffff; border-radius: 6px; top: -1px; }
            QTabWidget::tab-bar { left: 8px; }
            QTabBar::tab { background: #f8fafc; color: #64748b; padding: 7px 18px; font-size: 11px; font-weight: 500; border: 1px solid #e2e8f0; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 4px; margin-top: 3px; min-width: 70px; }
            QTabBar::tab:selected { background: #ffffff; color: #0f172a; font-weight: 700; border-bottom: 1px solid #ffffff; margin-top: 0px; }
            QTabBar::tab:hover:!selected { background: #f1f5f9; color: #1e293b; }
        """)

        # Tab 1: Parameters
        self.param_tab = QWidget()
        param_layout = QVBoxLayout(self.param_tab)
        param_layout.setContentsMargins(14, 14, 14, 14)
        param_layout.setSpacing(10)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)

        build_parameters_form(self)
        param_layout.addLayout(self.form_layout)

        # Processing Engine Group Box (GPU/CPU Acceleration)
        if self.algo.supports_gpu:
            engine_box = QGroupBox("Processing Acceleration Engine")
            engine_box.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 8px; padding-top: 14px; background: #f8fafc; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #0f172a; }")
            engine_layout = QHBoxLayout(engine_box)
            engine_layout.setContentsMargins(10, 8, 10, 8)

            self.engine_btn_group = QButtonGroup(self)
            self.rb_auto = QRadioButton("⚡ Auto (Fastest)")
            self.rb_auto.setChecked(True)
            self.rb_gpu = QRadioButton("🚀 NVIDIA CUDA (GPU)")
            self.rb_cpu = QRadioButton("💻 Multi-Core CPU (C++ / OpenMP)")

            if not CudaDetector.is_cuda_available():
                self.rb_gpu.setEnabled(False)
                self.rb_gpu.setText("🚀 NVIDIA CUDA (Not Detected)")

            self.engine_btn_group.addButton(self.rb_auto)
            self.engine_btn_group.addButton(self.rb_gpu)
            self.engine_btn_group.addButton(self.rb_cpu)

            engine_layout.addWidget(self.rb_auto)
            engine_layout.addWidget(self.rb_gpu)
            engine_layout.addWidget(self.rb_cpu)
            engine_layout.addStretch()

            param_layout.addWidget(engine_box)
        else:
            self.rb_auto = QRadioButton()
            self.rb_auto.setChecked(True)
            self.rb_gpu = QRadioButton()
            self.rb_cpu = QRadioButton()

        # Output Path Selection
        out_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("[Create temporary layer]")
        btn_out_browse = QPushButton("Browse...")
        btn_out_browse.setMinimumWidth(85)
        btn_out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_edit)
        out_row.addWidget(btn_out_browse)

        self.form_layout.addRow("Save Output As:", out_row)

        from PyQt5.QtWidgets import QCheckBox
        self.open_output_cb = QCheckBox("Open output file after running algorithm")
        self.open_output_cb.setChecked(True)
        param_layout.addWidget(self.open_output_cb)
        param_layout.addStretch()

        self.tabs.addTab(self.param_tab, "Parameters")

        # Tab 2: Log
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        log_layout.setContentsMargins(12, 12, 12, 12)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("background: #0f172a; color: #f8fafc; font-family: Consolas, monospace; font-size: 11px; border-radius: 4px; padding: 8px;")
        log_layout.addWidget(self.log_edit)
        self.tabs.addTab(self.log_tab, "Log")

        # Tab 3: Help / Description
        self.help_tab = QWidget()
        help_layout = QVBoxLayout(self.help_tab)
        help_layout.setContentsMargins(14, 14, 14, 14)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_content = f"<h3>{self.algo.name}</h3><p><b>Group:</b> {self.algo.group}</p><p><b>Algorithm ID:</b> <code>{self.algo.algo_id}</code></p><p>{self.algo.description}</p>"
        help_text.setHtml(help_content)
        help_layout.addWidget(help_text)
        self.tabs.addTab(self.help_tab, "Help")

        main_layout.addWidget(self.tabs)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #cbd5e1; border-radius: 4px; background-color: #f1f5f9; text-align: center; font-size: 10px; font-weight: 600; color: #0f172a; } QProgressBar::chunk { background-color: #0284c7; border-radius: 3px; }")
        main_layout.addWidget(self.progress_bar)

        # Bottom Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_run = QPushButton("▶ Run")
        self.btn_run.setObjectName("blueBtn")
        self.btn_run.clicked.connect(self._run_algorithm)
        btn_box.addWidget(self.btn_run)

        self.btn_close = QPushButton("Close")
        self.btn_close.setObjectName("grayBtn")
        self.btn_close.clicked.connect(self.close)
        btn_box.addWidget(self.btn_close)

        main_layout.addLayout(btn_box)

    def _browse_mtl_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Landsat MTL Metadata File", "", "Landsat Metadata (*_MTL.txt);;Text Files (*.txt);;All Files (*.*)")
        if path:
            self.mtl_path_edit.setText(path)
            fn = os.path.basename(path).upper()
            if "LC08" in fn or "LC09" in fn or "LO08" in fn or "LO09" in fn:
                self.sensor_detect_lbl.setText("Auto-detected Sensor: <b>Landsat 8-9 OLI/TIRS</b> (11 Bands)")
            elif "LE07" in fn:
                self.sensor_detect_lbl.setText("Auto-detected Sensor: <b>Landsat 7 ETM+</b> (8 Bands)")
            elif "LT05" in fn or "LT04" in fn:
                self.sensor_detect_lbl.setText("Auto-detected Sensor: <b>Landsat 4-5 TM</b> (7 Bands)")
            else:
                self.sensor_detect_lbl.setText("Auto-detected Sensor: <b>Generic Landsat Scene</b>")

    def _browse_raw_img(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Unreferenced Image", "", "Raster Images (*.tif *.tiff *.jpg *.jpeg *.png *.bmp);;All Files (*.*)")
        if path:
            self.raw_img_edit.setText(path)

    def _refresh_layers(self):
        """Populate layers in raster / vector combo boxes."""
        layers = QgsProject.instance().mapLayers().values()
        if hasattr(self, "raster_combo"):
            self.raster_combo.clear()
            for lyr in layers:
                if isinstance(lyr, QgsRasterLayer) and lyr.isValid():
                    self.raster_combo.addItem(f"🗺 {lyr.name()}", lyr.id())

        if hasattr(self, "compare_dem_combo"):
            self.compare_dem_combo.clear()
            for lyr in layers:
                if isinstance(lyr, QgsRasterLayer) and lyr.isValid():
                    self.compare_dem_combo.addItem(f"🗺 {lyr.name()}", lyr.id())
            if self.compare_dem_combo.count() > 1:
                self.compare_dem_combo.setCurrentIndex(1)

        if hasattr(self, "vector_combo"):
            self.vector_combo.clear()
            for lyr in layers:
                if isinstance(lyr, QgsVectorLayer) and lyr.isValid():
                    self.vector_combo.addItem(f"📍 {lyr.name()}", lyr.id())

    def _set_observer_to_dem_center(self):
        if not hasattr(self, "raster_combo") or not hasattr(self, "observer_x_spin"):
            return
        r_id = self.raster_combo.currentData()
        if not r_id:
            return
        layer = QgsProject.instance().mapLayer(r_id)
        if layer and layer.isValid():
            ext = layer.extent()
            cx = ext.center().x()
            cy = ext.center().y()
            self.observer_x_spin.setValue(cx)
            self.observer_y_spin.setValue(cy)
            self.log(f"Observer set to DEM Center: ({cx:.2f}, {cy:.2f})")

    def _browse_output(self):
        suffix = "tif" if "raster" in self.algo.dialog_type or "terrain" in self.algo.dialog_type else "gpkg"
        filt = "GeoTIFF Raster (*.tif);;All Files (*.*)" if suffix == "tif" else "GeoPackage (*.gpkg);;Shapefile (*.shp);;All Files (*.*)"
        path, _ = QFileDialog.getSaveFileName(self, f"Save {self.algo.name} Output", "", filt)
        if path:
            self.output_edit.setText(path)

    def log(self, text: str):
        self.log_edit.append(text)
        QApplication.processEvents()

    def _run_algorithm(self):
        AlgorithmExecutor.execute(self)
