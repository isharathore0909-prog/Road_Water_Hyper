@echo off
setlocal

set "PROJECT_DIR=M:\Geo Studio\GeoStudio"
set "QGIS_DIR=C:\Program Files\QGIS 3.44.15"
set "PYTHON_EXE=%QGIS_DIR%\bin\python.exe"
set "MAIN_SCRIPT=%PROJECT_DIR%\app\main.py"
set "O4W_ENV=%QGIS_DIR%\bin\o4w_env.bat"

echo ============================================================
echo Starting GeoStudio...
echo ============================================================
echo [GeoStudio] Project directory: %PROJECT_DIR%
echo [GeoStudio] QGIS directory:    %QGIS_DIR%
echo [GeoStudio] Python executable: %PYTHON_EXE%
echo [GeoStudio] Main script:       %MAIN_SCRIPT%

if not exist "%PROJECT_DIR%" (
    echo.
    echo [ERROR] GeoStudio project directory not found:
    echo %PROJECT_DIR%
    pause
    exit /b 3
)
echo [OK] Project directory

if not exist "%QGIS_DIR%" (
    echo.
    echo [ERROR] QGIS installation not found:
    echo %QGIS_DIR%
    pause
    exit /b 3
)
echo [OK] QGIS installation

if not exist "%PYTHON_EXE%" (
    echo.
    echo [ERROR] QGIS Python not found:
    echo %PYTHON_EXE%
    pause
    exit /b 3
)
echo [OK] QGIS Python

if not exist "%MAIN_SCRIPT%" (
    echo.
    echo [ERROR] GeoStudio main.py not found:
    echo %MAIN_SCRIPT%
    pause
    exit /b 3
)
echo [OK] Main script

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo.
    echo [ERROR] Could not enter GeoStudio directory.
    pause
    exit /b 3
)
echo [GeoStudio] Current directory: %CD%

echo.
echo Initializing QGIS environment...
if not exist "%O4W_ENV%" (
    echo.
    echo [ERROR] QGIS environment script o4w_env.bat not found:
    echo %O4W_ENV%
    pause
    exit /b 3
)

call "%O4W_ENV%"
path %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%
set "QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-ltr"
set "GDAL_FILENAME_IS_UTF8=YES"
set "VSI_CACHE=TRUE"
set "VSI_CACHE_SIZE=1000000"
set "QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\Qt5\plugins"
set "PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-ltr\python;%OSGEO4W_ROOT%\apps\qgis-ltr\python\plugins;%PROJECT_DIR%;%PROJECT_DIR%\app;%PYTHONPATH%"
set "QGIS_ROOT=%QGIS_DIR%"
set "QT_LOGGING_RULES=*.debug=false;qt.qpa.*=false"

echo [OK] QGIS environment configured
echo.
echo Starting GeoStudio Python...
echo.

"%PYTHON_EXE%" "%MAIN_SCRIPT%" %*

set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo GeoStudio exited with error code %EXIT_CODE%

if not "%~1"=="--test" pause
exit /b %EXIT_CODE%
