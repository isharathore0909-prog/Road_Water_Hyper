@echo off
REM ============================================================
REM  GeoStudio - Standalone GIS Application Launcher
REM  Uses QGIS 3.40's bundled Python + PyQGIS as backend engine
REM ============================================================

SET QGIS_ROOT=C:\Program Files\QGIS 3.40.14
SET QGIS_APP=%QGIS_ROOT%\apps\qgis-ltr
SET QGIS_PYTHON=%QGIS_ROOT%\apps\Python312
SET PYTHON_QGIS=%QGIS_ROOT%\bin\python-qgis-ltr.bat

REM -- Additional Python plugin path for processing module --
SET PYTHONPATH=%QGIS_APP%\python;%QGIS_APP%\python\plugins;%APPDATA%\Python\Python312\site-packages;%QGIS_PYTHON%\Lib\site-packages;%QGIS_PYTHON%\Lib;%~dp0app;%PYTHONPATH%

REM -- Suppress Qt warnings --
SET QT_LOGGING_RULES=*.debug=false;qt.qpa.*=false

REM -- Launch GeoStudio --
echo Starting GeoStudio...
if exist "%PYTHON_QGIS%" (
    call "%PYTHON_QGIS%" "%~dp0app\main.py" %*
) else (
    "%QGIS_PYTHON%\python.exe" "%~dp0app\main.py" %*
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo GeoStudio exited with error code %ERRORLEVEL%
    pause
)

