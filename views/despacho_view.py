"""
Vista de Despacho Operativo Rediseñada.
Flujo rápido mediante "Chips" de choferes libres y vista limpia de viajes activos.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from database import models
import tkinter.messagebox as messagebox

class DespachoView(ctk.CTkFrame):
    def __init__(self, master, get_operador_actual_cb, **kwargs):
        super().__init__(master, **kwargs)
        self.get_operador_actual_cb = get_operador_actual_cb 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) # Formulario (aprox 30%)
        self.grid_columnconfigure(1, weight=3) # Panel de flota (aprox 70%)

        self.timer_id = None
        self.choferes_activos = []
        
        # Guardar estado de la interfaz de cada tarjeta para flujos inline
        self.card_states = {}
        # Variables temporales para el inline de finalización
        self.finalizar_vars = {} 

        self._build_form()
        self._build_flota_panel()
        self.load_data()
        self._update_timers()

    def _build_form(self):
        """Panel Izquierdo: Formulario de Despacho y Chips de Disponibles."""
        self.form_frame = ctk.CTkFrame(self, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        
        # Hacemos que la columna 0 se expanda para que los inputs ocupen todo el ancho
        self.form_frame.grid_columnconfigure(0, weight=1)
        # Hacemos que la fila de los chips (6) ocupe todo el espacio vertical restante
        self.form_frame.grid_rowconfigure(6, weight=1)

        lbl_titulo = ctk.CTkLabel(self.form_frame, text="NUEVO VIAJE", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.grid(row=0, column=0, pady=(20, 20))

        self.entry_origen = ctk.CTkEntry(self.form_frame, placeholder_text="Origen (Obligatorio)", font=ctk.CTkFont(size=16), height=40)
        self.entry_origen.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.entry_destino = ctk.CTkEntry(self.form_frame, placeholder_text="Destino (Opcional)", font=ctk.CTkFont(size=16), height=40)
        self.entry_destino.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.entry_cliente = ctk.CTkEntry(self.form_frame, placeholder_text="Cliente (Opcional)", font=ctk.CTkFont(size=16), height=40)
        self.entry_cliente.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.msg_label = ctk.CTkLabel(self.form_frame, text="", text_color="red")
        self.msg_label.grid(row=4, column=0, pady=(5,0))

        # --- Sección Choferes Disponibles (Chips) ---
        lbl_disp = ctk.CTkLabel(self.form_frame, text="Choferes Disponibles", font=ctk.CTkFont(size=16, weight="bold"), text_color="gray")
        lbl_disp.grid(row=5, column=0, pady=(20, 5), sticky="n")

        self.chips_frame = ctk.CTkScrollableFrame(self.form_frame, fg_color="transparent")
        self.chips_frame.grid(row=6, column=0, padx=10, pady=5, sticky="nsew")

    def _build_flota_panel(self):
        """Panel Derecho: Tarjetas de Flota Activa."""
        self.flota_frame = ctk.CTkScrollableFrame(self, corner_radius=10, label_text="Viajes en Curso", label_font=ctk.CTkFont(size=18, weight="bold"))
        self.flota_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.flota_frame.grid_columnconfigure(0, weight=1)

    def load_data(self):
        """Obtiene el estado de la flota y dibuja chips y tarjetas."""
        for widget in self.flota_frame.winfo_children():
            widget.destroy()
        for widget in self.chips_frame.winfo_children():
            widget.destroy()

        self.choferes_activos = models.get_flota_status()
        self.timer_labels = []

        # Separar libres y ocupados
        libres = []
        ocupados = []

        for c in self.choferes_activos:
            if c["viaje_actual"] is None and not c["viajes_pendientes"]:
                libres.append(c)
            else:
                ocupados.append(c)

        # Ordenar ocupados: 1. Activos (con viaje_actual), 2. Pausados (sin viaje actual pero con pendientes)
        ocupados.sort(key=lambda x: 0 if x["viaje_actual"] is not None else 1)

        # --- Dibujar Chips (Libres) ---
        # Grid layout para los chips (2 columnas por fila para aprovechar el espacio)
        col_count = 0
        row_count = 0
        self.chips_frame.grid_columnconfigure(0, weight=1)
        self.chips_frame.grid_columnconfigure(1, weight=1)

        for c in libres:
            texto_chip = f"🚖 {c['movil']} - {c['nombre']}\n🟢 Libre"
            btn_chip = ctk.CTkButton(
                self.chips_frame, 
                text=texto_chip, 
                font=ctk.CTkFont(weight="bold"),
                fg_color="#34495e", 
                hover_color="#2c3e50",
                border_width=2,
                border_color="#2ecc71",
                command=lambda cid=c["id"]: self._on_chip_click(cid)
            )
            btn_chip.grid(row=row_count, column=col_count, padx=5, pady=5, sticky="ew")
            
            col_count += 1
            if col_count > 1:
                col_count = 0
                row_count += 1

        if not libres:
            ctk.CTkLabel(self.chips_frame, text="No hay choferes libres.", text_color="gray").grid(row=0, column=0, columnspan=2, pady=20)

        # --- Dibujar Tarjetas (Ocupados) ---
        for i, chofer in enumerate(ocupados):
            self._draw_ocupado_card(chofer, i)

    def _draw_ocupado_card(self, chofer, row_index):
        chofer_id = chofer["id"]
        state = self.card_states.get(chofer_id, "normal")
        is_busy = chofer["viaje_actual"] is not None
        border_color = "#f1c40f" if is_busy else "#e67e22" # Amarillo si viaja, Naranja si pausado
        
        card = ctk.CTkFrame(self.flota_frame, border_width=2, border_color=border_color, corner_radius=10)
        card.grid(row=row_index, column=0, padx=10, pady=10, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # --- Info Básica ---
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nw")

        lbl_movil = ctk.CTkLabel(info_frame, text=f"[{chofer['movil']}]", font=ctk.CTkFont(size=28, weight="bold"), text_color=border_color)
        lbl_movil.pack(anchor="w")
        
        lbl_nombre = ctk.CTkLabel(info_frame, text=chofer["nombre"], font=ctk.CTkFont(size=16))
        lbl_nombre.pack(anchor="w")

        estado_txt = "EN VIAJE" if is_busy else "PAUSADO"
        if state == "preguntar_siguiente":
            estado_txt = "ESPERANDO CONFIRMACIÓN"
        lbl_estado = ctk.CTkLabel(info_frame, text=estado_txt, font=ctk.CTkFont(size=14, weight="bold"), text_color=border_color)
        lbl_estado.pack(anchor="w", pady=(10, 0))

        if is_busy:
            inicio_str = chofer["viaje_actual"]["created_at"]
            lbl_tiempo = ctk.CTkLabel(info_frame, text="00:00", font=ctk.CTkFont(size=24, weight="bold"))
            lbl_tiempo.pack(anchor="w")
            self.timer_labels.append({"label": lbl_tiempo, "inicio": inicio_str})

        # --- Detalles del Viaje y Cola ---
        detalles_frame = ctk.CTkFrame(card, fg_color="transparent")
        detalles_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # MODO PREGUNTAR SIGUIENTE
        if state == "preguntar_siguiente":
            ctk.CTkLabel(detalles_frame, text="Viaje finalizado con éxito.", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=5)
            ctk.CTkLabel(detalles_frame, text="Este chofer tiene viajes pendientes en cola. ¿Desea iniciar el próximo ahora?", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
            
            btn_frame = ctk.CTkFrame(detalles_frame, fg_color="transparent")
            btn_frame.pack(anchor="w", pady=10)
            
            if chofer["viajes_pendientes"]:
                next_v_id = chofer["viajes_pendientes"][0]["id"]
                ctk.CTkButton(btn_frame, text="▶ Iniciar Siguiente", fg_color="#3498db", hover_color="#2980b9", width=150, command=lambda c=chofer_id, v=next_v_id: self._on_iniciar_pendiente_from_prompt(c, v)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="Mantener en Cola", fg_color="gray", hover_color="darkgray", width=150, command=lambda c=chofer_id: self._cancel_prompt(c)).pack(side="left", padx=5)
        else:
            # MODO NORMAL O FINALIZANDO
            if is_busy:
                v_actual = chofer["viaje_actual"]
                ctk.CTkLabel(detalles_frame, text="Viaje Actual:", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
                
                origen = v_actual['origen']
                destino = v_actual['destino'] if v_actual['destino'] else "Destino pendiente"
                
                viaje_frame = ctk.CTkFrame(detalles_frame, fg_color="transparent")
                viaje_frame.pack(anchor="w", fill="x")
                ctk.CTkLabel(viaje_frame, text=f"📍 {origen} ➔ {destino}", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
                
                # Boton editar destino rápido
                ctk.CTkButton(viaje_frame, text="✏", width=30, height=20, fg_color="transparent", text_color="gray", hover_color="gray20", command=lambda v=v_actual["id"]: self._on_edit_destino_prompt(v)).pack(side="left", padx=5)

                if v_actual["cliente"]:
                    ctk.CTkLabel(detalles_frame, text=f"👤 {v_actual['cliente']}", font=ctk.CTkFont(size=14)).pack(anchor="w")
            
            # Próximos viajes en cola
            pendientes = chofer.get("viajes_pendientes", [])
            if pendientes:
                ctk.CTkLabel(detalles_frame, text="En cola (Pendientes):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f39c12").pack(anchor="w", pady=(10, 0))
                for p in pendientes:
                    pend_frame = ctk.CTkFrame(detalles_frame, fg_color="#34495e", corner_radius=5)
                    pend_frame.pack(anchor="w", fill="x", pady=2, ipadx=5, ipady=2)
                    
                    origen = p['origen']
                    destino = p['destino'] if p['destino'] else "Destino pendiente"
                    
                    ctk.CTkLabel(pend_frame, text=f"📍 {origen} ➔ {destino}", font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
                    
                    # Botones inline para el viaje pendiente
                    ctk.CTkButton(pend_frame, text="❌", width=25, height=20, fg_color="transparent", text_color="#e74c3c", command=lambda v=p["id"]: self._on_cancelar_pendiente(v)).pack(side="right", padx=2)
                    ctk.CTkButton(pend_frame, text="▲", width=25, height=20, fg_color="transparent", text_color="white", command=lambda v=p["id"]: self._on_priorizar_pendiente(v)).pack(side="right", padx=2)
                    ctk.CTkButton(pend_frame, text="✏", width=25, height=20, fg_color="transparent", text_color="gray", command=lambda v=p["id"]: self._on_edit_destino_prompt(v)).pack(side="right", padx=2)
                    if not is_busy:
                        # Si está pausado, puede forzar inicio manual
                        ctk.CTkButton(pend_frame, text="▶", width=25, height=20, fg_color="transparent", text_color="#2ecc71", command=lambda v=p["id"]: self._on_iniciar_pendiente_manual(v)).pack(side="right", padx=2)

        # --- Action Frame ---
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.grid(row=0, column=2, padx=15, pady=15, sticky="ne")

        if state == "normal":
            if is_busy:
                btn_fin = ctk.CTkButton(
                    action_frame, text="Finalizar", width=120, height=40,
                    fg_color="#e67e22", hover_color="#d35400", font=ctk.CTkFont(weight="bold"),
                    command=lambda c=chofer_id: self._start_finalizar(c)
                )
                btn_fin.pack(pady=5)
        elif state == "finalizando":
            # Formulario Inline de finalización
            v_id = chofer["viaje_actual"]["id"]
            ctk.CTkLabel(action_frame, text="Cerrar Viaje", font=ctk.CTkFont(weight="bold")).pack(pady=(0,5))
            
            entry_monto = ctk.CTkEntry(action_frame, placeholder_text="Monto ($)", width=120)
            entry_monto.pack(pady=2)
            
            entry_cliente = ctk.CTkEntry(action_frame, placeholder_text="Nombre del Cliente", width=120)
            if chofer["viaje_actual"]["cliente"]:
                entry_cliente.insert(0, chofer["viaje_actual"]["cliente"])
            
            def on_pago_changed(choice, e_cli=entry_cliente):
                if choice != "Efectivo":
                    e_cli.pack(pady=2)
                else:
                    e_cli.pack_forget()

            combo_pago = ctk.CTkComboBox(
                action_frame, 
                values=["Efectivo", "Transferencia", "Cuenta Corriente"], 
                width=120, 
                state="readonly",
                command=on_pago_changed
            )
            combo_pago.set("Efectivo")
            combo_pago.pack(pady=2)
            
            entry_obs = ctk.CTkEntry(action_frame, placeholder_text="Recorrido / Pedido (Opc.)", width=120)
            entry_obs.pack(pady=2)
            
            self.finalizar_vars[chofer_id] = {
                "monto": entry_monto, 
                "pago": combo_pago, 
                "cliente": entry_cliente,
                "obs": entry_obs,
                "v_id": v_id
            }
            
            btn_confirm = ctk.CTkButton(
                action_frame, text="Confirmar", width=120, fg_color="#2ecc71", hover_color="#27ae60",
                command=lambda c=chofer_id: self._commit_finalizar(c)
            )
            btn_confirm.pack(pady=5)
            
            btn_cancel = ctk.CTkButton(
                action_frame, text="Cancelar", width=120, fg_color="transparent", border_width=1,
                command=lambda c=chofer_id: self._cancel_finalizar(c)
            )
            btn_cancel.pack()

    def _update_timers(self):
        for item in self.timer_labels:
            try:
                inicio = datetime.strptime(item["inicio"], "%Y-%m-%d %H:%M:%S")
                ahora = datetime.now()
                # CORRECCIÓN: Si el delta es negativo (por pequeña desincronización de timezone), forzar a 0.
                delta = ahora - inicio
                if delta.total_seconds() < 0:
                    delta = timedelta(0)
                
                minutos = int(delta.total_seconds() // 60)
                segundos = int(delta.total_seconds() % 60)
                
                if minutos > 59:
                    horas = minutos // 60
                    minutos = minutos % 60
                    tiempo_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                else:
                    tiempo_str = f"{minutos:02d}:{segundos:02d}"
                
                item["label"].configure(text=tiempo_str)
            except Exception as e:
                pass

        self.timer_id = self.after(1000, self._update_timers)

    def destroy(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
        super().destroy()

    # --- Lógica de Creación vía Chips ---
    def _on_chip_click(self, chofer_id):
        origen = self.entry_origen.get().strip()
        destino = self.entry_destino.get().strip()
        cliente = self.entry_cliente.get().strip()
        operador = self.get_operador_actual_cb()

        if not origen:
            self.msg_label.configure(text="El Origen es obligatorio.", text_color="red")
            return
        if not operador or "Operador" in operador or "Sin " in operador:
            self.msg_label.configure(text="Debe seleccionar un Operador en la barra lateral.", text_color="red")
            return

        ops = models.get_operadores()
        op_id = next((op["id"] for op in ops if op["nombre"] == operador), None)
        if not op_id: return

        try:
            models.create_viaje(op_id, chofer_id, origen, destino, cliente)
            self.entry_origen.delete(0, 'end')
            self.entry_destino.delete(0, 'end')
            self.entry_cliente.delete(0, 'end')
            self.msg_label.configure(text="")
            self.load_data()
        except Exception as e:
            self.msg_label.configure(text=f"Error: {e}", text_color="red")

    # --- Eventos Inline Finalización ---
    def _start_finalizar(self, chofer_id):
        self.card_states[chofer_id] = "finalizando"
        self.load_data()

    def _cancel_finalizar(self, chofer_id):
        self.card_states[chofer_id] = "normal"
        if chofer_id in self.finalizar_vars:
            del self.finalizar_vars[chofer_id]
        self.load_data()

    def _commit_finalizar(self, chofer_id):
        vars_dict = self.finalizar_vars.get(chofer_id)
        if not vars_dict: return
        
        monto_str = vars_dict["monto"].get().strip()
        metodo = vars_dict["pago"].get()
        cliente_nombre = vars_dict["cliente"].get().strip()
        observaciones = vars_dict["obs"].get().strip()
        v_id = vars_dict["v_id"]
        
        if metodo != "Efectivo" and not cliente_nombre:
            vars_dict["cliente"].configure(border_color="red")
            return
        
        try:
            monto = float(monto_str) if monto_str else 0.0
        except ValueError:
            vars_dict["monto"].configure(border_color="red")
            return
            
        models.finalizar_viaje(v_id, monto, metodo, cliente_nombre, observaciones)
        del self.finalizar_vars[chofer_id]
        
        chofer = next((c for c in self.choferes_activos if c["id"] == chofer_id), None)
        if chofer and chofer.get("viajes_pendientes"):
            self.card_states[chofer_id] = "preguntar_siguiente"
        else:
            self.card_states[chofer_id] = "normal"
            
        self.load_data()

    def _on_iniciar_pendiente_from_prompt(self, chofer_id, viaje_id):
        models.iniciar_viaje_pendiente(viaje_id)
        self.card_states[chofer_id] = "normal"
        self.load_data()

    def _cancel_prompt(self, chofer_id):
        self.card_states[chofer_id] = "normal"
        self.load_data()

    # --- Eventos Edición y Cola ---
    def _on_edit_destino_prompt(self, viaje_id):
        dialog = ctk.CTkInputDialog(text="Ingrese el nuevo destino:", title="Editar Destino")
        nuevo = dialog.get_input()
        if nuevo is not None:
            models.edit_destino(viaje_id, nuevo.strip())
            self.load_data()

    def _on_cancelar_pendiente(self, viaje_id):
        models.cancelar_viaje(viaje_id)
        self.load_data()

    def _on_priorizar_pendiente(self, viaje_id):
        models.priorizar_viaje(viaje_id)
        self.load_data()

    def _on_iniciar_pendiente_manual(self, viaje_id):
        models.iniciar_viaje_pendiente(viaje_id)
        self.load_data()
