# Operacion y Auditoria

## Objetivo

Este proyecto procesa reportes operativos de Telepase y los transforma en un dashboard web con foco en:

- lectura de antena
- estados operativos
- clasificacion de EXENTOS
- auditoria fina de casos y export de resultados

## Superficies funcionales

La aplicacion expone cuatro vistas principales:

- `Portada operativa`: KPIs, efectividad real de antena, tendencia y mezcla de estados
- `Anexo EXENTOS`: distribucion y detalle del universo EXENTOS / Otros
- `Detalles minuciosos`: separacion entre exenciones reales y eventos operativos
- `Auditoria operativa`: resumen exportable del lote, top de vias/estados y descarga de CSV / JSON

## Flujo tecnico

1. El usuario carga un archivo `.csv`, `.xls` o `.xlsx`
2. FastAPI recibe el archivo en `POST /api/v1/dashboard/analyze`
3. `etl.py` detecta cabeceras, normaliza columnas y agrupa transitos
4. `app_logic.py` calcula metricas, distribuciones y analitica de EXENTOS
5. El frontend React renderiza el dashboard y habilita export de auditoria

## Archivos clave

- `backend/app/main.py`: API, middleware HTTP y observabilidad de requests
- `backend/app/services.py`: armado del payload del dashboard y logs de negocio
- `backend/app/observability.py`: logging estructurado JSON
- `etl.py`: lectura y normalizacion de reportes operativos
- `app_logic.py`: metricas y transformaciones del dashboard
- `frontend/src/App.tsx`: vistas, filtros y export de auditoria
- `frontend/src/styles.css`: estilo de la interfaz

## Observabilidad

El backend emite logs estructurados en Railway con eventos:

- `request_completed`
- `request_failed`
- `dashboard_built`
- `dashboard_build_failed`

Campos relevantes:

- `request_id`
- `file_name`
- `file_size_bytes`
- `total_transits`
- `antenna_base`
- `antenna_reads`
- `antenna_manuals`
- `antenna_read_rate`
- `exempt_total`
- `exempt_classified`
- `active_vias`
- `duration_ms`

Esto permite correlacionar errores de carga con el lote exacto procesado y medir performance del ETL.

## Auditoria operativa

La vista `Auditoria operativa` esta pensada para uso interno y seguimiento:

- resume el archivo procesado y la fecha de generacion
- muestra el corte actual de transitos y EXENTOS
- destaca estados con mayor peso por via
- permite exportar:
  - resumen ejecutivo en `JSON`
  - transitos visibles en `CSV`
  - EXENTOS visibles en `CSV`

Los exports respetan el contexto del dashboard ya construido.

## Operacion local

Backend:

```powershell
Sistema_Python\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir .
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Produccion

- Railway workspace activo: `Pink Panthers`
- URL publica actual: `https://visualizador-telepase.up.railway.app/`

## Recomendaciones siguientes

- agregar export `XLSX` para auditoria ejecutiva
- registrar usuario/operador que genero cada corrida
- persistir historial de corridas para comparativas por fecha o turno
- incorporar alertas basicas por umbral de manuales o caida de efectividad
