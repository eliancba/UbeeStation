"""
Configuración general de la aplicación UBEEstation.

Todas las constantes van acá para poder cambiarlas desde un solo lugar.
"""

import os

# --- Aplicación ---
APP_NAME = "UBEEstation"
APP_VERSION = "1.0.0"

# --- Ventana principal ---
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 720

# --- Base de datos ---
# La base de datos se guarda en la misma carpeta del proyecto.
# os.path.dirname(__file__) nos da la carpeta de este archivo (config/).
# Subimos un nivel (..) para llegar a la raíz del proyecto.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ubeestation.db")

# --- Tema ---
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"
