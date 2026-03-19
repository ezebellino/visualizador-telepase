@echo off
title Visualizador Telepase - Modo operativo
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%Sistema_Python\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR CRITICO: No se encuentra Python portable.
    echo Buscando en: "%PYTHON_EXE%"
    exit /b 1
)

echo Iniciando Visualizador Telepase en modo operativo...
echo URL esperada: http://localhost:8501
"%PYTHON_EXE%" -m streamlit run "%PROJECT_ROOT%app.py" --server.headless=true --server.port=8501 --server.address=0.0.0.0
