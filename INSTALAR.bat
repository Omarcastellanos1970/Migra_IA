@echo off
setlocal
title MIGRA-IA v0.3.0 - Instalacion (una sola vez)
cd /d "%~dp0"

echo ============================================================
echo   MIGRA-IA v0.3.0 - Instalacion
echo ============================================================
echo.
echo   Esto se hace UNA SOLA VEZ y tarda unos minutos.
echo   Necesita conexion a internet.
echo.

REM ---------- 1. Buscar Python ----------
set "PYEXE="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYEXE=py -3"
if not defined PYEXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
    echo   [X] No se encontro Python en esta computadora.
    echo.
    echo       Que hacer:
    echo       1. Entra a  https://www.python.org/downloads/
    echo       2. Descarga Python 3.10 o superior.
    echo       3. Al instalar, MARCA la casilla "Add Python to PATH".
    echo       4. Cuando termine, vuelve a hacer doble clic en INSTALAR.bat
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYEXE% --version 2^>^&1') do set "PYVER=%%v"
echo   [OK] Python encontrado: %PYVER%
echo.

REM ---------- 2. Crear el entorno ----------
if exist ".venv\Scripts\python.exe" (
    echo   [OK] El entorno .venv ya existe, se reutiliza.
) else (
    echo   [..] Creando el entorno virtual .venv ...
    %PYEXE% -m venv .venv
    if errorlevel 1 goto :error_venv
    echo   [OK] Entorno creado.
)
echo.

REM ---------- 3. Instalar dependencias ----------
echo   [..] Instalando dependencias ^(anthropic, flask^) ...
echo.
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error_pip
echo.

REM ---------- 4. Comprobacion ----------
echo   [..] Comprobando la instalacion ...
".venv\Scripts\python.exe" -c "import anthropic, flask, migra_ia; print('   [OK] MIGRA-IA version', migra_ia.__version__, 'lista para usarse')"
if errorlevel 1 goto :error_check

echo.
echo ============================================================
echo   INSTALACION TERMINADA
echo ============================================================
echo.
echo   Ahora haz doble clic en:   Iniciar_MIGRA-IA.bat
echo.
echo   Se abrira el navegador. Pulsa "Modo demo (sin clave)"
echo   para probarlo gratis, sin clave de API y sin costo.
echo.
pause
exit /b 0

:error_venv
echo.
echo   [X] No se pudo crear el entorno virtual.
echo       Revisa que Python este bien instalado y vuelve a intentarlo.
echo.
pause
exit /b 1

:error_pip
echo.
echo   [X] Fallo la instalacion de dependencias.
echo       Causa mas comun: sin conexion a internet o un antivirus/proxy
echo       bloqueando pip. Revisa la conexion y vuelve a ejecutar este archivo.
echo.
pause
exit /b 1

:error_check
echo.
echo   [X] La instalacion termino pero la comprobacion fallo.
echo       Envia una captura de esta ventana a Carlos.
echo.
pause
exit /b 1
