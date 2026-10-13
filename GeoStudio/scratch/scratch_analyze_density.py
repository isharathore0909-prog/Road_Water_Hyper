import laspy
import numpy as np

with laspy.open(r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz') as fh:
    las = fh.read()
    print("Total points:", len(las.x))
    
    # Check flight strips / point source id
    if hasattr(las, 'point_source_id'):
        psids, counts = np.unique(las.point_source_id, return_counts=True)
        print("Point source IDs and counts:")
        for psi, cnt in zip(psids, counts):
            print(f"  ID {psi}: {cnt} points")
            
    # Check GPS time range
    if hasattr(las, 'gps_time'):
        print(f"GPS time: min {np.min(las.gps_time)}, max {np.max(las.gps_time)}")
        
    # Check classification distribution
    cls, c_counts = np.unique(las.classification, return_counts=True)
    print("Classifications:")
    for c, cnt in zip(cls, c_counts):
        print(f"  Class {c}: {cnt} points")

    # Let's inspect spatial density of ALL 18.8M points vs the sampled 1.2M points:
    # Divide into 20x20 grid
    x_min, x_max = np.min(las.x), np.max(las.x)
    y_min, y_max = np.min(las.y), np.max(las.y)
    
    h_all, _, _ = np.histogram2d(las.x, las.y, bins=10)
    print("\nFull 18.8M points 10x10 density (points per grid cell):")
    for row in reversed(h_all.T):
        print("  " + " ".join(f"{int(v):7d}" for v in row))

    # Now let's check with step=15
    h_step, _, _ = np.histogram2d(las.x[::15], las.y[::15], bins=10)
    print("\nSampled [::15] 10x10 density:")
    for row in reversed(h_step.T):
        print("  " + " ".join(f"{int(v):7d}" for v in row))
