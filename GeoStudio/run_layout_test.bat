@echo off
set "PROJECT_DIR=M:\Geo Studio\GeoStudio"
set "QGIS_DIR=C:\Program Files\QGIS 3.44.15"
set "PYTHON_EXE=%QGIS_DIR%\bin\python.exe"
set "O4W_ENV=%QGIS_DIR%\bin\o4w_env.bat"

call "%O4W_ENV%"
path %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%
set "QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-ltr"
set "QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\Qt5\plugins"
set "PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-ltr\python;%OSGEO4W_ROOT%\apps\qgis-ltr\python\plugins;%PROJECT_DIR%;%PROJECT_DIR%\app;%PYTHONPATH%"
set "QGIS_ROOT=%QGIS_DIR%"

"%PYTHON_EXE%" -u "%PROJECT_DIR%\test_layout_system.py"
exit /b %ERRORLEVEL%
