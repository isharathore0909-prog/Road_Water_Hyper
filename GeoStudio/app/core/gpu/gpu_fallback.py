# -*- coding: utf-8 -*-
"""
GeoStudio - CPU Fallback Kernels (NumPy / SciPy Vectorized)
Equivalent mathematical implementations of terrain and spectral algorithms for systems without CUDA.
"""

import math
import numpy as np


class CpuFallbackKernels:
    """Multi-threaded NumPy/SciPy fallback routines."""

    @classmethod
    def compute_slope_aspect_hillshade(
        cls,
        dem_tile: np.ndarray,
        cellsize_x: float,
        cellsize_y: float,
        z_factor: float = 1.0,
        azimuth_deg: float = 315.0,
        altitude_deg: float = 45.0,
        mode: str = "slope"
    ) -> np.ndarray:
        """NumPy implementation of Horn's 3x3 algorithm."""
        data = dem_tile.astype(np.float32)
        if z_factor != 1.0:
            data = data * z_factor

        # 3x3 Horn kernels on numpy slices
        # z1 z2 z3
        # z4 z5 z6
        # z7 z8 z9
        z1 = data[:-2, :-2]
        z2 = data[:-2, 1:-1]
        z3 = data[:-2, 2:]
        z4 = data[1:-1, :-2]
        z6 = data[1:-1, 2:]
        z7 = data[2:, :-2]
        z8 = data[2:, 1:-1]
        z9 = data[2:, 2:]

        dz_dx = ((z3 + 2.0 * z6 + z9) - (z1 + 2.0 * z4 + z7)) / (8.0 * cellsize_x)
        dz_dy = ((z7 + 2.0 * z8 + z9) - (z1 + 2.0 * z2 + z3)) / (8.0 * cellsize_y)

        if mode == "slope":
            slope_rad = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
            return np.degrees(slope_rad).astype(np.float32)

        elif mode == "aspect":
            aspect_rad = np.arctan2(dz_dy, -dz_dx)
            aspect_deg = np.degrees(aspect_rad)
            aspect_deg = np.where(aspect_deg < 0.0, 90.0 - aspect_deg, 90.0 - aspect_deg)
            aspect_deg = np.where(aspect_deg > 90.0, 360.0 - aspect_deg + 90.0, 90.0 - aspect_deg)
            return np.remainder(aspect_deg, 360.0).astype(np.float32)

        elif mode == "hillshade":
            zenith_rad = math.radians(90.0 - altitude_deg)
            azimuth_rad = math.radians(azimuth_deg)

            slope_rad = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
            aspect_rad = np.arctan2(dz_dy, -dz_dx)

            c_zen = math.cos(zenith_rad)
            s_zen = math.sin(zenith_rad)

            hs = (c_zen * np.cos(slope_rad)) + (s_zen * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad))
            hs = np.clip(hs * 255.0, 0.0, 255.0)
            return hs.astype(np.float32)

        elif mode == "tri":
            return np.sqrt(dz_dx ** 2 + dz_dy ** 2).astype(np.float32)

        return data[1:-1, 1:-1].astype(np.float32)

    @classmethod
    def compute_spectral_index(cls, index_type: str, bands: dict) -> np.ndarray:
        """Vectorized NumPy spectral index computation."""
        eps = 1e-7

        if index_type == "ndvi":
            nir, red = bands["nir"].astype(np.float32), bands["red"].astype(np.float32)
            return np.clip((nir - red) / (nir + red + eps), -1.0, 1.0)

        elif index_type == "evi":
            nir, red = bands["nir"].astype(np.float32), bands["red"].astype(np.float32)
            blue = bands.get("blue", red).astype(np.float32)
            return np.clip(2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + eps), -1.0, 1.0)

        elif index_type == "savi":
            nir, red = bands["nir"].astype(np.float32), bands["red"].astype(np.float32)
            L = 0.5
            return np.clip(((nir - red) / (nir + red + L + eps)) * (1.0 + L), -1.0, 1.0)

        elif index_type == "ndwi":
            green, nir = bands["green"].astype(np.float32), bands["nir"].astype(np.float32)
            return np.clip((green - nir) / (green + nir + eps), -1.0, 1.0)

        elif index_type == "ndbi":
            swir, nir = bands["swir1"].astype(np.float32), bands["nir"].astype(np.float32)
            return np.clip((swir - nir) / (swir + nir + eps), -1.0, 1.0)

        elif index_type == "nbr":
            nir, swir2 = bands["nir"].astype(np.float32), bands["swir2"].astype(np.float32)
            return np.clip((nir - swir2) / (nir + swir2 + eps), -1.0, 1.0)

        elif index_type == "ndsi":
            green, swir1 = bands["green"].astype(np.float32), bands["swir1"].astype(np.float32)
            return np.clip((green - swir1) / (green + swir1 + eps), -1.0, 1.0)

        nir, red = bands["nir"].astype(np.float32), bands["red"].astype(np.float32)
        return np.clip((nir - red) / (nir + red + eps), -1.0, 1.0)
