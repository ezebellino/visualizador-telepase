# PLAN DE MEJORA - Visualizador Telepase

## Objetivo
Tener un proceso iterativo, profesional y con control de calidad para mejorar el sistema de visualización de reportes Telepase que usas en tu trabajo actual.

---

## Fase 1: Diagnóstico inmediato (1-2 días)
- [x] Crear `requirements-dev.txt` con `pytest`, `black`, `ruff`, `isort`, `pydocstyle`, `mypy`.
- [x] Crear estructura de código fuente:
  - `src/visualizador_telepase/` y submódulos. (creado `src/etl.py`, pero se consolidó `etl.py` en raíz para compatibilidad de imports)
  - `tests/test_processing.py`. (creado `tests/test_etl.py`)
- [x] Refactor inicial del backend:
  - `app.py` (interfaz Streamlit).
  - `etl.py` (funciones `load_data`, `find_header_and_data`, `process_events`).
  - `extract.py` (funciones `extract_patente`, `extract_tag`). (combinadas en `etl.py`)
- [ ] Configuración de CI con `pyproject.toml` y `.github/workflows/python-app.yml`.
- [x] Validar que `pytest` pase y que los lints no arrojen errores. (tests local OK)

Entregable: repositorio con pruebas y lint listos.

---

## Fase 2: Robustez de datos + casos de borde (2-3 días)
- [x] Validar esquema mínimo de columnas: `Hora`, `Vía`, `Tránsito`, `Descripción`. `Observación` opcional.
- [x] Mensajes de error claros en UI si esquema inválido.
- [x] `load_data` mejorado:
  - Detectar separador con `csv.Sniffer`.
  - `on_bad_lines='warn'`.
  - Lectura segura para Excel y CSV.
- [x] Mejora de `find_header_and_data` con alias y excepciones.
- [x] `process_events` vectorizado y `groupby` para estado final.
  - Manual si hay evento manual previo.
  - TAG leído si hay registro TAG y no manual.
  - Otro si no hay TAG.
  - Dirección de tránsito heredada desde fila previa si valor faltante.
- [x] Tests: cobertura 80% + casos reales.

Entregable: pipeline estable bajo datos ruidosos.

---

## Fase 3: UI & UX empresarial (2-3 días)
- [ ] Filtros adicionales: `Sentido`, rango horario, `Patente`, `Vía`.
- [ ] Métricas avanzadas: tasa por hora, por vía, nuevos vs repetidos.
- [ ] Visualizaciones: barra por hora, pivote por vía, heatmap.
- [ ] Exportar resultados: CSV/Excel.
- [ ] Manejo datasets grandes con `st.cache_data` + paginación UI.
- [ ] Actualizar README con guía rápida y troubleshooting.

Entregable: UX completo y usable en operación diaria.

---

## Fase 4: Producción y mantenimiento (1 semana)
- [ ] Docker / docker-compose.
- [ ] Empaquetado (poetry o setup).
- [ ] Logging rotativo y alertas (Slack/email). 
- [ ] Monitor / health check.
- [ ] Documentación de operación (`docs/OPERATION.md`, `CHANGELOG`).
- [ ] CI con pruebas en cada PR.

Entregable: Deployable, monitoreado, con respaldo de QA.

---

## Cronograma sugerido
1. Semana 1: Fase 1
2. Semana 2: Fase 2
3. Semana 3: Fase 3
4. Semana 4: Fase 4
5. Semana 5: buffer y ajustes

---

## Seguimiento y actualización
- Mantener este archivo actualizado con listas de control.
- En cada avance cerrar tareas y agregar sección de log de cambios.

### Registro de cambios
- 2026-03-18: Creado plan inicial con 4 fases y entregables.
