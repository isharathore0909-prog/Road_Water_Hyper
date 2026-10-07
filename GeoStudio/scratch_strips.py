import laspy
import numpy as np

with laspy.open(r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz') as fh:
    las = fh.read()
    psid = np.array(las.point_source_id)
    for id_val in [23, 24]:
        mask = (psid == id_val)
        xs = las.x[mask]
        ys = las.y[mask]
        print(f"Strip {id_val}: {np.sum(mask)} pts, X: ({np.min(xs):.1f}, {np.max(xs):.1f}), Y: ({np.min(ys):.1f}, {np.max(ys):.1f})")
