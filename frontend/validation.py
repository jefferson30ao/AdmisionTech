import pandas as pd
import numpy as np
import json
import os

def log_entry(log_file: str, level: str, message: str):
    """
    Registra un mensaje en un archivo JSONL con un nivel específico.
    También imprime el mensaje en la consola para depuración.

    Args:
        log_file (str): Ruta al archivo JSONL.
        level (str): Nivel del log (e.g., 'INFO', 'ERROR').
        message (str): Mensaje a registrar.
    """
    log_entry_dict = {'level': level, 'message': message}
    print(f"LOG ({level}): {message}") # Imprimir en consola para depuración
    try:
        with open(log_file, 'a') as f:
            json.dump(log_entry_dict, f)
            f.write('\n')
    except Exception as e:
        print(f"Error al escribir en el archivo de log {log_file}: {e}")

def log_error(log_file: str, message: str):
    log_entry(log_file, 'ERROR', message)

def log_info(log_file: str, message: str):
    log_entry(log_file, 'INFO', message)

def validate_and_load_responses(path: str) -> pd.DataFrame:
    """
    Valida DNI y respuestas de un archivo Excel, convierte respuestas a valores numéricos,
    registra errores en un archivo JSONL y retorna un DataFrame con las filas válidas.

    Args:
        path (str): Ruta al archivo Excel con las respuestas.

    Returns:
        pandas.DataFrame: DataFrame con las filas válidas.
    """
    log_file = "logs/validate_responses.jsonl"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        log_error(log_file, f"Error: Archivo no encontrado: {path}")
        return pd.DataFrame()
    except Exception as e:
        log_error(log_file, f"Error inesperado al leer Excel: {e}")
        return pd.DataFrame()

    log_info(log_file, f"DataFrame cargado. Filas iniciales: {len(df)}")

    # Convertir DNI a string para asegurar consistencia
    if 'DNI' not in df.columns:
        log_error(log_file, "Error de estructura: Columna 'DNI' no encontrada en el archivo de respuestas.")
        return pd.DataFrame()
    df['DNI'] = df['DNI'].astype(str)

    # Inicializar una columna para marcar filas válidas/inválidas
    df['is_valid'] = True

    # Validar DNI: longitud y dígitos
    invalid_dni_format_mask = ~df['DNI'].apply(lambda x: x.isdigit() and len(x) == 8)
    for index in df[invalid_dni_format_mask].index:
        log_error(log_file, f"Fila {index}: DNI inválido (formato o longitud): {df.loc[index, 'DNI']}")
        df.loc[index, 'is_valid'] = False

    # Identificar DNI duplicados y marcar todas sus ocurrencias como inválidas
    # Solo considerar DNI que no fueron ya invalidados por formato
    temp_df = df[df['is_valid']].copy()
    dni_counts = temp_df['DNI'].value_counts()
    duplicated_dnis = dni_counts[dni_counts > 1].index
    
    for dni in duplicated_dnis:
        indices = df[df['DNI'] == dni].index
        for index in indices:
            if df.loc[index, 'is_valid']: # Solo loguear si no fue ya invalidado por formato
                log_error(log_file, f"Fila {index}: DNI duplicado: {dni}")
            df.loc[index, 'is_valid'] = False

    # Validar respuestas
    for i in range(1, 101):
        columna = f'answer_{i}'
        if columna not in df.columns:
            log_error(log_file, f"Error de estructura: Columna '{columna}' no encontrada en el archivo de respuestas. Todas las filas serán marcadas como inválidas.")
            df['is_valid'] = False # Marcar todas las filas como inválidas si la estructura es incorrecta
            break # Salir del bucle de validación de respuestas

        # Convertir NaN a cadena vacía antes de la validación
        answers_series = df[columna].replace({np.nan: ''}).astype(str).str.upper()
        invalid_answer_mask = ~answers_series.isin(['A', 'B', 'C', 'D', ''])
        
        if invalid_answer_mask.any(): # Solo iterar si hay respuestas inválidas
            for index in df[invalid_answer_mask].index:
                if df.loc[index, 'is_valid']: # Solo loguear si no fue ya invalidado
                    log_error(log_file, f"Fila {index}, Columna {columna}: Respuesta inválida: {df.loc[index, columna]}")
                df.loc[index, 'is_valid'] = False
    
    # Filtrar filas válidas
    df_valid = df[df['is_valid']].copy()

    # Convertir respuestas a valores numéricos para las filas válidas
    conversion_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, '': -1}
    for i in range(1, 101):
        columna = f'answer_{i}'
        if columna in df_valid.columns: # Asegurarse de que la columna existe en el DataFrame válido
            df_valid[columna] = df_valid[columna].astype(str).str.upper().map(conversion_map)
    
    # Eliminar la columna 'is_valid' antes de retornar
    df_valid = df_valid.drop(columns=['is_valid'])

    print(f"Filas válidas antes de retornar: {len(df_valid)}") # Debugging
    return df_valid

def validate_and_load_answer_key(path: str) -> pd.Series:
    """
    Valida question_id y correct_answer de un archivo Excel, convierte respuestas a valores numéricos,
    registra errores en un archivo JSONL y retorna una Series indexada por question_id.

    Args:
        path (str): Ruta al archivo Excel con la clave de respuestas.

    Returns:
        pandas.Series: Series indexada por question_id con las respuestas correctas en formato numérico.
    """
    log_file = "logs/validate_answer_key.jsonl"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        log_error(log_file, f"Error: Archivo no encontrado: {path}")
        return pd.Series()
    except Exception as e:
        log_error(log_file, f"Error inesperado al leer Excel: {e}")
        return pd.Series()

    answer_key = {}
    
    question_id_anterior = 0
    
    for index, row in df.iterrows():
        # Asegurarse de que 'question_id' y 'correct_answer' existen
        if 'question_id' not in row or 'correct_answer' not in row:
            log_error(log_file, f"Fila {index}: Error de estructura, faltan columnas 'question_id' o 'correct_answer'.")
            continue

        try:
            question_id = int(row['question_id'])
        except ValueError:
            log_error(log_file, f"Fila {index}: question_id no es un número entero: {row['question_id']}")
            continue

        correct_answer = str(row['correct_answer']).upper()
        
        # Validar question_id
        if not (1 <= question_id <= 100) or question_id <= question_id_anterior:
            log_error(log_file, f"Fila {index}: question_id inválido o fuera de secuencia: {question_id}")
            continue
        
        # Validar correct_answer
        if correct_answer not in ('A', 'B', 'C', 'D'):
            log_error(log_file, f"Fila {index}: correct_answer inválida: {correct_answer}")
            continue
        
        # Convertir respuesta a valor numérico
        if correct_answer == 'A':
            answer_key[question_id] = 0
        elif correct_answer == 'B':
            answer_key[question_id] = 1
        elif correct_answer == 'C':
            answer_key[question_id] = 2
        elif correct_answer == 'D':
            answer_key[question_id] = 3
            
        question_id_anterior = question_id
    
    answer_key_series = pd.Series(answer_key)
    answer_key_series.index.name = 'question_id'
    return answer_key_series