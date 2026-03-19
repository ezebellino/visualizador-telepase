# Deploy & Operación - Visualizador Telepase

## 1. Requisitos
- Docker Desktop (Windows) o Docker Engine (Linux/Mac)
- Puertos disponibles: 8501
- Acceso a Internet para descargar imágenes si no están en cache
- Para ejecución Windows sin Docker: Python embebido en `Sistema_Python`.

## 2. Ejecutar localmente (modo app directa)
```bash
cd "C:\Users\ezebe\OneDrive\Escritorio\VisualizadorTelepase"
\\ Asegurarse de haber instalado dependencias:
Sistema_Python\python.exe -m pip install -r requirements.txt

Sistema_Python\python.exe -m streamlit run app.py
```
Abrir: `http://localhost:8501`

## 3. Ejecutar por Docker
1. Build:
```bash
docker build -t visualizador-telepase .
```
2. Run:
```bash
docker run --rm -p 8501:8501 visualizador-telepase
```
3. Abrir: `http://localhost:8501`

### 3.1 Si el contenedor no arranca
- Verificar Docker Desktop está ejecutándose.
- En Windows: debe estar el motor `Docker Desktop Linux Engine` activo.
- Si da error `cannot find the file specified` equivalente a:
  - Docker no está iniciado
  - Reinstalar/actualizar Docker Desktop

## 4. Ejecución al iniciar Windows

### Opción 1: Carpeta de inicio
1. Crear un acceso directo al `run_telepase.bat`.
2. Mover ese acceso directo a:
   `C:\Users\<usuario>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
3. Reiniciar. Al iniciar Windows se ejecutará automáticamente.

### Opción 2: Task Scheduler (recomendado)
1. Abrir 'Programador de tareas'.
2. Crear tarea básica:
   - Nombre: Visualizador Telepase
   - Desencadenar: Al iniciar sesión o al iniciar el sistema (según preferencia)
   - Acción: Iniciar un programa
   - Programa/script: `run_telepase.bat`
   - Iniciar en: `C:\Users\<usuario>\OneDrive\Escritorio\VisualizadorTelepase`
3. Permitir ejecutar con privilegios altos y si no ha iniciado sesión.

### Opción 3: Docker en servicio Windows (avanzado)
- Instalar y configurar `docker run --rm -p 8501:8501 visualizador-telepase` como servicio.

## 5. Healthcheck y supervisión

### 5.1 Healthcheck en Docker
En `Dockerfile` se agregó:
- `HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \` 
- `CMD curl -f http://localhost:8501/ || exit 1`

Esto permite:
- detectar si la app no responde
- que orquestadores (Docker Compose, Kubernetes) reinicien el contenedor

### 5.2 Monitorización local simple
- Usar `docker ps` para ver estado: `healthy` / `unhealthy`.
- Logs: `docker logs -f <container_id>`.

### 5.3 Auto-actualización al iniciar
`run_telepase.bat` ahora hace:
- `git pull --ff-only` (si existe `.git`)
- `pip install -r requirements.txt`
- inicia Streamlit.

## 6. Workflow CI
En `.github/workflows/python-app.yml` se ejecuta en cada push/PR:
- `pip install -r requirements-dev.txt`
- `pytest -q`
- `ruff check .`
- `black --check .`

## 7. Rollback (de emergencia)
- Volver a commit anterior con `git checkout <commit_id>`
- Rebuild y run.

## 6. Nota de seguridad
- No subir archivos `Sistema_Python` al repo si contiene información sensible.
- Sólo el código fuente y requirements.
