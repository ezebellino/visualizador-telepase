# Deployment y operacion

## Objetivo
Documentar la forma actual de ejecutar, desplegar y mantener el Visualizador Telepase sin depender de supuestos implícitos.

## Modos de ejecucion soportados

### 1. Desarrollo local
Con Python del sistema:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Con Python portable:

```bash
Sistema_Python\python.exe -m pip install -r requirements.txt
Sistema_Python\python.exe -m streamlit run app.py
```

La aplicacion queda disponible en `http://localhost:8501`.

### 2. Docker
Build:

```bash
docker build -t visualizador-telepase .
```

Run:

```bash
docker run --rm -p 8501:8501 visualizador-telepase
```

## Scripts de inicio

### `INICIAR.bat`
- Pensado para usuarios finales.
- Ejecuta un launcher oculto basado en `pythonw.exe`.
- No instala dependencias ni actualiza el repositorio.
- Evita dejar la consola abierta durante el uso normal.

### `ACTUALIZAR_SISTEMA.bat`
- Ejecuta `git pull --ff-only` si el proyecto es un repositorio Git.
- Instala dependencias desde `requirements.txt`.
- Se usa solo cuando se quiere actualizar el sistema de forma explicita.

### `CREAR_ACCESO_DIRECTO.bat`
- Crea un acceso directo `.lnk` en el escritorio.
- Usa `antena.ico` como icono visible en Windows.
- Apunta al launcher oculto para evitar consola visible.

### `run_telepase.bat`
- Pensado para una operacion mas automatizada.
- Inicia Streamlit en modo headless en el puerto `8501`.
- No modifica codigo ni dependencias durante el arranque.

## Flujo operativo recomendado
- Usar `INICIAR.bat` para usuarios finales.
- Usar `run_telepase.bat` para tareas de inicio automatico o modo servicio.
- Usar `ACTUALIZAR_SISTEMA.bat` cuando se quiera actualizar el sistema.
- Usar `CREAR_ACCESO_DIRECTO.bat` si se quiere un acceso directo con icono y sin consola visible.

## Healthcheck del contenedor
El `Dockerfile` implementa un `HEALTHCHECK` con `urllib.request` contra `http://localhost:8501`.

Esto permite:
- detectar si la app dejo de responder
- exponer un estado `healthy` o `unhealthy` en Docker

Para revisar estado y logs:

```bash
docker ps
docker logs -f <container_id>
```

## Calidad y validacion antes de desplegar
Instalar dependencias:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Ejecutar validaciones:

```bash
python -m pytest -q
ruff check .
black --check .
```

## CI actual
El workflow de GitHub Actions:
- instala dependencias runtime y dev
- ejecuta `python -m pytest -q`
- corre `ruff check .`
- corre `black --check .`

Archivo: `.github/workflows/python-app.yml`

## Recomendaciones operativas
- No versionar reportes reales dentro del repositorio.
- Mantener `Sistema_Python` fuera de Git.
- Hacer pruebas locales antes de cada push importante.
- Usar Docker para una ejecucion mas predecible si el entorno local cambia seguido.

## Rollback
Si una version nueva falla:

1. Volver al commit anterior estable.
2. Reinstalar dependencias si cambiaron.
3. Reejecutar tests.
4. Reiniciar la app o recrear el contenedor.
