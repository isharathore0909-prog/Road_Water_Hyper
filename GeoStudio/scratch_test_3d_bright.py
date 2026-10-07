import sys, os, time
from PyQt5.QtWidgets import QApplication
import numpy as np

app = QApplication(sys.argv)

sys.path.insert(0, r'd:\DUPLICACY\GeoStudio\app')
from ui.viewer3d.window import GeoStudio3DViewerWindow
from ui.viewer3d.reader import PointCloudReader

path = r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz'
win = GeoStudio3DViewerWindow(file_path=path)
win.resize(1100, 850)
win.show()

import laspy
with laspy.open(path) as fh:
    total = fh.header.point_count
    step = max(1, total // 6000000)
    las = fh.read()
    x = np.array(las.x[::step], dtype=np.float64)
    y = np.array(las.y[::step], dtype=np.float64)
    z = np.array(las.z[::step], dtype=np.float32)
    
    r_raw = np.array(las.red[::step], dtype=np.float32)
    g_raw = np.array(las.green[::step], dtype=np.float32)
    b_raw = np.array(las.blue[::step], dtype=np.float32)
    
    if np.max(r_raw) > 255:
        p1 = float(np.percentile(np.concatenate([r_raw, g_raw, b_raw]), 1))
        p99 = float(np.percentile(np.concatenate([r_raw, g_raw, b_raw]), 99))
        r = np.clip((r_raw - p1) / max(1.0, p99 - p1), 0.0, 1.0).astype(np.float32)
        g = np.clip((g_raw - p1) / max(1.0, p99 - p1), 0.0, 1.0).astype(np.float32)
        b = np.clip((b_raw - p1) / max(1.0, p99 - p1), 0.0, 1.0).astype(np.float32)
    else:
        r = (r_raw / 255.0).astype(np.float32)
        g = (g_raw / 255.0).astype(np.float32)
        b = (b_raw / 255.0).astype(np.float32)
        
    rgb = np.column_stack((r, g, b)).astype(np.float32)
    
    res = PointCloudReader._process_coordinates(x, y, z, rgb, None, None, total)
    pts_xyz, rgb_c, z_col, class_col, int_col, center, z_min, z_max, total_pts, color_dict = res
    
    win.pts_xyz = pts_xyz
    win.canvas.set_point_data(pts_xyz, rgb_c, z_col, class_col, int_col, mode="auto", color_dict=color_dict)
    win.canvas.point_size = 4.5
    win.canvas.set_top_view()

loop_end = time.time() + 2.0
while time.time() < loop_end:
    app.processEvents()
    time.sleep(0.05)

pix = win.canvas.grab()
pix.save(r'd:\DUPLICACY\GeoStudio\test_3d_6m_bright.png')
print("Saved bright 6M points 3D rendering!")

app.quit()
