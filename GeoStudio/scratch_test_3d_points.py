import laspy
import numpy as np

for path in [r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.copc.laz', r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz']:
    with laspy.open(path) as fh:
        total = fh.header.point_count
        print(f"File: {path}, total_points: {total}")
        las = fh.read()
        print(f"  las points read: {len(las.x)}")
        
        # Test step slicing: step = max(1, total // 1200000)
        step = max(1, total // 1200000)
        xs = np.array(las.x[::step])
        ys = np.array(las.y[::step])
        print(f"  Sampled count with step {step}: {len(xs)}")
        
        # Check spatial distribution: divide into 4 quadrants
        x_mid = (np.min(xs) + np.max(xs)) / 2
        y_mid = (np.min(ys) + np.max(ys)) / 2
        q_bl = np.sum((xs <= x_mid) & (ys <= y_mid))
        q_br = np.sum((xs > x_mid) & (ys <= y_mid))
        q_tl = np.sum((xs <= x_mid) & (ys > y_mid))
        q_tr = np.sum((xs > x_mid) & (ys > y_mid))
        print(f"  Quadrant point distribution:")
        print(f"    Bottom-Left: {q_bl} ({q_bl/len(xs)*100:.1f}%)")
        print(f"    Bottom-Right: {q_br} ({q_br/len(xs)*100:.1f}%)")
        print(f"    Top-Left: {q_tl} ({q_tl/len(xs)*100:.1f}%)")
        print(f"    Top-Right: {q_tr} ({q_tr/len(xs)*100:.1f}%)")
