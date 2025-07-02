import time
import pandas as pd
import pyevalcore
import numpy as np
import argparse
import os
import plotly.graph_objects as go
import plotly.express as px

def create_sample_data(num_students, num_questions):
    answers = np.random.randint(0, 4, size=(num_students, num_questions), dtype=np.int8)
    key = np.random.randint(0, 4, size=num_questions, dtype=np.int8)
    return answers, key

def benchmark(modes, runs, num_students=1000, num_questions=100):
    all_results = []
    answers, key = create_sample_data(num_students, num_questions)
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = 20
    scoring_rule.wrong = -1.125
    scoring_rule.blank = 0

    for run_idx in range(runs):
        for mode in modes:
            start_time = time.perf_counter()
            if mode == "serial":
                py_results = pyevalcore.run_serial(answers, key, scoring_rule)
            elif mode == "openmp":
                py_results = pyevalcore.run_openmp(answers, key, scoring_rule)
            elif mode == "cuda":
                py_results = pyevalcore.run_cuda(answers, key, scoring_rule)
            elif mode == "pthreads":
                py_results = pyevalcore.run_pthreads(answers, key, scoring_rule)
            elif mode == "mpi":
                # Asumiendo que existe una función run_mpi en pyevalcore
                py_results = pyevalcore.run_mpi(answers, key, scoring_rule)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            end_time = time.perf_counter()
            all_results.append({"mode": mode, "run": run_idx + 1, "time": end_time - start_time})

    df = pd.DataFrame(all_results)
    
    # Guardar resultados en data/benchmark.csv
    os.makedirs('data', exist_ok=True)
    df.to_csv("data/benchmark.csv", index=False)
    print(f"Resultados de benchmark guardados en data/benchmark.csv")

    # Calcular speed-up
    # Promediar tiempos por modo
    avg_times = df.groupby('mode')['time'].mean().reset_index()
    
    # Asegurarse de que el modo 'serial' exista para el cálculo del speed-up
    if 'serial' in avg_times['mode'].values:
        serial_time = avg_times[avg_times['mode'] == 'serial']['time'].iloc[0]
        avg_times['speed_up'] = serial_time / avg_times['time']
    else:
        print("Advertencia: El modo 'serial' no se encontró en los resultados. No se calculará el speed-up.")
        avg_times['speed_up'] = 1.0 # Default a 1 si serial no está presente, o manejar de otra forma

    # Generar gráfico interactivo de speed-up con Plotly
    fig = px.bar(avg_times, x='mode', y='speed_up', title='Speed-up de los Modos de Evaluación (vs. Serial)',
                 labels={'mode': 'Modo de Evaluación', 'speed_up': 'Speed-up'})
    fig.update_traces(marker_color='skyblue')
    fig.update_layout(xaxis_title="Modo", yaxis_title="Speed-up")
    
    # Guardar gráfico en output/benchmark_plot.html
    os.makedirs('output', exist_ok=True)
    fig.write_html("output/benchmark_plot.html")
    print(f"Gráfico de speed-up guardado en output/benchmark_plot.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar benchmarks para diferentes modos de evaluación.")
    parser.add_argument("--modes", type=str, required=True,
                        help="Una cadena de texto separada por comas que especifica los modos de evaluación a probar (ej: serial,openmp,cuda,pthreads,mpi).")
    parser.add_argument("--runs", type=int, default=1,
                        help="Un número entero que indica cuántas veces se debe ejecutar cada modo para promediar los resultados.")
    
    args = parser.parse_args()

    modes_list = [m.strip() for m in args.modes.split(',') if m.strip() != 'mpi']
    
    benchmark(modes_list, args.runs)