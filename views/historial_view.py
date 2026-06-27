"""
Vista del Historial de Viajes.
Registro permanente de solo lectura.
"""

import customtkinter as ctk
import tkinter.messagebox as messagebox
from database import models
from datetime import datetime

class HistorialView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado
        lbl_titulo = ctk.CTkLabel(self, text="HISTORIAL DE VIAJES", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_titulo.grid(row=0, column=0, pady=20, padx=20, sticky="w")

        # Contenedor de la tabla
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def load_data(self):
        """Carga y muestra los registros del historial en un grid unificado para alineación perfecta."""
        # Limpiar tabla
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        registros = models.get_historial()
        
        if not registros:
            lbl_vacio = ctk.CTkLabel(self.table_frame, text="No hay registros en el historial.", text_color="gray")
            lbl_vacio.grid(row=0, column=0, pady=20)
            return

        # 1. Configurar anchos de columnas unificados para toda la tabla
        headers = ["Fecha/Hora", "Móvil", "Chofer", "Estado", "Origen", "Destino", "Monto", "Pago", "Obs.", "Acción"]
        weights = [1, 0, 1, 1, 2, 2, 1, 1, 1, 0]
        
        for col, w in enumerate(weights):
            self.table_frame.grid_columnconfigure(col, weight=w)

        # 2. Dibujar Encabezados (Fila 0)
        for col, text in enumerate(headers):
            # Usamos un frame de fondo para los encabezados para que destaquen
            bg_frame = ctk.CTkFrame(self.table_frame, fg_color=("gray80", "gray25"), corner_radius=0)
            bg_frame.grid(row=0, column=col, sticky="nsew", padx=1, pady=(0, 5))
            
            lbl = ctk.CTkLabel(bg_frame, text=text, font=ctk.CTkFont(weight="bold"))
            lbl.pack(padx=5, pady=5, anchor="w")

        # 3. Dibujar Filas de Datos (Filas 1 a N)
        for row_idx, r in enumerate(registros, start=1):
            
            # Formatear fecha
            try:
                dt = datetime.strptime(r['updated_at'], "%Y-%m-%d %H:%M:%S")
                fecha_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_str = r['updated_at']

            estado_color = "#2ecc71" if r['estado'] == 'Finalizado' else "#e74c3c"
            monto_str = f"${r['monto']:.2f}" if r['monto'] is not None else "-"
            pago_str = r['metodo_pago'] if r['metodo_pago'] else "-"
            destino_str = r['destino'] if r['destino'] else "-"
            obs_str = r['observaciones'] if r['observaciones'] else "-"

            cols_data = [
                (fecha_str, None),
                (f"[{r['chofer_movil']}]", None),
                (r['chofer_nombre'], None),
                (r['estado'], estado_color),
                (r['origen'], None),
                (destino_str, None),
                (monto_str, None),
                (pago_str, None),
                (obs_str, None)
            ]

            # Dibujar celdas de texto
            for col, (text, color) in enumerate(cols_data):
                lbl = ctk.CTkLabel(self.table_frame, text=str(text), text_color=color)
                # sticky="w" asegura que el texto quede alineado a la izquierda dentro de su celda grid
                lbl.grid(row=row_idx, column=col, padx=5, pady=5, sticky="w")
                
            # Dibujar botón Eliminar en la última columna
            btn_delete = ctk.CTkButton(
                self.table_frame, text="❌", width=30, height=24,
                fg_color="transparent", text_color="#e74c3c", hover_color="#c0392b",
                command=lambda v=r["id"]: self._on_delete_viaje(v)
            )
            # sticky="e" para que quede alineado a la derecha
            btn_delete.grid(row=row_idx, column=9, padx=5, pady=5, sticky="e")

    def _on_delete_viaje(self, viaje_id: int):
        if messagebox.askyesno("Eliminar Viaje", "¿Estás seguro de que deseas eliminar este viaje del historial permanentemente? Esta acción no se puede deshacer."):
            models.delete_viaje_historial(viaje_id)
            self.load_data()
