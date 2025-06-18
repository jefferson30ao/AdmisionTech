### Prompt 1 ·
---

### Prompt 2 · Dataset de ejemplo + validación en Python

> **Objetivo:** Implementa el módulo Python que lee, valida y normaliza los dos `.xlsx`, conforme a los requisitos.
> **Tareas:**
>
> 1. En `frontend/validation.py` implementa:
>
>    * `validate_and_load_responses(path: str) -> pandas.DataFrame`
>    * `validate_and_load_answer_key(path: str) -> pandas.Series`
>    * Conversión A/B/C/D/”” → 0/1/2/3/-1.
> 2. Rechaza filas inválidas y registra error en `logs/validate_*.json`.
> 3. Crea datasets de juguete en `data/` (20 filas).
> 4. Añade prueba *pytest* que espera 20 filas válidas y 2 errores deliberados.
>    **Entrega:** Pull request “feat/validation” con código, datasets y prueba verde.

---

### Prompt 3 · Núcleo C++ (serie) + CMake

> **Objetivo:** Construye la columna vertebral serial en C++17 con CMake.
> **Tareas:**
>
> 1. Dentro de `backend/`, crea:
>
>    * `include/evaluator.hpp`
>    * `src/evaluator_serial.cpp` (función `evaluate_serial(const int8_t* answers, size_t num_students, const int8_t* key, ScoringRule rule, Result* out)` ).
> 2. Define struct `Result { uint32_t score, correct, wrong, blank; }`.
> 3. CMakeLists que genere la librería estática `libevalcore.a`.
> 4. Prueba `tests/test_serial.cpp` con los datasets pequeños.
>    **Entrega:** Pull request “feat/serial-core” con build sin warnings y test pasando.

---

### Prompt 4 · Enlace Python ↔ C++ via pybind11

> **Objetivo:** Exponer la librería C++ al entorno Python.
> **Tareas:**
>
> 1. Añade subdir `backend/bindings/py/` con módulo `pyevalcore`.
> 2. Compila con `pybind11` y publica artefacto de rueda local (`pip install -e .`).
> 3. Escribe en `frontend/bridge.py` la función `run_serial(df_answers, series_key, rule) -> pd.DataFrame`.
> 4. Testea round-trip: carga Dataset → puente → CSV de salida.
>    **Entrega:** Pull request “feat/pybind-bridge” + notebook corto que muestre uso.

---

### Prompt 5 · Modo OpenMP

> **Objetivo:** Añadir evaluación paralela con OpenMP y medir speed-up vs serial.
> **Tareas:**
>
> 1. `src/evaluator_openmp.cpp`; pragma `omp parallel for schedule(dynamic,64)`.
> 2. Selector en código: `enum class Mode { Serial, OpenMP }`.
> 3. Script `scripts/benchmark.py` que ejecute ambos modos y guarde `benchmark.csv`.
> 4. Actualiza pruebas para verificar igualdad de resultados y que el tiempo OpenMP < Serial.
>    **Entrega:** Pull request “feat/openmp” con gráfico simple de speed-up (pandas/Plotly).

---

### Prompt 6 · Interfaz web mínima (FastAPI + Dash)

> **Objetivo:** Prototipo local que permita subir datasets y disparar el modo serial u OpenMP.
> **Tareas:**
>
> 1. FastAPI endpoint `/upload` (multipart) y `/run`.
> 2. Dash layout:
>
>    * Dos botones de carga.
>    * Radio de selección de modo (serial/OpenMP).
>    * Tabla con resultados y gráfico histograma.
> 3. Llama a `bridge.py` bajo el capó.
>    **Entrega:** Pull request “feat/web-mvp”; instrucciones en README para probar en localhost.

---

### Prompt 7 · Modo CUDA (GTX 1650)

> **Objetivo:** Implementa kernel CUDA y conéctalo al selector.
> **Tareas:**
>
> 1. `src/evaluator_cuda.cu` con memoria constante para la clave.
> 2. `CMakeLists` condicional (`if(CUDA_FOUND)`).
> 3. Prueba que verifique igualdad con los modos previos y mida speed-up.
> 4. En la UI, deshabilitar opción CUDA si `cudaGetDeviceCount()==0`.
>    **Entrega:** Pull request “feat/cuda\`” con benchmark actualizado.

---

### Prompt 8 · Modo Pthreads (comparativo ligero)

> **Objetivo:** Proveer alternativa Pthreads para fines académicos.
> **Tareas:**
>
> 1. `src/evaluator_pthreads.cpp` con un pool sencillo.
> 2. Añadir a selector `Mode::Pthreads`.
> 3. Benchmarks comparando todos los modos en `benchmark.csv`.
>    **Entrega:** Pull request “feat/pthreads” + comentario de performance observado.

---

### Prompt 9 · Modo MPI 2 nodos Windows

> **Objetivo:** Permitir ejecución distribuida básica usando MS-MPI.
> **Tareas:**
>
> 1. `src/evaluator_mpi.cpp`: master reparte rangos de filas; esclavo devuelve vector `Result`.
> 2. Script `scripts/run_mpi.ps1` para lanzar en ambas laptops (hostfile simple).
> 3. Retry si `MPI_Send` falla una vez.
>    **Entrega:** Pull request “feat/mpi” con log de prueba real + speed-up registrado.

---

### Prompt 10 · Configuración avanzada y regla de puntaje

> **Objetivo:** UI para cambiar puntajes y opciones de chunk size / procesamiento por lotes.
> **Tareas:**
>
> 1. Modal Dash → edita `scoring.json`.
> 2. Campo numérico “chunk size” con default = “todo en memoria”.
> 3. Backend Python parte DataFrame si se define chunk.
>    **Entrega:** Pull request “feat/advanced-config”.

---

### Prompt 11 · Sistema de logs unificado

> **Objetivo:** Registrar validación, ejecución, errores y benchmarks.
> **Tareas:**
>
> 1. Directorio `logs/` estructurado por fecha.
> 2. Formato JSON Lined (`.jsonl`) con campos: timestamp, level, module, message.
> 3. UI pestaña “Historial” que lista ejecuciones y permite descargar log/CSV.
>    **Entrega:** Pull request “feat/logging”.

---

### Prompt 12 · Scripts de benchmarking automatizado

> **Objetivo:** Facilitar mediciones repetibles y graficar speed-up.
> **Tareas:**
>
> 1. `scripts/benchmark.py --modes serial,openmp,cuda,pthreads,mpi --runs 5`.
> 2. Produce `benchmark.csv` y `benchmark_plot.html`.
> 3. Integra en pestaña “Historial” (mostrar tabla + enlace al HTML).
>    **Entrega:** Pull request “feat/benchmark-automation”.

---

### Prompt 13 · Pruebas de humo end-to-end

> **Objetivo:** Validar flujo completo UI → backend → CSV → dashboard.
> **Tareas:**
>
> 1. Usa `pytest + requests + selenium` (chrome-driver) para cargar datasets y verificar que aparece histograma.
> 2. Garantiza que el puntaje de la fila 1 = valor esperado.
>    **Entrega:** Pull request “feat/e2e-smoke”.

---

### Prompt 14 · Pulido final y documentación

> **Objetivo:** Concluir v1.0.
> **Tareas:**
>
> 1. Rellena `docs/user_guide.md` (instalación, uso, troubleshooting).
> 2. Genera Doxygen HTML en `docs/doxygen/`.
> 3. Actualiza README con GIF corto del dashboard.
> 4. Cierra issues “TODO” restantes y crea *Milestone v1.0* en GitHub.
>    **Entrega:** Pull request “release/v1.0”.

---
