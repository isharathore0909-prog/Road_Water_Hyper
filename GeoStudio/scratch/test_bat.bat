@echo off
set "PYTHON_CMD=C:\Program Files\QGIS 3.44.15\bin\python-qgis-ltr.bat"
call "%PYTHON_CMD%" "M:\Geo Studio\GeoStudio\app\main.py" --test-autoclose
echo THE_ERRORLEVEL=%ERRORLEVEL%
