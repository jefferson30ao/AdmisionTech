# Sistema de Evaluación Paralela

*Documento de especificación técnica*

> Este documento describe de forma integral el proyecto —incluye las decisiones ya fijadas.
> Al finalizar, una IA agéntica debería poder guiar, coordinar y/o ejecutar las tareas de desarrollo con mínima tutela humana.

---

## 1 · Objetivo general

Construir una aplicación que **corrija exámenes de 100 preguntas** a gran escala (decenas de miles de postulantes) aplicando **paralelismo** para reducir el tiempo de cómputo a segundos por lote.

---

## 2 · Requisitos funcionales

| #     | Descripción                                                                                                                                                  |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RF-01 | Cargar dos archivos **.xlsx**: `respuestas_postulantes.xlsx` (101 cols) y `clave.xlsx` (2 cols).                                                             |
| RF-02 | Validar ambos datasets (estructura fija, 8 dígitos de DNI, mayúsculas/minúsculas indiferentes). Rechazar fila inválida y registrar error.                    |
| RF-03 | Convertir respuestas *(A = 0, B = 1, C = 2, D = 3, vacío = -1)*.                                                                                             |
| RF-04 | Permitir al usuario **elegir el modo de evaluación**: <br>• Serial (referencia) • OpenMP • Pthreads • CUDA *(GTX 1650 local)* • MPI *(máx. 2 nodos Windows)* |
| RF-05 | Entregar `resultados.csv` con: `student_id, score, correct, wrong, blank`.                                                                                   |
| RF-06 | Mostrar un **dashboard local** con: tiempo total, speed-up vs serial, histograma de puntajes, tabla de ejecuciones previas.                                  |
| RF-07 | Botón de **configuración avanzada** por cada dataset y por cada modo (p. ej., “procesar por lotes” o “usar servicio CUDA en la nube”).                       |
| RF-08 | Registrar logs de validación, ejecución y fallos; descargables en CSV/JSON.                                                                                  |
| RF-09 | Permitir cambiar la **regla de puntaje** (aciertos = 20, errores = -1.125, blanco = 0) mediante diálogo modal; valores por pregunta, sin redondear.          |

---

## 3 · Modelo de datos

### 3.1 Dataset de respuestas (`.xlsx`)

| Columna                   | Tipo      | Regla                                    |
| ------------------------- | --------- | ---------------------------------------- |
| `DNI`                     | string(8) | Solo dígitos, duplicados ⇒ fila inválida |
| `answer_1` … `answer_100` | char      | `A/B/C/D` o vacío                        |

### 3.2 Clave de respuestas

| Columna          | Tipo        | Regla                          |
| ---------------- | ----------- | ------------------------------ |
| `question_id`    | int (1-100) | Estrictamente orden ascendente |
| `correct_answer` | char        | `A/B/C/D`                      |

### 3.3 Resultado

```csv
student_id,score,correct_answers,wrong_answers,blank_answers
01234567,1520,76,18,6
...
```

---

## 4 · Arquitectura de alto nivel

```text
┌──────────────┐   REST / CLI   ┌─────────────────┐
│  Dash+FastAPI│◀──────────────▶│ Módulo Python   │  pandas, NumPy
│    Frontend  │                │  (puente)       │
└──────────────┘                └──────▲──────────┘
                                       │ pybind11
                          ┌────────────┴────────────┐
                          │  Núcleo C++17 (sin RTTI)│
                          │  ────────┬──────────────│
                          │          │              │
                    OpenMP│      Pthreads         CUDA
                          │          │              │
                          └─────MPI (local 2 nodos)─┘
```

### 4.1 Flujo resumido

1. **Frontend** recibe los `.xlsx`, invoca validaciones en Python.
2. Python llama al **núcleo C++** vía pybind11 (opción sugerida por simplicidad y velocidad).
3. El núcleo delega a la **estrategia** elegida (OpenMP, CUDA, …).
4. Se genera `resultados.csv` y métricas; frontend actualiza dashboard.

---

## 5 · Diseño del backend C++

| Aspecto         | Decisión / Sugerencia                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lenguaje        | C++17, sin RTTI/virtual (estructura de pods + funciones libres).                                                                                                          |
| Build           | **CMake** + `-O3 -march=native -funroll-loops`. <br>CUDA: compilado condicional con `find_package(CUDA)`; flags `-use_fast_math`.                                         |
| Estrategia base | Evaluar por **estudiante** (fila) ⇒ excelente para OpenMP/threads; copiar clave a memoria constante en CUDA.                                                              |
| OpenMP          | `#pragma omp parallel for schedule(dynamic, 64)` por defecto; permitir cambiar a `static` vía CLI.                                                                        |
| Pthreads        | Implementación espejo de OpenMP (útil para benchmark).                                                                                                                    |
| CUDA            | Kernel con `gridDim.x = ceil(N/256)`, `blockDim.x = 256`. Acceso coalescente: <br>`answers[row * 100 + col]`.                                                             |
| MPI (simple)    | División por rangos de filas; uso de **MS-MPI** en Windows. Master reparte, slaves devuelven vectores de puntaje. Reintento: volver a procesar chunk si `MPI_Send` falla. |
| I/O             | Leer clave una sola vez a `std::array<int,100>`; usar `mmap` (Windows: `CreateFileMapping`) opcional para datasets > 500 MB.                                              |

---

## 6 · Frontend y dashboard

| Elemento     | Elección                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Framework    | **FastAPI** + **Dash (Plotly)** sobre Uvicorn.                                                                                                                                                                                                                                                                                                                                                    |
| Distribución | Ejecutable único (`python -m venv venv && pip install -r requirements.txt`).                                                                                                                                                                                                                                                                                                                      |
| UX mínima    | <br>1. **Carga de datasets** (dos botones + rueda loader). <br>2. Selección de modo (radiobuttons); botones deshabilitados si recurso no detectado. <br>3. Panel “Configuración avanzada” (modal). <br>4. Botón **“Iniciar evaluación”**. <br>5. Pestaña “Historial” con tabla de ejecuciones, tiempos, speed-up.<br>6. Gráficos: histograma de puntajes (Plotly) y barra de correct/wrong/blank. |
| Logs         | Mostrar al terminar; exportar CSV. Para streaming en futuro: WebSockets.                                                                                                                                                                                                                                                                                                                          |

---

## 7 · Configuración y extensiones

| Tema                        | Implementación recomendada                                                                                        |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Regla de puntaje**        | Archivo `scoring.json` editado por el modal; Python lo pasa al núcleo.                                            |
| **Procesamiento por lotes** | Parámetro “chunk\_size” en config; Python parte el DataFrame y llama repetidamente al backend.                    |
| **CUDA en la nube**         | Mantener interfaz gRPC hueca (“TODO”); por defecto, la GTX 1650 local es suficiente.                              |
| **Scripts de benchmarking** | Bash/PowerShell: corre serial + OpenMP + CUDA, guarda `benchmark.csv`. Frontend lee y grafica speed-up histórico. |
| **Autenticación**           | *Fuera de alcance* (local single-user).                                                                           |
| **Docker**                  | *No necesario* (local).                                                                                           |

---

## 8 · Logging y manejo de errores

```text
logs/
 ├─ validate_2025-06-18T12-03-14.json
 ├─ run_2025-06-18T12-03-27.json
 └─ error_2025-06-18T12-03-27.txt
```

*Formato JSON line by line para fácil parseo; nivel = INFO/ERROR.
Ante fallo en CUDA o MPI ⇢ mostrar diálogo y registrar.*

---

## 9 · Pruebas básicas sugeridas

| Tipo          | Herramienta                                                               | Nota |
| ------------- | ------------------------------------------------------------------------- | ---- |
| Unit C++      | **doctest** (ligero, header-only).                                        |      |
| Smoke         | Dataset pequeño (3 filas) + todas las estrategias; comparar puntuaciones. |      |
| Performance   | Script `benchmark.ps1` ↔ CSV histórico.                                   |      |
| Validación UI | Selenium *(opcional; manual es aceptable en esta fase)*.                  |      |

---

## 10 · Hoja de ruta (indicativa)

| Semana | Hito                                                      |
| ------ | --------------------------------------------------------- |
| 1      | Estructura Git + CMake + serial C++.                      |
| 2      | Validación/lectura `.xlsx` en Python (pandas + openpyxl). |
| 3      | Integración pybind11 + OpenMP.                            |
| 4      | Dashboard básico (carga, tabla, histograma).              |
| 5      | CUDA (GTX 1650) + comparativa speed-up.                   |
| 6      | MPI 2 nodos + selector de modo + logs robustos.           |
| 7      | Configuración avanzada (chunk\_size, scoring).            |
| 8      | Benchmarks automatizados + pulido interfaz.               |

---

## 11 · Buenas prácticas de implementación

1. **Mantener el core puramente numérico** (sin dependencias externas) para facilitar pruebas de rendimiento.
2. **Commit temprano y frecuente** (`feature/modo-cuda`, `ci/benchmark`).
3. Documentar funciones críticas en Doxygen; generar HTML estático.
4. Evitar sobre-ingeniería: empezar por **OpenMP** (5-10 líneas de pragma) antes de Pthreads.
5. Para selección dinámica de dispositivo CUDA, usar `cudaGetDeviceCount` y deshabilitar botón si `count==0`.
6. Garantizar **reproducibilidad**: registrar `git commit hash` en los logs.

---

## 12 · Pendientes / futuros

* Servicio CUDA en la nube (requiere credenciales y gestor de colas).
* Monitoreo Prometheus + Grafana si la app se hace multi-usuario.
* Extensión a preguntas de opción múltiple o formatos mixtos.

---
