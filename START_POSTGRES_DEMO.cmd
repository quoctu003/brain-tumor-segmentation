@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-postgres.ps1
set "launchExit=%errorlevel%"
if not "%launchExit%"=="0" pause
exit /b %launchExit%
