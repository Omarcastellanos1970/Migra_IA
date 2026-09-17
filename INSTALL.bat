@echo off
setlocal
title MIGRA-IA v0.5.0 - Installation (once only)
cd /d "%~dp0"

echo ============================================================
echo   MIGRA-IA v0.5.0 - Installation
echo ============================================================
echo.
echo   This is done ONCE ONLY and takes a few minutes.
echo   It needs an internet connection.
echo.

REM ---------- 1. Find Python ----------
set "PYEXE="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYEXE=py -3"
if not defined PYEXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
    echo   [X] Python was not found on this computer.
    echo.
    echo       What to do:
    echo       1. Go to  https://www.python.org/downloads/
    echo       2. Download Python 3.10 or above.
    echo       3. When installing, TICK the box "Add Python to PATH".
    echo       4. When it finishes, double-click INSTALL.bat again
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYEXE% --version 2^>^&1') do set "PYVER=%%v"
echo   [OK] Python found: %PYVER%
echo.

REM ---------- 2. Create the environment ----------
if exist ".venv\Scripts\python.exe" (
    echo   [OK] The .venv environment already exists, it is reused.
) else (
    echo   [..] Creating the .venv virtual environment ...
    %PYEXE% -m venv .venv
    if errorlevel 1 goto :error_venv
    echo   [OK] Environment created.
)
echo.

REM ---------- 3. Install the dependencies ----------
echo   [..] Installing the dependencies ^(anthropic, flask^) ...
echo.
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error_pip
echo.

REM ---------- 4. Check ----------
echo   [..] Checking the installation ...
".venv\Scripts\python.exe" -c "import anthropic, flask, migra_ia; print('   [OK] MIGRA-IA version', migra_ia.__version__, 'ready to use')"
if errorlevel 1 goto :error_check

echo.
echo ============================================================
echo   INSTALLATION FINISHED
echo ============================================================
echo.
echo   Now double-click on:   Start_MIGRA-IA.bat
echo.
echo   The browser will open. Press "Interactive demo (no API key)"
echo   to try it free, with no API key and at no cost.
echo.
pause
exit /b 0

:error_venv
echo.
echo   [X] The virtual environment could not be created.
echo       Check that Python is properly installed and try again.
echo.
pause
exit /b 1

:error_pip
echo.
echo   [X] The installation of the dependencies failed.
echo       Most common cause: no internet connection, or an antivirus/proxy
echo       blocking pip. Check the connection and run this file again.
echo.
pause
exit /b 1

:error_check
echo.
echo   [X] The installation finished but the check failed.
echo       Send a screenshot of this window to Carlos.
echo.
pause
exit /b 1
