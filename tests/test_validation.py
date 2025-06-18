import pytest
import pandas as pd
import json
import os
from frontend.validation import validate_and_load_responses, validate_and_load_answer_key

# Rutas a los archivos de prueba
RESPONSES_FILE = "data/respuestas_postulantes.xlsx"
ANSWER_KEY_FILE = "data/clave_respuestas.xlsx"
LOG_RESPONSES_FILE = "logs/validate_responses.jsonl"
LOG_ANSWER_KEY_FILE = "logs/validate_answer_key.jsonl"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """
    Fixture para limpiar los archivos de log antes de cada prueba.
    """
    os.makedirs(os.path.dirname(LOG_RESPONSES_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_ANSWER_KEY_FILE), exist_ok=True)
    if os.path.exists(LOG_RESPONSES_FILE):
        os.remove(LOG_RESPONSES_FILE)
    if os.path.exists(LOG_ANSWER_KEY_FILE):
        os.remove(LOG_ANSWER_KEY_FILE)
    yield
    # No es necesario limpiar después de la prueba para este caso,
    # ya que cada prueba limpia al inicio.

def test_validate_and_load_responses():
    """
    Verifica la funcionalidad de validate_and_load_responses.
    """
    # 1. Verificar que validate_and_load_responses retorna un DataFrame con 20 filas válidas.
    df_responses = validate_and_load_responses(RESPONSES_FILE)
    assert isinstance(df_responses, pd.DataFrame)
    assert len(df_responses) == 20, f"Se esperaban 20 filas válidas, pero se obtuvieron {len(df_responses)}"

    # 2. Verificar que se registran 2 errores en el archivo de log validate_responses.jsonl.
    with open(LOG_RESPONSES_FILE, 'r') as f:
        all_logs = [json.loads(line) for line in f]
        errors = [log for log in all_logs if log['level'] == 'ERROR']
    assert len(errors) == 2, f"Se esperaban 2 errores en el log, pero se encontraron {len(errors)}"
    
    # Opcional: Verificar el contenido de los errores si es necesario
    # assert "DNI inválido" in errors[0]['message']
    # assert "Respuesta inválida" in errors[1]['message']

def test_validate_and_load_answer_key():
    """
    Verifica que validate_and_load_answer_key carga correctamente la clave de respuestas.
    """
    answer_key = validate_and_load_answer_key(ANSWER_KEY_FILE)
    assert isinstance(answer_key, pd.Series)
    assert not answer_key.empty
    assert answer_key.index.name == 'question_id'
    assert len(answer_key) == 100 # Asumiendo 100 preguntas en la clave de respuestas
    
    # Verificar algunos valores esperados si se conoce la estructura de la clave
    # assert answer_key[1] == 0 # Ejemplo: pregunta 1, respuesta A (0)
    # assert answer_key[100] == 3 # Ejemplo: pregunta 100, respuesta D (3)