# -*- coding: utf-8 -*-
"""
GeoStudio - Specialized Algorithm Runners
Contains execution routines for contours, viewshed, cut & fill, flood simulation, and vector buffering.
"""

import os
import tempfile
import numpy as np
from osgeo import gdal, ogr, osr
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsProcessingFeedback,
    QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader
)
import processing

from core.elevation_styler import ElevationStyler


def run_raster_contours(dialog):
    """Generates contour vector lines from an input DEM."""
    r_id = dialog.raster_combo.currentData()
    if not r_id:
        raise ValueError("Please select an input DEM raster layer.")
    layer = QgsProject.instance().mapLayer(r_id)
    if not layer or not layer.isValid():
        raise ValueError("Selected DEM layer is invalid.")

    interval = dialog.interval_spin.value() if hasattr(dialog, "interval_spin") else 20.0
    base_val = dialog.base_spin.value() if hasattr(dialog, "base_spin") else 0.0

    out_path = dialog.output_edit.text().strip()
    if not out_path or out_path == "[Create temporary layer]" or out_path.endswith(".tif"):
        out_path = tempfile.mktemp(suffix=".gpkg")

    dialog.log(f"Extracting contour lines: interval = <b>{interval:.1f} m</b>, base = <b>{base_val:.1f} m</b>...")
    dialog.progress_bar.setValue(20)

    ds_in = gdal.Open(layer.source(), gdal.GA_ReadOnly)
    if not ds_in:
        raise RuntimeError(f"Could not open input raster: {layer.source()}")
    band = ds_in.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    ext = os.path.splitext(out_path)[1].lower()
    driver_name = "GPKG" if ext == ".gpkg" else "ESRI Shapefile"
    ogr_driver = ogr.GetDriverByName(driver_name)
    if not ogr_driver:
        driver_name = "GPKG"
        ogr_driver = ogr.GetDriverByName("GPKG")
        out_path = tempfile.mktemp(suffix=".gpkg")

    if os.path.exists(out_path):
        ogr_driver.DeleteDataSource(out_path)

    out_ds = ogr_driver.CreateDataSource(out_path)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds_in.GetProjection())
    out_layer_ogr = out_ds.CreateLayer("contours", srs, ogr.wkbLineString)

    id_fld = ogr.FieldDefn("ID", ogr.OFTInteger)
    elev_fld = ogr.FieldDefn("ELEV", ogr.OFTReal)
    out_layer_ogr.CreateField(id_fld)
    out_layer_ogr.CreateField(elev_fld)

    dialog.progress_bar.setValue(45)
    gdal.ContourGenerate(
        band, interval, base_val, [],
        1 if nodata is not None else 0,
        float(nodata) if nodata is not None else 0.0,
        out_layer_ogr, 0, 1
    )

    feat_count = out_layer_ogr.GetFeatureCount()
    del out_layer_ogr, id_fld, elev_fld
    out_ds.FlushCache()
    out_ds = None
    band = None
    ds_in = None

    dialog.progress_bar.setValue(85)
    dialog.log(f"Contour extraction complete: generated <b>{feat_count:,}</b> contour lines.")

    if dialog.open_output_cb.isChecked() and os.path.exists(out_path):
        clean_name = layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "")
        qgs_vec = QgsVectorLayer(out_path, f"{clean_name}_contours_{int(interval)}m", "ogr")
        if qgs_vec.isValid():
            QgsProject.instance().addMapLayer(qgs_vec)
            dialog.log(f"Added contour layer to project: <b>{qgs_vec.name()}</b>")


def run_raster_viewshed(dialog):
    """Performs line-of-sight viewshed computation using GDAL."""
    r_id = dialog.raster_combo.currentData()
    if not r_id:
        raise ValueError("Please select an input DEM raster layer.")
    layer = QgsProject.instance().mapLayer(r_id)
    if not layer or not layer.isValid():
        raise ValueError("Selected DEM layer is invalid.")

    obs_x = dialog.observer_x_spin.value()
    obs_y = dialog.observer_y_spin.value()
    obs_h = dialog.observer_h_spin.value()
    tgt_h = dialog.target_h_spin.value()
    max_d = dialog.max_dist_spin.value()

    out_path = dialog.output_edit.text().strip()
    if not out_path or out_path == "[Create temporary layer]":
        out_path = tempfile.mktemp(suffix=".tif")

    dialog.log(f"Running Viewshed analysis from observer ({obs_x:.2f}, {obs_y:.2f})...")
    dialog.log(f"Observer height: <b>{obs_h:.1f} m</b> | Target height: <b>{tgt_h:.1f} m</b> | Radius: <b>{max_d:,.0f} m</b>")
    dialog.progress_bar.setValue(30)

    ds_in = gdal.Open(layer.source(), gdal.GA_ReadOnly)
    if not ds_in:
        raise RuntimeError(f"Could not open input raster: {layer.source()}")
    band = ds_in.GetRasterBand(1)

    vs_ds = gdal.ViewshedGenerate(
        srcBand=band, driverName="GTiff", targetRasterName=out_path,
        creationOptions=["TILED=YES", "COMPRESS=LZW"],
        observerX=obs_x, observerY=obs_y, observerHeight=obs_h, targetHeight=tgt_h,
        visibleVal=255.0, invisibleVal=0.0, outOfRangeVal=0.0, noDataVal=0.0,
        dfCurvCoeff=0.85714, mode=gdal.GVM_Diagonal, maxDistance=max_d
    )
    band = None
    vs_ds = None
    ds_in = None

    dialog.progress_bar.setValue(85)
    dialog.log("Viewshed line-of-sight computation complete.")

    if dialog.open_output_cb.isChecked() and os.path.exists(out_path):
        clean_name = layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "")
        vs_layer = QgsRasterLayer(out_path, f"{clean_name}_viewshed")
        if vs_layer.isValid():
            fcn = QgsColorRampShader()
            fcn.setColorRampType(QgsColorRampShader.Exact)
            fcn.setColorRampItemList([
                QgsColorRampShader.ColorRampItem(0, QColor(0, 0, 0, 0), "Invisible"),
                QgsColorRampShader.ColorRampItem(255, QColor(34, 197, 94, 180), "Visible")
            ])
            shader = QgsRasterShader()
            shader.setRasterShaderFunction(fcn)
            renderer = QgsSingleBandPseudoColorRenderer(vs_layer.dataProvider(), 1, shader)
            vs_layer.setRenderer(renderer)
            vs_layer.triggerRepaint()
            QgsProject.instance().addMapLayer(vs_layer)
            dialog.log(f"Added viewshed visibility layer to project: <b>{vs_layer.name()}</b>")


def run_terrain_cutfill(dialog):
    """Performs earthwork cut and fill volumetric calculation."""
    from core.earthworks.cut_fill_engine import CutFillEngine
    r_id = dialog.raster_combo.currentData()
    if not r_id:
        raise ValueError("Please select a base DEM layer.")
    base_layer = QgsProject.instance().mapLayer(r_id)
    if not base_layer or not base_layer.isValid():
        raise ValueError("Selected base DEM is invalid.")

    mode_idx = dialog.compare_mode_combo.currentIndex()
    datum = dialog.datum_height_spin.value() if mode_idx == 0 else None
    comp_layer = None
    if mode_idx == 1:
        comp_id = dialog.compare_dem_combo.currentData() if hasattr(dialog, "compare_dem_combo") else None
        if not comp_id:
            raise ValueError("Please select a comparison (second) DEM layer.")
        comp_layer = QgsProject.instance().mapLayer(comp_id)

    out_path = dialog.output_edit.text().strip()
    if not out_path or out_path == "[Create temporary layer]":
        out_path = tempfile.mktemp(suffix=".tif")

    res = CutFillEngine.compute_cut_fill(
        base_source=base_layer, comp_source=comp_layer, datum_elevation=datum,
        output_diff_path=out_path, generate_daylight_vector=False,
        progress_callback=lambda pct, msg: (dialog.progress_bar.setValue(int(pct)), dialog.progress_bar.setFormat(msg))
    )

    dialog.log(CutFillEngine.generate_report_text(res))

    if dialog.open_output_cb.isChecked() and os.path.exists(out_path):
        clean_name = base_layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "")
        diff_layer = QgsRasterLayer(out_path, f"{clean_name}_cutfill_diff")
        if diff_layer.isValid():
            ElevationStyler.apply_cut_fill_colormap(diff_layer)
            QgsProject.instance().addMapLayer(diff_layer)
            dialog.log(f"Added earthwork difference raster to project: <b>{diff_layer.name()}</b>")


def run_terrain_flood(dialog):
    """Simulates flood inundation and computes depth/volume statistics."""
    r_id = dialog.raster_combo.currentData()
    if not r_id:
        raise ValueError("Please select an input DEM layer.")
    base_layer = QgsProject.instance().mapLayer(r_id)
    if not base_layer or not base_layer.isValid():
        raise ValueError("Selected DEM layer is invalid.")

    water_lvl = dialog.water_level_spin.value()
    dialog.log(f"Simulating flood inundation at elevation: <b>{water_lvl:.2f} m</b>...")
    dialog.progress_bar.setValue(25)

    ds_in = gdal.Open(base_layer.source(), gdal.GA_ReadOnly)
    gt = ds_in.GetGeoTransform()
    w = ds_in.RasterXSize
    h = ds_in.RasterYSize
    cell_area = abs(gt[1]) * abs(gt[5])

    b = ds_in.GetRasterBand(1)
    nodata = b.GetNoDataValue()
    arr = b.ReadAsArray().astype(np.float32)
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    valid_mask = ~np.isnan(arr)
    flood_mask = valid_mask & (arr <= water_lvl)
    depth_arr = np.where(flood_mask, water_lvl - arr, 0.0)

    flooded_cells = int(np.sum(flood_mask))
    flooded_area_m2 = flooded_cells * cell_area
    flooded_area_km2 = flooded_area_m2 / 1e6
    inundated_vol_m3 = float(np.sum(depth_arr[flood_mask]) * cell_area)
    max_depth = float(np.max(depth_arr[flood_mask])) if flooded_cells > 0 else 0.0
    avg_depth = float(np.mean(depth_arr[flood_mask])) if flooded_cells > 0 else 0.0

    dialog.progress_bar.setValue(75)
    dialog.log("\n<b>===== FLOOD & INUNDATION SIMULATION REPORT =====</b>")
    dialog.log(f"Target Water Elevation: <b>{water_lvl:.2f} m</b>")
    dialog.log(f"Flooded Area: <b>{flooded_area_km2:.3f} km²</b> ({flooded_area_m2:,.0f} m²)")
    dialog.log(f"Inundated Water Volume: <span style='color:#0284c7;'><b>{inundated_vol_m3:,.1f} m³</b></span>")
    dialog.log(f"Maximum Water Depth: <b>{max_depth:.2f} m</b> | Average Depth: <b>{avg_depth:.2f} m</b>")
    dialog.log("================================================\n")

    out_path = dialog.output_edit.text().strip()
    if not out_path or out_path == "[Create temporary layer]":
        out_path = tempfile.mktemp(suffix=".tif")

    driver = gdal.GetDriverByName("GTiff")
    ds_out = driver.Create(out_path, w, h, 1, gdal.GDT_Float32, ["TILED=YES", "COMPRESS=LZW"])
    ds_out.SetGeoTransform(gt)
    ds_out.SetProjection(ds_in.GetProjection())
    depth_out = np.where(flood_mask, depth_arr, -9999.0)
    b_out = ds_out.GetRasterBand(1)
    b_out.SetNoDataValue(-9999.0)
    b_out.WriteArray(depth_out)
    b_out = None
    b = None
    ds_out.FlushCache()
    ds_out = None
    ds_in = None

    if dialog.open_output_cb.isChecked() and os.path.exists(out_path):
        clean_name = base_layer.name().replace(" [DEM]", "").replace(" [3D Relief]", "")
        flood_layer = QgsRasterLayer(out_path, f"{clean_name}_flood_depth_{int(water_lvl)}m")
        if flood_layer.isValid():
            QgsProject.instance().addMapLayer(flood_layer)
            dialog.log(f"Added flood depth raster to project: <b>{flood_layer.name()}</b>")


def run_vector_buffer(dialog):
    """Executes native QGIS buffer on vector layers."""
    v_id = dialog.vector_combo.currentData()
    if not v_id:
        raise ValueError("Please select an input vector layer.")
    layer = QgsProject.instance().mapLayer(v_id)

    params = {
        "INPUT": layer,
        "DISTANCE": dialog.dist_spin.value(),
        "SEGMENTS": dialog.seg_spin.value(),
        "DISSOLVE": False,
        "OUTPUT": "memory:",
    }
    dialog.log(f"Input parameters:\n{params}\n")
    res = processing.run("native:buffer", params, feedback=QgsProcessingFeedback())
    out = res.get("OUTPUT")
    if out:
        if isinstance(out, str):
            out = QgsVectorLayer(out, f"{layer.name()}_buffer", "ogr")
        out.setName(f"{layer.name()}_buffer")
        if dialog.open_output_cb.isChecked():
            QgsProject.instance().addMapLayer(out)
            dialog.log(f"Loaded output layer: <b>{out.name()}</b>")
