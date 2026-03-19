@echo off
REM Script para levantar el Visualizador Telepase por Streamlit con auto-actualización
cd /d "%~dp0"

REM Auto-actualización de código y dependencias (solo si es repositorio git)
if exist "%~dp0\.git" (
    echo Actualizando repo desde Git...
    git -C "%~dp0" pull --ff-only
    echo Instalando dependencias actualizadas...
    "%~dp0Sistema_Python\python.exe" -m pip install -r "%~dp0requirements.txt"
) else (
    echo No se encontró .git, se salta la actualización automática de código.
)

echo Iniciando Streamlit...
"%~dp0Sistema_Python\python.exe" -m streamlit run "%~dp0app.py" --server.headless=true --server.port=8501 --server.address=0.0.0.0
