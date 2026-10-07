import time, laspy, numpy as np

path = r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz'
with laspy.open(path) as fh:
    total = fh.header.point_count
    las = fh.read()
    
    t0 = time.perf_counter()
    x = np.array(las.x, dtype=np.float32)
    y = np.array(las.y, dtype=np.float32)
    z = np.array(las.z, dtype=np.float32)
    
    # Target points: ~5,000,000
    target_pts = 5000000
    
    # Method A: Step slicing (step = total // target_pts = 3)
    step = max(1, total // target_pts)
    idx_step = slice(None, None, step)
    print(f"Step {step} count: {len(x[idx_step]):,}")
    
    # Spatial density comparison between left (X < mid) and right (X >= mid)
    mid_x = (np.min(x) + np.max(x)) / 2
    
    left_cnt = np.sum(x[idx_step] < mid_x)
    right_cnt = np.sum(x[idx_step] >= mid_x)
    print(f"Step slicing: Left half = {left_cnt:,} pts, Right half = {right_cnt:,} pts (ratio = {left_cnt/right_cnt:.2f}x)")
    
    # Method B: Spatial uniform sampling
    # If we compute voxel size to get ~target_pts
    # Bounding box area: (x_max - x_min) * (y_max - y_min)
    area = (np.max(x) - np.min(x)) * (np.max(y) - np.min(y))
    target_spacing = np.sqrt(area / target_pts)
    print(f"Target spatial spacing: {target_spacing:.2f} meters")
