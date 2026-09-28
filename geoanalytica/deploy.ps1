# GeoAnalytica Deploy Script
# Run this from PowerShell to install the plugin into QGIS

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$qgisPluginDir = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\geoanalytica"

Write-Host "GeoAnalytica Plugin Deploy Script" -ForegroundColor Cyan
Write-Host "Source: $source" -ForegroundColor Yellow
Write-Host "Target: $qgisPluginDir" -ForegroundColor Yellow
Write-Host ""

# Remove old installation
if (Test-Path $qgisPluginDir) {
    Write-Host "Removing old installation..." -ForegroundColor Red
    Remove-Item -Recurse -Force $qgisPluginDir
}

# Copy plugin files
Write-Host "Copying plugin files..." -ForegroundColor Green
Copy-Item -Recurse -Force $source $qgisPluginDir

# Copy SVG icon as PNG (QGIS prefers PNG for toolbar icons)
$svgIcon = "$qgisPluginDir\resources\icon.svg"
$pngIcon = "$qgisPluginDir\resources\icon.png"
if (Test-Path $svgIcon -and -not (Test-Path $pngIcon)) {
    Write-Host "Note: Convert resources/icon.svg to icon.png for best results." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✓ GeoAnalytica deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Open QGIS 3.40"
Write-Host "  2. Go to: Plugins > Manage and Install Plugins"
Write-Host "  3. Click 'Installed' tab and find 'GeoAnalytica'"
Write-Host "  4. Enable it with the checkbox"
Write-Host "  5. Click the GeoAnalytica icon in the toolbar!"
Write-Host ""
Write-Host "Or use QGIS Python Console to reload:" -ForegroundColor Cyan
Write-Host '  import importlib; import qgis.utils; qgis.utils.reloadPlugin("geoanalytica")'
