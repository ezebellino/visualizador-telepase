@echo off
title Visualizador Telepase - Verificacion
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%Sistema_Python\python.exe"
set "PYTHONW_EXE=%PROJECT_ROOT%Sistema_Python\pythonw.exe"
set "APP_FILE=%PROJECT_ROOT%app.py"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"
set "HEALTH_SCRIPT=%PROJECT_ROOT%scripts\check_app_health.ps1"

echo ---------------------------------------------------
echo      VERIFICACION DEL VISUALIZADOR TELEPASE
echo ---------------------------------------------------
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR: no se encontro python.exe en Sistema_Python.
    pause
    exit /b 1
)

if not exist "%PYTHONW_EXE%" (
    echo ERROR: no se encontro pythonw.exe en Sistema_Python.
    pause
    exit /b 1
)

if not exist "%APP_FILE%" (
    echo ERROR: no se encontro app.py en la carpeta del proyecto.
    pause
    exit /b 1
)

if not exist "%REQUIREMENTS_FILE%" (
    echo ERROR: no se encontro requirements.txt.
    pause
    exit /b 1
)

if not exist "%HEALTH_SCRIPT%" (
    echo ERROR: no se encontro el script de healthcheck local.
    pause
    exit /b 1
)

echo Verificando dependencias base...
"%PYTHON_EXE%" -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit no esta disponible en el entorno portable.
    echo Sugerencia: ejecutar ACTUALIZAR_SISTEMA.bat para reinstalar dependencias.
    pause
    exit /b 1
)

echo Verificando respuesta local de la app...
powershell -NoProfile -ExecutionPolicy Bypass -File "%HEALTH_SCRIPT%"
if errorlevel 1 (
    echo.
    echo La app no responde actualmente en http://127.0.0.1:8501
    echo Si todavia no la iniciaste, esto puede ser normal.
    echo Si deberia estar corriendo, prueba este orden:
    echo 1. Cerrar instancias previas del navegador y la app.
    echo 2. Ejecutar INICIAR.bat o run_telepase.bat.
    echo 3. Si sigue fallando, ejecutar ACTUALIZAR_SISTEMA.bat.
    pause
    exit /b 1
)

echo.
echo Verificacion finalizada correctamente.
pause
