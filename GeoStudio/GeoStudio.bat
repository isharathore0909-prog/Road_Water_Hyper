@echo off
setlocal

REM ============================================================
REM  GeoStudio - Standalone GIS Application Launcher
REM  Dynamically resolves QGIS runtime & project paths
REM ============================================================

REM 1. Determine GeoStudio project root directory dynamically
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo ============================================================
    echo GeoStudio Startup Error: Cannot access project directory
    echo ============================================================
    echo Missing directory: "%PROJECT_ROOT%"
    echo ============================================================
    pause
    exit /b 1
)

REM 2. Validate entry point script
if not exist "%PROJECT_ROOT%\app\main.py" (
    echo ============================================================
    echo GeoStudio Startup Error: Entry point script missing
    echo ============================================================
    echo Missing file: "%PROJECT_ROOT%\app\main.py"
    echo Project root: "%PROJECT_ROOT%"
    echo Current dir:  "%CD%"
    echo ============================================================
    pause
    exit /b 2
)

REM 3. Discover QGIS installation
set "QGIS_FOUND="

REM Check environment variable first if valid
if defined QGIS_ROOT (
    if exist "%QGIS_ROOT%\bin\python-qgis-ltr.bat" set "QGIS_FOUND=%QGIS_ROOT%"
    if not defined QGIS_FOUND if exist "%QGIS_ROOT%\bin\python.exe" set "QGIS_FOUND=%QGIS_ROOT%"
)

REM Search standard Program Files directories
if not defined QGIS_FOUND (
    for /d %%I in ("%ProgramFiles%\QGIS*" "C:\Program Files\QGIS*" "D:\Program Files\QGIS*") do (
        if exist "%%~I\bin\python-qgis-ltr.bat" set "QGIS_FOUND=%%~I"
        if not defined QGIS_FOUND if exist "%%~I\bin\python.exe" set "QGIS_FOUND=%%~I"
    )
)

REM Search 32-bit Program Files if applicable
if not defined QGIS_FOUND (
    for /d %%I in ("%ProgramFiles(x86)%\QGIS*" "C:\Program Files (x86)\QGIS*") do (
        if exist "%%~I\bin\python-qgis-ltr.bat" set "QGIS_FOUND=%%~I"
    )
)

REM Search OSGeo4W directories
if not defined QGIS_FOUND (
    for %%D in ("C:\OSGeo4W" "C:\OSGeo4W64" "D:\OSGeo4W" "D:\OSGeo4W64") do (
        if exist "%%~D\bin\python-qgis-ltr.bat" set "QGIS_FOUND=%%~D"
        if not defined QGIS_FOUND if exist "%%~D\bin\python.exe" set "QGIS_FOUND=%%~D"
    )
)

if not defined QGIS_FOUND (
    echo.
    echo ============================================================
    echo GeoStudio Startup Error: QGIS Runtime Not Found
    echo ============================================================
    echo GeoStudio requires QGIS with PyQGIS to operate.
    echo Searched locations:
    echo   - Environment: %%QGIS_ROOT%%
    echo   - %%ProgramFiles%%\QGIS*
    echo   - C:\Program Files\QGIS*
    echo   - C:\OSGeo4W / C:\OSGeo4W64
    echo.
    echo Please install QGIS or set the QGIS_ROOT environment variable.
    echo ============================================================
    echo.
    pause
    exit /b 3
)

set "QGIS_ROOT=%QGIS_FOUND%"

REM 4. Detect QGIS app folder (qgis-ltr or qgis)
if exist "%QGIS_ROOT%\apps\qgis-ltr" (
    set "QGIS_APP=%QGIS_ROOT%\apps\qgis-ltr"
) else if exist "%QGIS_ROOT%\apps\qgis" (
    set "QGIS_APP=%QGIS_ROOT%\apps\qgis"
) else (
    set "QGIS_APP=%QGIS_ROOT%"
)

REM 5. Detect Python runner
set "PYTHON_CMD="
if exist "%QGIS_ROOT%\bin\python-qgis-ltr.bat" (
    set "PYTHON_CMD=%QGIS_ROOT%\bin\python-qgis-ltr.bat"
) else if exist "%QGIS_ROOT%\bin\python-qgis.bat" (
    set "PYTHON_CMD=%QGIS_ROOT%\bin\python-qgis.bat"
) else if exist "%QGIS_ROOT%\bin\python.exe" (
    set "PYTHON_CMD=%QGIS_ROOT%\bin\python.exe"
) else (
    for /d %%P in ("%QGIS_ROOT%\apps\Python*") do (
        if exist "%%~P\python.exe" set "PYTHON_CMD=%%~P\python.exe"
    )
)

if not defined PYTHON_CMD (
    echo ============================================================
    echo GeoStudio Startup Error: Python Runtime Not Found
    echo ============================================================
    echo Missing Python executable in QGIS installation:
    echo %QGIS_ROOT%
    echo ============================================================
    echo.
    pause
    exit /b 4
)

REM 6. Configure environment variables
set "QGIS_PREFIX_PATH=%QGIS_APP%"
if exist "%QGIS_ROOT%\apps\gdal\share\gdal" (
    set "GDAL_DATA=%QGIS_ROOT%\apps\gdal\share\gdal"
) else if exist "%QGIS_ROOT%\share\gdal" (
    set "GDAL_DATA=%QGIS_ROOT%\share\gdal"
)
if exist "%QGIS_ROOT%\share\proj" set "PROJ_LIB=%QGIS_ROOT%\share\proj"

REM Qt plugin paths
set "QT_PLUGIN_PATH=%QGIS_APP%\qtplugins;%QGIS_ROOT%\apps\Qt5\plugins;%QT_PLUGIN_PATH%"

REM Additional Python search paths
set "PYTHONPATH=%QGIS_APP%\python;%QGIS_APP%\python\plugins;%PROJECT_ROOT%\app;%PROJECT_ROOT%;%PYTHONPATH%"

REM Suppress Qt internal warnings
set "QT_LOGGING_RULES=*.debug=false;qt.qpa.*=false;qt.core.mimetype.*=false;%QT_LOGGING_RULES%"

REM Check for diagnostic mode
if "%1"=="--diagnostic" (
    call "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py" --diagnostic
    exit /b %ERRORLEVEL%
)
if "%2"=="--diagnostic" (
    call "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py" --diagnostic
    exit /b %ERRORLEVEL%
)

REM 7. Launch GeoStudio
echo Starting GeoStudio...
echo.
echo Validating environment...
call "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py" --validate
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo GeoStudio failed to start during environment validation.
    echo Exit code: %ERRORLEVEL%
    echo ============================================================
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Starting application...
echo.

call "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py" %*
set "APP_EXIT_CODE=%ERRORLEVEL%"

if %APP_EXIT_CODE% NEQ 0 (
    echo.
    echo ============================================================
    echo GeoStudio failed to start.
    echo Exit code: %APP_EXIT_CODE%
    if "%APP_EXIT_CODE%"=="-1073741819" (
        echo Error code: 0xC0000005 - Access Violation
    )
    echo Startup command:
    echo "%PYTHON_CMD%" "%PROJECT_ROOT%\app\main.py"
    echo ============================================================
    pause
    exit /b %APP_EXIT_CODE%
)
exit /b 0
