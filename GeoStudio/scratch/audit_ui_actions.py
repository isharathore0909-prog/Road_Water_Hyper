import sys
import os
import traceback

qgis_root = r"C:\Program Files\QGIS 3.44.15"
qgis_app = os.path.join(qgis_root, "apps", "qgis-ltr")
qgis_py = os.path.join(qgis_root, "apps", "Python312")

for p in [
    os.path.join(qgis_app, "python"),
    os.path.join(qgis_app, "python", "plugins"),
    os.path.join(qgis_py, "Lib", "site-packages"),
    os.path.join(qgis_py, "Lib"),
    r"M:\Geo Studio\GeoStudio\app",
    r"M:\Geo Studio\GeoStudio",
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from PyQt5.QtWidgets import QApplication, QAction, QToolButton
from qgis.core import QgsApplication

QgsApplication.setPrefixPath(qgis_app, True)
app = QgsApplication([b"GeoStudio"], False)
app.initQgis()

from ui.main_window import GeoStudioMainWindow
win = GeoStudioMainWindow(qgs_app=app)

print("=" * 60)
print("AUDITING MAIN WINDOW MENUS AND ACTIONS")
print("=" * 60)

mb = win.menuBar()
menu_actions = []

def inspect_menu(menu, prefix=""):
    for action in menu.actions():
        sub = action.menu()
        if sub:
            inspect_menu(sub, f"{prefix}{action.text()} -> ")
        else:
            if not action.isSeparator():
                menu_actions.append((f"{prefix}{action.text()}", action))

for action in mb.actions():
    if action.menu():
        inspect_menu(action.menu(), f"{action.text()} -> ")

print(f"Total Menu Actions: {len(menu_actions)}")

toolbar_actions = []
for tb in win.findChildren(QApplication.allWidgets()[0].__class__):
    pass

from PyQt5.QtWidgets import QToolBar
for tb in win.findChildren(QToolBar):
    tb_name = tb.windowTitle() or tb.objectName()
    for act in tb.actions():
        if not act.isSeparator():
            toolbar_actions.append((f"[{tb_name}] {act.text() or act.toolTip()}", act))

print(f"Total Toolbar Actions: {len(toolbar_actions)}")

print("\n--- CHECKING METHODS ON GEOSTUDIO MAIN WINDOW ---")
missing_methods = []
for name, act in menu_actions + toolbar_actions:
    # See if the slot is callable or checks
    pass

# Direct inspection of all methods expected by menus
expected_methods = [
    "new_project", "open_project", "save_project", "save_project_as",
    "project_properties", "create_layout_from_current_map", "open_layout_manager",
    "print_map", "quick_export_map", "undo_action", "redo_action", "cut_features",
    "copy_features", "paste_features", "delete_selected", "toggle_editing",
    "zoom_in", "zoom_out", "zoom_full", "zoom_last", "zoom_next", "refresh_canvas",
    "add_vector", "add_raster", "add_csv", "add_wms", "add_xyz_basemap",
    "remove_layer", "layer_properties", "open_processing_settings", "set_project_crs",
    "open_plugin_manager", "toggle_python_console", "run_centroids", "run_convex_hull",
    "run_voronoi", "open_buffer_dialog", "open_dissolve_dialog", "open_clip_dialog",
    "open_intersect_dialog", "open_union_dialog", "open_diff_dialog",
    "open_attribute_table", "run_merge", "open_slope_dialog", "open_aspect_dialog",
    "open_hillshade_dialog", "open_tri_dialog", "open_twi_dialog", "open_contour_dialog",
    "open_hydro_fillsinks", "open_hydro_flowdir", "open_hydro_flowaccum",
    "open_hydro_watershed", "open_band_math_dialog", "raster_stats",
    "open_crop_raster_dialog", "raster_reproject", "open_composite_dialog",
    "open_band_stack_dialog", "open_pca_dialog", "open_sam_dialog",
    "open_dem_elevation_dialog", "open_elevation_profile", "open_viewshed",
    "open_volumetric_analysis", "open_cut_fill", "load_las_file", "open_3d_viewer",
    "toggle_processing_dock", "show_recently_used", "open_gpu_status",
    "open_docs", "about"
]

for m in expected_methods:
    if not hasattr(win, m):
        missing_methods.append(m)
        print(f"MISSING METHOD: win.{m}")
    else:
        fn = getattr(win, m)
        if not callable(fn):
            missing_methods.append(m)
            print(f"NOT CALLABLE: win.{m}")

if not missing_methods:
    print(f"ALL {len(expected_methods)} EXPECTED METHODS EXIST ON GeoStudioMainWindow!")
else:
    print(f"TOTAL MISSING METHODS: {len(missing_methods)}")

app.exitQgis()
