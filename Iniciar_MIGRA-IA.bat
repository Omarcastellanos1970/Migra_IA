@echo off
title MIGRA-IA - Servidor (no cerrar esta ventana mientras lo usas)
cd /d "%~dp0"

echo ============================================================
echo   MIGRA-IA v0.3.0 - Iniciando el agente...
echo ============================================================
echo.

REM Si el entorno no esta instalado, avisar en vez de cerrarse de golpe.
if not exist ".venv\Scripts\python.exe" (
    echo   [X] Todavia no has instalado el agente en esta computadora.
    echo.
    echo       Haz doble clic primero en:   INSTALAR.bat
    echo       Cuando termine, vuelve a abrir este archivo.
    echo.
    pause
    exit /b 1
)

echo   Se abrira tu navegador en http://127.0.0.1:5000
echo   Ahi pulsa "Modo demo (sin clave)" para usarlo gratis.
echo.
echo   IMPORTANTE: NO cierres esta ventana negra mientras usas
echo   el agente. Para apagarlo, cierra esta ventana o pulsa
echo   Ctrl+C.
echo.

REM Abrir el navegador unos segundos despues (dar tiempo a que arranque el servidor)
start "" cmd /c "timeout /t 4 >nul & start "" http://127.0.0.1:5000"

REM Arrancar el servidor con el Python del entorno virtual
".venv\Scripts\python.exe" -m webapp.app

echo.
echo El servidor se detuvo. Puedes cerrar esta ventana.
pause
