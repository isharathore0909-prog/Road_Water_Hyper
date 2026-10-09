# -*- coding: utf-8 -*-
"""
GeoStudio - Desktop GIS Menu Bar Builder
Constructs the formal 13-category Desktop GIS menu system:
Project | Edit | View | Layer | Map | Selection | Analysis | Processing | Database | Plugins | Settings | Window | Help
"""

from PyQt5.QtWidgets import QAction, QMenuBar, QMenu
from PyQt5.QtGui import QKeySequence

from resources.icons.icon_provider import get_icon


def _act(parent, text, slot, shortcut=None, tip=None, icon_key=None):
    """Helper to create a configured QAction with optional vector icon."""
    if icon_key:
        a = QAction(get_icon(icon_key), text, parent)
    else:
        a = QAction(text, parent)
    if slot:
        a.triggered.connect(slot)
    if shortcut:
        a.setShortcut(QKeySequence(shortcut))
    if tip:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    return a


def build_main_menus(mw):
    """
    Builds the formal desktop GIS menu hierarchy for GeoStudio.
    """
    mb = mw.menuBar()
    mb.clear()

    # ── 1. Project ────────────────────────────────────────────
    m_proj = mb.addMenu("&Project")
    m_proj.addAction(_act(mw, "New Project", mw.new_project, "Ctrl+N", "Create new empty project", "new_project"))
    m_proj.addAction(_act(mw, "Open Project...", mw.open_project, "Ctrl+O", "Open existing QGIS project", "open_project"))
    m_proj.addSeparator()
    m_proj.addAction(_act(mw, "Save Project", mw.save_project, "Ctrl+S", "Save project file", "save_project"))
    m_proj.addAction(_act(mw, "Save Project As...", mw.save_project_as, "Ctrl+Shift+S", "Save project to new file", "save_project_as"))
    m_proj.addSeparator()
    m_proj.addAction(_act(mw, "New Print Layout...", mw.create_layout_from_current_map, "Ctrl+Shift+L", "Create a new print layout from current map", "print_map"))
    m_proj.addAction(_act(mw, "Layout Manager...", mw.open_layout_manager, tip="Manage project map layouts and templates", icon_key="layer_properties"))
    m_proj.addAction(_act(mw, "Quick Print / Export Map...", mw.print_map, "Ctrl+P", "Export high-resolution map image or PDF", "print_map"))
    m_proj.addSeparator()
    m_proj.addAction(_act(mw, "Project Properties...", mw.project_properties, tip="Configure project coordinate system & metadata"))
    m_proj.addSeparator()
    m_proj.addAction(_act(mw, "Close Project", mw.close_project, tip="Close current project"))
    m_proj.addAction(_act(mw, "Exit", mw.close, "Ctrl+Q", tip="Exit GeoStudio"))

    # ── 2. Edit ───────────────────────────────────────────────
    m_edit = mb.addMenu("&Edit")
    m_edit.addAction(_act(mw, "Undo", mw.undo_action, "Ctrl+Z", "Undo last edit", "zoom_last"))
    m_edit.addAction(_act(mw, "Redo", mw.redo_action, "Ctrl+Y", "Redo last edit", "zoom_next"))
    m_edit.addSeparator()
    m_edit.addAction(_act(mw, "Cut Features", mw.cut_features, "Ctrl+X", "Cut selected features to clipboard", "clip"))
    m_edit.addAction(_act(mw, "Copy Features", mw.copy_features, "Ctrl+C", "Copy selected features to clipboard"))
    m_edit.addAction(_act(mw, "Paste Features", mw.paste_features, "Ctrl+V", "Paste features from clipboard"))
    m_edit.addAction(_act(mw, "Delete Selected", mw.delete_selected, "Delete", "Delete selected features", "delete"))
    m_edit.addSeparator()
    m_edit.addAction(_act(mw, "Toggle Editing", mw.toggle_editing, "Ctrl+E", "Start or finish editing active layer", "toggle_edit"))

    # ── 3. View ───────────────────────────────────────────────
    m_view = mb.addMenu("&View")

    # Workspace Presets
    m_ws = m_view.addMenu("Workspace Presets")
    m_ws.addAction(_act(mw, "Default Workspace", lambda: mw.set_workspace_preset("default"), tip="Standard Map, Layers, and Browser"))
    m_ws.addAction(_act(mw, "Mapping", lambda: mw.set_workspace_preset("mapping"), tip="Clean canvas for cartography"))
    m_ws.addAction(_act(mw, "Analysis", lambda: mw.set_workspace_preset("analysis"), tip="Expanded Processing Toolbox layout"))
    m_ws.addAction(_act(mw, "Editing", lambda: mw.set_workspace_preset("editing"), tip="Attribute Table & Digitizing tools"))
    m_ws.addAction(_act(mw, "Remote Sensing", lambda: mw.set_workspace_preset("remotesensing"), tip="Raster & Spectral Analysis layout"))

    # Panels Submenu
    m_panels = m_view.addMenu("Panels")
    m_panels.addAction(_act(mw, "Browser Catalog", mw.toggle_browser_dock, tip="Toggle GIS Browser Catalog panel"))
    m_panels.addAction(_act(mw, "Layers Panel", mw.toggle_layer_dock, tip="Toggle Layer Tree panel"))
    m_panels.addAction(_act(mw, "Processing Toolbox", mw.toggle_processing_dock, "Ctrl+Alt+T", tip="Toggle Processing Toolbox"))
    m_panels.addAction(_act(mw, "Attribute Table", mw.toggle_attr_table_dock, "F6", tip="Toggle bottom Attribute Table dock"))
    m_panels.addAction(_act(mw, "Identify Results", mw.toggle_identify_dock, tip="Toggle Identify Results panel"))
    m_panels.addAction(_act(mw, "Remote Sensing Analytics", mw.toggle_remote_sensing_dock, tip="Toggle Remote Sensing & Hyperspectral dock"))
    m_panels.addAction(_act(mw, "Python Console", mw.toggle_python_console, "Ctrl+Alt+P", tip="Toggle interactive Python console"))

    # Toolbars Submenu
    m_tbs = m_view.addMenu("Toolbars")
    m_tbs.addAction(_act(mw, "Project Toolbar", lambda: mw.tb_file.setVisible(not mw.tb_file.isVisible())))
    m_tbs.addAction(_act(mw, "Navigation Toolbar", lambda: mw.tb_nav.setVisible(not mw.tb_nav.isVisible())))
    m_tbs.addAction(_act(mw, "Data Sources Toolbar", lambda: mw.tb_data.setVisible(not mw.tb_data.isVisible())))
    m_tbs.addAction(_act(mw, "Selection Toolbar", lambda: mw.tb_selection.setVisible(not mw.tb_selection.isVisible())))
    m_tbs.addAction(_act(mw, "Measurement Toolbar", lambda: mw.tb_measure.setVisible(not mw.tb_measure.isVisible())))
    m_tbs.addAction(_act(mw, "Context Actions Toolbar", lambda: mw.tb_context.setVisible(not mw.tb_context.isVisible())))
    m_tbs.addAction(_act(mw, "Terrain Toolbar", lambda: mw.tb_terrain.setVisible(not mw.tb_terrain.isVisible())))
    m_tbs.addAction(_act(mw, "LiDAR Toolbar", lambda: mw.tb_lidar.setVisible(not mw.tb_lidar.isVisible())))

    m_view.addSeparator()
    m_view.addAction(_act(mw, "Zoom In", mw.zoom_in, "Ctrl++", "Zoom into canvas", "zoom_in"))
    m_view.addAction(_act(mw, "Zoom Out", mw.zoom_out, "Ctrl+-", "Zoom out of canvas", "zoom_out"))
    m_view.addAction(_act(mw, "Zoom Full Extent", mw.zoom_full, "Ctrl+Shift+F", "Fit entire layer extent", "zoom_full"))
    m_view.addAction(_act(mw, "Zoom Last", mw.zoom_last, "Ctrl+[", "Previous map extent", "zoom_last"))
    m_view.addAction(_act(mw, "Zoom Next", mw.zoom_next, "Ctrl+]", "Next map extent", "zoom_next"))
    m_view.addSeparator()
    m_view.addAction(_act(mw, "Refresh Map Canvas", mw.refresh_canvas, "F5", "Force redraw canvas", "refresh"))

    # ── 4. Layer ──────────────────────────────────────────────
    m_layer = mb.addMenu("&Layer")
    m_add_layer = m_layer.addMenu("Add Layer")
    m_add_layer.addAction(_act(mw, "Add Vector Layer...", mw.add_vector, "Ctrl+Shift+V", "Open Shapefile, GeoPackage, GeoJSON", "add_vector"))
    m_add_layer.addAction(_act(mw, "Add Raster / DEM Layer...", mw.add_raster, "Ctrl+Shift+R", "Open GeoTIFF, DEM, Point Cloud", "add_raster"))
    m_add_layer.addAction(_act(mw, "Add Delimited Text (CSV)...", mw.add_csv, tip="Open CSV points layer", icon_key="add_csv"))
    m_add_layer.addAction(_act(mw, "Add WMS / WMTS Basemap...", mw.add_wms, tip="Connect OGC WMS/WMTS service", icon_key="add_wms"))
    m_add_layer.addAction(_act(mw, "Add OpenStreetMap...", mw.add_xyz_basemap, tip="Add OpenStreetMap web tiles", icon_key="add_xyz"))

    m_layer.addSeparator()
    m_layer.addAction(_act(mw, "Open Attribute Table", mw.open_attribute_table, "F6", "Inspect layer attributes", "layer_properties"))
    m_layer.addAction(_act(mw, "Layer Properties...", mw.layer_properties, "F3", "Configure layer symbology and metadata", "identify"))
    m_layer.addAction(_act(mw, "Duplicate Layer", lambda: mw.layer_panel.duplicate_layer(mw.layer_panel.get_active_layer()) if hasattr(mw.layer_panel, "duplicate_layer") else None, tip="Clone active layer"))
    m_layer.addSeparator()
    m_layer.addAction(_act(mw, "Remove Selected Layer", mw.remove_layer, "Ctrl+D", "Remove layer from project", "delete"))

    # ── 5. Map ────────────────────────────────────────────────
    m_map = mb.addMenu("&Map")
    m_map.addAction(_act(mw, "Pan", mw.set_pan_tool, tip="Pan map canvas", icon_key="pan"))
    m_map.addAction(_act(mw, "Zoom In", mw.set_zoom_in, tip="Interactive zoom box", icon_key="zoom_in"))
    m_map.addAction(_act(mw, "Zoom Out", mw.set_zoom_out, tip="Interactive zoom out", icon_key="zoom_out"))
    m_map.addAction(_act(mw, "Full Extent", mw.zoom_full, tip="Zoom to all layers", icon_key="zoom_full"))
    m_map.addSeparator()
    m_map.addAction(_act(mw, "Identify Features", mw.set_identify_tool, "I", "Click map features to view attributes", "identify"))
    m_map.addAction(_act(mw, "Measure Distance", mw.set_measure_distance, tip="Measure path length", icon_key="measure_dist"))
    m_map.addAction(_act(mw, "Measure Area", mw.set_measure_area, tip="Measure polygon area", icon_key="measure_area"))
    m_map.addAction(_act(mw, "Measure Bearing / Angle", mw.set_measure_angle, tip="Measure azimuth and angles"))
    m_map.addSeparator()
    m_map.addAction(_act(mw, "Set Map Projection (CRS)...", mw.set_project_crs, tip="Change project destination CRS"))
    m_map.addAction(_act(mw, "3D Terrain & Point Cloud Viewer...", mw.open_3d_viewer, tip="Open 3D perspective viewer", icon_key="view_3d"))

    # ── 6. Selection ──────────────────────────────────────────
    m_sel = mb.addMenu("&Selection")
    m_sel.addAction(_act(mw, "Select Features", mw.set_select_tool, tip="Select feature by point click", icon_key="select_single"))
    m_sel.addAction(_act(mw, "Select by Rectangle", lambda: mw.set_select_mode("rectangle"), tip="Marquee box selection", icon_key="select_rect"))
    m_sel.addAction(_act(mw, "Select by Polygon", lambda: mw.set_select_mode("polygon"), tip="Draw selection polygon", icon_key="select_polygon"))
    m_sel.addAction(_act(mw, "Select by Radius", lambda: mw.set_select_mode("radius"), tip="Radial buffer selection", icon_key="select_radius"))
    m_sel.addSeparator()
    m_sel.addAction(_act(mw, "Select All Features", mw.select_all_features, "Ctrl+A", "Select all features in layer"))
    m_sel.addAction(_act(mw, "Invert Selection", mw.invert_selection, "Ctrl+Shift+A", "Invert selected features"))
    m_sel.addAction(_act(mw, "Clear Selection", mw.clear_selection, "Ctrl+Alt+A", "Deselect all features", "clear_selection"))
    m_sel.addSeparator()
    m_sel.addAction(_act(mw, "Zoom to Selected Features", mw.zoom_to_selection, tip="Zoom canvas to selected geometry"))

    # ── 7. Analysis ───────────────────────────────────────────
    m_analysis = mb.addMenu("&Analysis")
    m_analysis.addAction(_act(mw, "Processing Toolbox", mw.toggle_processing_dock, "Ctrl+Alt+T", "Open searchable GIS processing tools"))
    m_analysis.addSeparator()
    m_analysis.addAction(_act(mw, "Volumetric Analysis & Stage-Storage...", mw.open_volumetric_analysis, icon_key="profile"))
    m_analysis.addAction(_act(mw, "Cut & Fill Surface Comparison...", mw.open_cut_fill, icon_key="cut_fill"))
    m_analysis.addAction(_act(mw, "Elevation Profile Tool...", mw.open_elevation_profile, icon_key="profile"))
    m_analysis.addAction(_act(mw, "Viewshed Analysis...", mw.open_viewshed, icon_key="viewshed"))
    m_analysis.addSeparator()
    m_analysis.addAction(_act(mw, "GPU Acceleration & VRAM Status...", mw.open_gpu_status))

    # ── 8. Raster ─────────────────────────────────────────────
    m_raster = mb.addMenu("&Raster")
    m_raster.addAction(_act(mw, "Raster Calculator...", mw.open_band_math_dialog, tip="Perform map algebra on raster layers"))
    m_raster.addAction(_act(mw, "Raster Statistics...", mw.raster_stats, tip="Compute statistical metrics across bands"))
    m_raster.addAction(_act(mw, "Crop / Clip Raster by Mask...", mw.open_crop_raster_dialog, icon_key="clip"))
    m_raster.addAction(_act(mw, "Reproject / Warp Raster...", mw.raster_reproject))
    m_raster.addSeparator()

    # Terrain sub
    m_ter = m_raster.addMenu("Terrain Analysis")
    m_ter.addAction(_act(mw, "Elevation Symbology & 3D Relief...", mw.open_dem_elevation_dialog, "Ctrl+Shift+E", icon_key="elevation"))
    m_ter.addAction(_act(mw, "Slope Calculation...", mw.open_slope_dialog, icon_key="slope"))
    m_ter.addAction(_act(mw, "Aspect Calculation...", mw.open_aspect_dialog, icon_key="aspect"))
    m_ter.addAction(_act(mw, "3D Hillshade Relief...", mw.open_hillshade_dialog, icon_key="hillshade"))
    m_ter.addAction(_act(mw, "Generate Contours...", mw.open_contour_dialog))
    m_ter.addAction(_act(mw, "Terrain Ruggedness (TRI)...", mw.open_tri_dialog))
    m_ter.addAction(_act(mw, "Topographic Position (TPI)...", mw.open_tpi_dialog))
    m_ter.addAction(_act(mw, "Topographic Wetness (TWI)...", mw.open_twi_dialog, icon_key="watershed"))

    # Hydrology sub
    m_hyd = m_raster.addMenu("Hydrology")
    m_hyd.addAction(_act(mw, "Fill Sinks", mw.open_hydro_fillsinks))
    m_hyd.addAction(_act(mw, "Flow Direction (D8)", mw.open_hydro_flowdir))
    m_hyd.addAction(_act(mw, "Flow Accumulation", mw.open_hydro_flowaccum))
    m_hyd.addAction(_act(mw, "Watershed Delineation", mw.open_hydro_watershed, icon_key="watershed"))

    # ── 9. Vector ─────────────────────────────────────────────
    m_vec = mb.addMenu("&Vector")
    m_vec.addAction(_act(mw, "Buffer...", mw.open_buffer_dialog, icon_key="buffer", tip="Create buffer polygon around features"))
    m_vec.addAction(_act(mw, "Clip...", mw.open_clip_dialog, icon_key="clip", tip="Clip vector features with overlay mask"))
    m_vec.addAction(_act(mw, "Dissolve...", mw.open_dissolve_dialog, tip="Merge adjacent features with common attribute"))
    m_vec.addAction(_act(mw, "Intersection...", mw.open_intersect_dialog, tip="Extract overlapping geometries"))
    m_vec.addAction(_act(mw, "Union...", mw.open_union_dialog, tip="Combine layers into unified geometry layer"))
    m_vec.addAction(_act(mw, "Difference...", mw.open_diff_dialog, tip="Extract areas outside overlay"))
    m_vec.addSeparator()
    m_vec.addAction(_act(mw, "Centroids...", mw.run_centroids, tip="Generate point centroids of polygons"))
    m_vec.addAction(_act(mw, "Convex Hull...", mw.run_convex_hull, tip="Generate convex hull boundaries"))
    m_vec.addAction(_act(mw, "Voronoi Polygons...", mw.run_voronoi, tip="Generate Thiessen/Voronoi polygons"))
    m_vec.addSeparator()
    m_vec.addAction(_act(mw, "Open Attribute Table", mw.open_attribute_table, "F6", icon_key="layer_properties"))

    # ── 10. Remote Sensing ────────────────────────────────────
    m_rs = mb.addMenu("&Remote Sensing")
    m_rs.addAction(_act(mw, "Remote Sensing Workspace", lambda: mw.set_workspace_preset("remotesensing"), tip="Switch to ENVI-style imagery layout"))
    m_rs.addAction(_act(mw, "Band Manager & RGB Composite...", mw.open_band_manager_dialog if hasattr(mw, "open_band_manager_dialog") else mw.open_composite_dialog, tip="Configure multispectral band combinations"))
    m_rs.addAction(_act(mw, "False Color Composite...", mw.open_composite_dialog))
    m_rs.addSeparator()

    m_indices = m_rs.addMenu("Spectral Indices")
    m_indices.addAction(_act(mw, "NDVI (Normalized Difference Vegetation)", lambda: mw.open_spectral_index("satellite:ndvi")))
    m_indices.addAction(_act(mw, "EVI (Enhanced Vegetation Index)", lambda: mw.open_spectral_index("satellite:evi")))
    m_indices.addAction(_act(mw, "NDWI (Normalized Difference Water)", lambda: mw.open_spectral_index("satellite:ndwi")))
    m_indices.addAction(_act(mw, "NDBI (Built-up Index)", lambda: mw.open_spectral_index("satellite:ndbi")))
    m_indices.addAction(_act(mw, "NBR (Normalized Burn Ratio)", lambda: mw.open_spectral_index("satellite:nbr")))

    m_hyp = m_rs.addMenu("Hyperspectral & Dimensionality")
    m_hyp.addAction(_act(mw, "Principal Component Analysis (PCA)...", mw.open_pca_dialog))
    m_hyp.addAction(_act(mw, "Spectral Angle Mapper (SAM)...", mw.open_sam_dialog))
    m_hyp.addAction(_act(mw, "Hyperspectral Band Stacking...", mw.open_band_stack_dialog))

    # ── 11. Processing ────────────────────────────────────────
    m_proc = mb.addMenu("&Processing")
    m_proc.addAction(_act(mw, "Processing Toolbox", mw.toggle_processing_dock, "Ctrl+Alt+T", tip="Toggle categorized processing toolbox"))
    m_proc.addAction(_act(mw, "GPU Acceleration & VRAM Status...", mw.open_gpu_status))
    m_proc.addAction(_act(mw, "Processing Settings & GPU Budget...", mw.open_processing_settings))

    # ── 12. Database ──────────────────────────────────────────
    m_db = mb.addMenu("&Database")
    m_db.addAction(_act(mw, "GeoPackage Manager...", lambda: mw.layer_panel._quick_add_vector()))
    m_db.addAction(_act(mw, "Execute Spatial SQL Query...", mw.toggle_python_console))

    # ── 13. Settings ──────────────────────────────────────────
    m_settings = mb.addMenu("&Settings")
    theme_menu = m_settings.addMenu("UI Theme")
    theme_menu.addAction(_act(mw, "Off-White Light Workstation", lambda: mw.set_theme("offwhite")))
    theme_menu.addAction(_act(mw, "Dark GIS Workstation", lambda: mw.set_theme("dark")))
    m_settings.addSeparator()
    m_settings.addAction(_act(mw, "Project Properties & CRS...", mw.project_properties))
    m_settings.addAction(_act(mw, "Processing Settings...", mw.open_processing_settings))

    # ── 14. Help ──────────────────────────────────────────────
    m_help = mb.addMenu("&Help")
    m_help.addAction(_act(mw, "GeoStudio Documentation", mw.open_docs))
    m_help.addAction(_act(mw, "About GeoStudio", mw.about))

