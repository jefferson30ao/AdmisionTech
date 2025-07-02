from dash import html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import pyevalcore

# Cargar configuración inicial
try:
    from frontend.config_utils import load_scoring_config
    scoring_config = load_scoring_config()
except ImportError:
    scoring_config = {
      "chunk_size": 0,
      "scoring": {
        "correct": 20.0,
        "wrong": -1.125,
        "blank": 0.0
      }
    }

try:
    cuda_available = (pyevalcore.get_device_count() > 0)
except Exception:
    cuda_available = False

# Definición de elementos de navegación
nav_items = [
    {"id": "evaluacion", "label": "Nueva Evaluación", "badge": "Nuevo"},
    {"id": "historial", "label": "Historial de Ejecuciones"},
    {"id": "configuracion", "label": "Configuración Global"},
    {"id": "benchmarking", "label": "Benchmarking"}, # Nueva pestaña para benchmarking
    {"id": "ayuda", "label": "Ayuda / Documentación"},
]

def render_sidebar():
    return dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.Div(
                    dbc.Button("\U0001F4CB", color="warning", className="rounded-circle text-white")), width="auto"),
                dbc.Col([
                    html.H5("Sistema de Evaluación", className="mb-0"),
                    html.Small("Panel de Control", className="text-muted")
                ])
            ], align="center", className="g-2")
        ),
        dbc.CardBody([
            html.H6("Navegación Principal", className="text-warning fw-bold"),
            dbc.Nav([
                dbc.NavLink([
                    item["label"],
                    dbc.Badge(item["badge"], color="warning", className="ms-auto") if "badge" in item else None
                ], href="#", id=f"nav-{item['id']}", active="exact", className="text-dark")
                for item in nav_items
            ], vertical=True, pills=True)
        ]),
    ])

def render_header():
    return dbc.Row([
        dbc.Col(dbc.Button("☰", id="sidebar-toggle", outline=True, color="warning"), width="auto"),
        dbc.Col(html.H4("AdmisionTech", className="mb-0 text-warning fw-bold"), width="auto"),
        dbc.Col(dbc.Badge("Sistema Activo", color="warning", className="rounded-pill"), width="auto"),
    ], className="border-bottom border-warning p-3 align-items-center")

def content_evaluacion():
    return html.Div([
        dbc.Row([
            dbc.Col(html.H1("Nueva Evaluación", className="text-dark fw-bold")),
        ], align="center"),
        dbc.Row([
            dbc.Col(
                dbc.Nav(
                    [
                        dbc.NavLink("Cargar Archivos", id="tab-upload-files-nav", href="#", active=True, className="me-2"),
                        dbc.NavLink("Seleccionar Modo", id="tab-select-mode-nav", href="#", className="me-2"),
                        dbc.NavLink("Dashboard de Resultados", id="tab-results-dashboard-nav", href="#", className="me-2"),
                    ],
                    pills=True,
                    className="nav-pills-custom mb-3"
                ),
                width=12
            )
        ]),
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Div(id="tab-upload-files-content", style={'display': 'block'}, children=[
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                dbc.CardHeader([
                                    html.Div([
                                        html.Img(src="/assets/excel_icon.svg", style={'width': '20px', 'marginRight': '5px'}),
                                        html.H5("Respuestas de Postulantes", className="mb-0 d-inline-block")
                                    ]),
                                    html.Small("Archivo .xlsx con 101 columnas (DNI + 100 respuestas)", className="text-muted d-block")
                                ], className="text-dark fw-bold"),
                                dbc.CardBody([
                                    dcc.Upload(
                                        id='upload-students-data',
                                        children=html.Div([
                                            html.Img(src="/assets/upload_icon.svg", style={'width': '30px', 'marginBottom': '5px'}),
                                            html.P("Arrastra o haz clic para cargar", className="mb-0")
                                        ]),
                                        style={
                                            'width': '100%', 'height': '150px',
                                            'borderWidth': '2px', 'borderStyle': 'dashed',
                                            'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px 0',
                                            'borderColor': '#FFC107', 'backgroundColor': '#FFF8E1', 'cursor': 'pointer'
                                        },
                                        multiple=False,
                                        className="d-flex flex-column justify-content-center align-items-center"
                                    ),
                                ]),
                            ], className="h-100"), width=6),
                            dbc.Col(dbc.Card([
                                dbc.CardHeader([
                                    html.Div([
                                        html.Img(src="/assets/excel_icon.svg", style={'width': '20px', 'marginRight': '5px'}),
                                        html.H5("Clave de Respuestas", className="mb-0 d-inline-block")
                                    ]),
                                    html.Small("Archivo .xlsx con 2 columnas (pregunta_id + respuesta_correcta)", className="text-muted d-block")
                                ], className="text-dark fw-bold"),
                                dbc.CardBody([
                                    dcc.Upload(
                                        id='upload-key-data',
                                        children=html.Div([
                                            html.Img(src="/assets/upload_icon.svg", style={'width': '30px', 'marginBottom': '5px'}),
                                            html.P("Arrastra o haz clic para cargar", className="mb-0")
                                        ]),
                                        style={
                                            'width': '100%', 'height': '150px',
                                            'borderWidth': '2px', 'borderStyle': 'dashed',
                                            'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px 0',
                                            'borderColor': '#FFC107', 'backgroundColor': '#FFF8E1', 'cursor': 'pointer'
                                        },
                                        multiple=False,
                                        className="d-flex flex-column justify-content-center align-items-center"
                                    ),
                                ]),
                            ], className="h-100"), width=6),
                        ], className="g-4 mt-3"),
                        html.Div(id='output-upload-status', className="mt-3"),
                    ]),
                    html.Div(id="tab-select-mode-content", style={'display': 'none'}, children=[
                        dbc.Card([
                            dbc.CardHeader(["\U0001F50D Configuración de Evaluación"], className="text-warning fw-bold"),
                            dbc.CardBody([
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
                                        className="ms-3"
                                    ),
                                ], className="mb-3"),
                                html.Div([
                                    html.Label("Puntuación Correcta:"),
                                    dcc.Input(id='score-correct', type='number', value=scoring_config['scoring']['correct'], className="me-2"),
                                    html.Label("Puntuación Incorrecta:"),
                                    dcc.Input(id='score-wrong', type='number', value=scoring_config['scoring']['wrong'], className="me-2"),
                                    html.Label("Puntuación en Blanco:"),
                                    dcc.Input(id='score-blank', type='number', value=scoring_config['scoring']['blank']),
                                ], className="mb-3"),
                                dbc.Button('Iniciar Evaluación', id='run-button', n_clicks=0, color="warning", className="text-white me-2"),
                                dbc.Button('Configuración Avanzada', id='open-config-modal', n_clicks=0, outline=True, color="warning"),
                                html.Div(id='output-run-status', className="mt-3"),
                                dcc.Store(id='scoring-config-store', data=scoring_config),
                            ]),
                        ], className="h-100 mt-3")
                    ]),
                    html.Div(id="tab-results-dashboard-content", style={'display': 'none'}, children=[
                        dbc.Card([
                            dbc.CardHeader(["\U00002699 Resultados de la Evaluación"], className="text-warning fw-bold"),
                            dbc.CardBody([
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
                                html.Div(id='metrics-output', className="mt-3"),
                                dcc.Graph(id='score-histogram'),
                            ]),
                        ], className="h-100 mt-3")
                    ]),
                ]),
                width=12
            )
        ], className="g-4 mt-3"),
        html.Div(id='modal-content', children=[
            dbc.Card([
                dbc.CardHeader(html.H3("Configuración Avanzada")),
                dbc.CardBody([
                    html.Div([
                        html.Label("Chunk Size:"),
                        dcc.Input(id='modal-chunk-size', type='number', value=scoring_config['chunk_size']),
                    ], className="mb-3"),
                    html.Div([
                        html.H4("Reglas de Puntuación"),
                        html.Label("Correctas:"),
                        dcc.Input(id='modal-score-correct', type='number', value=scoring_config['scoring']['correct']),
                        html.Label("Incorrectas:"),
                        dcc.Input(id='modal-score-wrong', type='number', value=scoring_config['scoring']['wrong']),
                        html.Label("En Blanco:"),
                        dcc.Input(id='modal-score-blank', type='number', value=scoring_config['scoring']['blank']),
                    ], className="mb-3"),
                    dbc.Button('Guardar Configuración', id='save-config-button', n_clicks=0, color="warning", className="text-white me-2"),
                    dbc.Button('Cerrar', id='close-config-modal', n_clicks=0, outline=True, color="secondary"),
                    html.Div(id='config-save-status', className="mt-3")
                ])
            ])
        ], style={'display': 'none', 'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 'backgroundColor': 'white', 'padding': '20px', 'border': '1px solid #ccc', 'zIndex': '1000', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)'}),
    ])

def content_historial():
    return html.Div([
        html.H1("Historial de Ejecuciones", className="text-dark fw-bold"),
        dbc.Card([
            dbc.CardHeader("Logs de Evaluación", className="text-warning fw-bold"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Seleccionar Fecha:"),
                        dcc.Dropdown(
                            id='log-date-dropdown',
                            options=[],
                            placeholder="Selecciona una fecha",
                            className="mb-3"
                        ),
                    ]),
                ]),
                html.Div([
                    dbc.Label("Archivos de Log:"),
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
                    html.Div(id='log-history-status', className="mt-3"),
                ])
            ])
        ])
    ])

def content_configuracion():
    return html.Div([
        html.H1("Configuración Global", className="text-dark fw-bold"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Idioma"),
                        dcc.Dropdown(options=[{"label": i, "value": i} for i in ["Español", "English"]], value="Español")
                    ]),
                    dbc.Col([
                        dbc.Label("Zona Horaria"),
                        dcc.Dropdown(options=[{"label": i, "value": i} for i in ["GMT-5 (Lima)", "GMT-3 (Buenos Aires)"]], value="GMT-5 (Lima)")
                    ])
                ], className="g-4 mb-3"),
                dbc.Button("Guardar Cambios", color="warning", className="text-white")
            ])
        ])
    ])

def content_benchmarking():
    return html.Div([
        html.H1("Resultados de Benchmarking", className="text-dark fw-bold"),
        dbc.Card([
            dbc.CardHeader("Tabla de Resultados", className="text-warning fw-bold"),
            dbc.CardBody([
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
                )
            ])
        ]),
        dbc.Card([
            dbc.CardHeader("Gráfico de Speed-up", className="text-warning fw-bold"),
            dbc.CardBody([
                html.Iframe(
                    id='benchmark-plot-iframe',
                    src='/output/benchmark_plot.html', # La ruta al archivo HTML del gráfico
                    style={"height": "600px", "width": "100%", "border": "none"}
                )
            ])
        ], className="mt-4")
    ])

def content_ayuda():
    return html.Div([
        html.H1("Ayuda y Documentación", className="text-dark fw-bold"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("\U00002753 Guía de Usuario", className="text-warning fw-bold"),
                dbc.CardBody([
                    html.Ul([
                        html.Li("Cómo crear una nueva evaluación"),
                        html.Li("Configuración de parámetros"),
                        html.Li("Interpretación de resultados"),
                        html.Li("Exportación de datos")
                    ])
                ])
            ])),
            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001F4C4 Documentación Técnica", className="text-warning fw-bold"),
                dbc.CardBody([
                    html.Ul([
                        html.Li("API de integración"),
                        html.Li("Formatos de datos"),
                        html.Li("Solución de problemas"),
                        html.Li("Actualizaciones del sistema")
                    ])
                ])
            ]))
        ], className="g-4 mt-2")
    ])

# Layout principal de la aplicación Dash
dash_layout = dbc.Container([
    dbc.Row(id="app-container", children=[
        dbc.Col(id="sidebar-column", children=[
            render_sidebar()
        ], width=3, className="bg-white border-end border-warning"),
        dbc.Col(id="page-content", children=[
            render_header(),
            html.Div(id="main-content", className="p-4")
        ], width=9)
    ])
], fluid=True)