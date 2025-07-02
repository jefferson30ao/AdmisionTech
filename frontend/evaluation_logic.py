import pandas as pd
import numpy as np
import pyevalcore

def run_serial(df_answers: pd.DataFrame, series_key: pd.Series, rule: dict) -> pd.DataFrame:
    """
    Ejecuta la evaluación de respuestas en modo serial utilizando la librería C++ a través de pybind11.

    Args:
        df_answers (pd.DataFrame): DataFrame con las respuestas de los estudiantes.
                                   Se espera que las columnas de respuestas sean 'answer_1' a 'answer_100'
                                   y contengan valores de cadena (A-D) o NaN.
        series_key (pd.Series): Serie con la clave de respuestas, indexada por question_id (1-100).
                                 Se espera que contenga valores de cadena (A-D) o NaN.
        rule (dict): Diccionario con las reglas de puntuación:
                     {'correct': float, 'wrong': float, 'blank': float}.

    Returns:
        pd.DataFrame: DataFrame con los resultados de la evaluación para cada estudiante,
                      incluyendo 'score', 'correct', 'wrong', 'blank'.
    """
    # Asegurar orden de columnas de respuestas
    answer_cols = [f'answer_{i}' for i in range(1, 101)]
    # Mapeo de respuestas A-D a valores -1 a 3
    mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    # Limpiar y convertir respuestas de estudiantes a valores numéricos (-1 inválido)
    df_clean = df_answers[answer_cols].fillna('').astype(str).apply(lambda col: col.str.strip().str.upper())
    df_mapped = df_clean.apply(lambda col: col.map(mapping).fillna(-1).astype(np.int8))
    answers_np = df_mapped.to_numpy()

    # Convertir clave de respuestas a valores numéricos (-1 inválido)
    key_series = series_key.sort_index().fillna('').astype(str).str.strip().str.upper()
    key_np = key_series.map(lambda v: mapping.get(v, -1)).astype(np.int8).to_numpy()

    # Crear instancia de ScoringRule
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = rule.get('correct', 0.0)
    scoring_rule.wrong = rule.get('wrong', 0.0)
    scoring_rule.blank = rule.get('blank', 0.0)

    # Llamar a la función C++
    results_list = pyevalcore.run_serial(answers_np, key_np, scoring_rule)
    df_results = pd.DataFrame(results_list)
    # Añadir columna student_id desde el DataFrame original
    if 'student_id' in df_answers.columns:
        df_results.insert(0, 'student_id', df_answers['student_id'].values)
    else:
        df_results.insert(0, 'student_id', df_results.index)
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
    # Normalizar respuestas de estudiantes y mapear a valores numéricos (-1 inválido)
    df_clean = df_answers[answer_cols].fillna('').astype(str).apply(lambda col: col.str.strip().str.upper())
    mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    df_mapped = df_clean.apply(lambda col: col.map(mapping).fillna(-1).astype(np.int8))
    answers_np = df_mapped.to_numpy()

    # Convertir series_key a valores numéricos (A-D map a 0-3, inválido -1)
    key_clean = series_key.sort_index().astype(str).str.strip().str.upper().map(mapping).fillna(-1).astype(np.int8)
    key_np = key_clean.values

    # Crear una instancia de ScoringRule
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = rule.get('correct', 0.0)
    scoring_rule.wrong = rule.get('wrong', 0.0)
    scoring_rule.blank = rule.get('blank', 0.0)

    # Llamar a la función C++
    results_list = pyevalcore.run_openmp(answers_np, key_np, scoring_rule)

    # Convertir la lista de diccionarios de resultados a un DataFrame de Pandas
    df_results = pd.DataFrame(results_list)
    # Añadir columna student_id desde el DataFrame original
    if 'student_id' in df_answers.columns:
        df_results.insert(0, 'student_id', df_answers['student_id'].values)
    else:
        df_results.insert(0, 'student_id', df_results.index)
    return df_results

def run_cuda(df_answers: pd.DataFrame, series_key: pd.Series, rule: dict) -> pd.DataFrame:
   """
   Ejecuta la evaluación de respuestas en modo CUDA utilizando la librería C++ a través de pybind11.

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
   # Normalizar respuestas de estudiantes y mapear a valores numéricos (-1 inválido)
   df_clean = df_answers[answer_cols].fillna('').astype(str).apply(lambda col: col.str.strip().str.upper())
   mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
   df_mapped = df_clean.apply(lambda col: col.map(mapping).fillna(-1).astype(np.int8))
   answers_np = df_mapped.to_numpy()

   # Convertir series_key a valores numéricos (A-D map a 0-3, inválido -1)
   key_clean = series_key.sort_index().astype(str).str.strip().str.upper().map(mapping).fillna(-1).astype(np.int8)
   key_np = key_clean.values

   # Crear una instancia de ScoringRule
   scoring_rule = pyevalcore.ScoringRule()
   scoring_rule.correct = rule.get('correct', 0.0)
   scoring_rule.wrong = rule.get('wrong', 0.0)
   scoring_rule.blank = rule.get('blank', 0.0)

   # Llamar a la función C++
   results_list = pyevalcore.run_cuda(answers_np, key_np, scoring_rule)

   # Convertir la lista de diccionarios de resultados a un DataFrame de Pandas
   df_results = pd.DataFrame(results_list)
   # Añadir columna student_id desde el DataFrame original
   if 'student_id' in df_answers.columns:
       df_results.insert(0, 'student_id', df_answers['student_id'].values)
   else:
       df_results.insert(0, 'student_id', df_results.index)
   return df_results

def run_pthreads(df_answers: pd.DataFrame, series_key: pd.Series, rule: dict) -> pd.DataFrame:
   """
   Ejecuta la evaluación de respuestas en modo Pthreads utilizando la librería C++ a través de pybind11.

   Args:
       df_answers (pd.DataFrame): DataFrame con las respuestas de los estudiantes.
       series_key (pd.Series): Serie con la clave de respuestas.
       rule (dict): Diccionario con las reglas de puntuación.

   Returns:
       pd.DataFrame: DataFrame con los resultados de la evaluación.
   """
   answer_cols = [f'answer_{i}' for i in range(1, 101)]
   df_clean = df_answers[answer_cols].fillna('').astype(str).apply(lambda col: col.str.strip().str.upper())
   mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
   df_mapped = df_clean.apply(lambda col: col.map(mapping).fillna(-1).astype(np.int8))
   answers_np = df_mapped.to_numpy()

   key_clean = series_key.sort_index().astype(str).str.strip().str.upper().map(mapping).fillna(-1).astype(np.int8)
   key_np = key_clean.values

   scoring_rule = pyevalcore.ScoringRule()
   scoring_rule.correct = rule.get('correct', 0.0)
   scoring_rule.wrong = rule.get('wrong', 0.0)
   scoring_rule.blank = rule.get('blank', 0.0)

   results_list = pyevalcore.run_pthreads(answers_np, key_np, scoring_rule)

   df_results = pd.DataFrame(results_list)
   if 'student_id' in df_answers.columns:
       df_results.insert(0, 'student_id', df_answers['student_id'].values)
   else:
       df_results.insert(0, 'student_id', df_results.index)
   return df_results