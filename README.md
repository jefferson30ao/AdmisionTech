# Sistema de Evaluación Paralela

Este proyecto tiene como objetivo construir una aplicación que corrija exámenes de 100 preguntas a gran escala aplicando paralelismo para reducir el tiempo de cómputo.

Trabajo Final del Curso de Programación Paralela de la UNMSM, Facultad de Ingeniería de Sistemas e Informática

## Instalación y ejecución del prototipo web

Para probar localmente la nueva interfaz FastAPI + Dash, sigue los siguientes pasos:

1.  **Crear y activar un entorno virtual:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Ejecutar la aplicación:**
    ```bash
    uvicorn frontend.bridge:app --reload
    ```
4.  **Acceder en el navegador a:**
    -   `http://localhost:8000/dash` para ver el dashboard.
    -   **Endpoints:**
        -   `POST /upload` para cargar los archivos `.xlsx`.
        -   `POST /run` para disparar la evaluación (modo serial/OpenMP).