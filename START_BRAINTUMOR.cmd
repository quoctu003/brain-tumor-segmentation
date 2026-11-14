@echo off
setlocal
title BrainTumor AI - Local Research Workspace
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" scripts\launch.py %*
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        for %%V in (3.13 3.12) do (
            py -%%V -c "import sys" >nul 2>nul
            if not errorlevel 1 (
                py -%%V scripts\launch.py %*
                goto launchFinished
            )
        )
    )
    python scripts\launch.py %*
)
:launchFinished
set "launchExit=%errorlevel%"
if not "%launchExit%"=="0" (
    echo.
    echo Startup failed. Read the message above and docs\05-DEMO-VA-VAN-HANH.md.
    pause
)
exit /b %launchExit%
