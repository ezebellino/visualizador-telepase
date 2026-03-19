@echo off
title Visualizador Telepase - Inicio rapido
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "PYTHONW_EXE=%PROJECT_ROOT%Sistema_Python\pythonw.exe"
set "LAUNCHER_SCRIPT=%PROJECT_ROOT%scripts\launch_app_hidden.vbs"
set "STOP_SCRIPT=%PROJECT_ROOT%scripts\stop_visualizador_processes.ps1"

if not exist "%PYTHONW_EXE%" (
    echo ERROR CRITICO: No se encuentra pythonw.exe.
    echo Buscando en: "%PYTHONW_EXE%"
    echo.
    echo Sugerencia: verificar que la carpeta Sistema_Python este completa.
    pause
    exit /b 1
)

if not exist "%LAUNCHER_SCRIPT%" (
    echo ERROR CRITICO: No se encuentra el launcher oculto.
    echo Buscando en: "%LAUNCHER_SCRIPT%"
    pause
    exit /b 1
)

if exist "%STOP_SCRIPT%" (
    powershell.exe -ExecutionPolicy Bypass -File "%STOP_SCRIPT%" >nul 2>&1
)

start "" wscript.exe //nologo "%LAUNCHER_SCRIPT%"
exit /b 0
