"""
Ventana principal de UBEEstation con Sidebar Layout.
"""

import customtkinter as ctk
import shutil
import os
from datetime import datetime
from config.settings import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, DB_PATH
from views.choferes_view import ChoferesView
from views.despacho_view import DespachoView
from views.historial_view import HistorialView
from database import models
from PIL import Image


class MainWindow(ctk.CTk):
    def __init__(self, db_status: bool):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(True, True) # Ahora permitimos redimensionar, el layout es fluido
        self.minsize(720, 600)

        self._center_window()
        self._build_layout()
        self._init_views()
        
        # Mostramos una vista por defecto. Si la DB falló, mostramos un error.
        if not db_status:
            self._show_error_view()
        else:
            self.show_view("despacho")

    def _center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _build_layout(self):
        """Construye el layout principal: Sidebar a la izquierda, Contenido a la derecha."""
        # Grid principal: 1 fila, 2 columnas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar: tamaño fijo
        self.grid_columnconfigure(1, weight=1)  # Contenido: toma todo el resto

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Espacio vacío abajo

        # --- Logo ---
        assets_dir = os.path.join(os.path.dirname(DB_PATH), "assets")
        logo_path = None
        for ext in ["png", "jpg", "jpeg"]:
            temp_path = os.path.join(assets_dir, f"logo.{ext}")
            if os.path.exists(temp_path):
                logo_path = temp_path
                break
                
        if logo_path:
            try:
                img_data = Image.open(logo_path)
                logo_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(120, 120))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=logo_img)
            except Exception:
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=f"🐝 {APP_NAME}", font=ctk.CTkFont(size=20, weight="bold"))
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=f"🐝 {APP_NAME}", font=ctk.CTkFont(size=20, weight="bold"))
            
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Selector de Operador ---
        self.operador_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.operador_frame.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="ew")
        self.operador_frame.grid_columnconfigure(0, weight=1)

        self.operador_var = ctk.StringVar(value="Operador...")
        self.operador_combo = ctk.CTkComboBox(
            self.operador_frame, 
            variable=self.operador_var,
            state="readonly"
        )
        self.operador_combo.grid(row=0, column=0, sticky="ew")

        self.btn_add_operador = ctk.CTkButton(
            self.operador_frame, text="+", width=30,
            command=self._on_add_operador
        )
        self.btn_add_operador.grid(row=0, column=1, padx=(5, 0))

        self._load_operadores()

        # Botones del Sidebar
        self.sidebar_btns = {}
        
        self.btn_despacho = ctk.CTkButton(
            self.sidebar_frame, text="Despacho", anchor="w",
            command=lambda: self.show_view("despacho"),
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30")
        )
        self.btn_despacho.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.sidebar_btns["despacho"] = self.btn_despacho

        self.btn_choferes = ctk.CTkButton(
            self.sidebar_frame, text="Choferes", anchor="w",
            command=lambda: self.show_view("choferes"),
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30")
        )
        self.btn_choferes.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.sidebar_btns["choferes"] = self.btn_choferes

        self.btn_historial = ctk.CTkButton(
            self.sidebar_frame, text="Historial", anchor="w",
            command=lambda: self.show_view("historial"),
            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30")
        )
        self.btn_historial.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.sidebar_btns["historial"] = self.btn_historial

        # --- Botón de Backup (abajo del todo) ---
        self.backup_label = ctk.CTkLabel(self.sidebar_frame, text="", font=ctk.CTkFont(size=11))
        self.backup_label.grid(row=7, column=0, padx=10, pady=(0, 5))

        self.btn_backup = ctk.CTkButton(
            self.sidebar_frame, text="💾 Copia de Seguridad",
            fg_color="#34495e", hover_color="#2c3e50",
            command=self._on_backup
        )
        self.btn_backup.grid(row=8, column=0, padx=10, pady=(0, 15), sticky="ew")


        # --- Contenedor Principal ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew")
        # El contenedor principal tiene un solo grid celda para apilar las vistas
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

    def _init_views(self):
        """Inicializa todas las vistas y las guarda en un diccionario."""
        self.views = {}
        
        # Instanciamos la vista de Choferes
        self.views["choferes"] = ChoferesView(self.main_content_frame, fg_color="transparent")
        self.views["choferes"].grid(row=0, column=0, sticky="nsew")

        # Instanciamos la vista de Despacho
        self.views["despacho"] = DespachoView(
            self.main_content_frame, 
            get_operador_actual_cb=self.operador_var.get,
            fg_color="transparent"
        )
        self.views["despacho"].grid(row=0, column=0, sticky="nsew")

        # Instanciamos la vista de Historial
        self.views["historial"] = HistorialView(self.main_content_frame, fg_color="transparent")
        self.views["historial"].grid(row=0, column=0, sticky="nsew")

    def _create_placeholder(self, text):
        """Crea una vista temporal para las secciones no implementadas."""
        frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        lbl = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=20), text_color="gray")
        lbl.pack(expand=True)
        return frame

    def _show_error_view(self):
        """Muestra una pantalla de error si la base de datos falla."""
        frame = self._create_placeholder("❌ Error grave:\nNo se pudo conectar a la base de datos.")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise() # Traer al frente

    def show_view(self, view_name: str):
        """Cambia la vista principal y actualiza los botones del sidebar."""
        # 1. Traer la vista seleccionada al frente
        if view_name in self.views:
            self.views[view_name].tkraise()
            
            # Recargar datos de la vista correspondiente
            if view_name == "choferes":
                self.views["choferes"].load_choferes()
            elif view_name == "despacho":
                self.views["despacho"].load_data()
            elif view_name == "historial":
                self.views["historial"].load_data()

        # 2. Actualizar estilos de los botones (marcar el activo)
        for name, btn in self.sidebar_btns.items():
            if name == view_name:
                # Botón activo
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                # Botón inactivo
                btn.configure(fg_color="transparent")

    # --- Lógica de Operadores ---

    def _load_operadores(self):
        """Carga la lista de operadores en el ComboBox."""
        operadores = models.get_operadores()
        nombres = [op["nombre"] for op in operadores]
        
        if nombres:
            self.operador_combo.configure(values=nombres)
            # Si no hay nada seleccionado o lo seleccionado ya no existe, elegimos el primero
            if self.operador_var.get() == "Operador..." or self.operador_var.get() not in nombres:
                self.operador_var.set(nombres[0])
        else:
            self.operador_combo.configure(values=["Sin operadores"])
            self.operador_var.set("Sin operadores")

    def _on_add_operador(self):
        """Muestra un diálogo simple para agregar un operador."""
        dialog = ctk.CTkInputDialog(text="Ingrese el nombre del nuevo operador:", title="Agregar Operador")
        nombre = dialog.get_input()
        
        if nombre and nombre.strip():
            models.add_operador(nombre.strip())
            self._load_operadores()
            self.operador_var.set(nombre.strip())

    # --- Copia de Seguridad ---

    def _on_backup(self):
        """Crea una copia del archivo SQLite en la carpeta /backups."""
        try:
            # Crear carpeta backups si no existe
            backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            # Nombre con timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            backup_name = f"ubeestation_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)

            shutil.copy2(DB_PATH, backup_path)

            self.backup_label.configure(text=f"✅ Backup OK ({timestamp})", text_color="#2ecc71")
        except Exception as e:
            self.backup_label.configure(text=f"❌ Error: {e}", text_color="#e74c3c")
