@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM  Test GeoStudio Imports
REM ============================================================
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

REM Find QGIS
set "QGIS_FOUND="
if defined QGIS_ROOT (
    if exist "%QGIS_ROOT%\bin\python-qgis-ltr.bat" set "QGIS_FOUND=%QGIS_ROOT%"
)
if not defined QGIS_FOUND (
    for /f "delims=" %%I in ('dir /b /ad /o-n "C:\Program Files\QGIS*" 2^>nul') do (
        if not defined QGIS_FOUND (
            if exist "C:\Program Files\%%I\bin\python-qgis-ltr.bat" set "QGIS_FOUND=C:\Program Files\%%I"
        )
    )
)
if not defined QGIS_FOUND (
    set "QGIS_FOUND=C:\Program Files\QGIS 3.44.15"
)
set "QGIS_ROOT=%QGIS_FOUND%"
set "PYTHON_QGIS=%QGIS_ROOT%\bin\python-qgis-ltr.bat"

echo Testing GeoStudio imports...
if exist "%PYTHON_QGIS%" (
    call "%PYTHON_QGIS%" "%PROJECT_ROOT%\test_imports.py"
) else (
    echo [ERROR] Python QGIS runner not found at: "%PYTHON_QGIS%"
)
pause
