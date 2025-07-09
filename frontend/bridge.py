import os
import sys
import logging # Importar el módulo logging

# Configurar logging inicial a un archivo
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_startup.log')
logging.basicConfig(filename=log_file_path, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug("Starting bridge.py script execution.")

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

logging.debug("Imports successful. Initializing FastAPI and Dash.")

# Inicialización de FastAPI y Dash
app = FastAPI()
logger = Logger()
dash_app = Dash(__name__, requests_pathname_prefix='/dash/', external_stylesheets=[dbc.themes.FLATLY])
dash_app.title = "Sistema de Evaluación"

# Montar la aplicación Dash en FastAPI
app.mount("/dash", WSGIMiddleware(dash_app.server))

# Determinar la ruta base para los recursos empaquetados por PyInstaller
if getattr(sys, 'frozen', False): # Comprobar si se ejecuta como un ejecutable de PyInstaller
    # En PyInstaller, los archivos se extraen a una carpeta temporal accesible vía sys._MEIPASS
    base_path = sys._MEIPASS
else:
    # En modo desarrollo, la ruta base es el directorio del script
    base_path = os.path.dirname(os.path.abspath(__file__))

logging.debug(f"Determined base_path: {base_path}")

# Montar la carpeta de assets para servir archivos estáticos
assets_path = os.path.join(base_path, 'assets')
logging.debug(f"Assets path: {assets_path}")
app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

logging.debug("Assets mounted. Setting up API routes.")

# Configurar rutas de la API
setup_api_routes(app)

logging.debug("API routes set up. Setting Dash layout.")

# Configurar el layout de Dash
dash_app.layout = dash_layout

logging.debug("Dash layout set. Setting up callbacks.")

# Configurar callbacks de Dash
setup_dash_callbacks(dash_app)

logging.debug("Dash callbacks set up. Loading initial scoring config.")

# Cargar configuración inicial desde scoring.json (para asegurar que scoring_config esté disponible globalmente si es necesario)
scoring_config = load_scoring_config()

# Nota: la detección de CUDA ahora se realiza dentro de dash_layout.py
logging.debug("Script setup complete. Starting server if run as main.")

if __name__ == "__main__":
    import uvicorn
    logging.info("Starting Uvicorn server.")
    uvicorn.run(app, host="127.0.0.1", port=8050)