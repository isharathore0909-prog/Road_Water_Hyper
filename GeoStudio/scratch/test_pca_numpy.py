import numpy as np
from osgeo import gdal

# Test SVD on random multi-band array
bands = [np.random.rand(100, 100).astype(np.float32) for _ in range(4)]
stack = np.stack(bands, axis=-1) # shape (100, 100, 4)
flat = stack.reshape(-1, 4)
mean = np.mean(flat, axis=0)
flat_centered = flat - mean
cov = np.cov(flat_centered, rowvar=False)
eigvals, eigvecs = np.linalg.eigh(cov)
# sort descending
idx = np.argsort(eigvals)[::-1]
eigvecs = eigvecs[:, idx]
projected = np.dot(flat_centered, eigvecs)
proj_stack = projected.reshape(100, 100, 4)
print("Projected shape:", proj_stack.shape, "variance explained:", eigvals[idx] / np.sum(eigvals))
print("Pure numpy PCA works seamlessly!")
