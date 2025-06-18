import pandas as pd
import numpy as np
import random

def create_respuestas_postulantes(num_validas=20, num_invalidas=2):
    """Crea un DataFrame con respuestas de postulantes."""
    data = []
    dnis_generados = set()
    # Filas válidas
    for i in range(num_validas):
        dni = str(random.randint(10000000, 99999999))
        while dni in dnis_generados: # Asegurar DNI único
            dni = str(random.randint(10000000, 99999999))
        dnis_generados.add(dni)
        respuestas = [random.choice(['A', 'B', 'C', 'D', '']) for _ in range(100)]  # 100 respuestas A/B/C/D o vacías
        data.append([dni] + respuestas)

    # Filas inválidas
    # DNI de 7 dígitos
    dni_invalido_1 = str(random.randint(1000000, 9999999)).zfill(8)
    respuestas_invalidas_1 = [random.choice(['A', 'B', 'C', 'D', '']) for _ in range(100)]
    data.append([dni_invalido_1] + respuestas_invalidas_1)

    # Respuesta 'X'
    dni_invalido_2 = str(random.randint(10000000, 99999999))
    respuestas_invalidas_2 = [random.choice(['A', 'B', 'C', 'D', '']) for _ in range(100)]
    respuestas_invalidas_2[random.randint(0, 99)] = 'X'
    data.append([dni_invalido_2] + respuestas_invalidas_2)

    df = pd.DataFrame(data, columns=['DNI'] + [f'answer_{i+1}' for i in range(100)])
    return df

def create_clave_respuestas(num_preguntas=100):
    """Crea un DataFrame con la clave de respuestas."""
    data = []
    for i in range(num_preguntas):
        correct_answer = random.choice(['A', 'B', 'C', 'D'])
        data.append([i+1, correct_answer])
    df = pd.DataFrame(data, columns=['question_id', 'correct_answer'])
    return df

# Crear y exportar los DataFrames
respuestas_df = create_respuestas_postulantes()
clave_df = create_clave_respuestas()

respuestas_df.to_excel('data/respuestas_postulantes.xlsx', index=False)
clave_df.to_excel('data/clave_respuestas.xlsx', index=False)

print("Columnas de respuestas_postulantes.xlsx:", respuestas_df.columns.tolist())
print("Datasets de prueba creados exitosamente en la carpeta 'data/'.")