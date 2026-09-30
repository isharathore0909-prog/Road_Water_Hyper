# -*- coding: utf-8 -*-
"""
GeoStudio - Modern Vector Icon Provider
Generates crisp, high-detail GIS icons matching Global Mapper & QGIS visual design.
"""

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QByteArray, QSize, QRectF
from PyQt5.QtSvg import QSvgRenderer

_ICON_CACHE = {}

# ══════════════════════════════════════════════════════════════════════
# SVG ICON DEFINITIONS (Global Mapper & QGIS Inspired Desktop GIS Icons)
# ══════════════════════════════════════════════════════════════════════
_SVGS = {
    # ── Map Tools (Global Mapper Style) ────────────────────────
    "zoom": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="1" width="22" height="22" rx="3" fill="#fef08a" stroke="#f59e0b" stroke-width="1.5"/>
            <circle cx="11" cy="11" r="5.5" stroke="#0369a1" stroke-width="2" fill="#e0f2fe"/>
            <line x1="15" y1="15" x2="20" y2="20" stroke="#0369a1" stroke-width="2.5"/>
            <line x1="11" y1="8.5" x2="11" y2="13.5" stroke="#0284c7" stroke-width="1.8"/>
            <line x1="8.5" y1="11" x2="13.5" y2="11" stroke="#0284c7" stroke-width="1.8"/>
            <line x1="4" y1="4" x2="4" y2="8" stroke="#0284c7" stroke-width="1.5"/>
            <line x1="2" y1="6" x2="6" y2="6" stroke="#0284c7" stroke-width="1.5"/>
        </svg>
    """,
    "pan": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 11V6a1.5 1.5 0 0 0-3 0v4M15 10V4a1.5 1.5 0 0 0-3 0v6M12 10.5V5a1.5 1.5 0 0 0-3 0v8M18 8a1.5 1.5 0 1 1 3 0v6a7 7 0 0 1-7 7h-1.5c-2.5 0-4-.8-5.5-2.2l-3-3a1.5 1.5 0 0 1 2.1-2.1L8 14.5" fill="#fef08a" stroke="#b45309" stroke-width="1.6"/>
        </svg>
    """,
    "measure": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 7 7 20l-4-4L16 3l4 4z" fill="#fed7aa" stroke="#c2410c" stroke-width="1.6"/>
            <line x1="8.5" y1="9.5" x2="10.5" y2="11.5" stroke="#c2410c" stroke-width="1.4"/>
            <line x1="12" y1="6" x2="14" y2="8" stroke="#c2410c" stroke-width="1.4"/>
            <line x1="5.5" y1="12.5" x2="7.5" y2="14.5" stroke="#c2410c" stroke-width="1.4"/>
            <circle cx="20.5" cy="5.5" r="2" fill="#0284c7" stroke="#0c4a6e" stroke-width="1"/>
            <circle cx="4.5" cy="20.5" r="2" fill="#0284c7" stroke="#0c4a6e" stroke-width="1"/>
            <line x1="20" y1="6" x2="5" y2="20" stroke="#0284c7" stroke-width="1.4" stroke-dasharray="2 2"/>
        </svg>
    """,
    "identify": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
            <line x1="12" y1="16.5" x2="12" y2="11.5" stroke="#0369a1" stroke-width="2.2"/>
            <circle cx="12" cy="8" r="1.3" fill="#0369a1"/>
        </svg>
    """,
    "profile": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <line x1="2" y1="7" x2="22" y2="7" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="2 2"/>
            <line x1="2" y1="13" x2="22" y2="13" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="2 2"/>
            <line x1="2" y1="21" x2="22" y2="21" stroke="#334155" stroke-width="1.8"/>
            <path d="M2 21 8 8l5 6 5-11 4 18H2z" fill="#dcfce7" stroke="#15803d" stroke-width="1.8"/>
        </svg>
    """,
    "viewshed": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="3 14 12 8 21 14 12 12" fill="#f97316" stroke="#c2410c" stroke-width="1.4"/>
            <path d="M2 21 7 13l5 4 6-9 4 13H2z" fill="#dcfce7" stroke="#15803d" stroke-width="1.6"/>
            <line x1="12" y1="3" x2="12" y2="8" stroke="#dc2626" stroke-width="2"/>
        </svg>
    """,
    "digitizer": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.5 2.5 0 1 1 3.5 3.5L7.5 19.5 2 21l1.5-5.5L17 3z" fill="#fed7aa" stroke="#c2410c" stroke-width="1.6"/>
            <polygon points="2 21 4 15.5 8.5 20" fill="#334155"/>
            <line x1="14.5" y1="5.5" x2="18.5" y2="9.5" stroke="#c2410c" stroke-width="1.5"/>
        </svg>
    """,
    "control_center": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="1" width="22" height="22" rx="3" fill="#fef08a" stroke="#f59e0b" stroke-width="1.5"/>
            <rect x="5" y="4" width="14" height="4" rx="1" fill="#f97316" stroke="#c2410c" stroke-width="1.2"/>
            <rect x="5" y="10" width="14" height="4" rx="1" fill="#0284c7" stroke="#0369a1" stroke-width="1.2"/>
            <rect x="5" y="16" width="14" height="4" rx="1" fill="#16a34a" stroke="#15803d" stroke-width="1.2"/>
            <line x1="3" y1="6" x2="5" y2="6" stroke="#475569" stroke-width="1.2"/>
            <line x1="3" y1="12" x2="5" y2="12" stroke="#475569" stroke-width="1.2"/>
            <line x1="3" y1="18" x2="5" y2="18" stroke="#475569" stroke-width="1.2"/>
        </svg>
    """,
    "configure": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="#e0f2fe" stroke="#0369a1" stroke-width="1.8"/>
        </svg>
    """,
    "map_layout": """
        <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#ffffff" stroke="#0284c7" stroke-width="1.8"/>
            <rect x="6" y="6" width="7" height="7" fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>
            <line x1="15" y1="7" x2="19" y2="7" stroke="#64748b" stroke-width="1.4"/>
            <line x1="15" y1="10" x2="19" y2="10" stroke="#64748b" stroke-width="1.4"/>
            <line x1="6" y1="16" x2="19" y2="16" stroke="#64748b" stroke-width="1.4"/>
        </svg>
    """,

    # ── Project / File ─────────────────────────────────────────
    "new_project": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="#eff6ff"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12" stroke="#16a34a"/>
            <line x1="9" y1="15" x2="15" y2="15" stroke="#16a34a"/>
        </svg>
    """,
    "open_project": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" fill="#fef3c7"/>
            <polygon points="12 11 12 17 16 14" fill="#d97706"/>
        </svg>
    """,
    "save_project": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" fill="#eff6ff"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
        </svg>
    """,
    "save_project_as": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" fill="#eff6ff"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <circle cx="18" cy="18" r="3.5" fill="#16a34a" stroke="#ffffff" stroke-width="1.2"/>
            <line x1="18" y1="16" x2="18" y2="20" stroke="#ffffff"/>
            <line x1="16" y1="18" x2="20" y2="18" stroke="#ffffff"/>
        </svg>
    """,
    "print_map": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 6 2 18 2 18 9"/>
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" fill="#f8fafc"/>
            <rect x="6" y="14" width="12" height="8" fill="#ffffff"/>
        </svg>
    """,

    # ── Navigation ─────────────────────────────────────────────
    "zoom_in": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7.5" fill="#e0f2fe"/>
            <line x1="21" y1="21" x2="16.5" y2="16.5" stroke-width="2.5"/>
            <line x1="11" y1="8" x2="11" y2="14" stroke="#16a34a" stroke-width="2"/>
            <line x1="8" y1="11" x2="14" y2="11" stroke="#16a34a" stroke-width="2"/>
        </svg>
    """,
    "zoom_out": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7.5" fill="#e0f2fe"/>
            <line x1="21" y1="21" x2="16.5" y2="16.5" stroke-width="2.5"/>
            <line x1="8" y1="11" x2="14" y2="11" stroke="#dc2626" stroke-width="2"/>
        </svg>
    """,
    "zoom_full": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#dcfce7"/>
            <line x1="2.5" y1="12" x2="21.5" y2="12"/>
            <path d="M12 2.5a15 15 0 0 1 4 9.5 15 15 0 0 1-4 9.5 15 15 0 0 1-4-9.5 15 15 0 0 1 4-9.5z"/>
        </svg>
    """,
    "zoom_last": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 14 4 9l5-5"/>
            <path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v1a5.5 5.5 0 0 1-5.5 5.5H11"/>
        </svg>
    """,
    "zoom_next": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 14 5-5-5-5"/>
            <path d="M20 9H9.5A5.5 5.5 0 0 0 4 14.5v1A5.5 5.5 0 0 0 9.5 21H13"/>
        </svg>
    """,
    "refresh": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3L21.5 8M22 12.5a10 10 0 0 1-18.8 4.2L2.5 16"/>
        </svg>
    """,

    # ── Data Sources ───────────────────────────────────────────
    "add_vector": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2" fill="#dcfce7"/>
            <polyline points="2 17 12 22 22 17"/>
            <polyline points="2 12 12 17 22 12"/>
            <circle cx="19" cy="19" r="4.5" fill="#16a34a"/>
            <line x1="19" y1="16.5" x2="19" y2="21.5" stroke="#ffffff" stroke-width="1.8"/>
            <line x1="16.5" y1="19" x2="21.5" y2="19" stroke="#ffffff" stroke-width="1.8"/>
        </svg>
    """,
    "add_raster": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#ffedd5"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="3" y1="15" x2="21" y2="15"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
            <line x1="15" y1="3" x2="15" y2="21"/>
            <circle cx="19" cy="19" r="4.5" fill="#ea580c"/>
            <line x1="19" y1="16.5" x2="19" y2="21.5" stroke="#ffffff" stroke-width="1.8"/>
            <line x1="16.5" y1="19" x2="21.5" y2="19" stroke="#ffffff" stroke-width="1.8"/>
        </svg>
    """,
    "add_csv": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="#ecfeff"/>
            <polyline points="14 2 14 8 20 8"/>
            <circle cx="8" cy="13" r="1.5" fill="#0891b2"/>
            <circle cx="14" cy="13" r="1.5" fill="#0891b2"/>
            <circle cx="10" cy="17" r="1.5" fill="#0891b2"/>
        </svg>
    """,
    "add_wms": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#e0f2fe"/>
            <line x1="2.5" y1="12" x2="21.5" y2="12"/>
            <path d="M12 2.5a15 15 0 0 1 4 9.5 15 15 0 0 1-4 9.5 15 15 0 0 1-4-9.5 15 15 0 0 1 4-9.5z"/>
        </svg>
    """,
    "add_xyz": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" fill="#eef2ff"/>
            <line x1="8" y1="2" x2="8" y2="18"/>
            <line x1="16" y1="6" x2="16" y2="22"/>
        </svg>
    """,
    "browser_panel": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#f8fafc"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
        </svg>
    """,

    # ── Identify / Selection ───────────────────────────────────
    "select": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 3 7 18 3-7 7-3L3 3z" fill="#dbeafe"/>
        </svg>
    """,
    "select_rect": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-dasharray="3 3">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#eff6ff"/>
        </svg>
    """,
    "select_poly": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-dasharray="3 3">
            <polygon points="12 2 22 8.5 18 20 6 20 2 8.5" fill="#eff6ff"/>
        </svg>
    """,
    "select_radius": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-dasharray="3 3">
            <circle cx="12" cy="12" r="9" fill="#eff6ff"/>
            <line x1="12" y1="12" x2="21" y2="12" stroke-dasharray="none" stroke="#2563eb"/>
        </svg>
    """,
    "clear_selection": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#fef2f2"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
        </svg>
    """,

    # ── Measurement ────────────────────────────────────────────
    "measure_dist": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.3 8.7 8.7 21.3a1 1 0 0 1-1.4 0L2.7 16.7a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4z" fill="#fef3c7"/>
            <line x1="7.5" y1="10.5" x2="9" y2="12"/>
            <line x1="10.5" y1="7.5" x2="12" y2="9"/>
            <line x1="13.5" y1="4.5" x2="15" y2="6"/>
        </svg>
    """,
    "measure_area": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="3 6 14 2 21 10 17 21 6 18" fill="#fef3c7"/>
            <circle cx="3" cy="6" r="2" fill="#d97706"/>
            <circle cx="14" cy="2" r="2" fill="#d97706"/>
            <circle cx="21" cy="10" r="2" fill="#d97706"/>
            <circle cx="17" cy="21" r="2" fill="#d97706"/>
            <circle cx="6" cy="18" r="2" fill="#d97706"/>
        </svg>
    """,
    "measure_angle": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="21 20 4 20 16 4"/>
            <path d="M12 20a8 8 0 0 0-4-7" stroke-dasharray="2 2"/>
        </svg>
    """,
    "coord_capture": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#fef3c7"/>
            <line x1="22" y1="12" x2="18" y2="12"/>
            <line x1="6" y1="12" x2="2" y2="12"/>
            <line x1="12" y1="6" x2="12" y2="2"/>
            <line x1="12" y1="22" x2="12" y2="18"/>
            <circle cx="12" cy="12" r="2" fill="#d97706"/>
        </svg>
    """,

    # ── Terrain & Elevation ────────────────────────────────────
    "shader": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="18" rx="2" fill="#ede9fe"/>
            <path d="M2 15l5-5 5 5 5-5 5 5" stroke="#8b5cf6" stroke-width="2.5"/>
            <circle cx="18" cy="8" r="2" fill="#f59e0b"/>
        </svg>
    """,
    "elevation": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 20h20"/>
            <path d="m5 20 6-12 4 6 4-9 3 15" fill="#d1fae5"/>
        </svg>
    """,
    "slope": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="3 20 21 20 21 4 3 20" fill="#ffedd5"/>
            <line x1="7" y1="16" x2="17" y2="8" stroke="#ea580c" stroke-width="2.5"/>
        </svg>
    """,
    "aspect": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#f8fafc"/>
            <polygon points="12 4 15 12 12 10 9 12 12 4" fill="#dc2626" stroke="#dc2626"/>
            <polygon points="12 20 15 12 12 14 9 12 12 20" fill="#64748b" stroke="#64748b"/>
        </svg>
    """,
    "hillshade": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="3" fill="#fef08a"/>
            <path d="m2 20 8-10 6 7 3-4 3 7H2z" fill="#475569" stroke="#334155"/>
        </svg>
    """,
    "view_3d": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2" fill="#e0e7ff"/>
            <polyline points="2 17 12 22 22 17"/>
            <polyline points="2 12 12 17 22 12"/>
        </svg>
    """,
    "cut_fill": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 14h18"/>
            <path d="m4 14 4-6 6 6" fill="#fecaca"/>
            <path d="m14 14 3 5 4-5" fill="#bbf7d0"/>
        </svg>
    """,
    "watershed": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a5 5 0 0 0-5 5c0 4 5 11 5 11s5-7 5-11a5 5 0 0 0-5-5Z" fill="#bae6fd"/>
            <path d="M2 19c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2"/>
        </svg>
    """,

    # ── LiDAR / Point Cloud ────────────────────────────────────
    "load_las": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" fill="#f3e8ff"/>
            <circle cx="8" cy="15" r="1" fill="#9333ea"/>
            <circle cx="12" cy="13" r="1" fill="#9333ea"/>
            <circle cx="15" cy="16" r="1" fill="#9333ea"/>
            <circle cx="11" cy="17" r="1" fill="#9333ea"/>
        </svg>
    """,
    "classify_ground": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 18h20" stroke-width="3"/>
            <circle cx="5" cy="14" r="1.5" fill="#16a34a"/>
            <circle cx="10" cy="14" r="1.5" fill="#16a34a"/>
            <circle cx="15" cy="14" r="1.5" fill="#16a34a"/>
            <circle cx="19" cy="14" r="1.5" fill="#16a34a"/>
        </svg>
    """,
    "classify_buildings": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" fill="#fee2e2"/>
            <line x1="8" y1="8" x2="8" y2="10"/>
            <line x1="16" y1="8" x2="16" y2="10"/>
            <line x1="8" y1="14" x2="8" y2="16"/>
            <line x1="16" y1="14" x2="16" y2="16"/>
        </svg>
    """,
    "classify_veg": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a7 7 0 0 0-7 7c0 3 2 5 4 6.5V20h6v-4.5c2-1.5 4-3.5 4-6.5a7 7 0 0 0-7-7Z" fill="#d1fae5"/>
            <line x1="12" y1="11" x2="12" y2="20"/>
        </svg>
    """,
    "thin": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="1.5" fill="#64748b"/>
            <circle cx="18" cy="6" r="1.5" fill="#64748b"/>
            <circle cx="12" cy="12" r="1.5" fill="#64748b"/>
            <circle cx="6" cy="18" r="1.5" fill="#64748b"/>
            <circle cx="18" cy="18" r="1.5" fill="#64748b"/>
            <line x1="3" y1="21" x2="21" y2="3" stroke="#dc2626" stroke-width="1.8"/>
        </svg>
    """,
    "clip": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="3"/>
            <circle cx="6" cy="18" r="3"/>
            <line x1="20" y1="4" x2="8.12" y2="15.88"/>
            <line x1="14.47" y1="14.48" x2="20" y2="20"/>
            <line x1="8.12" y1="8.12" x2="12" y2="12"/>
        </svg>
    """,
    "color_by": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="13.5" cy="6.5" r="2.5" fill="#ef4444"/>
            <circle cx="17.5" cy="10.5" r="2.5" fill="#10b981"/>
            <circle cx="8.5" cy="7.5" r="2.5" fill="#3b82f6"/>
            <circle cx="6.5" cy="12.5" r="2.5" fill="#f59e0b"/>
            <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.6-.7 1.6-1.6 0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1 0-.9.7-1.6 1.6-1.6H16c3.3 0 6-2.7 6-6 0-5.5-4.5-9.6-10-9.6Z"/>
        </svg>
    """,

    # ── Digitizing ─────────────────────────────────────────────
    "toggle_edit": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" fill="#ffedd5"/>
        </svg>
    """,
    "add_point": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4" fill="#e11d48"/>
            <line x1="12" y1="2" x2="12" y2="6"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="2" y1="12" x2="6" y2="12"/>
            <line x1="18" y1="12" x2="22" y2="12"/>
        </svg>
    """,
    "add_line": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="4" cy="19" r="2.5" fill="#2563eb"/>
            <circle cx="11" cy="6" r="2.5" fill="#2563eb"/>
            <circle cx="20" cy="14" r="2.5" fill="#2563eb"/>
            <line x1="6" y1="17.5" x2="9.5" y2="8"/>
            <line x1="13" y1="7.5" x2="18" y2="12.5"/>
        </svg>
    """,
    "add_poly": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 3 21 9 18 20 6 20 3 9" fill="#dcfce7"/>
            <circle cx="12" cy="3" r="2" fill="#16a34a"/>
            <circle cx="21" cy="9" r="2" fill="#16a34a"/>
            <circle cx="18" cy="20" r="2" fill="#16a34a"/>
            <circle cx="6" cy="20" r="2" fill="#16a34a"/>
            <circle cx="3" cy="9" r="2" fill="#16a34a"/>
        </svg>
    """,
    "vertex_tool": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 20 10 4l6 10 4-4"/>
            <rect x="2" y="18" width="4" height="4" fill="#2563eb"/>
            <rect x="8" y="2" width="4" height="4" fill="#2563eb"/>
            <rect x="14" y="12" width="4" height="4" fill="#2563eb"/>
            <rect x="18" y="8" width="4" height="4" fill="#2563eb"/>
        </svg>
    """,
    "split": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" fill="#f8fafc"/>
            <line x1="3" y1="3" x2="21" y2="21" stroke="#dc2626" stroke-width="2.5" stroke-dasharray="2 2"/>
        </svg>
    """,
    "merge": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="5" width="10" height="14" rx="1" fill="#dcfce7"/>
            <rect x="12" y="5" width="10" height="14" rx="1" fill="#dcfce7"/>
            <line x1="8" y1="12" x2="16" y2="12" stroke="#16a34a" stroke-width="2"/>
        </svg>
    """,
    "delete": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
    """,
    "move": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="5 9 2 12 5 15"/>
            <polyline points="9 5 12 2 15 5"/>
            <polyline points="15 19 12 22 9 19"/>
            <polyline points="19 9 22 12 19 15"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <line x1="12" y1="2" x2="12" y2="22"/>
        </svg>
    """,
    "rotate": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.85.99 6.57 2.57L21 8"/>
            <polyline points="21 3 21 8 16 8"/>
        </svg>
    """,
    "snapping": """
        <svg viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 15-4-4 6.75-6.77a7.79 7.79 0 0 1 11 11L13 22l-4-4 6.36-6.36a2.14 2.14 0 0 0-3-3L6 15Z" fill="#fee2e2"/>
        </svg>
    """
}


def get_icon(name: str, size: int = 24) -> QIcon:
    """Returns a high-resolution, anti-aliased QIcon with clean margin and background clarity."""
    cache_key = f"{name}_{size}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    svg_data = _SVGS.get(name)
    if not svg_data:
        return QIcon()

    renderer = QSvgRenderer(QByteArray(svg_data.strip().encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    padding = 1.5
    target_rect = QRectF(padding, padding, float(size) - (padding * 2.0), float(size) - (padding * 2.0))
    renderer.render(painter, target_rect)
    painter.end()

    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon
