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
    {"id": "evaluacion", "label": "Nueva Evaluación", "badge": "Nuevo", "icon": "🚀"},
    {"id": "historial", "label": "Historial de Ejecuciones", "icon": "📊"},
    {"id": "configuracion", "label": "Configuración Global", "icon": "⚙️"},
    {"id": "benchmarking", "label": "Benchmarking", "icon": "⚡"},
    {"id": "ayuda", "label": "Ayuda / Documentación", "icon": "❓"},
]

def render_sidebar():
    return html.Div([
        # Header del sidebar
        html.Div([
            html.Div([
                html.Div("📋", className="fs-2 mb-2"),
                html.H4("AdmisionTech", className="mb-1 fw-bold text-white"),
                html.Small("Sistema de Evaluación", className="text-white-50")
            ], className="text-center py-4")
        ], className="bg-gradient", style={
            'background': '#343a40',
            'borderRadius': '0 0 20px 20px',
            'marginBottom': '2rem',
            'color': 'white'
        }),
        
        # Navegación
        html.Div([
            html.H6("Navegación", className="text-muted fw-bold mb-3 px-3"),
            html.Div([
                html.A([
                    html.Div([
                        html.Span(item["icon"], className="me-3 fs-5"),
                        html.Span(item["label"], className="fw-medium"),
                        dbc.Badge(item["badge"], color="primary", className="ms-auto rounded-pill") if "badge" in item else None
                    ], className="d-flex align-items-center")
                ], href="#", id=f"nav-{item['id']}", className="nav-link-modern text-decoration-none text-dark p-3 mb-2 rounded-3 d-block position-relative", style={
                    'transition': 'all 0.3s ease',
                    'border': '1px solid transparent'
                })
                for item in nav_items
            ], className="px-3")
        ])
    ], className="h-100", style={
        'background': '#f8f9fa',
        'borderRight': '1px solid #e9ecef'
    })

def render_header():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Button(
                    html.Span("☰", className="navbar-toggler-icon"),
                    id="sidebar-toggle",
                    className="btn btn-link text-secondary me-3",
                    style={'fontSize': '1.5rem', 'border': 'none', 'background': 'transparent'}
                ),
                html.Div([
                    html.H3("AdmisionTech", className="mb-0 fw-bold text-primary"),
                    html.Small("Sistema de Evaluación Inteligente", className="text-muted")
                ], className="d-inline-block align-middle")
            ], width="auto", className="d-flex align-items-center"),
            dbc.Col([
                html.Div([
                    dbc.Badge([
                        html.I(className="fas fa-circle me-1", style={'fontSize': '8px', 'color': '#28a745'}),
                        "Sistema Activo"
                    ], color="light", className="text-success border border-success px-3 py-2 rounded-pill")
                ], className="text-end")
            ], width="auto")
        ], className="align-items-center")
    ], className="bg-white border-bottom p-4 shadow-sm")

def content_evaluacion():
    return html.Div([
        # Header de sección
        html.Div([
            html.H1([
                html.Span("🚀", className="me-3"),
                "Nueva Evaluación"
            ], className="display-6 fw-bold text-dark mb-0"),
            html.P("Configura y ejecuta evaluaciones de manera eficiente", className="text-muted fs-5 mb-0")
        ], className="mb-5"),
        
        # Tabs navegación
        html.Div([
            dbc.Nav([
                dbc.NavLink([
                    html.Span("📁", className="me-2"),
                    "Cargar Archivos"
                ], id="tab-upload-files-nav", href="#", active=True, className="nav-tab-modern px-4 py-3 me-2"),
                dbc.NavLink([
                    html.Span("⚡", className="me-2"),
                    "Configurar Modo"
                ], id="tab-select-mode-nav", href="#", className="nav-tab-modern px-4 py-3 me-2"),
                dbc.NavLink([
                    html.Span("📊", className="me-2"),
                    "Resultados"
                ], id="tab-results-dashboard-nav", href="#", className="nav-tab-modern px-4 py-3"),
            ], pills=True, className="nav-pills-modern mb-4")
        ]),
        
        # Contenido de tabs
        html.Div([
            # Tab 1: Upload Files
            html.Div(id="tab-upload-files-content", style={'display': 'block'}, children=[
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            # Header de la card
                            html.Div([
                                html.Div([
                                    html.Span("📊", className="fs-2 text-primary me-3"),
                                    html.Div([
                                        html.H4("Respuestas de Postulantes", className="mb-1 fw-bold"),
                                        html.P("Archivo Excel con DNI + 100 respuestas", className="text-muted mb-0 small")
                                    ])
                                ], className="d-flex align-items-center mb-4")
                            ]),
                            
                            # Upload area
                            dcc.Upload(
                                id='upload-students-data',
                                children=html.Div([
                                    html.Div("📤", className="fs-1 text-primary mb-3"),
                                    html.H5("Arrastra tu archivo aquí", className="text-primary fw-bold mb-2"),
                                    html.P("o haz clic para seleccionar", className="text-muted mb-3"),
                                    html.Small("Formatos soportados: .xlsx", className="text-muted")
                                ], className="text-center py-5"),
                                style={
                                    'borderRadius': '15px',
                                    'border': '2px dashed #6c63ff',
                                    'background': 'linear-gradient(145deg, #f8f9ff 0%, #ffffff 100%)',
                                    'cursor': 'pointer',
                                    'transition': 'all 0.3s ease'
                                },
                                className="upload-area-modern"
                            )
                        ], className="modern-card p-4")
                    ], width=6),
                    
                    dbc.Col([
                        html.Div([
                            # Header de la card
                            html.Div([
                                html.Div([
                                    html.Span("🔑", className="fs-2 text-success me-3"),
                                    html.Div([
                                        html.H4("Clave de Respuestas", className="mb-1 fw-bold"),
                                        html.P("Archivo con pregunta_id + respuesta_correcta", className="text-muted mb-0 small")
                                    ])
                                ], className="d-flex align-items-center mb-4")
                            ]),
                            
                            # Upload area
                            dcc.Upload(
                                id='upload-key-data',
                                children=html.Div([
                                    html.Div("📤", className="fs-1 text-success mb-3"),
                                    html.H5("Arrastra tu archivo aquí", className="text-success fw-bold mb-2"),
                                    html.P("o haz clic para seleccionar", className="text-muted mb-3"),
                                    html.Small("Formatos soportados: .xlsx", className="text-muted")
                                ], className="text-center py-5"),
                                style={
                                    'borderRadius': '15px',
                                    'border': '2px dashed #20c997',
                                    'background': 'linear-gradient(145deg, #f8fff8 0%, #ffffff 100%)',
                                    'cursor': 'pointer',
                                    'transition': 'all 0.3s ease'
                                },
                                className="upload-area-modern"
                            )
                        ], className="modern-card p-4")
                    ], width=6),
                ], className="g-4"),
                
                html.Div(id='output-upload-status', className="mt-4"),
            ]),
            
            # Tab 2: Select Mode
            html.Div(id="tab-select-mode-content", style={'display': 'none'}, children=[
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("⚙️", className="fs-2 text-warning me-3"),
                            html.H4("Configuración de Evaluación", className="mb-0 fw-bold")
                        ], className="d-flex align-items-center mb-4"),
                        
                        # Modo de ejecución
                        html.Div([
                            html.H5("Modo de Ejecución", className="fw-bold mb-3 text-dark"),
                            html.Div([
                                dcc.RadioItems(
                                    id='mode-selector',
                                    options=[
                                        {'label': html.Div(['⚡ Serial'], className="mode-option"), 'value': 'serial'},
                                        {'label': html.Div(['🔥 OpenMP'], className="mode-option"), 'value': 'openmp'},
                                        {'label': html.Div(['🧵 Pthreads'], className="mode-option"), 'value': 'pthreads'},
                                        {'label': html.Div(['🚀 CUDA'], className="mode-option text-muted" if not cuda_available else "mode-option"), 'value': 'cuda', 'disabled': not cuda_available}
                                    ],
                                    value='serial',
                                    className="mode-selector-modern",
                                    labelStyle={'display': 'block', 'margin': '10px 0'}
                                )
                            ], className="p-3 bg-light rounded-3")
                        ], className="mb-4"),
                        
                        # Configuración de puntuación
                        html.Div([
                            html.H5("Configuración de Puntuación", className="fw-bold mb-3 text-dark"),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Respuesta Correcta", className="form-label fw-medium text-success"),
                                    dcc.Input(
                                        id='score-correct', 
                                        type='number', 
                                        value=scoring_config['scoring']['correct'], 
                                        className="form-control form-control-modern",
                                        style={'borderColor': '#28a745'}
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Respuesta Incorrecta", className="form-label fw-medium text-danger"),
                                    dcc.Input(
                                        id='score-wrong', 
                                        type='number', 
                                        value=scoring_config['scoring']['wrong'], 
                                        className="form-control form-control-modern",
                                        style={'borderColor': '#dc3545'}
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Respuesta en Blanco", className="form-label fw-medium text-secondary"),
                                    dcc.Input(
                                        id='score-blank', 
                                        type='number', 
                                        value=scoring_config['scoring']['blank'], 
                                        className="form-control form-control-modern",
                                        style={'borderColor': '#6c757d'}
                                    )
                                ], width=4),
                            ], className="g-3")
                        ], className="p-3 bg-light rounded-3 mb-4"),
                        
                        # Botones de acción
                        html.Div([
                            dbc.Button([
                                html.Span("🚀", className="me-2"),
                                "Iniciar Evaluación"
                            ], id='run-button', n_clicks=0, className="btn-modern-primary me-3 px-4 py-3"),
                            dbc.Button([
                                html.Span("⚙️", className="me-2"),
                                "Configuración Avanzada"
                            ], id='open-config-modal', n_clicks=0, className="btn-modern-outline px-4 py-3"),
                        ], className="d-flex"),
                        
                        html.Div(id='output-run-status', className="mt-4"),
                        dcc.Store(id='scoring-config-store', data=scoring_config),
                    ])
                ], className="modern-card p-4")
            ]),
            
            # Tab 3: Results Dashboard
            html.Div(id="tab-results-dashboard-content", style={'display': 'none'}, children=[
                html.Div([
                    html.Div([
                        html.Span("📈", className="fs-2 text-info me-3"),
                        html.H4("Dashboard de Resultados", className="mb-0 fw-bold")
                    ], className="d-flex align-items-center mb-4"),
                    
                    # Tabla de resultados
                    html.Div([
                        dash_table.DataTable(
                            id='results-table',
                            columns=[
                                {"name": "ID", "id": "ID"},
                                {"name": "DNI", "id": "DNI"},
                                {"name": "Puntuación", "id": "score"},
                                {"name": "Correctas", "id": "correct"},
                                {"name": "Incorrectas", "id": "wrong"},
                                {"name": "Blancas", "id": "blank"},
                            ],
                            data=[],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left', 
                                'padding': '12px',
                                'fontFamily': 'Inter, sans-serif',
                                'border': '1px solid #e9ecef'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold',
                                'color': '#495057',
                                'border': '1px solid #dee2e6'
                            },
                            style_data={
                                'backgroundColor': 'white',
                                'color': '#212529'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }
                            ]
                        )
                    ], className="mb-4"),
                    
                    html.Div(id='metrics-output', className="mb-4"),
                    
                    # Botones de descarga
                    html.Div([
                        dbc.Button([
                            html.Span("📊", className="me-2"),
                            "Descargar CSV"
                        ], id="download-results-button", className="btn-modern-success me-3"),
                        dbc.Button([
                            html.Span("📄", className="me-2"),
                            "Descargar PDF"
                        ], id="download-pdf-button", className="btn-modern-danger"),
                    ], className="mb-4"),
                    
                    dcc.Download(id="download-dataframe-csv"),
                    dcc.Download(id="download-dataframe-pdf"),
                    
                    # Gráfico
                    html.Div([
                        dcc.Graph(id='score-histogram', className="rounded-3")
                    ], className="bg-white p-3 rounded-3 shadow-sm")
                    
                ], className="modern-card p-4")
            ]),
        ]),
        
        # Modal de configuración avanzada
        html.Div(children=[
            html.Div([
                html.Div([
                    html.Div([
                        html.H3([
                            html.Span("⚙️", className="me-3"),
                            "Configuración Avanzada"
                        ], className="fw-bold text-dark mb-0")
                    ], className="modal-header-modern p-4 border-bottom"),
                    
                    html.Div([
                        html.Div([
                            html.Label("Chunk Size", className="form-label fw-medium"),
                            dcc.Input(
                                id='modal-chunk-size', 
                                type='number', 
                                value=scoring_config['chunk_size'],
                                className="form-control form-control-modern"
                            ),
                        ], className="mb-4"),
                        
                        html.Div([
                            html.H5("Reglas de Puntuación", className="fw-bold mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Correctas", className="form-label fw-medium text-success"),
                                    dcc.Input(
                                        id='modal-score-correct', 
                                        type='number', 
                                        value=scoring_config['scoring']['correct'],
                                        className="form-control form-control-modern"
                                    ),
                                ], width=4),
                                dbc.Col([
                                    html.Label("Incorrectas", className="form-label fw-medium text-danger"),
                                    dcc.Input(
                                        id='modal-score-wrong', 
                                        type='number', 
                                        value=scoring_config['scoring']['wrong'],
                                        className="form-control form-control-modern"
                                    ),
                                ], width=4),
                                dbc.Col([
                                    html.Label("En Blanco", className="form-label fw-medium text-secondary"),
                                    dcc.Input(
                                        id='modal-score-blank', 
                                        type='number', 
                                        value=scoring_config['scoring']['blank'],
                                        className="form-control form-control-modern"
                                    ),
                                ], width=4),
                            ], className="g-3")
                        ], className="mb-4"),
                        
                        html.Div([
                            dbc.Button([
                                html.Span("💾", className="me-2"),
                                "Guardar Configuración"
                            ], id='save-config-button', n_clicks=0, className="btn-modern-primary me-3"),
                            dbc.Button("Cerrar", id='close-config-modal', n_clicks=0, className="btn-modern-outline"),
                        ]),
                        
                        html.Div(id='config-save-status', className="mt-3")
                    ], className="p-4")
                ], className="bg-white rounded-4 shadow-lg", style={'width': '600px', 'maxWidth': '90vw'})
            ], className="modal-backdrop-modern")
        ], id="modal-container", style={'display': 'none'})
    ])

def content_historial():
    return html.Div([
        html.Div([
            html.H1([
                html.Span("📊", className="me-3"),
                "Historial de Ejecuciones"
            ], className="display-6 fw-bold text-dark mb-0"),
            html.P("Revisa y descarga logs de evaluaciones anteriores", className="text-muted fs-5 mb-0")
        ], className="mb-5"),
        
        html.Div([
            html.Div([
                html.Span("📋", className="fs-2 text-primary me-3"),
                html.H4("Logs de Evaluación", className="mb-0 fw-bold")
            ], className="d-flex align-items-center mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Seleccionar Fecha:", className="form-label fw-medium"),
                    dcc.Dropdown(
                        id='log-date-dropdown',
                        options=[],
                        placeholder="Selecciona una fecha",
                        className="dropdown-modern mb-3"
                    ),
                ]),
            ]),
            
            html.Div([
                html.Label("Archivos de Log:", className="form-label fw-medium mb-3"),
                dash_table.DataTable(
                    id='log-files-table',
                    columns=[
                        {"name": "Archivo", "id": "filename"},
                        {"name": "Descargar JSONL", "id": "download_jsonl", "presentation": "markdown"},
                        {"name": "Descargar CSV", "id": "download_csv", "presentation": "markdown"},
                    ],
                    data=[],
                    page_size=10,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left', 
                        'padding': '12px',
                        'fontFamily': 'Inter, sans-serif',
                        'border': '1px solid #e9ecef'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'color': '#495057'
                    }
                ),
                html.Div(id='log-history-status', className="mt-3"),
            ])
        ], className="modern-card p-4")
    ])

def content_configuracion():
    return html.Div([
        html.Div([
            html.H1([
                html.Span("⚙️", className="me-3"),
                "Configuración Global"
            ], className="display-6 fw-bold text-dark mb-0"),
            html.P("Personaliza las configuraciones del sistema", className="text-muted fs-5 mb-0")
        ], className="mb-5"),
        
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Idioma", className="form-label fw-medium"),
                    dcc.Dropdown(
                        options=[{"label": i, "value": i} for i in ["Español", "English"]], 
                        value="Español",
                        className="dropdown-modern"
                    )
                ]),
                dbc.Col([
                    html.Label("Zona Horaria", className="form-label fw-medium"),
                    dcc.Dropdown(
                        options=[{"label": i, "value": i} for i in ["GMT-5 (Lima)", "GMT-3 (Buenos Aires)"]], 
                        value="GMT-5 (Lima)",
                        className="dropdown-modern"
                    )
                ])
            ], className="g-4 mb-4"),
            
            dbc.Button([
                html.Span("💾", className="me-2"),
                "Guardar Cambios"
            ], className="btn-modern-primary px-4 py-3")
        ], className="modern-card p-4")
    ])

def content_benchmarking():
    return html.Div([
        html.Div([
            html.H1([
                html.Span("⚡", className="me-3"),
                "Benchmarking"
            ], className="display-6 fw-bold text-dark mb-0"),
            html.P("Análisis de rendimiento y comparación de modos", className="text-muted fs-5 mb-0")
        ], className="mb-5"),
        
        html.Div([
            html.Div([
                html.Span("📊", className="fs-2 text-success me-3"),
                html.H4("Tabla de Resultados", className="mb-0 fw-bold")
            ], className="d-flex align-items-center mb-4"),
            
            dash_table.DataTable(
                id='benchmark-table',
                columns=[{"name": i, "id": i} for i in ["Modo", "Tiempo (ms)", "Speed-up"]],
                data=[],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left', 
                    'padding': '12px',
                    'fontFamily': 'Inter, sans-serif',
                    'border': '1px solid #e9ecef'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'color': '#495057'
                }
            )
        ], className="modern-card p-4 mb-4"),
        
        html.Div([
            html.Div([
                html.Span("📈", className="fs-2 text-info me-3"),
                html.H4("Gráfico de Speed-up", className="mb-0 fw-bold")
            ], className="d-flex align-items-center mb-4"),
            
            html.Iframe(
                id='benchmark-plot-iframe',
                src='/output/benchmark_plot.html',
                style={"height": "600px", "width": "100%", "border": "none", "borderRadius": "10px"}
            )
        ], className="modern-card p-4")
    ])

def content_ayuda():
    return html.Div([
        html.Div([
            html.H1([
                html.Span("❓", className="me-3"),
                "Ayuda y Documentación"
            ], className="display-6 fw-bold text-dark mb-0"),
            html.P("Encuentra respuestas y recursos para usar el sistema", className="text-muted fs-5 mb-0")
        ], className="mb-5"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Span("📚", className="fs-2 text-primary me-3"),
                        html.H4("Guía de Usuario", className="mb-0 fw-bold")
                    ], className="d-flex align-items-center mb-4"),
                    
                    html.Div([
                        html.Div([
                            html.Span("✅", className="me-3 text-success"),
                            "Cómo crear una nueva evaluación"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("✅", className="me-3 text-success"),
                            "Configuración de parámetros"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("✅", className="me-3 text-success"),
                            "Interpretación de resultados"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("✅", className="me-3 text-success"),
                            "Exportación de datos"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                    ])
                ], className="modern-card p-4 h-100")
            ]),
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Span("🔧", className="fs-2 text-warning me-3"),
                        html.H4("Documentación Técnica", className="mb-0 fw-bold")
                    ], className="d-flex align-items-center mb-4"),
                    
                    html.Div([
                        html.Div([
                            html.Span("🔗", className="me-3 text-info"),
                            "API de integración"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("📄", className="me-3 text-info"),
                            "Formatos de datos"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("🛠️", className="me-3 text-info"),
                            "Solución de problemas"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                        html.Div([
                            html.Span("🆕", className="me-3 text-info"),
                            "Actualizaciones del sistema"
                        ], className="guide-item p-3 mb-2 rounded-3"),
                    ])
                ], className="modern-card p-4 h-100")
            ])
        ], className="g-4")
    ])

# Layout principal de la aplicación Dash
dash_layout = html.Div([
    # Estilos CSS personalizados
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                render_sidebar()
            ], id="sidebar-column", width=3, className="sidebar-modern p-0"),
            dbc.Col([
                render_header(),
                html.Div(id="page-content", className="p-4", style={'minHeight': 'calc(100vh - 80px)'})
            ], id="page-content-column", width=9, className="p-0")
        ], className="g-0")
    ], fluid=True, className="p-0")
], style={'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', 'minHeight': '100vh'})