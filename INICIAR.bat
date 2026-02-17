@echo off
title Visualizador Telepase - Iniciando...
echo ---------------------------------------------------
echo      INICIANDO SISTEMA DE GESTION DE TELEPASE
echo ---------------------------------------------------
echo.

:: 1. Definimos donde estamos parados (La carpeta raiz)
set "PROJECT_ROOT=%~dp0"

:: 2. Apuntamos al ejecutable de Python dentro de su nueva carpeta
set "PYTHON_EXE=%PROJECT_ROOT%Sistema_Python\python.exe"

:: 3. Verificamos que Python exista
if not exist "%PYTHON_EXE%" (
    echo ERROR CRITICO: No se encuentra Python.
    echo Buscando en: "%PYTHON_EXE%"
    echo.
    echo Asegurate de que la carpeta 'Sistema_Python' existe y tiene 'python.exe'.
    pause
    exit
)

echo Iniciando servidor...
echo Se abrira tu navegador en unos segundos...
echo.

:: 4. Ejecutamos la App
:: Quitamos 'headless=true' y ponemos 'headless=false' para obligar a abrir ventana
"%PYTHON_EXE%" -m streamlit run "%PROJECT_ROOT%app.py" --global.developmentMode=false --server.headless=false

pause