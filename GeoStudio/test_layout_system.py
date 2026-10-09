import sys
import os
import traceback

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

    # Test adding items dynamically
    print("Testing add_label_item...", flush=True)
    designer.add_label_item()
    print("Testing add_shape_item...", flush=True)
    designer.add_shape_item()
    current_items = [it for it in layout_a4.items() if hasattr(it, "id")]
    assert len(current_items) >= 6, "Dynamic items insertion failed"
    print("[3/5] Layout Designer window & dynamic items verified!", flush=True)

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
