@echo off
REM Forward to start_geostudio.bat
call "%~dp0start_geostudio.bat" %*
exit /b %ERRORLEVEL%
