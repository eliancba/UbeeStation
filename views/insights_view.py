"""
Vista de Insights / Resumen por Chofer.
"""

import customtkinter as ctk
from database import models
from datetime import datetime

class InsightsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Encabezado y Filtro
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        lbl_titulo = ctk.CTkLabel(top_frame, text="RESUMEN DIARIO", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_titulo.grid(row=0, column=0, sticky="w")

        self.chofer_var = ctk.StringVar(value="Todos los choferes")
        self.combo_choferes = ctk.CTkComboBox(
            top_frame, 
            variable=self.chofer_var,
            state="readonly",
            command=self._on_chofer_selected,
            width=250
        )
        self.combo_choferes.grid(row=0, column=2, sticky="e")

        # Contenedor de Tarjetas de Insights
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, padx=20, sticky="nsew")
        
        for i in range(5):
            self.cards_frame.grid_columnconfigure(i, weight=1)

        # Crear tarjetas de métricas
        self.lbl_viajes = self._create_metric_card(self.cards_frame, 0, "Viajes Hoy", "0")
        self.lbl_efectivo = self._create_metric_card(self.cards_frame, 1, "Efectivo", "$0", "#2ecc71")
        self.lbl_transf = self._create_metric_card(self.cards_frame, 2, "Transferencias", "$0", "#9b59b6")
        self.lbl_fiados = self._create_metric_card(self.cards_frame, 3, "Fiados", "$0", "#e67e22")
        self.lbl_neto = self._create_metric_card(self.cards_frame, 4, "NETO CAJA", "$0", "#f1c40f")

        # Historial del chofer
        self.history_frame = ctk.CTkScrollableFrame(self, label_text="Últimos viajes del día")
        self.history_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.grid_rowconfigure(2, weight=3)
        self.history_frame.grid_columnconfigure(0, weight=1)

    def _create_metric_card(self, parent, col, title, initial_val, color="white"):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e272e")
        card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(15, 5))
        lbl_val = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
        lbl_val.pack(pady=(0, 15))
        return lbl_val

    def load_data(self):
        """Carga los choferes en el combo y actualiza los insights."""
        choferes = models.get_choferes()
        # Filtrar solo los activos, o todos? Usualmente se quiere ver de los activos hoy.
        nombres = ["Todos los choferes"] + [f"[{c['movil']}] {c['nombre']}" for c in choferes]
        self.combo_choferes.configure(values=nombres)
        
        if self.chofer_var.get() not in nombres:
            self.chofer_var.set("Todos los choferes")
            
        self._update_stats()

    def _on_chofer_selected(self, choice):
        self._update_stats()

    def _update_stats(self):
        # 1. Obtener stats generales o por chofer
        chofer_id = None
        sel = self.chofer_var.get()
        if sel != "Todos los choferes":
            movil = sel.split("]")[0].replace("[", "").strip()
            choferes = models.get_choferes()
            for c in choferes:
                if str(c["movil"]) == movil:
                    chofer_id = c["id"]
                    break

        stats = models.get_daily_stats(chofer_id)
        
        self.lbl_viajes.configure(text=f"{stats['viajes_hechos']}")
        self.lbl_efectivo.configure(text=f"${stats['efectivo']:.2f}")
        self.lbl_transf.configure(text=f"${stats['transferencia']:.2f}")
        self.lbl_fiados.configure(text=f"${stats['fiados']:.2f}")
        self.lbl_neto.configure(text=f"${stats['neto']:.2f}")

        # 2. Cargar lista de viajes del día para este contexto
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        viajes_hoy = models.get_viajes_hoy(chofer_id)
        if not viajes_hoy:
            ctk.CTkLabel(self.history_frame, text="No hay viajes registrados hoy.", text_color="gray").grid(row=0, column=0, pady=20)
            return

        # Configurar las columnas de la tabla de forma uniforme
        for i in range(5):
            self.history_frame.grid_columnconfigure(i, weight=1)

        # Encabezados
        headers = ["Hora", "Móvil / Chofer", "Trayecto", "Monto", "Estado"]
        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.history_frame, text=h, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=col, sticky="w", padx=5, pady=(0, 10))

        # Filas de datos
        for row_idx, v in enumerate(viajes_hoy, start=1):
            hora = v["updated_at"].split(" ")[1][:5] if " " in v["updated_at"] else v["updated_at"]
            color = "#2ecc71" if v["estado"] == "Finalizado" else "#e74c3c"
            
            ctk.CTkLabel(self.history_frame, text=hora).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
            ctk.CTkLabel(self.history_frame, text=f"[{v['chofer_movil']}] {v['chofer_nombre']}").grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)
            ctk.CTkLabel(self.history_frame, text=f"{v['origen']} ➔ {v['destino'] or 'Pend.'}").grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)
            ctk.CTkLabel(self.history_frame, text=f"${v['monto']} ({v['metodo_pago']})").grid(row=row_idx, column=3, sticky="w", padx=5, pady=2)
            ctk.CTkLabel(self.history_frame, text=v["estado"], text_color=color).grid(row=row_idx, column=4, sticky="e", padx=5, pady=2)
