from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.staticfiles import StaticFiles # Importar StaticFiles
from dash import Dash
import dash_bootstrap_components as dbc
from frontend.utils.logger import Logger
from frontend.api_routes import setup_api_routes
from frontend.dash_layout import dash_layout
from frontend.dash_callbacks import setup_dash_callbacks
from frontend.config_utils import load_scoring_config # Importar para inicializar scoring_config

# Inicialización de FastAPI y Dash
app = FastAPI()
logger = Logger()
dash_app = Dash(__name__, requests_pathname_prefix='/dash/', external_stylesheets=[dbc.themes.FLATLY])
dash_app.title = "Sistema de Evaluación"

# Montar la aplicación Dash en FastAPI
app.mount("/dash", WSGIMiddleware(dash_app.server))

# Montar la carpeta de assets para servir archivos estáticos
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Configurar rutas de la API
setup_api_routes(app)

# Configurar el layout de Dash
dash_app.layout = dash_layout

# Configurar callbacks de Dash
setup_dash_callbacks(dash_app)

# Cargar configuración inicial desde scoring.json (para asegurar que scoring_config esté disponible globalmente si es necesario)
scoring_config = load_scoring_config()

# Nota: la detección de CUDA ahora se realiza dentro de dash_layout.py