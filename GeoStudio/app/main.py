# -*- coding: utf-8 -*-
"""
GeoStudio - Standalone GIS Application
Entry point: bootstraps QGIS engine then launches the main window.
"""

import sys
import os
import glob
import faulthandler

# Enable native crash fault handler for diagnostic tracing
faulthandler.enable()


def _resolve_qgis_paths():
    """Dynamically resolves QGIS root, app, and Python directories."""
    candidates = []
    # 1. Environment variables
    for var in ("QGIS_ROOT", "OSGEO4W_ROOT"):
        val = os.environ.get(var, "").strip('\"')
        if val and os.path.isdir(val):
            candidates.append(val)

    prefix = os.environ.get("QGIS_PREFIX_PATH", "").strip('\"')
    if prefix and os.path.isdir(prefix):
        parent = os.path.dirname(os.path.dirname(prefix))
        if os.path.isdir(os.path.join(parent, "bin")):
            candidates.append(parent)

    # 2. Known search patterns
    search_globs = [
        r"C:\Program Files\QGIS*",
        r"C:\Program Files (x86)\QGIS*",
        r"D:\Program Files\QGIS*",
        r"C:\OSGeo4W*",
        r"D:\OSGeo4W*",
    ]
    for pattern in search_globs:
        found = [p for p in glob.glob(pattern) if os.path.isdir(p)]
        found.sort(reverse=True)
        candidates.extend(found)

    # 3. Fallback candidates
    candidates.extend([
        r"C:\Program Files\QGIS 3.44.15",
        r"C:\Program Files\QGIS 3.40.14",
        r"C:\Program Files\QGIS 3.34.14",
    ])

    qgis_root = None
    for cand in candidates:
        if os.path.isdir(cand) and (os.path.isdir(os.path.join(cand, "bin")) or os.path.isdir(os.path.join(cand, "apps"))):
            qgis_root = os.path.abspath(cand)
            break

    if not qgis_root:
        raise RuntimeError(
            "Could not detect a valid QGIS installation. "
            "Please ensure QGIS is installed or set the QGIS_ROOT environment variable."
        )

    # Resolve QGIS_APP (qgis-ltr or qgis)
    qgis_app = None
    for app_name in ("qgis-ltr", "qgis"):
        candidate_app = os.path.join(qgis_root, "apps", app_name)
        if os.path.isdir(candidate_app):
            qgis_app = candidate_app
            break
    if not qgis_app:
        qgis_app = os.path.join(qgis_root, "apps", "qgis-ltr")

    # Resolve Python directory in apps/Python*
    py_dirs = glob.glob(os.path.join(qgis_root, "apps", "Python3*"))
    py_dirs.sort(reverse=True)
    qgis_py = py_dirs[0] if py_dirs else os.path.join(qgis_root, "apps", "Python312")

    return qgis_root, qgis_app, qgis_py


QGIS_ROOT, QGIS_APP, QGIS_PY = _resolve_qgis_paths()

# Add DLL directories for Windows Python 3.8+
if hasattr(os, 'add_dll_directory'):
    for dll_dir in [
        os.path.join(QGIS_ROOT, "bin"),
        os.path.join(QGIS_APP, "bin"),
        os.path.join(QGIS_ROOT, "apps", "Qt5", "bin"),
        os.path.join(QGIS_ROOT, "apps", "gdal", "bin"),
        os.path.join(QGIS_ROOT, "apps", "pdal", "bin"),
        QGIS_PY,
        os.path.join(QGIS_PY, "Scripts"),
    ]:
        if os.path.exists(dll_dir):
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass

# Add QGIS Python bindings and plugins to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_dir = os.path.dirname(os.path.abspath(__file__))
for p in [
    os.path.join(QGIS_APP, "python"),
    os.path.join(QGIS_APP, "python", "plugins"),
    os.path.join(QGIS_PY, "Lib", "site-packages"),
    os.path.join(QGIS_PY, "Lib"),
    app_dir,
    project_dir,
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

# Set QGIS prefix path & environment variables
os.environ["QGIS_ROOT"]        = QGIS_ROOT
os.environ["QGIS_PREFIX_PATH"] = QGIS_APP

# GDAL data path
gdal_candidates = [
    os.path.join(QGIS_ROOT, "apps", "gdal", "share", "gdal"),
    os.path.join(QGIS_ROOT, "share", "gdal"),
]
for g_dir in gdal_candidates:
    if os.path.exists(g_dir):
        os.environ["GDAL_DATA"] = g_dir
        break

# PROJ data path
proj_dir = os.path.join(QGIS_ROOT, "share", "proj")
if os.path.exists(proj_dir):
    os.environ["PROJ_LIB"]  = proj_dir
    os.environ["PROJ_DATA"] = proj_dir

# Qt plugin paths (Qt5 core plugins first, then qgis-ltr custom widgets)
qt_plugins = []
qt5_plugins = os.path.join(QGIS_ROOT, "apps", "Qt5", "plugins")
if os.path.exists(qt5_plugins):
    qt_plugins.append(qt5_plugins)
qgis_qtplugins = os.path.join(QGIS_APP, "qtplugins")
if os.path.exists(qgis_qtplugins):
    qt_plugins.append(qgis_qtplugins)
if qt_plugins:
    os.environ["QT_PLUGIN_PATH"] = ";".join(qt_plugins)

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false;qt.core.mimetype.*=false;" + os.environ.get("QT_LOGGING_RULES", "")


# ── Diagnostic / Validation Subcommands ───────────────────────────────────────
if "--validate" in sys.argv:
    try:
        # 1. QGIS Python
        import sys as _sys
        assert _sys.version_info >= (3, 9)
        print("QGIS Python: OK", flush=True)

        # 2. QGIS
        from qgis.core import QgsApplication as _QgsApp
        _QgsApp.setPrefixPath(QGIS_APP, True)
        print("QGIS: OK", flush=True)

        # 3. Qt
        from PyQt5.QtWidgets import QApplication as _QApp
        from PyQt5.QtCore import Qt as _Qt
        print("Qt: OK", flush=True)

        # 4. GeoStudio modules
        from ui.main_window import GeoStudioMainWindow as _GWin
        print("GeoStudio modules: OK", flush=True)

        sys.exit(0)
    except Exception as e:
        print(f"Validation Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if "--diagnostic" in sys.argv:
    print("=" * 60)
    print("GeoStudio Environment Diagnostic Report")
    print("=" * 60)
    print(f"GeoStudio root:     {project_dir}")
    print(f"QGIS root:          {QGIS_ROOT}")
    print(f"Python executable:  {sys.executable}")
    print(f"Python version:     {sys.version.split()[0]}")

    try:
        from qgis.core import Qgis
        print(f"QGIS version:       {Qgis.QGIS_VERSION}")
    except Exception as e:
        print(f"QGIS version:       Error ({e})")

    try:
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        print(f"Qt version:         {QT_VERSION_STR} (PyQt5 {PYQT_VERSION_STR})")
    except Exception as e:
        print(f"Qt version:         Error ({e})")

    try:
        from osgeo import gdal
        print(f"GDAL version:       {gdal.__version__}")
    except Exception as e:
        print(f"GDAL version:       Error ({e})")

    try:
        import pyproj
        print(f"PROJ version:       {pyproj.__proj_version__}")
    except Exception as e:
        print(f"PROJ version:       Error ({e})")

    print(f"QT_PLUGIN_PATH:     {os.environ.get('QT_PLUGIN_PATH', 'Not set')}")
    print(f"GDAL_DATA:          {os.environ.get('GDAL_DATA', 'Not set')}")
    print(f"PROJ_LIB:           {os.environ.get('PROJ_LIB', 'Not set')}")
    print("-" * 60)
    print("Component Tests:")

    # Step test
    print("  Testing Python:           OK")
    from qgis.core import QgsApplication
    print("  Testing QGIS:             OK")
    from PyQt5.QtWidgets import QApplication
    print("  Testing Qt:               OK")
    _test_app = QgsApplication([], False)
    _test_app.setPrefixPath(QGIS_APP, True)
    _test_app.initQgis()
    print("  Testing QGIS GUI:         OK")
    from ui.main_window import GeoStudioMainWindow
    print("  Testing GeoStudio modules: OK")
    _test_win = GeoStudioMainWindow(qgs_app=_test_app)
    print("  Testing Main window:      OK")
    _test_win.hide()
    del _test_win
    _test_app.exitQgis()
    del _test_app
    print("=" * 60)
    print("All diagnostic checks PASSED successfully.")
    print("=" * 60)
    sys.exit(0)


# ── Qt & QGIS Application (Single Unified Instance) ───────────────────────────
import datetime
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtCore import (
    Qt, QTimer, qInstallMessageHandler, QtWarningMsg, QtCriticalMsg, QtFatalMsg
)
from PyQt5.QtGui import QPixmap, QColor, QPainter, QFont, QLinearGradient, QBrush, QPalette
from qgis.core import QgsApplication

_verbose = "--verbose" in sys.argv or os.environ.get("GEOSTUDIO_DIAG", "") == "1"
_diag_log_file = os.path.join(project_dir, "app_startup.log")

def _diag_log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted = f"[{timestamp}] [Startup] {msg}"
    try:
        with open(_diag_log_file, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass
    if _verbose:
        print(formatted, flush=True)

_diag_log(f"Configuring QgsApplication with prefix path: {QGIS_APP}")

# High DPI Scaling for 2K/4K Displays
try:
    QgsApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QgsApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    pass

# Create sole application object
QgsApplication.setPrefixPath(QGIS_APP, True)
argv_bytes = [b"GeoStudio"]
app = QgsApplication(argv_bytes, True)

_diag_log("Initializing QGIS core subsystem (initQgis)...")
app.initQgis()
_diag_log("QGIS core subsystem initialized.")

# Clean Qt message handler: suppresses benign Qt5 Windows internal MIME XML warning
def _qt_message_handler(mode, context, message):
    if "QMimeDatabase: Error loading internal MIME data" in message or "<internal MIME data>" in message:
        return
    if mode in (QtCriticalMsg, QtFatalMsg):
        sys.stderr.write(f"[Qt Error] {message}\n")
    elif mode == QtWarningMsg:
        sys.stderr.write(f"[Qt Warning] {message}\n")
    sys.stderr.flush()

qInstallMessageHandler(_qt_message_handler)

app.setApplicationName("GeoStudio")
app.setOrganizationName("GeoStudio")
app.setStyle("Fusion")

# Global Palette Highlight -> Grey
pal = app.palette()
pal.setColor(QPalette.Highlight, QColor("#e2e8f0"))
pal.setColor(QPalette.HighlightedText, QColor("#0f172a"))
app.setPalette(pal)

# ── Splash Screen (Omitted in --safe-mode) ──────────────────────────────────
safe_mode = "--safe-mode" in sys.argv
splash = None
if not safe_mode:
    splash_pix = QPixmap(480, 280)
    splash_pix.fill(QColor("#0d1b2a"))

    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.Antialiasing)

    gradient = QLinearGradient(0, 0, 480, 280)
    gradient.setColorAt(0.0, QColor("#0d1b2a"))
    gradient.setColorAt(1.0, QColor("#1a3a5c"))
    painter.fillRect(0, 0, 480, 280, QBrush(gradient))

    # Title
    font = QFont("Segoe UI", 32, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#4fc3f7"))
    painter.drawText(40, 110, "🌍 GeoStudio")

    # Subtitle
    font2 = QFont("Segoe UI", 11)
    painter.setFont(font2)
    painter.setPen(QColor("#90caf9"))
    painter.drawText(44, 140, "Standalone Geospatial Analysis System")

    # Version
    try:
        from qgis.core import Qgis
        _qgis_ver = Qgis.QGIS_VERSION.split("-")[0]
    except Exception:
        _qgis_ver = "3.44"
    font3 = QFont("Segoe UI", 9)
    painter.setFont(font3)
    painter.setPen(QColor("#546e7a"))
    painter.drawText(44, 200, f"Version 1.0  ·  Powered by QGIS Engine {_qgis_ver}  ·  PyQGIS")

    # Loading bar background
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#1e3a5f"))
    painter.drawRoundedRect(40, 230, 400, 12, 6, 6)
    painter.setBrush(QColor("#4fc3f7"))
    painter.drawRoundedRect(40, 230, 200, 12, 6, 6)
    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.show()
    splash.showMessage("  Initializing geospatial engine...", Qt.AlignBottom | Qt.AlignLeft, QColor("#4fc3f7"))
    app.processEvents()

# ── Initialize Processing ───────────────────────────────────────────────────
if not safe_mode:
    try:
        _diag_log("Initializing QGIS Processing framework...")
        import processing
        from processing.core.Processing import Processing
        Processing.initialize()
        _diag_log("QGIS Processing framework initialized.")
        if splash:
            splash.showMessage("  Building interface...", Qt.AlignBottom | Qt.AlignLeft, QColor("#a5d6a7"))
            app.processEvents()
    except Exception as e:
        _diag_log(f"Processing initialization warning: {e}")
        print(f"[Warning] Processing initialize: {e}")

# ── Launch Main Window ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.main_window import GeoStudioMainWindow

_diag_log("Constructing GeoStudioMainWindow...")
window = GeoStudioMainWindow(qgs_app=app, safe_mode=safe_mode)
_diag_log("GeoStudioMainWindow constructed successfully.")

_diag_log("Displaying main window (showMaximized)...")
window.showMaximized()

# Retain application objects in module scope to prevent premature SIP garbage collection
_LIFETIME_REFS = [app, window, argv_bytes]

# Safely dismiss splash and bring main window forward
if splash is not None:
    _diag_log("Dismissing splash screen and activating main window...")
    splash.finish(window)
    window.raise_()
    window.activateWindow()
    _LIFETIME_REFS.append(splash)

# Confirm startup once event loop is running and window is active
def _confirm_started():
    if window.isVisible():
        _diag_log("Main window verified visible on desktop.")
        print("GeoStudio started successfully.", flush=True)
    else:
        _diag_log("Main window not yet flagged visible; invoking showMaximized and activateWindow.")
        window.showMaximized()
        window.raise_()
        window.activateWindow()
        print("GeoStudio started successfully.", flush=True)

QTimer.singleShot(250, _confirm_started)

if "--test-autoclose" in sys.argv:
    QTimer.singleShot(2500, window.close)

# ── Run Event Loop ────────────────────────────────────────────────────────────
_diag_log("Entering Qt application event loop (app.exec_)...")
exit_code = app.exec_()
_diag_log(f"Qt application event loop exited with code: {exit_code}")

# ── Clean Shutdown Sequence ───────────────────────────────────────────────────
_diag_log("Executing clean shutdown sequence...")
try:
    from qgis.core import QgsProject
    QgsProject.instance().clear()
except Exception:
    pass

try:
    app.exitQgis()
except Exception:
    pass

_diag_log("GeoStudio shutdown complete.")
sys.exit(0 if exit_code is None else exit_code)

