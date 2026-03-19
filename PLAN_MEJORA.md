# PLAN DE MEJORA - Visualizador Telepase

## Objetivo
Evolucionar el proyecto hacia una aplicacion confiable, mantenible y profesional, con foco en:

- consistencia de la arquitectura
- calidad tecnica verificable
- operacion estable
- documentacion clara
- mejoras iterativas con bajo riesgo

---

## Diagnostico actual

### Fortalezas detectadas
- La logica principal de procesamiento ya resuelve un problema real y util.
- Existe cobertura automatizada sobre el ETL.
- La app ya tiene una UX funcional para uso operativo diario.
- El proyecto cuenta con Docker, scripts de arranque y CI inicial.

### Riesgos prioritarios detectados
- Hay dos implementaciones de ETL (`etl.py` y `src/etl.py`) con comportamiento diferente.
- El CI no instala dependencias runtime, por lo que puede quedar inconsistente en un entorno limpio.
- La ejecucion local de tests no esta aislada y puede barrer paquetes de `Sistema_Python`.
- Hay documentacion que no refleja exactamente el estado real del proyecto.
- El arranque automatico mezcla ejecucion con actualizacion de codigo y dependencias.
- Existe un archivo de datos versionado que no deberia vivir en el repositorio.

---

## Principios de trabajo
- Avanzar en pasos pequenos, verificables y reversibles.
- No cambiar comportamiento funcional sin cubrirlo con pruebas.
- Priorizar primero consistencia y calidad interna, luego refinamientos visuales y operativos.
- Mantener este plan como fuente unica de verdad para el roadmap tecnico.

---

## Hoja de ruta propuesta

## Fase 0: Estabilizacion de base
Estado: completada.
Objetivo: eliminar inconsistencias estructurales antes de seguir agregando funcionalidades.

- [x] Unificar la implementacion ETL en una sola ubicacion canonical.
- [x] Definir una estructura de proyecto clara para imports y tests.
- [x] Eliminar o adaptar `src/etl.py` para evitar divergencia futura.
- [x] Revisar imports de `app.py` y tests para que apunten a la capa correcta.
- [x] Confirmar que el comportamiento actual siga cubierto por tests.

Nota:
La fuente de verdad actual del procesamiento es `etl.py` en la raiz del proyecto.
`src/etl.py` queda solo como wrapper de compatibilidad mientras estabilizamos la estructura.

### Criterios de aceptacion
- Existe una sola fuente de verdad para el ETL.
- Ningun archivo duplicado puede generar comportamientos distintos.
- La app sigue funcionando sin regresiones visibles.
- Los tests del proyecto pasan contra la estructura nueva.

### Entregable
Repositorio consistente a nivel arquitectura minima.

---

## Fase 1: Calidad automatizada y CI real
Estado: completada.
Objetivo: hacer que la calidad no dependa del entorno local ni de conocimiento manual.

- [x] Ajustar CI para instalar `requirements.txt` y `requirements-dev.txt`.
- [x] Configurar `pytest` para ejecutar solo `tests/`.
- [x] Agregar configuracion centralizada de herramientas (`pyproject.toml` o equivalente).
- [x] Dejar definidos `testpaths`, exclusiones y convenciones de lint.
- [x] Verificar corrida local y en CI con comandos simples y repetibles.

### Criterios de aceptacion
- `pytest` corre igual en local y en CI.
- El pipeline valida tests y formato en un entorno limpio.
- No se recolectan tests de librerias de terceros.
- Las herramientas de calidad tienen una configuracion versionada y explicita.

### Entregable
Base de QA automatizada, confiable y repetible.

---

## Fase 2: Higiene del repositorio y documentacion
Estado: completada.
Objetivo: ordenar el proyecto para que sea entendible y seguro para mantenimiento.

- [x] Revisar `.gitignore` y limpiar artefactos que no deberian versionarse.
- [x] Retirar archivos de datos reales del repo y reemplazarlos por ejemplos anonimizados o instrucciones.
- [x] Actualizar `README.md` para reflejar el flujo real de instalacion, pruebas y uso.
- [x] Actualizar `DEPLOYMENT.md` con procedimientos consistentes con el codigo actual.
- [x] Documentar claramente la diferencia entre modo desarrollo, portable y Docker.
- [x] Registrar decisiones tecnicas basicas del proyecto.

### Criterios de aceptacion
- El repo no contiene datos operativos innecesarios.
- La documentacion coincide con el estado real del proyecto.
- Un tercero puede clonar el repo y entender como correrlo.

### Entregable
Proyecto prolijo, compartible y mantenible.

---

## Fase 3: Robustez operativa
Estado: completada.
Objetivo: mejorar la confiabilidad del arranque y del uso diario.

- [x] Separar scripts de "ejecutar" y "actualizar".
- [x] Evitar `git pull` y `pip install` automaticos en cada arranque operativo.
- [x] Definir un flujo seguro de actualizacion manual o asistida.
- [x] Mejorar mensajes de error y troubleshooting para usuarios finales.
- [x] Revisar healthcheck y procedimientos de recuperacion.

### Criterios de aceptacion
- La app puede iniciarse de forma predecible sin depender de red.
- Las actualizaciones tienen un flujo explicito y controlado.
- Los scripts de arranque son claros para soporte y operacion.

### Entregable
Operacion mas estable y profesional.

---

## Fase 4: Endurecimiento funcional y experiencia de uso
Objetivo: refinar la aplicacion ya estabilizada para un uso empresarial mas pulido.

- [ ] Revisar la UI para mejorar claridad visual y jerarquia de informacion.
- [ ] Reforzar manejo de errores en carga de archivos y filtros extremos.
- [ ] Agregar pruebas para casos reales de borde detectados en operacion.
- [ ] Evaluar separar logica de negocio, capa de presentacion y utilidades.
- [ ] Incorporar logging util para diagnostico sin exponer datos sensibles.

### Criterios de aceptacion
- La app responde mejor a entradas imperfectas.
- Hay mejor trazabilidad ante fallos.
- La interfaz transmite mas confianza y profesionalismo.

### Entregable
Aplicacion robusta y mas madura de cara al usuario final.

---

## Orden recomendado de ejecucion
1. Fase 0: estabilizacion de base
2. Fase 1: calidad automatizada y CI real
3. Fase 2: higiene del repositorio y documentacion
4. Fase 3: robustez operativa
5. Fase 4: endurecimiento funcional y experiencia de uso

---

## Plan inmediato
Esta es la secuencia recomendada para las proximas iteraciones:

1. Unificar el ETL y eliminar duplicacion.
2. Dejar `pytest` acotado al proyecto y estabilizar CI.
3. Limpiar repo y corregir documentacion.
4. Replantear scripts de arranque y actualizacion.
5. Recién despues avanzar con refinamientos de experiencia y logging.

---

## Seguimiento
- Marcar cada tarea cerrada apenas quede implementada y verificada.
- Agregar en cada iteracion una nota breve con fecha y resultado.
- No iniciar una fase nueva si la anterior quedo parcialmente consistente.

### Registro de cambios
- 2026-03-18: Plan reestructurado segun analisis tecnico del proyecto, con foco en consistencia, calidad automatizada, higiene del repo y operacion profesional.
- 2026-03-18: Fase 0 ejecutada a nivel ETL. Se elimino la divergencia entre `etl.py` y `src/etl.py`; tests del proyecto verificados en `tests/`.
- 2026-03-18: Fase 1 ejecutada. Se agrego `pyproject.toml`, `pytest` quedo acotado a `tests/` y el workflow de CI ahora instala dependencias runtime y dev.
- 2026-03-18: Fase 2 ejecutada. Se actualizo `.gitignore`, se retiro el Excel versionado y se reescribieron `README.md` y `DEPLOYMENT.md` con el estado real del proyecto.
- 2026-03-18: Fase 3 iniciada. Se separo el arranque estable (`INICIAR.bat` y `run_telepase.bat`) del flujo de actualizacion (`ACTUALIZAR_SISTEMA.bat`).
- 2026-03-18: Se agrego un launcher oculto con `pythonw.exe` para evitar la consola visible en el uso normal y se mejoro la documentacion operativa.
- 2026-03-18: Fase 3 completada. Se endurecio `ACTUALIZAR_SISTEMA.bat`, se agrego `VERIFICAR_SISTEMA.bat` y se documentaron chequeos de salud y recuperacion.
