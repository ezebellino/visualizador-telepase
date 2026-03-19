@echo off
title Visualizador Telepase - Actualizacion
cd /d "%~dp0"

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%Sistema_Python\python.exe"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"

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

if not exist "%REQUIREMENTS_FILE%" (
    echo ERROR CRITICO: No se encuentra requirements.txt.
    echo Buscando en: "%REQUIREMENTS_FILE%"
    pause
    exit /b 1
)

echo Este proceso puede modificar el codigo local y las dependencias.
choice /M "Deseas continuar con la actualizacion"
if errorlevel 2 (
    echo.
    echo Actualizacion cancelada por el usuario.
    pause
    exit /b 0
)

if exist "%PROJECT_ROOT%\.git" (
    for /f %%i in ('git -C "%PROJECT_ROOT%" status --porcelain') do (
        echo.
        echo ERROR: hay cambios locales sin confirmar en el repositorio.
        echo Para evitar conflictos, confirma o guarda esos cambios antes de actualizar.
        pause
        exit /b 1
    )

    echo Actualizando repositorio...
    git -C "%PROJECT_ROOT%" pull --ff-only
    if errorlevel 1 (
        echo.
        echo ERROR: fallo la actualizacion del repositorio.
        echo Verifica conexion a Internet, permisos de Git y estado del remoto.
        pause
        exit /b 1
    )
) else (
    echo No se encontro .git. Se omite la actualizacion de codigo.
)

echo.
echo Instalando dependencias...
"%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo.
    echo ERROR: no se pudieron instalar las dependencias.
    echo Verifica conexion, permisos y consistencia de requirements.txt.
    pause
    exit /b 1
)

echo.
echo Validando entorno...
"%PYTHON_EXE%" -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit no quedo disponible luego de la actualizacion.
    pause
    exit /b 1
)

echo Actualizacion finalizada correctamente.
echo Sugerencia: ejecutar VERIFICAR_SISTEMA.bat antes de iniciar la app si deseas una comprobacion rapida.
pause
