@echo off
SET QGIS_ROOT=C:\Program Files\QGIS 3.44.15
SET PYTHON_QGIS=%QGIS_ROOT%\bin\python-qgis-ltr.bat

echo Testing GeoStudio imports...
if exist "%PYTHON_QGIS%" (
    call "%PYTHON_QGIS%" "%~dp0test_imports.py"
) else (
    "%QGIS_ROOT%\apps\Python312\python.exe" "%~dp0test_imports.py"
)
pause

