@echo off
title Visualizador Telepase - Actualizacion
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%Sistema_Python\python.exe"

echo ---------------------------------------------------
echo      ACTUALIZACION DEL VISUALIZADOR TELEPASE
echo ---------------------------------------------------
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR CRITICO: No se encuentra Python portable.
    echo Buscando en: "%PYTHON_EXE%"
    pause
    exit /b 1
)

if exist "%PROJECT_ROOT%\.git" (
    echo Actualizando repositorio...
    git -C "%PROJECT_ROOT%" pull --ff-only
    if errorlevel 1 (
        echo.
        echo ERROR: fallo la actualizacion del repositorio.
        pause
        exit /b 1
    )
) else (
    echo No se encontro .git. Se omite la actualizacion de codigo.
)

echo.
echo Instalando dependencias...
"%PYTHON_EXE%" -m pip install -r "%PROJECT_ROOT%requirements.txt"
if errorlevel 1 (
    echo.
    echo ERROR: no se pudieron instalar las dependencias.
    pause
    exit /b 1
)

echo.
echo Actualizacion finalizada correctamente.
pause
