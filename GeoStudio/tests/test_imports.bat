@echo off
SET QGIS_ROOT=C:\Program Files\QGIS 3.40.14
SET PYTHON_QGIS=%QGIS_ROOT%\bin\python-qgis-ltr.bat

echo Testing GeoStudio imports...
if exist "%PYTHON_QGIS%" (
    call "%PYTHON_QGIS%" "%~dp0test_imports.py"
) else (
    "C:\Program Files\QGIS 3.40.14\apps\Python312\python.exe" "%~dp0test_imports.py"
)
pause

