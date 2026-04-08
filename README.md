# Visualizador Telepase

Aplicacion web para analizar reportes de eventos Telepase con arquitectura `FastAPI + React`.

## Stack
- Backend: `FastAPI`
- Frontend: `React + Vite`
- Procesamiento: `pandas`, `numpy`, `openpyxl`, `xlrd`
- Deploy: `Railway`

## Estructura
- `backend/app/main.py`: API y servidor del frontend compilado
- `backend/app/services.py`: armado de respuesta del dashboard
- `backend/app/observability.py`: logging estructurado y eventos operativos
- `etl.py`: procesamiento y normalizacion de reportes
- `app_logic.py`: metricas y transformaciones para dashboard
- `frontend/`: interfaz React
- `Dockerfile`: imagen de despliegue para Railway
- `OPERACION_Y_AUDITORIA.md`: documentacion operativa y de observabilidad

## Vistas principales

- `Portada operativa`
- `Anexo EXENTOS`
- `Detalles minuciosos`
- `Auditoria operativa` con export de `CSV` y `JSON`

## Desarrollo local

Backend:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir .
```

Si usas el Python portable del proyecto:

```bash
Sistema_Python\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir .
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Build local de produccion

```bash
cd frontend
npm install
npm run build
cd ..
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --app-dir .
```

## Deploy en Railway

Railway usa el `Dockerfile` del repo y publica un unico servicio que sirve API + frontend compilado.

Flujo base:

```bash
railway login
railway init
railway up
```

Proyecto desplegado:
- URL publica: `https://visualizador-telepase.up.railway.app/`
- `GET /health`: healthcheck
- `POST /api/v1/dashboard/analyze`: API principal
- `/`: frontend React servido por FastAPI

## Notas
- El frontend usa el mismo origen en produccion, por lo que no necesita `VITE_API_BASE_URL` en Railway para este despliegue de un solo servicio.
- Railway emite logs de request y de negocio para cada corrida del dashboard.
- No guardar reportes operativos reales dentro del repositorio.
- El repositorio fue depurado para despliegue: la superficie legacy de `Streamlit`, scripts de Windows y artefactos locales ya no forman parte del codigo versionado principal.
- `Sistema_Python` puede mantenerse como ayuda local, pero no forma parte del release en Railway.
