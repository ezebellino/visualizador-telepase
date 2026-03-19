# Manual de Usuario - Visualizador Telepase

## 1. Objetivo
Este manual explica cómo instalar, ejecutar y usar el Visualizador Telepase en una PC con Windows.

La aplicación permite:
- cargar reportes `CSV`, `XLS` o `XLSX`
- analizar lecturas correctas de TAG
- detectar fallos manuales
- filtrar por vía, sentido, patente y horario
- exportar resultados a CSV o Excel

---

## 2. Formas de instalación

## Opción A: Uso simple con carpeta portable
Esta es la forma recomendada para la mayoría de los usuarios.

### Qué necesitas
- una carpeta del proyecto ya preparada
- Windows
- navegador web

### Pasos
1. Copia la carpeta `VisualizadorTelepase` en tu PC.
2. Verifica que dentro exista la carpeta `Sistema_Python`.
3. Si quieres un acceso directo con icono, ejecuta `CREAR_ACCESO_DIRECTO.bat`.
4. Usa el acceso directo creado o ejecuta `INICIAR.bat`.

No hace falta instalar Python manualmente si usas esta modalidad.

---

## Opción B: Instalación desde código fuente
Esta opción es útil para usuarios técnicos o desarrollo.

### Qué necesitas
- Python instalado en el sistema
- acceso a la carpeta del proyecto

### Pasos
1. Abre una terminal en la carpeta del proyecto.
2. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Ejecuta la app:

```bash
python -m streamlit run app.py
```

4. Abre `http://localhost:8501`.

---

## 3. Cómo ejecutar la aplicación

## Inicio normal para usuarios
Usa:
- `INICIAR.bat`

Este modo:
- abre la aplicación sin dejar la consola visible
- lanza el navegador automáticamente
- es el modo recomendado para el uso diario

## Inicio con acceso directo e icono
Usa:
- `CREAR_ACCESO_DIRECTO.bat`

Esto crea un acceso directo en el escritorio con el icono de la app.

Luego puedes abrir la aplicación desde ese acceso directo.

## Inicio operativo
Usa:
- `run_telepase.bat`

Este modo:
- inicia la aplicación en modo headless
- sirve para arranque automático o tareas operativas
- no es el modo principal para usuarios finales

---

## 3.1 Como hacer que arranque automaticamente en Windows

Hay dos formas recomendadas.

## Opcion A: Inicio automatico al iniciar sesion
Es la opcion mas simple para una PC de uso operativo.

### Pasos
1. Ejecuta `CREAR_ACCESO_DIRECTO.bat`.
2. Verifica que se haya creado el acceso directo en el escritorio.
3. Presiona `Win + R`.
4. Escribe `shell:startup` y presiona Enter.
5. Se abrira la carpeta de Inicio de Windows.
6. Copia dentro de esa carpeta el acceso directo creado para la app.
7. Reinicia sesion o reinicia la PC para probar.

### Resultado
Cada vez que el usuario inicie sesion en Windows, la app se abrira automaticamente.

### Cuando conviene
- si la PC siempre inicia con el mismo usuario
- si quieres una configuracion simple
- si quieres evitar consola visible

## Opcion B: Programador de tareas de Windows
Es la opcion mas profesional cuando quieres mayor control.

### Cuando conviene
- si quieres retrasar unos segundos el inicio
- si quieres dejar la tarea documentada en Windows
- si prefieres un arranque mas controlado que la carpeta Inicio

### Pasos
1. Abre `Programador de tareas`.
2. Elige `Crear tarea`.
3. En la pestaña `General`, ponle un nombre como `Visualizador Telepase`.
4. Marca `Ejecutar solo cuando el usuario haya iniciado sesion`.
5. En la pestaña `Desencadenadores`, agrega un desencadenador `Al iniciar sesion`.
6. En la pestaña `Acciones`, crea una accion `Iniciar un programa`.
7. En `Programa o script`, coloca:

```text
wscript.exe
```

8. En `Agregar argumentos`, coloca:

```text
//nologo "C:\RUTA\A\VisualizadorTelepase\scripts\launch_app_hidden.vbs"
```

9. Reemplaza `C:\RUTA\A\VisualizadorTelepase` por la ruta real de tu carpeta.
10. Guarda la tarea y ejecutala manualmente una vez para comprobar.

### Nota importante
- Si mueves la carpeta del proyecto, debes actualizar el acceso directo o la tarea.
- Si vas a usar el proyecto desde pendrive, primero copia toda la carpeta a la PC y despues configura el arranque automatico.

---

## 4. Primer uso
1. Ejecuta `INICIAR.bat`.
2. Espera a que se abra el navegador.
3. En la pantalla principal, usa el botón de carga de archivo.
4. Selecciona un archivo `CSV`, `XLS` o `XLSX`.
5. Espera a que se muestren las métricas y gráficos.

Si el archivo es válido, verás:
- resumen operativo
- gráficos por estado
- heatmap por vía
- detalle paginado
- opciones de exportación

---

## 5. Cómo usar los filtros

En la barra lateral puedes filtrar por:
- vía
- sentido
- patente
- hora de inicio
- hora de fin
- tipo de gráfico
- tamaño de página

### Recomendaciones
- Si no seleccionas ninguna vía, no habrá resultados.
- Si no seleccionas ningún sentido, no habrá resultados.
- Si la hora de inicio es mayor que la hora de fin, la app mostrará una advertencia.
- Si filtras demasiado y no ves datos, vuelve a ampliar vías, sentidos o rango horario.

---

## 6. Cómo exportar resultados

En la pestaña de detalle puedes exportar:
- `CSV`
- `Excel`

Los archivos exportados contienen el subconjunto actualmente filtrado.

Esto permite:
- guardar evidencia
- compartir resultados
- continuar análisis por fuera de la app

---

## 7. Cómo actualizar la aplicación

Si la carpeta del proyecto tiene `.git` y está conectada a un repositorio, puedes usar:
- `ACTUALIZAR_SISTEMA.bat`

Este script:
- pide confirmación antes de continuar
- actualiza el código
- reinstala dependencias necesarias
- valida que Streamlit siga disponible

No uses este script mientras tengas cambios locales sin guardar o sin confirmar en Git.

---

## 8. Cómo verificar si todo está bien

Usa:
- `VERIFICAR_SISTEMA.bat`

Este script revisa:
- que exista `python.exe`
- que exista `pythonw.exe`
- que exista `app.py`
- que exista `requirements.txt`
- que Streamlit esté disponible
- que la app responda en `http://127.0.0.1:8501`

Es útil cuando:
- la app no abre
- el navegador no carga
- sospechas que faltan dependencias

---

## 9. Problemas comunes

## La aplicación no abre
Prueba este orden:
1. Ejecuta `VERIFICAR_SISTEMA.bat`.
2. Si falla, ejecuta `ACTUALIZAR_SISTEMA.bat`.
3. Intenta de nuevo con `INICIAR.bat`.

## Se abre el navegador pero no carga datos
- Verifica que el archivo tenga contenido.
- Verifica que el archivo tenga columnas equivalentes a Hora, Vía, Tránsito y Descripción.
- Si el archivo fue exportado manualmente, vuelve a generarlo desde origen.

## No aparecen resultados
- Revisa filtros de vía y sentido.
- Revisa el rango horario.
- Quita el filtro de patente.

## No se genera el Excel
- Intenta primero con exportación CSV.
- Cierra otras aplicaciones que puedan estar usando archivos similares.
- Vuelve a intentar la exportación.

## Quiero usar la app sin ver la consola
Usa:
- `INICIAR.bat`

O crea el acceso directo con:
- `CREAR_ACCESO_DIRECTO.bat`

## Quiero que la app arranque sola al prender la PC
- Usa la carpeta `shell:startup` si quieres la opcion mas simple.
- Usa el `Programador de tareas` si quieres una configuracion mas controlada.
- Revisa la seccion `3.1 Como hacer que arranque automaticamente en Windows`.

---

## 10. Archivos importantes

- `INICIAR.bat`: inicio normal sin consola visible
- `CREAR_ACCESO_DIRECTO.bat`: crea acceso directo con icono
- `ACTUALIZAR_SISTEMA.bat`: actualiza código y dependencias
- `VERIFICAR_SISTEMA.bat`: chequeo rápido del sistema
- `run_telepase.bat`: inicio operativo headless
- `logs/visualizador_telepase.log`: archivo de diagnóstico

---

## 11. Recomendaciones de uso
- Mantén una copia de la carpeta completa.
- No elimines `Sistema_Python`.
- No modifiques archivos internos si no sabes para qué sirven.
- Guarda los reportes originales por separado.
- Si algo falla, usa primero `VERIFICAR_SISTEMA.bat`.

---

## 12. Resumen rápido

Para un usuario normal:
1. Abrir `INICIAR.bat`
2. Cargar archivo
3. Usar filtros
4. Exportar resultados si hace falta

Para soporte:
1. Ejecutar `VERIFICAR_SISTEMA.bat`
2. Si hace falta, correr `ACTUALIZAR_SISTEMA.bat`
3. Revisar `logs/visualizador_telepase.log`
