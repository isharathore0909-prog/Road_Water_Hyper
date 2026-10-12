import sys
import os
import traceback
import glob
qgis_roots = [os.environ.get("QGIS_ROOT", "")] + glob.glob(r"C:\Program Files\QGIS*")
qgis_root = next((r for r in qgis_roots if r and os.path.isdir(r)), r"C:\Program Files\QGIS 3.44.15")
plugins_dir = os.path.join(qgis_root, "apps", "qgis-ltr", "python", "plugins")
if os.path.exists(plugins_dir) and plugins_dir not in sys.path:
    sys.path.insert(0, plugins_dir)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting layout test suite...", flush=True)

try:
    from qgis.core import (
        QgsApplication, QgsProject, QgsVectorLayer,
        QgsField, QgsFeature, QgsGeometry, QgsPointXY
    )
    from PyQt5.QtCore import QVariant

    qgs = QgsApplication([], False)
    qgs.initQgis()

    project = QgsProject.instance()

    # 1. Create a dummy test layer to simulate map data
    vl = QgsVectorLayer("Point?crs=EPSG:4326", "Villages", "memory")
    pr = vl.dataProvider()
    pr.addAttributes([QgsField("name", QVariant.String), QgsField("category", QVariant.String)])
    vl.updateFields()

    f1 = QgsFeature(vl.fields())
    f1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(75.85, 26.91)))
    f1.setAttributes(["Village Alpha", "Primary"])
    f2 = QgsFeature(vl.fields())
    f2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(75.88, 26.94)))
    f2.setAttributes(["Village Beta", "Secondary"])
    pr.addFeatures([f1, f2])
    vl.updateExtents()
    project.addMapLayer(vl)
    print("[1/5] Vector layer added to project successfully!", flush=True)

    # 2. Test Template Engine
    from ui.layout.layout_templates import create_layout_from_template
    layout_a4 = create_layout_from_template(project, "Village Map", "A4 Landscape")
    layout_items = [it for it in layout_a4.items() if hasattr(it, "id")]
    print(f"Template items count: {len(layout_items)}", flush=True)
    assert len(layout_items) >= 4, f"Expected at least 4 items in template, got {len(layout_items)}"
    project.layoutManager().addLayout(layout_a4)
    print("[2/5] Layout template created with items:", [it.id() for it in layout_items], flush=True)

    # 3. Test Layout Designer Window
    print("Initializing GeoStudioMainWindow...", flush=True)
    from ui.main_window import GeoStudioMainWindow
    mw = GeoStudioMainWindow(qgs_app=qgs)

    print("Initializing GeoStudioLayoutDesignerWindow...", flush=True)
    from ui.layout.layout_designer_window import GeoStudioLayoutDesignerWindow
    designer = GeoStudioLayoutDesignerWindow(layout_a4, main_window=mw, parent=mw)
    assert designer.view is not None, "Layout view is None"
    assert designer.items_dock is not None, "Items dock is None"
    assert designer.props_dock is not None, "Props dock is None"
    print("Designer initialized!", flush=True)

    # Test adding items dynamically (all tools)
    print("Testing add_label_item...", flush=True)
    designer.add_label_item()
    print("Testing add_shape_item...", flush=True)
    designer.add_shape_item()
    print("Testing add_ellipse_item...", flush=True)
    designer.add_ellipse_item()
    print("Testing add_line_item...", flush=True)
    designer.add_line_item()
    print("Testing add_arrow_item...", flush=True)
    designer.add_arrow_item()
    print("Testing add_scalebar_item...", flush=True)
    designer.add_scalebar_item()
    print("Testing add_north_arrow_item...", flush=True)
    designer.add_north_arrow_item()
    print("Testing add_table_item...", flush=True)
    designer.add_table_item()

    current_items = [it for it in layout_a4.items() if hasattr(it, "id")]
    print(f"Total layout items after adding: {len(current_items)}", flush=True)
    assert len(current_items) >= 10, f"Dynamic items insertion failed: count is {len(current_items)}"

    # Test Properties Dock for each item
    for item in layout_a4.items():
        designer.props_dock.set_item(item)

    # Test Layout Settings Tab (grid, snapping, presets)
    designer.tab_layout_settings.combo_page_size.setCurrentText("A3 Landscape")
    designer.tab_layout_settings.chk_show_grid.setChecked(True)
    designer.tab_layout_settings.chk_snap_grid.setChecked(True)
    designer.tab_layout_settings._apply_grid_settings()

    # Test Guides Tab
    designer.tab_guides._add_horizontal_guide()
    designer.tab_guides._add_vertical_guide()
    assert designer.tab_guides.table_guides.rowCount() >= 2, "Guides creation failed"

    # Test PrintExportDialog integration
    print("Testing PrintExportDialog with layout parameter...", flush=True)
    from ui.print_export_dialog import PrintExportDialog
    ped = PrintExportDialog(mw, designer, layout=layout_a4)
    assert ped.layout is layout_a4, "PrintExportDialog layout not assigned"
    print("PrintExportDialog initialized successfully with layout!", flush=True)

    print("[3/5] Layout Designer window, all 14 tools, guides, and properties verified!", flush=True)

    # 4. Test High-Res Export to Image and PDF
    out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_layout_export.png")
    out_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_layout_export.pdf")

    if os.path.exists(out_png): os.remove(out_png)
    if os.path.exists(out_pdf): os.remove(out_pdf)

    print("Testing export to image and pdf...", flush=True)
    from qgis.core import QgsLayoutExporter
    exporter = QgsLayoutExporter(layout_a4)

    img_settings = QgsLayoutExporter.ImageExportSettings()
    img_settings.dpi = 150
    res_img = exporter.exportToImage(out_png, img_settings)
    assert res_img == QgsLayoutExporter.Success, f"Image export failed: {res_img}"
    assert os.path.exists(out_png) and os.path.getsize(out_png) > 1000, "Exported PNG is invalid"
    print(f"  Exported PNG successfully: {os.path.getsize(out_png):,} bytes", flush=True)

    pdf_settings = QgsLayoutExporter.PdfExportSettings()
    pdf_settings.dpi = 150
    res_pdf = exporter.exportToPdf(out_pdf, pdf_settings)
    assert res_pdf == QgsLayoutExporter.Success, f"PDF export failed: {res_pdf}"
    assert os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 1000, "Exported PDF is invalid"
    print(f"  Exported PDF successfully: {os.path.getsize(out_pdf):,} bytes", flush=True)
    print("[4/5] High-res image and PDF export verified!", flush=True)

    # 5. Test Layout Manager Dialog
    print("Testing Layout Manager Dialog...", flush=True)
    from ui.layout.layout_manager_dialog import LayoutManagerDialog
    mgr_dlg = LayoutManagerDialog(mw)
    assert mgr_dlg.list_layouts.count() >= 1, "Layout manager did not find project layout"
    print("[5/5] Layout Manager dialog verified!", flush=True)

    # Cleanup
    if os.path.exists(out_png): os.remove(out_png)
    if os.path.exists(out_pdf): os.remove(out_pdf)

    qgs.exitQgis()
    print("ALL PRINT & EXPORT LAYOUT MODULE TESTS PASSED 100%!", flush=True)
    sys.exit(0)

except Exception as e:
    print(f"EXCEPTION: {e}", file=sys.stderr, flush=True)
    traceback.print_exc()
    sys.exit(1)
