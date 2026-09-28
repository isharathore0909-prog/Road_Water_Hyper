# -*- coding: utf-8 -*-
"""GeoStudio - Global Dark Stylesheet."""

DARK_STYLESHEET = """
/* ═══════════════════════════════════════════════════════════════
   GeoStudio — Professional Dark GIS Theme
   Inspired by: QGIS Dark, JetBrains IDEs, ArcGIS Pro Dark
   ═══════════════════════════════════════════════════════════════ */

/* ── Global ─────────────────────────────────────────────────── */
QMainWindow, QDialog, QWidget {
    background-color: #0d1b2a;
    color: #cfd8dc;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 12px;
}

/* ── Menu Bar ────────────────────────────────────────────────── */
QMenuBar {
    background: #0a1628;
    color: #b0bec5;
    border-bottom: 1px solid #1a3a5c;
    padding: 2px 4px;
    font-size: 12px;
}
QMenuBar::item {
    padding: 5px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #1565c0;
    color: #e3f2fd;
}

/* ── Menus ───────────────────────────────────────────────────── */
QMenu {
    background: #0f2337;
    color: #cfd8dc;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    padding: 4px 0;
}
QMenu::item {
    padding: 6px 28px 6px 16px;
}
QMenu::item:selected {
    background: #1565c0;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #1a3a5c;
    margin: 3px 8px;
}

/* ── Toolbars ────────────────────────────────────────────────── */
QToolBar {
    background: #0a1628;
    border-bottom: 1px solid #1a3a5c;
    spacing: 3px;
    padding: 3px 6px;
}
QToolBar::separator {
    background: #1a3a5c;
    width: 1px;
    margin: 4px 4px;
}
QToolButton {
    background: transparent;
    color: #90caf9;
    border: none;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
}
QToolButton:hover {
    background: #1a3a5c;
    color: #e3f2fd;
}
QToolButton:pressed {
    background: #1565c0;
}
QToolButton:checked {
    background: #0d47a1;
    border: 1px solid #1976d2;
}

/* ── Dock Widgets ────────────────────────────────────────────── */
QDockWidget {
    color: #90caf9;
    font-weight: bold;
    font-size: 12px;
    titlebar-close-icon: none;
}
QDockWidget::title {
    background: #0f2337;
    padding: 6px 8px;
    border-bottom: 1px solid #1a3a5c;
    text-align: left;
}
QDockWidget::close-button, QDockWidget::float-button {
    background: transparent;
    border: none;
    padding: 2px;
    border-radius: 3px;
}
QDockWidget::close-button:hover { background: #c62828; }

/* ── Splitter ────────────────────────────────────────────────── */
QSplitter::handle {
    background: #1a3a5c;
}
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }
QSplitter::handle:hover { background: #1976d2; }

/* ── Scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0d1b2a;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #1a3a5c;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: #1565c0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #0d1b2a;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #1a3a5c;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover { background: #1565c0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Tab Widget ──────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1a3a5c;
    background: #0d1b2a;
    border-radius: 4px;
}
QTabBar::tab {
    background: #0a1628;
    color: #78909c;
    border: 1px solid #1a3a5c;
    padding: 6px 14px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1565c0;
    color: #ffffff;
    font-weight: bold;
    border-color: #1976d2;
}
QTabBar::tab:hover:!selected {
    background: #1a3a5c;
    color: #e3f2fd;
}

/* ── Buttons ─────────────────────────────────────────────────── */
QPushButton {
    background: #1565c0;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton:hover   { background: #1976d2; }
QPushButton:pressed { background: #0d47a1; }
QPushButton:disabled { background: #37474f; color: #607d8b; }
QPushButton:flat    { background: transparent; color: #90caf9; }
QPushButton:flat:hover { background: #1a3a5c; }

/* ── Input Fields ────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background: #0f2337;
    color: #e0e0e0;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #1565c0;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #1976d2;
    outline: none;
}

QComboBox {
    background: #0f2337;
    color: #cfd8dc;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #0f2337;
    color: #cfd8dc;
    selection-background-color: #1565c0;
    border: 1px solid #1a3a5c;
}

QSpinBox, QDoubleSpinBox {
    background: #0f2337;
    color: #cfd8dc;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    padding: 4px 6px;
}

/* ── Group Box ───────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1a3a5c;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #90caf9;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    top: -7px;
    padding: 0 4px;
    background: #0d1b2a;
}

/* ── Progress Bar ────────────────────────────────────────────── */
QProgressBar {
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    background: #0f2337;
    text-align: center;
    color: #cfd8dc;
    font-size: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1565c0, stop:1 #0288d1);
    border-radius: 3px;
}

/* ── List / Tree Widgets ─────────────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget {
    background: #0f2337;
    color: #cfd8dc;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    outline: none;
}
QListWidget::item, QTreeWidget::item {
    padding: 4px 6px;
    border-radius: 3px;
}
QListWidget::item:selected, QTreeWidget::item:selected {
    background: #1565c0;
    color: #ffffff;
}
QListWidget::item:hover, QTreeWidget::item:hover {
    background: #1a3a5c;
}
QHeaderView::section {
    background: #0a1628;
    color: #90caf9;
    border: none;
    border-bottom: 1px solid #1a3a5c;
    border-right: 1px solid #1a3a5c;
    padding: 5px 8px;
    font-weight: bold;
}

/* ── Check Box / Radio ───────────────────────────────────────── */
QCheckBox, QRadioButton {
    color: #b0bec5;
    spacing: 6px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 14px; height: 14px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid #37474f;
    background: #0f2337;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background: #1565c0;
    border: 1px solid #1976d2;
    border-radius: 3px;
}

/* ── Tooltip ─────────────────────────────────────────────────── */
QToolTip {
    background: #1a3a5c;
    color: #e3f2fd;
    border: 1px solid #1976d2;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 11px;
}

/* ── Slider ──────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #1a3a5c;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #1976d2;
    width: 14px; height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::handle:horizontal:hover { background: #42a5f5; }
"""
