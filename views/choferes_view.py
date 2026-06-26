"""
Vista de Gestión de Choferes.
Muestra el formulario para agregar y la lista scrolleable de choferes.
"""

import customtkinter as ctk
from database import models


class ChoferesView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Configurar grid principal (2 filas: Formulario y Lista)
        self.grid_rowconfigure(0, weight=0)  # Formulario no se expande
        self.grid_rowconfigure(1, weight=1)  # Lista ocupa el resto
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.load_choferes()

    def _build_ui(self):
        """Construye la interfaz de la vista."""
        # --- Título ---
        self.title_label = ctk.CTkLabel(
            self, 
            text="Gestión de Choferes", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # --- Formulario de Alta ---
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Grid para el formulario (1 fila, 5 columnas)
        self.form_frame.grid_columnconfigure(0, weight=0) # Movil (pequeño)
        self.form_frame.grid_columnconfigure(1, weight=1) # Nombre
        self.form_frame.grid_columnconfigure(2, weight=1) # Telefono
        self.form_frame.grid_columnconfigure(3, weight=0) # Boton

        # Entry: Móvil
        self.entry_movil = ctk.CTkEntry(self.form_frame, placeholder_text="Móvil", width=70)
        self.entry_movil.grid(row=0, column=0, padx=(15, 5), pady=15, sticky="ew")

        # Entry: Nombre
        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre del chofer")
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=15, sticky="ew")

        # Entry: Teléfono
        self.entry_telefono = ctk.CTkEntry(self.form_frame, placeholder_text="Teléfono")
        self.entry_telefono.grid(row=0, column=2, padx=5, pady=15, sticky="ew")

        # Botón: Agregar
        self.btn_agregar = ctk.CTkButton(
            self.form_frame, 
            text="Agregar Chofer",
            command=self._on_add_chofer
        )
        self.btn_agregar.grid(row=0, column=3, padx=15, pady=15)

        # Mensaje de error/éxito
        self.msg_label = ctk.CTkLabel(self.form_frame, text="", text_color="red")
        self.msg_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))

        # --- Lista de Choferes ---
        # Usamos un ScrollableFrame por si hay muchos choferes
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Lista de Choferes")
        self.list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1) # Columna de info se expande
        
        # Ajustamos el grid principal para acomodar el título que agregamos al principio
        self.grid_rowconfigure(0, weight=0) # Titulo
        self.grid_rowconfigure(1, weight=0) # Formulario
        self.grid_rowconfigure(2, weight=1) # Lista (se expande)

    def load_choferes(self):
        """Carga la lista de choferes desde la base de datos y la dibuja."""
        # Limpiar lista actual
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Obtener de DB
        choferes = models.get_choferes()

        if not choferes:
            lbl = ctk.CTkLabel(self.list_frame, text="No hay choferes registrados.", text_color="gray")
            lbl.pack(pady=20)
            return

        # Dibujar cada chofer
        for i, chofer in enumerate(choferes):
            item_frame = ctk.CTkFrame(self.list_frame, fg_color=("gray85", "gray20"))
            item_frame.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)

            # Info: Nombre y teléfono con Móvil destacado
            estado_txt = "🟢" if chofer["activo"] else "🔴"
            movil_txt = chofer.get('movil', '')
            movil_display = f"[Móvil {movil_txt}]" if movil_txt else "[Sin Móvil]"
            info_text = f"{estado_txt}  {movil_display}  {chofer['nombre']}  -  {chofer['telefono']}"
            
            lbl_info = ctk.CTkLabel(
                item_frame, 
                text=info_text,
                font=ctk.CTkFont(size=16, overstrike=not chofer["activo"], weight="bold"),
                text_color="gray" if not chofer["activo"] else None
            )
            lbl_info.grid(row=0, column=0, padx=15, pady=10, sticky="w")

            # Botón: Activar/Desactivar
            btn_text = "Desactivar" if chofer["activo"] else "Activar"
            btn_color = "#e74c3c" if chofer["activo"] else "#2ecc71" # Rojo si esta activo, verde si inactivo
            btn_hover = "#c0392b" if chofer["activo"] else "#27ae60"

            # Necesitamos forzar el valor de 'chofer' en el lambda (closure)
            btn_toggle = ctk.CTkButton(
                item_frame,
                text=btn_text,
                width=100,
                fg_color=btn_color,
                hover_color=btn_hover,
                command=lambda c_id=chofer['id'], status=chofer['activo']: self._on_toggle_status(c_id, status)
            )
            btn_toggle.grid(row=0, column=1, padx=15, pady=10)

            # Botón: Eliminar
            btn_delete = ctk.CTkButton(
                item_frame,
                text="Eliminar",
                width=80,
                fg_color="transparent",
                border_color="#e74c3c",
                border_width=1,
                text_color="#e74c3c",
                hover_color="#e74c3c",
                command=lambda c_id=chofer['id']: self._on_delete_chofer(c_id)
            )
            # Cambiamos el color del texto a blanco al pasar el mouse por encima (hover_color es rojo, no contrasta si la letra queda roja)
            btn_delete.bind("<Enter>", lambda e, b=btn_delete: b.configure(text_color="white"))
            btn_delete.bind("<Leave>", lambda e, b=btn_delete: b.configure(text_color="#e74c3c"))
            btn_delete.grid(row=0, column=2, padx=(0, 15), pady=10)


    # --- Eventos ---

    def _on_add_chofer(self):
        """Manejador del botón agregar."""
        movil = self.entry_movil.get().strip()
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()

        if not nombre or not movil:
            self.msg_label.configure(text="El móvil y el nombre son obligatorios.", text_color="#e74c3c")
            return

        try:
            models.add_chofer(nombre, movil, telefono)
            # Limpiar inputs
            self.entry_movil.delete(0, 'end')
            self.entry_nombre.delete(0, 'end')
            self.entry_telefono.delete(0, 'end')
            self.msg_label.configure(text="Chofer agregado con éxito.", text_color="#2ecc71")
            
            # Recargar lista
            self.load_choferes()
        except Exception as e:
            self.msg_label.configure(text=f"Error al guardar: {e}", text_color="#e74c3c")

    def _on_toggle_status(self, chofer_id: int, current_status: int):
        """Manejador del botón activar/desactivar."""
        nuevo_estado = 0 if current_status == 1 else 1
        models.toggle_chofer_status(chofer_id, nuevo_estado)
        self.load_choferes()

    def _on_delete_chofer(self, chofer_id: int):
        """Manejador del botón eliminar."""
        models.delete_chofer(chofer_id)
        self.msg_label.configure(text="Chofer eliminado correctamente.", text_color="#e74c3c")
        self.load_choferes()
