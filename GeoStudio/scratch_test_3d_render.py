import sys, os, time
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

sys.path.insert(0, r'd:\DUPLICACY\GeoStudio\app')
from ui.viewer3d.window import GeoStudio3DViewerWindow
from ui.viewer3d.reader import PointCloudReader

path = r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz'
win = GeoStudio3DViewerWindow(file_path=path)
win.resize(1100, 850)
win.show()

# Test loading with max_points = 6,000,000
res = PointCloudReader.load_las_points(path, max_points=6000000)
pts_xyz, rgb, z_col, class_col, int_col, center, z_min, z_max, total_pts, color_dict = res
win.pts_xyz = pts_xyz
win.canvas.set_point_data(pts_xyz, rgb, z_col, class_col, int_col, mode="auto", color_dict=color_dict)
win.canvas.point_size = 4.5
win.canvas.set_top_view()

loop_end = time.time() + 2.0
while time.time() < loop_end:
    app.processEvents()
    time.sleep(0.05)

pix = win.canvas.grab()
pix.save(r'd:\DUPLICACY\GeoStudio\test_3d_6m_rendered.png')
print(f"Rendered {len(pts_xyz):,} points in 3D canvas successfully!")

app.quit()
