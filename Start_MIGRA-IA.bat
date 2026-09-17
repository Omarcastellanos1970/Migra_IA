@echo off
setlocal
title MIGRA-IA - Server (do not close this window while you use it)
cd /d "%~dp0"

REM This launcher opens the agent IN ENGLISH. The Spanish one is
REM Iniciar_MIGRA-IA.bat. setlocal keeps the variable inside this window.
set "MIGRA_IA_LANG=en"

echo ============================================================
echo   MIGRA-IA v0.3.0 - Starting the agent...
echo ============================================================
echo.

REM If the environment is not installed, warn instead of closing abruptly.
if not exist ".venv\Scripts\python.exe" (
    echo   [X] You have not installed the agent on this computer yet.
    echo.
    echo       Double-click first on:   INSTALL.bat
    echo       When it finishes, open this file again.
    echo.
    pause
    exit /b 1
)

echo   Your browser will open at http://127.0.0.1:5000
echo   There, press "Interactive demo (no API key)" to use it free.
echo.
echo   IMPORTANT: do NOT close this black window while you use
echo   the agent. To shut it down, close this window or press
echo   Ctrl+C.
echo.

REM Open the browser a few seconds later (give the server time to start)
start "" cmd /c "timeout /t 4 >nul & start "" http://127.0.0.1:5000"

REM Start the server with the Python of the virtual environment
".venv\Scripts\python.exe" -m webapp.app

echo.
echo The server stopped. You can close this window.
pause
