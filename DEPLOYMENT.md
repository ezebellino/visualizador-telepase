# Deploy & Operación - Visualizador Telepase

## 1. Requisitos
- Docker Desktop (Windows) o Docker Engine (Linux/Mac)
- Puertos disponibles: 8501
- Acceso a Internet para descargar imágenes si no están en cache

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

## 4. Workflow CI
En `.github/workflows/python-app.yml` se ejecuta en cada push/PR:
- `pip install -r requirements-dev.txt`
- `pytest -q`
- `ruff check .`
- `black --check .`

## 5. Rollback (de emergencia)
- Volver a commit anterior con `git checkout <commit_id>`
- Rebuild y run.

## 6. Nota de seguridad
- No subir archivos `Sistema_Python` al repo si contiene información sensible.
- Sólo el código fuente y requirements.
