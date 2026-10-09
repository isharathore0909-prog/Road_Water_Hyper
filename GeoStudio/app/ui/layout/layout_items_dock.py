# -*- coding: utf-8 -*-
"""
GeoStudio - Layout Items Dock Panel
Manages items in the current layout:
- Item list with icons, visibility toggles, and lock indicators
- Z-order management (Bring Forward, Send Backward)
- Rename, delete, and duplicate items
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QToolButton, QLabel, QMenu, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor

from resources.icons.icon_provider import get_icon


class LayoutItemsDock(QDockWidget):
    """Dock widget listing all items in the layout with Z-order & lock controls."""

    item_selected = pyqtSignal(object)  # QgsLayoutItem

    def __init__(self, layout_designer, parent=None):
        super().__init__("Items", parent or layout_designer)
        self.designer = layout_designer
        self.setObjectName("layout_items_dock")
        self.setMinimumWidth(220)
        self.setMaximumWidth(380)

        self._build_ui()

    def _build_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar for Items
        tb = QHBoxLayout()
        tb.setSpacing(2)

        btn_raise = QToolButton()
        btn_raise.setIcon(get_icon("zoom_next"))
        btn_raise.setToolTip("Raise Item (Bring Forward)")
        btn_raise.clicked.connect(self._raise_item)
        tb.addWidget(btn_raise)

        btn_lower = QToolButton()
        btn_lower.setIcon(get_icon("zoom_last"))
        btn_lower.setToolTip("Lower Item (Send Backward)")
        btn_lower.clicked.connect(self._lower_item)
        tb.addWidget(btn_lower)

        tb.addSpacing(6)

        btn_lock = QToolButton()
        btn_lock.setIcon(get_icon("edit"))
        btn_lock.setToolTip("Lock / Unlock Selected Item")
        btn_lock.clicked.connect(self._toggle_selected_lock)
        tb.addWidget(btn_lock)

        btn_delete = QToolButton()
        btn_delete.setIcon(get_icon("delete"))
        btn_delete.setToolTip("Delete Selected Item")
        btn_delete.clicked.connect(self._delete_item)
        tb.addWidget(btn_delete)

        tb.addStretch()

        btn_refresh = QToolButton()
        btn_refresh.setIcon(get_icon("refresh"))
        btn_refresh.setToolTip("Refresh Items List")
        btn_refresh.clicked.connect(self.refresh_items)
        tb.addWidget(btn_refresh)

        layout.addLayout(tb)

        # Tree Widget for Layout Items
        self.tree = QTreeWidget(container)
        self.tree.setHeaderLabels(["Item", "Type", "Lock"])
        self.tree.setColumnWidth(0, 130)
        self.tree.setColumnWidth(1, 65)
        self.tree.setColumnWidth(2, 45)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                font-size: 11px;
            }
            QTreeWidget::item { padding: 4px; }
            QTreeWidget::item:selected { background: #e2e8f0; color: #0f172a; font-weight: 600; }
        """)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemChanged.connect(self._on_item_checked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree, 1)

        container.setLayout(layout)
        self.setWidget(container)

    def refresh_items(self):
        """Populates the tree with items from the active QgsPrintLayout."""
        self.tree.blockSignals(True)
        self.tree.clear()

        layout = self.designer.layout
        if not layout:
            self.tree.blockSignals(False)
            return

        items = [it for it in layout.items() if hasattr(it, "id")]
        # Sort items by Z-value descending (top items first)
        items.sort(key=lambda it: it.zValue() if hasattr(it, "zValue") else 0, reverse=True)

        for item in items:
            name = item.id() if hasattr(item, "id") else (item.displayName() if hasattr(item, "displayName") else type(item).__name__)
            if not name:
                name = type(item).__name__.replace("QgsLayoutItem", "Item")
            item_type = type(item).__name__.replace("QgsLayoutItem", "")

            is_locked = item.isLocked() if hasattr(item, "isLocked") else False
            is_vis = item.isVisible() if hasattr(item, "isVisible") else True

            tree_item = QTreeWidgetItem(self.tree, [name, item_type, "🔒" if is_locked else ""])
            tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable)
            tree_item.setCheckState(0, Qt.Checked if is_vis else Qt.Unchecked)
            tree_item.setData(0, Qt.UserRole, item)

            # Icon based on type
            if "Map" in item_type:
                tree_item.setIcon(0, get_icon("new_project"))
            elif "Legend" in item_type:
                tree_item.setIcon(0, get_icon("layer_properties"))
            elif "ScaleBar" in item_type:
                tree_item.setIcon(0, get_icon("measure_dist"))
            elif "Picture" in item_type:
                tree_item.setIcon(0, get_icon("pan"))
            elif "Label" in item_type:
                tree_item.setIcon(0, get_icon("edit"))

        self.tree.blockSignals(False)

    def _on_tree_selection_changed(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        layout_item = selected_items[0].data(0, Qt.UserRole)
        if layout_item:
            self.item_selected.emit(layout_item)
            # Synchronize canvas selection
            layout = self.designer.layout
            if layout:
                layout.setSelectedItem(layout_item)

    def _on_item_checked(self, item, col):
        if col == 0:
            layout_item = item.data(0, Qt.UserRole)
            if layout_item:
                is_vis = (item.checkState(0) == Qt.Checked)
                layout_item.setVisibility(is_vis)

    def _raise_item(self):
        item = self._get_current_layout_item()
        if item and hasattr(item, "setZValue"):
            item.setZValue(item.zValue() + 1)
            self.refresh_items()

    def _lower_item(self):
        item = self._get_current_layout_item()
        if item and hasattr(item, "setZValue"):
            item.setZValue(max(0, item.zValue() - 1))
            self.refresh_items()

    def _toggle_selected_lock(self):
        item = self._get_current_layout_item()
        if item:
            item.setLocked(not item.isLocked())
            self.refresh_items()

    def _delete_item(self):
        item = self._get_current_layout_item()
        if item and self.designer.layout:
            self.designer.layout.removeLayoutItem(item)
            self.refresh_items()

    def _get_current_layout_item(self):
        selected = self.tree.selectedItems()
        return selected[0].data(0, Qt.UserRole) if selected else None

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        layout_item = item.data(0, Qt.UserRole)
        if not layout_item:
            return

        menu = QMenu(self)
        act_rename = menu.addAction("Rename Item...")
        act_rename.triggered.connect(lambda: self._rename_item(layout_item))

        act_lock = menu.addAction("Unlock Item" if layout_item.isLocked() else "Lock Item")
        act_lock.triggered.connect(self._toggle_selected_lock)

        act_del = menu.addAction("Delete Item")
        act_del.setIcon(get_icon("delete"))
        act_del.triggered.connect(self._delete_item)

        menu.exec_(self.tree.mapToGlobal(pos))

    def _rename_item(self, layout_item):
        old_id = layout_item.id() or ""
        new_name, ok = QInputDialog.getText(self, "Rename Layout Item", "New Name:", text=old_id)
        if ok and new_name.strip():
            layout_item.setId(new_name.strip())
            self.refresh_items()
