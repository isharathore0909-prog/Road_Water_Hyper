# -*- coding: utf-8 -*-
"""
GeoStudio - 3D Point Cloud & DEM Reader
Ultra-fast reader to extract 3D points from LAS/LAZ point clouds and DEMs into numpy arrays.
"""

import os
import math
import numpy as np

from .colormaps import (
    apply_turbo_colormap, apply_viridis_colormap, apply_spectral_colormap,
    apply_plasma_colormap, apply_rdylgn_colormap, apply_blues_colormap,
    apply_ylorrd_colormap, apply_categorical_colormap,
    apply_return_number_colormap, apply_las_classification
)
from .las_reader import load_las_points_data


class PointCloudReader:
    """Ultra-fast reader to extract 3D points from LAS/LAZ point clouds and DEMs."""

    # Re-export colormap methods for backward compatibility
    apply_turbo_colormap = staticmethod(apply_turbo_colormap)
    apply_viridis_colormap = staticmethod(apply_viridis_colormap)
    apply_spectral_colormap = staticmethod(apply_spectral_colormap)
    apply_plasma_colormap = staticmethod(apply_plasma_colormap)
    apply_rdylgn_colormap = staticmethod(apply_rdylgn_colormap)
    apply_blues_colormap = staticmethod(apply_blues_colormap)
    apply_ylorrd_colormap = staticmethod(apply_ylorrd_colormap)
    apply_categorical_colormap = staticmethod(apply_categorical_colormap)
    apply_return_number_colormap = staticmethod(apply_return_number_colormap)
    apply_las_classification = staticmethod(apply_las_classification)

    @staticmethod
    def load_dem_points(file_path: str, max_points: int = 8000000):
        """Extracts high-resolution 3D terrain mesh points directly from any DEM/DSM/DTM GeoTIFF raster."""
        from osgeo import gdal
        ds = gdal.Open(file_path, gdal.GA_ReadOnly)
        if not ds:
            raise ValueError(f"Could not open raster file: {file_path}")

        band = ds.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        w = ds.RasterXSize
        h = ds.RasterYSize
        gt = ds.GetGeoTransform()

        total_pts = w * h
        step = max(1, int(math.ceil(math.sqrt(total_pts / max_points))))

        out_w = w // step
        out_h = h // step

        elev = band.ReadAsArray(0, 0, w, h, buf_xsize=out_w, buf_ysize=out_h).astype(np.float32)
        band = None
        ds = None

        cols = np.arange(out_w)
        rows = np.arange(out_h)
        grid_c, grid_r = np.meshgrid(cols, rows)

        res_x = gt[1] * step
        res_y = gt[5] * step
        x_arr = gt[0] + grid_c * res_x
        y_arr = gt[3] + grid_r * res_y

        valid = np.isfinite(elev) & (elev > -10000) & (elev < 50000)
        if nodata is not None:
            valid &= (elev != nodata)

        x_v = x_arr[valid].astype(np.float64)
        y_v = y_arr[valid].astype(np.float64)
        z_v = elev[valid].astype(np.float32)

        if not np.any(valid):
            raise ValueError("No valid elevation pixels found in raster.")

        z_min = float(np.min(z_v))
        z_max = float(np.max(z_v))
        z_range = max(0.001, z_max - z_min)

        cx = float(np.median(x_v))
        cy = float(np.median(y_v))
        cz = float((z_min + z_max) / 2.0)

        x_centered = (x_v - cx).astype(np.float32)
        y_centered = (y_v - cy).astype(np.float32)
        z_centered = (z_v - cz).astype(np.float32)

        if abs(cx) <= 180 and abs(cy) <= 90:
            meters_per_deg_lat = 111320.0
            meters_per_deg_lon = 111320.0 * math.cos(math.radians(cy))
            x_centered = (x_centered * meters_per_deg_lon).astype(np.float32)
            y_centered = (y_centered * meters_per_deg_lat).astype(np.float32)

        pts_xyz = np.column_stack((x_centered, y_centered, z_centered)).astype(np.float32)

        z_norm = np.clip((z_v - z_min) / z_range, 0.0, 1.0)
        z_colors = apply_turbo_colormap(z_norm)

        return (pts_xyz, None, z_colors, None, None, (cx, cy, cz), z_min, z_max, total_pts)

    @staticmethod
    def load_ascii_ply_points(file_path: str, max_points: int = 8000000):
        """Loads points from ASCII XYZ, PTS, CSV, TXT, or PLY point cloud files."""
        ext = os.path.splitext(file_path)[1].lower()
        xyz_list = []
        rgb_list = []

        if ext in [".xyz", ".txt", ".pts", ".csv"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = []
                    for i, line in enumerate(f):
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("//"):
                            continue
                        lines.append(line)
                        if len(lines) >= max_points * 2:
                            break

                total_points = len(lines)
                step = max(1, total_points // max_points)
                sampled_lines = lines[::step]

                for line in sampled_lines:
                    parts = line.replace(",", " ").split()
                    if len(parts) >= 3:
                        try:
                            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                            xyz_list.append((x, y, z))
                            if len(parts) >= 6:
                                r, g, b = float(parts[3]), float(parts[4]), float(parts[5])
                                if r > 1.0 or g > 1.0 or b > 1.0:
                                    r, g, b = r / 255.0, g / 255.0, b / 255.0
                                rgb_list.append((r, g, b))
                        except ValueError:
                            continue
            except Exception:
                pass

        if not xyz_list:
            raise ValueError(f"Could not parse point cloud data from: {file_path}")

        pts = np.array(xyz_list, dtype=np.float64)
        x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
        rgb_colors = np.array(rgb_list, dtype=np.float32) if len(rgb_list) == len(pts) else None
        return PointCloudReader._process_coordinates(x, y, z, rgb_colors, None, None, len(pts))

    @staticmethod
    def _process_coordinates(x, y, z, rgb_colors, class_colors, intensity_colors, total_points, extra_attrs=None):
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        valid &= ~((x == 0.0) & (y == 0.0))
        if not np.any(valid):
            raise ValueError("No valid 3D points found in dataset.")

        x = x[valid]
        y = y[valid]
        z = z[valid]

        if rgb_colors is not None and len(rgb_colors) == len(valid):
            rgb_colors = rgb_colors[valid]
        if class_colors is not None and len(class_colors) == len(valid):
            class_colors = class_colors[valid]
        if intensity_colors is not None and len(intensity_colors) == len(valid):
            intensity_colors = intensity_colors[valid]

        z_min = float(np.min(z))
        z_max = float(np.max(z))
        z_range = max(0.001, z_max - z_min)

        cx = float(np.median(x))
        cy = float(np.median(y))
        cz = float((z_min + z_max) / 2.0)

        x_centered = (x - cx).astype(np.float32)
        y_centered = (y - cy).astype(np.float32)
        z_centered = (z - cz).astype(np.float32)

        if abs(cx) <= 180 and abs(cy) <= 90:
            meters_per_deg_lat = 111320.0
            meters_per_deg_lon = 111320.0 * math.cos(math.radians(cy))
            x_centered = (x_centered * meters_per_deg_lon).astype(np.float32)
            y_centered = (y_centered * meters_per_deg_lat).astype(np.float32)

        pts_xyz = np.column_stack((x_centered, y_centered, z_centered)).astype(np.float32)

        z_norm = np.clip((z - z_min) / z_range, 0.0, 1.0)
        z_colors = apply_turbo_colormap(z_norm)

        color_dict = {}
        if extra_attrs:
            for k, arr in extra_attrs.items():
                if len(arr) == len(valid):
                    arr_valid = arr[valid]
                    if k == 'return_number':
                        color_dict[k] = apply_return_number_colormap(arr_valid)
                    elif k == 'scan_angle':
                        s_norm = np.clip((arr_valid + 35.0) / 70.0, 0.0, 1.0)
                        color_dict[k] = apply_spectral_colormap(s_norm)
                    elif k == 'point_source_id':
                        color_dict[k] = apply_categorical_colormap(arr_valid)
                    elif k in ['nir', 'intensity']:
                        i_min, i_max = np.percentile(arr_valid, [2, 98]) if len(arr_valid) > 0 else (0, 1)
                        i_norm = np.clip((arr_valid - i_min) / max(1.0, i_max - i_min), 0.0, 1.0)
                        color_dict[k] = apply_plasma_colormap(i_norm)

        return (
            pts_xyz, rgb_colors, z_colors, class_colors,
            intensity_colors, (cx, cy, cz), z_min, z_max, total_points, color_dict
        )

    @staticmethod
    def load_las_points(file_path: str, max_points: int = 8000000):
        """
        Extracts 3D points from ANY LAS, LAZ, COPC, DEM, XYZ, PTS, CSV file:
        Returns: (xyz_centered, rgb_colors, z_colors, class_colors,
                  intensity_colors, center_orig, z_min, z_max, total_points, color_dict)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Point cloud file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".tif", ".tiff", ".dem", ".dtm", ".dsm", ".hgt", ".asc", ".img"]:
            for las_ext in [".las", ".laz", ".copc.laz"]:
                cand = file_path.replace(ext, las_ext)
                if os.path.exists(cand):
                    file_path = cand
                    ext = las_ext
                    break
            else:
                return PointCloudReader.load_dem_points(file_path, max_points)

        if ext in [".xyz", ".pts", ".csv", ".txt", ".ply"]:
            return PointCloudReader.load_ascii_ply_points(file_path, max_points)

        if file_path.endswith("_surface.tif"):
            for cand_ext in [".las", ".laz", ".copc.laz", ".e57"]:
                cand = file_path.replace("_surface.tif", cand_ext)
                if os.path.exists(cand):
                    file_path = cand
                    break

        x, y, z, rgb_colors, class_colors, intensity_colors, total_points, extra_attrs = load_las_points_data(
            file_path, max_points=max_points
        )

        return PointCloudReader._process_coordinates(
            x, y, z, rgb_colors, class_colors, intensity_colors, total_points, extra_attrs
        )
