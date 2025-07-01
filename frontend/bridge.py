from fastapi import FastAPI, UploadFile, File, Form
from starlette.middleware.wsgi import WSGIMiddleware
import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table
import io
import pandas as pd
import numpy as np
import pyevalcore
import json
from frontend.utils.logger import Logger
from starlette.responses import FileResponse, StreamingResponse
import os
from datetime import datetime

app = FastAPI()
logger = Logger()
dash_app = Dash(__name__, requests_pathname_prefix='/dash/')
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.post("/upload")
async def upload_files(students_file: UploadFile = File(...), key_file: UploadFile = File(...)):
    try:
        students_content = await students_file.read()
        key_content = await key_file.read()

        app.state.students_df = pd.read_excel(io.BytesIO(students_content))
        app.state.key_df = pd.read_excel(io.BytesIO(key_content))
        logger.log("INFO", "file_upload", "Archivos cargados exitosamente.", extra={"students_file": students_file.filename, "key_file": key_file.filename})
        return {"status": "ok"}
    except Exception as e:
        logger.log("ERROR", "file_upload", f"Error al cargar archivos: {str(e)}", extra={"error_details": str(e)})
        return {"status": "error", "message": str(e)}

@app.post("/run")
async def run_evaluation(
    mode: str = Form(...),
):
    try:
        if not hasattr(app.state, 'students_df') or not hasattr(app.state, 'key_df'):
            logger.log("ERROR", "validation", "Archivos de estudiantes o clave no cargados.", extra={"rule_id": "RF-02"})
            return {"status": "error", "message": "Archivos de estudiantes o clave no cargados."}

        students_df = app.state.students_df
        key_df = app.state.key_df
        # Leer configuración de puntuación desde el archivo en cada ejecución
        scoring_config_current = load_scoring_config()
        chunk_size = scoring_config_current.get('chunk_size', 0)
        scoring_rules = scoring_config_current.get('scoring', {"correct": 0.0, "wrong": 0.0, "blank": 0.0})

        if chunk_size > 0:
            all_results_list = []
            num_students = len(students_df)
            for i in range(0, num_students, chunk_size):
                chunk_df = students_df.iloc[i:i + chunk_size]
                if mode == "serial":
                    chunk_results_df = run_serial(chunk_df, key_df['correct_answer'], scoring_rules)
                elif mode == "openmp":
                    chunk_results_df = run_openmp(chunk_df, key_df['correct_answer'], scoring_rules)
                elif mode == "cuda":
                    chunk_results_df = run_cuda(chunk_df, key_df['correct_answer'], scoring_rules)
                elif mode == "pthreads":
                    chunk_results_df = run_pthreads(chunk_df, key_df['correct_answer'], scoring_rules)
                else:
                    logger.log("ERROR", "validation", f"Modo de ejecución no válido: {mode}", extra={"rule_id": "RF-02", "mode_attempted": mode})
                    return {"status": "error", "message": "Modo de ejecución no válido."}
                all_results_list.append(chunk_results_df)

            results_df = pd.concat(all_results_list, ignore_index=True)
        else:
            if mode == "serial":
                results_df = run_serial(students_df, key_df['correct_answer'], scoring_rules)
            elif mode == "openmp":
                results_df = run_openmp(students_df, key_df['correct_answer'], scoring_rules)
            elif mode == "cuda":
                results_df = run_cuda(students_df, key_df['correct_answer'], scoring_rules)
            elif mode == "pthreads":
                results_df = run_pthreads(students_df, key_df['correct_answer'], scoring_rules)
            else:
                logger.log("ERROR", "validation", f"Modo de ejecución no válido: {mode}", extra={"rule_id": "RF-02", "mode_attempted": mode})
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
        logger.log("INFO", "execution", "Evaluación completada exitosamente.", extra={"mode": mode, "metrics": metrics, "rule_ids": ["RF-05", "RF-08"]})
        return {"status": "ok", "results": results_json, "metrics": metrics}
    except Exception as e:
        logger.log("ERROR", "execution", f"Error durante la evaluación: {str(e)}", extra={"error_details": str(e), "rule_id": "RF-08"})
        return {"status": "error", "message": str(e)}

@app.get("/logs/list")
async def list_logs():
    log_dir = "logs"
    dates = []
    files_by_date = {}

    if not os.path.exists(log_dir):
        return {"dates": dates, "files": files_by_date}

    for date_dir in os.listdir(log_dir):
        full_date_path = os.path.join(log_dir, date_dir)
        if os.path.isdir(full_date_path):
            try:
                # Validate date format (YYYY-MM-DD)
                datetime.strptime(date_dir, "%Y-%m-%d")
                dates.append(date_dir)
                files_by_date[date_dir] = []
                for log_file in os.listdir(full_date_path):
                    if log_file.endswith(".jsonl"):
                        files_by_date[date_dir].append(log_file)
                files_by_date[date_dir].sort()
            except ValueError:
                # Ignore directories that are not in YYYY-MM-DD format
                continue
    dates.sort(reverse=True) # Sort dates in descending order
    return {"dates": dates, "files": files_by_date}

@app.get("/logs/download/{date}/{filename}")
async def download_log(date: str, filename: str, format: str = None):
    log_filepath = os.path.join("logs", date, filename)

    if not os.path.exists(log_filepath):
        logger.log("ERROR", "log_download", f"Archivo de log no encontrado: {log_filepath}", extra={"date": date, "filename": filename})
        return {"status": "error", "message": "Archivo no encontrado."}, 404
    
    if format == "csv":
        try:
            records = []
            with open(log_filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    records.append(json.loads(line))
            
            if not records:
                return StreamingResponse(io.StringIO(""), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename.replace('.jsonl', '.csv')}"})

            df = pd.DataFrame.from_records(records)
            
            # Flatten 'extra' column if it exists and contains dictionaries
            if 'extra' in df.columns and any(isinstance(x, dict) for x in df['extra'].dropna()):
                extra_df = pd.json_normalize(df['extra'])
                df = pd.concat([df.drop(columns=['extra']), extra_df], axis=1)

            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            logger.log("INFO", "log_download", f"Log convertido y descargado como CSV: {log_filepath}", extra={"date": date, "filename": filename, "format": "csv"})
            return StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename.replace('.jsonl', '.csv')}"})
        except Exception as e:
            logger.log("ERROR", "log_download", f"Error al convertir log a CSV: {log_filepath} - {str(e)}", extra={"date": date, "filename": filename, "error_details": str(e)})
            return {"status": "error", "message": f"Error al convertir a CSV: {str(e)}"}, 500
    else:
        logger.log("INFO", "log_download", f"Log descargado: {log_filepath}", extra={"date": date, "filename": filename})
        return FileResponse(log_filepath, media_type="application/jsonl", filename=filename)
@app.get("/benchmark/data")
async def get_benchmark_data():
    try:
        df = pd.read_csv("data/benchmark.csv")
        return {"status": "ok", "data": df.to_dict(orient='records')}
    except FileNotFoundError:
        logger.log("ERROR", "benchmark_data", "Archivo data/benchmark.csv no encontrado.")
        return {"status": "error", "message": "Archivo data/benchmark.csv no encontrado."}, 404
    except Exception as e:
        logger.log("ERROR", "benchmark_data", f"Error al leer benchmark.csv: {str(e)}")
        return {"status": "error", "message": f"Error al leer benchmark.csv: {str(e)}"}, 500

@app.get("/output/benchmark_plot.html")
async def get_benchmark_plot():
    plot_path = "output/benchmark_plot.html"
    if not os.path.exists(plot_path):
        logger.log("ERROR", "benchmark_plot", f"Archivo {plot_path} no encontrado.")
        return {"status": "error", "message": f"Archivo {plot_path} no encontrado."}, 404
    return FileResponse(plot_path, media_type="text/html")


# Cargar configuración inicial desde scoring.json
def load_scoring_config():
    try:
        with open("data/scoring.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
          "chunk_size": 0,
          "scoring": {
            "correct": 20.0,
            "wrong": -1.125,
            "blank": 0.0
          }
        }

scoring_config = load_scoring_config()

try:
    cuda_available = (pyevalcore.get_device_count() > 0)
except Exception:
    cuda_available = False

dash_app.layout = html.Div([
    html.H1("Sistema de Evaluación de Exámenes"),

    dcc.Tabs(id="tabs-main", value='tab-evaluation', children=[
        dcc.Tab(label='Evaluación', value='tab-evaluation', children=[
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
                            {'label': 'OpenMP', 'value': 'openmp'},
                            {'label': 'Pthreads', 'value': 'pthreads'},
                            {'label': 'CUDA', 'value': 'cuda', 'disabled': not cuda_available}
                        ],
                        value='serial',
                        inline=True,
                        style={'margin-bottom': '10px'}
                    ),
                ]),
                html.Div([
                    html.Label("Puntuación Correcta:"),
                    dcc.Input(id='score-correct', type='number', value=scoring_config['scoring']['correct'], style={'margin-right': '10px'}),
                    html.Label("Puntuación Incorrecta:"),
                    dcc.Input(id='score-wrong', type='number', value=scoring_config['scoring']['wrong'], style={'margin-right': '10px'}),
                    html.Label("Puntuación en Blanco:"),
                    dcc.Input(id='score-blank', type='number', value=scoring_config['scoring']['blank']),
                ]),
                html.Button('Iniciar Evaluación', id='run-button', n_clicks=0, style={'margin-top': '20px'}),
                html.Button('Configuración Avanzada', id='open-config-modal', n_clicks=0, style={'margin-top': '20px', 'margin-left': '10px'}),
                html.Div(id='output-run-status'),
            ]),

            dcc.Store(id='scoring-config-store', data=scoring_config), # Almacenar la configuración actual

            # Modal de Configuración Avanzada
            dcc.ConfirmDialog(
                id='config-modal',
                message='',
                displayed=False,
            ),
            html.Div(id='modal-content', children=[
                html.H3("Configuración Avanzada"),
                html.Div([
                    html.Label("Chunk Size:"),
                    dcc.Input(id='modal-chunk-size', type='number', value=scoring_config['chunk_size']),
                ]),
                html.Div([
                    html.H4("Reglas de Puntuación"),
                    html.Label("Correctas:"),
                    dcc.Input(id='modal-score-correct', type='number', value=scoring_config['scoring']['correct']),
                    html.Label("Incorrectas:"),
                    dcc.Input(id='modal-score-wrong', type='number', value=scoring_config['scoring']['wrong']),
                    html.Label("En Blanco:"),
                    dcc.Input(id='modal-score-blank', type='number', value=scoring_config['scoring']['blank']),
                ]),
                html.Button('Guardar Configuración', id='save-config-button', n_clicks=0),
                html.Button('Cerrar', id='close-config-modal', n_clicks=0),
                html.Div(id='config-save-status')
            ], style={'display': 'none', 'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '20px', 'border': '1px solid #ccc', 'zIndex': '1000'}),

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
        ]),
        dcc.Tab(label='Historial', value='tab-history', children=[
            html.Div([
                html.H3("Historial de Logs"),
                html.Div([
                    html.Label("Seleccionar Fecha:"),
                    dcc.Dropdown(
                        id='log-date-dropdown',
                        options=[],
                        placeholder="Selecciona una fecha",
                        style={'width': '50%'}
                    ),
                ]),
                html.Div([
                    html.Label("Archivos de Log:"),
                    dash_table.DataTable(
                        id='log-files-table',
                        columns=[
                            {"name": "Archivo", "id": "filename"},
                            {"name": "Descargar JSONL", "id": "download_jsonl", "presentation": "markdown"},
                            {"name": "Descargar CSV", "id": "download_csv", "presentation": "markdown"},
                        ],
                        data=[],
                        page_size=10,
                        style_table={'overflowX': 'auto', 'margin-top': '10px'},
                        style_cell={'textAlign': 'left', 'padding': '5px'},
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    ),
                    html.Div(id='log-history-status'),
                ])
            ])
        ]),
        dcc.Tab(label='Benchmarking', value='tab-benchmarking', children=[
            html.Div([
                html.H3("Resultados de Benchmarking"),
                dash_table.DataTable(
                    id='benchmark-table',
                    columns=[{"name": i, "id": i} for i in ["Modo", "Tiempo (ms)", "Speed-up"]], # Columnas iniciales
                    data=[],
                    page_size=10,
                    style_table={'overflowX': 'auto', 'margin-top': '10px'},
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                ),
                html.H3("Gráfico de Speed-up"),
                html.Iframe(
                    id='benchmark-plot-iframe',
                    src='/output/benchmark_plot.html', # La ruta al archivo HTML del gráfico
                    style={"height": "600px", "width": "100%", "border": "none"}
                )
            ])
        ])
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
)
def run_evaluation_callback(n_clicks, mode):
    if n_clicks > 0:
        try:
            import requests
            data = {
                'mode': mode
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


@dash_app.callback(
    Output('config-modal', 'displayed'),
    Output('modal-content', 'style'),
    Output('modal-chunk-size', 'value'),
    Output('modal-score-correct', 'value'),
    Output('modal-score-wrong', 'value'),
    Output('modal-score-blank', 'value'),
    Input('open-config-modal', 'n_clicks'),
    Input('close-config-modal', 'n_clicks'),
    State('scoring-config-store', 'data')
)
def toggle_config_modal(open_clicks, close_clicks, current_config):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'open-config-modal' and open_clicks > 0:
        return True, {'display': 'block', 'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '20px', 'border': '1px solid #ccc', 'zIndex': '1000'}, \
               current_config['chunk_size'], current_config['scoring']['correct'], current_config['scoring']['wrong'], current_config['scoring']['blank']
    elif button_id == 'close-config-modal' and close_clicks > 0:
        return False, {'display': 'none'}, \
               current_config['chunk_size'], current_config['scoring']['correct'], current_config['scoring']['wrong'], current_config['scoring']['blank']
    
    raise dash.exceptions.PreventUpdate


@dash_app.callback(
    Output('config-save-status', 'children'),
    Output('scoring-config-store', 'data'),
    Output('score-correct', 'value'),
    Output('score-wrong', 'value'),
    Output('score-blank', 'value'),
    Input('save-config-button', 'n_clicks'),
    State('modal-chunk-size', 'value'),
    State('modal-score-correct', 'value'),
    State('modal-score-wrong', 'value'),
    State('modal-score-blank', 'value')
)
def save_config(n_clicks, chunk_size, correct, wrong, blank):
    if n_clicks > 0:
        updated_config = {
            "chunk_size": chunk_size,
            "scoring": {
                "correct": correct,
                "wrong": wrong,
                "blank": blank
            }
        }
        try:
            with open("data/scoring.json", "w") as f:
                json.dump(updated_config, f, indent=2)
            return html.Div("Configuración guardada exitosamente.", style={'color': 'green'}), \
                   updated_config, correct, wrong, blank
        except Exception as e:
            return html.Div(f"Error al guardar la configuración: {str(e)}", style={'color': 'red'}), \
                   dash.no_update, dash.no_update, dash.no_update, dash.no_update
    return "", dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Callbacks para la pestaña de Historial de Logs
@dash_app.callback(
    Output('log-date-dropdown', 'options'),
    Output('log-date-dropdown', 'value'),
    Input('tabs-main', 'value')
)
def load_log_dates(tab_value):
    if tab_value == 'tab-history':
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/logs/list")
            response_data = response.json()
            dates = response_data.get("dates", [])
            options = [{'label': date, 'value': date} for date in dates]
            return options, dates[0] if dates else None
        except Exception as e:
            print(f"Error al cargar fechas de logs: {e}")
            return [], None
    return dash.no_update, dash.no_update

@dash_app.callback(
    Output('log-files-table', 'data'),
    Output('log-history-status', 'children'),
    Input('log-date-dropdown', 'value')
)
def update_log_files_table(selected_date):
    if selected_date:
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/logs/list")
            response_data = response.json()
            files_by_date = response_data.get("files", {})
            log_files = files_by_date.get(selected_date, [])
            
            data = []
            for filename in log_files:
                # Generar URLs para descarga
                download_jsonl_url = f"http://127.0.0.1:8000/logs/download/{selected_date}/{filename}"
                download_csv_url = f"http://127.0.0.1:8000/logs/download/{selected_date}/{filename}?format=csv"
                
                data.append({
                    "filename": filename,
                    "download_jsonl": f"[Descargar JSONL]({download_jsonl_url})",
                    "download_csv": f"[Descargar CSV]({download_csv_url})"
                })
            
            if not data:
                return [], html.Div("No hay archivos de log para la fecha seleccionada.")
            return data, ""
        except Exception as e:
            return [], html.Div(f"Error al cargar archivos de log: {str(e)}", style={'color': 'red'})
    return [], html.Div("Seleccione una fecha para ver los archivos de log.")

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
@dash_app.callback(
    Output('benchmark-table', 'data'),
    Input('tabs-main', 'value')
)
def load_benchmark_data(tab_value):
    if tab_value == 'tab-benchmarking':
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/benchmark/data")
            response_data = response.json()
            if response_data.get("status") == "ok":
                return response_data.get("data", [])
            else:
                print(f"Error al cargar datos de benchmarking: {response_data.get('message', 'Error desconocido')}")
                return []
        except Exception as e:
            print(f"Error en el procesamiento de carga de datos de benchmarking: {str(e)}")
            return []
    return dash.no_update
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
