Sistema de Evaluación Paralela

Desarrollar una **aplicación** capaz de evaluar de manera paralela las respuestas de exámenes. Para ello, se utilizarán datasets en formato CSV o Excel que contienen tanto las respuestas de los postulantes como la clave oficial de respuestas, y se emplearán tecnologías de computación paralela (OpenMP, Pthreads, MPI, CUDA), con el fin de obtener resultados en el menor tiempo posible.

1. **Procesos del Negocio**

El sistema propuesto para la evaluación paralela de los postulantes sigue una serie de procesos lógicos que veremos a continuación en esta parte. Como se espera, se buscará aprovechar al máximo los recursos disponibles.

1. **Carga de Datasets**
    - El programa carga un dataset en csv o excel, que contiene por fila, el DNI del postulante y sus 100 respuestas codificadas con las letras A, B, C, D, “” Respuestas de los estudiantes (student_id, answer_1, ..., answer_n).
    - Clave de respuestas (question_id, correct_answer). respuestas en orden.
    - Esquema de puntajes (value para respuestas correctas, erróneas y en blanco).
2. **Preprocesamiento**
    - Conversión de las respuestas (A, B, C, D, “” a códigos numéricos).
    - Validaciones de integridad de datasets (verificación de que todos los campos estén presentes, que los formato sea correcto).
3. **Selección de módulo de evaluación**
    
    Según el entorno de ejecución y los recursos disponibles, se habilitarán las distintas técnicas de paralelización:
    
    - Evaluación con hilos (OpenMP, Pthreads)
    - Evaluación con GPU, CUDA
    - MPI (Multi Proceso distribuido)
    
    El usuario será capaz de seleccionar el módulo que crea conveniente;
    
4. **Ejecución paralela**
    - Utilización de un **backend en C++ (sin virtual)**, compilado con optimizaciones para operaciones intensivas en cómputo.
5. **Generación de Resultados**
    - Salida en formato CSV: student_id, score, correct_answers, wrong_answers, blank_answers.
6. **Visualización y Dashboard**
    - **Frontend en Python** (FastAPI junto con Plotly/Dash) para:
        - Carga de archivos CSV.
        - Visualización de logs y tiempos de ejecución.
        - Estadísticas globales (promedio, desviación estándar, histograma de puntajes).

2. Arquitectura 

**Frontend (Python)**:

- Permite la manipulación directa de archivos CSV y la generación de gráficos mediante librerías de Python.

**Backend (C++)**:

- Proporciona un control eficiente sobre el manejo de hilos y memoria.
- Bibliotecas y frameworks: pandas, NumPy para manejo y preprocesamiento de datos; FastAPI, Plotly/Dash interfaz y visualización.
- Herramientas de compilación y optimización: uso de opciones de compilación avanzadas (-O3, -march=native, -funroll-loops), así como herramientas de profiling como gprof, nvprof y perf para medición y mejora del rendimiento.
1. **Reglas del negocio**
    - El archivo de entrada debe estar en formato CSV o Excel
    - Cada examen tiene cien preguntas de opción múltiple.
    - La clave de respuestas debe tener el mismo número de preguntas.
    - Cada respuesta correcta tiene un valor de 20 puntos, con un valor de -1,125 por respuesta incorrecta, la pregunta omitida no resta ni suma puntos. El máximo de puntos que se puede obtener es de 2000.
    - El sistema debe poder corregir más de 1000 exámenes en menos de 5 segundos, o eso se espera.

1. Nota/Observaciones
- Se planea utilizaar CUDA en un servicio externo de cloud computer. utilizar memoria constante para la clave de respuestas y puntajes, así como accesos coalescentes a los arreglos de respuestas.
- Con OpenMP, comparar los esquemas de planificación estática y dinámica para ajustar los tamaños de bloques.

Medir tiempos de ejecución con herramientas como gprof, nvprof y perf, y desarrollar scripts automáticos para benchmarking.

