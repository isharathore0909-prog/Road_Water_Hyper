# -*- coding: utf-8 -*-
"""
GeoStudio - Modern Workstation UI Design System & Global Stylesheets
Provides high-fidelity, clean, and professional themes (Off-White Pro Light & Slate Pro Dark).
"""

# ── Font Stack ──────────────────────────────────────────────────
FONT_FAMILY = '"Segoe UI Variable Display", "Segoe UI", "Inter", -apple-system, system-ui, sans-serif'
MONO_FONT   = '"JetBrains Mono", "Cascadia Code", "Consolas", "Courier New", monospace'

# ═══════════════════════════════════════════════════════════════════
# 1. MODULE / DIALOG STYLESHEET
# ═══════════════════════════════════════════════════════════════════
MODULE_STYLE = f"""
    QWidget {{
        background: #ffffff;
        color: #0f172a;
        font-family: {FONT_FAMILY};
        font-size: 12px;
    }}
    QDialog {{
        background-color: #f8fafc;
        color: #0f172a;
    }}
    QGroupBox {{
        font-weight: 600;
        font-size: 11px;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 14px;
        padding: 10px 8px 8px 8px;
        background: #ffffff;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
        background: #ffffff;
        color: #0f172a;
        font-weight: 600;
    }}
    QPushButton {{
        background: #0f172a;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 6px 16px;
        font-weight: 600;
        font-size: 12px;
        min-height: 20px;
    }}
    QPushButton:hover {{ background: #1e293b; }}
    QPushButton:pressed {{ background: #334155; }}
    QPushButton:disabled {{ background: #e2e8f0; color: #94a3b8; }}
    QPushButton#blueBtn {{
        background: #0f172a;
        color: #ffffff;
    }}
    QPushButton#blueBtn:hover {{ background: #1e293b; }}
    QPushButton#grayBtn, QPushButton#toolBtn, QPushButton#secondaryBtn {{
        background: #ffffff;
        color: #334155;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 6px 14px;
        font-weight: 500;
        font-size: 11px;
        min-height: 18px;
    }}
    QPushButton#grayBtn:hover, QPushButton#toolBtn:hover, QPushButton#secondaryBtn:hover {{
        background: #f1f5f9;
        color: #0f172a;
        border-color: #94a3b8;
    }}
    QPushButton#grayBtn:pressed, QPushButton#toolBtn:pressed, QPushButton#secondaryBtn:pressed {{
        background: #e2e8f0;
    }}
    QPushButton:checked {{
        background: #e2e8f0;
        color: #0f172a;
        border: 1px solid #475569;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 5px 8px;
        font-size: 12px;
        selection-background-color: #cbd5e1;
        selection-color: #0f172a;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1.5px solid #0f172a;
        background: #ffffff;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background: #ffffff;
        color: #1e293b;
        selection-background-color: #e2e8f0;
        selection-color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 2px;
    }}
    QLabel {{
        color: #475569;
        font-size: 12px;
    }}
    QProgressBar {{
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        background: #f1f5f9;
        text-align: center;
        color: #334155;
        font-size: 11px;
        font-weight: 600;
        min-height: 18px;
    }}
    QProgressBar::chunk {{
        background: #0f172a;
        border-radius: 3px;
    }}
    QListWidget, QTreeWidget, QTableWidget, QTreeView, QTableView {{
        background: #ffffff;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        border-radius: 5px;
        font-size: 12px;
        outline: none;
        selection-background-color: #e2e8f0;
        selection-color: #0f172a;
    }}
    QTreeWidget::branch, QTreeView::branch {{
        background: transparent;
    }}
    QTreeWidget::branch:selected, QTreeView::branch:selected {{
        background: #e2e8f0;
    }}
    QTreeWidget::branch:hover:!selected, QTreeView::branch:hover:!selected {{
        background: #f8fafc;
    }}
    QListWidget::item, QTreeWidget::item, QTableWidget::item, QTreeView::item, QTableView::item {{
        padding: 5px 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected, QTreeView::item:selected, QTableView::item:selected {{
        background: #e2e8f0;
        color: #0f172a;
        font-weight: 600;
    }}
    QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected, QTableWidget::item:hover:!selected, QTreeView::item:hover:!selected, QTableView::item:hover:!selected {{
        background: #f8fafc;
    }}
    QCheckBox, QRadioButton {{
        color: #334155;
        font-size: 12px;
        spacing: 6px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 15px;
        height: 15px;
        border: 1px solid #94a3b8;
        border-radius: 3px;
        background: #ffffff;
    }}
    QRadioButton::indicator {{
        border-radius: 8px;
    }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: #0f172a;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: #0f172a;
        border: 1px solid #000000;
    }}
    QTabWidget::pane {{
        border: 1px solid #e2e8f0;
        background: #ffffff;
        border-radius: 6px;
        top: -1px;
    }}
    QTabWidget::tab-bar {{
        left: 6px;
    }}
    QTabBar::tab {{
        background: #f1f5f9;
        color: #64748b;
        padding: 7px 18px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid #e2e8f0;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        margin-right: 4px;
        margin-top: 2px;
        min-width: 68px;
    }}
    QTabBar::tab:selected {{
        background: #ffffff;
        color: #0f172a;
        font-weight: 700;
        border-bottom: 1px solid #ffffff;
        margin-top: 0px;
    }}
    QTabBar::tab:hover:!selected {{
        background: #e2e8f0;
        color: #0f172a;
    }}
    QToolTip {{
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 6px 10px;
        font-size: 11px;
    }}
"""


# ═══════════════════════════════════════════════════════════════════
# 2. OFF-WHITE PRO LIGHT THEME (Default Standalone GIS Workstation)
# ═══════════════════════════════════════════════════════════════════
OFFWHITE_STYLESHEET = f"""
/* ═══════════════════════════════════════════════════════════════
   GeoStudio — Professional Off-White Workstation Light Theme
   ═══════════════════════════════════════════════════════════════ */

/* ── Global ─────────────────────────────────────────────────── */
QMainWindow, QDialog, QWidget {{
    background-color: #f8fafc;
    color: #0f172a;
    font-family: {FONT_FAMILY};
    font-size: 12px;
}}

/* ── Menu Bar ────────────────────────────────────────────────── */
QMenuBar {{
    background-color: #ffffff;
    color: #334155;
    border-bottom: 1px solid #e2e8f0;
    padding: 3px 6px;
    font-size: 12px;
    font-weight: 500;
}}
QMenuBar::item {{
    padding: 5px 10px;
    border-radius: 4px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: #f1f5f9;
    color: #0f172a;
}}
QMenuBar::item:pressed {{
    background-color: #e2e8f0;
}}

/* ── Floating Menus ──────────────────────────────────────────── */
QMenu {{
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 0px;
}}
QMenu::item {{
    background-color: transparent;
    color: #1e293b;
    padding: 6px 36px 6px 32px;
    margin: 1px 4px;
    font-size: 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: 600;
}}
QMenu::item:disabled {{
    color: #94a3b8;
}}
QMenu::icon {{
    position: absolute;
    left: 8px;
    top: 5px;
}}
QMenu::separator {{
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 8px 4px 30px;
}}

/* ── Toolbars (Grouped Ribbon Containers) ────────────────────── */
QToolBar {{
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    spacing: 3px;
    padding: 3px 4px;
}}
QToolBar::separator {{
    background: #e2e8f0;
    width: 1px;
    margin: 4px 6px;
}}
QToolBar::handle:horizontal {{
    background: #cbd5e1;
    width: 4px;
    margin: 6px 2px;
    border-radius: 2px;
}}
QToolButton {{
    background: transparent;
    color: #334155;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px 6px;
    margin: 1px 1px;
    font-size: 11px;
    font-weight: 500;
}}
QToolButton:hover {{
    background: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
}}
QToolButton:pressed {{
    background: #e2e8f0;
    border: 1px solid #94a3b8;
}}
QToolButton:checked {{
    background: #e2e8f0;
    color: #0f172a;
    border: 1px solid #475569;
    font-weight: 600;
}}
QToolButton[popupMode="1"], QToolButton[popupMode="2"] {{
    padding-right: 8px;
}}

/* ── Dock Widgets (Panels) ───────────────────────────────────── */
QDockWidget {{
    color: #0f172a;
    font-weight: 600;
    font-size: 12px;
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: #f8fafc;
    color: #0f172a;
    padding: 7px 12px;
    border-bottom: 1px solid #e2e8f0;
    border-top: 1px solid #e2e8f0;
    text-align: left;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.3px;
}}
QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 3px;
    border-radius: 4px;
}}
QDockWidget::close-button:hover {{
    background: #fee2e2;
    color: #dc2626;
}}
QDockWidget::float-button:hover {{
    background: #f1f5f9;
    color: #0f172a;
}}

/* ── Splitters ───────────────────────────────────────────────── */
QSplitter::handle {{
    background: #e2e8f0;
}}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical   {{ height: 2px; }}
QSplitter::handle:hover {{ background: #475569; }}

/* ── Scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: #f8fafc;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #cbd5e1;
    min-height: 28px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{ background: #64748b; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: #f8fafc;
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: #cbd5e1;
    min-width: 28px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{ background: #64748b; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Tab Widgets ─────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 6px;
    top: -1px;
}}
QTabWidget::tab-bar {{
    left: 6px;
}}
QTabBar::tab {{
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
    padding: 7px 18px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 4px;
    margin-top: 2px;
    font-size: 11px;
    font-weight: 500;
    min-width: 68px;
}}
QTabBar::tab:selected {{
    background: #ffffff;
    color: #0f172a;
    font-weight: 700;
    border-bottom-color: #ffffff;
    margin-top: 0px;
}}
QTabBar::tab:hover:!selected {{
    background: #e2e8f0;
    color: #0f172a;
}}

/* ── Buttons ─────────────────────────────────────────────────── */
QPushButton {{
    background: #0f172a;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
    min-height: 20px;
}}
QPushButton:hover   {{ background: #1e293b; }}
QPushButton:pressed {{ background: #334155; }}
QPushButton:disabled {{ background: #e2e8f0; color: #94a3b8; }}
QPushButton:flat    {{ background: transparent; color: #0f172a; font-weight: 600; padding: 4px 8px; }}
QPushButton:flat:hover {{ background: #f1f5f9; }}

/* ── Input Fields ────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 12px;
    selection-background-color: #cbd5e1;
    selection-color: #0f172a;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1.5px solid #0f172a;
    outline: none;
}}

/* ── Combo Box / Spin Box ────────────────────────────────────── */
QComboBox {{
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 12px;
}}
QComboBox:focus {{ border: 1.5px solid #0f172a; }}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: #ffffff;
    color: #1e293b;
    selection-background-color: #e2e8f0;
    selection-color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 2px;
}}

QSpinBox, QDoubleSpinBox {{
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 6px;
    font-size: 12px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1.5px solid #0f172a; }}

/* ── Group Box ───────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-weight: 600;
    color: #0f172a;
    background: #ffffff;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background: #ffffff;
    color: #0f172a;
    font-weight: 600;
}}

/* ── Progress Bar ────────────────────────────────────────────── */
QProgressBar {{
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    background: #f1f5f9;
    text-align: center;
    color: #334155;
    font-size: 11px;
    font-weight: 600;
    min-height: 18px;
}}
QProgressBar::chunk {{
    background: #0f172a;
    border-radius: 3px;
}}

/* ── List / Tree / Table Widgets ─────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget, QTreeView, QTableView {{
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    outline: none;
    font-size: 12px;
    selection-background-color: #e2e8f0;
    selection-color: #0f172a;
}}
QTreeWidget::branch, QTreeView::branch {{
    background: transparent;
}}
QTreeWidget::branch:selected, QTreeView::branch:selected {{
    background: #e2e8f0;
}}
QTreeWidget::branch:hover:!selected, QTreeView::branch:hover:!selected {{
    background: #f8fafc;
}}
QListWidget::item, QTreeWidget::item, QTableWidget::item, QTreeView::item, QTableView::item {{
    padding: 5px 8px;
    border-radius: 4px;
}}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected, QTreeView::item:selected, QTableView::item:selected {{
    background: #e2e8f0;
    color: #0f172a;
    font-weight: 600;
}}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected, QTableWidget::item:hover:!selected, QTreeView::item:hover:!selected, QTableView::item:hover:!selected {{
    background: #f8fafc;
}}
QHeaderView::section {{
    background: #f8fafc;
    color: #475569;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 11px;
}}

/* ── Check Box / Radio ───────────────────────────────────────── */
QCheckBox, QRadioButton {{
    color: #334155;
    spacing: 7px;
    font-size: 12px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 15px; height: 15px;
    border: 1px solid #94a3b8;
    border-radius: 3px;
    background: #ffffff;
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: #0f172a;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: #0f172a;
    border: 1px solid #000000;
}}

/* ── Tooltip ─────────────────────────────────────────────────── */
QToolTip {{
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 11px;
    font-family: {FONT_FAMILY};
}}

/* ── Slider ──────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: #e2e8f0;
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #0f172a;
    width: 16px; height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}}
QSlider::handle:horizontal:hover {{ background: #334155; }}

/* ── Status Bar ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: #ffffff;
    color: #475569;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
    min-height: 26px;
}}
"""


# ═══════════════════════════════════════════════════════════════════
# 3. SLATE PRO DARK THEME (Professional Dark GIS Workstation)
# ═══════════════════════════════════════════════════════════════════
DARK_STYLESHEET = f"""
/* ═══════════════════════════════════════════════════════════════
   GeoStudio — Professional Slate Pro Dark Theme
   ═══════════════════════════════════════════════════════════════ */
QMainWindow, QDialog, QWidget {{
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: {FONT_FAMILY};
    font-size: 12px;
}}
QMenuBar {{
    background: #090e1a;
    color: #94a3b8;
    border-bottom: 1px solid #1e293b;
    padding: 3px 6px;
    font-size: 12px;
    font-weight: 500;
}}
QMenuBar::item {{
    padding: 5px 10px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background: #1e293b;
    color: #f8fafc;
}}
QMenu {{
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 0px;
}}
QMenu::item {{
    background-color: transparent;
    color: #e2e8f0;
    padding: 6px 36px 6px 32px;
    margin: 1px 4px;
    font-size: 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: #334155;
    color: #ffffff;
}}
QMenu::item:disabled {{
    color: #64748b;
}}
QMenu::separator {{
    height: 1px;
    background-color: #334155;
    margin: 4px 8px 4px 30px;
}}
QToolBar {{
    background: #090e1a;
    border-bottom: 1px solid #1e293b;
    border-right: 1px solid #1e293b;
    spacing: 3px;
    padding: 3px 4px;
}}
QToolBar::separator {{
    background: #334155;
    width: 1px;
    margin: 4px 6px;
}}
QToolButton {{
    background: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px 6px;
    margin: 1px 1px;
    font-size: 11px;
    font-weight: 500;
}}
QToolButton:hover {{
    background: #1e293b;
    color: #f8fafc;
    border: 1px solid #475569;
}}
QToolButton:pressed {{
    background: #334155;
    color: #ffffff;
}}
QToolButton:checked {{
    background: #334155;
    color: #ffffff;
    border: 1px solid #64748b;
    font-weight: 600;
}}
QDockWidget {{
    color: #f8fafc;
    font-weight: 600;
    font-size: 12px;
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: #1e293b;
    color: #e2e8f0;
    padding: 7px 12px;
    border-bottom: 1px solid #334155;
    border-top: 1px solid #334155;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.3px;
}}
QDockWidget::close-button:hover {{ background: #7f1d1d; color: #f87171; }}
QDockWidget::float-button:hover {{ background: #334155; color: #ffffff; }}
QSplitter::handle {{ background: #1e293b; }}
QSplitter::handle:hover {{ background: #475569; }}
QScrollBar:vertical {{ background: #0f172a; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #334155; min-height: 28px; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: #475569; }}
QScrollBar:horizontal {{ background: #0f172a; height: 8px; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background: #334155; min-width: 28px; border-radius: 4px; }}
QScrollBar::handle:horizontal:hover {{ background: #475569; }}
QTabWidget::pane {{ border: 1px solid #334155; background: #0f172a; border-radius: 6px; }}
QTabBar::tab {{ background: #090e1a; color: #64748b; border: 1px solid #334155; padding: 6px 14px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; }}
QTabBar::tab:selected {{ background: #334155; color: #ffffff; font-weight: 600; }}
QPushButton {{ background: #334155; color: #ffffff; border: none; border-radius: 5px; padding: 6px 14px; font-weight: 600; }}
QPushButton:hover {{ background: #475569; }}
QPushButton:pressed {{ background: #1e293b; }}
QPushButton:disabled {{ background: #1e293b; color: #64748b; }}
QLineEdit, QTextEdit, QPlainTextEdit {{ background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 5px; padding: 5px 8px; }}
QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid #64748b; }}
QComboBox {{ background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 5px; padding: 5px 8px; }}
QComboBox:focus {{ border: 1.5px solid #64748b; }}
QComboBox QAbstractItemView {{ background: #1e293b; color: #f8fafc; selection-background-color: #334155; border: 1px solid #334155; }}
QSpinBox, QDoubleSpinBox {{ background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 5px; padding: 5px 6px; }}
QGroupBox {{ border: 1px solid #334155; border-radius: 6px; margin-top: 14px; padding: 10px 8px 8px 8px; color: #f8fafc; font-weight: 600; background: #0f172a; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 6px; background: #0f172a; }}
QListWidget, QTreeWidget, QTableWidget {{ background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 6px; outline: none; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: #334155; color: #ffffff; font-weight: 600; }}
QHeaderView::section {{ background: #090e1a; color: #94a3b8; border: none; border-bottom: 1px solid #334155; border-right: 1px solid #334155; padding: 6px 10px; font-weight: 600; }}
QCheckBox, QRadioButton {{ color: #94a3b8; spacing: 7px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 15px; height: 15px; border: 1px solid #475569; border-radius: 3px; background: #1e293b; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ background: #475569; border: 1px solid #64748b; }}
QProgressBar {{ border: 1px solid #334155; border-radius: 4px; background: #1e293b; text-align: center; color: #e2e8f0; font-size: 11px; }}
QProgressBar::chunk {{ background: #475569; border-radius: 3px; }}
QStatusBar {{ background-color: #090e1a; color: #94a3b8; border-top: 1px solid #1e293b; min-height: 26px; }}
QToolTip {{ background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px 10px; font-size: 11px; font-family: {FONT_FAMILY}; }}
"""
