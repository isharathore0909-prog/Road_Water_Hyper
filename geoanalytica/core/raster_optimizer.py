# -*- coding: utf-8 -*-
"""
GeoAnalytica - Raster Auto-Optimizer
Automatically detects large raster layers missing overviews/pyramids and builds
multi-resolution overviews in a background thread for instantaneous zooming and panning.
"""

import os
from PyQt5.QtCore import QObject, pyqtSignal, QThread


class RasterOverviewWorker(QThread):
    progress_changed = pyqtSignal(str, int)
    finished_success = pyqtSignal(str, str)
    finished_error = pyqtSignal(str, str)

    def __init__(self, file_path, layer_name, layer=None, canvas=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.layer_name = layer_name
        self.layer = layer
        self.canvas = canvas

    def run(self):
        try:
            from osgeo import gdal
            gdal.UseExceptions()

            gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
            gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")

            ds = gdal.Open(self.file_path, gdal.GA_ReadOnly)
            if ds is None:
                return

            band = ds.GetRasterBand(1)
            if band is None or band.GetOverviewCount() > 0:
                return

            width = ds.RasterXSize
            height = ds.RasterYSize
            max_dim = max(width, height)

            levels = []
            f = 2
            while (max_dim // f) >= 128 and f <= 256:
                levels.append(f)
                f *= 2

            if not levels:
                levels = [2, 4, 8, 16, 32]

            def gdal_progress_cb(complete, message, user_data):
                pct = int(complete * 100)
                self.progress_changed.emit(self.layer_name, pct)
                return 1

            ds.BuildOverviews("AVERAGE", levels, gdal_progress_cb)
            ds.FlushCache()
            del ds

            self.finished_success.emit(self.layer_name, self.file_path)

        except Exception as e:
            self.finished_error.emit(self.layer_name, str(e))


class AutoRasterOptimizer(QObject):
    status_message = pyqtSignal(str, int)

    def __init__(self, iface=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._active_workers = {}
        self._processed_paths = set()

    def check_and_optimize(self, layer, canvas=None):
        if not layer or not layer.isValid():
            return

        source = layer.source()
        if not source or not os.path.isfile(source):
            return

        norm_path = os.path.normpath(source)
        if norm_path in self._processed_paths or norm_path in self._active_workers:
            return

        try:
            from osgeo import gdal
            ds = gdal.Open(source, gdal.GA_ReadOnly)
            if ds is None:
                return

            width = ds.RasterXSize
            height = ds.RasterYSize

            if width <= 1500 and height <= 1500:
                del ds
                return

            band = ds.GetRasterBand(1)
            if band is None:
                del ds
                return

            has_overviews = band.GetOverviewCount() > 0
            del ds

            if not has_overviews:
                self._start_worker(norm_path, layer.name(), layer, canvas)

        except Exception as e:
            print(f"[AutoRasterOptimizer] Error: {e}")

    def _start_worker(self, path, name, layer, canvas):
        msg = f"⚡ Auto-optimizing '{name}' for instant zooming..."
        if self.iface:
            self.iface.messageBar().pushInfo("GeoAnalytica", msg)

        worker = RasterOverviewWorker(path, name, layer, canvas, self)
        self._active_workers[path] = worker

        worker.finished_success.connect(self._on_success)
        worker.start()

    def _on_success(self, name, path):
        self._processed_paths.add(path)
        worker = self._active_workers.pop(path, None)
        if worker:
            try:
                if worker.layer and worker.layer.isValid():
                    worker.layer.reload()
                if worker.canvas:
                    worker.canvas.refresh()
                elif self.iface:
                    self.iface.mapCanvas().refresh()
            except Exception:
                pass

        if self.iface:
            self.iface.messageBar().pushSuccess("GeoAnalytica", f"✓ '{name}' optimized for instant zoom!")


_instance = None

def get_raster_optimizer(iface=None):
    global _instance
    if _instance is None:
        _instance = AutoRasterOptimizer(iface)
    elif iface and _instance.iface is None:
        _instance.iface = iface
    return _instance
