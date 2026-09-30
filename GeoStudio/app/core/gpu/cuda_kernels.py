# -*- coding: utf-8 -*-
"""
GeoStudio - High Performance CUDA GPU Processing Kernels
Accelerated raster algorithms using PyTorch/CuPy for terrain analysis, spectral indices, and PCA.
"""

import math
import numpy as np
from typing import Tuple, Optional


class CudaKernels:
    """CUDA GPU kernel implementations for raster & imagery processing."""

    @staticmethod
    def is_available() -> bool:
        """Check if CUDA execution backend is functional."""
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            pass
        try:
            import cupy as cp
            return cp.cuda.is_available()
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # TERRAIN ANALYSIS (SLOPE, ASPECT, HILLSHADE, TRI)
    # ═══════════════════════════════════════════════════════════════
    @classmethod
    def compute_slope_aspect_hillshade(
        cls,
        dem_tile: np.ndarray,
        cellsize_x: float,
        cellsize_y: float,
        z_factor: float = 1.0,
        azimuth_deg: float = 315.0,
        altitude_deg: float = 45.0,
        mode: str = "slope"  # "slope", "aspect", "hillshade", "tri"
    ) -> np.ndarray:
        """
        CUDA-accelerated Horn's 3x3 algorithm for Slope, Aspect, Hillshade, and TRI.
        Expected dem_tile shape: (H, W) with 1-pixel halo included.
        """
        import torch
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        # Transfer tile to GPU tensor
        tensor = torch.from_numpy(dem_tile.astype(np.float32)).to(device)
        tensor = tensor.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W) for conv2d

        # Apply z-factor
        if z_factor != 1.0:
            tensor = tensor * z_factor

        # Horn's 3x3 derivative filters
        # dx kernel: [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]] / (8 * cellsize_x)
        # dy kernel: [[-1, -2, -1], [0, 0, 0], [1, 2, 1]] / (8 * cellsize_y)
        dx_weight = torch.tensor([
            [-1.0, 0.0, 1.0],
            [-2.0, 0.0, 2.0],
            [-1.0, 0.0, 1.0]
        ], dtype=torch.float32, device=device).unsqueeze(0).unsqueeze(0) / (8.0 * cellsize_x)

        dy_weight = torch.tensor([
            [-1.0, -2.0, -1.0],
            [ 0.0,  0.0,  0.0],
            [ 1.0,  2.0,  1.0]
        ], dtype=torch.float32, device=device).unsqueeze(0).unsqueeze(0) / (8.0 * cellsize_y)

        # Compute partial derivatives on GPU
        dz_dx = torch.nn.functional.conv2d(tensor, dx_weight, padding=0).squeeze()
        dz_dy = torch.nn.functional.conv2d(tensor, dy_weight, padding=0).squeeze()

        if mode == "slope":
            # Slope in degrees = arctan(sqrt(p^2 + q^2)) * (180 / pi)
            slope_rad = torch.atan(torch.sqrt(dz_dx ** 2 + dz_dy ** 2))
            result = slope_rad * (180.0 / math.pi)

        elif mode == "aspect":
            # Aspect in degrees = 57.29578 * atan2(dy, -dx)
            aspect_rad = torch.atan2(dz_dy, -dz_dx)
            aspect_deg = aspect_rad * (180.0 / math.pi)
            # Adjust to 0 - 360 compass degrees
            result = torch.where(aspect_deg < 0.0, 90.0 - aspect_deg, aspect_deg)
            result = torch.where(aspect_deg > 90.0, 360.0 - aspect_deg + 90.0, 90.0 - aspect_deg)
            result = torch.remainder(result, 360.0)

        elif mode == "hillshade":
            zenith_rad = math.radians(90.0 - altitude_deg)
            azimuth_rad = math.radians(azimuth_deg)

            slope_rad = torch.atan(torch.sqrt(dz_dx ** 2 + dz_dy ** 2))
            aspect_rad = torch.atan2(dz_dy, -dz_dx)

            c_zen = math.cos(zenith_rad)
            s_zen = math.sin(zenith_rad)

            # Hillshade equation
            hs = (c_zen * torch.cos(slope_rad)) + (s_zen * torch.sin(slope_rad) * torch.cos(azimuth_rad - aspect_rad))
            result = torch.clamp(hs * 255.0, 0.0, 255.0)

        elif mode == "tri":
            # Topographic Roughness Index: sqrt(dx^2 + dy^2)
            result = torch.sqrt(dz_dx ** 2 + dz_dy ** 2)

        else:
            result = tensor.squeeze()

        # D2H Transfer back to host numpy array
        return result.cpu().numpy().astype(np.float32)

    # ═══════════════════════════════════════════════════════════════
    # SPECTRAL INDICES (NDVI, EVI, SAVI, NDWI, NDBI, NBR)
    # ═══════════════════════════════════════════════════════════════
    @classmethod
    def compute_spectral_index(
        cls,
        index_type: str,
        bands: dict  # {"nir": arr, "red": arr, "green": arr, "blue": arr, "swir1": arr, "swir2": arr}
    ) -> np.ndarray:
        """CUDA-accelerated vectorized spectral index computation."""
        import torch
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # Convert input bands to torch tensors on GPU
        t_bands = {}
        for k, v in bands.items():
            if v is not None:
                t_bands[k] = torch.from_numpy(v.astype(np.float32)).to(device)

        eps = 1e-7

        if index_type == "ndvi":
            nir, red = t_bands["nir"], t_bands["red"]
            result = (nir - red) / (nir + red + eps)

        elif index_type == "evi":
            nir, red, blue = t_bands["nir"], t_bands["red"], t_bands.get("blue", t_bands["red"])
            result = 2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + eps)

        elif index_type == "savi":
            nir, red = t_bands["nir"], t_bands["red"]
            L = 0.5
            result = ((nir - red) / (nir + red + L + eps)) * (1.0 + L)

        elif index_type == "ndwi":
            green, nir = t_bands["green"], t_bands["nir"]
            result = (green - nir) / (green + nir + eps)

        elif index_type == "ndbi":
            swir, nir = t_bands["swir1"], t_bands["nir"]
            result = (swir - nir) / (swir + nir + eps)

        elif index_type == "nbr":
            nir, swir2 = t_bands["nir"], t_bands["swir2"]
            result = (nir - swir2) / (nir + swir2 + eps)

        elif index_type == "ndsi":
            green, swir1 = t_bands["green"], t_bands["swir1"]
            result = (green - swir1) / (green + swir1 + eps)

        else:
            nir, red = t_bands["nir"], t_bands["red"]
            result = (nir - red) / (nir + red + eps)

        # Clamp results to valid [-1, 1] range for normalized indices
        result = torch.clamp(result, -1.0, 1.0)

        return result.cpu().numpy().astype(np.float32)

    # ═══════════════════════════════════════════════════════════════
    # HYPERSPECTRAL PCA (PRINCIPAL COMPONENT ANALYSIS)
    # ═══════════════════════════════════════════════════════════════
    @classmethod
    def compute_pca(cls, multiband_array: np.ndarray, num_components: int = 3) -> np.ndarray:
        """
        CUDA-accelerated PCA dimensionality reduction on multi-band hyperspectral data.
        multiband_array: shape (Bands, Height, Width)
        Returns: shape (num_components, Height, Width)
        """
        import torch
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        bands, h, w = multiband_array.shape
        # Reshape to (Pixels, Bands)
        X = torch.from_numpy(multiband_array.astype(np.float32)).to(device)
        X = X.view(bands, -1).t()  # (N_pixels, Bands)

        # Center data (subtract mean per band)
        mean = torch.mean(X, dim=0, keepdim=True)
        X_centered = X - mean

        # SVD on GPU: X = U * S * V.T
        U, S, V = torch.pca_lowrank(X_centered, q=min(num_components, bands), center=False)
        X_pca = torch.matmul(X_centered, V[:, :num_components])  # (N_pixels, num_components)

        # Reshape back to (num_components, H, W)
        result = X_pca.t().view(num_components, h, w)
        return result.cpu().numpy().astype(np.float32)
