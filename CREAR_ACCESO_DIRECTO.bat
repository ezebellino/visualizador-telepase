@echo off
title Visualizador Telepase - Crear acceso directo
cd /d "%~dp0"

set "SCRIPT_PATH=%~dp0scripts\create_shortcut.ps1"

if not exist "%SCRIPT_PATH%" (
    echo ERROR: No se encontro el script de acceso directo.
    pause
    exit /b 1
)

if not exist "%~dp0antena.ico" (
    echo ERROR: No se encontro el icono antena.ico.
    pause
    exit /b 1
)

echo Creando acceso directo de Visualizador Telepase en el escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo No se pudo crear el acceso directo.
    pause
    exit /b 1
)

echo.
echo Acceso directo creado correctamente.
pause
