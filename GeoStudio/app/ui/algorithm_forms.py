# -*- coding: utf-8 -*-
"""
GeoStudio - Universal Algorithm Parameter Form Builders
Builds UI form fields dynamically based on dialog_type (terrain, hydro, contours, landsat, earthworks, etc.).
"""

from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QCheckBox, QPushButton
)


def build_parameters_form(dialog):
    """Construct parameter inputs dynamically on dialog.form_layout based on algorithm type."""
    dtype = dialog.algo.dialog_type

    # ── 1. Landsat Specialized Dialogs ──
    if dtype == "landsat_mtl":
        mtl_row = QHBoxLayout()
        dialog.mtl_path_edit = QLineEdit()
        dialog.mtl_path_edit.setPlaceholderText("Select Landsat *_MTL.txt metadata file...")
        btn_mtl = QPushButton("Browse...")
        btn_mtl.setMinimumWidth(85)
        btn_mtl.clicked.connect(dialog._browse_mtl_file)
        mtl_row.addWidget(dialog.mtl_path_edit)
        mtl_row.addWidget(btn_mtl)
        dialog.form_layout.addRow("MTL Metadata File:", mtl_row)

        dialog.calib_mode_combo = QComboBox()
        dialog.calib_mode_combo.addItems([
            "Top of Atmosphere (TOA) Reflectance + Sun Elevation Correction",
            "Top of Atmosphere (TOA) Spectral Radiance",
            "Digital Number (DN) Calibrated Output"
        ])
        dialog.form_layout.addRow("Calibration Mode:", dialog.calib_mode_combo)

        dialog.sensor_detect_lbl = QLabel("Auto-detected Sensor: <i>(Select MTL file to detect)</i>")
        dialog.sensor_detect_lbl.setStyleSheet("color: #0284c7; font-weight: 500;")
        dialog.form_layout.addRow("Sensor:", dialog.sensor_detect_lbl)

    elif dtype == "landsat_lst":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Landsat Scene / Thermal Band:", dialog.raster_combo)

        dialog.lst_method_combo = QComboBox()
        dialog.lst_method_combo.addItems([
            "Single-Channel Split-Window (Band 10/11) with FVC Emissivity",
            "Mono-Window Algorithm (Landsat 4/5/7 Band 6)",
            "Direct Brightness Temperature Conversion"
        ])
        dialog.form_layout.addRow("Retrieval Method:", dialog.lst_method_combo)

        dialog.temp_unit_combo = QComboBox()
        dialog.temp_unit_combo.addItems(["Celsius (°C)", "Kelvin (K)", "Fahrenheit (°F)"])
        dialog.form_layout.addRow("Temperature Unit:", dialog.temp_unit_combo)

    elif dtype == "landsat_generic":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Landsat Layer:", dialog.raster_combo)

    # ── 2. Terrain & Earthworks (Global Mapper) ──
    elif dtype == "terrain_profile":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input DEM Raster:", dialog.raster_combo)

        dialog.sample_step_spin = QDoubleSpinBox()
        dialog.sample_step_spin.setRange(1.0, 1000.0)
        dialog.sample_step_spin.setValue(10.0)
        dialog.sample_step_spin.setSuffix(" m")
        dialog.form_layout.addRow("Sampling Interval:", dialog.sample_step_spin)

    elif dtype == "terrain_cutfill":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Base / Before DEM:", dialog.raster_combo)

        dialog.compare_mode_combo = QComboBox()
        dialog.compare_mode_combo.addItems([
            "Compare Against Fixed Elevation Datum Plane",
            "Compare Against Second DEM Surface"
        ])
        dialog.form_layout.addRow("Calculation Mode:", dialog.compare_mode_combo)

        dialog.datum_height_spin = QDoubleSpinBox()
        dialog.datum_height_spin.setRange(-500.0, 9000.0)
        dialog.datum_height_spin.setValue(100.0)
        dialog.datum_height_spin.setSuffix(" m")
        dialog.form_layout.addRow("Datum Elevation (Plane):", dialog.datum_height_spin)

        dialog.compare_dem_combo = QComboBox()
        dialog.form_layout.addRow("Comparison / After DEM:", dialog.compare_dem_combo)
        dialog.compare_dem_combo.setEnabled(False)

        dialog.compare_mode_combo.currentIndexChanged.connect(
            lambda idx: (
                dialog.datum_height_spin.setEnabled(idx == 0),
                dialog.compare_dem_combo.setEnabled(idx == 1)
            )
        )

    elif dtype == "terrain_flood":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Elevation DEM:", dialog.raster_combo)

        dialog.water_level_spin = QDoubleSpinBox()
        dialog.water_level_spin.setRange(-500.0, 9000.0)
        dialog.water_level_spin.setValue(50.0)
        dialog.water_level_spin.setSuffix(" m")
        dialog.form_layout.addRow("Target Water Level:", dialog.water_level_spin)

    elif dtype == "raster_viewshed":
        dialog.raster_combo = QComboBox()
        dialog.raster_combo.currentIndexChanged.connect(dialog._set_observer_to_dem_center)
        dialog.form_layout.addRow("Input DEM Raster:", dialog.raster_combo)

        obs_coord_row = QHBoxLayout()
        dialog.observer_x_spin = QDoubleSpinBox()
        dialog.observer_x_spin.setRange(-20000000.0, 20000000.0)
        dialog.observer_x_spin.setDecimals(4)
        dialog.observer_y_spin = QDoubleSpinBox()
        dialog.observer_y_spin.setRange(-20000000.0, 20000000.0)
        dialog.observer_y_spin.setDecimals(4)
        obs_coord_row.addWidget(QLabel("X:"))
        obs_coord_row.addWidget(dialog.observer_x_spin)
        obs_coord_row.addWidget(QLabel("Y:"))
        obs_coord_row.addWidget(dialog.observer_y_spin)
        dialog.form_layout.addRow("Observer Position:", obs_coord_row)

        btn_set_center = QPushButton("🎯 Set Observer to Center of DEM")
        btn_set_center.setStyleSheet("background: #e2e8f0; color: #0f172a; font-weight: normal; padding: 2px 6px; font-size: 11px;")
        btn_set_center.clicked.connect(dialog._set_observer_to_dem_center)
        dialog.form_layout.addRow("", btn_set_center)

        dialog.observer_h_spin = QDoubleSpinBox()
        dialog.observer_h_spin.setRange(0.0, 500.0)
        dialog.observer_h_spin.setValue(1.8)
        dialog.observer_h_spin.setSuffix(" m")
        dialog.form_layout.addRow("Observer Height (Above Ground):", dialog.observer_h_spin)

        dialog.target_h_spin = QDoubleSpinBox()
        dialog.target_h_spin.setRange(0.0, 500.0)
        dialog.target_h_spin.setValue(0.0)
        dialog.target_h_spin.setSuffix(" m")
        dialog.form_layout.addRow("Target Object Height:", dialog.target_h_spin)

        dialog.max_dist_spin = QDoubleSpinBox()
        dialog.max_dist_spin.setRange(0.0, 1000000.0)
        dialog.max_dist_spin.setValue(5000.0)
        dialog.max_dist_spin.setSuffix(" m")
        dialog.max_dist_spin.setToolTip("Set to 0 for unlimited / full DEM extent")
        dialog.form_layout.addRow("Max Visibility Radius:", dialog.max_dist_spin)

    elif dtype == "terrain_georef":
        img_row = QHBoxLayout()
        dialog.raw_img_edit = QLineEdit()
        dialog.raw_img_edit.setPlaceholderText("Select unreferenced image/map...")
        btn_raw = QPushButton("Browse...")
        btn_raw.setMinimumWidth(85)
        btn_raw.clicked.connect(dialog._browse_raw_img)
        img_row.addWidget(dialog.raw_img_edit)
        img_row.addWidget(btn_raw)
        dialog.form_layout.addRow("Input Image:", img_row)

        dialog.transform_combo = QComboBox()
        dialog.transform_combo.addItems(["Thin Plate Spline (TPS - Local rubber-sheeting)", "Polynomial 2nd Order (Quadratic)", "Affine (1st Order - Rotation/Scale/Shift)"])
        dialog.form_layout.addRow("Transformation Method:", dialog.transform_combo)

    # ── 3. Spatial Interpolation (ArcGIS) ──
    elif dtype == "spatial_interp":
        dialog.vector_combo = QComboBox()
        dialog.form_layout.addRow("Sample Points Layer:", dialog.vector_combo)

        dialog.power_spin = QDoubleSpinBox()
        dialog.power_spin.setRange(0.5, 10.0)
        dialog.power_spin.setValue(2.0)
        dialog.form_layout.addRow("Power / Variogram Weight:", dialog.power_spin)

    # ── 4. Raster Terrain & Surface Analysis ──
    elif dtype == "raster_terrain":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Elevation DEM:", dialog.raster_combo)

        dialog.z_factor_spin = QDoubleSpinBox()
        dialog.z_factor_spin.setRange(0.0001, 1000.0)
        dialog.z_factor_spin.setValue(1.0)
        dialog.z_factor_spin.setDecimals(4)
        dialog.z_factor_spin.setToolTip("Vertical exaggeration factor (Z scale)")
        dialog.form_layout.addRow("Z Factor (Vertical Scale):", dialog.z_factor_spin)

    # ── 5. Hydrological Modeling Suite ──
    elif dtype == "raster_hydro":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Elevation DEM:", dialog.raster_combo)

        if dialog.algo.algo_id in ("hydrology:stream_network", "hydrology:watershed"):
            thresh_row = QHBoxLayout()
            dialog.thresh_type_combo = QComboBox()
            dialog.thresh_type_combo.addItems([
                "Detailed (Minor streams & gullies - 500 cells)",
                "Standard (Medium rivers & tributaries - 2,000 cells)",
                "Major Catchments (Principal rivers - 10,000 cells)",
                "Custom Minimum Upslope Threshold"
            ])
            dialog.thresh_type_combo.setCurrentIndex(1)
            thresh_row.addWidget(dialog.thresh_type_combo)

            dialog.stream_thresh_spin = QSpinBox()
            dialog.stream_thresh_spin.setRange(10, 10000000)
            dialog.stream_thresh_spin.setValue(2000)
            dialog.stream_thresh_spin.setSuffix(" cells")
            dialog.stream_thresh_spin.setEnabled(False)
            thresh_row.addWidget(dialog.stream_thresh_spin)

            def _on_thresh_preset_changed(idx):
                dialog.stream_thresh_spin.setEnabled(idx == 3)
                if idx == 0:
                    dialog.stream_thresh_spin.setValue(500)
                elif idx == 1:
                    dialog.stream_thresh_spin.setValue(2000)
                elif idx == 2:
                    dialog.stream_thresh_spin.setValue(10000)

            dialog.thresh_type_combo.currentIndexChanged.connect(_on_thresh_preset_changed)
            dialog.form_layout.addRow("Stream Accumulation Threshold:", thresh_row)

        if dialog.algo.algo_id != "hydrology:fillsinks":
            dialog.cb_autofill = QCheckBox("Automatically fill depressions and sinks before routing (Barnes Priority-Flood)")
            dialog.cb_autofill.setChecked(True)
            dialog.form_layout.addRow("", dialog.cb_autofill)

    # ── 6. Contours & Isolines ──
    elif dtype == "raster_contours":
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Elevation DEM:", dialog.raster_combo)

        interval_row = QHBoxLayout()
        dialog.interval_preset_combo = QComboBox()
        dialog.interval_preset_combo.addItems([
            "1 meter (Ultra-detailed)",
            "5 meters (Detailed topographic)",
            "10 meters (Standard topographic)",
            "20 meters (Medium terrain)",
            "50 meters (Mountainous terrain)",
            "100 meters (Regional elevation)",
            "Custom Contour Interval..."
        ])
        dialog.interval_preset_combo.setCurrentIndex(3)
        interval_row.addWidget(dialog.interval_preset_combo)

        dialog.interval_spin = QDoubleSpinBox()
        dialog.interval_spin.setRange(0.1, 10000.0)
        dialog.interval_spin.setValue(20.0)
        dialog.interval_spin.setSuffix(" m")
        dialog.interval_spin.setEnabled(False)
        interval_row.addWidget(dialog.interval_spin)

        def _on_contour_preset(idx):
            dialog.interval_spin.setEnabled(idx == 6)
            vals = [1.0, 5.0, 10.0, 20.0, 50.0, 100.0]
            if idx < len(vals):
                dialog.interval_spin.setValue(vals[idx])

        dialog.interval_preset_combo.currentIndexChanged.connect(_on_contour_preset)
        dialog.form_layout.addRow("Contour Interval:", interval_row)

        dialog.base_spin = QDoubleSpinBox()
        dialog.base_spin.setRange(-10000.0, 10000.0)
        dialog.base_spin.setValue(0.0)
        dialog.base_spin.setSuffix(" m")
        dialog.form_layout.addRow("Base Contour Elevation:", dialog.base_spin)

    # ── 7. Vector Dialogs ──
    elif dtype == "vector_buffer":
        dialog.vector_combo = QComboBox()
        dialog.form_layout.addRow("Input Layer:", dialog.vector_combo)

        dialog.dist_spin = QDoubleSpinBox()
        dialog.dist_spin.setRange(0.01, 1000000.0)
        dialog.dist_spin.setValue(10.0)
        dialog.dist_spin.setSuffix(" m")
        dialog.form_layout.addRow("Distance:", dialog.dist_spin)

        dialog.seg_spin = QSpinBox()
        dialog.seg_spin.setRange(1, 100)
        dialog.seg_spin.setValue(5)
        dialog.form_layout.addRow("Segments:", dialog.seg_spin)

    else:
        dialog.raster_combo = QComboBox()
        dialog.form_layout.addRow("Input Layer:", dialog.raster_combo)
