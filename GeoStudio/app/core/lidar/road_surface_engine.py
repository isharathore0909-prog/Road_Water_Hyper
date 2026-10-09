# -*- coding: utf-8 -*-
"""
GeoStudio - High-Performance Road Surface & Pavement Classification Engine
Multi-criteria DTM and LiDAR evidence pipeline for detecting road corridors and ASPRS Class 11:
- Bare-earth raster DTM generation (1.0m resolution) with distance-transform hole filling
- Multi-criteria evidence evaluation: Slope (|∇DTM|), Terrain Micro-Roughness (σZ),
  Overhead tree canopy clearance, and optional Spectral Contrast (RGB Albedo / Excess Green)
- Distance transform corridor width constraint (rejects massive planar fields without erasing corridors)
- Connected component filtering: aspect ratio (linearity), minimum length, and corridor area
- Morphological skeletonization & 3D centerline LineString extraction
- Automated polygonization of road ribbon boundaries via GDAL
- Responsive execution pumping Qt event loop to guarantee zero UI freezing
"""

import os
import math
from typing import Dict, Any, Callable, Optional, List, Tuple
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from .road_models import ProcessingContext
from .road_io import RoadSpatialReference, RoadVectorWriter


class RoadGroundEstimator:
    """Estimates local terrain ground baseline and Height Above Ground (HAG) in vectorized C/NumPy."""

    @staticmethod
    def compute_hag(
        coords: np.ndarray,
        las=None,
        grid_resolution_m: float = 1.0,
        ctx: Optional[ProcessingContext] = None
    ) -> Tuple[np.ndarray, np.ndarray, float, float, int, int]:
        """
        Derives Height Above Ground (HAG) and returns the bare-earth DTM raster.
        Returns: (hag, dtm, x_min, y_min, nx, ny)
        """
        if ctx:
            ctx.process_events()

        x_min, y_min = float(np.min(coords[:, 0])), float(np.min(coords[:, 1]))
        x_max, y_max = float(np.max(coords[:, 0])), float(np.max(coords[:, 1]))
        res = max(0.5, float(grid_resolution_m))

        nx = max(1, int(np.ceil((x_max - x_min) / res)) + 1)
        ny = max(1, int(np.ceil((y_max - y_min) / res)) + 1)

        classes = np.array(las.classification) if (las is not None and hasattr(las, "classification")) else None
        has_ground_class = (classes is not None) and (np.sum(classes == 2) > 50)

        gx = np.clip(((coords[:, 0] - x_min) / res).astype(np.int32), 0, nx - 1)
        gy = np.clip(((coords[:, 1] - y_min) / res).astype(np.int32), 0, ny - 1)
        row = (ny - 1) - gy
        col = gx
        flat_idx = row * nx + col

        dtm_flat = np.full(nx * ny, np.inf, dtype=np.float32)

        # 1. First pass: use ground points if present, else lowest returns
        if has_ground_class:
            ground_mask = (classes == 2)
            np.minimum.at(dtm_flat, flat_idx[ground_mask], coords[ground_mask, 2].astype(np.float32))
        else:
            np.minimum.at(dtm_flat, flat_idx, coords[:, 2].astype(np.float32))

        # 2. Fill remaining boundary voids with nearest valid cell via distance transform
        dtm = dtm_flat.reshape((ny, nx))
        voids = np.isinf(dtm)
        if np.any(voids):
            if np.all(voids):
                dtm.fill(float(np.min(coords[:, 2])))
            else:
                nearest_idx = ndimage.distance_transform_edt(voids, return_distances=False, return_indices=True)
                dtm = dtm[tuple(nearest_idx)]

        if ctx:
            ctx.process_events()

        cell_ground = dtm[row, col]
        hag = coords[:, 2].astype(np.float32) - cell_ground
        return hag, dtm, x_min, y_min, nx, ny


class RoadCenterlineSkeletonizer:
    """Extracts 1-pixel medial skeletons and continuous 3D LineStrings from road raster grids."""

    @staticmethod
    def zhang_suen_thinning(image: np.ndarray, max_iters: int = 50) -> np.ndarray:
        """Vectorized Zhang-Suen morphological thinning for 1-pixel centerline extraction."""
        skel = image.astype(np.uint8)
        for _ in range(max_iters):
            p2 = np.roll(skel, -1, axis=0)
            p3 = np.roll(np.roll(skel, -1, axis=0), 1, axis=1)
            p4 = np.roll(skel, 1, axis=1)
            p5 = np.roll(np.roll(skel, 1, axis=0), 1, axis=1)
            p6 = np.roll(skel, 1, axis=0)
            p7 = np.roll(np.roll(skel, 1, axis=0), -1, axis=1)
            p8 = np.roll(skel, -1, axis=1)
            p9 = np.roll(np.roll(skel, -1, axis=0), -1, axis=1)

            n_neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            c1 = (n_neighbors >= 2) & (n_neighbors <= 6)

            s = ((p2 == 0) & (p3 == 1)).astype(int) + \
                ((p3 == 0) & (p4 == 1)).astype(int) + \
                ((p4 == 0) & (p5 == 1)).astype(int) + \
                ((p5 == 0) & (p6 == 1)).astype(int) + \
                ((p6 == 0) & (p7 == 1)).astype(int) + \
                ((p7 == 0) & (p8 == 1)).astype(int) + \
                ((p8 == 0) & (p9 == 1)).astype(int) + \
                ((p9 == 0) & (p2 == 1)).astype(int)

            c2 = (s == 1)
            c3 = (p2 * p4 * p6 == 0)
            c4 = (p4 * p6 * p8 == 0)

            del1 = (skel == 1) & c1 & c2 & c3 & c4
            skel[del1] = 0

            p2 = np.roll(skel, -1, axis=0)
            p3 = np.roll(np.roll(skel, -1, axis=0), 1, axis=1)
            p4 = np.roll(skel, 1, axis=1)
            p5 = np.roll(np.roll(skel, 1, axis=0), 1, axis=1)
            p6 = np.roll(skel, 1, axis=0)
            p7 = np.roll(np.roll(skel, 1, axis=0), -1, axis=1)
            p8 = np.roll(skel, -1, axis=1)
            p9 = np.roll(np.roll(skel, -1, axis=0), -1, axis=1)

            n_neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            c1 = (n_neighbors >= 2) & (n_neighbors <= 6)
            s = ((p2 == 0) & (p3 == 1)).astype(int) + \
                ((p3 == 0) & (p4 == 1)).astype(int) + \
                ((p4 == 0) & (p5 == 1)).astype(int) + \
                ((p5 == 0) & (p6 == 1)).astype(int) + \
                ((p6 == 0) & (p7 == 1)).astype(int) + \
                ((p7 == 0) & (p8 == 1)).astype(int) + \
                ((p8 == 0) & (p9 == 1)).astype(int) + \
                ((p9 == 0) & (p2 == 1)).astype(int)

            c2 = (s == 1)
            c3 = (p2 * p4 * p8 == 0)
            c4 = (p2 * p6 * p8 == 0)

            del2 = (skel == 1) & c1 & c2 & c3 & c4
            skel[del2] = 0

            if not np.any(del1) and not np.any(del2):
                break

        return skel.astype(bool)

    @classmethod
    def trace_centerlines(
        cls,
        skel: np.ndarray,
        dtm: np.ndarray,
        dist_trans: np.ndarray,
        x_min: float,
        y_min: float,
        res: float,
        ny: int,
        min_line_length_m: float = 20.0
    ) -> List[Dict[str, Any]]:
        """Traces continuous 3D LineString geometry along skeleton pixels."""
        visited = np.zeros_like(skel, dtype=bool)
        rows, cols = np.where(skel)
        if len(rows) == 0:
            return []

        nbr_kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=int)
        nbr_count = ndimage.convolve(skel.astype(int), nbr_kernel, mode='constant') * skel

        # Endpoints first (pixels with 1 neighbor)
        endpoints = list(zip(rows[nbr_count[rows, cols] == 1], cols[nbr_count[rows, cols] == 1]))
        if not endpoints:
            endpoints = list(zip(rows, cols))

        min_nodes = max(3, int(min_line_length_m / res))
        lines = []

        for sr, sc in endpoints:
            if visited[sr, sc]:
                continue

            chain = [(sr, sc)]
            visited[sr, sc] = True
            curr_r, curr_c = sr, sc

            while True:
                found_next = False
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < skel.shape[0] and 0 <= nc < skel.shape[1]:
                            if skel[nr, nc] and not visited[nr, nc]:
                                visited[nr, nc] = True
                                chain.append((nr, nc))
                                curr_r, curr_c = nr, nc
                                found_next = True
                                break
                    if found_next:
                        break
                if not found_next:
                    break

            if len(chain) >= min_nodes:
                pts_3d = []
                widths = []
                for r, c in chain:
                    xc = x_min + c * res
                    yc = y_min + (ny - 1 - r) * res
                    zc = float(dtm[r, c])
                    w = float(dist_trans[r, c] * 2.0)
                    pts_3d.append((xc, yc, zc))
                    widths.append(w)

                seg_len = float(len(chain) * res)
                dz = abs(pts_3d[-1][2] - pts_3d[0][2])
                slope_pct = (dz / seg_len * 100.0) if seg_len > 0 else 0.0

                lines.append({
                    "coords": pts_3d,
                    "length_m": round(seg_len, 1),
                    "mean_width_m": round(float(np.mean(widths)), 1),
                    "start_z_m": round(pts_3d[0][2], 2),
                    "end_z_m": round(pts_3d[-1][2], 2),
                    "slope_pct": round(slope_pct, 2)
                })

        return lines


class RoadPavementClassifier:
    """Identifies road corridors using DTM slope, micro-roughness, spectral contrast, and geometry constraints."""

    @classmethod
    def identify_road_grid(
        cls,
        coords: np.ndarray,
        candidate_indices: np.ndarray,
        dtm: np.ndarray,
        x_min: float,
        y_min: float,
        res: float,
        nx: int,
        ny: int,
        las=None,
        max_roughness_m: float = 0.08,
        max_slope_pct: float = 15.0,
        max_corridor_width_m: float = 14.0,
        min_corridor_area_m2: float = 20.0,
        ctx: Optional[ProcessingContext] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Derives the binary road corridor grid and distance transform.
        Returns: (road_grid, dist_trans)
        """
        if ctx:
            ctx.progress(30, "Computing DTM slope and surface micro-roughness evidence...")

        # 1. DTM Gradient, Slope and Elevation Micro-Roughness
        zy, zx = np.gradient(dtm, res)
        slope = np.sqrt(zx * zx + zy * zy)
        m_dtm = ndimage.uniform_filter(dtm, size=3)
        rough = np.sqrt(np.maximum(0.0, ndimage.uniform_filter((dtm - m_dtm) ** 2, size=3)))

        # 2. Seed raster grid from near-ground candidate returns
        cand_coords = coords[candidate_indices]
        cgx = np.clip(((cand_coords[:, 0] - x_min) / res).astype(np.int32), 0, nx - 1)
        cgy = np.clip(((cand_coords[:, 1] - y_min) / res).astype(np.int32), 0, ny - 1)
        crow = (ny - 1) - cgy
        ccol = cgx
        cflat = crow * nx + ccol

        grid = np.zeros((ny, nx), dtype=bool)
        grid[crow, ccol] = True

        # 3. Slope and Roughness Threshold Filtering
        slope_thresh = max(0.08, max_slope_pct / 100.0)
        rough_thresh = max(0.05, max_roughness_m * 1.5)
        grid = grid & (slope <= slope_thresh) & (rough <= rough_thresh)

        # 4. Spectral Evidence (when point cloud has populated RGB)
        has_rgb = (
            (las is not None)
            and hasattr(las, "red")
            and hasattr(las, "green")
            and (int(np.max(las.red)) > 0 or int(np.max(las.green)) > 0)
        )
        if has_rgb:
            if ctx:
                ctx.progress(45, "Evaluating multispectral albedo and vegetation indices...")
            r_pts = np.array(las.red, dtype=np.float32) // 256
            g_pts = np.array(las.green, dtype=np.float32) // 256
            b_pts = np.array(las.blue, dtype=np.float32) // 256

            sr = np.zeros(ny * nx, dtype=np.float32)
            sg = np.zeros(ny * nx, dtype=np.float32)
            sb = np.zeros(ny * nx, dtype=np.float32)
            scnt = np.zeros(ny * nx, dtype=np.float32)

            np.add.at(sr, cflat, r_pts[candidate_indices])
            np.add.at(sg, cflat, g_pts[candidate_indices])
            np.add.at(sb, cflat, b_pts[candidate_indices])
            np.add.at(scnt, cflat, 1.0)

            val = (scnt > 0).reshape((ny, nx))
            r_im = np.zeros((ny, nx), dtype=np.float32)
            g_im = np.zeros((ny, nx), dtype=np.float32)
            b_im = np.zeros((ny, nx), dtype=np.float32)
            r_im[val] = sr.reshape((ny, nx))[val] / scnt.reshape((ny, nx))[val]
            g_im[val] = sg.reshape((ny, nx))[val] / scnt.reshape((ny, nx))[val]
            b_im[val] = sb.reshape((ny, nx))[val] / scnt.reshape((ny, nx))[val]

            exg = 2.0 * g_im - r_im - b_im
            brightness = (r_im + g_im + b_im) / 3.0

            # Roads are neutral gray/brown pavement/gravel (ExG <= 4.5) and non-dark (Brightness >= 42.0)
            grid = grid & (exg <= 4.5) & (brightness >= 42.0)

        # 5. Morphological opening: eliminate narrow 1-pixel tractor tracks and speckles
        k_open = ndimage.generate_binary_structure(2, 1)
        grid = ndimage.binary_opening(grid, structure=k_open, iterations=1)

        # 6. Distance Transform Wide Core Excision: eliminate broad open fields & pastures
        #    Identifies wide interiors (half-width > 6.0m) and excises the core AND its 8m perimeter margin.
        #    This completely prevents hollow donut ring artifacts along field borders.
        dist_field = ndimage.distance_transform_edt(grid) * res
        field_thresh = max(6.0, max_corridor_width_m * 0.5)
        field_cores = dist_field > field_thresh
        if np.any(field_cores):
            dist_from_cores = ndimage.distance_transform_edt(~field_cores) * res
            grid = grid & (dist_from_cores > (field_thresh + 2.0))

        if ctx:
            ctx.progress(65, "Evaluating corridor elongation and geometric linearity...")

        # 7. Connected Component Geometric Ribbon Filtering directly on corridors
        #    (without dilation that bridges ditches into adjacent fields)
        labeled, num_features = ndimage.label(grid)
        sizes = ndimage.sum(grid, labeled, range(1, num_features + 1))
        dist_trans = ndimage.distance_transform_edt(grid) * res
        valid_labels = []

        min_area = max(20.0, min_corridor_area_m2)
        for lbl in range(1, num_features + 1):
            comp_area_m2 = sizes[lbl - 1] * res * res
            if comp_area_m2 < min_area:
                continue

            comp_mask = (labeled == lbl)
            d_vals = dist_trans[comp_mask]
            mean_w = max(1.0, float(np.mean(d_vals)) * 2.0)
            max_w = float(np.max(d_vals)) * 2.0
            est_len = comp_area_m2 / mean_w
            ratio = est_len / mean_w

            # Road corridors are linear ribbons with bounded mean width and high aspect ratio
            if max_w <= (max_corridor_width_m * 1.25) and est_len >= 35.0 and ratio >= 2.5:
                valid_labels.append(lbl)

        road_grid = np.isin(labeled, valid_labels)

        # Bridge small internal corridor gaps within confirmed road ribbons
        road_grid = ndimage.binary_closing(road_grid, structure=np.ones((3, 3)))
        dist_trans = ndimage.distance_transform_edt(road_grid) * res

        return road_grid, dist_trans

    @classmethod
    def identify_road_points(
        cls,
        coords: np.ndarray,
        candidate_indices: np.ndarray,
        dtm: np.ndarray,
        road_grid: np.ndarray,
        x_min: float,
        y_min: float,
        res: float,
        nx: int,
        ny: int,
        max_hag_m: float = 0.35,
        canopy_mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Maps road grid mask back to points within candidate indices."""
        cand_coords = coords[candidate_indices]
        cgx = np.clip(((cand_coords[:, 0] - x_min) / res).astype(np.int32), 0, nx - 1)
        cgy = np.clip(((cand_coords[:, 1] - y_min) / res).astype(np.int32), 0, ny - 1)
        crow = (ny - 1) - cgy
        ccol = cgx

        cell_ground = dtm[crow, ccol]
        hag = cand_coords[:, 2].astype(np.float32) - cell_ground

        in_corridor = road_grid[crow, ccol]
        hag_valid = (hag >= -0.25) & (hag <= max_hag_m)

        road_mask = in_corridor & hag_valid
        return candidate_indices[road_mask]

    @staticmethod
    def calculate_pavement_area(road_grid: np.ndarray, grid_res_m: float = 1.0) -> float:
        return float(np.sum(road_grid) * (grid_res_m ** 2))


class RoadSurfaceEngine:
    """Standalone engine for high-performance road surface and pavement point cloud classification."""

    @classmethod
    def classify_road_surface(
        cls,
        input_las_path: str,
        output_las_path: Optional[str] = None,
        output_vector_path: Optional[str] = None,
        road_centerline_vector: Optional[str] = None,
        max_corridor_width_m: float = 12.0,
        max_hag_m: float = 0.35,
        min_planarity: float = 0.65,
        max_roughness_m: float = 0.08,
        min_verticality: float = 0.85,
        min_intensity: Optional[float] = None,
        max_intensity: Optional[float] = None,
        min_corridor_area_m2: float = 50.0,
        export_footprint_polygon: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Detects and classifies road pavement points into ASPRS Class 11 (Road Surface)."""
        import laspy
        ctx = ProcessingContext(progress_callback, log_callback)

        ctx.progress(5, f"Reading LiDAR point cloud: {os.path.basename(input_las_path)}...")
        ctx.log(f"Loading point cloud: <code>{input_las_path}</code>")

        las = laspy.read(input_las_path)
        point_count = len(las.x)
        coords = np.vstack((las.x, las.y, las.z)).T
        srs = RoadSpatialReference.from_las(las)

        grid_res = 1.0
        ctx.progress(15, f"Rasterizing high-resolution bare-earth DTM ({grid_res}m cells)...")
        hag, dtm, x_min, y_min, nx, ny = RoadGroundEstimator.compute_hag(
            coords, las=las, grid_resolution_m=grid_res, ctx=ctx
        )

        ctx.log(f"Generated DTM grid: <b>{nx:,} × {ny:,}</b> cells across terrain extent")

        # Initial near-ground candidates
        cand_mask = (hag >= -0.25) & (hag <= max_hag_m)
        classes = np.array(las.classification) if hasattr(las, "classification") else None
        has_ground = (classes is not None) and (np.sum(classes == 2) > 50)
        if has_ground:
            cand_mask &= (classes == 2)
        elif classes is not None:
            cand_mask &= ~np.isin(classes, [3, 4, 5, 6, 7, 18])

        candidate_indices = np.where(cand_mask)[0]
        if len(candidate_indices) == 0:
            raise ValueError("No near-ground points found within specified height threshold.")

        ctx.log(f"Near-ground returns for road evaluation: <b>{len(candidate_indices):,}</b> points")

        # Reference road alignment vector guidance if provided
        if road_centerline_vector and os.path.exists(road_centerline_vector):
            ctx.log(f"Applying road alignment vector guidance: <code>{os.path.basename(road_centerline_vector)}</code>")
            from .road_io import RoadDataLoader
            cl_pts, _ = RoadDataLoader.load_centerline_coords_with_srs(road_centerline_vector)
            if len(cl_pts) > 0:
                half_w = max(2.5, max_corridor_width_m / 2.0)
                tree_cl = cKDTree(cl_pts[:, :2])
                dist_cl, _ = tree_cl.query(coords[candidate_indices, :2])
                candidate_indices = candidate_indices[dist_cl <= half_w]
                ctx.log(f"Centerline corridor envelope ({max_corridor_width_m:.1f}m): narrowed to <b>{len(candidate_indices):,}</b> candidates")

        # Radiometric intensity filtering if explicitly configured
        if hasattr(las, "intensity") and (min_intensity is not None or max_intensity is not None):
            ints = np.array(las.intensity[candidate_indices], dtype=np.float32)
            mask_int = np.ones(len(candidate_indices), dtype=bool)
            if min_intensity is not None:
                mask_int &= (ints >= min_intensity)
            if max_intensity is not None:
                mask_int &= (ints <= max_intensity)
            candidate_indices = candidate_indices[mask_int]

        # Multi-criteria DTM and morphology evidence pipeline
        road_grid, dist_trans = RoadPavementClassifier.identify_road_grid(
            coords=coords,
            candidate_indices=candidate_indices,
            dtm=dtm,
            x_min=x_min,
            y_min=y_min,
            res=grid_res,
            nx=nx,
            ny=ny,
            las=las,
            max_roughness_m=max_roughness_m,
            max_slope_pct=15.0,
            max_corridor_width_m=max_corridor_width_m,
            min_corridor_area_m2=min_corridor_area_m2,
            ctx=ctx
        )

        road_indices = RoadPavementClassifier.identify_road_points(
            coords=coords,
            candidate_indices=candidate_indices,
            dtm=dtm,
            road_grid=road_grid,
            x_min=x_min,
            y_min=y_min,
            res=grid_res,
            nx=nx,
            ny=ny,
            max_hag_m=max_hag_m
        )

        road_count = len(road_indices)
        road_pct = round((road_count / point_count * 100) if point_count > 0 else 0.0, 2)
        road_area_m2 = RoadPavementClassifier.calculate_pavement_area(road_grid, grid_res_m=grid_res)
        ctx.log(f"Confirmed Road Surface points (ASPRS 11): <b>{road_count:,}</b> (<b>{road_pct}%</b>)")
        ctx.log(f"Estimated continuous pavement area: <b>{road_area_m2:,.1f} m²</b>")

        # Reclassify output LAS
        ctx.progress(85, "Writing ASPRS Class 11 to output point cloud...")
        if not output_las_path:
            base, ext = os.path.splitext(input_las_path)
            output_las_path = f"{base}_roads_classified{ext if ext else '.laz'}"

        if classes is not None:
            classes[road_indices] = 11
            las.classification = classes
        else:
            new_classes = np.zeros(point_count, dtype=np.uint8)
            new_classes[road_indices] = 11
            las.classification = new_classes

        las.write(output_las_path)
        ctx.log(f"Saved reclassified LiDAR file: <code>{output_las_path}</code>")

        footprint_vector_path = None
        if export_footprint_polygon and road_area_m2 >= 10.0:
            ctx.progress(92, "Exporting road corridor boundary polygons and 3D centerlines...")
            if not output_vector_path:
                base = os.path.splitext(output_las_path)[0]
                output_vector_path = f"{base}_corridor.gpkg"

            # 1. Trace 3D Centerlines from medial skeleton
            skel = RoadCenterlineSkeletonizer.zhang_suen_thinning(road_grid)
            lines = RoadCenterlineSkeletonizer.trace_centerlines(
                skel=skel,
                dtm=dtm,
                dist_trans=dist_trans,
                x_min=x_min,
                y_min=y_min,
                res=grid_res,
                ny=ny,
                min_line_length_m=20.0
            )

            # 2. Write polygon boundaries and centerlines into GeoPackage
            RoadVectorWriter.write_pavement_boundary(
                points=coords[road_indices] if road_count > 0 else np.empty((0, 3)),
                out_path=output_vector_path,
                srs=srs,
                road_grid=road_grid,
                grid_meta={"x_min": x_min, "y_min": y_min, "res": grid_res, "nx": nx, "ny": ny, "dtm": dtm},
                centerlines=lines
            )
            footprint_vector_path = output_vector_path
            ctx.log(f"Exported road boundary polygons and <b>{len(lines)}</b> centerlines: <code>{output_vector_path}</code>")

        ctx.progress(100, "Road surface classification complete!")

        return {
            "total_points": point_count,
            "road_points_class_11": road_count,
            "road_points_pct": road_pct,
            "estimated_pavement_area_m2": round(road_area_m2, 1),
            "output_las_path": output_las_path,
            "footprint_vector": footprint_vector_path,
        }


__all__ = [
    "RoadGroundEstimator",
    "RoadCenterlineSkeletonizer",
    "RoadPavementClassifier",
    "RoadSurfaceEngine",
]
