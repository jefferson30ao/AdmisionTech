from fastapi import FastAPI, UploadFile, File, Form
from starlette.middleware.wsgi import WSGIMiddleware
from dash import Dash, html, dcc, Input, Output, State, dash_table
import io
import pandas as pd
import numpy as np
import pyevalcore

app = FastAPI()
dash_app = Dash(__name__, requests_pathname_prefix='/dash/')
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.post("/upload")
async def upload_files(students_file: UploadFile = File(...), key_file: UploadFile = File(...)):
    try:
        students_content = await students_file.read()
        key_content = await key_file.read()

        app.state.students_df = pd.read_excel(io.BytesIO(students_content))
        app.state.key_df = pd.read_excel(io.BytesIO(key_content))

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/run")
async def run_evaluation(
    mode: str = Form(...),
    correct: float = Form(...),
    wrong: float = Form(...),
    blank: float = Form(...)
):
    try:
        if not hasattr(app.state, 'students_df') or not hasattr(app.state, 'key_df'):
            return {"status": "error", "message": "Archivos de estudiantes o clave no cargados."}

        students_df = app.state.students_df
        key_df = app.state.key_df
        rule = {"correct": correct, "wrong": wrong, "blank": blank}

        if mode == "serial":
            results_df = run_serial(students_df, key_df['correct_answer'], rule)
        elif mode == "openmp":
            results_df = run_openmp(students_df, key_df['correct_answer'], rule)
        else:
            return {"status": "error", "message": "Modo de ejecución no válido."}

        # Convertir resultados a formato JSON para la respuesta
        results_json = results_df.to_dict(orient='records')
        metrics = {
            "total_students": len(results_df),
            "average_score": results_df['score'].mean(),
            "average_correct": results_df['correct'].mean(),
            "average_wrong": results_df['wrong'].mean(),
            "average_blank": results_df['blank'].mean(),
        }

        return {"status": "ok", "results": results_json, "metrics": metrics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

dash_app.layout = html.Div([
    html.H1("Sistema de Evaluación de Exámenes"),

    html.Div([
        html.H3("Cargar Archivos"),
        dcc.Upload(
            id='upload-students-data',
            children=html.Div(['Arrastra y suelta o ', html.A('Selecciona Archivo de Estudiantes')]),
            style={
                'width': '50%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
            multiple=False
        ),
        dcc.Upload(
            id='upload-key-data',
            children=html.Div(['Arrastra y suelta o ', html.A('Selecciona Archivo de Clave')]),
            style={
                'width': '50%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
            multiple=False
        ),
        html.Div(id='output-upload-status'),
    ]),

    html.Div([
        html.H3("Configuración de Evaluación"),
        html.Div([
            html.Label("Modo de Ejecución:"),
            dcc.RadioItems(
                id='mode-selector',
                options=[
                    {'label': 'Serial', 'value': 'serial'},
                    {'label': 'OpenMP', 'value': 'openmp'}
                ],
                value='serial',
                inline=True,
                style={'margin-bottom': '10px'}
            ),
        ]),
        html.Div([
            html.Label("Puntuación Correcta:"),
            dcc.Input(id='score-correct', type='number', value=1.0, style={'margin-right': '10px'}),
            html.Label("Puntuación Incorrecta:"),
            dcc.Input(id='score-wrong', type='number', value=-0.25, style={'margin-right': '10px'}),
            html.Label("Puntuación en Blanco:"),
            dcc.Input(id='score-blank', type='number', value=0.0),
        ]),
        html.Button('Iniciar Evaluación', id='run-button', n_clicks=0, style={'margin-top': '20px'}),
        html.Div(id='output-run-status'),
    ]),

    html.Div([
        html.H3("Resultados de la Evaluación"),
        dash_table.DataTable(
            id='results-table',
            columns=[
                {"name": "ID Estudiante", "id": "student_id"},
                {"name": "Puntuación", "id": "score"},
                {"name": "Correctas", "id": "correct"},
                {"name": "Incorrectas", "id": "wrong"},
                {"name": "Blancas", "id": "blank"},
            ],
            data=[],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        ),
        html.Div(id='metrics-output', style={'margin-top': '20px'}),
        dcc.Graph(id='score-histogram'),
    ])
])

@dash_app.callback(
    Output('output-upload-status', 'children'),
    Input('upload-students-data', 'contents'),
    Input('upload-key-data', 'contents'),
    State('upload-students-data', 'filename'),
    State('upload-key-data', 'filename')
)
def upload_data(students_contents, key_contents, students_filename, key_filename):
    if students_contents is not None and key_contents is not None:
        try:
            # Decodificar y enviar al endpoint de FastAPI
            students_decoded = students_contents.encode('utf8').split(b';base64,')[1]
            key_decoded = key_contents.encode('utf8').split(b';base64,')[1]

            import base64
            students_bytes = base64.b64decode(students_decoded)
            key_bytes = base64.b64decode(key_decoded)

            import requests
            files = {
                'students_file': (students_filename, students_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                'key_file': (key_filename, key_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            response = requests.post("http://127.0.0.1:8000/upload", files=files)
            response_data = response.json()

            if response_data.get("status") == "ok":
                return html.Div(f"Archivos '{students_filename}' y '{key_filename}' cargados exitosamente.")
            else:
                return html.Div(f"Error al cargar archivos: {response_data.get('message', 'Error desconocido')}", style={'color': 'red'})
        except Exception as e:
            return html.Div(f"Error en el procesamiento de carga: {str(e)}", style={'color': 'red'})
    return html.Div("Cargue ambos archivos para continuar.")

@dash_app.callback(
    Output('results-table', 'data'),
    Output('metrics-output', 'children'),
    Output('score-histogram', 'figure'),
    Output('output-run-status', 'children'),
    Input('run-button', 'n_clicks'),
    State('mode-selector', 'value'),
    State('score-correct', 'value'),
    State('score-wrong', 'value'),
    State('score-blank', 'value')
)
def run_evaluation_callback(n_clicks, mode, correct, wrong, blank):
    if n_clicks > 0:
        try:
            import requests
            data = {
                'mode': mode,
                'correct': correct,
                'wrong': wrong,
                'blank': blank
            }
            response = requests.post("http://127.0.0.1:8000/run", data=data)
            response_data = response.json()

            if response_data.get("status") == "ok":
                results = response_data.get("results", [])
                metrics = response_data.get("metrics", {})

                metrics_display = html.Div([
                    html.P(f"Total de Estudiantes: {metrics.get('total_students')}"),
                    html.P(f"Puntuación Promedio: {metrics.get('average_score'):.2f}"),
                    html.P(f"Respuestas Correctas Promedio: {metrics.get('average_correct'):.2f}"),
                    html.P(f"Respuestas Incorrectas Promedio: {metrics.get('average_wrong'):.2f}"),
                    html.P(f"Respuestas en Blanco Promedio: {metrics.get('average_blank'):.2f}"),
                ])

                import plotly.express as px
                scores = [res['score'] for res in results]
                if scores:
                    fig = px.histogram(x=scores, nbins=20, title="Distribución de Puntuaciones")
                else:
                    fig = {} # Empty figure if no data

                return results, metrics_display, fig, html.Div("Evaluación completada exitosamente.")
            else:
                return [], html.Div(), {}, html.Div(f"Error en la evaluación: {response_data.get('message', 'Error desconocido')}", style={'color': 'red'})
        except Exception as e:
            return [], html.Div(), {}, html.Div(f"Error en el procesamiento de evaluación: {str(e)}", style={'color': 'red'})
    return [], html.Div(), {}, html.Div("Presione 'Iniciar Evaluación' para ver los resultados.")

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