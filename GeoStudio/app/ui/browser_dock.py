# -*- coding: utf-8 -*-
"""
GeoStudio - GIS Browser & Catalog Panel
Dockable GIS data catalog providing hierarchical navigation of:
- Project items (Maps, Active Layers, Tables)
- Common GIS directories & Favorites
- System Drives & File System
Double-clicking or dragging supported GIS files automatically adds them to the Map Canvas.
"""

import os
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QToolButton, QLabel, QMenu, QAction,
    QMessageBox
)
from PyQt5.QtCore import Qt, QMimeData, QUrl, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont, QDrag

from resources.icons.icon_provider import get_icon

SUPPORTED_EXTENSIONS = {
    ".shp": "vector",
    ".gpkg": "vector",
    ".geojson": "vector",
    ".json": "vector",
    ".kml": "vector",
    ".kmz": "vector",
    ".tif": "raster",
    ".tiff": "raster",
    ".dem": "raster",
    ".dtm": "raster",
    ".dsm": "raster",
    ".asc": "raster",
    ".xyz": "raster",
    ".img": "raster",
    ".las": "lidar",
    ".laz": "lidar",
    ".copc.laz": "lidar",
    ".csv": "table",
}


class BrowserTreeWidget(QTreeWidget):
    """Tree widget with file drag support for map canvas drops."""

    file_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setDragEnabled(True)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.setStyleSheet("""
            QTreeWidget {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                font-size: 11px;
                outline: none;
                selection-background-color: #e2e8f0;
                selection-color: #0f172a;
            }
            QTreeWidget::item {
                padding: 4px 6px;
                border-radius: 3px;
            }
            QTreeWidget::item:selected {
                background: #e2e8f0;
                color: #0f172a;
                font-weight: 600;
            }
            QTreeWidget::item:hover:!selected {
                background: #f8fafc;
            }
        """)

    def _on_item_double_clicked(self, item, col):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.file_double_clicked.emit(file_path)
        else:
            item.setExpanded(not item.isExpanded())

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)
        item = self.currentItem()
        if not item:
            return super().mouseMoveEvent(event)
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            drag = QDrag(self)
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(file_path)])
            drag.setMimeData(mime)
            drag.exec_(Qt.CopyAction)
        else:
            super().mouseMoveEvent(event)


class BrowserDock(QDockWidget):
    """
    Professional GIS Catalog / Browser panel.
    Provides organized access to project layers, favorite GIS paths, and file drives.
    """

    add_layer_requested = pyqtSignal(str)

    def __init__(self, main_window=None, parent=None):
        super().__init__("Browser", parent or main_window)
        self.setObjectName("browser_dock")
        self.mw = main_window
        self.setMinimumWidth(240)
        self.setMaximumWidth(420)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._build_ui()
        self._populate_catalog()

    def _build_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header with Search and Refresh
        top_bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search browser...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1.5px solid #0f172a; }
        """)
        self.search_edit.textChanged.connect(self._filter_items)
        top_bar.addWidget(self.search_edit)

        btn_refresh = QToolButton()
        btn_refresh.setToolTip("Refresh Catalog")
        btn_refresh.setIcon(get_icon("refresh"))
        btn_refresh.setStyleSheet("QToolButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; } QToolButton:hover { background: #e2e8f0; }")
        btn_refresh.clicked.connect(self.refresh_catalog)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)

        # Tree View
        self.tree = BrowserTreeWidget(container)
        self.tree.file_double_clicked.connect(self._on_file_activated)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self.tree, 1)

        # Empty State Helper Label
        self.empty_label = QLabel("No GIS data found in this view.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 12px;")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        container.setLayout(layout)
        self.setWidget(container)

    def _populate_catalog(self):
        self.tree.clear()

        # ── 1. Project Root ───────────────────────────────────
        self.project_item = QTreeWidgetItem(self.tree, ["Project"])
        self.project_item.setFont(0, QFont("Segoe UI", 9, QFont.Bold))
        self.project_item.setIcon(0, get_icon("new_project"))
        self._update_project_subnodes()
        self.project_item.setExpanded(True)

        # ── 2. Favorites / Working Directories ───────────────
        self.fav_item = QTreeWidgetItem(self.tree, ["Favorites"])
        self.fav_item.setFont(0, QFont("Segoe UI", 9, QFont.Bold))
        self.fav_item.setIcon(0, get_icon("open_project"))

        # Add GeoStudio Workspace
        workspace_dir = r"M:\Geo Studio\GeoStudio"
        if os.path.exists(workspace_dir):
            self._add_folder_node(self.fav_item, "GeoStudio Project", workspace_dir)

        # User Documents
        docs_dir = os.path.expanduser("~/Documents")
        if os.path.exists(docs_dir):
            self._add_folder_node(self.fav_item, "Documents", docs_dir)

        # User Desktop
        desktop_dir = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop_dir):
            self._add_folder_node(self.fav_item, "Desktop", desktop_dir)

        self.fav_item.setExpanded(True)

        # ── 3. File System Drives ─────────────────────────────
        self.drives_item = QTreeWidgetItem(self.tree, ["Drives"])
        self.drives_item.setFont(0, QFont("Segoe UI", 9, QFont.Bold))
        self.drives_item.setIcon(0, get_icon("save_project"))

        # List Windows drives
        for letter in ["M", "C", "D", "E"]:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                self._add_folder_node(self.drives_item, f"Local Disk ({letter}:)", drive_path)

        self.drives_item.setExpanded(False)

    def _update_project_subnodes(self):
        self.project_item.takeChildren()

        # Active layers count
        layer_count = 0
        try:
            from qgis.core import QgsProject
            layer_count = len(QgsProject.instance().mapLayers())
        except Exception:
            pass

        layers_node = QTreeWidgetItem(self.project_item, [f"Layers ({layer_count})"])
        layers_node.setIcon(0, get_icon("layer_vector"))

        tables_node = QTreeWidgetItem(self.project_item, ["Tables"])
        tables_node.setIcon(0, get_icon("layer_properties"))

        results_node = QTreeWidgetItem(self.project_item, ["Analysis Results"])
        results_node.setIcon(0, get_icon("buffer"))

    def _add_folder_node(self, parent_item, label, dir_path):
        node = QTreeWidgetItem(parent_item, [label])
        node.setData(0, Qt.UserRole, dir_path)
        node.setIcon(0, get_icon("open_project"))
        # Add a dummy child to enable lazy folder expansion
        dummy = QTreeWidgetItem(node, ["Loading..."])
        dummy.setData(0, Qt.UserRole, "__dummy__")

    def _on_item_expanded(self, item):
        dir_path = item.data(0, Qt.UserRole)
        if not dir_path or not os.path.isdir(dir_path):
            return

        # Check if first child is dummy
        if item.childCount() == 1 and item.child(0).data(0, Qt.UserRole) == "__dummy__":
            item.takeChildren()
            try:
                entries = sorted(os.listdir(dir_path))
                # Add subdirectories first
                for entry in entries:
                    if entry.startswith(".") or entry.startswith("__"):
                        continue
                    full_p = os.path.join(dir_path, entry)
                    if os.path.isdir(full_p):
                        self._add_folder_node(item, entry, full_p)

                # Add supported GIS files
                for entry in entries:
                    full_p = os.path.join(dir_path, entry)
                    if os.path.isfile(full_p):
                        ext = os.path.splitext(entry)[1].lower()
                        if entry.lower().endswith(".copc.laz"):
                            ext = ".copc.laz"
                        if ext in SUPPORTED_EXTENSIONS:
                            file_node = QTreeWidgetItem(item, [entry])
                            file_node.setData(0, Qt.UserRole, full_p)
                            ftype = SUPPORTED_EXTENSIONS[ext]
                            if ftype == "vector":
                                file_node.setIcon(0, get_icon("layer_vector"))
                            elif ftype == "raster":
                                file_node.setIcon(0, get_icon("layer_raster"))
                            elif ftype == "lidar":
                                file_node.setIcon(0, get_icon("load_las"))
                            else:
                                file_node.setIcon(0, get_icon("layer_properties"))
            except Exception as e:
                err_node = QTreeWidgetItem(item, [f"Access denied ({e})"])
                err_node.setForeground(0, QColor("#ef4444"))

    def _on_file_activated(self, file_path):
        if not os.path.exists(file_path):
            return
        if self.mw and hasattr(self.mw, "layer_panel"):
            ext = os.path.splitext(file_path)[1].lower()
            if file_path.lower().endswith(".copc.laz"):
                ext = ".copc.laz"
            ftype = SUPPORTED_EXTENSIONS.get(ext)
            if ftype == "vector":
                self.mw.layer_panel.load_vector(file_path)
            elif ftype == "lidar":
                self.mw.layer_panel.load_point_cloud(file_path)
            elif ftype == "raster":
                self.mw.layer_panel.load_raster(file_path)
            elif ftype == "table":
                self.mw.layer_panel.load_csv(file_path)
        self.add_layer_requested.emit(file_path)

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        if not path or path == "__dummy__":
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px; font-size: 11px; }
            QMenu::item { padding: 5px 20px 5px 24px; border-radius: 4px; }
            QMenu::item:selected { background: #e2e8f0; color: #0f172a; font-weight: 600; }
        """)

        if os.path.isfile(path):
            act_add = menu.addAction("Add Layer to Map")
            act_add.setIcon(get_icon("add_vector"))
            act_add.triggered.connect(lambda: self._on_file_activated(path))

        if os.path.isdir(path):
            act_refresh = menu.addAction("Refresh Folder")
            act_refresh.setIcon(get_icon("refresh"))
            act_refresh.triggered.connect(lambda: self._refresh_folder(item))

        act_explorer = menu.addAction("Open in File Explorer")
        act_explorer.triggered.connect(lambda: self._open_in_explorer(path))

        menu.exec_(self.tree.mapToGlobal(pos))

    def _refresh_folder(self, item):
        item.takeChildren()
        dummy = QTreeWidgetItem(item, ["Loading..."])
        dummy.setData(0, Qt.UserRole, "__dummy__")
        item.setExpanded(False)
        item.setExpanded(True)

    def _open_in_explorer(self, path):
        import subprocess
        if os.path.isfile(path):
            subprocess.run(["explorer", "/select,", os.path.normpath(path)])
        elif os.path.isdir(path):
            subprocess.run(["explorer", os.path.normpath(path)])

    def _filter_items(self, query):
        query = query.strip().lower()
        if not query:
            for i in range(self.tree.topLevelItemCount()):
                self._set_item_visible_recursive(self.tree.topLevelItem(i), True)
            self.empty_label.hide()
            return

        has_match = False
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = self._filter_item_recursive(item, query)
            if match:
                has_match = True

        self.empty_label.setVisible(not has_match)

    def _filter_item_recursive(self, item, query):
        item_text = item.text(0).lower()
        direct_match = query in item_text
        child_match = False

        for i in range(item.childCount()):
            child = item.child(i)
            if self._filter_item_recursive(child, query):
                child_match = True

        visible = direct_match or child_match
        item.setHidden(not visible)
        if visible and child_match:
            item.setExpanded(True)
        return visible

    def _set_item_visible_recursive(self, item, visible):
        item.setHidden(not visible)
        for i in range(item.childCount()):
            self._set_item_visible_recursive(item.child(i), visible)

    def refresh_catalog(self):
        self._populate_catalog()
