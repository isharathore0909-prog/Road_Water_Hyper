# -*- coding: utf-8 -*-
"""
GeoStudio - 3D Point Cloud & DEM Reader
Ultra-fast reader to extract 3D points from LAS/LAZ point clouds and DEMs into numpy arrays.
"""

import os
import struct
import math
import numpy as np


class PointCloudReader:
    """Ultra-fast reader to extract 3D points from LAS/LAZ point clouds and DEMs."""

    @staticmethod
    def load_dem_points(file_path: str, max_points: int = 2000000):
        """Extracts 3D terrain mesh points directly from any DEM/DSM/DTM GeoTIFF raster."""
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
        del ds

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
        z_colors = PointCloudReader.apply_turbo_colormap(z_norm)

        return (pts_xyz, None, z_colors, None, None, (cx, cy, cz), z_min, z_max, total_pts)

    @staticmethod
    def load_ascii_ply_points(file_path: str, max_points: int = 3000000):
        """Loads points from ASCII XYZ, PTS, CSV, TXT, or PLY point cloud files."""
        ext = os.path.splitext(file_path)[1].lower()
        xyz_list = []
        rgb_list = []
        
        if ext in [".xyz", ".txt", ".pts", ".csv"]:
            try:
                # Fast sample read
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
    def _process_coordinates(x, y, z, rgb_colors, class_colors, intensity_colors, total_points):
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        valid &= ~((x == 0.0) & (y == 0.0))
        if not np.any(valid):
            raise ValueError("No valid 3D points found in dataset.")

        x = x[valid]
        y = y[valid]
        z = z[valid]
        if rgb_colors is not None: rgb_colors = rgb_colors[valid]
        if class_colors is not None: class_colors = class_colors[valid]
        if intensity_colors is not None: intensity_colors = intensity_colors[valid]

        # Rejection of extreme sensor outliers / corrupt records
        if len(z) > 100:
            p_low, p_high = np.percentile(z, [0.1, 99.9])
            span = max(30.0, (p_high - p_low) * 2.5)
            in_bounds = (z >= p_low - span) & (z <= p_high + span)
            if np.any(in_bounds) and np.sum(in_bounds) > 0.85 * len(z):
                x = x[in_bounds]
                y = y[in_bounds]
                z = z[in_bounds]
                if rgb_colors is not None: rgb_colors = rgb_colors[in_bounds]
                if class_colors is not None: class_colors = class_colors[in_bounds]
                if intensity_colors is not None: intensity_colors = intensity_colors[in_bounds]

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
        z_colors = PointCloudReader.apply_turbo_colormap(z_norm)

        return (pts_xyz, rgb_colors, z_colors, class_colors, intensity_colors, (cx, cy, cz), z_min, z_max, total_points)

    @staticmethod
    def load_las_points(file_path: str, max_points: int = 3000000):
        """
        Extracts 3D points from ANY LAS, LAZ, COPC, DEM, XYZ, PTS, CSV file into numpy arrays:
        Returns: (xyz_centered, rgb_colors, z_colors, class_colors, intensity_colors, center_orig, z_min, z_max, total_points)
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

        pts_data = None

        # 1. Try laspy first if available
        try:
            import sys
            user_site = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\site-packages")
            if os.path.exists(user_site) and user_site not in sys.path:
                sys.path.insert(0, user_site)

            import laspy
            with laspy.open(file_path) as fh:
                total_points = fh.header.point_count
                step = max(1, total_points // max_points)
                las = fh.read()

                x = np.array(las.x[::step], dtype=np.float64)
                y = np.array(las.y[::step], dtype=np.float64)
                z = np.array(las.z[::step], dtype=np.float32)

                has_rgb = hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue')
                if has_rgb:
                    r_raw = np.array(las.red[::step])
                    g_raw = np.array(las.green[::step])
                    b_raw = np.array(las.blue[::step])
                    if np.max(r_raw) > 255 or np.max(g_raw) > 255 or np.max(b_raw) > 255:
                        r = (r_raw >> 8).astype(np.float32) / 255.0
                        g = (g_raw >> 8).astype(np.float32) / 255.0
                        b = (b_raw >> 8).astype(np.float32) / 255.0
                    else:
                        r = r_raw.astype(np.float32) / 255.0
                        g = g_raw.astype(np.float32) / 255.0
                        b = b_raw.astype(np.float32) / 255.0
                    rgb_colors = np.column_stack((r, g, b)).astype(np.float32)
                else:
                    rgb_colors = None

                if hasattr(las, 'classification'):
                    class_raw = np.array(las.classification[::step])
                    class_colors = PointCloudReader.apply_las_classification(class_raw)
                else:
                    class_colors = None

                if hasattr(las, 'intensity'):
                    intens_raw = np.array(las.intensity[::step], dtype=np.float32)
                    i_min, i_max = np.percentile(intens_raw, [2, 98]) if len(intens_raw) > 0 else (0, 1)
                    i_norm = np.clip((intens_raw - i_min) / max(1.0, i_max - i_min), 0.0, 1.0)
                    intensity_colors = np.column_stack((i_norm, i_norm, i_norm)).astype(np.float32)
                else:
                    intensity_colors = None

                pts_data = (x, y, z, rgb_colors, class_colors, intensity_colors, total_points)
        except Exception:
            pts_data = None

        # 2. If compressed (.laz / .copc.laz) and laspy failed, use PDAL to dump a fast uncompressed sample
        if pts_data is None and file_path.lower().endswith(('.laz', '.copc.laz')):
            try:
                import subprocess, tempfile, shutil
                qgis_root = r"C:\Program Files\QGIS 3.40.14"
                pdal_candidates = [
                    os.path.join(qgis_root, "bin", "pdal.exe"),
                    os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "pdal.exe"),
                    shutil.which("pdal")
                ]
                pdal_exe = next((p for p in pdal_candidates if p and os.path.exists(p)), None)
                if pdal_exe:
                    tmp_las = os.path.join(tempfile.gettempdir(), f"view3d_{os.getpid()}.las")
                    env = os.environ.copy()
                    proj_dir = os.path.join(qgis_root, "share", "proj")
                    if os.path.exists(proj_dir):
                        env["PROJ_LIB"] = proj_dir
                        env["PROJ_DATA"] = proj_dir

                    subprocess.run(
                        [pdal_exe, "translate", file_path, tmp_las, f"--readers.copc.count={max_points}"],
                        capture_output=True, env=env, timeout=20
                    )
                    if os.path.exists(tmp_las) and os.path.getsize(tmp_las) > 1024:
                        file_path = tmp_las
            except Exception:
                pass

        # 3. Universal binary parser for uncompressed LAS 1.0 - 1.4 formats
        if pts_data is None:
            with open(file_path, 'rb') as f:
                header = f.read(375)
                if header[:4] != b'LASF':
                    raise ValueError("Not a valid standard LAS/LAZ point cloud dataset.")

                v_maj, v_min = header[24], header[25]
                hdr_sz, = struct.unpack('<H', header[94:96])
                offset_to_points, = struct.unpack('<I', header[96:100])
                point_format = header[104]
                point_len, = struct.unpack('<H', header[105:107])
                num_points_legacy, = struct.unpack('<I', header[107:111])
                x_scale, y_scale, z_scale = struct.unpack('<3d', header[131:155])
                x_off, y_off, z_off = struct.unpack('<3d', header[155:179])

                total_points = num_points_legacy
                if v_maj == 1 and v_min >= 4 and hdr_sz >= 375 and len(header) >= 255:
                    try:
                        num_points_64, = struct.unpack('<Q', header[247:255])
                        if num_points_64 > 0:
                            total_points = num_points_64
                    except Exception:
                        pass

                file_sz = os.path.getsize(file_path)
                avail_pts = (file_sz - offset_to_points) // point_len if point_len > 0 else 0
                total_points = min(total_points, avail_pts) if total_points > 0 else avail_pts
                if total_points <= 0:
                    raise ValueError("Point cloud contains 0 points or invalid header.")

                step = max(1, total_points // max_points)
                m = np.memmap(file_path, dtype=np.uint8, mode='r', offset=offset_to_points, shape=(total_points, point_len))
                raw = np.array(m[::step], copy=True)
                del m

                x_raw = np.ascontiguousarray(raw[:, 0:4]).view(np.int32).flatten()
                y_raw = np.ascontiguousarray(raw[:, 4:8]).view(np.int32).flatten()
                z_raw = np.ascontiguousarray(raw[:, 8:12]).view(np.int32).flatten()

                x = (x_raw * x_scale + x_off).astype(np.float64)
                y = (y_raw * y_scale + y_off).astype(np.float64)
                z = (z_raw * z_scale + z_off).astype(np.float32)

                # Determine RGB byte offset based on LAS point format (0-10)
                rgb_offset = None
                if point_format in [2]:
                    rgb_offset = 20 if point_len >= 26 else None
                elif point_format in [3, 5]:
                    rgb_offset = 28 if point_len >= 34 else None
                elif point_format in [7, 8, 10]:
                    rgb_offset = 30 if point_len >= 36 else None

                if rgb_offset is not None and point_len >= rgb_offset + 6:
                    r = np.ascontiguousarray(raw[:, rgb_offset:rgb_offset + 2]).view(np.uint16).flatten()
                    g = np.ascontiguousarray(raw[:, rgb_offset + 2:rgb_offset + 4]).view(np.uint16).flatten()
                    b = np.ascontiguousarray(raw[:, rgb_offset + 4:rgb_offset + 6]).view(np.uint16).flatten()
                    if np.max(r) > 255 or np.max(g) > 255 or np.max(b) > 255:
                        r = r >> 8
                        g = g >> 8
                        b = b >> 8
                    rgb_colors = np.column_stack((r, g, b)).astype(np.float32) / 255.0
                else:
                    rgb_colors = None

                # Classification byte
                class_byte_idx = 16 if point_format in [6, 7, 8, 9, 10] else 15
                if point_len > class_byte_idx:
                    class_raw = raw[:, class_byte_idx].flatten()
                    class_colors = PointCloudReader.apply_las_classification(class_raw)
                else:
                    class_colors = None

                # Intensity
                if point_len >= 14:
                    intens_raw = raw[:, 12:14].view(np.uint16).flatten().astype(np.float32)
                    i_min, i_max = np.percentile(intens_raw, [2, 98]) if len(intens_raw) > 0 else (0, 1)
                    i_norm = np.clip((intens_raw - i_min) / max(1.0, i_max - i_min), 0.0, 1.0)
                    intensity_colors = np.column_stack((i_norm, i_norm, i_norm)).astype(np.float32)
                else:
                    intensity_colors = None

                pts_data = (x, y, z, rgb_colors, class_colors, intensity_colors, total_points)

        x, y, z, rgb_colors, class_colors, intensity_colors, total_points = pts_data
        return PointCloudReader._process_coordinates(x, y, z, rgb_colors, class_colors, intensity_colors, total_points)

    @staticmethod
    def apply_turbo_colormap(norm_vals: np.ndarray) -> np.ndarray:
        """High-definition Turbo scientific colormap vectorization."""
        x = norm_vals
        r = 0.1357 + x * (4.5974 - x * (42.681 - x * (152.58 - x * (221.38 - x * 111.4))))
        g = 0.0914 + x * (2.1856 + x * (4.8052 - x * (14.095 - x * (4.2115 - x * 10.36))))
        b = 0.1067 + x * (12.585 - x * (60.118 - x * (109.07 - x * (88.5 - x * 26.85))))
        return np.clip(np.column_stack((r, g, b)), 0.0, 1.0).astype(np.float32)

    @staticmethod
    def apply_las_classification(classes: np.ndarray) -> np.ndarray:
        """Standard ASPRS LAS point cloud classification palette."""
        palette = {
            0: (0.6, 0.6, 0.6),      # Unclassified
            1: (0.7, 0.7, 0.7),      # Unassigned
            2: (0.83, 0.64, 0.45),   # Ground (Light Sandy Brown / Tan)
            3: (0.55, 0.90, 0.55),   # Low Veg (Light Green)
            4: (0.13, 0.75, 0.13),   # Medium Veg (Green)
            5: (0.05, 0.45, 0.05),   # High Veg / Canopy (Dark Green)
            6: (0.95, 0.15, 0.15),   # Building (Vivid Red)
            7: (0.40, 0.40, 0.40), # Low Point / Noise
            8: (0.95, 0.60, 0.10), # Key-point
            9: (0.00, 0.50, 0.95), # Water (Blue)
            11: (0.25, 0.25, 0.25) # Road Surface
        }
        colors = np.zeros((len(classes), 3), dtype=np.float32)
        for code, rgb in palette.items():
            mask = (classes == code)
            if np.any(mask):
                colors[mask] = rgb
        mask_other = np.all(colors == 0, axis=1)
        colors[mask_other] = (0.5, 0.6, 0.7)
        return colors
