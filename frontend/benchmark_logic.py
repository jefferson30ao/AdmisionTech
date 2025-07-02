import time
import pandas as pd
import pyevalcore
import numpy as np
import os
from frontend.evaluation_logic import run_serial, run_openmp, run_cuda, run_pthreads

def run_full_benchmark(students_df: pd.DataFrame, key_series: pd.Series, scoring_rules: dict, modes_to_run: list = None):
    """
    Ejecuta un benchmark de los modos de evaluación especificados con los datos proporcionados,
    calcula el speed-up y guarda los resultados en data/benchmark_summary.csv.

    Args:
        students_df (pd.DataFrame): DataFrame con las respuestas de los estudiantes.
        key_series (pd.Series): Serie con la clave de respuestas.
        scoring_rules (dict): Diccionario con las reglas de puntuación.
        modes_to_run (list, optional): Lista de modos a ejecutar. Si es None, se ejecutan todos.
    """
    all_results = []
    if modes_to_run is None:
        modes = ["serial", "openmp", "cuda", "pthreads"]
    else:
        modes = modes_to_run

    for mode in modes:
        start_time = time.perf_counter()
        if mode == "serial":
            _ = run_serial(students_df, key_series, scoring_rules)
        elif mode == "openmp":
            _ = run_openmp(students_df, key_series, scoring_rules)
        elif mode == "cuda":
            _ = run_cuda(students_df, key_series, scoring_rules)
        elif mode == "pthreads":
            _ = run_pthreads(students_df, key_series, scoring_rules)
        # No hay else, ya que los modos están fijos
        end_time = time.perf_counter()
        all_results.append({"mode": mode, "time": end_time - start_time})

    df = pd.DataFrame(all_results)
    
    # Calcular speed-up
    if 'serial' in df['mode'].values:
        serial_time = df[df['mode'] == 'serial']['time'].iloc[0]
        df['speed_up'] = serial_time / df['time']
    else:
        df['speed_up'] = 1.0 # Default a 1 si serial no está presente

    # Guardar resultados promediados y speed-up en un nuevo archivo
    os.makedirs('data', exist_ok=True)
    df.to_csv("data/benchmark_summary.csv", index=False)
    print(f"Resultados de benchmark actualizados en data/benchmark_summary.csv")
