"""
Vista de Despacho Operativo.
Panel principal donde se crean los viajes y se visualiza el estado de toda la flota.
"""

import customtkinter as ctk
from datetime import datetime
from database import models
import tkinter.messagebox as messagebox

class DespachoView(ctk.CTkFrame):
    def __init__(self, master, get_operador_actual_cb, **kwargs):
        super().__init__(master, **kwargs)
        self.get_operador_actual_cb = get_operador_actual_cb # Función para obtener el operador de la ventana principal
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) # Formulario (25%)
        self.grid_columnconfigure(1, weight=3) # Panel de flota (75%)

        self.timer_id = None
        self.choferes_activos = []

        self._build_form()
        self._build_flota_panel()
        self.load_data()
        self._update_timers()

    def _build_form(self):
        """Panel Izquierdo: Formulario rápido de Despacho."""
        self.form_frame = ctk.CTkFrame(self, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Título
        lbl_titulo = ctk.CTkLabel(self.form_frame, text="NUEVO VIAJE", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.pack(pady=(20, 30))

        # Origen
        self.entry_origen = ctk.CTkEntry(self.form_frame, placeholder_text="Origen", font=ctk.CTkFont(size=16), height=40)
        self.entry_origen.pack(padx=20, pady=10, fill="x")

        # Destino
        self.entry_destino = ctk.CTkEntry(self.form_frame, placeholder_text="Destino", font=ctk.CTkFont(size=16), height=40)
        self.entry_destino.pack(padx=20, pady=10, fill="x")

        # Cliente
        self.entry_cliente = ctk.CTkEntry(self.form_frame, placeholder_text="Cliente (Opcional)", font=ctk.CTkFont(size=16), height=40)
        self.entry_cliente.pack(padx=20, pady=10, fill="x")

        # Chofer (Desplegable)
        self.chofer_var = ctk.StringVar(value="Seleccionar Móvil...")
        self.chofer_combo = ctk.CTkComboBox(self.form_frame, variable=self.chofer_var, font=ctk.CTkFont(size=16), height=40, state="readonly")
        self.chofer_combo.pack(padx=20, pady=20, fill="x")

        # Botón Despachar
        self.btn_despachar = ctk.CTkButton(
            self.form_frame, 
            text="DESPACHAR VIAJE", 
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._on_despachar
        )
        self.btn_despachar.pack(padx=20, pady=30, fill="x")

        self.msg_label = ctk.CTkLabel(self.form_frame, text="", text_color="red")
        self.msg_label.pack(pady=10)

    def _build_flota_panel(self):
        """Panel Derecho: Tarjetas de Flota."""
        self.flota_frame = ctk.CTkScrollableFrame(self, corner_radius=10, label_text="Estado de Flota", label_font=ctk.CTkFont(size=18, weight="bold"))
        self.flota_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.flota_frame.grid_columnconfigure(0, weight=1)

    def load_data(self):
        """Obtiene el estado de la flota de la BD y dibuja las tarjetas."""
        # Limpiar panel actual
        for widget in self.flota_frame.winfo_children():
            widget.destroy()

        self.choferes_activos = models.get_flota_status()

        # Actualizar Combo de Formulario
        nombres_combo = [f"[Móvil {c['movil']}] {c['nombre']}" for c in self.choferes_activos]
        if nombres_combo:
            self.chofer_combo.configure(values=nombres_combo)
            if self.chofer_var.get() not in nombres_combo:
                self.chofer_var.set("Seleccionar Móvil...")
        else:
            self.chofer_combo.configure(values=["Sin choferes activos"])
            self.chofer_var.set("Sin choferes activos")

        # Dibujar tarjetas de choferes
        self.timer_labels = [] # Guardamos referencias a los labels de tiempo para actualizarlos

        for i, chofer in enumerate(self.choferes_activos):
            # El color del borde indicará el estado
            is_busy = chofer["viaje_actual"] is not None
            border_color = "#f1c40f" if is_busy else "#2ecc71" # Amarillo ocupado, Verde libre
            
            card = ctk.CTkFrame(self.flota_frame, border_width=2, border_color=border_color, corner_radius=10)
            card.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            # --- Info Básica ---
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nw")

            # Movil grande
            lbl_movil = ctk.CTkLabel(info_frame, text=f"[{chofer['movil']}]", font=ctk.CTkFont(size=28, weight="bold"), text_color=border_color)
            lbl_movil.pack(anchor="w")
            
            lbl_nombre = ctk.CTkLabel(info_frame, text=chofer["nombre"], font=ctk.CTkFont(size=16))
            lbl_nombre.pack(anchor="w")

            estado_txt = "EN VIAJE" if is_busy else "LIBRE"
            lbl_estado = ctk.CTkLabel(info_frame, text=estado_txt, font=ctk.CTkFont(size=14, weight="bold"), text_color=border_color)
            lbl_estado.pack(anchor="w", pady=(10, 0))

            # --- Cronómetro ---
            if is_busy:
                # Guardamos la fecha de inicio y la etiqueta para el actualizador
                inicio_str = chofer["viaje_actual"]["created_at"]
                lbl_tiempo = ctk.CTkLabel(info_frame, text="00:00", font=ctk.CTkFont(size=24, weight="bold"))
                lbl_tiempo.pack(anchor="w")
                self.timer_labels.append({"label": lbl_tiempo, "inicio": inicio_str})

            # --- Detalles del Viaje ---
            detalles_frame = ctk.CTkFrame(card, fg_color="transparent")
            detalles_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

            if is_busy:
                v_actual = chofer["viaje_actual"]
                ctk.CTkLabel(detalles_frame, text="Viaje Actual:", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
                ctk.CTkLabel(detalles_frame, text=f"📍 {v_actual['origen']} ➔ {v_actual['destino']}", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
                if v_actual["cliente"]:
                    ctk.CTkLabel(detalles_frame, text=f"👤 {v_actual['cliente']}", font=ctk.CTkFont(size=14)).pack(anchor="w")
            
            # Próximo viaje en cola
            if chofer["viaje_pendiente"]:
                v_pend = chofer["viaje_pendiente"]
                pend_frame = ctk.CTkFrame(detalles_frame, fg_color="#34495e", corner_radius=5)
                pend_frame.pack(anchor="w", fill="x", pady=(10, 0), ipadx=10, ipady=5)
                ctk.CTkLabel(pend_frame, text="En cola (Próximo):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f39c12").pack(anchor="w")
                ctk.CTkLabel(pend_frame, text=f"📍 {v_pend['origen']} ➔ {v_pend['destino']}", font=ctk.CTkFont(size=14)).pack(anchor="w")

            # --- Botones de Acción ---
            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.grid(row=0, column=2, padx=15, pady=15, sticky="e")

            if is_busy:
                # Botón Finalizar
                btn_fin = ctk.CTkButton(
                    action_frame, text="Finalizar", width=120, height=40,
                    fg_color="#e67e22", hover_color="#d35400", font=ctk.CTkFont(weight="bold"),
                    command=lambda v_id=chofer["viaje_actual"]["id"]: self._on_finalizar(v_id)
                )
                btn_fin.pack(pady=5)
            elif chofer["viaje_pendiente"]:
                # Si esta libre pero tiene pendiente
                btn_iniciar = ctk.CTkButton(
                    action_frame, text="Iniciar Próximo", width=120, height=40,
                    fg_color="#3498db", hover_color="#2980b9", font=ctk.CTkFont(weight="bold"),
                    command=lambda v_id=chofer["viaje_pendiente"]["id"]: self._on_iniciar_pendiente(v_id)
                )
                btn_iniciar.pack(pady=5)

    def _update_timers(self):
        """Actualiza los cronómetros de las tarjetas activas cada segundo."""
        for item in self.timer_labels:
            try:
                # SQLite datetime str: "YYYY-MM-DD HH:MM:SS"
                inicio = datetime.strptime(item["inicio"], "%Y-%m-%d %H:%M:%S")
                ahora = datetime.now()
                delta = ahora - inicio
                
                # Formatear a MM:SS
                minutos = int(delta.total_seconds() // 60)
                segundos = int(delta.total_seconds() % 60)
                
                # Si lleva más de una hora
                if minutos > 59:
                    horas = minutos // 60
                    minutos = minutos % 60
                    tiempo_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                else:
                    tiempo_str = f"{minutos:02d}:{segundos:02d}"
                
                item["label"].configure(text=tiempo_str)
            except Exception as e:
                pass # Ignoramos errores de parseo por seguridad

        # Volver a llamar a esta función en 1 segundo (1000 ms)
        self.timer_id = self.after(1000, self._update_timers)

    def destroy(self):
        """Detiene el timer si la vista se destruye."""
        if self.timer_id:
            self.after_cancel(self.timer_id)
        super().destroy()

    # --- Eventos ---

    def _on_despachar(self):
        origen = self.entry_origen.get().strip()
        destino = self.entry_destino.get().strip()
        cliente = self.entry_cliente.get().strip()
        chofer_combo = self.chofer_var.get()
        operador = self.get_operador_actual_cb()

        if not origen or not destino:
            self.msg_label.configure(text="Origen y Destino son obligatorios.", text_color="red")
            return
        if not operador or "Operador" in operador or "Sin " in operador:
            self.msg_label.configure(text="Debe seleccionar un Operador en la barra lateral.", text_color="red")
            return
        if "Móvil" not in chofer_combo:
            self.msg_label.configure(text="Debe seleccionar un Móvil válido.", text_color="red")
            return

        # Extraer el ID del chofer (buscamos en la lista original)
        # El string es: "[Móvil 14] Juan"
        chofer_id = None
        for c in self.choferes_activos:
            if f"[Móvil {c['movil']}] {c['nombre']}" == chofer_combo:
                chofer_id = c["id"]
                break
        
        if not chofer_id:
            return

        # Asumimos que podemos obtener el id del operador desde models
        # Para evitar complejidades de UI, buscamos el id del operador por nombre
        ops = models.get_operadores()
        op_id = next((op["id"] for op in ops if op["nombre"] == operador), None)
        if not op_id:
            return

        try:
            models.create_viaje(op_id, chofer_id, origen, destino, cliente)
            # Limpiar inputs
            self.entry_origen.delete(0, 'end')
            self.entry_destino.delete(0, 'end')
            self.entry_cliente.delete(0, 'end')
            self.msg_label.configure(text="Viaje despachado correctamente.", text_color="green")
            # Recargar panel
            self.load_data()
        except Exception as e:
            self.msg_label.configure(text=f"Error: {e}", text_color="red")

    def _on_finalizar(self, viaje_id):
        # Dialogo simple para ingresar el monto (Regla del monto al final)
        dialog = ctk.CTkInputDialog(text="Ingrese el monto cobrado ($):", title="Finalizar Viaje")
        monto_str = dialog.get_input()

        if monto_str is None: # El usuario canceló
            return
            
        try:
            monto = float(monto_str) if monto_str.strip() else 0.0
        except ValueError:
            messagebox.showerror("Error", "Monto inválido. Ingrese un número.")
            return

        models.finalizar_viaje(viaje_id, monto)
        self.load_data()

    def _on_iniciar_pendiente(self, viaje_id):
        # Regla 5: Confirmación simple Sí/Cancelar
        # CustomTkinter no tiene YesNo nativo, usamos messagebox de tkinter (es sutil y nativo)
        respuesta = messagebox.askyesno("Iniciar Viaje", "¿Desea iniciar el viaje en cola?")
        if respuesta:
            models.iniciar_viaje_pendiente(viaje_id)
            self.load_data()
