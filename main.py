"""
UBEEstation — Sistema de Gestión de Remisería
Punto de entrada de la aplicación.
"""

import customtkinter as ctk
from config.settings import APPEARANCE_MODE, COLOR_THEME
from database.connection import init_db
from views.main_window import MainWindow


def main():
    """Inicializa y ejecuta la aplicación."""

    # 1. Configurar el tema de CustomTkinter (antes de crear cualquier widget)
    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme(COLOR_THEME)

    # 2. Inicializar la base de datos (crear tablas si no existen)
    db_status = init_db()

    # 3. Crear y ejecutar la ventana principal
    app = MainWindow(db_status=db_status)
    app.mainloop()


if __name__ == "__main__":
    main()
