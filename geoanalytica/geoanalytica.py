# -*- coding: utf-8 -*-
"""
GeoAnalytica - Main Plugin Class
Handles plugin lifecycle: initGui, unload, and wiring all modules.
"""

import os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolBar, QDockWidget
from qgis.core import Qgis

from .core.utils import resource_path
from .ui.main_panel import GeoAnalyticaPanel


class GeoAnalytica:
    """QGIS Plugin Implementation - GeoAnalytica main class."""

    PLUGIN_NAME = "GeoAnalytica"
    MENU_TITLE = "&GeoAnalytica"

    def __init__(self, iface):
        """
        :param iface: QgisInterface - passed by QGIS on load.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = None
        self.toolbar = None
        self.main_panel = None
        self.dock_widget = None

        # Set up i18n
        locale = QSettings().value("locale/userLocale", "en")[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", f"geoanalytica_{locale}.qm")
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def tr(self, message):
        return QCoreApplication.translate(self.PLUGIN_NAME, message)

    def add_action(self, icon_path, text, callback, enabled=True,
                   add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path) if icon_path else QIcon()
        action = QAction(icon, text, parent or self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(enabled)
        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_toolbar and self.toolbar:
            self.toolbar.addAction(action)
        if add_to_menu and self.menu:
            self.menu.addAction(action)
        self.actions.append(action)
        return action

    def initGui(self):
        """Create menus, toolbar, and dock panel in QGIS GUI."""

        # --- Toolbar ---
        self.toolbar = self.iface.addToolBar(self.PLUGIN_NAME)
        self.toolbar.setObjectName("GeoAnalyticaToolBar")

        # --- Menu ---
        self.menu = QMenu(self.tr(self.MENU_TITLE), self.iface.mainWindow().menuBar())
        self.iface.mainWindow().menuBar().insertMenu(
            self.iface.firstRightStandardMenu().menuAction(), self.menu
        )

        # --- Main Panel Toggle Action ---
        panel_icon = resource_path("resources/icon.png")
        self.add_action(
            icon_path=panel_icon,
            text=self.tr("Open GeoAnalytica Panel"),
            callback=self.toggle_panel,
            status_tip=self.tr("Open the GeoAnalytica analysis panel"),
            add_to_toolbar=True,
            add_to_menu=True,
        )

        # --- Sub-menu actions ---
        self.menu.addSeparator()

        self.add_action(
            icon_path=resource_path("resources/layer_icon.png"),
            text=self.tr("Layer Manager"),
            callback=self.open_layer_manager,
            status_tip=self.tr("Manage and style layers"),
            add_to_toolbar=False,
            add_to_menu=True,
        )
        self.add_action(
            icon_path=resource_path("resources/analysis_icon.png"),
            text=self.tr("Spatial Analysis"),
            callback=self.open_spatial_analysis,
            status_tip=self.tr("Buffer, clip, intersect, dissolve and more"),
            add_to_toolbar=False,
            add_to_menu=True,
        )
        self.add_action(
            icon_path=resource_path("resources/raster_icon.png"),
            text=self.tr("Raster & DEM Processing"),
            callback=self.open_raster_processing,
            status_tip=self.tr("DEM, slope, aspect, hillshade, contours"),
            add_to_toolbar=False,
            add_to_menu=True,
        )
        self.add_action(
            icon_path=resource_path("resources/satellite_icon.png"),
            text=self.tr("Satellite & Hyperspectral"),
            callback=self.open_satellite_module,
            status_tip=self.tr("NDVI, band math, spectral profiles, hyperspectral analysis"),
            add_to_toolbar=False,
            add_to_menu=True,
        )
        self.add_action(
            icon_path=resource_path("resources/export_icon.png"),
            text=self.tr("Data Import / Export"),
            callback=self.open_import_export,
            status_tip=self.tr("Import/export CSV, GeoJSON, Shapefile, GeoPackage, KML"),
            add_to_toolbar=False,
            add_to_menu=True,
        )
        self.add_action(
            icon_path=resource_path("resources/tools_icon.png"),
            text=self.tr("Map Tools"),
            callback=self.open_map_tools,
            status_tip=self.tr("Measure, annotate, draw on map canvas"),
            add_to_toolbar=False,
            add_to_menu=True,
        )

        # --- Build main panel (dockable) ---
        self._create_dock_panel()

    def _create_dock_panel(self):
        """Create the main dockable GeoAnalytica panel."""
        self.main_panel = GeoAnalyticaPanel(self.iface, self)
        self.dock_widget = QDockWidget(self.tr("GeoAnalytica"), self.iface.mainWindow())
        self.dock_widget.setObjectName("GeoAnalyticaDock")
        self.dock_widget.setWidget(self.main_panel)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()  # Hidden by default

    def toggle_panel(self):
        """Show/hide the main GeoAnalytica dock panel."""
        if self.dock_widget:
            if self.dock_widget.isVisible():
                self.dock_widget.hide()
            else:
                self.dock_widget.show()
                self.dock_widget.raise_()

    def open_layer_manager(self):
        """Switch main panel to Layer Manager tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("layer_manager")

    def open_spatial_analysis(self):
        """Switch main panel to Spatial Analysis tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("spatial_analysis")

    def open_raster_processing(self):
        """Switch main panel to Raster Processing tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("raster_processing")

    def open_satellite_module(self):
        """Switch main panel to Satellite / Hyperspectral tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("satellite")

    def open_import_export(self):
        """Switch main panel to Import/Export tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("import_export")

    def open_map_tools(self):
        """Switch main panel to Map Tools tab."""
        if self.dock_widget:
            self.dock_widget.show()
            self.dock_widget.raise_()
            self.main_panel.switch_to_tab("map_tools")

    def unload(self):
        """Remove all GUI elements when plugin is disabled/unloaded."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(self.MENU_TITLE), action)
            self.iface.removeToolBarIcon(action)

        # Remove dock widget
        if self.dock_widget:
            self.iface.mainWindow().removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()
            self.dock_widget = None

        # Remove toolbar
        if self.toolbar:
            self.toolbar.deleteLater()
            self.toolbar = None

        # Remove menu
        if self.menu:
            self.menu.deleteLater()
            self.menu = None

        self.actions = []

    def show_message(self, message, level=Qgis.Info, duration=3):
        """Show a message in the QGIS message bar."""
        self.iface.messageBar().pushMessage(
            self.PLUGIN_NAME, message, level=level, duration=duration
        )
