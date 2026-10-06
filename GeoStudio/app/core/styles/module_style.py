# -*- coding: utf-8 -*-
"""
GeoStudio - Module / Dialog Stylesheet
"""

from .tokens import FONT_FAMILY, MONO_FONT

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
