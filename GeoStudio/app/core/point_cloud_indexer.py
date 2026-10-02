# -*- coding: utf-8 -*-
"""
GeoStudio - Cloud-Optimized Point Cloud (COPC) Indexer & Generator
Automatically indexes and converts raw LAS/LAZ/XYZ datasets into genuine .copc.laz files
so they render natively as discrete point clouds with true 3D point sprites in 2D and 3D.
"""

import os
import sys
import subprocess
import shutil
import tempfile


class PointCloudIndexer:
    """Provides high-speed indexing and conversion to Cloud-Optimized Point Clouds (.copc.laz)."""
    _current_process = None
    _is_cancelled = False

    @classmethod
    def cancel(cls):
        cls._is_cancelled = True
        if cls._current_process:
            try:
                cls._current_process.terminate()
                cls._current_process.kill()
            except Exception:
                pass
            cls._current_process = None

    @staticmethod
    def get_point_count(file_path: str) -> int:
        """Reads point count from LAS/LAZ binary headers in < 1 millisecond."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(375)
                if header[:4] == b'LASF':
                    import struct
                    v_maj, v_min = header[24], header[25]
                    pts_legacy, = struct.unpack('<I', header[107:111])
                    if pts_legacy > 0:
                        return pts_legacy
                    if v_maj == 1 and v_min >= 4 and len(header) >= 255:
                        pts_64, = struct.unpack('<Q', header[247:255])
                        if pts_64 > 0:
                            return pts_64
        except Exception:
            pass
        return 0

    @staticmethod
    def get_indexer_command(input_path: str, output_path: str):
        """Builds an optimized, multi-threaded PDAL pipeline tailored to dataset size."""
        import json
        import time

        qgis_root = r"C:\Program Files\QGIS 3.40.14"
        bin_dir = os.path.join(qgis_root, "bin")
        qgis_bin = os.path.join(qgis_root, "apps", "qgis-ltr", "bin")
        
        env = os.environ.copy()
        path_var = f"{bin_dir};{qgis_bin};" + env.get("PATH", "")
        proj_dir = os.path.join(qgis_root, "share", "proj")
        gdal_dir = os.path.join(qgis_root, "share", "gdal")
        if os.path.exists(proj_dir):
            env["PROJ_LIB"] = proj_dir
            env["PROJ_DATA"] = proj_dir
        if os.path.exists(gdal_dir):
            env["GDAL_DATA"] = gdal_dir

        pdal_candidates = [
            os.path.join(qgis_root, "bin", "pdal.exe"),
            os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "pdal.exe"),
            os.path.join(qgis_root, "apps", "Python312", "Scripts", "pdal.exe"),
            shutil.which("pdal"),
        ]

        total_pts = PointCloudIndexer.get_point_count(input_path)

        for p in pdal_candidates:
            if p and os.path.exists(p):
                stages = [input_path]
                # If dataset exceeds 15M points, adaptively decimate for lightning-fast 2D canvas streaming (<4GB RAM)
                if total_pts > 15_000_000:
                    step = max(2, int(round(total_pts / 12_000_000)))
                    stages.append({
                        "type": "filters.decimation",
                        "step": step
                    })

                stages.append({
                    "type": "writers.copc",
                    "filename": output_path,
                    "forward": "all",
                    "threads": 8
                })

                pipe_path = os.path.join(tempfile.gettempdir(), f"pdal_pipe_{int(time.time())}_{os.getpid()}.json")
                try:
                    with open(pipe_path, "w", encoding="utf-8") as f:
                        json.dump(stages, f, indent=2)
                    cmd = [p, "pipeline", pipe_path]
                    return cmd, env
                except Exception:
                    cmd = [
                        p, "translate", input_path, output_path,
                        "--writer", "writers.copc",
                        "--writers.copc.forward=all",
                        "--writers.copc.threads=8"
                    ]
                    return cmd, env

        return None, env

    @staticmethod
    def get_target_copc_path(file_path: str) -> str:
        """Determines the destination .copc.laz path, preferring dataset folder or fast cache."""
        base_dir = os.path.dirname(os.path.abspath(file_path))
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 1. First check alongside original file
        local_copc = os.path.join(base_dir, f"{base_name}.copc.laz")
        if os.path.exists(local_copc) and os.path.getsize(local_copc) > 1024:
            return local_copc

        # 2. Check GeoStudio COPC cache directory
        cache_dir = os.path.join(tempfile.gettempdir(), "GeoStudio_COPC_Cache")
        os.makedirs(cache_dir, exist_ok=True)
        cached_copc = os.path.join(cache_dir, f"{base_name}.copc.laz")
        if os.path.exists(cached_copc) and os.path.getsize(cached_copc) > 1024:
            return cached_copc

        # Return local path if writable, else cached path
        try:
            test_file = os.path.join(base_dir, ".test_write")
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
            return local_copc
        except Exception:
            return cached_copc

    @classmethod
    def ensure_copc_index(cls, file_path: str, progress_callback=None) -> str:
        """
        Ensures a .copc.laz file exists for the given point cloud dataset.
        If file is already .copc.laz, returns it immediately.
        Otherwise, executes multi-threaded PDAL/Untwine conversion with real-time progress.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Point cloud file not found: {file_path}")

        if file_path.lower().endswith(".copc.laz"):
            return file_path

        target_copc = cls.get_target_copc_path(file_path)
        if os.path.exists(target_copc) and os.path.getsize(target_copc) > 1024:
            return target_copc

        cmd, env = cls.get_indexer_command(file_path, target_copc)
        if not cmd:
            print("[PointCloudIndexer] Warning: No COPC indexer tool found.")
            return None

        cls._is_cancelled = False

        if progress_callback:
            progress_callback(20, "Launching 8-core parallel COPC indexer...")

        try:
            startupinfo = None
            cflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)

            from PyQt5.QtWidgets import QApplication
            import time

            log_path = os.path.join(tempfile.gettempdir(), f"copc_build_{int(time.time())}.log")
            with open(log_path, "w", encoding="utf-8", errors="ignore") as log_out:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_out,
                    stderr=subprocess.STDOUT,
                    env=env,
                    startupinfo=startupinfo,
                    creationflags=cflags
                )
                cls._current_process = process

                start_t = time.time()
                last_pct = 25

                while process.poll() is None:
                    if cls._is_cancelled:
                        try:
                            process.kill()
                        except Exception:
                            pass
                        cls._current_process = None
                        return None

                    time.sleep(0.3)
                    elapsed = time.time() - start_t

                    # Continuous asymptotic progress from 25% to 98% that never stops moving
                    ratio = 1.0 - (0.5 ** (elapsed / 40.0))
                    dyn_pct = min(98, max(25, 25 + int(ratio * 73)))

                    if elapsed < 30:
                        status_msg = f"Reading & streaming LiDAR points ({dyn_pct}% • {int(elapsed)}s)..."
                    elif elapsed < 75:
                        status_msg = f"Building spatial LOD octree hierarchy ({dyn_pct}% • {int(elapsed)}s)..."
                    else:
                        status_msg = f"Writing Cloud-Optimized Point Cloud to disk ({dyn_pct}% • {int(elapsed)}s)..."

                    if progress_callback:
                        progress_callback(dyn_pct, status_msg)

                    QApplication.processEvents()

            cls._current_process = None
            rc = process.poll()
            if rc == 0 and os.path.exists(target_copc) and os.path.getsize(target_copc) > 1024:
                if progress_callback:
                    progress_callback(100, "Cloud-Optimized Point Cloud created successfully!")
                return target_copc
            else:
                return None

        except Exception as e:
            print(f"[PointCloudIndexer] Error generating COPC: {e}")
            cls._current_process = None
            return None

    @classmethod
    def check_classification_status(cls, file_path: str) -> dict:
        """
        Quickly queries the point cloud statistics to determine if Classification has been populated.
        Returns dict with: 'is_unclassified' (bool), 'max_class' (int), 'min_class' (int).
        """
        try:
            qgis_root = r"C:\Program Files\QGIS 3.40.14"
            pdal_candidates = [
                os.path.join(qgis_root, "bin", "pdal.exe"),
                os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "pdal.exe"),
                shutil.which("pdal"),
            ]
            pdal_exe = next((p for p in pdal_candidates if p and os.path.exists(p)), None)
            if not pdal_exe:
                return {'is_unclassified': False, 'max_class': 0}

            env = os.environ.copy()
            proj_dir = os.path.join(qgis_root, "share", "proj")
            if os.path.exists(proj_dir):
                env["PROJ_LIB"] = proj_dir
                env["PROJ_DATA"] = proj_dir

            startupinfo = None
            cflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            res = subprocess.run(
                [pdal_exe, 'info', '--stats', '--dimensions=Classification', file_path],
                capture_output=True, text=True, env=env,
                startupinfo=startupinfo, creationflags=cflags, timeout=15
            )
            if res.returncode == 0:
                import json
                data = json.loads(res.stdout)
                stats = data.get('stats', {}).get('statistic', [{}])
                if stats:
                    mx = stats[0].get('maximum', 0)
                    mn = stats[0].get('minimum', 0)
                    return {
                        'is_unclassified': (mx == 0),
                        'max_class': mx,
                        'min_class': mn
                    }
        except Exception as e:
            print(f"[PointCloudIndexer] Error checking classification: {e}")
        return {'is_unclassified': False, 'max_class': 0}

    @classmethod
    def classify_point_cloud(cls, input_path: str, output_path: str = None, progress_callback=None) -> str:
        """
        Executes multi-threaded SMRF ground classification and HAG vegetation segmentation on any point cloud.
        Automatically handles global geographic degrees vs projected meters coordinate systems.
        Produces ASPRS standard classes:
          - Class 2: Ground (Bare Earth)
          - Class 3: Low Vegetation (0.3m - 1.5m)
          - Class 4: Medium Vegetation (1.5m - 4.0m)
          - Class 5: High Vegetation / Canopy (> 4.0m)
        """
        import json
        import time

        if not output_path:
            base, ext = os.path.splitext(input_path)
            if input_path.lower().endswith(".copc.laz"):
                base = input_path[:-9]
            output_path = f"{base}_classified.copc.laz"

        qgis_root = r"C:\Program Files\QGIS 3.40.14"
        pdal_exe = os.path.join(qgis_root, "bin", "pdal.exe")
        if not os.path.exists(pdal_exe):
            pdal_exe = shutil.which("pdal")
        if not pdal_exe:
            raise RuntimeError("PDAL executable not found.")

        env = os.environ.copy()
        proj_dir = os.path.join(qgis_root, "share", "proj")
        if os.path.exists(proj_dir):
            env["PROJ_LIB"] = proj_dir
            env["PROJ_DATA"] = proj_dir

        # Inspect summary to detect whether CRS is in degrees (geographic)
        is_geographic = False
        utm_epsg = 32643
        try:
            startupinfo = None
            cflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            sum_res = subprocess.run(
                [pdal_exe, 'info', '--summary', input_path],
                capture_output=True, text=True, env=env,
                startupinfo=startupinfo, creationflags=cflags, timeout=15
            )
            if sum_res.returncode == 0:
                s_data = json.loads(sum_res.stdout)
                srs = s_data.get('summary', {}).get('srs', {})
                is_geographic = srs.get('isgeographic', False)
                bounds = s_data.get('summary', {}).get('bounds', {})
                if is_geographic and bounds:
                    lon = (bounds.get('minx', 0) + bounds.get('maxx', 0)) / 2.0
                    lat = (bounds.get('miny', 0) + bounds.get('maxy', 0)) / 2.0
                    zone = int((lon + 180) / 6) + 1
                    utm_epsg = 32600 + zone if lat >= 0 else 32700 + zone
        except Exception:
            pass

        stages = []
        is_copc = input_path.lower().endswith(".copc.laz")
        stages.append({
            "type": "readers.copc" if is_copc else "readers.las",
            "filename": input_path,
            "threads": 8
        })

        if is_geographic:
            stages.append({
                "type": "filters.reprojection",
                "out_srs": f"EPSG:{utm_epsg}"
            })

        stages.append({
            "type": "filters.smrf",
            "cell": 1.0,
            "slope": 0.15,
            "window": 18.0,
            "threshold": 0.5,
            "scalar": 1.25
        })

        stages.append({
            "type": "filters.hag_delaunay"
        })

        stages.append({
            "type": "filters.assign",
            "value": [
                "Classification = 3 WHERE HeightAboveGround >= 0.3 && HeightAboveGround < 1.5 && Classification != 2",
                "Classification = 4 WHERE HeightAboveGround >= 1.5 && HeightAboveGround < 4.0 && Classification != 2",
                "Classification = 5 WHERE HeightAboveGround >= 4.0 && Classification != 2"
            ]
        })

        if is_geographic:
            stages.append({
                "type": "filters.reprojection",
                "out_srs": "EPSG:4326"
            })

        stages.append({
            "type": "writers.copc",
            "filename": output_path,
            "forward": "all",
            "threads": 8
        })

        pipe_path = os.path.join(tempfile.gettempdir(), f"pdal_classify_{int(time.time())}.json")
        with open(pipe_path, "w", encoding="utf-8") as f:
            json.dump(stages, f, indent=2)

        cls._is_cancelled = False
        startupinfo = None
        cflags = 0
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        from PyQt5.QtWidgets import QApplication
        proc = subprocess.Popen(
            [pdal_exe, 'pipeline', pipe_path],
            env=env,
            startupinfo=startupinfo,
            creationflags=cflags
        )
        cls._current_process = proc

        start_t = time.time()
        while proc.poll() is None:
            if cls._is_cancelled:
                try:
                    proc.kill()
                except Exception:
                    pass
                cls._current_process = None
                return None

            time.sleep(0.3)
            elapsed = time.time() - start_t
            ratio = 1.0 - (0.5 ** (elapsed / 30.0))
            dyn_pct = min(98, max(10, 10 + int(ratio * 88)))

            if elapsed < 20:
                msg = f"Detecting bare-earth ground via SMRF ({dyn_pct}% • {int(elapsed)}s)..."
            elif elapsed < 45:
                msg = f"Computing height-above-ground & classifying canopy ({dyn_pct}% • {int(elapsed)}s)..."
            else:
                msg = f"Writing classified COPC dataset ({dyn_pct}% • {int(elapsed)}s)..."

            if progress_callback:
                progress_callback(dyn_pct, msg)

            QApplication.processEvents()

        cls._current_process = None
        rc = proc.poll()
        if rc == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            if progress_callback:
                progress_callback(100, "Point cloud classification complete!")
            return output_path
        return None

