@echo off
echo Iniciando el Visualizador...

:: Obtiene la ruta de la carpeta actual
set "CURRENT_DIR=%~dp0"

:: Ejecuta streamlit usando el python de esta carpeta
"%CURRENT_DIR%python.exe" -m streamlit run "%CURRENT_DIR%app.py" --global.developmentMode=false

pause