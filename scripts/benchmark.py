import pandas as pd
import numpy as np
import argparse
import os
import plotly.express as px
from frontend.benchmark_logic import run_full_benchmark, generate_benchmark_plot
from frontend.config_utils import load_scoring_config
import pyevalcore # Necesario para ScoringRule si se usa en create_sample_data

def create_sample_data(num_students, num_questions):
    answers_np = np.random.randint(0, 4, size=(num_students, num_questions), dtype=np.int8)
    key_np = np.random.randint(0, 4, size=num_questions, dtype=np.int8)
    
    # Convertir a DataFrame y Series para que coincidan con la firma de run_full_benchmark
    df_answers = pd.DataFrame(answers_np, columns=[f'answer_{i}' for i in range(1, num_questions + 1)])
    series_key = pd.Series(key_np, name='correct_answer')
    
    return df_answers, series_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar benchmarks para diferentes modos de evaluación.")
    parser.add_argument("--num_students", type=int, default=1000,
                        help="Número de estudiantes para generar datos de prueba.")
    parser.add_argument("--num_questions", type=int, default=100,
                        help="Número de preguntas para generar datos de prueba.")
    
    args = parser.parse_args()

    # Cargar configuración de puntuación (o usar valores por defecto)
    scoring_config = load_scoring_config()
    scoring_rules = scoring_config.get('scoring', {"correct": 20.0, "wrong": -1.125, "blank": 0.0})

    # Crear datos de muestra
    students_df, key_series = create_sample_data(args.num_students, args.num_questions)
    
    # Ejecutar el benchmark completo usando la lógica centralizada
    run_full_benchmark(students_df, key_series, scoring_rules)
    
    # Generar el gráfico después de ejecutar el benchmark
    generate_benchmark_plot()