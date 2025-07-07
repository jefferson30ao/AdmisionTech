import dash
from dash import html, dcc, Input, Output, State, callback_context
import requests
import base64
import io
import pandas as pd
import plotly.express as px
import time
import json # Importar json para la función save_config
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# Importar load_scoring_config para asegurar que esté disponible
from frontend.config_utils import load_scoring_config
from frontend.dash_layout import content_evaluacion, content_historial, content_configuracion, content_ayuda, content_benchmarking, nav_items

# Callbacks para la pestaña de Evaluación
def setup_dash_callbacks(dash_app):
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
                students_decoded = students_contents.encode('utf8').split(b';base64,')[1]
                key_decoded = key_contents.encode('utf8').split(b';base64,')[1]

                students_bytes = base64.b64decode(students_decoded)
                key_bytes = base64.b64decode(key_decoded)

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

                    # Convertir resultados a DataFrame para manipulación
                    df_results = pd.DataFrame(results)

                    # Añadir columna 'ID' como índice + 1
                    df_results.insert(0, 'ID', range(1, 1 + len(df_results)))

                    # Renombrar 'student_id' a 'DNI'
                    df_results.rename(columns={'student_id': 'DNI'}, inplace=True)

                    # Reordenar columnas para que DNI esté después de ID
                    # Asegurarse de que todas las columnas esperadas estén presentes antes de reordenar
                    # Lista de columnas esperadas en el orden deseado
                    ordered_columns = ['ID', 'DNI', 'score', 'correct', 'wrong', 'blank']
                    # Filtrar las columnas que realmente existen en el DataFrame
                    existing_ordered_columns = [col for col in ordered_columns if col in df_results.columns]
                    df_results = df_results[existing_ordered_columns]

                    metrics_display = html.Div([
                        html.P(f"Total de Estudiantes: {metrics.get('total_students')}"),
                        html.P(f"Puntuación Promedio: {metrics.get('average_score'):.2f}"),
                        html.P(f"Respuestas Correctas Promedio: {metrics.get('average_correct'):.2f}"),
                        html.P(f"Respuestas Incorrectas Promedio: {metrics.get('average_wrong'):.2f}"),
                        html.P(f"Respuestas en Blanco Promedio: {metrics.get('average_blank'):.2f}"),
                    ])

                    scores = df_results['score'].tolist() # Usar la columna 'score' del DataFrame
                    if scores:
                        fig = px.histogram(x=scores, nbins=20, title="Distribución de Puntuaciones")
                    else:
                        fig = {} # Empty figure if no data

                    # Convertir el DataFrame de nuevo a formato de lista de diccionarios para Dash DataTable
                    return df_results.to_dict(orient='records'), metrics_display, fig, html.Div("Evaluación completada exitosamente.")
                else:
                    return [], html.Div(), {}, html.Div(f"Error en la evaluación: {response_data.get('message', 'Error desconocido')}", style={'color': 'red'})
            except Exception as e:
                return [], html.Div(), {}, html.Div(f"Error en el procesamiento de evaluación: {str(e)}", style={'color': 'red'})
        return [], html.Div(), {}, html.Div("Presione 'Iniciar Evaluación' para ver los resultados.")


    @dash_app.callback(
        Output("download-dataframe-csv", "data"),
        Input("download-results-button", "n_clicks"),
        State("results-table", "data"),
        prevent_initial_call=True,
    )
    def download_results_as_csv(n_clicks, table_data):
        if not n_clicks or not table_data:
            raise dash.exceptions.PreventUpdate

        df = pd.DataFrame(table_data)
        
        # Eliminar la columna 'ID' antes de guardar si no es necesaria en el CSV final
        if 'ID' in df.columns:
            df = df.drop(columns=['ID'])

        return dcc.send_data_frame(df.to_csv, "resultados_evaluacion.csv", index=False)

    @dash_app.callback(
        Output("download-dataframe-pdf", "data"),
        Input("download-pdf-button", "n_clicks"),
        State("results-table", "data"),
        State("results-table", "columns"),
        prevent_initial_call=True,
    )
    def download_results_as_pdf(n_clicks, table_data, table_columns):
        if not n_clicks or not table_data:
            raise dash.exceptions.PreventUpdate

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Preparar los datos para la tabla PDF
        header = [col["name"] for col in table_columns]
        data = [header] + [[row[col["id"]] for col in table_columns] for row in table_data]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements = [Paragraph("Resultados de la Evaluación", styles['h1']), table]
        doc.build(elements)

        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "resultados_evaluacion.pdf")
    @dash_app.callback(
        [Output('tab-upload-files-content', 'style'),
         Output('tab-select-mode-content', 'style'),
         Output('tab-results-dashboard-content', 'style')],
        [Input('tab-upload-files-nav', 'n_clicks'),
         Input('tab-select-mode-nav', 'n_clicks'),
         Input('tab-results-dashboard-nav', 'n_clicks')]
    )
    def display_tab_content(n_clicks_upload, n_clicks_mode, n_clicks_results):
        ctx = callback_context
        if not ctx.triggered:
            # Valor por defecto: mostrar la primera pestaña
            return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'tab-upload-files-nav':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
        elif button_id == 'tab-select-mode-nav':
            return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
        elif button_id == 'tab-results-dashboard-nav':
            return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
        
        # Fallback en caso de que algo inesperado ocurra
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}


    @dash_app.callback(
        [Output('tab-upload-files-nav', 'active'),
         Output('tab-select-mode-nav', 'active'),
         Output('tab-results-dashboard-nav', 'active')],
        [Input('tab-upload-files-nav', 'n_clicks'),
         Input('tab-select-mode-nav', 'n_clicks'),
         Input('tab-results-dashboard-nav', 'n_clicks')]
    )
    def update_tab_nav_links_active(n_clicks_upload, n_clicks_mode, n_clicks_results):
        ctx = dash.callback_context
        if not ctx.triggered:
            # Valor por defecto: activar la primera pestaña
            return True, False, False

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'tab-upload-files-nav':
            return True, False, False
        elif button_id == 'tab-select-mode-nav':
            return False, True, False
        elif button_id == 'tab-results-dashboard-nav':
            return False, False, True
        
        # Fallback
        return True, False, False


    @dash_app.callback(
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
            return {'display': 'block', 'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '20px', 'border': '1px solid #ccc', 'zIndex': '1000', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)'}, \
                   current_config['chunk_size'], current_config['scoring']['correct'], current_config['scoring']['wrong'], current_config['scoring']['blank']
        elif button_id == 'close-config-modal' and close_clicks > 0:
            return {'display': 'none'}, \
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
        Input('nav-historial', 'n_clicks') # Cambiado de tabs-main a nav-historial
    )
    def load_log_dates(n_clicks):
        if n_clicks: # Activado cuando se hace clic en la pestaña Historial
            try:
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
                response = requests.get("http://127.0.0.1:8000/logs/list")
                response_data = response.json()
                files_by_date = response_data.get("files", {})
                log_files = files_by_date.get(selected_date, [])
                
                data = []
                for filename in log_files:
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

    @dash_app.callback(
        Output('benchmark-table', 'data'),
        Input('nav-benchmarking', 'n_clicks') # Cambiado de tabs-main a nav-benchmarking
    )
    def load_benchmark_data(n_clicks):
        if n_clicks: # Activado cuando se hace clic en la pestaña Benchmarking
            try:
                # Cache busting by adding a timestamp
                timestamp = int(time.time())
                response = requests.get(f"http://127.0.0.1:8000/benchmark/data?_={timestamp}")
                response_data = response.json()
                if response_data.get("status") == "ok":
                    # Convertir tiempos a milisegundos y redondear speed-up
                    df = pd.DataFrame(response_data.get("data", []))
                    if not df.empty:
                        df['Tiempo (ms)'] = (df['time'] * 1000).round(2)
                        df['Speed-up'] = df['speed_up'].round(2)
                        # Seleccionar y reordenar columnas para la tabla
                        df_display = df[['mode', 'Tiempo (ms)', 'Speed-up']]
                        df_display = df[['mode', 'Tiempo (ms)', 'Speed-up']].copy()
                        df_display.rename(columns={'mode': 'Modo'}, inplace=True)
                        return df_display.to_dict(orient='records')
                    return []
                else:
                    print(f"Error al cargar datos de benchmarking: {response_data.get('message', 'Error desconocido')}")
                    return []
            except Exception as e:
                print(f"Error en el procesamiento de carga de datos de benchmarking: {str(e)}")
                return []
        return dash.no_update

    @dash_app.callback(
        Output('benchmark-plot-iframe', 'src'),
        Input('nav-benchmarking', 'n_clicks')
    )
    def update_benchmark_plot(n_clicks):
        if n_clicks:
            timestamp = int(time.time())
            return f'/output/benchmark_plot.html?_={timestamp}'
        return dash.no_update

    # Callback para manejar la activación/desactivación de la clase 'active' en los NavLink
    # Callback para manejar la activación/desactivación de la clase 'active' en los NavLink
    @dash_app.callback(
        [Output(f"nav-{item['id']}", "active") for item in nav_items],
        [Input(f"nav-{item['id']}", "n_clicks") for item in nav_items],
    )
    def toggle_active_nav_link(*n_clicks_args):
        ctx = dash.callback_context
        if not ctx.triggered:
            active_states = [False] * len(nav_items)
            active_states[0] = True # Activar la primera pestaña por defecto
            return active_states
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        active_states = [False] * len(nav_items)
        for i, item in enumerate(nav_items):
            if f"nav-{item['id']}" == button_id:
                active_states[i] = True
                break
        return active_states

    @dash_app.callback(
        Output("page-content", "children"),
        [Input(f"nav-{item['id']}", "n_clicks") for item in nav_items],
    )
    def display_content(*n_clicks_args):
        ctx = dash.callback_context
        if not ctx.triggered:
            # Al cargar la página, mostrar el contenido de la primera pestaña por defecto
            return content_evaluacion()
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        section = button_id.replace("nav-", "")

        if section == "evaluacion":
            return content_evaluacion()
        elif section == "historial":
            return content_historial()
        elif section == "configuracion":
            return content_configuracion()
        elif section == "benchmarking":
            return content_benchmarking()
        elif section == "ayuda":
            return content_ayuda()
        return html.P("Seleccione una sección")

    # Callback para el botón de alternar sidebar
    @dash_app.callback(
        Output("sidebar-column", "width"),
        Output("sidebar-column", "style"),
        Output("page-content-column", "width"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-column", "width"),
    )
    def toggle_sidebar(n_clicks, current_width):
        if n_clicks:
            if current_width == 3:
                return 0, {'display': 'none'}, 12
            else:
                return 3, {'display': 'block'}, 9
        return 3, {'display': 'block'}, 9