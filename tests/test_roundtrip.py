import pandas as pd
import numpy as np # Añadido para np.random.choice
import os
import sys

# Añadir la raíz del proyecto a sys.path para que Python encuentre los módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.validation import validate_and_load_responses, validate_and_load_answer_key
from frontend.bridge import run_serial

def create_dummy_excel_files():
    """Crea archivos Excel dummy para respuestas y clave de respuestas."""
    # Crear archivo de respuestas dummy
    df_answers_data = {
        'DNI': [f'1234567{i:01d}' for i in range(10)],
    }
    for i in range(1, 101):
        df_answers_data[f'answer_{i}'] = np.random.choice(['A', 'B', 'C', 'D', ''], size=10)
    df_answers = pd.DataFrame(df_answers_data)
    df_answers.to_excel('data/dummy_responses.xlsx', index=False)

    # Crear archivo de clave de respuestas dummy
    df_key_data = {
        'question_id': list(range(1, 101)),
        'correct_answer': np.random.choice(['A', 'B', 'C', 'D'], size=100)
    }
    df_key = pd.DataFrame(df_key_data)
    df_key.to_excel('data/dummy_answer_key.xlsx', index=False)

def test_round_trip():
    """
    Testea el round-trip completo: carga Dataset -> puente -> CSV de salida.
    """
    # Asegurarse de que el directorio 'data' existe
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    # Crear archivos dummy si no existen
    create_dummy_excel_files()

    # Rutas de los archivos dummy
    responses_path = 'data/dummy_responses.xlsx'
    answer_key_path = 'data/dummy_answer_key.xlsx'
    output_csv_path = 'output/evaluation_results.csv'

    print(f"Cargando respuestas desde: {responses_path}")
    df_answers = validate_and_load_responses(responses_path)
    print(f"Respuestas cargadas. Filas válidas: {len(df_answers)}")

    print(f"Cargando clave de respuestas desde: {answer_key_path}")
    series_key = validate_and_load_answer_key(answer_key_path)
    print(f"Clave de respuestas cargada. Longitud: {len(series_key)}")

    if df_answers.empty or series_key.empty:
        print("No se pudieron cargar datos válidos. Saliendo del test.")
        return

    # Definir la regla de puntuación
    scoring_rule = {'correct': 1.0, 'wrong': -0.25, 'blank': 0.0}

    print("Ejecutando run_serial...")
    df_results = run_serial(df_answers, series_key, scoring_rule)
    print(f"Resultados de run_serial obtenidos. Filas: {len(df_results)}")

    # Añadir DNI a los resultados si df_answers tiene la columna 'DNI'
    if 'DNI' in df_answers.columns:
        df_results['DNI'] = df_answers['DNI'].reset_index(drop=True)
        # Reordenar columnas para que DNI sea la primera
        cols = ['DNI'] + [col for col in df_results.columns if col != 'DNI']
        df_results = df_results[cols]

    print(f"Guardando resultados en: {output_csv_path}")
    df_results.to_csv(output_csv_path, index=False)
    print("Test de round-trip completado exitosamente.")

import unittest
import pandas as pd
import numpy as np
import os
import sys

# Add the project root to sys.path so Python finds modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.validation import validate_and_load_responses, validate_and_load_answer_key
from frontend.bridge import run_serial, run_openmp  # Import run_openmp

def create_dummy_excel_files():
    """Creates dummy Excel files for responses and answer key."""
    # Create dummy responses file
    df_answers_data = {
        'DNI': [f'1234567{i:01d}' for i in range(10)],
    }
    for i in range(1, 101):
        df_answers_data[f'answer_{i}'] = np.random.choice(['A', 'B', 'C', 'D', ''], size=10)
    df_answers = pd.DataFrame(df_answers_data)
    df_answers.to_excel('data/dummy_responses.xlsx', index=False)

    # Create dummy answer key file
    df_key_data = {
        'question_id': list(range(1, 101)),
        'correct_answer': np.random.choice(['A', 'B', 'C', 'D'], size=100)
    }
    df_key = pd.DataFrame(df_key_data)
    df_key.to_excel('data/dummy_answer_key.xlsx', index=False)

def test_round_trip(mode="serial"):
    """
    Tests the complete round-trip: load Dataset -> bridge -> CSV output.
    """
    # Ensure the 'data' directory exists
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    # Create dummy files if they don't exist
    create_dummy_excel_files()

    # Paths to the dummy files
    responses_path = 'data/dummy_responses.xlsx'
    answer_key_path = 'data/dummy_answer_key.xlsx'
    output_csv_path = 'output/evaluation_results.csv'

    print(f"Loading responses from: {responses_path}")
    df_answers = validate_and_load_responses(responses_path)
    print(f"Responses loaded. Valid rows: {len(df_answers)}")

    print(f"Loading answer key from: {answer_key_path}")
    series_key = validate_and_load_answer_key(answer_key_path)
    print(f"Answer key loaded. Length: {len(series_key)}")

    if df_answers.empty or series_key.empty:
        print("Could not load valid data. Exiting test.")
        return

    # Define the scoring rule
    scoring_rule = {'correct': 1.0, 'wrong': -0.25, 'blank': 0.0}

    print(f"Executing run_{mode}...")
    if mode == "serial":
        df_results = run_serial(df_answers, series_key, scoring_rule)
    elif mode == "openmp":
        df_results = run_openmp(df_answers, series_key, scoring_rule)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    print(f"Results from run_{mode} obtained. Rows: {len(df_results)}")

    # Add DNI to the results if df_answers has the 'DNI' column
    if 'DNI' in df_answers.columns:
        df_results['DNI'] = df_answers['DNI'].reset_index(drop=True)
        # Reorder columns so DNI is the first
        cols = ['DNI'] + [col for col in df_results.columns if col != 'DNI']
        df_results = df_results[cols]

    print(f"Saving results to: {output_csv_path}")
    df_results.to_csv(output_csv_path, index=False)
    print("Round-trip test completed successfully.")

class TestEvalCore(unittest.TestCase):

    def test_scoring_rule(self):
        rule = pyevalcore.ScoringRule()
        rule.correct = 1
        rule.wrong = 0
        rule.blank = 0

        self.assertEqual(rule.correct, 1)
        self.assertEqual(rule.wrong, 0)
        self.assertEqual(rule.blank, 0)

    def test_result(self):
        result = pyevalcore.Result()
        result.score = 1
        result.correct = 2
        result.wrong = 3
        result.blank = 4

        self.assertEqual(result.score, 1)
        self.assertEqual(result.correct, 2)
        self.assertEqual(result.wrong, 3)
        self.assertEqual(result.blank, 4)

    def test_evaluate_serial(self):
        answers = np.array([[1, 2, 3, 4, 1], [1, 2, 3, 4, 1], [1, 2, 3, 4, 1]], dtype=np.int8)
        key = np.array([1, 2, 3, 4, 1], dtype=np.int8)
        rule = pyevalcore.ScoringRule()
        rule.correct = 1
        rule.wrong = 0
        rule.blank = 0

        results = pyevalcore.run_serial(answers, key, rule)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['correct'], 5)
        self.assertEqual(results[0]['wrong'], 0)
        self.assertEqual(results[0]['blank'], 0)
        self.assertEqual(results[0]['score'], 5)

        self.assertEqual(results[1]['correct'], 5)
        self.assertEqual(results[1]['wrong'], 0)
        self.assertEqual(results[1]['blank'], 0)
        self.assertEqual(results[1]['score'], 5)


        self.assertEqual(results[2]['correct'], 5)
        self.assertEqual(results[2]['wrong'], 0)
        self.assertEqual(results[2]['blank'], 0)
        self.assertEqual(results[2]['score'], 5)

    def test_evaluate_openmp(self):
        answers = np.array([[1, 2, 3, 4, 1], [1, 2, 3, 4, 1], [1, 2, 3, 4, 1]], dtype=np.int8)
        key = np.array([1, 2, 3, 4, 1], dtype=np.int8)
        rule = pyevalcore.ScoringRule()
        rule.correct = 1
        rule.wrong = 0
        rule.blank = 0

        results = pyevalcore.run_openmp(answers, key, rule)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['correct'], 5)
        self.assertEqual(results[0]['wrong'], 0)
        self.assertEqual(results[0]['blank'], 0)
        self.assertEqual(results[0]['score'], 5)

        self.assertEqual(results[1]['correct'], 5)
        self.assertEqual(results[1]['wrong'], 0)
        self.assertEqual(results[1]['blank'], 0)
        self.assertEqual(results[1]['score'], 5)


        self.assertEqual(results[2]['correct'], 5)
        self.assertEqual(results[2]['wrong'], 0)
        self.assertEqual(results[2]['blank'], 0)
        self.assertEqual(results[2]['score'], 5)

if __name__ == "__main__":
    #test_round_trip()
    unittest.main()