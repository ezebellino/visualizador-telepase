# Release Notes - v1.0.0

## Visualizador Telepase v1.0.0
Primera version estable del proyecto.

## Incluye
- procesamiento ETL unificado y validado
- dashboard operativo con filtros, metricas y exportacion
- arranque normal sin consola visible
- acceso directo con icono para Windows
- flujo separado para iniciar, actualizar y verificar el sistema
- logging diagnostico en archivo
- manual de usuario y documentacion operativa

## Mejoras destacadas
- se elimino la divergencia entre implementaciones de ETL
- se estabilizo `pytest`, `ruff`, `black` y la CI
- se profesionalizo el arranque en Windows con `INICIAR.bat`
- se agrego limpieza automatica de instancias viejas de Streamlit al iniciar
- se mejoro la UX operativa del dashboard
- se incorporo un instructivo de arranque automatico en Windows

## Scripts principales
- `INICIAR.bat`: inicio normal sin consola visible
- `run_telepase.bat`: inicio operativo headless
- `ACTUALIZAR_SISTEMA.bat`: actualizacion controlada
- `VERIFICAR_SISTEMA.bat`: chequeo rapido del sistema
- `CREAR_ACCESO_DIRECTO.bat`: acceso directo con icono

## Validacion de la version
- `pytest -q`: OK
- `ruff check .`: OK

## Recomendacion de distribucion
Para uso portable, distribuir la carpeta completa del proyecto junto con `Sistema_Python`.
