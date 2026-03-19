# Visualizador Telepase

![Demo de la aplicacion](demo.png)

Aplicacion en Streamlit para analizar reportes de eventos Telepase, detectar lecturas correctas de TAG, identificar intervenciones manuales y filtrar la operacion por via, sentido, horario y patente.

## Que hace hoy
- Carga archivos `csv`, `xls` y `xlsx`.
- Detecta la fila real de cabecera en reportes ruidosos.
- Normaliza columnas clave como `Hora`, `Via`, `Transito` y `Descripcion`.
- Extrae `Patente` y `TAG` desde observaciones mediante expresiones regulares.
- Agrupa eventos por numero de transito para evitar duplicados funcionales.
- Clasifica cada transito como lectura correcta, manual o otro.
- Permite filtrar resultados y exportarlos a CSV y Excel.

## Estructura actual
- `app.py`: interfaz Streamlit.
- `etl.py`: fuente de verdad del procesamiento.
- `src/etl.py`: wrapper de compatibilidad.
- `tests/test_etl.py`: pruebas automatizadas del ETL.
- `PLAN_MEJORA.md`: roadmap tecnico.

## Ejecutar en desarrollo
Con Python del sistema:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Con el Python portable incluido:

```bash
Sistema_Python\python.exe -m pip install -r requirements.txt
Sistema_Python\python.exe -m streamlit run app.py
```

Abrir en `http://localhost:8501`.

## Ejecutar tests
Con Python del sistema:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Con el Python portable:

```bash
Sistema_Python\python.exe -m pytest -q
```

`pytest` ya esta configurado para ejecutar solo la carpeta `tests/`.

## Ejecutar con Docker
```bash
docker build -t visualizador-telepase .
docker run --rm -p 8501:8501 visualizador-telepase
```

## Scripts disponibles
- `INICIAR.bat`: inicio rapido que delega el arranque a un launcher oculto.
- `run_telepase.bat`: inicio operativo estable en modo headless.
- `ACTUALIZAR_SISTEMA.bat`: actualiza codigo y dependencias de forma explicita.
- `CREAR_ACCESO_DIRECTO.bat`: crea un acceso directo de Windows con `antena.ico`.
- `scripts/launch_app_hidden.vbs`: inicia la app sin dejar la consola abierta y abre el navegador.

## Flujo operativo recomendado
- Para usar la aplicacion en forma normal: `INICIAR.bat`.
- Para ejecutar la app como servicio local o arranque automatico: `run_telepase.bat`.
- Para actualizar el sistema de manera manual y controlada: `ACTUALIZAR_SISTEMA.bat`.
- Para evitar la consola visible en Windows: usar el acceso directo generado o `INICIAR.bat`.

## Icono del lanzador en Windows
Un archivo `.bat` no puede llevar un icono embebido propio en el Explorador de Windows. Para resolverlo de forma profesional, el proyecto incluye `CREAR_ACCESO_DIRECTO.bat`, que genera un acceso directo `.lnk` en el escritorio usando `antena.ico` y apuntando al launcher oculto de la aplicacion.

## Calidad automatizada
El proyecto incluye:

- `pytest` para pruebas.
- `ruff` para chequeos estaticos.
- `black` para formato.
- GitHub Actions en `.github/workflows/python-app.yml`.

## Datos y privacidad
El repositorio no deberia almacenar reportes operativos reales. Para pruebas manuales, usar archivos anonimizados fuera del repo o generar muestras sinteticas.

## Estado del proyecto
El proyecto esta en proceso de profesionalizacion incremental. La hoja de ruta vigente esta documentada en `PLAN_MEJORA.md`.
