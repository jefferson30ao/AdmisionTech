import pandas as pd
import numpy as np
import pyevalcore

def run_serial(df_answers: pd.DataFrame, series_key: pd.Series, rule: dict) -> pd.DataFrame:
    """
    Ejecuta la evaluación de respuestas en modo serial utilizando la librería C++ a través de pybind11.

    Args:
        df_answers (pd.DataFrame): DataFrame con las respuestas de los estudiantes.
                                   Se espera que las columnas de respuestas sean 'answer_1' a 'answer_100'
                                   y contengan valores numéricos (0-3 para A-D, -1 para blanco).
        series_key (pd.Series): Serie con la clave de respuestas, indexada por question_id (1-100).
                                Se espera que contenga valores numéricos (0-3 para A-D).
        rule (dict): Diccionario con las reglas de puntuación:
                     {'correct': float, 'wrong': float, 'blank': float}.

    Returns:
        pd.DataFrame: DataFrame con los resultados de la evaluación para cada estudiante,
                      incluyendo 'score', 'correct', 'wrong', 'blank'.
    """
    # Convertir df_answers a un array de NumPy de int8_t
    # Asegurarse de que las columnas de respuestas estén en el orden correcto (answer_1 a answer_100)
    answer_cols = [f'answer_{i}' for i in range(1, 101)]
    answers_np = df_answers[answer_cols].values.astype(np.int8)

    # Convertir series_key a un array de NumPy de int8_t
    # Asegurarse de que la serie esté ordenada por índice (question_id)
    key_np = series_key.sort_index().values.astype(np.int8)

    # Crear una instancia de ScoringRule
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = rule.get('correct', 0.0)
    scoring_rule.wrong = rule.get('wrong', 0.0)
    scoring_rule.blank = rule.get('blank', 0.0)

    # Llamar a la función C++
    results_list = pyevalcore.run_serial(answers_np, key_np, scoring_rule)

    # Convertir la lista de diccionarios de resultados a un DataFrame de Pandas
    df_results = pd.DataFrame(results_list)

    return df_results

def run_openmp(df_answers: pd.DataFrame, series_key: pd.Series, rule: dict) -> pd.DataFrame:
    """
    Ejecuta la evaluación de respuestas en modo OpenMP utilizando la librería C++ a través de pybind11.

    Args:
        df_answers (pd.DataFrame): DataFrame con las respuestas de los estudiantes.
                                   Se espera que las columnas de respuestas sean 'answer_1' a 'answer_100'
                                   y contengan valores numéricos (0-3 para A-D, -1 para blanco).
        series_key (pd.Series): Serie con la clave de respuestas, indexada por question_id (1-100).
                                 Se espera que contenga valores numéricos (0-3 para A-D).
        rule (dict): Diccionario con las reglas de puntuación:
                     {'correct': float, 'wrong': float, 'blank': float}.

    Returns:
        pd.DataFrame: DataFrame con los resultados de la evaluación para cada estudiante,
                       incluyendo 'score', 'correct', 'wrong', 'blank'.
    """
    # Convertir df_answers a un array de NumPy de int8_t
    answer_cols = [f'answer_{i}' for i in range(1, 101)]
    answers_np = df_answers[answer_cols].values.astype(np.int8)

    # Convertir series_key a un array de NumPy de int8_t
    key_np = series_key.sort_index().values.astype(np.int8)

    # Crear una instancia de ScoringRule
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = rule.get('correct', 0.0)
    scoring_rule.wrong = rule.get('wrong', 0.0)
    scoring_rule.blank = rule.get('blank', 0.0)

    # Llamar a la función C++
    results_list = pyevalcore.run_openmp(answers_np, key_np, scoring_rule)

    # Convertir la lista de diccionarios de resultados a un DataFrame de Pandas
    df_results = pd.DataFrame(results_list)

    return df_results