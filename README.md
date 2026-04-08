# Visualizador Telepase

Aplicacion web para analizar reportes de eventos Telepase con una arquitectura `FastAPI + React`.

## Stack
- Backend: `FastAPI`
- Frontend: `React + Vite`
- Procesamiento: `pandas`, `numpy`, `openpyxl`, `xlrd`
- Deploy recomendado: `Railway`

## Estructura
- `backend/app/main.py`: API y servidor del frontend compilado
- `backend/app/services.py`: armado de respuesta del dashboard
- `etl.py`: procesamiento y normalizacion de reportes
- `app_logic.py`: metricas y transformaciones para dashboard
- `frontend/`: interfaz React
- `Dockerfile`: imagen de despliegue para Railway

## Desarrollo local

Backend:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --app-dir .
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Build frontend

```bash
cd frontend
npm install
npm run build
```

## Tests

```bash
python -m pytest tests -q
```

## Deploy en Railway

Railway usa el `Dockerfile` del repo.

Flujo sugerido:

```bash
railway login
railway init
railway up
```

En produccion:
- `GET /health`: healthcheck
- `POST /api/v1/dashboard/analyze`: API principal
- `/`: frontend React servido por FastAPI

## Notas
- El frontend usa el mismo origen en produccion, por lo que no necesita `VITE_API_BASE_URL` en Railway para el caso simple de un solo servicio.
- No guardar reportes operativos reales dentro del repositorio.
- El repositorio fue depurado para despliegue: la superficie legacy de `Streamlit`, scripts de Windows y artefactos de empaquetado local ya no forman parte del codigo versionado principal.
- `Sistema_Python` puede mantenerse como ayuda local fuera del flujo de deploy, pero no es parte del release en Railway.
