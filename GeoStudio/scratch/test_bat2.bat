@echo off
set "PROJECT_ROOT=M:\Geo Studio\GeoStudio"
set "QGIS_ROOT=C:\Program Files\QGIS 3.44.15"
set "QGIS_APP=C:\Program Files\QGIS 3.44.15\apps\qgis-ltr"
set "PYTHON_CMD=C:\Program Files\QGIS 3.44.15\bin\python-qgis-ltr.bat"
set "QGIS_PREFIX_PATH=%QGIS_APP%"
set "QT_PLUGIN_PATH=%QGIS_APP%\qtplugins;%QGIS_ROOT%\apps\Qt5\plugins;%QT_PLUGIN_PATH%"
set "PYTHONPATH=%QGIS_APP%\python;%QGIS_APP%\python\plugins;%PROJECT_ROOT%\app;%PROJECT_ROOT%;%PYTHONPATH%"
set "QT_LOGGING_RULES=*.debug=false;qt.qpa.*=false;qt.core.mimetype.*=false;%QT_LOGGING_RULES%"

echo [TEST] Calling main.py with GeoStudio.bat env...
call "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py" --test-autoclose
echo [TEST] RET_ERRORLEVEL=%ERRORLEVEL%
