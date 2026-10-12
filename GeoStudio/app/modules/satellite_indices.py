# -*- coding: utf-8 -*-
"""
GeoStudio / GeoAnalytica - Satellite Indices & Hyperspectral Processing Core
Raster calculation, pseudocolor styling, composite generation, and PCA routines.
"""

import tempfile
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsContrastEnhancement,
    QgsRasterBandStats, QgsMultiBandColorRenderer,
    QgsSingleBandPseudoColorRenderer, QgsColorRampShader
)
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import processing


def apply_pseudocolor_ramp(layer):
    """Apply a blue-green-yellow-red pseudocolor ramp to a single-band raster."""
    provider = layer.dataProvider()
    stats = provider.bandStatistics(1)
    min_val = stats.minimumValue
    max_val = stats.maximumValue

    color_ramp = QgsColorRampShader()
    color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
    items = [
        QgsColorRampShader.ColorRampItem(min_val, Qt.blue, "Low"),
        QgsColorRampShader.ColorRampItem((min_val + max_val) / 2, Qt.yellow, "Mid"),
        QgsColorRampShader.ColorRampItem(max_val, Qt.red, "High"),
    ]
    color_ramp.setColorRampItemList(items)

    renderer = QgsSingleBandPseudoColorRenderer(provider, 1)
    renderer.setClassificationMin(min_val)
    renderer.setClassificationMax(max_val)
    renderer.setShader(color_ramp)
    layer.setRenderer(renderer)


def run_raster_calculation(formula: str, layer: QgsRasterLayer, output_name: str):
    """Run QGIS Raster Calculator with given formula and apply pseudocolor ramp."""
    if not layer:
        return None, "Select a raster layer."

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

    tmp = tempfile.mktemp(suffix=".tif")
    calc = QgsRasterCalculator(formula, tmp, "GTiff", extent, crs, cols, rows, entries)
    result_code = calc.processCalculation()

    if result_code == QgsRasterCalculator.Success:
        result_layer = QgsRasterLayer(tmp, output_name)
        if result_layer.isValid():
            apply_pseudocolor_ramp(result_layer)
            QgsProject.instance().addMapLayer(result_layer)
            return result_layer, None
    return None, f"Raster Calculator failed (code {result_code}). Check formula: {formula}"


def apply_false_color_composite(layer: QgsRasterLayer, r_band: int, g_band: int, b_band: int):
    """Applies multi-band color composite with auto contrast stretch."""
    if not layer:
        return False, "Select a raster layer."

    n_bands = layer.bandCount()
    if max(r_band, g_band, b_band) > n_bands:
        return False, f"Layer only has {n_bands} bands. Adjust band numbers."

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
    return True, f"False color composite applied: R={r_band} G={g_band} B={b_band}"


def run_pca(layer: QgsRasterLayer, max_components: int = 10):
    """Executes PCA on raster layer, falling back to pure numpy eigen-decomposition."""
    if not layer or not layer.isValid():
        return None, "Select a valid raster layer."
    # 1. Try GDAL processing if available
    try:
        params = {
            "INPUT": layer,
            "COMPONENTS": min(layer.bandCount(), max_components),
            "OUTPUT": "TEMPORARY_OUTPUT"
        }
        result = processing.run("gdal:pcaanalysis", params)
        out = result.get("OUTPUT")
        if out:
            pca_layer = QgsRasterLayer(out, f"{layer.name()}_PCA")
            if pca_layer.isValid():
                QgsProject.instance().addMapLayer(pca_layer)
                return pca_layer, f"✓ PCA completed: {layer.bandCount()} → {params['COMPONENTS']} components"
    except Exception:
        pass

    # 2. High-performance Numpy / GDAL Eigen-decomposition
    try:
        from osgeo import gdal
        import numpy as np

        src_path = layer.source()
        ds_in = gdal.Open(src_path, gdal.GA_ReadOnly)
        if not ds_in:
            return None, "Could not open raster data source for PCA."

        cols, rows = ds_in.RasterXSize, ds_in.RasterYSize
        nbands = ds_in.RasterCount
        if nbands < 2:
            return None, "PCA requires at least 2 spectral bands."

        n_comp = min(nbands, max_components)
        bands_data = [ds_in.GetRasterBand(i).ReadAsArray().astype(np.float32) for i in range(1, nbands + 1)]
        stack = np.stack(bands_data, axis=-1)
        flat = stack.reshape(-1, nbands)

        # Remove NaNs and zero variance
        mean = np.nanmean(flat, axis=0)
        flat_c = flat - mean
        flat_c[np.isnan(flat_c)] = 0.0

        cov = np.cov(flat_c, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(cov)
        idx = np.argsort(eigvals)[::-1]
        eigvecs = eigvecs[:, idx[:n_comp]]
        projected = np.dot(flat_c, eigvecs).reshape(rows, cols, n_comp)

        tmp_out = tempfile.mktemp(suffix=".tif")
        drv = gdal.GetDriverByName("GTiff")
        ds_out = drv.Create(tmp_out, cols, rows, n_comp, gdal.GDT_Float32)
        ds_out.SetProjection(ds_in.GetProjection())
        ds_out.SetGeoTransform(ds_in.GetGeoTransform())
        for b in range(n_comp):
            ds_out.GetRasterBand(b + 1).WriteArray(projected[:, :, b])
        ds_out.FlushCache()
        ds_out = None
        ds_in = None

        pca_layer = QgsRasterLayer(tmp_out, f"{layer.name()}_PCA")
        if pca_layer.isValid():
            QgsProject.instance().addMapLayer(pca_layer)
            explained = eigvals[idx[:n_comp]] / (np.sum(eigvals) + 1e-9) * 100
            return pca_layer, f"✓ PCA completed: {nbands} bands → {n_comp} components (PC1 explains {explained[0]:.1f}% variance)"
    except Exception as e:
        return None, f"PCA calculation failed: {e}"

    return None, "PCA execution yielded no output."
