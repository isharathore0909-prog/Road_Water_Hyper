import laspy
import numpy as np

for name, path in [("COPC", r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.copc.laz'), ("LAZ", r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz')]:
    with laspy.open(path) as fh:
        las = fh.read()
        print(f"\n--- {name} ({len(las.x)} points) ---")
        
        # Look at the first 500,000 points vs the next 500,000 points
        pts1 = (las.x[:500000], las.y[:500000])
        pts2 = (las.x[500000:1000000], las.y[500000:1000000])
        pts_last = (las.x[-500000:], las.y[-500000:])
        
        print("First 500k: X range:", (np.min(pts1[0]), np.max(pts1[0])), "Y range:", (np.min(pts1[1]), np.max(pts1[1])))
        print("Second 500k: X range:", (np.min(pts2[0]), np.max(pts2[0])), "Y range:", (np.min(pts2[1]), np.max(pts2[1])))
        print("Last 500k: X range:", (np.min(pts_last[0]), np.max(pts_last[0])), "Y range:", (np.min(pts_last[1]), np.max(pts_last[1])))

        # When we do las.x[::15]:
        step = 15
        xs = np.array(las.x[::step])
        ys = np.array(las.y[::step])
        
        # Grid density: divide extent into 10x10 bins
        x_bins = np.linspace(np.min(xs), np.max(xs), 11)
        y_bins = np.linspace(np.min(ys), np.max(ys), 11)
        h, _, _ = np.histogram2d(xs, ys, bins=[x_bins, y_bins])
        print(f"Density grid 10x10 (min={np.min(h):.0f}, max={np.max(h):.0f}, mean={np.mean(h):.0f}):")
        # Print a 5x5 summary
        h5, _, _ = np.histogram2d(xs, ys, bins=5)
        for row in reversed(h5.T): # top to bottom (Y high to low)
            print("  " + " ".join(f"{int(v):6d}" for v in row))
