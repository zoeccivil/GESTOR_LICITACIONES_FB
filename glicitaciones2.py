class VentanaMaestroCompetidores(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.competidores_copia = [dict(c) for c in self.parent_app.competidores_maestros]
        self.competidores_filtrados = self.competidores_copia

        self.title("Catálogo de Competidores")
        self.geometry("900x550") # Un poco más ancha para las nuevas columnas
        self.grab_set()

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Campo de búsqueda
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text="🔍 Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_var.trace_add("write", self.filtrar_lista)
        
        # Treeview con nuevas columnas
        tree_frame = ttk.LabelFrame(main_frame, text="Competidores Registrados", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        cols = ('nombre', 'rnc', 'rpe', 'representante') # <-- COLUMNAS ACTUALIZADAS
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.heading('nombre', text='Nombre')
        self.tree.heading('rnc', text='RNC')
        self.tree.heading('rpe', text='No. RPE')
        self.tree.heading('representante', text='Representante')
        
        self.tree.column('nombre', width=250)
        self.tree.column('rnc', width=120)
        self.tree.column('rpe', width=120)
        self.tree.column('representante', width=200)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        # Botones (sin cambios en su creación)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        btn_frame.columnconfigure(tuple(range(4)), weight=1)
        ttk.Button(btn_frame, text="Agregar", command=self.agregar).grid(row=0, column=0, sticky=tk.EW, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.editar).grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.btn_ver_perfil = ttk.Button(btn_frame, text="📈 Ver Perfil", command=self.ver_perfil, state="disabled")
        self.btn_ver_perfil.grid(row=0, column=2, sticky=tk.EW, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar).grid(row=0, column=3, sticky=tk.EW, padx=5)
        ttk.Button(main_frame, text="✅ Guardar Cambios y Cerrar", command=self.cerrar_y_guardar).pack(pady=(10,0), ipady=4)
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.actualizar_lista()
# In gestor_licitaciones_db.py, add this new method to VentanaMaestroCompetidores

    def filtrar_lista(self, *args):
        termino = self.search_var.get().lower()
        if not termino:
            # If the search box is empty, show all competitors
            self.competidores_filtrados = self.competidores_copia
        else:
            # Otherwise, filter the list by name or RNC
            self.competidores_filtrados = [
                c for c in self.competidores_copia
                if termino in c.get('nombre', '').lower() or termino in c.get('rnc', '').lower()
            ]
        self.actualizar_lista()

# Esta es la única versión de actualizar_lista que debe existir en VentanaMaestroCompetidores

# En gestor_licitaciones_db.py, clase VentanaMaestroCompetidores, reemplaza actualizar_lista

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        for comp in sorted(self.competidores_filtrados, key=lambda x: x['nombre']):
            # Añadir los nuevos valores a la tabla
            values = (
                comp.get('nombre', ''), 
                comp.get('rnc', ''),
                comp.get('rpe', ''),
                comp.get('representante', '')
            )
            self.tree.insert('', tk.END, iid=comp['nombre'], values=values)
        self._on_selection_change()
        
    def _on_selection_change(self, event=None):
        """Habilita o deshabilita el botón 'Ver Perfil' según la selección."""
        if self.tree.selection():
            self.btn_ver_perfil.config(state="normal")
        else:
            self.btn_ver_perfil.config(state="disabled")

    def ver_perfil(self):
        """Abre la ventana del perfil del competidor seleccionado."""
        if not self.tree.selection(): return
        
        nombre_competidor = self.tree.item(self.tree.selection()[0], 'values')[0]
        VentanaPerfilCompetidor(self, nombre_competidor, self.parent_app.gestor_licitaciones)




# In VentanaMaestroCompetidores, replace the 'agregar', 'editar', and 'eliminar' methods

    def agregar(self):
        data = DialogoGestionarEntidad(self, "Agregar Competidor", "competidor").result
        if data and data.get('nombre'):
            if any(c['nombre'].lower() == data['nombre'].lower() for c in self.competidores_copia):
                messagebox.showerror("Error", "Ya existe un competidor con ese nombre.", parent=self)
                return
            
            # Check for duplicate RNC only if it's provided
            if data.get('rnc') and any(c.get('rnc', '').lower() == data['rnc'].lower() and c.get('rnc', '') for c in self.competidores_copia):
                messagebox.showerror("Error", "Ya existe un competidor con ese RNC.", parent=self)
                return

            self.competidores_copia.append(data)
            self.filtrar_lista() # Re-apply filter to show the new item

    def editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Por favor, selecciona un competidor para editar.", parent=self)
            return
            
        nombre_actual = self.tree.item(sel[0])['values'][0]
        competidor_actual = next((c for c in self.competidores_copia if c['nombre'] == nombre_actual), None)
        if not competidor_actual:
            return

        data = DialogoGestionarEntidad(self, "Editar Competidor", "competidor", initial_data=competidor_actual).result
        if data and data.get('nombre'):
            competidor_actual.update(data)
            self.filtrar_lista() # Re-apply filter

    def eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Por favor, selecciona un competidor para eliminar.", parent=self)
            return

        nombre_a_eliminar = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que quieres eliminar a '{nombre_a_eliminar}' del catálogo maestro?", parent=self):
            self.competidores_copia = [c for c in self.competidores_copia if c['nombre'] != nombre_a_eliminar]
            self.filtrar_lista() # Re-apply filter

    def cerrar_y_guardar(self):
        # Actualiza la lista maestra en sitio (no cambies la referencia)
        self.parent_app.competidores_maestros[:] = self.competidores_copia

        # Guardar SOLO el catálogo de competidores como reemplazo total
        self.parent_app.db.save_master_lists(
            empresas=self.parent_app.empresas_registradas,
            instituciones=self.parent_app.instituciones_registradas,
            documentos_maestros=self.parent_app.documentos_maestros,
            competidores_maestros=self.parent_app.competidores_maestros,
            responsables_maestros=self.parent_app.responsables_maestros,
            replace_tables={'competidores_maestros'}
        )

        self.destroy()

class VentanaPerfilCompetidor(tk.Toplevel):
    """Muestra un dashboard con estadísticas y el historial de un competidor."""
    def __init__(self, parent, competidor_nombre, todas_las_licitaciones):
        super().__init__(parent)
        self.competidor_nombre = competidor_nombre
        self.todas_las_licitaciones = todas_las_licitaciones

        # Intentar encontrar la DB en distintos niveles del padre
        self.db = (
            getattr(parent, "db", None)
            or getattr(getattr(parent, "parent_app", None), "db", None)
        )

        self.title(f"Perfil de Competidor: {self.competidor_nombre}")
        self.geometry("1100x700")
        self.grab_set()

        # 1) Procesar datos
        self.historial, self.kpis = self._procesar_historial()

        # 2) UI
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        kpi_frame = ttk.Frame(main_frame)
        kpi_frame.pack(fill=tk.X, pady=10)
        self.crear_widgets_kpi(kpi_frame)

        historial_frame = ttk.LabelFrame(
            main_frame,
            text="Historial de Participación (Doble clic para ver detalles)",
            padding=10
        )
        historial_frame.pack(fill=tk.BOTH, expand=True)
        self.crear_tabla_historial(historial_frame)

    # ------------------- Lógica -------------------

    def _procesar_historial(self):
        """
        Construye el historial del competidor y KPIs, detectando GANADORES por LOTE.
        Regla de detección por cada lote de la licitación:
        1) Si el lote tiene 'ganador_nombre' y coincide con el competidor => ganó ese lote.
        2) Si no hay 'ganador_nombre', pero en la oferta del competidor para ese lote existe o['ganador'] == True => ganó ese lote.
        """
        historial = []
        participaciones_por_institucion = {}

        total_participaciones = 0               # cuántas licitaciones participó este competidor (aparece en oferentes_participantes)
        total_licitaciones_ganadas = 0         # en cuántas licitaciones ganó al menos 1 lote
        total_lotes_ganados = 0                # suma de lotes ganados en todas las licitaciones
        monto_ofertado_total = 0

        estados_finalizados = ["Adjudicada", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]

        for lic in self.todas_las_licitaciones:
            # localizar al competidor en esta licitación
            oferente_obj = next((o for o in lic.oferentes_participantes if o.nombre == self.competidor_nombre), None)
            if not oferente_obj:
                continue  # este competidor no participó en esta licitación

            total_participaciones += 1

            # monto ofertado (tu método actual)
            try:
                monto_ofertado = oferente_obj.get_monto_total_ofertado(solo_habilitados=True)
            except Exception:
                monto_ofertado = sum((o.get('monto', 0) or 0) for o in getattr(oferente_obj, 'ofertas_por_lote', []))
            monto_ofertado_total += monto_ofertado

            # institución (para KPI de "institución favorita")
            institucion = lic.institucion
            participaciones_por_institucion[institucion] = participaciones_por_institucion.get(institucion, 0) + 1

            # ======== conteo de lotes ganados por esta licitación ========
            lotes_ganados_en_esta_lic = 0
            # 1) si en el objeto lote ya guardas ganador_nombre / ganado_por_nosotros:
            for lote in getattr(lic, 'lotes', []):
                ganador_nombre = getattr(lote, 'ganador_nombre', '') or ''
                if ganador_nombre:
                    if ganador_nombre == self.competidor_nombre:
                        lotes_ganados_en_esta_lic += 1
                    continue  # ya resuelto este lote

                # 2) si no hay ganador_nombre, revisa la oferta marcada como ganador en oferente_obj
                for o in getattr(oferente_obj, 'ofertas_por_lote', []):
                    if str(o.get('lote_numero')) == str(getattr(lote, 'numero', '')) and o.get('ganador'):
                        lotes_ganados_en_esta_lic += 1
                        break

            # Construir "resultado" amigable
            if lic.estado in estados_finalizados:
                if lotes_ganados_en_esta_lic > 0:
                    total_licitaciones_ganadas += 1
                    total_lotes_ganados += lotes_ganados_en_esta_lic
                    resultado = f"🏆 Ganador de {lotes_ganados_en_esta_lic} lote{'s' if lotes_ganados_en_esta_lic != 1 else ''}"
                else:
                    resultado = "Perdedor"
            else:
                # Si está en proceso igual queremos mostrar si ya hay radios marcados (opcional)
                if lotes_ganados_en_esta_lic > 0:
                    total_lotes_ganados += lotes_ganados_en_esta_lic
                    resultado = f"En Proceso (marcado {lotes_ganados_en_esta_lic} lote{'s' if lotes_ganados_en_esta_lic != 1 else ''})"
                else:
                    resultado = "En Proceso"

            historial.append({
                'proceso': lic.numero_proceso,
                'nombre': lic.nombre_proceso,
                'institucion': lic.institucion,
                'monto_ofertado': monto_ofertado,
                'resultado': resultado
            })

        # para tasa de éxito usamos solo licitaciones finalizadas en las que participó
        participaciones_finalizadas = sum(1 for item in historial if item['resultado'].startswith("🏆") or item['resultado'] == "Perdedor")

        kpis = {
            'participaciones': total_participaciones,
            'ganadas': total_licitaciones_ganadas,                     # cuántas lic ganó (>=1 lote)
            'lotes_ganados': total_lotes_ganados,                      # total de lotes ganados
            'tasa_exito': (total_licitaciones_ganadas / participaciones_finalizadas * 100) if participaciones_finalizadas > 0 else 0,
            'monto_promedio': (monto_ofertado_total / total_participaciones) if total_participaciones > 0 else 0,
            'top_institucion': max(participaciones_por_institucion, key=participaciones_por_institucion.get) if participaciones_por_institucion else "N/A"
        }

        return historial, kpis


    # ------------------- Widgets -------------------
    
    
    def crear_widgets_kpi(self, parent_frame):
        parent_frame.columnconfigure(tuple(range(7)), weight=1)

        kpi_widgets = [
            ("Participaciones Totales", f"{self.kpis['participaciones']}"),
            ("Licitaciones Ganadas", f"{self.kpis['ganadas']}"),
            ("Lotes Ganados", f"{self.kpis['lotes_ganados']}"),
            ("Tasa de Éxito", f"{self.kpis['tasa_exito']:.1f}%"),
            ("Monto Ofertado Promedio", f"RD$ {self.kpis['monto_promedio']:,.2f}"),
            ("Institución Favorita", self.kpis['top_institucion'])
        ]

        for i, (titulo, valor) in enumerate(kpi_widgets):
            frame = ttk.LabelFrame(parent_frame, text=titulo)
            frame.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            lbl = ttk.Label(frame, text=valor, font=("Helvetica", 14, "bold"), anchor="center")
            lbl.pack(pady=10, padx=10)

    def crear_tabla_historial(self, parent_frame):
        cols = ('proceso', 'institucion', 'nombre', 'monto', 'resultado')
        self.tree = ttk.Treeview(parent_frame, columns=cols, show="headings")

        self.tree.heading('proceso', text="Proceso");       self.tree.column('proceso', width=150)
        self.tree.heading('institucion', text="Institución"); self.tree.column('institucion', width=220)
        self.tree.heading('nombre', text="Nombre Licitación"); self.tree.column('nombre', width=380)
        self.tree.heading('monto', text="Monto Ofertado");     self.tree.column('monto', width=160, anchor=tk.E)
        self.tree.heading('resultado', text="Resultado");      self.tree.column('resultado', width=110, anchor=tk.CENTER)

        self.tree.tag_configure('ganador', background='#d4edda')

        # Doble clic: abrir reporte de licitación
        self.tree.bind("<Double-1>", self._abrir_reporte_licitacion)

        for item in self.historial:
            tags = ('ganador',) if item['resultado'] == "🏆 Ganador" else ()
            self.tree.insert(
                '', tk.END,
                values=(item['proceso'], item['institucion'], item['nombre'],
                        f"RD$ {item['monto_ofertado']:,.2f}", item['resultado']),
                tags=tags
            )
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _abrir_reporte_licitacion(self, event=None):
        if not self.tree.selection():
            return
        sel = self.tree.selection()[0]
        numero_proceso = self.tree.item(sel, 'values')[0]
        lic = next((l for l in self.todas_las_licitaciones if l.numero_proceso == numero_proceso), None)
        if lic:
            VentanaReporte(self, lic)
        else:
            messagebox.showwarning("No Encontrado",
                                   "No se pudo encontrar el registro completo de la licitación seleccionada.",
                                   parent=self)


import tkinter as tk
from tkinter import ttk

import tkinter as tk
from tkinter import ttk, messagebox

import tkinter as tk
from tkinter import ttk, messagebox

class VentanaPerfilEmpresaNuestra(tk.Toplevel):
    """Muestra un dashboard con estadísticas y el historial de una de nuestras empresas."""
    def __init__(self, parent, empresa_nombre, todas_las_licitaciones):
        super().__init__(parent)
        self.empresa_nombre = empresa_nombre
        self.todas_las_licitaciones = todas_las_licitaciones
        self.parent_app = parent # Guardamos referencia a la app principal

        self.title(f"Perfil de Empresa: {self.empresa_nombre}")
        self.geometry("1100x700")
        self.grab_set()

        # 1) Procesar datos
        self.historial, self.kpis = self._procesar_historial()

        # 2) UI
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        kpi_frame = ttk.Frame(main_frame)
        kpi_frame.pack(fill=tk.X, pady=10)
        self.crear_widgets_kpi(kpi_frame)

        historial_frame = ttk.LabelFrame(
            main_frame,
            text="Historial de Participación (Doble clic para ver detalles de la licitación)",
            padding=10
        )
        historial_frame.pack(fill=tk.BOTH, expand=True)
        self.crear_tabla_historial(historial_frame)


    def _procesar_historial(self):
        """
        Construye el historial de la empresa y sus KPIs, usando una lógica robusta
        para identificar licitaciones ganadas en consorcio.
        """
        historial = []
        participaciones_por_institucion = {}
        total_participaciones = 0
        total_licitaciones_ganadas = 0
        total_lotes_ganados = 0
        monto_adjudicado_total = 0.0
        estados_finalizados = ["Adjudicada", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]

        def _norm(s: str) -> str:
            s = (s or "").strip().replace("➡️", "").replace("(Nuestra Oferta)", "")
            while "  " in s:
                s = s.replace("  ", " ")
            return s.upper()

        for lic in self.todas_las_licitaciones:
            # --- INICIO DE CORRECCIÓN ---
            # Lógica mejorada para manejar consorcios (nombres separados por comas)
            nombres_empresas_participantes = set()
            for e in lic.empresas_nuestras:
                # Convertimos el objeto/diccionario a un string
                nombre_str = str(e)
                # Dividimos el string por si contiene varios nombres
                for nombre_individual in nombre_str.split(','):
                    nombre_limpio = nombre_individual.strip()
                    if nombre_limpio:
                        nombres_empresas_participantes.add(nombre_limpio)
            
            # Si la empresa de este perfil no está en el conjunto de participantes, saltamos la licitación
            if self.empresa_nombre not in nombres_empresas_participantes:
                continue
            # --- FIN DE CORRECCIÓN ---

            total_participaciones += 1
            institucion = lic.institucion
            participaciones_por_institucion[institucion] = participaciones_por_institucion.get(institucion, 0) + 1

            # El resto de la lógica que ya habíamos corregido para manejar consorcios se mantiene,
            # ahora funcionará correctamente porque la primera comprobación es la correcta.
            
            # Normalizamos los nombres de las empresas para la comparación de ganadores
            nuestras_empresas_en_lic_norm = {_norm(nombre) for nombre in nombres_empresas_participantes}
            ganadores_por_lote = {_norm(l.ganador_nombre) for l in lic.lotes if l.ganador_nombre}
            es_licitacion_ganada_por_grupo = any(ganador in nuestras_empresas_en_lic_norm for ganador in ganadores_por_lote)
            
            lotes_ganados_por_el_grupo = 0
            monto_adjudicado_en_esta_lic = 0.0

            if es_licitacion_ganada_por_grupo:
                total_licitaciones_ganadas += 1
                for lote in lic.lotes:
                    if _norm(lote.ganador_nombre) in nuestras_empresas_en_lic_norm:
                        lotes_ganados_por_el_grupo += 1
                        monto_adjudicado_en_esta_lic += lote.monto_ofertado
                
                total_lotes_ganados += lotes_ganados_por_el_grupo
                monto_adjudicado_total += monto_adjudicado_en_esta_lic

            resultado = "En Proceso"
            if lic.estado in estados_finalizados:
                if es_licitacion_ganada_por_grupo:
                    resultado = f"🏆 Ganador ({lotes_ganados_por_el_grupo} lote{'s' if lotes_ganados_por_el_grupo != 1 else ''})"
                else:
                    resultado = "Perdedor"

            historial.append({
                'proceso': lic.numero_proceso,
                'nombre': lic.nombre_proceso,
                'institucion': lic.institucion,
                'monto_adjudicado': monto_adjudicado_en_esta_lic,
                'resultado': resultado
            })

        participaciones_finalizadas = sum(1 for item in historial if item['resultado'].startswith("🏆") or item['resultado'] == "Perdedor")

        kpis = {
            'participaciones': total_participaciones,
            'licitaciones_ganadas': total_licitaciones_ganadas,
            'lotes_ganados': total_lotes_ganados,
            'tasa_exito': (total_licitaciones_ganadas / participaciones_finalizadas * 100) if participaciones_finalizadas > 0 else 0,
            'monto_adjudicado_total': monto_adjudicado_total,
            'top_institucion': max(participaciones_por_institucion, key=participaciones_por_institucion.get) if participaciones_por_institucion else "N/A"
        }
        return historial, kpis
    
    def crear_widgets_kpi(self, parent_frame):
        parent_frame.columnconfigure(tuple(range(6)), weight=1)
        kpi_widgets = [
            ("Participaciones", f"{self.kpis['participaciones']}"),
            ("Licitaciones Ganadas", f"{self.kpis['licitaciones_ganadas']}"),
            ("Lotes Ganados", f"{self.kpis['lotes_ganados']}"),
            ("Tasa de Éxito", f"{self.kpis['tasa_exito']:.1f}%"),
            ("Monto Total Adjudicado", f"RD$ {self.kpis['monto_adjudicado_total']:,.2f}"),
            ("Institución Frecuente", self.kpis['top_institucion'])
        ]
        for i, (titulo, valor) in enumerate(kpi_widgets):
            frame = ttk.LabelFrame(parent_frame, text=titulo)
            frame.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            lbl = ttk.Label(frame, text=valor, font=("Helvetica", 14, "bold"), anchor="center")
            lbl.pack(pady=10, padx=10)

    def crear_tabla_historial(self, parent_frame):
        cols = ('proceso', 'institucion', 'nombre', 'monto', 'resultado')
        self.tree = ttk.Treeview(parent_frame, columns=cols, show="headings")
        self.tree.heading('proceso', text="Proceso")
        self.tree.heading('institucion', text="Institución")
        self.tree.heading('nombre', text="Nombre Licitación")
        self.tree.heading('monto', text="Monto Adjudicado")
        self.tree.heading('resultado', text="Resultado")
        self.tree.column('proceso', width=150)
        self.tree.column('institucion', width=220)
        self.tree.column('nombre', width=380)
        self.tree.column('monto', width=160, anchor=tk.E)
        self.tree.column('resultado', width=110, anchor=tk.CENTER)
        self.tree.tag_configure('ganador', background='#d4edda')
        self.tree.bind("<Double-1>", self._abrir_detalles_licitacion)

        for item in self.historial:
            tags = ('ganador',) if item['resultado'].startswith("🏆") else ()
            self.tree.insert('', tk.END,
                values=(item['proceso'], item['institucion'], item['nombre'],
                        f"RD$ {item['monto_adjudicado']:,.2f}", item['resultado']),
                tags=tags)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _abrir_detalles_licitacion(self, event=None):
        if not self.tree.selection(): return
        
        sel = self.tree.selection()[0]
        numero_proceso = self.tree.item(sel, 'values')[0]
        lic = next((l for l in self.todas_las_licitaciones if l.numero_proceso == numero_proceso), None)
        
        if lic:
            # Llamamos a la función de la app principal para abrir la ventana de detalles
            self.parent_app.abrir_ventana_detalles_desde_objeto(lic)

class VentanaAnalisisPaquetes(tk.Toplevel):
    """
    Una ventana dedicada a mostrar la tabla pivote de Lote x Oferente y
    el análisis de los mejores paquetes de ofertas.
    """
    def __init__(self, parent, licitacion):
        super().__init__(parent)
        self.licitacion = licitacion
        # CORRECCIÓN: Aseguramos la referencia a la app principal
        self.parent_app = parent if isinstance(parent, AppLicitacionesGUI) else parent.parent_app
        self.title(f"Análisis de Paquetes: {licitacion.numero_proceso}")
        self.geometry("1000x650") # Un poco más de alto para el nuevo botón
        self.grab_set()

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para la tabla pivote
        tabla_frame = ttk.LabelFrame(main_frame, text="Tabla Pivote de Ofertas (Lotes vs. Competidores)", padding=10)
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para el resumen del análisis
        resumen_frame = ttk.LabelFrame(main_frame, text="Resultados del Análisis", padding=15)
        resumen_frame.pack(fill=tk.X, pady=(15, 0))

        # --- Frame para botones inferiores ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0), padx=10)
        
        ttk.Button(bottom_frame, text="Exportar Reporte...", command=self._exportar_analisis).pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT)
        # --- Fin del frame de botones ---

        # Realizar los cálculos y construir la UI
        self._crear_tabla_pivote(tabla_frame)
        self._mostrar_resumen(resumen_frame)

    def _exportar_analisis(self):
        """Pide una ruta y llama al generador de reportes para el análisis de paquetes."""
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar Análisis de Paquetes",
            initialfile=f"Analisis_Paquetes_{self.licitacion.numero_proceso}",
            filetypes=[("Archivos de Excel", "*.xlsx"), ("Archivos PDF", "*.pdf")],
            defaultextension=".xlsx"
        )
        if not file_path:
            return

        try:
            # Usamos el generador de reportes de la app principal
            self.parent_app.reporter.generate_package_analysis_report(self.licitacion, file_path)
            messagebox.showinfo("Éxito", f"El reporte ha sido guardado exitosamente en:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo generar el reporte:\n{e}", parent=self)

    def _crear_tabla_pivote(self, parent_frame):
        # (Este método se mantiene exactamente igual que antes)
        matriz_ofertas = self.licitacion.get_matriz_ofertas()
        if not matriz_ofertas:
            ttk.Label(parent_frame, text="No hay ofertas habilitadas para analizar.").pack(pady=20)
            return

        todos_los_oferentes = sorted(list(set(
            oferente for ofertas_lote in matriz_ofertas.values() for oferente in ofertas_lote
        )))

        columnas = ['lote'] + todos_los_oferentes
        tree = ttk.Treeview(parent_frame, columns=columnas, show="headings")
        
        tree.heading('lote', text='Lote')
        tree.column('lote', width=250)
        for oferente in todos_los_oferentes:
            tree.heading(oferente, text=oferente)
            tree.column(oferente, width=120, anchor=tk.E)

        tree.tag_configure('oferta_minima', background='#d4edda', font=('Helvetica', 9, 'bold'))

        for lote_num, ofertas in sorted(matriz_ofertas.items()):
            monto_minimo = min((d['monto'] for d in ofertas.values() if isinstance(d.get('monto'), (int, float))), default=float('inf'))
            lote_obj = next((l for l in self.licitacion.lotes if str(l.numero) == lote_num), None)
            nombre_lote = lote_obj.nombre if lote_obj else 'N/D'
            
            valores_fila = [f"Lote {lote_num}: {nombre_lote}"]
            for oferente in todos_los_oferentes:
                oferta = ofertas.get(oferente)
                if oferta and isinstance(oferta.get('monto'), (int, float)):
                    valores_fila.append(f"RD$ {oferta['monto']:,.2f}")
                else:
                    valores_fila.append("---")

            item_id = tree.insert("", tk.END, values=valores_fila)
            
            for i, oferente in enumerate(todos_los_oferentes):
                oferta = ofertas.get(oferente)
                if oferta and oferta.get('monto') == monto_minimo:
                    tree.item(item_id, tags=('oferta_minima',))

        tree.pack(fill=tk.BOTH, expand=True)

    def _mostrar_resumen(self, parent_frame):
        # Limpiamos el frame por si acaso
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # --- 1. Incluir nuestra oferta en la matriz de datos (igual que en el PDF) ---
        matriz = self.licitacion.get_matriz_ofertas()
        for lote in self.licitacion.lotes:
            if getattr(lote, 'participamos', False) and float(getattr(lote, 'monto_ofertado', 0) or 0) > 0:
                lote_num_str = str(lote.numero)
                empresa_nuestra = f"➡️ {lote.empresa_nuestra or 'Nuestra Oferta'}"
                matriz.setdefault(lote_num_str, {})[empresa_nuestra] = {'monto': lote.monto_ofertado}

        if not matriz:
            ttk.Label(parent_frame, text="No hay ofertas habilitadas para analizar.").pack()
            return
            
        # Usamos un frame con scroll para que el contenido no desborde la ventana
        scroll_frame = ScrollableFrame(parent_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame interior donde irá el contenido del análisis
        content_frame = scroll_frame.scrollable_frame
        
        # --- 2. Sección de Análisis de Ofertas por Lote ---
        ttk.Label(content_frame, text="Análisis de Ofertas Más Bajas por Lote", font=('Helvetica', 11, 'bold')).pack(anchor="w", pady=(0, 5))

        for lote_num, ofertas_lote in sorted(matriz.items()):
            lote_obj = next((l for l in self.licitacion.lotes if str(l.numero) == lote_num), None)
            if not lote_obj: continue

            base_lote = float(lote_obj.monto_base or 0.0)
            ofertas_validas = [(data['monto'], oferente) for oferente, data in ofertas_lote.items() if isinstance(data.get('monto'), (int, float)) and data['monto'] > 0]
            
            if not ofertas_validas: continue

            ofertas_ordenadas = sorted(ofertas_validas)
            top_2 = ofertas_ordenadas[:2]

            lote_header = f"Lote {lote_num}: {lote_obj.nombre} (Base: RD$ {base_lote:,.2f})"
            ttk.Label(content_frame, text=lote_header, font=('Helvetica', 10, 'bold', 'underline')).pack(anchor="w", pady=(5, 2))

            for i, (monto, oferente) in enumerate(top_2, start=1):
                dif = monto - base_lote
                pct = (dif / base_lote * 100) if base_lote > 0 else 0
                detalle_text = f"  {i}. {oferente}: RD$ {monto:,.2f} (Diferencia: RD$ {dif:,.2f} / {pct:.2f}%)"
                ttk.Label(content_frame, text=detalle_text).pack(anchor="w")

        # --- 3. Sección de Análisis Comparativo (Nuestros Lotes) ---
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=15, padx=10)
        ttk.Label(content_frame, text="Análisis Comparativo (Nuestros Lotes)", font=('Helvetica', 11, 'bold')).pack(anchor="w", pady=(0, 5))

        lotes_participados = [l for l in self.licitacion.lotes if l.participamos and float(l.monto_ofertado or 0) > 0]
        if not lotes_participados:
            ttk.Label(content_frame, text="No se participó o no se registraron montos de oferta en ningún lote.").pack(anchor="w")
        
        for lote in sorted(lotes_participados, key=lambda l: l.numero):
            nuestra_oferta_monto = lote.monto_ofertado
            nuestra_empresa_nombre = f"➡️ {lote.empresa_nuestra or 'Nuestra Oferta'}"
            
            ofertas_competidores = [
                data['monto'] for oferente, data in matriz.get(str(lote.numero), {}).items()
                if oferente != nuestra_empresa_nombre and isinstance(data.get('monto'), (int, float)) and data['monto'] > 0
            ]

            texto_resultado = f"Lote {lote.numero}: Nuestra oferta es RD$ {nuestra_oferta_monto:,.2f}. "
            if not ofertas_competidores:
                texto_resultado += "Sin ofertas de competidores."
            else:
                mejor_competidor = min(ofertas_competidores)
                diferencial = nuestra_oferta_monto - mejor_competidor
                texto_resultado += f"Mejor competidor: RD$ {mejor_competidor:,.2f}. Diferencial: RD$ {diferencial:,.2f}"
            
            ttk.Label(content_frame, text=texto_resultado, wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=1)


class VentanaComparadorOfertas(tk.Toplevel):
    """Muestra una tabla comparativa de ofertas para un lote específico."""
    def __init__(self, parent, licitacion, num_lote):
        super().__init__(parent)
        self.parent = parent
        self.licitacion = licitacion
        # 🔴 CLAVE: guardar el parámetro en self para usarlo en toda la clase
        self.num_lote = str(num_lote)

        self.title(f"Comparador de Ofertas – Lote {self.num_lote}")
        self.geometry("800x500")
        try:
            self.grab_set()
        except Exception:
            pass

        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Tabla
        self.tree = ttk.Treeview(
            main,
            columns=("participante", "tipo", "monto", "pct", "ganador"),
            show="headings",
            height=14
        )
        self.tree.heading("participante", text="Participante")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("monto", text="Monto Ofertado")
        self.tree.heading("pct", text="% vs Base")
        self.tree.heading("ganador", text="Ganador")

        self.tree.column("participante", width=260, anchor=tk.W)
        self.tree.column("tipo", width=100, anchor=tk.CENTER)
        self.tree.column("monto", width=140, anchor=tk.E)
        self.tree.column("pct", width=100, anchor=tk.E)
        self.tree.column("ganador", width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Resaltado para ganador
        self.tree.tag_configure("ganador", background="#d4edda", font=("Helvetica", 9, "bold"))

        # Cargar datos desde el método que ya agregamos antes
        ofertas = self._recopilar_ofertas()  # ← EXISTE por el bloque que pegaste en el paso anterior

        for o in ofertas:
            pct = o.get('pct_vs_base', None)
            pct_txt = f"{pct:.2f}%" if isinstance(pct, (int, float)) else "N/D"
            tags = ("ganador",) if o.get('ganador') else ()
            self.tree.insert(
                "",
                tk.END,
                values=(
                    o.get('participante', ''),
                    o.get('tipo', ''),
                    f"RD$ {float(o.get('monto', 0) or 0):,.2f}",
                    pct_txt,
                    "Sí" if o.get('ganador') else "No"
                ),
                tags=tags
            )



    def _recopilar_ofertas(self):
        """
        Devuelve una lista de dicts con las ofertas del lote self.num_lote:
        [
        {
            'participante': str,
            'tipo': 'Nosotros' | 'Competidor',
            'monto': float,
            'ganador': bool,
            'pct_vs_base': float | None,
            'lote_num': str,
            'nombre_lote': str
        }, ...
        ]
        """
        lista = []
        lic = self.licitacion
        num = str(self.num_lote)

        # Buscar el lote
        lote = next((l for l in getattr(lic, "lotes", []) if str(getattr(l, "numero", "")) == num), None)
        if not lote:
            return lista

        nombre_lote = getattr(lote, "nombre", "") or ""
        base = float(getattr(lote, "monto_base_personal", 0) or getattr(lote, "monto_base", 0) or 0)

        # NUESTRA OFERTA (si existe)
        monto_nuestro = float(getattr(lote, "monto_ofertado", 0) or 0)
        if monto_nuestro > 0:
            nom_nuestra = (getattr(lote, "empresa_nuestra", None) or "NOSOTROS").strip() or "NOSOTROS"
            lista.append({
                'participante': nom_nuestra,
                'tipo': 'Nosotros',
                'monto': monto_nuestro,
                'ganador': bool(getattr(lote, "ganado_por_nosotros", False)),
                'pct_vs_base': ((monto_nuestro - base) / base * 100.0) if base > 0 else None,
                'lote_num': num,
                'nombre_lote': nombre_lote
            })

        # COMPETIDORES
        for comp in getattr(lic, "oferentes_participantes", []) or []:
            if isinstance(comp, dict):
                nombre_comp = (comp.get("nombre") or "").strip()
                ofertas = comp.get("ofertas_por_lote", []) or []
            else:
                nombre_comp = (getattr(comp, "nombre", "") or "").strip()
                ofertas = getattr(comp, "ofertas_por_lote", []) or []

            if not nombre_comp:
                continue

            for o in ofertas:
                if str(o.get("lote_numero")) == num:
                    monto = float(o.get("monto", 0) or 0)
                    ganador = bool(o.get("ganador", False))
                    lista.append({
                        'participante': nombre_comp,
                        'tipo': 'Competidor',
                        'monto': monto,
                        'ganador': ganador,
                        'pct_vs_base': ((monto - base) / base * 100.0) if base > 0 and monto > 0 else None,
                        'lote_num': num,
                        'nombre_lote': nombre_lote
                    })

        # Orden: primero los que tienen monto, de menor a mayor
        lista.sort(key=lambda d: (0 if d['monto'] > 0 else 1, d['monto']))
        return lista



    def _crear_tabla_comparativa(self, parent, ofertas):
        if not ofertas:
            ttk.Label(parent, text="No hay ofertas habilitadas para comparar en este lote.").pack()
            return

        oferentes = list(ofertas.keys())
        criterios = ["Monto Ofertado", "Plazo (días)", "Garantía (meses)"]

        tree = ttk.Treeview(parent, columns=['criterio'] + oferentes, show="headings")
        tree.heading('criterio', text='Criterio')
        tree.column('criterio', width=150, anchor=tk.W)
        for oferente in oferentes:
            tree.heading(oferente, text=oferente)
            tree.column(oferente, width=150, anchor=tk.E)

        # Encontrar los mejores valores para resaltar
        valores_monto = [d['monto'] for d in ofertas.values() if d['monto'] > 0]
        valores_plazo = [d['plazo'] for d in ofertas.values() if d['plazo'] > 0]
        valores_garantia = [d['garantia'] for d in ofertas.values() if d['garantia'] > 0]

        mejor_monto = min(valores_monto) if valores_monto else None
        mejor_plazo = min(valores_plazo) if valores_plazo else None
        mejor_garantia = max(valores_garantia) if valores_garantia else None

        # Poblar filas
        # Fila de Monto
        row_monto = [criterios[0]]
        for oferente in oferentes:
            monto = ofertas[oferente]['monto']
            display = f"RD$ {monto:,.2f}"
            if monto == mejor_monto: display += " ⭐" # Mejor oferta
            row_monto.append(display)
        tree.insert("", tk.END, values=row_monto)

        # Fila de Plazo
        row_plazo = [criterios[1]]
        for oferente in oferentes:
            plazo = ofertas[oferente]['plazo']
            display = f"{plazo} días"
            if plazo == mejor_plazo: display += " ⭐"
            row_plazo.append(display)
        tree.insert("", tk.END, values=row_plazo)

        # Fila de Garantía
        row_garantia = [criterios[2]]
        for oferente in oferentes:
            garantia = ofertas[oferente]['garantia']
            display = f"{garantia} meses"
            if garantia == mejor_garantia: display += " ⭐"
            row_garantia.append(display)
        tree.insert("", tk.END, values=row_garantia)

        tree.pack(fill=tk.BOTH, expand=True)


class DialogoSeleccionarDocumento(simpledialog.Dialog):
    """Un diálogo moderno con checkboxes, búsqueda y filtro por categoría para seleccionar múltiples documentos de plantilla."""
    def __init__(self, parent, title, documentos_maestros, documentos_actuales):
        codigos_actuales = {doc.codigo for doc in documentos_actuales}
        self.documentos_disponibles = [
            doc for doc in documentos_maestros if doc.codigo not in codigos_actuales
        ]
        
        # --- CAMBIO 1: Lógica para obtener categorías ---
        categorias_unicas = sorted(list(set(doc.categoria for doc in self.documentos_disponibles if doc.categoria)))
        self.categorias_filtro = ["Todas"] + categorias_unicas
        # --- FIN DEL CAMBIO ---
        
        self.selection_status = {doc.id: tk.BooleanVar(value=False) for doc in self.documentos_disponibles}
        super().__init__(parent, title)

# En la clase DialogoSeleccionarDocumento, REEMPLAZA este método:

    def body(self, master):
        self.geometry("800x400")
        
        filter_frame = ttk.Frame(master)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        filter_frame.columnconfigure(1, weight=1)

        ttk.Label(filter_frame, text="🔍 Buscar:").grid(row=0, column=0, padx=(0, 5), pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Label(filter_frame, text="Categoría:").grid(row=0, column=2, padx=(10, 5), pady=5)
        self.categoria_var = tk.StringVar(value="Todas")
        categoria_combo = ttk.Combobox(filter_frame, textvariable=self.categoria_var, values=self.categorias_filtro, state="readonly", width=15)
        categoria_combo.grid(row=0, column=3, pady=5)

        tree_frame = ttk.Frame(master)
        # --- LÍNEA CORREGIDA ---
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        cols = ('codigo', 'nombre', 'categoria')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='tree headings')
        self.tree.column("#0", width=40, anchor=tk.CENTER, stretch=False)
        self.tree.heading("#0", text="Sel.")
        self.tree.heading('codigo', text='Código')
        self.tree.heading('nombre', text='Nombre del Documento')
        self.tree.heading('categoria', text='Categoría')
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_var.trace_add("write", lambda *args: self._populate_treeview())
        categoria_combo.bind("<<ComboboxSelected>>", lambda *args: self._populate_treeview())
        
        self.tree.bind("<Button-1>", self._toggle_selection)
        self._populate_treeview()
        
        return search_entry
    
    def _populate_treeview(self):
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().lower()
        categoria_seleccionada = self.categoria_var.get()
        
        for doc in self.documentos_disponibles:
            nombre = doc.nombre or ""
            codigo = doc.codigo or ""
            categoria = doc.categoria or ""
            
            # --- CAMBIO 4: Lógica de filtrado combinada ---
            filtro_busqueda_pasa = (search_term in nombre.lower() or search_term in codigo.lower())
            filtro_categoria_pasa = (categoria_seleccionada == "Todas" or categoria_seleccionada == categoria)
            # --- FIN DEL CAMBIO ---

            if filtro_busqueda_pasa and filtro_categoria_pasa:
                check_char = '☑' if self.selection_status[doc.id].get() else '☐'
                self.tree.insert('', tk.END, text=check_char, values=(codigo, nombre, categoria), iid=doc.id)

    def _toggle_selection(self, event):
        row_id_str = self.tree.identify_row(event.y)
        if not row_id_str: return
        
        row_id = int(row_id_str)
        self.selection_status[row_id].set(not self.selection_status[row_id].get())
        
        check_char = '☑' if self.selection_status[row_id].get() else '☐'
        self.tree.item(row_id, text=check_char)
        
    def apply(self):
        self.result = [doc for doc in self.documentos_disponibles if self.selection_status[doc.id].get()]


class VentanaAnalisisFaseA(tk.Toplevel):
    """Ventana para registrar y analizar las causas de descalificación en Fase A."""
    # En la clase VentanaAnalisisFaseA, reemplaza el método __init__
    def __init__(self, parent, licitacion, db_manager):
        super().__init__(parent)
        self.parent_app = parent.parent_app
        self.licitacion = licitacion
        self.db = db_manager
        
        self.title(f"Análisis de Fallas Fase A - {self.licitacion.numero_proceso}")
        self.geometry("1200x700")
        self.grab_set()

        self.documentos_seleccionados = {doc.id: tk.BooleanVar(value=False) for doc in self.licitacion.documentos_solicitados}
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(left_pane, weight=2)
        
        self._crear_panel_participantes(left_pane)
        self._crear_panel_documentos(left_pane)
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=3)
        self._crear_panel_registro(right_frame)

        # --- INICIO DE LA CORRECCIÓN ---
        # Este frame de botones no estaba siendo empaquetado correctamente.
        # Ahora se mostrará en la parte inferior de la ventana.
        bottom_button_frame = ttk.Frame(main_frame)
        bottom_button_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM)
        
        ttk.Button(bottom_button_frame, text="✅ Aceptar y Cerrar", command=self.destroy).pack(side=tk.RIGHT, ipady=5)
        # --- FIN DE LA CORRECCIÓN ---

        # Cargamos la vista con las fallas que ya tiene la licitación en memoria
        self._refrescar_vista_fallas()

    def _crear_panel_participantes(self, parent):
        frame = ttk.LabelFrame(parent, text="1. Seleccione Participante(s)", padding=10)
        parent.add(frame, weight=1)
        
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="🔍 Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.participante_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.participante_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tree_container = ttk.Frame(frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.tree_participantes = ttk.Treeview(tree_container, columns=('nombre', 'tipo'), show='headings', selectmode="extended")
        self.tree_participantes.heading('nombre', text='Nombre'); self.tree_participantes.heading('tipo', text='Tipo')
        self.tree_participantes.column('tipo', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree_participantes.yview)
        self.tree_participantes.configure(yscrollcommand=scrollbar.set)
        self.tree_participantes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.participante_search_var.trace_add("write", lambda *args: self._poblar_participantes())
        self._poblar_participantes()

    def _crear_panel_documentos(self, parent):
        frame = ttk.LabelFrame(parent, text="2. Marque Documento(s) con Fallas", padding=10)
        parent.add(frame, weight=2)

        self.tree_docs = ttk.Treeview(frame, columns=('nombre', 'codigo'), show='tree headings')
        self.tree_docs.column("#0", width=40, anchor=tk.CENTER, stretch=False)
        self.tree_docs.heading("#0", text="Sel.")
        self.tree_docs.heading('nombre', text='Nombre del Documento')
        self.tree_docs.heading('codigo', text='Código')
        
        scrollbar_docs = ttk.Scrollbar(frame, orient="vertical", command=self.tree_docs.yview)
        self.tree_docs.configure(yscrollcommand=scrollbar_docs.set)
        
        self.tree_docs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_docs.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_docs.bind("<Button-1>", self._toggle_doc_selection)
        for doc in sorted(self.licitacion.documentos_solicitados, key=lambda d: d.codigo or ''):
            if doc.id:
                self.tree_docs.insert('', tk.END, text='☐', values=(doc.nombre, doc.codigo), iid=doc.id)

    def _crear_panel_registro(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="3. Comentario (Opcional) y Añadir a la Lista",
                font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        self.comentario_text = tk.Text(frame, height=4)
        self.comentario_text.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(frame, text="⬇️ Añadir Falla(s) a la Lista",
                command=self.anadir_fallas_a_memoria).pack(fill=tk.X, ipady=5, pady=(0, 20))
        
        # --- Contenedor de la lista temporal ---
        resultados_frame = ttk.LabelFrame(frame, text="Fallas a Registrar (Lista Temporal)", padding=10)
        resultados_frame.pack(fill=tk.BOTH, expand=True)
        self.frame_lista_temporal = resultados_frame  # (por si lo necesitas luego)

        # --- BARRA DE ACCIONES (BOTONES) ---
        actions = ttk.Frame(resultados_frame)
        actions.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(actions, text="🗑 Eliminar seleccionadas",
                command=self._eliminar_items_temporales).pack(side=tk.LEFT)
        ttk.Button(actions, text="✏️ Editar comentario…",
                command=self._editar_comentario_temporal).pack(side=tk.LEFT, padx=6)

        # --- TABLA ---
        self.tree_fallas = ttk.Treeview(
            resultados_frame,
            columns=('participante', 'documento', 'comentario'),
            show='headings',
            selectmode="extended"
        )
        self.tree_fallas.heading('participante', text='Participante')
        self.tree_fallas.heading('documento', text='Documento Fallido')
        self.tree_fallas.heading('comentario', text='Comentario')
        self.tree_fallas.pack(fill=tk.BOTH, expand=True)

        # --- MENÚ CONTEXTUAL (clic derecho) ---
        self.menu_tmp = tk.Menu(self, tearoff=0)  # padre = Toplevel
        self.menu_tmp.add_command(label="✏️ Editar comentario…", command=self._editar_comentario_temporal)
        self.menu_tmp.add_separator()
        self.menu_tmp.add_command(label="🗑 Eliminar seleccionadas", command=self._eliminar_items_temporales)

        def _popup_tmp(event):
            item = self.tree_fallas.identify_row(event.y)
            if item and item not in self.tree_fallas.selection():
                self.tree_fallas.selection_set(item)
            try:
                self.menu_tmp.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu_tmp.grab_release()

        # Win/Linux y (según config) macOS
        self.tree_fallas.bind("<Button-3>", _popup_tmp)
        self.tree_fallas.bind("<Button-2>", _popup_tmp)


    def _poblar_participantes(self):
        self.tree_participantes.delete(*self.tree_participantes.get_children())
        search_term = self.participante_search_var.get().lower()
        nuestras_empresas = self._nuestras_empresas_de_licitacion()
        
        todos_los_participantes = []
        for emp in nuestras_empresas: todos_los_participantes.append({'nombre': emp, 'tipo': "Nuestra"})
        for oferente in self.licitacion.oferentes_participantes:
            if oferente.nombre not in nuestras_empresas:
                todos_los_participantes.append({'nombre': oferente.nombre, 'tipo': "Competidor"})
        
        todos_los_participantes.sort(key=lambda p: p['nombre'])
        
        for p in todos_los_participantes:
            if search_term in p['nombre'].lower():
                self.tree_participantes.insert('', tk.END, values=(p['nombre'], p['tipo']), iid=p['nombre'])

    def _toggle_doc_selection(self, event):
        """Maneja el clic en una fila para marcar/desmarcar el checkbox."""
        iid = self.tree_docs.identify_row(event.y)
        if not iid: return
        
        try:
            doc_id = int(iid)
            if doc_id in self.documentos_seleccionados:
                var = self.documentos_seleccionados[doc_id]
                var.set(not var.get())
                check_char = '☑' if var.get() else '☐'
                self.tree_docs.item(iid, text=check_char)
        except (ValueError, KeyError):
            # Ignorar clics en áreas sin ID válido
            pass

    def _nuestras_empresas_de_licitacion(self):
        return {str(e) for e in self.licitacion.empresas_nuestras}


    def cargar_fallas_existentes(self):
        """Este método ya no es necesario, los datos vienen en self.licitacion."""
        self._refrescar_vista_fallas()

    def _refrescar_vista_fallas(self):
        self.tree_fallas.delete(*self.tree_fallas.get_children())

        # mapas de documentos
        self._docname_by_id = {doc.id: doc.nombre for doc in self.licitacion.documentos_solicitados}
        self._docid_by_name = {v: k for k, v in self._docname_by_id.items()}

        for falla in self.licitacion.fallas_fase_a:
            participante = falla.get('participante_nombre')
            doc_id = falla.get('documento_id')
            comentario = falla.get('comentario', '')
            doc_nombre = self._docname_by_id.get(doc_id, "Documento no encontrado")
            self.tree_fallas.insert('', tk.END, values=(participante, doc_nombre, comentario))
        
    def anadir_fallas_a_memoria(self):
        """Añade las selecciones actuales a la lista de fallas del objeto Licitacion."""
        participantes_sel = [self.tree_participantes.item(iid, 'values')[0] for iid in self.tree_participantes.selection()]
        documentos_sel_ids = [doc_id for doc_id, var in self.documentos_seleccionados.items() if var.get()]
        comentario = self.comentario_text.get("1.0", tk.END).strip()
        
        if not participantes_sel or not documentos_sel_ids:
            messagebox.showwarning("Datos Faltantes", "Debe seleccionar al menos un participante y un documento.", parent=self)
            return

        nuestras_empresas = self._nuestras_empresas_de_licitacion()
        nuevas_fallas_count = 0
        
        for participante in participantes_sel:
            es_nuestro = participante in nuestras_empresas
            for doc_id in documentos_sel_ids:
                # Comprobar si la falla ya existe en la lista de la licitación
                if not any(f['participante_nombre'] == participante and f['documento_id'] == doc_id for f in self.licitacion.fallas_fase_a):
                    nueva_falla = {
                        "licitacion_id": self.licitacion.id,
                        "participante_nombre": participante,
                        "documento_id": doc_id,
                        "comentario": comentario,
                        "es_nuestro": es_nuestro
                    }
                    self.licitacion.fallas_fase_a.append(nueva_falla)
                    nuevas_fallas_count += 1
        
        if nuevas_fallas_count > 0:
            self._refrescar_vista_fallas()
            self.comentario_text.delete("1.0", tk.END)
            for var in self.documentos_seleccionados.values(): var.set(False)
            for iid in self.tree_docs.get_children(): self.tree_docs.item(iid, text='☐')
        else:
            messagebox.showinfo("Información", "Las fallas seleccionadas ya estaban en la lista.", parent=self)

    def _guardar_y_cerrar(self):
        """Este método ya no necesita guardar. La ventana de Detalles lo hará."""
        self.destroy() # Simplemente cerramos la ventana

    def _eliminar_items_temporales(self):
        sel = self.tree_fallas.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona una o más filas de la lista temporal.", parent=self)
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar {len(sel)} fila(s)?", parent=self):
            return

        # quitamos de self.licitacion.fallas_fase_a
        for iid in sel:
            participante, doc_nombre, _coment = self.tree_fallas.item(iid, "values")
            doc_id = self._docid_by_name.get(doc_nombre)
            if doc_id is None:
                continue
            self.licitacion.fallas_fase_a = [
                f for f in self.licitacion.fallas_fase_a
                if not (f.get("participante_nombre") == participante and f.get("documento_id") == doc_id)
            ]
        self._refrescar_vista_fallas()
        messagebox.showinfo("Eliminar", "Falla(s) eliminada(s) de la lista temporal.", parent=self)

    def _editar_comentario_temporal(self):
        sel = self.tree_fallas.selection()
        if not sel:
            messagebox.showinfo("Editar comentario", "Selecciona una o más filas de la lista temporal.", parent=self)
            return

        top = tk.Toplevel(self); top.title("Editar comentario"); top.transient(self); top.grab_set()
        ttk.Label(top, text=f"Nuevo comentario para {len(sel)} fila(s):").pack(padx=10, pady=(10,5))
        var = tk.StringVar(); entry = ttk.Entry(top, textvariable=var, width=60)
        entry.pack(padx=10, pady=5); entry.focus_set()

        def _guardar():
            comentario = var.get().strip()
            if not comentario:
                messagebox.showwarning("Editar comentario", "Escribe un comentario.", parent=top); return

            for iid in sel:
                participante, doc_nombre, _old = self.tree_fallas.item(iid, "values")
                doc_id = self._docid_by_name.get(doc_nombre)
                if doc_id is None:
                    continue
                # actualiza en la lista de la licitación
                for f in self.licitacion.fallas_fase_a:
                    if f.get("participante_nombre") == participante and f.get("documento_id") == doc_id:
                        f["comentario"] = comentario
            top.destroy()
            self._refrescar_vista_fallas()
            messagebox.showinfo("Editar comentario", "Comentario actualizado.", parent=self)

        btns = ttk.Frame(top); btns.pack(pady=(10,10))
        ttk.Button(btns, text="Guardar", command=_guardar).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancelar", command=top.destroy).pack(side=tk.LEFT, padx=6)

class DialogoConfirmarImportacion(simpledialog.Dialog):
    """
    Una ventana avanzada para revisar documentos seleccionados,
    permitiendo cambiar su categoría de forma masiva o individual antes de importar.
    """
    def __init__(self, parent, documentos_seleccionados, categorias_disponibles):
        self.documentos = documentos_seleccionados
        self.categorias = categorias_disponibles
        super().__init__(parent, "Confirmar y Categorizar Documentos")

    def body(self, master):
        self.geometry("800x500")

        # Panel de Acción Masiva
        bulk_frame = ttk.Frame(master)
        bulk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(bulk_frame, text="Aplicar esta categoría a TODOS:").pack(side=tk.LEFT, padx=(0, 5))
        self.bulk_categoria_var = tk.StringVar()
        self.bulk_combo = ttk.Combobox(bulk_frame, textvariable=self.bulk_categoria_var, values=self.categorias, state="readonly", width=20)
        self.bulk_combo.pack(side=tk.LEFT)
        ttk.Button(bulk_frame, text="Aplicar a Todos", command=self._aplicar_a_todos).pack(side=tk.LEFT, padx=5)

        # Treeview para edición individual
        tree_frame = ttk.Frame(master)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ('codigo', 'nombre', 'categoria')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.heading('codigo', text='Código'); self.tree.column('codigo', width=150)
        self.tree.heading('nombre', text='Nombre del Documento'); self.tree.column('nombre', width=400)
        self.tree.heading('categoria', text='Categoría (Doble Clic para Editar)'); self.tree.column('categoria', width=150)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for doc in self.documentos:
            self.tree.insert('', tk.END, iid=doc.id, values=(doc.codigo, doc.nombre, doc.categoria))
            
        self.tree.bind("<Double-1>", self._editar_celda)
        return self.tree

    def _aplicar_a_todos(self):
        """Aplica la categoría seleccionada en el combo a todos los items del treeview."""
        nueva_categoria = self.bulk_categoria_var.get()
        if not nueva_categoria: return
        
        for iid in self.tree.get_children():
            self.tree.set(iid, 'categoria', nueva_categoria)

    def _editar_celda(self, event):
        """Crea un combobox de edición in-place sobre la celda de categoría."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        iid = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if column != "#3": # Columna de categoría
            return

        x, y, width, height = self.tree.bbox(iid, column)
        
        valor_actual = self.tree.set(iid, column)
        combo = ttk.Combobox(self.tree, values=self.categorias, state="readonly")
        combo.place(x=x, y=y, width=width, height=height)
        combo.set(valor_actual)
        combo.focus_set()

        def on_selection_change(event=None):
            self.tree.set(iid, column, combo.get())
            combo.destroy()
        
        combo.bind("<<ComboboxSelected>>", on_selection_change)
        combo.bind("<FocusOut>", lambda e: combo.destroy())

    def apply(self):
        self.result = []
        # ESTA ES LA LÓGICA CORRECTA Y DEFINITIVA
        # Lee el valor actual de cada celda con .set()
        for iid in self.tree.get_children():
            self.result.append({
                'codigo': self.tree.set(iid, 'codigo'),
                'nombre': self.tree.set(iid, 'nombre'),
                'categoria': self.tree.set(iid, 'categoria'), # <-- Lee el valor actualizado
                'id_maestro': iid 
            })


class VentanaGestionDocumentos(tk.Toplevel):
    def __init__(
        self,
        parent,
        licitacion,
        callback=None,
        documentos_maestros=None,
        categorias=None,
        todas_las_licitaciones=None,
        lista_responsables=None,
        on_docs_changed=None,
        *args, **kwargs
    ):
        super().__init__(parent)
        self.parent = parent
        self.parent_app = parent.parent_app
        self.licitacion = licitacion
        self.callback_actualizar = callback
        self._on_docs_changed = on_docs_changed
        self.documentos_maestros = documentos_maestros or []
        self.categorias = categorias or ["Legal", "Financiera", "Técnica", "Sobre B", "Otros"]
        self.todas_las_licitaciones = todas_las_licitaciones or []
        lr = lista_responsables or []
        if isinstance(lr, dict): lr = [lr]
        self.lista_responsables = ["Sin Asignar"] + sorted([r["nombre"] if isinstance(r, dict) else str(r) for r in lr])
        self.title(f"Gestionar Documentos de {licitacion.nombre_proceso}")
        self.geometry("1200x700")
        self.grab_set()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.trees = {}
        for categoria in self.categorias:
            frame = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(frame, text=categoria)
            cols = ('estado', 'rev', 'adj', 'codigo', 'nombre', 'condicion', 'responsable')
            tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode=tk.EXTENDED)
            tree.heading('estado', text='✓'); tree.heading('rev', text='👁️'); tree.heading('adj', text='📎'); tree.heading('codigo', text='Código'); tree.heading('nombre', text='Nombre del Documento'); tree.heading('condicion', text='Condición'); tree.heading('responsable', text='Responsable')
            tree.column('estado', width=30, anchor=tk.CENTER, stretch=False); tree.column('rev', width=30, anchor=tk.CENTER, stretch=False); tree.column('adj', width=30, anchor=tk.CENTER, stretch=False); tree.column('codigo', width=120); tree.column('nombre', width=450); tree.column('condicion', width=100, anchor=tk.CENTER); tree.column('responsable', width=150)
            tree.pack(side=tk.LEFT, fill="both", expand=True)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.trees[categoria] = tree
            tree.bind("<<TreeviewSelect>>", self.on_doc_select)

        frame_subsanables = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame_subsanables, text="⚠️ Subsanables")
        self._crear_tab_subsanables(frame_subsanables)

        action_frame = ttk.Frame(self)
        action_frame.pack(pady=5, fill="x", padx=10)
        ttk.Label(action_frame, text="Asignar Responsable:").pack(side=tk.LEFT, padx=(0, 5))
        self.responsable_var = tk.StringVar()
        self.responsable_combo = ttk.Combobox(action_frame, textvariable=self.responsable_var, values=self.lista_responsables, state="disabled", width=20)
        self.responsable_combo.pack(side=tk.LEFT, padx=5)
        self.responsable_combo.bind("<<ComboboxSelected>>", self._guardar_responsable_multiple)
        ttk.Separator(action_frame, orient="vertical").pack(side=tk.LEFT, padx=15, fill="y")
        self.revisado_button = ttk.Button(action_frame, text="👁️ Marcar como Revisado/No Revisado", command=self._toggle_estado_revisado, state="disabled")
        self.revisado_button.pack(side=tk.LEFT, padx=5)
        self.subsanable_button = ttk.Button(action_frame, text="⚖️ Cambiar Condición (Subsanable)", command=self.cambiar_estado_subsanable, state="disabled")
        self.subsanable_button.pack(side=tk.LEFT, padx=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5, fill="x", padx=10)
        btn_frame.columnconfigure(tuple(range(4)), weight=1)

        acciones = {
            "agregar_manual": ("➕ Agregar Manual", self.agregar_manual),
            "importar_licitacion": ("📥 Importar de Licitación", self.importar_desde_licitacion),
            "agregar_plantilla": ("✨ Agregar de Plantilla", self.agregar_desde_plantilla),
            "gestionar_subsanacion": ("⚠️ Iniciar/Gestionar Subsanación", self.iniciar_subsanacion),
            "editar": ("✏️ Editar", self.editar_documento),
            "cambiar_estado": ("🟢/❌ Cambiar Estado", self.cambiar_estado_documento),
            "eliminar": ("🗑️ Eliminar", self.eliminar_documento),
            "adjuntar_archivo": ("📎 Adjuntar Archivo", self.adjuntar_archivo),
            "ver_archivo": ("📂 Ver Archivo", self.ver_archivo),
            "quitar_adjunto": ("❌ Quitar Adjunto", self.quitar_adjunto),
            # --- ¡NUEVO BOTÓN! ---
            "rellenar_formulario": ("📄 Rellenar Formulario", self._rellenar_formulario_seleccionado),
        }
        self.buttons = {}
        # Ajustamos la cuadrícula para que quepan más botones
        num_columnas = 4
        for i, (key, (text, cmd)) in enumerate(acciones.items()):
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.grid(row=i // num_columnas, column=i % num_columnas, sticky=tk.EW, padx=5, pady=2)
            self.buttons[key] = btn

        self.actualizar_listas_docs()
        self.on_doc_select(None)


    def _rellenar_formulario_seleccionado(self):
        docs_seleccionados = self._find_docs_from_selection()
        if len(docs_seleccionados) != 1:
            return

        doc_plantilla = docs_seleccionados[0]
        ruta_plantilla_guardada = getattr(doc_plantilla, "ruta_archivo", None)

        if not ruta_plantilla_guardada:
            messagebox.showerror("Error", "El documento seleccionado no tiene un archivo de plantilla adjunto.", parent=self)
            return

        ruta_plantilla_absoluta = reconstruir_ruta_absoluta(ruta_plantilla_guardada)
        if not ruta_plantilla_absoluta or not os.path.isfile(ruta_plantilla_absoluta):
            messagebox.showerror("Error", f"No se encontró el archivo de plantilla en la ruta:\n{ruta_plantilla_absoluta}", parent=self)
            return

        nuestras_empresas = self.parent_app.empresas_registradas
        if not nuestras_empresas:
            messagebox.showerror("Error", "No hay empresas maestras registradas.", parent=self)
            return

        nombres_empresas = sorted([e['nombre'] for e in nuestras_empresas])
        
        empresa_seleccionada_nombre = None
        if len(nombres_empresas) == 1:
            empresa_seleccionada_nombre = nombres_empresas[0]
        else:
            top = tk.Toplevel(self)
            top.title("Seleccionar Empresa")
            top.transient(self)
            top.grab_set()
            ttk.Label(top, text="¿Con los datos de qué empresa desea rellenar el formulario?").pack(padx=20, pady=10)
            combo_var = tk.StringVar(value=nombres_empresas[0])
            ttk.Combobox(top, textvariable=combo_var, values=nombres_empresas, state="readonly").pack(padx=20, pady=5)
            
            def on_ok():
                nonlocal empresa_seleccionada_nombre
                empresa_seleccionada_nombre = combo_var.get()
                top.destroy()
            
            ttk.Button(top, text="Aceptar", command=on_ok).pack(pady=10)
            self.wait_window(top)

        if not empresa_seleccionada_nombre:
            return

        empresa_data = next((e for e in nuestras_empresas if e['nombre'] == empresa_seleccionada_nombre), None)
        if not empresa_data:
            messagebox.showerror("Error", "No se encontraron los datos de la empresa seleccionada.", parent=self)
            return
            
        contexto = {
            "numero_proceso": self.licitacion.numero_proceso,
            "nombre_proceso": self.licitacion.nombre_proceso,
            "institucion": self.licitacion.institucion,
            "lotes_participados": ", ".join(sorted([str(l.numero) for l in self.licitacion.lotes if l.participamos])),
            "fecha_actual": datetime.date.today().strftime("%d/%m/%Y"),
            "empresa_nombre": empresa_data.get("nombre", ""),
            "empresa_rnc": empresa_data.get("rnc", ""),
            "empresa_rpe": empresa_data.get("rpe", ""),
            "empresa_telefono": empresa_data.get("telefono", ""),
            "empresa_correo": empresa_data.get("correo", ""),
            "empresa_direccion": empresa_data.get("direccion", ""),
            "empresa_representante": empresa_data.get("representante", ""),
            "empresa_cargo_representante": empresa_data.get("cargo_representante", "")
        }
        
        nombre_archivo_sugerido = f"{doc_plantilla.codigo}_{self.licitacion.numero_proceso}_{empresa_data.get('nombre', '').replace(' ', '_')}.docx"
        
        ruta_salida = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Formulario Rellenado",
            initialfile=nombre_archivo_sugerido,
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")]
        )

        if not ruta_salida:
            return
        
        # --- INICIO DE CÓDIGO DE DIAGNÓSTICO ---
        print("\n" + "="*25)
        print("--- DEBUG: Datos para la Plantilla ---")
        import json
        # Imprimimos el diccionario de datos de forma legible
        print(json.dumps(contexto, indent=2, ensure_ascii=False))
        print("="*25 + "\n")
        # --- FIN DE CÓDIGO DE DIAGNÓSTICO ---

        try:
            self.config(cursor="wait")
            self.update_idletasks()
            fill_template(ruta_plantilla_absoluta, ruta_salida, contexto, debug=True)

            messagebox.showinfo("Éxito", f"Documento rellenado y guardado correctamente en:\n{ruta_salida}", parent=self)
            
            if messagebox.askyesno("Abrir Archivo", "¿Desea abrir el documento generado?", parent=self):
                os.startfile(ruta_salida)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al rellenar el documento:\n{e}", parent=self)
        finally:
            self.config(cursor="")
    def _crear_tab_subsanables(self, parent_frame):
        estado_frame = ttk.LabelFrame(parent_frame, text="Estado del Proceso de Subsanación", padding=10)
        estado_frame.pack(fill=tk.X, pady=(0, 10))
        datos_evento = self.licitacion.cronograma.get("Entrega de Subsanaciones", {})
        fecha = datos_evento.get("fecha_limite", "No definida")
        estado = datos_evento.get("estado", "No iniciado")
        ttk.Label(estado_frame, text=f"Fecha Límite: {fecha}  |  Estado: {estado}").pack(side=tk.LEFT)
        ttk.Button(estado_frame, text="✅ Finalizar Proceso de Subsanación", command=self._finalizar_proceso_subsanacion).pack(side=tk.RIGHT)

        lista_frame = ttk.LabelFrame(parent_frame, text="Documentos Requeridos para Subsanar", padding=10)
        lista_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('presentado', 'codigo', 'nombre')
        self.tree_subsanables = ttk.Treeview(lista_frame, columns=cols, show="headings")
        self.tree_subsanables.heading('presentado', text='✓'); self.tree_subsanables.column('presentado', width=30, anchor=tk.CENTER, stretch=False)
        self.tree_subsanables.heading('codigo', text='Código'); self.tree_subsanables.column('codigo', width=150)
        self.tree_subsanables.heading('nombre', text='Nombre'); self.tree_subsanables.column('nombre', width=450)
        self.tree_subsanables.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree_subsanables.yview)
        self.tree_subsanables.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- INICIO DE CAMBIOS: Botones de acción en la pestaña ---
        acciones_sub_frame = ttk.Frame(parent_frame, padding=(0, 10, 0, 0))
        acciones_sub_frame.pack(fill=tk.X)
        ttk.Button(acciones_sub_frame, text="Marcar Seleccionado(s) como Completado", command=self._marcar_subsanables_completados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(acciones_sub_frame, text="➕ Agregar Manualmente...", command=self.agregar_manual).pack(side=tk.LEFT, padx=5)
        ttk.Button(acciones_sub_frame, text="✨ Agregar desde Plantilla...", command=self.agregar_desde_plantilla).pack(side=tk.LEFT, padx=5)
        # --- FIN DE CAMBIOS ---


    def _poblar_tab_subsanables(self):
        self.tree_subsanables.delete(*self.tree_subsanables.get_children())
        docs_a_subsanar = [d for d in self.licitacion.documentos_solicitados if d.requiere_subsanacion]
        
        for doc in docs_a_subsanar:
            estado_icono = "✅" if doc.presentado else "❌"
            self.tree_subsanables.insert("", tk.END, iid=doc.id, values=(estado_icono, doc.codigo, doc.nombre))

    def _marcar_subsanables_completados(self):
        seleccion = self.tree_subsanables.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Seleccione uno o más documentos de la lista de subsanables.", parent=self)
            return

        for doc_id_str in seleccion:
            doc_id = int(doc_id_str)
            doc = next((d for d in self.licitacion.documentos_solicitados if d.id == doc_id), None)
            if doc:
                doc.presentado = True
                doc.requiere_subsanacion = False
                # --- INICIO LÍNEA NUEVA ---
                # Marcamos el evento como completado en el historial
                # Si tu objeto 'doc' tiene atributo 'codigo', pasa ambos
                self.parent.db.completar_evento_subsanacion(self.licitacion.id, doc.id, getattr(doc, "codigo", None))

                # --- FIN LÍNEA NUEVA ---
        
        self.parent._guardar_sin_cerrar()
        self.actualizar_listas_docs()
        messagebox.showinfo("Éxito", f"{len(seleccion)} documento(s) marcado(s) como completados.", parent=self)


    def _finalizar_proceso_subsanacion(self):
        """
        Marca todo el proceso de subsanación como 'Cumplido' y actualiza el historial
        de todos los documentos que estaban pendientes.
        """
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea marcar todo el proceso de subsanación como 'Cumplido'?\nEsto quitará la alerta roja de la ventana principal.", parent=self):
            
            # --- INICIO DEL CÓDIGO AÑADIDO ---
            # 1. Identificar qué documentos estaban pendientes ANTES de hacer cambios.
            docs_pendientes = [
                doc for doc in self.licitacion.documentos_solicitados 
                if doc.requiere_subsanacion and doc.id is not None
            ]
            # --- FIN DEL CÓDIGO AÑADIDO ---

            # 2. Actualizar el objeto licitación en memoria (como ya lo hacías)
            self.licitacion.cronograma["Entrega de Subsanaciones"]["estado"] = "Cumplido"
            for doc in self.licitacion.documentos_solicitados:
                doc.requiere_subsanacion = False
            
            # 3. Guardar todos los cambios de la licitación en la base de datos
            self.parent._guardar_sin_cerrar()

            # --- INICIO DEL CÓDIGO AÑADIDO ---
            # 4. AHORA, actualizar el historial en la BD para cada documento que estaba pendiente.
            for doc in docs_pendientes:
                # Si tu objeto 'doc' tiene atributo 'codigo', pasa ambos
                self.parent.db.completar_evento_subsanacion(self.licitacion.id, doc.id, getattr(doc, "codigo", None))

            # --- FIN DEL CÓDIGO AÑADIDO ---

            # 5. Refrescar toda la interfaz gráfica
            self.actualizar_listas_docs()
            
            # Lógica para refrescar el label de estado en la pestaña de subsanables
            try:
                tab_actual = self.notebook.tab(self.notebook.select(), "text")
                if "Subsanables" in tab_actual:
                    tab_frame = self.notebook.nametowidget(self.notebook.tabs()[-1])
                    for widget in tab_frame.winfo_children():
                        widget.destroy()
                    self._crear_tab_subsanables(tab_frame)
                    self._poblar_tab_subsanables()
            except Exception as e:
                print(f"Error menor al refrescar UI de subsanables: {e}")

    # --- MÉTODO _get_active_category_and_tree ACTUALIZADO ---
    def _get_active_category_and_tree(self):
        try:
            tab_id = self.notebook.select()
            cat_activa = self.notebook.tab(tab_id, "text")
            return cat_activa, self.trees[cat_activa]
        except (KeyError, tk.TclError):
            return None, None

    # --- MÉTODO _find_docs_from_selection ACTUALIZADO ---
    def _find_docs_from_selection(self):
        """Devuelve los objetos Documento seleccionados en el Treeview activo."""
        _, tree = self._get_active_category_and_tree()
        if not tree:
            return []

        selected_iids = set(tree.selection())
        if not selected_iids:
            return []

        # Mapeamos por el iid que realmente metimos en el Treeview (id real o tmp-...)
        result = []
        for doc in self.licitacion.documentos_solicitados:
            iid = self._iid_for_doc(doc)
            if iid in selected_iids:
                result.append(doc)
        return result


    @staticmethod
    def _orden_sort_val(d):
        """Normaliza orden_pliego a int; si está vacío/None/no convertible, lo manda al final."""
        val = getattr(d, "orden_pliego", None)
        try:
            return int(val)
        except (TypeError, ValueError):
            return 999_999
        

    def _iid_for_doc(self, doc):
        """IID estable para Treeview: usa id de DB si existe; si no, un temporal."""
        return f"doc-{doc.id}" if getattr(doc, "id", None) else f"tmp-{id(doc)}"


    def actualizar_listas_docs(self):
        """Redibuja TODOS los Treeviews, incluyendo el nuevo de subsanables."""
        # Agrupar por categoría
        docs_por_categoria = {cat: [] for cat in self.categorias}
        for doc in self.licitacion.documentos_solicitados:
            cat = getattr(doc, "categoria", None)
            if cat in docs_por_categoria:
                docs_por_categoria[cat].append(doc)

        for categoria, tree in self.trees.items():
            tree.delete(*tree.get_children())
            documentos_ordenados = sorted(docs_por_categoria.get(categoria, []), key=lambda d: (self._orden_sort_val(d), d.codigo or "", d.nombre or ""))
            for doc in documentos_ordenados:
                iid = self._iid_for_doc(doc)
                estado = "✓" if getattr(doc, "presentado", False) else "❌"
                # --- LÓGICA DE ALERTA VISUAL ---
                if getattr(doc, "requiere_subsanacion", False):
                    estado = "⚠️ " + estado # Añadimos un ícono de advertencia
                
                revisado = "✓" if getattr(doc, "revisado", False) else ""
                adjunto = "✓" if getattr(doc, "ruta_archivo", "") else ""
                condicion = getattr(doc, "subsanable", None) or "No Definido"
                responsable = getattr(doc, "responsable", "") or "Sin Asignar"
                tree.insert("", tk.END, iid=iid, values=(estado, revisado, adjunto, doc.codigo, doc.nombre, condicion, responsable))
        
        # Poblar la nueva pestaña
        self._poblar_tab_subsanables()
        self.on_doc_select(None)


    def _notify_docs_changed(self):
        try:
            if callable(self._on_docs_changed): self._on_docs_changed()
            elif callable(self.callback_actualizar): self.callback_actualizar()
            elif hasattr(self.parent, "actualizar_info_docs"): self.parent.actualizar_info_docs()
        except Exception: pass

    def _next_orden(self):
        docs = getattr(self.licitacion, "documentos_solicitados", []) or []
        if not docs: return 1
        try: return max(int(getattr(d, "orden_pliego", 0) or 0) for d in docs) + 1
        except Exception: return len(docs) + 1

    def on_doc_select(self, event=None):
        docs = self._find_docs_from_selection()
        state_if_selection = "normal" if docs else "disabled"
        
        for key in ["cambiar_estado", "eliminar", "adjuntar_archivo"]:
            self.buttons[key].config(state=state_if_selection)
        
        self.responsable_combo.config(state="readonly" if docs else "disabled")
        self.revisado_button.config(state=state_if_selection)
        
        state_if_single = "normal" if len(docs) == 1 else "disabled"
        
        self.buttons["editar"].config(state=state_if_single)
        self.subsanable_button.config(state=state_if_single)
        
        # --- ¡NUEVA LÓGICA! ---
        # Habilitar "Rellenar Formulario" solo si hay un único documento seleccionado
        self.buttons["rellenar_formulario"].config(state=state_if_single)

        doc = docs[0] if len(docs) == 1 else None
        
        self.buttons["ver_archivo"].config(state="normal" if (doc and getattr(doc, "ruta_archivo", "")) else "disabled")
        any_has_file = any(getattr(d, "ruta_archivo", "") for d in docs)
        self.buttons["quitar_adjunto"].config(state="normal" if (docs and any_has_file) else "disabled")

        if doc: self.responsable_var.set(doc.responsable or "Sin Asignar")
        else: self.responsable_var.set("")


    def agregar_desde_plantilla(self):
            # --- INICIO DE LA CORRECCIÓN ---
            # Ya no filtramos por empresa, tomamos todas las plantillas globales.
            plantillas_disponibles = self.documentos_maestros
            
            if not plantillas_disponibles:
                messagebox.showinfo("Sin Plantillas", "No hay plantillas de documentos globales guardadas.", parent=self)
                return
            # --- FIN DE LA CORRECCIÓN ---

            dialogo_seleccion = DialogoSeleccionarDocumento(self, "Seleccionar de Plantilla", plantillas_disponibles, self.licitacion.documentos_solicitados)
            
            if dialogo_seleccion.result:
                documentos_a_importar = dialogo_seleccion.result
                dialogo_confirmacion = DialogoConfirmarImportacion(self, documentos_a_importar, self.categorias)
                
                if dialogo_confirmacion.result:
                    es_desde_subsanables = False
                    try:
                        tab_actual = self.notebook.tab(self.notebook.select(), "text")
                        if "Subsanables" in tab_actual:
                            es_desde_subsanables = True
                    except tk.TclError:
                        pass

                    nuevos_agregados = 0
                    for doc_data in dialogo_confirmacion.result:
                        doc_maestro = next((d for d in self.documentos_maestros if str(d.id) == str(doc_data['id_maestro'])), None)
                        if doc_maestro:
                            nuevo_doc = Documento(
                                codigo=doc_maestro.codigo,
                                nombre=doc_maestro.nombre,
                                categoria=doc_data['categoria'],
                                comentario=doc_maestro.comentario,
                                subsanable=getattr(doc_maestro, "subsanable", "Subsanable"),
                                obligatorio=bool(getattr(doc_maestro, "obligatorio", False))
                            )
                            if es_desde_subsanables:
                                nuevo_doc.requiere_subsanacion = True
                            self.licitacion.documentos_solicitados.append(nuevo_doc)
                            nuevos_agregados += 1
                    
                    if nuevos_agregados > 0:
                        self.actualizar_listas_docs()
                        self._notify_docs_changed()
                        messagebox.showinfo("Éxito", f"Se agregaron {nuevos_agregados} documentos.", parent=self)
            
            self.grab_set()


    def importar_desde_licitacion(self):
        dialogo = DialogoSeleccionarLicitacion(self, "Importar Documentos", self.todas_las_licitaciones, self.licitacion.numero_proceso)
        if dialogo.result:
            origen = next((l for l in self.todas_las_licitaciones if l.numero_proceso == dialogo.result), None)
            if not origen: return
            codigos_existentes = {d.codigo for d in self.licitacion.documentos_solicitados}
            for d_o in getattr(origen, "documentos_solicitados", []):
                if d_o.codigo in codigos_existentes: continue
                nuevo = Documento(codigo=d_o.codigo, nombre=d_o.nombre, categoria=d_o.categoria, subsanable=getattr(d_o, "subsanable", "No Definido"), comentario=getattr(d_o, "comentario", ""), obligatorio=bool(getattr(d_o, "obligatorio", False)))
                nuevo.orden_pliego = self._next_orden(); self.licitacion.documentos_solicitados.append(nuevo)
            self.actualizar_listas_docs(); self._notify_docs_changed()
        self.grab_set()

    def agregar_manual(self):
        cat = None
        es_desde_subsanables = False
        
        try:
            tab_actual_id = self.notebook.select()
            nombre_tab = self.notebook.tab(tab_actual_id, "text")
            
            if "Subsanables" in nombre_tab:
                es_desde_subsanables = True
                dlg_cat = DialogoElegirCategoria(self, "Seleccionar Categoría", self.categorias, self.categorias[0])
                cat = dlg_cat.result
            else:
                cat = nombre_tab # La categoría es el nombre de la pestaña activa
        except tk.TclError:
            messagebox.showwarning("Error", "No se pudo determinar la pestaña activa.", parent=self)
            return

        if not cat:
            # Si el usuario canceló la selección de categoría, no continuamos
            if es_desde_subsanables: return 
            messagebox.showwarning("Selección Requerida", "Por favor, selecciona una categoría (pestaña) primero.", parent=self)
            return

        empresa_principal = str(self.licitacion.empresas_nuestras[0]) if self.licitacion.empresas_nuestras else None
        
        # Pasamos la categoría seleccionada como dato inicial
        dlg_datos = DialogoAgregarDocumento(self, f"Nuevo Documento - {cat}", initial_data={'categoria': cat}, categorias=self.categorias, empresa_actual=empresa_principal)
        
        if dlg_datos.result:
            datos = dlg_datos.result
            nuevo_doc = Documento(codigo=datos["codigo"], nombre=datos["nombre"], categoria=datos["categoria"], comentario=datos["comentario"])
            
            if es_desde_subsanables:
                nuevo_doc.requiere_subsanacion = True

            self.licitacion.documentos_solicitados.append(nuevo_doc)
            
            # (Lógica para guardar plantilla sin cambios)
            if datos["guardar_plantilla"] and empresa_principal:
                if any(d.codigo == datos["codigo"] and d.empresa_nombre == empresa_principal for d in self.documentos_maestros):
                     messagebox.showwarning("Plantilla Duplicada", f"Ya existe una plantilla con el código '{datos['codigo']}'.", parent=self)
                else:
                    doc_plantilla = Documento(**datos, empresa_nombre=empresa_principal)
                    self.parent_app.documentos_maestros.append(doc_plantilla)
                    self.parent_app.db.save_master_lists(
                        empresas=self.parent_app.empresas_registradas, 
                        instituciones=self.parent_app.instituciones_registradas,
                        documentos_maestros=self.parent_app.documentos_maestros,
                        competidores_maestros=self.parent_app.competidores_maestros,
                        responsables_maestros=self.parent_app.responsables_maestros,
                        replace_tables={'documentos_maestros'}
                    )
            
            self.actualizar_listas_docs()
            self._notify_docs_changed()
        self.grab_set()

    def editar_documento(self):
        docs = self._find_docs_from_selection()
        if not docs or len(docs) > 1: return
        doc = docs[0]
        dlg = DialogoAgregarDocumento(self, "Editar Documento", initial_data=doc, categorias=self.categorias)
        if dlg.result:
            # Corrección: El resultado de DialogoAgregarDocumento es un diccionario
            datos = dlg.result
            doc.codigo = datos['codigo']
            doc.nombre = datos['nombre']
            doc.categoria = datos['categoria']
            doc.comentario = datos['comentario']
            self.actualizar_listas_docs()
            self._notify_docs_changed()
        self.grab_set()

    def cambiar_estado_documento(self):
        docs = self._find_docs_from_selection()
        if not docs: return
        nuevo = not all(d.presentado for d in docs)
        for d in docs: d.presentado = nuevo
        self.actualizar_listas_docs(); self._notify_docs_changed()

    def eliminar_documento(self):
        docs = self._find_docs_from_selection()
        if not docs: return
        if messagebox.askyesno("Confirmar", f"¿Eliminar {len(docs)} documento(s) seleccionado(s)?", parent=self):
            for d in docs:
                try: self.licitacion.documentos_solicitados.remove(d)
                except ValueError: pass
            self.actualizar_listas_docs(); self._notify_docs_changed()
            self.grab_set()

    def cambiar_estado_subsanable(self):
        docs = self._find_docs_from_selection()
        if not docs or len(docs) > 1: return
        doc = docs[0]
        estados = ["No Definido", "Subsanable", "No Subsanable"]
        try: idx = estados.index(doc.subsanable)
        except ValueError: idx = 0
        doc.subsanable = estados[(idx + 1) % len(estados)]
        self.actualizar_listas_docs(); self._notify_docs_changed()
        self.grab_set()

    def _guardar_responsable_multiple(self, event=None):
        docs = self._find_docs_from_selection()
        nuevo = self.responsable_var.get()
        if docs and nuevo:
            for d in docs: d.responsable = nuevo
            self.actualizar_listas_docs(); self._notify_docs_changed()

    def adjuntar_archivo(self):
        docs = self._find_docs_from_selection()
        if not docs:
            messagebox.showwarning("Sin selección", "Seleccione al menos un documento.", parent=self)
            return
            
        ruta_absoluta = filedialog.askopenfilename(parent=self, title="Seleccionar Archivo")
        if not ruta_absoluta:
            return

        dropbox_base = obtener_ruta_dropbox()
        ruta_para_db = ruta_absoluta # Por defecto, guardamos la ruta completa

        if dropbox_base and ruta_absoluta.startswith(dropbox_base):
            # Si el archivo está DENTRO de Dropbox, calculamos la ruta relativa
            ruta_relativa = os.path.relpath(ruta_absoluta, dropbox_base)
            # Guardamos con separadores universales (/) para consistencia entre sistemas operativos
            ruta_para_db = ruta_relativa.replace(os.sep, '/')
            print(f"Archivo en Dropbox detectado. Guardando ruta relativa: {ruta_para_db}")
        else:
            # Si no está en Dropbox, advertimos al usuario
            messagebox.showinfo("Advertencia de Ruta", 
                "El archivo seleccionado no se encuentra en la carpeta de Dropbox.\n\n"
                "La ruta se guardará de forma absoluta y podría no funcionar en otros PCs.",
                parent=self)

        for doc in docs:
            doc.ruta_archivo = ruta_para_db
            doc.presentado = True
            
        self.actualizar_listas_docs()
        self._notify_docs_changed()

    def ver_archivo(self):
        docs = self._find_docs_from_selection()
        if not docs or len(docs) > 1 or not getattr(docs[0], "ruta_archivo", ""): return
        
        ruta_absoluta = reconstruir_ruta_absoluta(docs[0].ruta_archivo)
        
        if ruta_absoluta and os.path.exists(ruta_absoluta):
            try:
                os.startfile(ruta_absoluta)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}", parent=self)
        else:
            messagebox.showerror("Error", f"No se pudo encontrar el archivo en la ruta:\n{ruta_absoluta}", parent=self)

    def quitar_adjunto(self):
        docs = self._find_docs_from_selection()
        if not docs: return
        
        con_archivo = [d for d in docs if getattr(d, "ruta_archivo", "")]
        if not con_archivo:
            messagebox.showinfo("Sin adjuntos", "Ninguno de los documentos seleccionados tiene archivo adjunto.", parent=self)
            return

        plural = "s" if len(con_archivo) > 1 else ""
        if not messagebox.askyesno("Confirmar", f"¿Quitar el archivo adjunto de {len(con_archivo)} documento{plural}?", parent=self):
            return
            
        for d in con_archivo:
            d.ruta_archivo = ""
            d.presentado = False # Marcar como no presentado si se quita el archivo
            
        self.actualizar_listas_docs()
        self._notify_docs_changed()

    def _toggle_estado_revisado(self):
        docs = self._find_docs_from_selection()
        if not docs: return
        nuevo = not all(getattr(d, "revisado", False) for d in docs)
        for d in docs: d.revisado = nuevo
        self.actualizar_listas_docs(); self._notify_docs_changed()

    def on_guardar_y_continuar(self):
        self._notify_docs_changed(); self.destroy()


    def iniciar_subsanacion(self):
        """Abre el diálogo para gestionar el proceso de subsanación."""
        def guardar_y_refrescar():
            # Primero, se guardan todos los cambios pendientes en la licitación.
            # Esto es crucial para que los documentos nuevos obtengan un ID de la BD.
            self.parent._guardar_sin_cerrar()
            
            # Ahora, actualizamos todas las vistas.
            self.actualizar_listas_docs()
            
            # Finalmente, refrescamos la pestaña de subsanables para mostrar la nueva fecha/estado.
            try:
                # En lugar de borrar y reinsertar, solo actualizamos su contenido.
                # Buscamos el frame de la pestaña.
                tab_frame = self.notebook.nametowidget(self.notebook.tabs()[-1])
                for widget in tab_frame.winfo_children():
                    widget.destroy() # Limpiamos el contenido viejo
                
                # Recreamos el contenido con la información actualizada.
                self._crear_tab_subsanables(tab_frame)
                self._poblar_tab_subsanables()

            except Exception as e:
                print(f"Error refrescando tab de subsanables: {e}")

        # Pasamos la DB correctamente al diálogo.
        DialogoGestionSubsanacion(self, self.licitacion, self.parent.db, guardar_y_refrescar)


    def _rellenar_formulario_seleccionado(self):
        docs_seleccionados = self._find_docs_from_selection()
        if len(docs_seleccionados) != 1:
            # Este chequeo es por seguridad, el botón debería estar deshabilitado
            return

        doc_plantilla = docs_seleccionados[0]
        ruta_plantilla_guardada = getattr(doc_plantilla, "ruta_archivo", None)

        if not ruta_plantilla_guardada:
            messagebox.showerror("Error", "El documento seleccionado no tiene un archivo de plantilla adjunto.", parent=self)
            return

        ruta_plantilla_absoluta = reconstruir_ruta_absoluta(ruta_plantilla_guardada)
        if not ruta_plantilla_absoluta or not os.path.isfile(ruta_plantilla_absoluta):
            messagebox.showerror("Error", f"No se encontró el archivo de plantilla en la ruta:\n{ruta_plantilla_absoluta}", parent=self)
            return

        # 1. Seleccionar la empresa para usar sus datos
        nuestras_empresas = self.parent_app.empresas_registradas
        if not nuestras_empresas:
            messagebox.showerror("Error", "No hay empresas maestras registradas.", parent=self)
            return

        nombres_empresas = sorted([e['nombre'] for e in nuestras_empresas])
        
        empresa_seleccionada_nombre = None
        if len(nombres_empresas) == 1:
            empresa_seleccionada_nombre = nombres_empresas[0]
        else:
            # Usamos un diálogo simple para elegir. Podríamos mejorarlo después.
            top = tk.Toplevel(self)
            top.title("Seleccionar Empresa")
            top.transient(self)
            top.grab_set()
            ttk.Label(top, text="¿Con los datos de qué empresa desea rellenar el formulario?").pack(padx=20, pady=10)
            combo_var = tk.StringVar(value=nombres_empresas[0])
            ttk.Combobox(top, textvariable=combo_var, values=nombres_empresas, state="readonly").pack(padx=20, pady=5)
            
            def on_ok():
                nonlocal empresa_seleccionada_nombre
                empresa_seleccionada_nombre = combo_var.get()
                top.destroy()
            
            ttk.Button(top, text="Aceptar", command=on_ok).pack(pady=10)
            self.wait_window(top)


        if not empresa_seleccionada_nombre:
            return # El usuario cerró el diálogo

        empresa_data = next((e for e in nuestras_empresas if e['nombre'] == empresa_seleccionada_nombre), None)
        if not empresa_data:
            messagebox.showerror("Error", "No se encontraron los datos de la empresa seleccionada.", parent=self)
            return
            
        # 2. Construir el diccionario de contexto con todos los datos
        contexto = {
            "numero_proceso": self.licitacion.numero_proceso,
            "nombre_proceso": self.licitacion.nombre_proceso,
            "institucion": self.licitacion.institucion,
            "lotes_participados": ", ".join(sorted([str(l.numero) for l in self.licitacion.lotes if l.participamos])),
            "fecha_actual": datetime.date.today().strftime("%d/%m/%Y"),
            "empresa_nombre": empresa_data.get("nombre", ""),
            "empresa_rnc": empresa_data.get("rnc", ""),
            "empresa_rpe": empresa_data.get("rpe", ""),
            "empresa_telefono": empresa_data.get("telefono", ""),
            "empresa_correo": empresa_data.get("correo", ""),
            "empresa_direccion": empresa_data.get("direccion", ""),
            "empresa_representante": empresa_data.get("representante", ""),
            "empresa_cargo_representante": empresa_data.get("cargo_representante", "")
        }
        
        # 3. Pedir al usuario dónde guardar el nuevo archivo
        nombre_archivo_sugerido = f"{doc_plantilla.codigo}_{self.licitacion.numero_proceso}_{empresa_data['nombre'].replace(' ', '_')}.docx"
        
        ruta_salida = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Formulario Rellenado",
            initialfile=nombre_archivo_sugerido,
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")]
        )

        if not ruta_salida:
            return

        # 4. Llamar a la función de llenado
        try:
            self.config(cursor="wait")
            self.update_idletasks()
            fill_template(ruta_plantilla_absoluta, ruta_salida, contexto, debug=True)
            messagebox.showinfo("Éxito", f"Documento rellenado y guardado correctamente en:\n{ruta_salida}", parent=self)
            
            if messagebox.askyesno("Abrir Archivo", "¿Desea abrir el documento generado?", parent=self):
                os.startfile(ruta_salida)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al rellenar el documento:\n{e}", parent=self)
        finally:
            self.config(cursor="")

class VentanaMaestroDocumentos(tk.Toplevel):
    def __init__(self, parent, documentos_maestros, categorias, db_manager):
        super().__init__(parent)
        self.parent_app = parent
        self.documentos_maestros = documentos_maestros
        self.categorias_documentos = ["Todas"] + categorias
        self.db = db_manager
        
        self.title("Gestor de Plantillas de Documentos por Empresa")
        self.geometry("950x650") # Un poco más ancha para la nueva tabla
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Panel superior con todos los filtros ---
        filter_frame = ttk.Frame(main_frame, padding=5)
        filter_frame.pack(fill=tk.X, pady=5)
        filter_frame.columnconfigure(1, weight=1) # Hacemos que la búsqueda se expanda

        # Filtro de Empresa
        ttk.Label(filter_frame, text="Seleccionar Empresa:").grid(row=0, column=0, padx=(0,5), sticky="w")
        self.empresa_var = tk.StringVar()
        nombres_empresas = sorted([e['nombre'] for e in self.parent_app.empresas_registradas])
        self.empresa_combo = ttk.Combobox(filter_frame, textvariable=self.empresa_var, values=nombres_empresas, state="readonly")
        self.empresa_combo.grid(row=0, column=1, columnspan=3, sticky="ew")
        self.empresa_combo.bind("<<ComboboxSelected>>", self.actualizar_lista)

        # Filtro de Búsqueda y Categoría
        ttk.Label(filter_frame, text="Buscar:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.search_var.trace_add("write", lambda *args: self.actualizar_lista())

        ttk.Label(filter_frame, text="Categoría:").grid(row=1, column=2, padx=(10,5), pady=5, sticky="w")
        self.categoria_var = tk.StringVar(value="Todas")
        categoria_combo = ttk.Combobox(filter_frame, textvariable=self.categoria_var, values=self.categorias_documentos, state="readonly")
        categoria_combo.grid(row=1, column=3, sticky="ew", pady=5)
        categoria_combo.bind("<<ComboboxSelected>>", lambda *args: self.actualizar_lista())

        # --- Reemplazamos Listbox por Treeview ---
        list_frame = ttk.LabelFrame(main_frame, text="Documentos de la Plantilla", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        cols = ('adjunto', 'codigo', 'nombre', 'categoria')
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        self.tree.heading('adjunto', text='📎')
        self.tree.heading('codigo', text='Código')
        self.tree.heading('nombre', text='Nombre del Documento')
        self.tree.heading('categoria', text='Categoría')
        
        self.tree.column('adjunto', width=30, anchor=tk.CENTER, stretch=False)
        self.tree.column('codigo', width=150)
        self.tree.column('nombre', width=400)
        self.tree.column('categoria', width=120)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_doc_select)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Botones de acción (sin cambios en su creación) ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        btn_frame.columnconfigure(tuple(range(3)), weight=1)
        acciones = {"➕ Agregar Nuevo": self.agregar_doc, "✏️ Editar": self.editar_doc, "🗑️ Eliminar": self.eliminar_doc, "📎 Adjuntar Plantilla": self.adjuntar_archivo, "📂 Ver Plantilla": self.ver_archivo, "❌ Quitar Plantilla": self.quitar_adjunto}
        self.buttons = {}
        for i, (text, cmd) in enumerate(acciones.items()):
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.grid(row=i//3, column=i%3, sticky=tk.EW, padx=5, pady=2)
            self.buttons[text] = btn
        
        self.on_doc_select(None)
        self.protocol("WM_DELETE_WINDOW", self.cerrar_y_recargar)

    def cerrar_y_recargar(self):
        self.parent_app.cargar_datos_desde_db()
        self.destroy()

    def actualizar_lista(self, event=None):
        """Método rediseñado para filtrar y poblar el Treeview."""
        self.tree.delete(*self.tree.get_children())
        
        # Obtenemos los valores de todos los filtros
        empresa_sel = self.empresa_var.get()
        search_term = self.search_var.get().lower()
        categoria_sel = self.categoria_var.get()

        if not empresa_sel:
            return

        # Filtramos la lista de documentos maestros
        docs_filtrados = []
        for doc in self.documentos_maestros:
            if doc.empresa_nombre == empresa_sel:
                # Filtro por categoría
                if categoria_sel != "Todas" and doc.categoria != categoria_sel:
                    continue
                # Filtro por búsqueda de texto
                if search_term not in doc.nombre.lower() and search_term not in doc.codigo.lower():
                    continue
                docs_filtrados.append(doc)
        
        # Llenamos el Treeview con los resultados
        for doc in sorted(docs_filtrados, key=lambda d: (d.categoria, d.nombre)):
            adjunto_icono = "📎" if hasattr(doc, 'ruta_archivo') and doc.ruta_archivo else ""
            self.tree.insert('', tk.END, iid=doc.id, values=(
                adjunto_icono,
                doc.codigo,
                doc.nombre,
                doc.categoria
            ))
        self.on_doc_select(None)

    def on_doc_select(self, event=None):
        doc = self._get_selected_doc()
        state_if_doc = "normal" if doc else "disabled"
        for key in ["✏️ Editar", "🗑️ Eliminar", "📎 Adjuntar Plantilla"]:
            self.buttons[key].config(state=state_if_doc)
        
        if doc:
            state_if_path = "normal" if hasattr(doc, 'ruta_archivo') and doc.ruta_archivo else "disabled"
            self.buttons["📂 Ver Plantilla"].config(state=state_if_path)
            self.buttons["❌ Quitar Plantilla"].config(state=state_if_path)
        else:
            self.buttons["📂 Ver Plantilla"].config(state="disabled")
            self.buttons["❌ Quitar Plantilla"].config(state="disabled")

    def _get_selected_doc(self):
        """Método actualizado para obtener el documento desde la selección del Treeview."""
        selection = self.tree.selection()
        if not selection:
            return None
        doc_id = int(selection[0])
        return next((doc for doc in self.documentos_maestros if doc.id == doc_id), None)

    def adjuntar_archivo(self):
        if (doc := self._get_selected_doc()) and (ruta := filedialog.askopenfilename(parent=self, title="Seleccionar Archivo de Plantilla")):
            doc.ruta_archivo = ruta
            self._save_and_reload()

    def ver_archivo(self):
        if (doc := self._get_selected_doc()) and hasattr(doc, 'ruta_archivo') and doc.ruta_archivo:
            try:
                os.startfile(doc.ruta_archivo)
            except Exception:
                messagebox.showerror("Error", "No se pudo abrir el archivo.", parent=self)

    def quitar_adjunto(self):
        if (doc := self._get_selected_doc()):
            doc.ruta_archivo = ""
            self._save_and_reload()

    def agregar_doc(self):
        empresa = self.empresa_var.get()
        if not empresa:
            messagebox.showerror("Error", "Primero debe seleccionar una empresa.", parent=self)
            return
        
        dialogo = DialogoAgregarDocumento(self, "Nueva Plantilla", categorias=self.categorias_documentos, empresa_actual=empresa)
        if dialogo.result:
            datos = dialogo.result
        
            if any(d.codigo == datos["codigo"] and d.empresa_nombre == empresa for d in self.documentos_maestros):
                messagebox.showerror("Error", f"Ya existe un documento con el código '{datos['codigo']}' para esta empresa.", parent=self)
                return
            
            nuevo_doc = Documento(
                codigo=datos["codigo"], nombre=datos["nombre"], categoria=datos["categoria"],
                comentario=datos["comentario"], empresa_nombre=empresa
            )
            self.documentos_maestros.append(nuevo_doc)
            
            # El argumento correcto es 'documentos_maestros'
            self.parent_app.db.save_master_lists(
                empresas=self.parent_app.empresas_registradas,
                instituciones=self.parent_app.instituciones_registradas,
                documentos_maestros=self.parent_app.documentos_maestros,
                competidores_maestros=self.parent_app.competidores_maestros,
                responsables_maestros=self.parent_app.responsables_maestros,
                replace_tables={'documentos_maestros'}
            )
            
            self.parent_app.cargar_datos_desde_db()
            self.actualizar_lista()
 
 
 
    def editar_doc(self):
        if not (doc := self._get_selected_doc()):
            return
        dialogo = DialogoAgregarDocumento(self, "Editar Plantilla", initial_data=doc, categorias=self.categorias_documentos, empresa_actual=doc.empresa_nombre)
        if dialogo.result:
            datos = dialogo.result
            doc.codigo, doc.nombre, doc.categoria, doc.comentario = datos["codigo"], datos["nombre"], datos["categoria"], datos["comentario"]
            self._save_and_reload()

    def eliminar_doc(self):
        if (doc := self._get_selected_doc()) and messagebox.askyesno("Confirmar", f"¿Está seguro de que desea eliminar la plantilla '{doc.nombre}'?", parent=self):
            self.documentos_maestros.remove(doc)
            self._save_and_reload()

    def _save_and_reload(self):
        self.parent_app.db.save_master_lists(
            empresas=self.parent_app.empresas_registradas,
            instituciones=self.parent_app.instituciones_registradas,
            documentos_maestros=self.documentos_maestros,
            competidores_maestros=self.parent_app.competidores_maestros,
            responsables_maestros=self.parent_app.responsables_maestros,
            replace_tables={'documentos_maestros'}
        )
        self.parent_app.cargar_datos_desde_db()
        self.actualizar_lista()


class VentanaSeleccionMaestro(tk.Toplevel):
    # ... (sin cambios)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Gestión de Datos Maestros")
        self.geometry("450x250")
        self.resizable(False, False)
        self.grab_set()

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Seleccione el área que desea gestionar:", font=("Helvetica", 11)).pack(pady=(0, 15))

        style = ttk.Style(self)
        style.configure("Maestro.TButton", font=("Helvetica", 10, "bold"), padding=10)

        ttk.Button(main_frame, text="📚 Gestionar Plantillas de Documentos", style="Maestro.TButton", 
                   command=self.abrir_maestro_docs).pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="🏢 Gestionar Empresas e Instituciones", style="Maestro.TButton", 
                   command=self.abrir_maestro_entidades).pack(fill=tk.X, pady=5)

    def abrir_maestro_docs(self):
        self.destroy()
        self.parent_app.abrir_ventana_maestro_docs()

    def abrir_maestro_entidades(self):
        self.destroy()
        self.parent_app.abrir_ventana_maestro_entidades()

class VentanaMaestroEntidades(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent

        # Copias de trabajo (no tocan las listas reales hasta "Guardar y Cerrar")
        self.entidades_copia = {
            'empresa':       [dict(e) for e in self.parent_app.empresas_registradas],
            'institucion':   [dict(i) for i in self.parent_app.instituciones_registradas],
        }

        self.title("Gestor de Empresas e Instituciones")
        self.geometry("950x550")
        self.grab_set()

        notebook = ttk.Notebook(self, padding="10")
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- Pestaña Empresas ---
        self.widgets_empresas = self._crear_panel_entidad(notebook, "empresa")
        notebook.add(self.widgets_empresas['frame'], text="Empresas")

        # --- Pestaña Instituciones ---
        self.widgets_instituciones = self._crear_panel_entidad(notebook, "institucion")
        notebook.add(self.widgets_instituciones['frame'], text="Instituciones")

        ttk.Button(self, text="✅ Guardar y Cerrar", command=self.cerrar_y_guardar)\
            .pack(pady=10, ipady=4)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.cargar_listas()

    def _crear_panel_entidad(self, parent, entity_type):
        frame = ttk.Frame(parent, padding="10")
        # ... (el código de tree_frame y tree se mantiene igual) ...
        tree_frame = ttk.LabelFrame(frame, text=f"Listado de {entity_type.capitalize()}s")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        cols = ("nombre", "rnc", "telefono", "correo")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            tree.heading(col, text=col.capitalize())
        tree.column("nombre",   width=250)
        tree.column("rnc",      width=120)
        tree.column("telefono", width=120)
        tree.column("correo",   width=250)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        # --- INICIO DEL CAMBIO ---
        num_columns = 4 if entity_type == 'empresa' else 3
        btn_frame.columnconfigure(tuple(range(num_columns)), weight=1)

        btn_add    = ttk.Button(btn_frame, text="➕ Agregar",  command=lambda: self._agregar(entity_type))
        btn_edit   = ttk.Button(btn_frame, text="✏️ Editar",   state="disabled", command=lambda: self._editar(entity_type))
        btn_delete = ttk.Button(btn_frame, text="🗑️ Eliminar", state="disabled", command=lambda: self._eliminar(entity_type))

        btn_add.grid(row=0, column=0, sticky=tk.EW, padx=5)
        btn_edit.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        # Agregamos el botón de perfil solo para empresas
        if entity_type == 'empresa':
            btn_perfil = ttk.Button(btn_frame, text="📈 Ver Perfil", state="disabled", command=self._ver_perfil_empresa)
            btn_perfil.grid(row=0, column=2, sticky=tk.EW, padx=5)
            btn_delete.grid(row=0, column=3, sticky=tk.EW, padx=5)
        else:
            btn_delete.grid(row=0, column=2, sticky=tk.EW, padx=5)
        
        status_var = tk.StringVar()
        ttk.Label(frame, textvariable=status_var, anchor=tk.W, relief=tk.SUNKEN).pack(fill=tk.X, side=tk.BOTTOM, pady=(10,0), ipady=2)
        
        # Pasamos el nuevo botón de perfil a la función que lo habilita/deshabilita
        widgets_a_controlar = (btn_edit, btn_delete, btn_perfil) if entity_type == 'empresa' else (btn_edit, btn_delete)
        tree.bind("<<TreeviewSelect>>", lambda e: self._on_selection_change(tree, *widgets_a_controlar))
        # --- FIN DEL CAMBIO ---
        
        tree.bind("<Double-1>", lambda e: self._editar(entity_type))

        return {"frame": frame, "tree": tree, "status_var": status_var}

    def _on_selection_change(self, tree, *buttons_to_toggle):
        state = "normal" if tree.selection() else "disabled"
        for btn in buttons_to_toggle:
            if btn: # Comprobamos que el botón existe
                btn.config(state=state)

    def _get_entity_list_and_tree(self, entity_type):
        if entity_type == 'empresa':
            return self.entidades_copia['empresa'], self.widgets_empresas['tree']
        else:
            return self.entidades_copia['institucion'], self.widgets_instituciones['tree']
        
    def _ver_perfil_empresa(self):
        entity_list, tree = self._get_entity_list_and_tree('empresa')
        if not tree.selection(): return
        
        nombre_empresa = tree.item(tree.selection()[0], 'values')[0]
        VentanaPerfilEmpresaNuestra(self, nombre_empresa, self.parent_app.gestor_licitaciones)


    # ----------------- Carga / CRUD -----------------
# En la clase VentanaMaestroEntidades, REEMPLAZA este método:

    def cargar_listas(self):
        for entity_type, widgets in [("empresa", self.widgets_empresas), ("institucion", self.widgets_instituciones)]:
            tree, entity_list = widgets["tree"], self.entidades_copia[entity_type]
            tree.delete(*tree.get_children())
            
            # --- LÓGICA ANTI-DUPLICADOS ---
            nombres_vistos = set()
            entidades_unicas = []
            for e in entity_list:
                nombre = e.get('nombre', '').strip()
                if nombre and nombre.lower() not in nombres_vistos:
                    nombres_vistos.add(nombre.lower())
                    entidades_unicas.append(e)
            # --- FIN DE LA LÓGICA ---

            # Usar la lista ya filtrada y ordenada
            for e in sorted(entidades_unicas, key=lambda x: x.get('nombre', '')):
                values = (e.get('nombre', ''), e.get('rnc', ''), e.get('telefono', ''), e.get('correo', ''))
                if e.get('nombre'):
                    tree.insert("", tk.END, values=values, iid=e['nombre'])
            widgets["status_var"].set(f"Total: {len(entidades_unicas)} {entity_type}s")
# En la clase VentanaMaestroEntidades, REEMPLAZA este método:

    def _agregar(self, entity_type):
        dialogo = DialogoGestionarEntidad(self, f"Agregar {entity_type.capitalize()}", entity_type)
        if dialogo.result and dialogo.result.get('nombre'):
            nueva_entidad_data = dialogo.result
            nombre_nuevo = nueva_entidad_data['nombre'].strip()

            if not nombre_nuevo:
                messagebox.showwarning("Dato requerido", "El nombre no puede estar vacío.", parent=self)
                return

            entity_list, _ = self._get_entity_list_and_tree(entity_type)

            # --- CORRECCIÓN CLAVE ---
            # Verificar si ya existe, ignorando mayúsculas/minúsculas
            if any(e.get('nombre', '').strip().lower() == nombre_nuevo.lower() for e in entity_list):
                messagebox.showerror("Error", f"Ya existe un(a) {entity_type} con el nombre '{nombre_nuevo}'.", parent=self)
                return
            
            entity_list.append(nueva_entidad_data)
            self.cargar_listas()

    def _editar(self, entity_type):
        entity_list, tree = self._get_entity_list_and_tree(entity_type)
        if not tree.selection():
            return
        selected_name = tree.selection()[0]
        entidad_actual = next((e for e in entity_list if e.get('nombre') == selected_name), None)
        if not entidad_actual:
            return
        dialogo = DialogoGestionarEntidad(self, f"Editar {entity_type.capitalize()}", entity_type, initial_data=entidad_actual)
        if dialogo.result and dialogo.result.get('nombre'):
            entidad_actual.update(dialogo.result)
            self.cargar_listas()

    def _eliminar(self, entity_type):
        """
        Evita eliminar:
         - una INSTITUCIÓN usada por alguna licitación (lic.institucion == nombre)
         - una EMPRESA usada por alguna licitación en su lista multi-empresa (nombre ∈ [e.nombre for e in lic.empresas_nuestras])
        """
        entity_list, tree = self._get_entity_list_and_tree(entity_type)
        if not tree.selection():
            return
        selected_name = tree.selection()[0]

        # ¿Está en uso?
        en_uso = False
        for lic in getattr(self.parent_app, "gestor_licitaciones", []):
            if entity_type == 'institucion':
                if str(getattr(lic, "institucion", "")) == selected_name:
                    en_uso = True
                    break
            else:  # empresa
                # lic.empresas_nuestras es una lista de objetos Empresa
                empresas_lic = {str(e) for e in getattr(lic, "empresas_nuestras", [])}
                if selected_name in empresas_lic:
                    en_uso = True
                    break

        if en_uso:
            messagebox.showerror("Error",
                                 f"'{selected_name}' está en uso en una o más licitaciones y no puede ser eliminado.",
                                 parent=self)
            return

        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{selected_name}' del catálogo?"):
            entity_list[:] = [e for e in entity_list if e.get('nombre') != selected_name]
            self.cargar_listas()

    def cerrar_y_guardar(self):
        try:
            self.parent_app.db.save_master_lists(
                empresas=self.parent_app.empresas_registradas,
                instituciones=self.parent_app.instituciones_registradas,
                documentos=self.parent_app.documentos_maestros,
                competidores=self.parent_app.competidores_maestros,
                responsables=self.parent_app.responsables_maestros,
                replace_tables={'empresas_maestras', 'instituciones_maestras'}  # ajusta si quieres incluir más
            )
        except Exception as e:
            print("[WARN] Falló save_master_lists:", e)
        finally:
            # cierra la ventana sin romper la app si hubo error
            try:
                self.destroy()
            except Exception:
                pass





class VentanaReporte(tk.Toplevel):
    # ... (sin cambios)
    def __init__(self, parent, licitacion):
        super().__init__(parent); self.licitacion = licitacion
        self.title(f"Reporte: {self.licitacion.nombre_proceso}"); self.geometry("950x800"); self.grab_set()

        main_frame = ttk.Frame(self, padding="15"); main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame); header_frame.pack(fill=tk.X, pady=(0, 10))
        kpis = {"Estado Actual": self.licitacion.estado, "Progreso Docs": f"{self.licitacion.get_porcentaje_completado():.1f}%", 
                "Días Restantes": self.licitacion.get_dias_restantes(), "Diferencia Oferta": f"{self.licitacion.get_diferencia_porcentual():.2f}%"}
        for i, (titulo, valor) in enumerate(kpis.items()): self.crear_kpi(header_frame, titulo, valor, i)

        middle_frame = ttk.Frame(main_frame); middle_frame.pack(fill=tk.X, pady=10)
        self.crear_seccion_cronograma(middle_frame); self.crear_seccion_financiera(middle_frame)

        notebook = ttk.Notebook(main_frame); notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        tabs = {"Checklist de Documentos": self.crear_checklist_documentos, "Competidores y Resultados": self.crear_seccion_competidores}
        for text, func in tabs.items(): tab = ttk.Frame(notebook, padding=(0,10)); notebook.add(tab, text=text); func(tab)
        
        export_frame = ttk.Frame(main_frame); export_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM)
        ttk.Label(export_frame, text="Exportar este reporte:").pack(side=tk.LEFT, padx=(0,10))
        if REPORTLAB_AVAILABLE: ttk.Button(export_frame, text="📄 Exportar a PDF", command=lambda: self.exportar_reporte('pdf')).pack(side=tk.LEFT, padx=5)
        if OPENPYXL_AVAILABLE: ttk.Button(export_frame, text="📈 Exportar a Excel", command=lambda: self.exportar_reporte('excel')).pack(side=tk.LEFT, padx=5)

    def exportar_reporte(self, formato):
        ext = '.pdf' if formato == 'pdf' else '.xlsx'
        filetypes = [('PDF', '*.pdf')] if formato == 'pdf' else [('Excel', '*.xlsx')]
        default_filename = f"Reporte_{self.licitacion.numero_proceso.replace(' ', '_')}{ext}"
        if file_path := filedialog.asksaveasfilename(parent=self, title=f"Guardar como {formato.upper()}", initialfile=default_filename, filetypes=filetypes, defaultextension=ext):
            ReportGenerator().generate_bid_results_report(self.licitacion, file_path)
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{file_path}", parent=self)

    def crear_kpi(self, parent, titulo, valor, columna):
        frame = ttk.LabelFrame(parent, text=titulo, padding=10); frame.grid(row=0, column=columna, padx=5, sticky="ew")
        parent.grid_columnconfigure(columna, weight=1)
        ttk.Label(frame, text=valor, font=("Helvetica", 14, "bold")).pack()
        if "%" in valor: ttk.Progressbar(frame, orient="horizontal", length=150, mode="determinate", value=float(valor.replace('%',''))).pack(pady=(5,0))

    def crear_seccion_cronograma(self, parent):
        frame = ttk.LabelFrame(parent, text="Cronograma", padding=10); frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        tree = ttk.Treeview(frame, columns=("evento", "fecha", "estado"), show="headings", height=7)
        tree.heading("evento", text="Hito"); tree.heading("fecha", text="Fecha Límite"); tree.heading("estado", text="Estado")
        tree.column("evento", width=250); tree.column("fecha", anchor=tk.CENTER); tree.column("estado", anchor=tk.CENTER)
        tree.tag_configure('cumplido', background='#d4edda'); tree.tag_configure('incumplido', background='#f8d7da')
        for evento, datos in sorted(self.licitacion.cronograma.items()):
            tree.insert("", tk.END, values=(evento, datos.get("fecha_limite", "N/D"), datos.get("estado", "Pendiente")), tags=(datos.get("estado", "Pendiente").lower(),))
        tree.pack(fill=tk.BOTH, expand=True)

# En la clase VentanaReporte, reemplaza este método

    def crear_seccion_financiera(self, parent):
        frame = ttk.LabelFrame(parent, text="Resumen Financiero (Solo Lotes Participados)", padding=10)
        frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # Usar solo_participados=True para reflejar los montos relevantes
        base = self.licitacion.get_monto_base_total(solo_participados=True)
        ofertado = self.licitacion.get_oferta_total(solo_participados=True)
        diferencia_pct = self.licitacion.get_diferencia_porcentual(solo_participados=True)

        data = {
            "Monto Base (Presupuesto):": base, 
            "Monto de Nuestra Oferta:": ofertado, 
            "Diferencia Absoluta:": ofertado - base, 
            "Diferencia Porcentual:": diferencia_pct
        }

        for i, (label, value) in enumerate(data.items()):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            is_pct = "Porcentual" in label
            format_str = "{:,.2f}%" if is_pct else "RD$ {:,.2f}"
            ttk.Label(frame, text=format_str.format(value), font=("Helvetica", 10, "bold")).grid(row=i, column=1, sticky=tk.E, padx=10)

    def crear_checklist_documentos(self, parent):
        tree = ttk.Treeview(parent, columns=("estado", "nombre", "categoria", "subsanable"), show="headings")
        tree.heading("estado", text="✓"); tree.heading("nombre", text="Documento"); tree.heading("categoria", text="Categoría"); tree.heading("subsanable", text="Condición")
        tree.column("estado", width=30, anchor=tk.CENTER); tree.column("nombre", width=400); tree.column("categoria", anchor=tk.CENTER); tree.column("subsanable", anchor=tk.CENTER)
        tree.tag_configure('no_subsanable_pendiente', background='#f8d7da')
        for doc in sorted(self.licitacion.documentos_solicitados, key=lambda d: (d.categoria, d.nombre)):
            tag = 'no_subsanable_pendiente' if doc.subsanable == "No Subsanable" and not doc.presentado else ""
            tree.insert("", tk.END, values=("✅" if doc.presentado else "❌", doc.nombre, doc.categoria, doc.subsanable), tags=(tag,))
        tree.pack(fill=tk.BOTH, expand=True)

    def crear_seccion_competidores(self, parent_frame):
        self.participants_frame = ttk.LabelFrame(parent_frame, text="Resultados Detallados"); self.participants_frame.pack(fill=tk.BOTH, expand=True)
        self._actualizar_vista_participantes()


    def _actualizar_vista_participantes(self, event=None):
        for widget in self.participants_frame.winfo_children():
            widget.destroy()

        tree = ttk.Treeview(
            self.participants_frame,
            columns=("participante", "monto_ofertado", "monto_habilitado",
                    "fase_a_general", "monto_base_lote", "dif_lote", "ganador"),
            show="headings"
        )

        tree.heading("participante", text="Participante / Lote Ofertado")
        tree.heading("monto_ofertado", text="Monto Ofertado")
        tree.heading("monto_habilitado", text="Monto Habilitado (Fase A)")
        tree.heading("fase_a_general", text="Estado Fase A")
        tree.heading("monto_base_lote", text="Monto Base Lote")
        tree.heading("dif_lote", text="% Diferencia")
        tree.heading("ganador", text="Ganador")

        tree.column("participante", width=350, anchor=tk.W)
        tree.column("monto_ofertado", width=130, anchor=tk.E)
        tree.column("monto_habilitado", width=150, anchor=tk.E)
        tree.column("fase_a_general", width=110, anchor=tk.CENTER)
        tree.column("monto_base_lote", width=130, anchor=tk.E)
        tree.column("dif_lote", width=90, anchor=tk.CENTER)
        tree.column("ganador", width=90, anchor=tk.CENTER)

        tree.tag_configure('competidor', font=('Helvetica', 10, 'bold'))
        tree.tag_configure('ganador_real', background='#d4edda', font=('Helvetica', 9, 'bold'))
        tree.tag_configure('nuestra_empresa', background='#cce5ff')
        tree.tag_configure('descalificado', foreground='red')
        tree.tag_configure('pendiente', foreground='orange')

        def _norm(s: str) -> str:
            s = (s or "").strip()
            s = s.replace("➡️", "").replace("(Nuestra Oferta)", "")
            while "  " in s:
                s = s.replace("  ", " ")
            return s.upper()

        # Fase A evaluada
        hito_eval = self.licitacion.cronograma.get("Informe de Evaluacion Tecnica", {})
        estado_hito_cumplido = hito_eval.get("estado") == "Cumplido"
        estados_que_implican_fase_A_evaluada = {"Adjudicada", "Descalificado Fase B", "Sobre B Entregado"}
        fase_A_evaluada = estado_hito_cumplido or (self.licitacion.estado in estados_que_implican_fase_A_evaluada)

        # Ganadores reales (por lote) + nuestras empresas
        ganadores_por_lote = {str(l.numero): (l.ganador_nombre or "").strip() for l in self.licitacion.lotes}
        nuestras_empresas = {_norm(str(e)) for e in getattr(self.licitacion, "empresas_nuestras", [])}

        # Participantes + nuestra fila
        participantes = [o.__dict__ for o in getattr(self.licitacion, "oferentes_participantes", [])]
        nuestras = ", ".join(str(e) for e in getattr(self.licitacion, "empresas_nuestras", [])) or "Nuestras Empresas"
        nuestras_ofertas = [
            {'lote_numero': l.numero, 'monto': l.monto_ofertado, 'paso_fase_A': l.fase_A_superada}
            for l in getattr(self.licitacion, "lotes", [])
            if l.participamos
        ]
        participantes.append({"nombre": f"➡️ {nuestras} (Nuestra Oferta)", "es_nuestra": True, "ofertas_por_lote": nuestras_ofertas})

        # Monto habilitado (si procede)
        for p in participantes:
            if fase_A_evaluada:
                p["monto_habilitado"] = sum(o.get('monto', 0) for o in p.get("ofertas_por_lote", []) if o.get('paso_fase_A', True))
            else:
                p["monto_habilitado"] = 0

        participantes_orden = sorted(
            participantes,
            key=lambda it: it["monto_habilitado"] if it["monto_habilitado"] > 0 else float('inf')
        )

        for p in participantes_orden:
            tags = ['competidor']
            if p.get("es_nuestra"):
                tags.append('nuestra_empresa')

            if fase_A_evaluada:
                habilitado = any(o.get('paso_fase_A', False) for o in p.get('ofertas_por_lote', [])) if p.get('ofertas_por_lote') else False
                estado_general = "Habilitado" if habilitado else "Descalificado"
                if not habilitado:
                    tags.append('descalificado')
                monto_habilitado_str = f"RD$ {p['monto_habilitado']:,.2f}"
            else:
                estado_general = "Pendiente"
                monto_habilitado_str = "N/D"
                tags.append('pendiente')

            parent_id = tree.insert(
                "", tk.END,
                values=(p['nombre'],
                        f"RD$ {sum(o.get('monto', 0) for o in p.get('ofertas_por_lote', [])):,.2f}",
                        monto_habilitado_str, estado_general, "", "", ""),
                tags=tuple(tags)
            )

            # === CLAVE: nombres del padre "desglosados" para matchear "BARNHOUSE SERVICES, ZOEC CIVIL" ===
            nombre_participante_norm = _norm(p['nombre'])
            nombres_en_padre = {x.strip() for x in nombre_participante_norm.split(",") if x.strip()}  # {"BARNHOUSE SERVICES", "ZOEC CIVIL"}

            gano_alguno = 0

            for oferta in sorted(p.get('ofertas_por_lote', []), key=lambda o: o.get('lote_numero', '')):
                lote_num = str(oferta.get('lote_numero'))
                lote_obj = next((l for l in getattr(self.licitacion, "lotes", []) if str(l.numero) == lote_num), None)
                lote_nombre = getattr(lote_obj, "nombre", "N/E")

                # Montos y %dif
                base_str, dif_pct_str = "N/D", "N/D"
                if lote_obj:
                    base = float(getattr(lote_obj, "monto_base", 0) or 0)
                    of_m = float(oferta.get('monto', 0) or 0)
                    base_str = f"RD$ {base:,.2f}"
                    if base > 0 and of_m > 0:
                        dif_pct_str = f"{((of_m - base)/base)*100:.2f}%"

                # Estado Fase A por lote
                if fase_A_evaluada:
                    paso_a = oferta.get('paso_fase_A', True) if p.get('es_nuestra') else oferta.get('paso_fase_A', False)
                    estado_a = "✅" if paso_a else "❌"
                    lote_tags = [] if paso_a else ['descalificado']
                else:
                    estado_a = "⏳"; lote_tags = ['pendiente']

                # === DECISIÓN DE GANADOR (mejorada) ===
                ganador_real = _norm(ganadores_por_lote.get(lote_num, ""))

                es_ganador_esta_fila = False
                if ganador_real:
                    # 1) Si es nuestra fila y el ganador está en nuestras empresas
                    if p.get('es_nuestra') and (ganador_real in nuestras_empresas):
                        es_ganador_esta_fila = True
                    # 2) Si el nombre del ganador aparece en el texto del padre (separado por comas)
                    elif ganador_real in nombres_en_padre:
                        es_ganador_esta_fila = True
                    # 3) fallback: si el texto del padre comienza exactamente con el ganador
                    elif nombre_participante_norm.startswith(ganador_real):
                        es_ganador_esta_fila = True

                ganador_txt = "Sí" if es_ganador_esta_fila else "No"
                if es_ganador_esta_fila:
                    lote_tags.append('ganador_real')
                    gano_alguno += 1

                tree.insert(
                    parent_id, tk.END,
                    values=(f"    ↳ Lote {lote_num}: {lote_nombre}",
                            f"RD$ {oferta.get('monto', 0):,.2f}",
                            "", estado_a, base_str, dif_pct_str, ganador_txt),
                    tags=tuple(lote_tags)
                )

            # Si ganó al menos un lote: pinto el padre y muestro conteo
            if gano_alguno > 0:
                current_tags = set(tree.item(parent_id, 'tags') or ())
                current_tags.add('ganador_real')
                tree.item(parent_id, tags=tuple(current_tags))
                vals = list(tree.item(parent_id, 'values'))
                vals[-1] = f"Sí ({gano_alguno})"
                tree.item(parent_id, values=tuple(vals))

        tree.pack(fill=tk.BOTH, expand=True)


class DialogoSeleccionarReporteGlobal(simpledialog.Dialog):
    def __init__(self, parent, title="Generar Reporte Global"): super().__init__(parent, title)
    def body(self, master):
        ttk.Label(master, text="Tipo de Reporte:").pack(pady=5)
        self.report_type_var = tk.StringVar(value="Historial por Institución")
        ttk.Combobox(master, state="readonly", textvariable=self.report_type_var, values=["Historial por Institución"]).pack(pady=5)
        ttk.Label(master, text="Formato de Salida:").pack(pady=5)
        self.format_var = tk.StringVar(value="Excel")
        ttk.Combobox(master, state="readonly", textvariable=self.format_var, values=["Excel", "PDF"]).pack(pady=5)
    def apply(self): self.result = (self.report_type_var.get(), self.format_var.get())


class VentanaRestauracion(tk.Toplevel):
    """Muestra una lista de backups disponibles y permite restaurar uno."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.db = parent.db
        self.title("Restaurar desde Copia de Seguridad")
        self.geometry("800x400")
        self.grab_set()

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Seleccione una copia de seguridad para restaurar. La aplicación se reiniciará.",
                  wraplength=750, justify=tk.LEFT).pack(pady=(0, 10))

        cols = ('fecha', 'comentario', 'ruta')
        self.tree = ttk.Treeview(main_frame, columns=cols, show='headings')
        self.tree.heading('fecha', text='Fecha de Creación')
        self.tree.heading('comentario', text='Comentario')
        self.tree.heading('ruta', text='Ruta del Archivo')
        self.tree.column('fecha', width=150)
        self.tree.column('comentario', width=300)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self._on_restore)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Restaurar Selección", command=self._on_restore).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Abrir Manualmente...", command=self._restore_manual).pack(side=tk.RIGHT)

        self._cargar_backups()

    def _cargar_backups(self):
        self.tree.delete(*self.tree.get_children())
        try:
            self.db.cursor.execute("SELECT timestamp, comentario, ruta_archivo FROM backups_log ORDER BY timestamp DESC")
            for ts, com, ruta in self.db.cursor.fetchall():
                # Solo mostrar backups que todavía existen en el disco
                if os.path.exists(ruta):
                    fecha = datetime.datetime.fromisoformat(ts).strftime('%Y-%m-%d %H:%M:%S')
                    self.tree.insert('', tk.END, values=(fecha, com, ruta))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial de backups:\n{e}", parent=self)

    def _on_restore(self, event=None):
        if not self.tree.selection():
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un respaldo de la lista.", parent=self)
            return

        ruta_backup = self.tree.item(self.tree.selection()[0], 'values')[2]
        self._proceder_restauracion(ruta_backup)

    def _restore_manual(self):
        ruta_backup = filedialog.askopenfilename(parent=self, title="Seleccionar Copia de Seguridad Manualmente",
                                                 filetypes=[("DB files", "*.db")])
        if ruta_backup:
            self._proceder_restauracion(ruta_backup)

    def _proceder_restauracion(self, ruta_backup):
        if messagebox.askyesno("¡ADVERTENCIA!",
                                 "Se reemplazarán TODOS los datos actuales con los del respaldo.\n\nEsta acción no se puede deshacer. ¿Desea continuar?",
                                 icon='warning', parent=self):
            try:
                self.parent_app.db.close()
                shutil.copyfile(ruta_backup, self.parent_app.db_path)
                messagebox.showinfo("Éxito", "Base de datos restaurada. La aplicación se reiniciará.", parent=self)
                self.parent_app._reiniciar_app()
            except Exception as e:
                messagebox.showerror("Error", f"Falló la restauración:\n{e}", parent=self)
                # Intentar reconectar a la BD original si la restauración falla
                self.parent_app._conectar_a_db(self.parent_app.db_path)



class VentanaSanityCheck(tk.Toplevel):
    """Una interfaz para ejecutar chequeos de integridad y reparar la base de datos."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.db = parent.db
        self.issues_found = {}

        self.title("Diagnóstico y Reparación de Base de Datos")
        self.geometry("700x500")
        self.grab_set()

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Controles Superiores ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(controls_frame, text="🔎 Ejecutar Diagnóstico", command=self.run_checks).pack(side=tk.LEFT)
        self.btn_repair = ttk.Button(controls_frame, text="🛠️ Aplicar Correcciones", state="disabled", command=self.apply_fixes)
        self.btn_repair.pack(side=tk.LEFT, padx=10)

        # --- Ventana de Reporte ---
        report_frame = ttk.LabelFrame(main_frame, text="Reporte de Diagnóstico", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True)

        self.report_text = tk.Text(report_frame, wrap=tk.WORD, height=10, font=("Consolas", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self.report_text.insert(tk.END, "Presione 'Ejecutar Diagnóstico' para comenzar...")
        self.report_text.config(state="disabled")

    def run_checks(self):
        self.report_text.config(state="normal")
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, "Ejecutando diagnóstico, por favor espere...\n\n")
        self.update_idletasks() # Forzar actualización de la UI

        self.issues_found = self.db.run_sanity_checks()

        has_orphans = bool(self.issues_found.get('orphans'))
        has_missing_indexes = bool(self.issues_found.get('missing_indexes'))

        if not (has_orphans or has_missing_indexes):
            self.report_text.insert(tk.END, "✅ ¡Excelente! No se encontraron problemas de integridad en la base de datos.")
            self.btn_repair.config(state="disabled")
        else:
            self.report_text.insert(tk.END, "⚠️ Se encontraron los siguientes problemas:\n\n")
            if has_orphans:
                self.report_text.insert(tk.END, "--- Registros Huérfanos Encontrados ---\n")
                for table, ids in self.issues_found['orphans'].items():
                    self.report_text.insert(tk.END, f"  - Tabla '{table}': {len(ids)} registros sin padre.\n")

            if has_missing_indexes:
                self.report_text.insert(tk.END, "\n--- Índices de Rendimiento Faltantes ---\n")
                for index in self.issues_found['missing_indexes']:
                    self.report_text.insert(tk.END, f"  - Falta el índice '{index['name']}' en la tabla '{index['table']}'.\n")

            self.report_text.insert(tk.END, "\nSe recomienda aplicar las correcciones.")
            self.btn_repair.config(state="normal")

        self.report_text.config(state="disabled")

    def apply_fixes(self):
        if not self.issues_found:
            messagebox.showinfo("Información", "No hay problemas que corregir.", parent=self)
            return

        if messagebox.askyesno("Confirmar Reparación",
                                 "Se aplicarán las siguientes correcciones:\n"
                                 "  - Se eliminarán permanentemente los registros huérfanos.\n"
                                 "  - Se crearán los índices de rendimiento faltantes.\n\n"
                                 "¿Desea continuar?", icon='warning', parent=self):

            success, message = self.db.auto_repair(self.issues_found)
            if success:
                messagebox.showinfo("Éxito", message, parent=self)
                # Volver a ejecutar los chequeos para confirmar que todo está limpio
                self.run_checks()
            else:
                messagebox.showerror("Error", message, parent=self)

def seleccionar_o_crear_db_inicial():
    """
    Usa una ventana raíz temporal para manejar la selección de la base de datos
    antes de que la aplicación principal sea creada.
    """
    root_temp = tk.Tk()
    root_temp.withdraw()

    config_file = "config.json"
    db_path = None
    try:
        with open(config_file, 'r') as f: config = json.load(f)
        last_db = config.get("db_path")
        # --- MEJORA: Comprobar que la ruta no solo exista, sino que sea un archivo ---
        if last_db and os.path.isfile(last_db):
            if messagebox.askyesno("Reanudar Sesión", f"¿Desea abrir la última base de datos utilizada?\n\n{last_db}", parent=root_temp):
                db_path = last_db
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    if not db_path:
        if messagebox.askyesno("Iniciar", "¿Desea abrir un archivo de base de datos existente?", parent=root_temp):
            db_path = filedialog.askopenfilename(parent=root_temp, title="Seleccionar Base de Datos", filetypes=[("Database files", "*.db")])
        else:
            db_path = filedialog.asksaveasfilename(parent=root_temp, title="Crear Nueva Base de Datos", filetypes=[("Database files", "*.db")], defaultextension=".db")

    root_temp.destroy()
    
    # Se retorna la ruta solo si no es una cadena vacía.
    return db_path if db_path else None



class AppLicitacionesGUI(ThemedTk):

    def __init__(self, db_path):
            super().__init__()
            self.set_theme("arc")

            self.__version__ = "10.0-Stable"
            self.db_path = db_path
            self.api_key = None 
            self._cargar_configuracion() 

            self.title(f"Gestor de Licitaciones v{self.__version__} - [{os.path.basename(db_path)}]")
            self.geometry("1400x750")

            self._conectar_a_db(db_path)
            self._guardar_configuracion(db_path=self.db_path) 
            
            # Inicialización de atributos
            self.gestor_licitaciones = []
            self.empresas_registradas = []
            self.instituciones_registradas = []
            self.documentos_maestros = []
            self.competidores_maestros = LoggingList("competidores_maestros", self) 
            self.responsables_maestros = []
            self.categorias_documentos = ["Legal", "Financiera", "Técnica", "Sobre B", "Otros"]
            self.perfil_entorno = tk.StringVar()
            self.posibles_perfiles = ["Local (Rápido)", "Red / Dropbox (Seguro)"]
            self.debug_mode = False
            self.debug_viewer = None
            self.debug_mode_var = tk.BooleanVar(value=False)
            self.reporter = ReportGenerator()
            
            # Estilos
            style = ttk.Style(self)
            style.configure("Urgent.TLabel", background="red", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
            style.configure("Soon.TLabel", background="orange", foreground="black", font=('Helvetica', 10, 'bold'), padding=5)
            style.configure("Safe.TLabel", background="green", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
            style.configure("Done.TLabel", background="grey", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
            style.configure("Small.TButton", font=("Helvetica", 9), padding=4)
            
            # Creación de la interfaz
            self.crear_widgets()
            # --- INICIO CAMBIO: Mover la configuración de tags aquí, después de crear self.tree ---
            self.tree.tag_configure('ganada', background='#E6F4EA', foreground='#1E7D32')
            self.tree.tag_configure('perdida', background='#FDECEA', foreground='#B71C1C')
            self.tree.tag_configure('proceso', background='#FFF8E1', foreground='#8D6E00')
            self.tree.tag_configure('finalizadas_header', background='#F3F4F6', foreground='#374151', font=('Helvetica', 9, 'bold'))
            self.tree.tag_configure('proximo', foreground='#D35400', font=('Helvetica', 9, 'bold'))
            self.tree.tag_configure('subsana', foreground='red', font=('Helvetica', 9, 'bold'))
            self.tree.tag_configure('subsanacion_pendiente', background='#FFE0B2') # Color naranja
            self.crear_menu_contextual()
            self._crear_menu_superior()
            self.protocol("WM_DELETE_WINDOW", self.al_cerrar)
            
            # Carga de datos
            self.cargar_datos_desde_db()
            self._realizar_backup_automatico()
            self.reporter = ReportGenerator()

    def _cargar_configuracion(self):
        """Lee el archivo config.json y carga la clave API si existe."""
        try:
            with open("config.json", 'r') as f:
                config = json.load(f)
                self.api_key = config.get("api_key", None)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está vacío, no hacemos nada.
            self.api_key = None

    def _diagnosticar_ganadores_actual(self):
        # toma la licitación actualmente seleccionada (ajusta si tu app usa otro método)
        lic = getattr(self, "licitacion_seleccionada", None)
        if not lic or not getattr(self, "db", None):
            print("No hay licitación seleccionada o DB no disponible.")
            return
        print("\n=== DEBUG GANADORES ===")
        print("Proceso:", getattr(lic, "numero_proceso", "N/A"), "| ID:", getattr(lic, "id", None))
        dump = self.db.debug_dump_ganadores_por_licitacion(getattr(lic, "id", -1))
        print("BD -> licitacion_ganadores_lote:")
        for r in dump["db"]:
            print("  Lote", r["lote_numero"], "| ganador_nombre:", r["ganador_nombre"], "| empresa_nuestra:", r["empresa_nuestra"])
        print("MEMORIA -> lotes:")
        for l in getattr(lic, "lotes", []):
            print("  Lote", getattr(l, "numero", "?"),
                "| ganador_nombre:", getattr(l, "ganador_nombre", None),
                "| empresa_nuestra:", getattr(l, "empresa_nuestra", None),
                "| ganado_por_nosotros:", getattr(l, "ganado_por_nosotros", None))
        print("=== FIN DEBUG ===\n")


    def abrir_ventana_detalles_desde_objeto(self, licitacion_obj):
        if licitacion_obj:
            # --- AÑADE self.instituciones_registradas AL FINAL ---
            VentanaDetalles(self, licitacion_obj, self.cargar_datos_desde_db, self.documentos_maestros, self.categorias_documentos, self.db, self.instituciones_registradas)

    def _actualizar_contadores_barra_estado(self):
        """Calcula y actualiza las etiquetas de la barra de estado inferior."""
        if not hasattr(self, 'status_label_total'): # Evita errores si aún no se ha creado la UI
            return

        total_ganadas = 0
        total_perdidas = 0
        total_lotes_ganados = 0
        estados_perdida_directa = ["Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]

        for lic in self.gestor_licitaciones:
            if lic.estado == "Adjudicada":
                lotes_ganados_en_esta_lic = sum(1 for lote in lic.lotes if getattr(lote, "ganado_por_nosotros", False))
                if lotes_ganados_en_esta_lic > 0:
                    total_ganadas += 1
                    total_lotes_ganados += lotes_ganados_en_esta_lic
                else:
                    total_perdidas += 1
            elif lic.estado in estados_perdida_directa:
                total_perdidas += 1

        total_activas = len(self.gestor_licitaciones) - total_ganadas - total_perdidas
        
        self.status_label_total.config(text=f"Datos Cargados. {len(self.gestor_licitaciones)} Licitaciones en Total")
        self.status_label_activas.config(text=f"Activas: {total_activas}")
        self.status_label_ganadas.config(text=f"Ganadas: {total_ganadas}")
        self.status_label_lotes_ganados.config(text=f"Lotes Ganados: {total_lotes_ganados}")
        self.status_label_perdidas.config(text=f"Perdidas: {total_perdidas}")

    def _realizar_backup_automatico(self):
        """Crea un backup si el último tiene más de 1 día de antigüedad."""
        try:
            self.db.cursor.execute("SELECT MAX(timestamp) FROM backups_log")
            last_backup_ts_str = self.db.cursor.fetchone()[0]

            if last_backup_ts_str:
                last_backup_date = datetime.datetime.fromisoformat(last_backup_ts_str).date()
                if (datetime.date.today() - last_backup_date).days < 1:
                    print("INFO: Backup automático omitido, ya se hizo uno hoy.")
                    return # Ya se hizo un backup hoy
            
            print("INFO: Realizando backup automático...")
            timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d")
            backup_folder = os.path.join(os.path.dirname(self.db_path), "Backups")
            os.makedirs(backup_folder, exist_ok=True)
            
            base_filename = os.path.basename(self.db_path).replace('.db', '')
            backup_filename = f"{base_filename}_auto_{timestamp_str}.db"
            backup_path = os.path.join(backup_folder, backup_filename)

            # Pausar, copiar, reconectar
            self.db.close()
            shutil.copyfile(self.db_path, backup_path)
            self._conectar_a_db(self.db_path)

            self.db.cursor.execute(
                "INSERT INTO backups_log (timestamp, ruta_archivo, comentario) VALUES (?, ?, ?)",
                (datetime.datetime.now().isoformat(), backup_path, "Backup Automático")
            )
            self.db.conn.commit()
            print(f"INFO: Backup automático creado en {backup_path}")

        except Exception as e:
            print(f"ERROR: Falló el backup automático: {e}")
            # Asegurarse de reconectar si algo falla
            if not getattr(self.db, 'conn', None):
                self._conectar_a_db(self.db_path)

    def _get_tooltip_text(self):
        try:
            row_id = self.tree.identify_row(self.tree.winfo_pointery() - self.tree.winfo_rooty())
            column_id = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            if not row_id or row_id == "finalizadas_parent": return None
            
            # <-- CORRECCIÓN: El nombre del proceso ahora es la columna #3 y el índice 2
# Ahora 'nombre' es la columna #2 (índice 1)
            if column_id == '#2':
                return self.tree.item(row_id, 'values')[1]
        except Exception: 
            return None
        return None

    def _seleccionar_o_crear_db(self):
        config_file = "config.json"
        try:
            with open(config_file, 'r') as f: config = json.load(f)
            last_db = config.get("db_path")
            if last_db and os.path.exists(last_db):
                if messagebox.askyesno("Reanudar Sesión", f"¿Desea abrir la última base de datos utilizada?\n\n{last_db}"):
                    return last_db
        except (FileNotFoundError, json.JSONDecodeError): pass

        if messagebox.askyesno("Iniciar", "¿Desea abrir un archivo de base de datos existente?"):
            return filedialog.askopenfilename(title="Seleccionar Base de Datos", filetypes=[("Database files", "*.db")])
        else:
            return filedialog.asksaveasfilename(title="Crear Nueva Base de Datos", filetypes=[("Database files", "*.db")], defaultextension=".db")
            
    def _conectar_a_db(self, db_path):
        try:
            self.db = DatabaseManager(db_path)
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo abrir la base de datos:\n{e}")
            self.destroy()
            sys.exit()

# En gestor_licitaciones_db_2.py, dentro de la clase AppLicitacionesGUI

# En la clase AppLicitacionesGUI
# En la clase AppLicitacionesGUI, REEMPLAZA este método:

    def _guardar_configuracion(self, db_path=None):
        config = {}
        config_file = "config.json"
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        if db_path and isinstance(db_path, str) and db_path.strip():
            config["db_path"] = db_path

        # --- LÍNEA NUEVA ---
        # Añade la clave API al diccionario de configuración si la tenemos
        if self.api_key:
            config["api_key"] = self.api_key
        # --- FIN LÍNEA NUEVA ---

        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Advertencia: No se pudo escribir en {config_file}: {e}")

    def _reiniciar_app(self): self.destroy(); main()

    def analizar_competidores(self, licitaciones_filtradas): 
        """
        Analiza participación de competidores en las licitaciones filtradas,
        excluyendo nuestras empresas.
        """
        competidores = {}

        for lic in licitaciones_filtradas:
            # Lista de nuestras empresas en esta licitación
            nombres_empresas_nuestras = {str(e) for e in lic.empresas_nuestras}

            for oferente in lic.oferentes_participantes:
                # Saltar nuestras propias empresas
                if oferente.nombre in nombres_empresas_nuestras:
                    continue

                stats = competidores.setdefault(oferente.nombre, {
                    "participaciones": 0,
                    "monto_total_habilitado": 0.0,
                    "conteo_monto": 0
                })

                stats["participaciones"] += 1

                monto_hab = oferente.get_monto_total_ofertado(solo_habilitados=True)
                if monto_hab > 0:
                    stats["monto_total_habilitado"] += monto_hab
                    stats["conteo_monto"] += 1
        
        # Convertir a lista y calcular promedios
        resultado = []
        for nombre, datos in competidores.items():
            promedio = (datos["monto_total_habilitado"] / datos["conteo_monto"]) if datos["conteo_monto"] > 0 else 0
            resultado.append({
                "nombre": nombre,
                "participaciones": datos["participaciones"],
                "monto_promedio": promedio
            })

        # Ordenar por participaciones
        return sorted(resultado, key=lambda x: x["participaciones"], reverse=True)

    def abrir_ventana_maestro_responsables(self):
        VentanaMaestroResponsables(self)


    def _crear_menu_superior(self):
        import tkinter as tk  # por si este archivo no lo tiene arriba
        self.menu_bar = tk.Menu(self)
        self.winfo_toplevel().config(menu=self.menu_bar)

        menus_data = {
            "Archivo": [
                ("Seleccionar/Crear Base de Datos...", self._reiniciar_app), None,
                ("Crear Copia de Seguridad...", self._crear_copia_seguridad),
                ("Restaurar desde Copia...", self._restaurar_desde_copia), None,
                ("Salir", self.al_cerrar)
            ],
            "Editar": [
                ("Agregar Licitación...", self.abrir_ventana_agregar),
                ("Gestionar Empresas e Instituciones", self.abrir_ventana_maestro_entidades),
                ("Gestionar Plantillas de Documentos", self.abrir_ventana_maestro_docs),
                ("Gestionar Catálogo de Competidores", self.abrir_ventana_maestro_competidores),
                ("Gestionar Catálogo de Responsables", self.abrir_ventana_maestro_responsables),
                ("Gestionar Kits de Requisitos", self.abrir_ventana_maestro_kits), None,
            ],
            "Ver": [
                ("Dashboard Global", self.abrir_dashboard_global)
            ],
            "Reportes": [
                ("Reporte de Licitación Seleccionada", self.abrir_ventana_reporte),
                ("Reportes Globales", self.abrir_ventana_reportes_globales)
            ],
            "Herramientas": [
                # Diagnóstico / pruebas
                ("Diagnóstico y Reparación de BD...", self.abrir_ventana_sanity_check),
                ("Ejecutar Pruebas de Integridad...", self.ejecutar_smoke_tests),

                # <<< NUEVO: Backfill de ganadores >>>
                ("Reparar datos de ganadores (backfill)", self._accion_backfill_ganadores),

                # <<< NUEVO: Diagnóstico ganadores (actual) >>>
                ("Diagnóstico ganadores (actual)", self._diagnosticar_ganadores_actual),

                {"type": "checkbutton", "label": "Activar Modo Diagnóstico",
                "variable": self.debug_mode_var, "command": self._toggle_debug_mode},
                None,
                {"type": "submenu", "label": "Perfil de Entorno", "options": self.posibles_perfiles, "variable": self.perfil_entorno}
            ],
            "Ayuda": [
                ("Acerca de...", self._mostrar_acerca_de)
            ]
        }

        for menu_label, command_list in menus_data.items():
            menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label=menu_label, menu=menu)

            for item in command_list:
                if item is None:
                    menu.add_separator()

                elif isinstance(item, dict) and item.get("type") == "submenu":
                    submenu = tk.Menu(menu, tearoff=0)
                    menu.add_cascade(label=item["label"], menu=submenu)
                    for option in item["options"]:
                        submenu.add_radiobutton(
                            label=option,
                            variable=item["variable"],
                            command=self._guardar_perfil_entorno
                        )

                elif isinstance(item, dict) and item.get("type") == "checkbutton":
                    menu.add_checkbutton(
                        label=item["label"],
                        variable=item["variable"],
                        command=item["command"]
                    )

                else:
                    menu.add_command(label=item[0], command=item[1])

    def _on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection or selection[0] == "finalizadas_parent":
            self.status_display_label.config(text="-- Selecciona una Fila --", style="Done.TLabel")
            return
        
        # <-- CORRECCIÓN: Índice cambiado a [1] para obtener el código del proceso
        numero_proceso_sel = self.tree.item(selection[0], 'values')[0]

        if licitacion := next((lic for lic in self.gestor_licitaciones if lic.numero_proceso == numero_proceso_sel), None):
            self._update_status_display(licitacion)

    def _update_status_display(self, licitacion):
        self.status_display_label.config(text=licitacion.get_dias_restantes())
        style_to_use = "Done.TLabel"
        hoy = datetime.date.today()
        eventos_futuros = [datetime.datetime.strptime(d["fecha_limite"], '%Y-%m-%d').date() for d in licitacion.cronograma.values() if d.get("estado") == "Pendiente" and d.get("fecha_limite")]
        if eventos_futuros:
            diferencia = (min(eventos_futuros) - hoy).days
            if 0 <= diferencia <= 7: style_to_use = "Urgent.TLabel"
            elif 8 <= diferencia <= 30: style_to_use = "Soon.TLabel"
            elif diferencia > 30: style_to_use = "Safe.TLabel"
        self.status_display_label.config(style=style_to_use)

    def _mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", f"Gestor de Licitaciones\nVersión {self.__version__}\n\nDesarrollado por ZOEC CIVIL.")

# En la clase AppLicitacionesGUI, reemplaza este método

    def _crear_copia_seguridad(self):
        if not self.db_path: return

        # Pedir un comentario opcional al usuario
        comentario = simpledialog.askstring("Crear Copia de Seguridad",
                                            "Añada un comentario para este respaldo (ej: 'Antes de importar masivamente'):",
                                            parent=self)
        if comentario is None: # Si el usuario presiona "Cancelar"
            return

        try:
            timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_folder = os.path.join(os.path.dirname(self.db_path), "Backups")
            os.makedirs(backup_folder, exist_ok=True)

            base_filename = os.path.basename(self.db_path).replace('.db', '')
            backup_filename = f"{base_filename}_backup_{timestamp_str}.db"
            backup_path = os.path.join(backup_folder, backup_filename)

            # Pausamos la conexión a la BD actual para copiar el archivo de forma segura
            self.db.close()
            shutil.copyfile(self.db_path, backup_path)

            # Nos reconectamos y guardamos el registro del backup
            self._conectar_a_db(self.db_path)
            self.db.cursor.execute(
                "INSERT INTO backups_log (timestamp, ruta_archivo, comentario) VALUES (?, ?, ?)",
                (datetime.datetime.now().isoformat(), backup_path, comentario)
            )
            self.db.conn.commit()

            messagebox.showinfo("Éxito", f"Copia de seguridad creada con éxito en:\n{backup_path}", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la copia de seguridad:\n{e}", parent=self)
            # Intentar reconectar incluso si falla
            if not self.db.conn:
                self._conectar_a_db(self.db_path)


    def _restaurar_desde_copia(self):
        """Abre la ventana de gestión de restauración."""
        VentanaRestauracion(self)

    def aplicar_filtros(self):
        criterios = { 'estado': self.filtro_estado_var.get(), 'empresa': self.filtro_empresa_var.get(),
                      'busqueda': self.filtro_busqueda_var.get().lower(), 'lote': self.filtro_lote_var.get().lower() }
        lista_filtrada = self.gestor_licitaciones[:]
        if criterios['estado']: lista_filtrada = [l for l in lista_filtrada if l.estado == criterios['estado']]
        if criterios['empresa']: lista_filtrada = [l for l in lista_filtrada if str(l.empresa_nuestra) == criterios['empresa']]
        if criterios['busqueda']: lista_filtrada = [l for l in lista_filtrada if criterios['busqueda'] in f"{l.nombre_proceso} {l.numero_proceso} {l.institucion}".lower()]
        if criterios['lote']: lista_filtrada = [l for l in lista_filtrada if any(criterios['lote'] in f"{lt.numero} {lt.nombre}".lower() for lt in l.lotes)]
        self.actualizar_tabla_gui(lista_filtrada)

    def limpiar_filtros(self):
        for var in [self.filtro_estado_var, self.filtro_empresa_var, self.filtro_busqueda_var, self.filtro_lote_var]: var.set('')
        self.aplicar_filtros()

    def actualizar_combos_filtros(self):
        self.filtro_estado_combo['values'] = [""] + sorted({l.estado for l in self.gestor_licitaciones})
        # Reunir todas las empresas de todas las licitaciones
        todas_empresas = set()
        for l in self.gestor_licitaciones:
            for e in l.empresas_nuestras:
                todas_empresas.add(str(e))

        self.filtro_empresa_combo['values'] = [""] + sorted(todas_empresas)

# EN LA CLASE AppLicitacionesGUI, DENTRO DE gestor_licitaciones_db.py

    def cargar_datos_desde_db(self):
        lic_data, emp_data, inst_data, docs_data, comp_maestros, resp_maestros = self.db.get_all_data()
        self.gestor_licitaciones = [Licitacion(**data) for data in lic_data]
        for lic in self.gestor_licitaciones:
            if not getattr(lic, 'id', None):
                continue
            # --- Inyectar ganadores por lote desde la BD (ESQUEMA NUEVO) ---
            try:
                filas = self.db.get_ganadores_por_lote(lic.id)  # devuelve dicts con ganador_nombre y empresa_nuestra (si aplica)
                by_lote = {str(r.get("lote_numero")): r for r in filas}

                # Conjunto con nombres de nuestras empresas para comparar rápido
                nuestras_empresas = {str(e).strip() for e in getattr(lic, "empresas_nuestras", [])}

                for lote in lic.lotes:
                    key = str(getattr(lote, "numero", ""))
                    info = by_lote.get(key)

                    if not info:
                        # limpiar por si venía algo colgado
                        lote.ganador_nombre = ""
                        lote.ganado_por_nosotros = False
                        continue

                    ganador = (info.get("ganador_nombre") or "").strip()
                    emp_nuestra_row = (info.get("empresa_nuestra") or "").strip()
                    emp_nuestra_lote = (getattr(lote, "empresa_nuestra", "") or "").strip()

                    lote.ganador_nombre = ganador

                    # Regla: es nuestro si (a) la fila tiene empresa_nuestra, o
                    # (b) la empresa_nuestra del lote coincide con el ganador, o
                    # (c) el ganador es alguna de nuestras empresas cargadas en la licitación.
                    es_nuestro = bool(emp_nuestra_row) \
                                or (emp_nuestra_lote and ganador and emp_nuestra_lote == ganador) \
                                or (ganador in nuestras_empresas)

                    lote.ganado_por_nosotros = bool(es_nuestro)

                    # (Opcional) marca 'ganador' en las ofertas de competidores para este lote
                    if hasattr(lic, "oferentes_participantes") and lic.oferentes_participantes:
                        for comp in lic.oferentes_participantes:
                            for o in comp.ofertas_por_lote:
                                if str(o.get("lote_numero")) == key:
                                    o["ganador"] = (comp.nombre.strip() == ganador)

            except Exception as e:
                print("[WARN] No se pudo inyectar ganadores por lote al cargar:", e)
            # --- fin bloque de inyección ---

        self.empresas_registradas = emp_data
        self.instituciones_registradas = inst_data
        self.documentos_maestros = [Documento(**data) for data in docs_data]
        self.competidores_maestros.clear()
        self.competidores_maestros.extend(comp_maestros)
        self.responsables_maestros = resp_maestros
        perfil_guardado = self.db.get_setting('env_profile', self.posibles_perfiles[0])
        self.perfil_entorno.set(perfil_guardado)
        print(f"Perfil de Entorno cargado: '{perfil_guardado}'")
        debug_state = self.db.get_setting('debug', 'false').lower() == 'true'
        self.debug_mode_var.set(debug_state)
        self._toggle_debug_mode(inicializando=True)
        self.actualizar_tabla_gui()
        self.actualizar_combos_filtros()

        # --- ✅ INICIO DE LA LÓGICA CORREGIDA ---
# Al final de la función cargar_datos_desde_db, reemplaza el bloque del contador

        self.actualizar_tabla_gui()
        self.actualizar_combos_filtros()
        
        # Llama a la nueva función centralizada para actualizar los contadores
        self._actualizar_contadores_barra_estado()
    def al_cerrar(self):
        # (opcional) prints de diagnóstico
        try:
            print("\n=== [APP] Cierre: guardando listas maestras (no destructivo) ===")
            print(f" - empresas: {len(self.empresas_registradas)}")
            print(f" - instituciones: {len(self.instituciones_registradas)}")
            print(f" - documentos_maestros: {len(self.documentos_maestros)}")
            print(f" - competidores_maestros: {len(self.competidores_maestros)}")
            print(f" - responsables_maestros: {len(self.responsables_maestros)}")
        except Exception as e:
            print(f"[APP] (warning) No se pudo contar alguna lista: {e}")

        # Guardado NO destructivo: no pasar replace_tables aquí
        try:
            self.db.save_master_lists(
                empresas=self.empresas_registradas,
                instituciones=self.instituciones_registradas,
                documentos_maestros=self.documentos_maestros,
                competidores_maestros=self.competidores_maestros,
                responsables_maestros=self.responsables_maestros,
                replace_tables=None
            )
        except Exception as e:
            print(f"[APP] Error guardando listas maestras al cerrar: {e}")
        finally:
            try:
                self.db.close()
            except Exception:
                pass
            self.destroy()

    def crear_menu_contextual(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📝 Editar Detalles", command=self.abrir_ventana_detalles)
        self.context_menu.add_command(label="🐑 Duplicar Licitación", command=self.duplicar_licitacion)
        self.context_menu.add_separator(); self.context_menu.add_command(label="🗑️ Eliminar Licitación", command=self.eliminar_licitacion)
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
        Tooltip(self.tree, text_func=self._get_tooltip_text)

    def mostrar_menu_contextual(self, event):
        if iid := self.tree.identify_row(event.y):
            self.tree.selection_set(iid); self.tree.focus(iid); self.context_menu.post(event.x_root, event.y_root)


    def crear_widgets(self):
            # === NOTEBOOK con pestañas ===
            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill="both", expand=True)

            # --- Pestaña 1: Licitaciones (la vista de tabla principal) ---
            self.tab_licitaciones = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_licitaciones, text="📑 Licitaciones")

            # --- Pestaña 2: Dashboard (NUEVA) ---
            self.tab_dashboard = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(self.tab_dashboard, text="📊 Dashboard General")
            
            # --- Pestaña 3: Análisis de Fallas (Reubicada) ---
            self.tab_fallas_a = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_fallas_a, text="🔍 Análisis de Fallas Fase A")

            # ================== CONTENIDO DE LA PESTAÑA "Licitaciones" ==================
            main_frame = ttk.Frame(self.tab_licitaciones, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            filter_frame = ttk.LabelFrame(main_frame, text="Filtros y Búsqueda", padding="10")
            filter_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.filtro_busqueda_var = tk.StringVar()
            self.filtro_busqueda_var.trace_add('write', lambda *a: self.aplicar_filtros())
            self.filtro_lote_var = tk.StringVar()
            self.filtro_lote_var.trace_add('write', lambda *a: self.aplicar_filtros())
            self.filtro_estado_var = tk.StringVar()
            self.filtro_empresa_var = tk.StringVar()

            ttk.Label(filter_frame, text="🔍 Buscar Proceso:").grid(row=0, column=0, padx=(0,5), sticky="w")
            ttk.Entry(filter_frame, textvariable=self.filtro_busqueda_var, width=30).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(filter_frame, text="📦 Contiene Lote:").grid(row=0, column=2, padx=(10,5), sticky="w")
            ttk.Entry(filter_frame, textvariable=self.filtro_lote_var, width=30).grid(row=0, column=3, padx=5, pady=5)
            ttk.Label(filter_frame, text="Estado:").grid(row=1, column=0, padx=(0,5), sticky="w")
            self.filtro_estado_combo = ttk.Combobox(filter_frame, textvariable=self.filtro_estado_var, state="readonly", width=28)
            self.filtro_estado_combo.grid(row=1, column=1, padx=5, pady=5)
            self.filtro_estado_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())
            ttk.Label(filter_frame, text="Empresa:").grid(row=1, column=2, padx=(10,5), sticky="w")
            self.filtro_empresa_combo = ttk.Combobox(filter_frame, textvariable=self.filtro_empresa_var, state="readonly", width=28)
            self.filtro_empresa_combo.grid(row=1, column=3, padx=5, pady=5)
            self.filtro_empresa_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())
            ttk.Button(filter_frame, text="🧹 Limpiar Filtros", command=self.limpiar_filtros).grid(row=0, column=4, rowspan=2, padx=(20,0), ipady=5)
            ttk.Separator(filter_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky="ew", pady=10)
            status_display_frame = ttk.LabelFrame(filter_frame, text="Próximo Vencimiento")
            status_display_frame.grid(row=0, column=5, rowspan=2, padx=(20, 5), pady=5, sticky="nsew")
            self.status_display_label = ttk.Label(status_display_frame, text="-- Selecciona una Fila --", anchor="center", style="Done.TLabel")
            self.status_display_label.pack(fill=tk.BOTH, expand=True)
            filter_frame.columnconfigure(5, weight=1)

            table_frame = ttk.Frame(main_frame)
            table_frame.pack(fill=tk.BOTH, expand=True)
            cols = ('codigo', 'nombre', 'empresa', 'dias_restantes', 'porcentaje_docs', 'diferencia', 'monto_ofertado', 'estatus')
            self.tree = ttk.Treeview(table_frame, columns=cols, show='headings')
            self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
            self.tree.bind("<Double-1>", self.abrir_vista_detallada_lotes)
            headings = {'codigo':'Código', 'nombre':'Nombre Proceso', 'empresa':'Empresa','dias_restantes':'Restan', 'porcentaje_docs':'% Docs', 'diferencia':'% Dif.','monto_ofertado':'Monto Ofertado', 'estatus':'Estatus'}
            for col, txt in headings.items(): self.tree.heading(col, text=txt)
            widths = {'codigo': 140, 'nombre': 450, 'empresa': 150, 'dias_restantes': 120, 'porcentaje_docs': 75, 'diferencia': 75, 'monto_ofertado': 140, 'estatus': 100}
            for col, width in widths.items():
                anchor = tk.W
                if col not in ['codigo', 'nombre', 'empresa', 'monto_ofertado', 'dias_restantes']: anchor = tk.CENTER
                elif col == 'monto_ofertado': anchor = tk.E
                self.tree.column(col, width=width, anchor=anchor, stretch=True)
            # --- INICIO DEL CAMBIO: LUGAR CORRECTO PARA LA CONFIGURACIÓN ---
            self.tree.tag_configure('ganada', background='#E6F4EA', foreground='#1E7D32')
            self.tree.tag_configure('perdida', background='#FDECEA', foreground='#B71C1C')
            self.tree.tag_configure('proceso', background='#FFF8E1', foreground='#8D6E00')
            self.tree.tag_configure('finalizadas_header', background='#F3F4F6', foreground='#374151', font=('Helvetica', 9, 'bold'))
            self.tree.tag_configure('proximo', foreground='#D35400', font=('Helvetica', 9, 'bold'))
            self.tree.tag_configure('subsana', foreground='red', font=('Helvetica', 9, 'bold')) # <-- LÍNEA MOVIDA AQUÍ
            # --- FIN DEL CAMBIO ---
            style = ttk.Style(self); style.map('Treeview', background=[('selected', '#C7F0D8')], foreground=[('selected', '#0B6B32')])
            self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
            self.tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            hscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
            self.tree.configure(xscrollcommand=hscroll.set)
            hscroll.pack(side=tk.BOTTOM, fill=tk.X)
            status_frame = ttk.Frame(main_frame, relief="sunken", padding=(5,2))
            status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
            self.status_label_total = ttk.Label(status_frame, font=("Helvetica", 9)); self.status_label_total.pack(side=tk.LEFT, padx=(0, 5))
            ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')
            self.status_label_activas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="#007bff"); self.status_label_activas.pack(side=tk.LEFT, padx=5)
            self.status_label_ganadas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="green"); self.status_label_ganadas.pack(side=tk.LEFT, padx=5)
            self.status_label_lotes_ganados = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="#2E7D32"); self.status_label_lotes_ganados.pack(side=tk.LEFT, padx=5)
            self.status_label_perdidas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="red"); self.status_label_perdidas.pack(side=tk.LEFT, padx=5)
            style.configure("Accion.TButton", font=("Helvetica", 10, "bold"))
            botones_frame = ttk.Frame(self.tab_licitaciones)
            botones_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))
            ttk.Button(botones_frame, text="➕ Agregar", style="Accion.TButton", command=self.abrir_ventana_agregar).pack(side=tk.LEFT, padx=5, ipady=4)
            ttk.Button(botones_frame, text="📝 Ver/Editar", style="Accion.TButton", command=self.abrir_ventana_detalles).pack(side=tk.LEFT, padx=5, ipady=4)
            Tooltip(self.tree, text_func=self._get_tooltip_text)

            # ================== CONTENIDO DE LA PESTAÑA "Dashboard" ==================
            ttk.Button(self.tab_dashboard, text="🔄 Actualizar Gráficos", command=self.actualizar_dashboard)\
            .pack(pady=10, padx=10, anchor="ne")
            self.dashboard_content = ttk.Frame(self.tab_dashboard)
            self.dashboard_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.dashboard_content.columnconfigure(0, weight=2)
            self.dashboard_content.columnconfigure(1, weight=1)
            self.dashboard_content.rowconfigure(0, weight=1)
            self.dashboard_content.rowconfigure(1, weight=1)

            # ========================================================================
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            self.after(100, self.actualizar_dashboard)

    def _ajustar_ancho_columnas(self, event=None):
        # Porcentajes (pesos) de cada columna — deben sumar 1.0
        pesos = {
            'codigo':           0.12,
            'nombre':           0.38,
            'empresa':          0.10,
            'dias_restantes':   0.12,
            'porcentaje_docs':  0.08,
            'diferencia':       0.08,
            'monto_ofertado':   0.07,
            'estatus':          0.05,
        }
        total = max(self.tree.winfo_width(), 1)
        for col, p in pesos.items():
            # Mínimos simpáticos para que no colapsen
            minimo = 70 if col != 'nombre' else 150
            self.tree.column(col, width=max(int(total * p), minimo))



    def _nuestras_empresas_de(self, lic):
        """Devuelve un set con los nombres de nuestras empresas que participan en una licitación."""
        empresas = set()
        # Primero, revisamos las empresas asignadas a nivel de lote
        for lote in getattr(lic, "lotes", []):
            nombre_empresa_lote = (getattr(lote, "empresa_nuestra", None) or "").strip()
            # --- LÓGICA MEJORADA: Ignoramos si está vacío o es '(Sin Asignar)' ---
            if nombre_empresa_lote and nombre_empresa_lote != "(Sin Asignar)":
                empresas.add(nombre_empresa_lote)
        
        # Si después de revisar los lotes no encontramos ninguna empresa,
        # usamos la lista general de la licitación como respaldo.
        if not empresas:
            for item in getattr(lic, "empresas_nuestras", []):
                nombre = None
                if hasattr(item, 'nombre'):
                    nombre = item.nombre
                elif isinstance(item, dict) and 'nombre' in item:
                    nombre = item.get('nombre')
                
                if nombre and isinstance(nombre, str) and nombre.strip() and nombre.lower() != 'none':
                    empresas.add(nombre.strip())
        return empresas
    

    def _display_empresas_de(self, lic):
        """Devuelve un string amigable para mostrar las empresas de una licitación."""
        # La función _nuestras_empresas_de ahora solo devuelve nombres de empresas reales
        emps = sorted(self._nuestras_empresas_de(lic))
        
        # Si la lista de empresas reales no está vacía, las mostramos.
        # Si está vacía, significa que no hay ninguna asignada, y mostramos "(Sin Asignar)".
        return ", ".join(emps) if emps else "(Sin Asignar)"

    def actualizar_tabla_gui(self, lista_a_mostrar=None):
        lista_para_usar = lista_a_mostrar if lista_a_mostrar is not None else self.gestor_licitaciones
        self.tree.delete(*self.tree.get_children())

        estados_finalizados = ["Adjudicada", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]
        licitaciones_activas = [l for l in lista_para_usar if l.estado not in estados_finalizados]
        licitaciones_finalizadas = [l for l in lista_para_usar if l.estado in estados_finalizados]

        def obtener_clave_ordenamiento(licitacion):
            hoy = datetime.date.today()
            # Si tiene subsanables, es la máxima prioridad
            if any(getattr(doc, 'requiere_subsanacion', False) for doc in licitacion.documentos_solicitados):
                datos_sub = licitacion.cronograma.get("Entrega de Subsanaciones", {})
                if datos_sub.get("fecha_limite"):
                    try: return datetime.datetime.strptime(datos_sub["fecha_limite"], "%Y-%m-%d").date()
                    except: pass
                return datetime.date.min # Poner al principio si no tiene fecha

            fechas = []
            for d in licitacion.cronograma.values():
                if d.get("estado") == "Pendiente" and d.get("fecha_limite"):
                    try:
                        f = datetime.datetime.strptime(d["fecha_limite"], "%Y-%m-%d").date()
                        if f >= hoy: fechas.append(f)
                    except Exception: pass
            return min(fechas) if fechas else datetime.date.max

        activas_ordenadas = sorted(licitaciones_activas, key=obtener_clave_ordenamiento)

        for lic in activas_ordenadas:
            tags = []
            dias_restantes_str = lic.get_dias_restantes()
            
            # Lógica de estilos: naranja y rojo para subsanación, amarillo para proceso normal
            if "SUBSANAR" in dias_restantes_str.upper() or "PENDIENTE" in dias_restantes_str.upper():
                tags.append('subsanacion_pendiente') # Fondo naranja
                tags.append('subsana')              # Texto rojo
            else:
                tags.append('proceso')              # Fondo amarillo/crema
                if "días" in dias_restantes_str:
                    try:
                        dias = int(dias_restantes_str.split()[1])
                        if dias <= 7: tags.append('proximo')
                    except (ValueError, IndexError): pass
            
            monto_ofertado = lic.get_oferta_total(solo_participados=True)
            monto_ofertado_str = f"RD$ {monto_ofertado:,.2f}" if monto_ofertado > 0 else "N/D"
            dif_str = f"{lic.get_diferencia_porcentual(solo_participados=True, usar_base_personal=False):.2f}%" if monto_ofertado > 0 else "N/D"
            
            values = (lic.numero_proceso, lic.nombre_proceso, self._display_empresas_de(lic),
                      dias_restantes_str, f"{lic.get_porcentaje_completado():.1f}%",
                      dif_str, monto_ofertado_str, lic.estado)
            self.tree.insert('', tk.END, values=values, tags=tuple(tags))


        if licitaciones_finalizadas:
            tv = self.tree  # <— usa SIEMPRE el Treeview real

            parent_id = "finalizadas_parent"
            tv.insert(
                '', tk.END, iid=parent_id,
                values=("", f"▶ Licitaciones Finalizadas ({len(licitaciones_finalizadas)})", "", "", "", "", "", ""),
                tags=('finalizadas_header',)
            )

            finalizadas_ordenadas = sorted(licitaciones_finalizadas, key=lambda l: l.nombre_proceso, reverse=True)

            for lic in finalizadas_ordenadas:
                # 1) Calcula los valores de la fila
                monto_ofertado = lic.get_oferta_total(solo_participados=True)
                monto_ofertado_str = f"RD$ {monto_ofertado:,.2f}" if monto_ofertado > 0 else "N/D"
                dif_str = (
                    f"{lic.get_diferencia_porcentual(solo_participados=True, usar_base_personal=False):.2f}%"
                    if monto_ofertado > 0 else "N/D"
                )

                values = (
                    lic.numero_proceso,
                    lic.nombre_proceso,
                    self._display_empresas_de(lic),
                    lic.get_dias_restantes(),
                    f"{lic.get_porcentaje_completado():.1f}%",
                    dif_str,
                    monto_ofertado_str,
                    lic.estado
                )

                # 2) Construye los tags (color de fila)
                tags = []
                estado = getattr(lic, "estado", "Iniciada") or "Iniciada"
                if estado == "Adjudicada":
                    hay_lote_nuestro = any(getattr(l, "ganado_por_nosotros", False) for l in getattr(lic, "lotes", []))
                    tags.append("ganada" if hay_lote_nuestro else "perdida")
                else:
                    tags.append("en_proceso")

                # 3) Inserta la fila usando el Treeview correcto
                tv.insert(parent_id, tk.END, values=values, tags=tuple(tags))

        self._actualizar_contadores_barra_estado()

    def agregar_licitacion_callback(self, nueva_licitacion):
        self.db.save_licitacion(nueva_licitacion); self.cargar_datos_desde_db()




    def duplicar_licitacion(self):
        # 1) Verificación de selección
        iid = self.tree.focus()
        if not iid:
            messagebox.showwarning("Sin Selección", "Selecciona una licitación.")
            return
        if iid == "finalizadas_parent":
            return

        # 2) Obtener la licitación original desde el Treeview
        #    Tomamos el número de proceso (columna 0 de values)
        numero_original = self.tree.item(iid, 'values')[0]
        original = next((l for l in self.gestor_licitaciones if l.numero_proceso == numero_original), None)
        if not original:
            messagebox.showerror("Error", "No se encontró la licitación original.")
            return

        # 3) Pedir la nueva empresa
        empresas_nombres = [e['nombre'] for e in self.empresas_registradas]
        dlg = DialogoSeleccionarEmpresa(self, "Duplicar para...", empresas_nombres)
        nueva_empresa_nombre = dlg.result
        if not nueva_empresa_nombre:
            return  # usuario canceló

        # 4) Clonar usando dict plano para "romper" ids y referencias
        #    (esto evita que se conserve 'id' y que el guardado sea tratado como UPDATE)
        data = original.to_dict()

        # 4.1) Limpiar identificadores y campos que forzarían UPDATE
        data['id'] = None
        data['last_modified'] = None

        # 4.2) Asignar la nueva empresa y ajustar nombre del proceso (opcional)
        data['empresa_nuestra'] = {'nombre': nueva_empresa_nombre}
        data['nombre_proceso'] = f"{original.nombre_proceso} ({nueva_empresa_nombre})"

        # 4.3) Generar un número de proceso NUEVO y único
        base_code = original.numero_proceso
        sufijo = ("".join(filter(str.isalnum, nueva_empresa_nombre))[:10]).upper()
        propuesto = f"{base_code}-{sufijo}"

        existentes = {l.numero_proceso for l in self.gestor_licitaciones}
        nuevo_codigo = propuesto
        contador = 2
        while nuevo_codigo in existentes:
            nuevo_codigo = f"{propuesto}-{contador}"
            contador += 1
        data['numero_proceso'] = nuevo_codigo  # <- clave para que sea un registro distinto

        # 4.4) Resetear documentos (ids/estado/archivos)
        for d in data.get('documentos_solicitados', []):
            d['id'] = None
            d['empresa_nombre'] = nueva_empresa_nombre
            d['presentado'] = False
            d['revisado'] = False
            d['ruta_archivo'] = ""

        # 4.5) Resetear lotes (ids/montos/ganadores)
        for l in data.get('lotes', []):
            l['id'] = None
            l['monto_ofertado'] = 0.0
            l['ganado_por_nosotros'] = False
            l['ganador_nombre'] = ""

        # 4.6) Resetear marcas de ganador en ofertas de competidores
        for comp in data.get('oferentes_participantes', []):
            if 'id' in comp:
                comp['id'] = None
            for o in comp.get('ofertas_por_lote', []):
                o['ganador'] = False  # limpiar cualquier marca previa

        # 4.7) Dejar la licitación en estado inicial (ajusta a tu flujo si lo prefieres)
        data['adjudicada'] = False
        data['adjudicada_a'] = ""
        data['estado'] = "Iniciada"

        # 5) Construir el objeto y guardar (se insertará porque id=None)
        copia = Licitacion(**data)
        try:
            self.db.save_licitacion(copia)
            self.cargar_datos_desde_db()
            messagebox.showinfo(
                "Éxito",
                f"Licitación duplicada para '{nueva_empresa_nombre}' con código '{nuevo_codigo}'.",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo duplicar la licitación:\n{e}", parent=self)


    def abrir_vista_detallada_lotes(self, event=None):
        if not (iid := self.tree.focus()): return
        if iid == "finalizadas_parent": return
        try:
            # <-- CORRECCIÓN: Índice cambiado a [1] para obtener el código del proceso
            numero_proceso_sel = self.tree.item(iid, 'values')[0]
            licitacion = next((l for l in self.gestor_licitaciones if l.numero_proceso == numero_proceso_sel), None)
            if licitacion:
                VentanaVistaLotes(self, licitacion)
        except (IndexError, StopIteration):
            pass

    def abrir_ventana_agregar(self): VentanaAgregarLicitacion(self, self.empresas_registradas, self.instituciones_registradas, self.agregar_licitacion_callback)
    
    def abrir_ventana_detalles(self):
        if not (iid := self.tree.focus()): messagebox.showwarning("Sin Selección", "Selecciona una licitación."); return
        if iid == "finalizadas_parent": return
        if licitacion := next((l for l in self.gestor_licitaciones if l.numero_proceso == self.tree.item(iid, 'values')[0]), None):
            # --- AÑADE self.instituciones_registradas AL FINAL ---
            VentanaDetalles(self, licitacion, self.cargar_datos_desde_db, self.documentos_maestros, self.categorias_documentos, self.db, self.instituciones_registradas)
    
    
    
    def abrir_ventana_reporte(self):
        if not (iid := self.tree.focus()): messagebox.showwarning("Sin Selección", "Selecciona una licitación."); return
        if iid == "finalizadas_parent": return
        # <-- CORRECCIÓN: Índice cambiado a [1] para obtener el código del proceso
        if licitacion := next((l for l in self.gestor_licitaciones if l.numero_proceso == self.tree.item(iid, 'values')[0]), None):
            VentanaReporte(self, licitacion)
            
    def abrir_ventana_reportes_globales(self):
        if not (dialogo_result := DialogoSeleccionarReporteGlobal(self).result): return
        _, formato = dialogo_result; ext = '.xlsx' if formato == 'Excel' else '.pdf'
        if file_path := filedialog.asksaveasfilename(parent=self, title="Guardar Reporte Histórico", initialfile=f"Reporte_Historial_{datetime.date.today()}{ext}", filetypes=[(formato, f"*{ext}")], defaultextension=ext):
            ReportGenerator().generate_institution_history_report(self.gestor_licitaciones, file_path)
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{file_path}", parent=self)
            
    def abrir_dashboard_global(self):
        if not self.gestor_licitaciones: messagebox.showinfo("Sin Datos", "No hay licitaciones para generar un dashboard."); return
        VentanaDashboardGlobal(self, self.gestor_licitaciones)
        
    def abrir_ventana_maestro_docs(self): VentanaMaestroDocumentos(self, self.documentos_maestros, self.categorias_documentos, self.db)
    
    def abrir_ventana_maestros(self): VentanaSeleccionMaestro(self)
    
    def abrir_ventana_maestro_entidades(self): VentanaMaestroEntidades(self)

    def abrir_ventana_maestro_competidores(self):
        VentanaMaestroCompetidores(self)


    def abrir_ventana_maestro_kits(self):
        """Abre la ventana para gestionar los kits de requisitos."""
        VentanaMaestroKits(self)

    # En la clase AppLicitacionesGUI, pega este nuevo método

    def abrir_ventana_sanity_check(self):
        """Abre la ventana de diagnóstico de la base de datos."""
        VentanaSanityCheck(self)

    # En la clase AppLicitacionesGUI, pega este nuevo método

    def _guardar_perfil_entorno(self, *args):
        """Se activa cuando el perfil de entorno cambia y lo guarda en la BD."""
        nuevo_perfil = self.perfil_entorno.get()
        self.db.set_setting('env_profile', nuevo_perfil)
        messagebox.showinfo("Perfil Actualizado",
                            f"Se ha cambiado el perfil a '{nuevo_perfil}'.\n\n"
                            "Se recomienda reiniciar la aplicación para que todos los ajustes surtan efecto.",
                            parent=self)

    # Pega estos 5 nuevos métodos dentro de la clase AppLicitacionesGUI

    def debug_log(self, evento, payload=None):
        """
        Registra un evento en el visor de diagnóstico si el modo está activo.
        """
        if not self.debug_mode:
            return

        # Si el modo está activo pero la ventana no existe, la creamos.
        if not self.debug_viewer or not self.debug_viewer.winfo_exists():
            self.debug_viewer = VentanaVisorDebug(self)

        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        payload_str = ""
        if payload is not None:
            if isinstance(payload, (dict, list)):
                # Usamos json para una visualización bonita de diccionarios o listas
                try:
                    payload_str = json.dumps(payload, indent=2, ensure_ascii=False)
                except TypeError:
                    payload_str = str(payload)
            else:
                payload_str = str(payload)

        mensaje = f"[{timestamp}] -- {evento}"
        if payload_str:
            mensaje += f":\n{payload_str}"

        self.debug_viewer.add_log_entry(mensaje)

    def _toggle_debug_mode(self, inicializando=False):
        """
        Activa o desactiva el modo de diagnóstico y lo guarda en la BD.
        """
        self.debug_mode = self.debug_mode_var.get()
        self.db.set_setting('debug', str(self.debug_mode))

        if self.debug_mode:
            # Si se activa, nos aseguramos de que la ventana exista
            if not self.debug_viewer or not self.debug_viewer.winfo_exists():
                self.debug_viewer = VentanaVisorDebug(self)
            self.debug_viewer.deiconify() # La trae al frente si estaba minimizada
        else:
            # Si se desactiva, cerramos la ventana si existe
            if self.debug_viewer and self.debug_viewer.winfo_exists():
                self.debug_viewer.destroy()
                self.debug_viewer = None

        # No mostramos el mensaje si solo estamos cargando el estado al inicio
        if not inicializando:
            self.debug_log("Modo Diagnóstico", f"Estado: {'Activado' if self.debug_mode else 'Desactivado'}")

    def on_debug_viewer_closed(self):
        """
        Llamado por la ventana de debug cuando el usuario la cierra.
        Actualiza el estado para que el checkbutton del menú se desmarque.
        """
        self.debug_viewer = None
        if self.debug_mode: # Si el modo seguía activo
            self.debug_mode_var.set(False)
            self._toggle_debug_mode()

    def abrir_ventana_maestro_competidores(self):
        self.debug_log("Acción de UI", "Abriendo ventana 'Maestro de Competidores'")
        VentanaMaestroCompetidores(self)

    def eliminar_licitacion(self):
        if not (iid := self.tree.focus()): return
        if iid == "finalizadas_parent": return

        numero_proceso_sel = self.tree.item(iid, 'values')[0]
        licitacion = next((l for l in self.gestor_licitaciones if l.numero_proceso == numero_proceso_sel), None)

        if licitacion:
            self.debug_log("Eliminación Licitación (Inicio)", licitacion.to_summary_dict())
            if messagebox.askyesno("Confirmar", f"¿Eliminar '{licitacion.nombre_proceso}'?"):
                if self.db.delete_licitacion(numero_proceso_sel):
                    self.debug_log("Eliminación Licitación (Éxito)", {"numero_proceso": numero_proceso_sel})
                else:
                    self.debug_log("Eliminación Licitación (Fallo)", {"numero_proceso": numero_proceso_sel})
                self.cargar_datos_desde_db()


    def ejecutar_smoke_tests(self):
            """Orquesta la ejecución de todas las pruebas y muestra los resultados."""
            log = [f"--- INICIO DE PRUEBAS DE INTEGRIDAD (SMOKE TESTS) v{self.__version__} ---"]
            log.append(f"Fecha y Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log.append(f"Base de Datos: {self.db_path}\n")

            self.config(cursor="wait")
            self.update_idletasks()

            try:
                self.db.begin_transaction()
                log.append("INFO: Transacción iniciada. Todos los cambios serán revertidos.")

                # --- Ejecutar Casos de Prueba ---
                self._test_crud_licitacion(log)
                self._test_crud_maestros(log)
                # --- NUEVAS PRUEBAS AVANZADAS ---
                self._test_ganadores_por_lote(log)
                self._test_fallas_fase_a(log)
                # Nota: La prueba de duplicación se omite en el modo transaccional
                # porque requiere que los IDs se confirmen, lo cual no ocurre
                # hasta el commit, pero la lógica está disponible si se necesita.
                # self._test_duplicacion(log)

                log.append("\n--- PRUEBAS COMPLETADAS ---")
                if any("[FAIL]" in line for line in log):
                    log.append("RESULTADO: ❌ FALLO. Se encontraron uno o más errores.")
                else:
                    log.append("RESULTADO: ✅ ÉXITO. Todas las pruebas avanzadas pasaron.")

            except Exception as e:
                log.append(f"\n[FAIL] ERROR CATASTRÓFICO DURANTE LAS PRUEBAS: {e}")
                log.append(traceback.format_exc())
            finally:
                self.db.rollback_transaction()
                log.append("INFO: Transacción revertida. La base de datos no ha sido modificada.")
                self.config(cursor="")

            VentanaResultadosTests(self, "\n".join(log))

    def _test_crud_licitacion(self, log):
        """Prueba la creación, actualización y eliminación de una licitación."""
        log.append("\n--- Módulo: Licitaciones ---")
        test_id = f"SMOKETEST-{int(datetime.datetime.now().timestamp())}"
        lic_obj = None
        try:
            # 1. CREATE
            datos_lic = {
                "nombre_proceso": "Licitación de Prueba", "numero_proceso": test_id,
                "institucion": "Institucion Maestra", "empresa_nuestra": {"nombre": "Empresa Maestra"},
                "lotes": [{"numero": 1, "nombre": "Lote de Prueba", "monto_base": 1000}]
            }
            lic_obj = Licitacion(**datos_lic)
            self.db.save_licitacion(lic_obj)
            log.append(f"[PASS] CREATE: Se creó la licitación de prueba '{test_id}'.")
        except Exception as e:
            log.append(f"[FAIL] CREATE: No se pudo crear la licitación de prueba. Error: {e}")
            return # Si la creación falla, no podemos continuar

        try:
            # 2. READ (implícito en el update y delete)
            # 3. UPDATE
            lic_obj.estado = "En Proceso"
            self.db.save_licitacion(lic_obj)
            log.append(f"[PASS] UPDATE: Se actualizó el estado de la licitación '{test_id}'.")
        except Exception as e:
            log.append(f"[FAIL] UPDATE: No se pudo actualizar la licitación '{test_id}'. Error: {e}")

        try:
            # 4. DELETE
            if self.db.delete_licitacion(test_id):
                log.append(f"[PASS] DELETE: Se eliminó la licitación de prueba '{test_id}'.")
            else:
                log.append(f"[FAIL] DELETE: El borrado de '{test_id}' no reportó filas afectadas.")
        except Exception as e:
            log.append(f"[FAIL] DELETE: No se pudo eliminar la licitación '{test_id}'. Error: {e}")

    def _test_crud_maestros(self, log):
            """Prueba la escritura y eliminación en tablas maestras (ej: competidores)."""
            log.append("\n--- Módulo: Datos Maestros (Competidores) ---")
            test_name = "Competidor de Prueba Auto"

            try:
                # 1. CREATE
                # Creamos una copia para no modificar la lista en memoria durante la prueba
                temp_competidores = list(self.competidores_maestros)
                temp_competidores.append({'nombre': test_name, 'rnc': '000-0000000-0'})
                
                self.db.save_master_lists(
                    empresas=self.empresas_registradas,
                    instituciones=self.instituciones_registradas,
                    documentos_maestros=[d.to_dict() for d in self.documentos_maestros],
                    competidores_maestros=temp_competidores, # Usamos la lista temporal
                    responsables_maestros=self.responsables_maestros,
                    replace_tables={'competidores_maestros'}
                )
                log.append(f"[PASS] CREATE: Se guardó un nuevo competidor maestro '{test_name}'.")

            except Exception as e:
                log.append(f"[FAIL] CREATE: No se pudo guardar el competidor maestro. Error: {e}")
                log.append(traceback.format_exc()) # Añadimos más detalle al log
                return

            try:
                # 2. DELETE
                temp_competidores_del = [c for c in temp_competidores if c['nombre'] != test_name]
                self.db.save_master_lists(
                    empresas=self.empresas_registradas,
                    instituciones=self.instituciones_registradas,
                    documentos_maestros=[d.to_dict() for d in self.documentos_maestros],
                    competidores_maestros=temp_competidores_del, # Usamos la lista sin el competidor de prueba
                    responsables_maestros=self.responsables_maestros,
                    replace_tables={'competidores_maestros'}
                )
                log.append(f"[PASS] DELETE: Se eliminó el competidor maestro de prueba.")
            except Exception as e:
                log.append(f"[FAIL] DELETE: No se pudo eliminar el competidor maestro. Error: {e}")
                log.append(traceback.format_exc()) # Añadimos más detalle al log

    def _test_ganadores_por_lote(self, log):
            """Prueba la asignación y eliminación de ganadores por lote."""
            log.append("\n--- Módulo: Ganadores por Lote ---")
            test_id = f"SMOKETEST-GANADOR-{int(datetime.datetime.now().timestamp())}"
            
            try:
                # Setup: Crear una licitación con un lote y un competidor
                datos_lic = {
                    "nombre_proceso": "Prueba Ganadores", "numero_proceso": test_id,
                    "lotes": [{"numero": "101", "nombre": "Lote Ganador"}],
                    "oferentes_participantes": [{"nombre": "Competidor Ganador", "ofertas_por_lote": [{"lote_numero": "101", "monto": 500}]}]
                }
                lic_obj = Licitacion(**datos_lic)
                self.db.save_licitacion(lic_obj)
                lic_id_db = lic_obj.id

                # 1. ASIGNAR GANADOR
                self.db.marcar_ganador_lote(lic_id_db, "101", "Competidor Ganador", None)
                ganadores = self.db.get_ganadores_por_lote(lic_id_db)
                if ganadores and ganadores[0]['ganador_nombre'] == "Competidor Ganador":
                    log.append("[PASS] ASIGNAR: Se asignó correctamente un ganador al lote.")
                else:
                    log.append(f"[FAIL] ASIGNAR: No se pudo verificar la asignación del ganador. Se obtuvo: {ganadores}")

                # 2. ELIMINAR GANADOR
                self.db.borrar_ganador_lote(lic_id_db, "101")
                ganadores_despues = self.db.get_ganadores_por_lote(lic_id_db)
                if not ganadores_despues:
                    log.append("[PASS] ELIMINAR: Se eliminó correctamente la asignación del ganador.")
                else:
                    log.append(f"[FAIL] ELIMINAR: La asignación del ganador no se eliminó. Se obtuvo: {ganadores_despues}")

            except Exception as e:
                log.append(f"[FAIL] PRUEBA DE GANADORES: La prueba falló con una excepción. Error: {e}")
                log.append(traceback.format_exc())
            finally:
                # Limpieza
                try:
                    self.db.delete_licitacion(test_id)
                except Exception:
                    pass

    def _test_fallas_fase_a(self, log):
        """Prueba el registro de fallas de Fase A."""
        log.append("\n--- Módulo: Fallas Fase A ---")
        test_id = f"SMOKETEST-FALLAS-{int(datetime.datetime.now().timestamp())}"
        
        try:
            # Setup: Crear licitación con documento y competidor
            datos_lic = {
                "nombre_proceso": "Prueba Fallas", "numero_proceso": test_id,
                "documentos_solicitados": [{"codigo": "F-01", "nombre": "Doc de Falla"}],
                "oferentes_participantes": [{"nombre": "Competidor con Falla"}]
            }
            lic_obj = Licitacion(**datos_lic)
            self.db.save_licitacion(lic_obj)
            lic_id_db = lic_obj.id
            doc_id_db = lic_obj.documentos_solicitados[0].id

            # 1. REGISTRAR FALLA
            fallas_a_registrar = [{
                "licitacion_id": lic_id_db,
                "participante_nombre": "Competidor con Falla",
                "documento_id": doc_id_db,
                "comentario": "Falla de prueba",
                "es_nuestro": False
            }]
            # Usamos el método genérico _save_related_data que ya existe
            self.db._save_related_data('descalificaciones_fase_a', lic_id_db, fallas_a_registrar, 
                                    ['licitacion_id', 'participante_nombre', 'documento_id', 'comentario', 'es_nuestro'])
            
            # 2. VERIFICAR FALLA
            # Recargamos la licitación completa para verificar
            lic_data, _, _, _, _, _ = self.db.get_all_data()
            lic_recargada_data = next((l for l in lic_data if l.get('id') == lic_id_db), None)
            
            if lic_recargada_data and lic_recargada_data.get('fallas_fase_a'):
                falla_registrada = lic_recargada_data['fallas_fase_a'][0]
                if falla_registrada['documento_id'] == doc_id_db and falla_registrada['participante_nombre'] == "Competidor con Falla":
                    log.append("[PASS] REGISTRAR: Se registró y verificó correctamente una falla de Fase A.")
                else:
                    log.append(f"[FAIL] VERIFICAR: La falla registrada no coincide con los datos esperados. Se obtuvo: {falla_registrada}")
            else:
                log.append("[FAIL] VERIFICAR: No se encontraron fallas registradas para la licitación de prueba.")

        except Exception as e:
            log.append(f"[FAIL] PRUEBA DE FALLAS: La prueba falló con una excepción. Error: {e}")
            log.append(traceback.format_exc())
        finally:
            # Limpieza
            try:
                self.db.delete_licitacion(test_id)
            except Exception:
                pass


    def actualizar_dashboard(self):
            """Limpia y vuelve a generar todos los gráficos del dashboard."""
            for widget in self.dashboard_content.winfo_children():
                widget.destroy()

            if not self.gestor_licitaciones:
                ttk.Label(self.dashboard_content, text="No hay datos para mostrar.", font=("Helvetica", 14)).pack(pady=50)
                return

            # Crear y posicionar los widgets de gráficos en la cuadrícula
            frame_estados = self._crear_grafico_distribucion_estados(self.dashboard_content)
            frame_estados.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            frame_rendimiento = self._crear_grafico_rendimiento_por_empresa(self.dashboard_content)
            frame_rendimiento.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            
            frame_instituciones = self._crear_tabla_top_instituciones(self.dashboard_content)
            frame_instituciones.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

    def _crear_grafico_distribucion_estados(self, parent):
        """Crea el gráfico de distribución de estados de licitaciones."""
        frame = ttk.LabelFrame(parent, text="Distribución de Estados")
        
        stats = {"Ganada": 0, "Perdida": 0, "En Proceso": 0}
        estados_finalizados = ["Adjudicada", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]

        for lic in self.gestor_licitaciones:
            if lic.estado == "Adjudicada":
                if any(l.ganado_por_nosotros for l in lic.lotes):
                    stats["Ganada"] += 1
                else:
                    stats["Perdida"] += 1
            elif lic.estado in estados_finalizados:
                stats["Perdida"] += 1
            else:
                stats["En Proceso"] += 1

        if not MATPLOTLIB_AVAILABLE or sum(stats.values()) == 0:
            ttk.Label(frame, text="Datos insuficientes o matplotlib no instalado.").pack(pady=20)
            return frame

        labels = stats.keys()
        sizes = stats.values()
        colors = ['#2E7D32', '#C62828', '#FFAB00']

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
        
        # Dibuja un círculo en el centro para hacerlo un gráfico de dona
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        ax.add_artist(centre_circle)
        
        ax.axis('equal') # Asegura que el pie sea un círculo.
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return frame

    def _crear_grafico_rendimiento_por_empresa(self, parent):
        """Crea el gráfico de barras comparando participaciones vs. ganadas por empresa."""
        frame = ttk.LabelFrame(parent, text="Rendimiento por Empresa")
        
        stats = defaultdict(lambda: {'participaciones': 0, 'ganadas': 0})
        for lic in self.gestor_licitaciones:
            empresas_participantes = self._nuestras_empresas_de(lic)
            if not empresas_participantes: continue

            es_ganada = lic.estado == "Adjudicada" and any(l.ganado_por_nosotros for l in lic.lotes)
            for empresa in empresas_participantes:
                stats[empresa]['participaciones'] += 1
                if es_ganada:
                    stats[empresa]['ganadas'] += 1
        
        if not MATPLOTLIB_AVAILABLE or not stats:
            ttk.Label(frame, text="Datos insuficientes o matplotlib no instalado.").pack(pady=20)
            return frame

        labels = sorted(stats.keys())
        participaciones = [stats[l]['participaciones'] for l in labels]
        ganadas = [stats[l]['ganadas'] for l in labels]
        
        x = np.arange(len(labels))
        width = 0.35

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        rects1 = ax.bar(x - width/2, participaciones, width, label='Participaciones')
        rects2 = ax.bar(x + width/2, ganadas, width, label='Ganadas')

        ax.set_ylabel('Cantidad de Licitaciones')
        ax.set_title('Participaciones vs. Ganadas')
        ax.set_xticks(x, labels, rotation=45, ha="right")
        ax.legend()
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return frame

    def _crear_tabla_top_instituciones(self, parent):
        """Crea una tabla con el top 5 de instituciones."""
        frame = ttk.LabelFrame(parent, text="Top 5 Instituciones por Participación")
        
        if not self.gestor_licitaciones:
            ttk.Label(frame, text="No hay datos.").pack()
            return frame

        conteo = Counter(lic.institucion for lic in self.gestor_licitaciones)
        
        tree = ttk.Treeview(frame, columns=("institucion", "cantidad"), show="headings", height=5)
        tree.heading("institucion", text="Institución")
        tree.heading("cantidad", text="Participaciones")
        tree.column("institucion", width=200, anchor=tk.W)
        tree.column("cantidad", width=100, anchor=tk.CENTER)

        for institucion, cantidad in conteo.most_common(5):
            tree.insert("", tk.END, values=(institucion, cantidad))

        tree.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        return frame


    def _on_tab_changed(self, event):
            """
            Detecta el cambio de pestaña y carga el contenido dinámicamente.
            """
            try:
                selected_tab_text = event.widget.tab(event.widget.select(), "text")
                
                if "Dashboard" in selected_tab_text:
                    # Actualiza el dashboard si no tiene contenido o si se quiere forzar
                    if not self.dashboard_content.winfo_children():
                        self.actualizar_dashboard()
                
                elif "Análisis de Fallas" in selected_tab_text:
                    # Siempre refresca los datos de fallas al visitar la pestaña
                    self._actualizar_tab_fallas()

            except Exception as e:
                print(f"Error al cambiar de pestaña: {e}")

    def _actualizar_tab_fallas(self):
        """
        Limpia y rellena la pestaña de 'Análisis de Fallas Fase A' con datos actualizados.
        """
        # Limpiar contenido anterior
        for widget in self.tab_fallas_a.winfo_children():
            widget.destroy()

        try:
            fallas = self.db.obtener_todas_las_fallas()
            if not fallas:
                ttk.Label(self.tab_fallas_a, text="No hay datos de fallas registrados en la base de datos.", font=("Helvetica", 12)).pack(pady=50, padx=20)
                return

            frame = ttk.Frame(self.tab_fallas_a, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            cols = ('institucion', 'participante', 'documento', 'comentario')
            tree = ttk.Treeview(frame, columns=cols, show="headings")
            
            tree.heading('institucion', text='Institución')
            tree.heading('participante', text='Participante')
            tree.heading('documento', text='Documento Fallido')
            tree.heading('comentario', text='Comentario')

            tree.column('institucion', width=250)
            tree.column('participante', width=250)
            tree.column('documento', width=300)
            tree.column('comentario', width=300)

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for (institucion, participante, documento, es_nuestro, comentario) in fallas:
                # Agregamos un indicador visual si la falla es de una de nuestras empresas
                participante_display = f"➡️ {participante}" if es_nuestro else participante
                tree.insert("", tk.END, values=(institucion, participante_display, documento, comentario))

        except Exception as e:
            ttk.Label(self.tab_fallas_a, text=f"Error al cargar los datos de fallas:\n{e}", foreground="red").pack(pady=20, padx=20)


    def _accion_backfill_ganadores(self):
        if not getattr(self, "db", None):
            messagebox.showerror("Error", "No hay conexión a la base de datos.", parent=self)
            return
        try:
            # Ejecuta el backfill en la BD
            n_norm, n_exact, n_like = self.db.backfill_empresa_nuestra_en_ganadores()

            # Intentar refrescar vistas/listas abiertas (si existen esos métodos)
            refrescos = 0

            # 1) Recargar listado principal de licitaciones
            for m in ("_recargar_listas", "_recargar_listas_licitaciones", "_reload_main_list"):
                if hasattr(self, m):
                    try:
                        getattr(self, m)()
                        refrescos += 1
                        break
                    except Exception:
                        pass

            # 2) Refrescar perfiles de empresa abiertos (si los hubiera)
            try:
                for w in self.winfo_children():
                    try:
                        from glicitaciones import VentanaPerfilEmpresaNuestra
                    except Exception:
                        VentanaPerfilEmpresaNuestra = type("Dummy", (), {})
                    if isinstance(w, VentanaPerfilEmpresaNuestra):
                        w._cargar_kpis_y_tabla(w.empresa_nombre)
                        refrescos += 1
            except Exception:
                pass

            messagebox.showinfo(
                "Backfill completado",
                f"Normalizados: {n_norm}\n"
                f"Asignados exactos: {n_exact}\n"
                f"Asignados por coincidencia: {n_like}\n\n"
                f"Vistas refrescadas: {refrescos}",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar el backfill.\n\nDetalle: {e}", parent=self)



def _render_portada_pdf_bytes(titulo_expediente, lic_data, qr_text=None):
    """
    Genera un PDF (en memoria) con portada: título, info de licitación y QR.
    Devuelve bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    W, H = letter

    # Título
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1.0*inch, H - 1.5*inch, titulo_expediente)

    # Info básica de la licitación
    c.setFont("Helvetica", 11)
    y = H - 2.0*inch
    info_lines = [
        f"Proceso: {lic_data.get('numero_proceso','')}",
        f"Nombre:  {lic_data.get('nombre_proceso','')}",
        f"Institución: {lic_data.get('institucion','')}",
        f"Empresa: {lic_data.get('empresa_nuestra','')}",
        f"Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    for line in info_lines:
        c.drawString(1.0*inch, y, line); y -= 0.25*inch

    # QR (opcional)
    if qr_text and QR_AVAILABLE:
        qr_img = qrcode.make(qr_text)
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        from reportlab.lib.utils import ImageReader
        img = ImageReader(qr_buf)
        c.drawImage(img, W - 2.2*inch, H - 2.7*inch, width=1.8*inch, height=1.8*inch)

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _render_indice_pdf_bytes(items_con_paginas):
    """
    Genera un PDF (en memoria) con un índice paginado.
    items_con_paginas: lista de dicts [{ 'titulo':..., 'pagina_inicio': int }, ...]
    Devuelve bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    W, H = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.0*inch, H - 1.0*inch, "ÍNDICE DEL EXPEDIENTE")
    c.setFont("Helvetica", 10)
    y = H - 1.5*inch

    for it in items_con_paginas:
        titulo = it['titulo']
        pag = it['pagina_inicio']
        line = f"{titulo}"
        c.drawString(1.0*inch, y, line)
        c.drawRightString(W - 1.0*inch, y, f"Pág. {pag}")
        y -= 0.28*inch
        if y < 1.0*inch:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = H - 1.0*inch

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_expediente_pdf(db: DatabaseManager, licitacion, items, out_path, meta):
    """
    Une PDFs en un solo expediente con:
      - Portada (con QR)
      - Índice paginado
      - Marcadores (si PyPDF2 lo soporta)
    """
    # 1) Guardar cabecera + items en BD (para trazabilidad)
    exp_id = db.crear_expediente(licitacion.id, meta.get('titulo_expediente','Expediente'), meta.get('creado_por','Usuario'))
    db.agregar_items_expediente(exp_id, items)

    # 2) Construir lista de PDFs existentes y títulos
    merger = PdfMerger()

    # --- Portada ---
    # Obtenemos el texto formateado de las empresas
    empresas_str = ", ".join(str(e) for e in licitacion.empresas_nuestras) if licitacion.empresas_nuestras else "No Asignada"

    portada_bytes = _render_portada_pdf_bytes(
        meta.get('titulo_expediente', 'Expediente'),
        {
            'numero_proceso': licitacion.numero_proceso,
            'nombre_proceso': licitacion.nombre_proceso,
            'institucion': licitacion.institucion,
            # ----- LÍNEA CORREGIDA -----
            'empresa_nuestra': empresas_str,
            # ---------------------------
        },
        qr_text=meta.get('qr_text')
    )
    merger.append(PdfReader(io.BytesIO(portada_bytes)))

    pagina_actual = len(merger.pages)
    indice_tmp = []


    # --- Recorrer items (documentos) ---
    for it in sorted(items, key=lambda x: x['orden']):
        doc_id = it['doc_version_id']
        titulo = it['titulo']
        
        # Obtenemos la ruta guardada desde la BD
        db.cursor.execute("SELECT ruta_archivo FROM documentos WHERE id=?", (doc_id,))
        row = db.cursor.fetchone()
        ruta_guardada = (row[0] or "") if row else ""
        
        # Reconstruimos la ruta a su versión absoluta para poder leerla
        ruta_absoluta = reconstruir_ruta_absoluta(ruta_guardada)

        if not ruta_absoluta or not os.path.isfile(ruta_absoluta):
            # Si falta, insertamos una página en blanco con aviso
            aviso = _render_indice_pdf_bytes([{'titulo': f"[FALTANTE] {titulo}", 'pagina_inicio': 0}])
            merger.append(PdfReader(io.BytesIO(aviso)))
            indice_tmp.append({'titulo': f"[FALTANTE] {titulo}", 'pagina_inicio': pagina_actual + 1})
            pagina_actual = len(merger.pages)
            continue

        reader = PdfReader(ruta_absoluta)
        num_pages = len(reader.pages)
        
        merger.append(reader)
        
        try:
            merger.add_outline_item(titulo, pagina_actual)
        except Exception:
            pass

        indice_tmp.append({'titulo': titulo, 'pagina_inicio': pagina_actual + 1})
        pagina_actual += num_pages

    # --- Índice (después de portada) ---
    indice_bytes = _render_indice_pdf_bytes(indice_tmp)
    merger.merge(1, PdfReader(io.BytesIO(indice_bytes)))

    # --- Guardar PDF final ---
    with open(out_path, "wb") as f:
        merger.write(f)
    merger.close()

    return exp_id




def previsualizar_expediente(ruta_pdf):
    if not os.path.isfile(ruta_pdf):
        messagebox.showerror("Archivo no encontrado", "No existe el PDF generado.", parent=None)
        return
    try:
        if platform.system() == "Windows":
            os.startfile(ruta_pdf)
        elif platform.system() == "Darwin":
            subprocess.call(["open", ruta_pdf])
        else:
            subprocess.call(["xdg-open", ruta_pdf])
    except Exception as e:
        messagebox.showwarning("Aviso", f"No se pudo abrir el PDF automáticamente.\nRuta: {ruta_pdf}\n\n{e}")

# ===================== Confirmador de Orden por Categoría =====================

# ===== Categorías fijas del expediente (exactamente 4) =====
CATS_ORDEN_EXPD = ["Legal", "Financiera", "Técnica", "Sobre B"]

def _cat_norm_exp(s: str) -> str:
    """
    Normaliza la categoría a una de las 4 fijas:
    Legal, Financiera, Técnica, Sobre B.
    Si no reconoce, la envía a 'Técnica' como default para no perderla.
    """
    if not isinstance(s, str):
        return "Técnica"
    s0 = s.strip().lower()

    # quitar acentos
    import unicodedata, re
    s1 = "".join(c for c in unicodedata.normalize("NFD", s0) if unicodedata.category(c) != "Mn")

    if "sobre" in s1 and "b" in s1:
        return "Sobre B"
    if "finan" in s1:
        return "Financiera"
    if "legal" in s1 or "jurid" in s1:
        return "Legal"
    if "tec" in s1 or "tecnic" in s1:
        return "Técnica"

    # Default (para no perder documentos por nombre raro)
    return "Técnica"


class DialogoOrdenExpediente(tk.Toplevel):
    """
    Revisa y reordena documentos agrupados en las 4 categorías fijas del expediente,
    utilizando una interfaz moderna de tablas.
    """

    def __init__(self, parent, documentos_obj, cats_prioridad=CATS_ORDEN_EXPD):
        super().__init__(parent)
        self.title("Confirmar orden del expediente")
        self.geometry("950x550")
        self.transient(parent)
        self.grab_set()

        grupos = {cat: [] for cat in cats_prioridad}
        for d in documentos_obj:
            cat = _cat_norm_exp(getattr(d, "categoria", ""))
            grupos[cat].append(d)

        self._data = {}
        self._trees = {} # La variable correcta es _trees
        self._incluir = {}
        self._tabs = ttk.Notebook(self)
        self._tabs.pack(fill="both", expand=True, padx=10, pady=10)

        for cat in cats_prioridad:
            docs = grupos.get(cat, [])
            
            def get_sort_key(documento):
                orden = getattr(documento, "orden_pliego", None)
                return 999999 if orden is None else int(orden)
            
            docs = sorted(docs, key=get_sort_key)
            
            f = ttk.Frame(self._tabs, padding=10)
            self._tabs.add(f, text=cat)
            self._data[cat] = list(docs)
            self._incluir[cat] = tk.BooleanVar(value=True)

            top = ttk.Frame(f)
            top.pack(fill="x")
            ttk.Checkbutton(top, text=f"Incluir {cat} en el expediente", variable=self._incluir[cat]).pack(side="left")

            mid = ttk.Frame(f)
            mid.pack(fill="both", expand=True, pady=6)

            cols = ('presentado', 'codigo', 'nombre')
            tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode=tk.EXTENDED)
            tree.heading('presentado', text='✓'); tree.heading('codigo', text='Código'); tree.heading('nombre', text='Nombre del Documento')
            tree.column('presentado', width=30, anchor=tk.CENTER, stretch=False); tree.column('codigo', width=150); tree.column('nombre', width=500)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar = ttk.Scrollbar(mid, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self._trees[cat] = tree

            btns = ttk.Frame(mid)
            btns.pack(side="left", fill="y", padx=8)
            ttk.Button(btns, text="⬆️ Subir", command=lambda c=cat: self._mover(c, -1)).pack(fill="x", pady=3)
            ttk.Button(btns, text="⬇️ Bajar", command=lambda c=cat: self._mover(c, 1)).pack(fill="x", pady=3)
            ttk.Button(btns, text="⤒ Arriba", command=lambda c=cat: self._to_edge(c, top=True)).pack(fill="x", pady=3)
            ttk.Button(btns, text="⤓ Abajo", command=lambda c=cat: self._to_edge(c, top=False)).pack(fill="x", pady=3)
            ttk.Button(btns, text="↺ Reset (orden guardado)", command=lambda c=cat: self._reset(c)).pack(fill="x", pady=12)

            self._render(cat)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="Cancelar", command=self._cancel).pack(side="right", padx=6)
        ttk.Button(bottom, text="Guardar y continuar", command=self._accept).pack(side="right")

        self.result_incluir = None
        self.result_orden = None


    def _render(self, cat):
        tree = self._trees[cat] # CORRECCIÓN: Usar self._trees
        tree.delete(*tree.get_children())
        for i, d in enumerate(self._data[cat]):
            presentado_icono = "✓" if getattr(d, "presentado", False) else "❌"
            codigo = getattr(d, 'codigo', '')
            nombre = getattr(d, 'nombre', '')
            tree.insert('', tk.END, iid=str(i), values=(presentado_icono, codigo, nombre))

# En DialogoOrdenExpediente, reemplaza el método _mover

    def _mover(self, cat, delta):
        tree = self._trees[cat] # CORRECCIÓN: Usar self._trees
        sel_iids = tree.selection()
        if not sel_iids: return

        sel_indices = sorted([int(iid) for iid in sel_iids])
        
        items = self._data[cat]
        if delta < 0:
            for i in sel_indices:
                if i > 0 and str(i - 1) not in sel_iids:
                    items[i], items[i-1] = items[i-1], items[i]
        else:
            for i in reversed(sel_indices):
                if i < len(items) - 1 and str(i + 1) not in sel_iids:
                    items[i], items[i+1] = items[i+1], items[i]
        
        self._render(cat)
        
        nuevos_iids_a_seleccionar = []
        for i in sel_indices:
            try:
                # Recalculamos la nueva posición del objeto en la lista
                obj = self._data[cat][i+delta]
                nuevo_indice = self._data[cat].index(obj)
                nuevos_iids_a_seleccionar.append(str(nuevo_indice))
            except (ValueError, IndexError):
                pass
        
        tree.selection_set(nuevos_iids_a_seleccionar)

# En DialogoOrdenExpediente, reemplaza el método _to_edge

    def _to_edge(self, cat, top=True):
        tree = self._trees[cat] # CORRECCIÓN: Usar self._trees
        sel_iids = tree.selection()
        if not sel_iids: return
        
        sel_indices = {int(iid) for iid in sel_iids}
        items = self._data[cat]
        
        picked = [item for i, item in enumerate(items) if i in sel_indices]
        rest = [item for i, item in enumerate(items) if i not in sel_indices]
        
        self._data[cat] = picked + rest if top else rest + picked
        
        self._render(cat)
        
        if top:
            nuevos_iids = [str(i) for i in range(len(sel_indices))]
        else:
            nuevos_iids = [str(i) for i in range(len(rest), len(items))]
        tree.selection_set(nuevos_iids)

    def _reset(self, cat):
        def get_sort_key(d):
            orden = getattr(d, "orden_pliego", None)
            return 999999 if orden is None else int(orden)
        self._data[cat].sort(key=get_sort_key)
        self._render(cat)

    def _accept(self):
        self.result_incluir = {cat: var.get() for cat, var in self._incluir.items()}
        self.result_orden = {cat: list(self._data[cat]) for cat in self._data}
        self.destroy()

    def _cancel(self):
        self.result_incluir = None
        self.result_orden = None
        self.destroy()

    def _render(self, cat):
        tree = self._trees[cat]
        tree.delete(*tree.get_children())
        for i, d in enumerate(self._data[cat]):
            presentado_icono = "✓" if getattr(d, "presentado", False) else "❌"
            codigo = getattr(d, 'codigo', '')
            nombre = getattr(d, 'nombre', '')
            tree.insert('', tk.END, iid=str(i), values=(presentado_icono, codigo, nombre))

    def _mover(self, cat, delta):
        tree = self._trees[cat]
        sel_iids = tree.selection()
        if not sel_iids: return
        sel_indices = sorted([int(iid) for iid in sel_iids])
        items = self._data[cat]
        if delta < 0:
            for i in sel_indices:
                if i > 0 and str(i - 1) not in sel_iids:
                    items[i], items[i-1] = items[i-1], items[i]
        else:
            for i in reversed(sel_indices):
                if i < len(items) - 1 and str(i + 1) not in sel_iids:
                    items[i], items[i+1] = items[i+1], items[i]
        self._render(cat)
        nuevos_iids = []
        for i in sel_indices:
            j = i + delta
            if 0 <= j < len(self._data[cat]):
                nuevos_iids.append(str(j))
        tree.selection_set(nuevos_iids)

    def _to_edge(self, cat, top=True):
        tree = self._trees[cat]
        sel_iids = tree.selection()
        if not sel_iids: return
        sel_indices = {int(iid) for iid in sel_iids}
        items = self._data[cat]
        picked = [item for i, item in enumerate(items) if i in sel_indices]
        rest = [item for i, item in enumerate(items) if i not in sel_indices]
        self._data[cat] = picked + rest if top else rest + picked
        self._render(cat)
        if top:
            nuevos_iids = [str(i) for i in range(len(picked))]
        else:
            nuevos_iids = [str(i) for i in range(len(self._data[cat]) - len(picked), len(self._data[cat]))]
        tree.selection_set(nuevos_iids)

    def _reset(self, cat):
        def get_sort_key(d):
            orden = getattr(d, "orden_pliego", None)
            return 999999 if orden is None else int(orden)
        self._data[cat].sort(key=get_sort_key)
        self._render(cat)

    def _accept(self):
        self.result_incluir = {cat: var.get() for cat, var in self._incluir.items()}
        self.result_orden = {cat: list(self._data[cat]) for cat in self._data}
        self.destroy()

    def _cancel(self):
        self.result_incluir = None
        self.result_orden = None
        self.destroy()


def generar_expediente_zip_por_categoria(db, licitacion, carpeta_salida, orden_por_cat, incluir):
    """
    Crea un ZIP por cada categoría marcada en 'incluir', respetando el orden manual
    confirmado en 'orden_por_cat' (que contiene listas de OBJETOS Documento).
    - CATS: ["Legal", "Financiera", "Técnica", "Sobre B"]
    - Dentro del ZIP:
        * index.csv -> [orden, codigo, nombre, categoria, archivo]
        * Archivos en orden (prefijo 001-, 002-, ...). Si falta, crea FALTANTE_###.txt
    Devuelve: lista de rutas zip generadas.
    """
    import os, io
    from zipfile import ZipFile, ZIP_DEFLATED
    from csv import writer

    os.makedirs(carpeta_salida, exist_ok=True)
    generados = []

    for cat in CATS_ORDEN_EXPD:
        if not incluir.get(cat, False):
            continue
        docs_obj = list(orden_por_cat.get(cat, []) or [])
        if not docs_obj:
            continue

        nombre_zip = f"Expediente - {cat} - {licitacion.numero_proceso}.zip"
        out_zip_path = os.path.join(carpeta_salida, nombre_zip)

        try:
            with ZipFile(out_zip_path, "w", compression=ZIP_DEFLATED) as zf:
                # 1) index.csv con el orden
                buf = io.StringIO()
                w = writer(buf)
                w.writerow(["orden", "codigo", "nombre", "categoria", "archivo"])
                for i, d in enumerate(docs_obj, start=1):
                    codigo = getattr(d, "codigo", "") or ""
                    nombre = getattr(d, "nombre", "") or ""
                    categoria = getattr(d, "categoria", "") or ""
                    ruta = getattr(d, "ruta_archivo", "") or ""
                    archivo = os.path.basename(ruta) if ruta else f"FALTANTE_{i:03d}.txt"
                    w.writerow([i, codigo, nombre, categoria, archivo])
                zf.writestr("index.csv", buf.getvalue())

                # 2) Archivos en orden (prefijo para mantener orden y evitar duplicados)
                for i, d in enumerate(docs_obj, start=1):
                    ruta = getattr(d, "ruta_archivo", "") or ""
                    if ruta and os.path.isfile(ruta):
                        base = os.path.basename(ruta)
                        arcname = f"{i:03d} - {base}"
                        zf.write(ruta, arcname=arcname)
                    else:
                        zf.writestr(f"FALTANTE_{i:03d}.txt", "Documento no encontrado o sin archivo adjunto.")

            generados.append(out_zip_path)

        except Exception as e:
            try:
                messagebox.showerror("Error ZIP", f"No se pudo crear el ZIP de {cat}:\n{e}")
            except Exception:
                pass

    return generados


def generar_expediente_zip(db: DatabaseManager, licitacion, out_zip_path, items=None):
    """
    Crea un ZIP con:
      - Archivos PDF/DOCX existentes de los documentos seleccionados (o todos)
      - index.csv con orden, título, nombre de archivo
    """
    docs = db.obtener_documentos_de_licitacion(licitacion.id)
    if items:
        ids = {it['doc_version_id'] for it in items}
        docs = [d for d in docs if d['id'] in ids]

    if not docs:
        messagebox.showwarning("Sin documentos", "No hay documentos para incluir.", parent=None)
        return False

        # Orden: por items (si se pasa), si no: categoria+codigo
    if items:
        # Si te pasaron items, ese orden manda.
        orden_map = {it['doc_version_id']: it['orden'] for it in items}
        docs.sort(key=lambda d: orden_map.get(d['id'], 999999))
    else:
        # No hay items -> intentamos orden del pliego.
        # Construimos un mapa (codigo+nombre normalizados -> orden_pliego) desde los OBJETOS en memoria.
# ... else:
        try:
            objs = list(getattr(licitacion, "documentos_solicitados", []) or [])
        except Exception:
            objs = []

        orden_map_pliego = {getattr(o, "id", -1): getattr(o, "orden_pliego", 999999) for o in objs}
        docs.sort(key=lambda d: (orden_map_pliego.get(d.get("id", -1), 999999), d.get("categoria") or "", d.get("codigo") or ""))

        def _norm(s):
            s = str(s or "").strip().lower()
            import unicodedata, re
            s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
            return re.sub(r"\s+", " ", s)

        orden_map_pliego = {}
        # Si tus objetos Documento tienen 'id' de BD, podrías usar un map por id;
        # este enfoque por (codigo,nombre) funciona aunque no tengas id sincronizado.
        for obj in objs:
            key = (_norm(getattr(obj, "codigo", "")), _norm(getattr(obj, "nombre", "")))
            orden_map_pliego[key] = getattr(obj, "orden_pliego", 999999)

        def _zip_key(d):
            key = (_norm(d.get("codigo", "")), _norm(d.get("nombre", "")))
            # Orden principal: orden_pliego (si no está, 999999 para dejarlos al final)
            # Orden secundario estable: categoria+codigo
            return (orden_map_pliego.get(key, 999999), d.get("categoria") or "", d.get("codigo") or "")

        docs.sort(key=_zip_key)


    try:
        with ZipFile(out_zip_path, "w", compression=ZIP_DEFLATED) as zf:
            # índice CSV
            from csv import writer
            buf = io.StringIO()
            w = writer(buf)
            w.writerow(["orden", "titulo", "archivo"])
            for i, d in enumerate(docs, start=1):
                titulo = f"[{d.get('codigo') or ''}] {d.get('nombre') or ''}".strip()
                ruta = d.get('ruta_archivo') or ''
                nombre_archivo = os.path.basename(ruta) if ruta else f"FALTANTE_{i}.txt"
                w.writerow([i, titulo, nombre_archivo])
            zf.writestr("index.csv", buf.getvalue())

            # ficheros
            for i, d in enumerate(docs, start=1):
                ruta = d.get('ruta_archivo') or ''
                if os.path.isfile(ruta):
                    arcname = os.path.basename(ruta)
                    zf.write(ruta, arcname=arcname)
                else:
                    # marcador “faltante”
                    zf.writestr(f"FALTANTE_{i}.txt", "Documento no encontrado.")
        return True
    except Exception as e:
        messagebox.showerror("Error ZIP", f"No se pudo crear el ZIP:\n{e}")
        return False


class DialogoElegirMetodoEvaluacion(ThemedDialog):
    """Un diálogo para que el usuario elija el método de evaluación de ofertas."""
    def __init__(self, parent):
        self.metodos = [
            "Precio Más Bajo (Cumple/No Cumple)",
            "Sistema de Puntos Absolutos (ej: 70 Tec + 30 Eco)",
            "Sistema de Puntos Ponderados (ej: 70% Tec + 30% Eco)"
        ]
        # Llama al __init__ de la clase padre (ThemedDialog) al final
        super().__init__(parent, "Seleccionar Método de Evaluación")

    def body(self, master):
        self.metodo_var = tk.StringVar(value=self.metodos[0])
        
        ttk.Label(master, text="Seleccione el método de evaluación para esta licitación:").pack(padx=10, pady=10)
        
        for metodo in self.metodos:
            ttk.Radiobutton(master, text=metodo, variable=self.metodo_var, value=metodo).pack(anchor="w", padx=15, pady=2)
            
        return master # Devuelve el frame principal

    def buttonbox(self):
        # Personalizamos el botón para que diga "Siguiente" en lugar de "Aceptar"
        box = ttk.Frame(self)
        ttk.Button(box, text="Siguiente", width=10, command=self.ok, default=tk.ACTIVE).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(box, text="Cancelar", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def apply(self):
        self.result = self.metodo_var.get()


class DialogoEntradaPuntajes(ThemedDialog):
    """
    Diálogo para definir parámetros, puntajes técnicos (globales o por lote)
    y gestionar descalificaciones manuales.
    """
    def __init__(self, parent, licitacion, metodo_evaluacion):
        self.licitacion = licitacion
        self.metodo = metodo_evaluacion
        self.parent_ventana_detalles = parent
        self.parent_app = parent.parent_app

        # === Nombres "raw" (sin flecha) y display ===
        self._nuestras_empresas_raw = {str(e) for e in licitacion.empresas_nuestras if str(e).strip()}
        self._competidores_raw = {oferente.nombre for oferente in licitacion.oferentes_participantes if getattr(oferente, "nombre", "").strip()}
        self._display_by_raw = {
            n: (f"➡️ {n}" if n in self._nuestras_empresas_raw else n)
            for n in (self._nuestras_empresas_raw | self._competidores_raw)
        }
        participantes_raw = set(self._display_by_raw.keys())

        # === Cargar parámetros y puntajes existentes ===
        pe = licitacion.parametros_evaluacion or {}
        self.parametros_existentes = pe.get('parametros', {}) or {}
        puntajes_existentes = pe.get('puntajes_tecnicos', {}) or {}

        # --- INICIO CAMBIO 1: Cargar el estado de la nueva regla ---
        # Por defecto, la regla estará activada si no se ha guardado nada antes.
        self.aplicar_regla_inicial = pe.get('aplicar_regla_un_lote', True)
        # --- FIN CAMBIO 1 ---

        # Normalizar claves (acepta viejas guardadas con flecha)
        self.puntajes_existentes = {}
        for k, v in (puntajes_existentes.items() if isinstance(puntajes_existentes, dict) else []):
            k_raw = k.replace("➡️ ", "") if isinstance(k, str) else k
            try:
                self.puntajes_existentes[k_raw] = float(v)
            except Exception:
                self.puntajes_existentes[k_raw] = 0.0

        # Descalificados iniciales (raw)
        self.participantes_con_fallas_inicial = {
            (falla.get('participante_nombre') or "").replace("➡️ ", "")
            for falla in licitacion.fallas_fase_a
        }

        # Participantes [{raw, display, tipo}]
        self.participantes = []
        for nombre_raw in participantes_raw:
            tipo = "Nuestra" if nombre_raw in self._nuestras_empresas_raw else "Competidor"
            self.participantes.append({"raw": nombre_raw, "display": self._display_by_raw[nombre_raw], "tipo": tipo})
        self.participantes.sort(key=lambda x: x['display'])

        # Variables globales de puntaje y descalificación (CLAVE RAW)
        self.puntajes_tecnicos = {
            p['raw']: tk.StringVar(value=str(self.puntajes_existentes.get(p['raw'], 0.0)))
            for p in self.participantes
        }
        self.descalificados_vars = {
            p['raw']: tk.BooleanVar(value=(p['raw'] in self.participantes_con_fallas_inicial))
            for p in self.participantes
        }

        # Modo por lote
        self.modo_por_lote_var = tk.BooleanVar(value=False)
        self.puntajes_por_lote_exist = (pe.get("puntajes_tecnicos_por_lote", {}) or {}).copy()
        self._lote_ids = [str(l.numero) for l in licitacion.lotes]
        self.lote_sel_var = tk.StringVar(value=self._lote_ids[0] if self._lote_ids else "")
        self._puntajes_vars_por_lote = {}

        super().__init__(parent, f"Definir Parámetros: {metodo_evaluacion.split('(')[0]}")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def body(self, master):
        self.geometry("850x600")

        # 1) Parámetros del método
        params_frame = ttk.LabelFrame(master, text="1. Parámetros de Evaluación", padding=10)
        params_frame.pack(fill="x", padx=10, pady=5)

        self.parametros_vars = {}
        self.param_entries = []

        campos, defaults = {}, {}
        if "Puntos Absolutos" in self.metodo:
            campos = {
                "Puntaje Técnico Máximo:": "puntaje_tec_max",
                "Puntaje Técnico Mínimo para Calificar:": "puntaje_tec_min",
                "Puntaje Económico Máximo:": "puntaje_eco_max"
            }
            defaults = {"puntaje_tec_max": "70", "puntaje_tec_min": "49", "puntaje_eco_max": "30"}
        elif "Puntos Ponderados" in self.metodo:
            campos = {
                "Puntaje Técnico Mínimo para Calificar (base 100):": "puntaje_tec_min",
                "Ponderación Técnica (%):": "pond_tec",
                "Ponderación Económica (%):": "pond_eco"
            }
            defaults = {"puntaje_tec_min": "70", "pond_tec": "70", "pond_eco": "30"}
        else:
            ttk.Label(params_frame, text="Este método no requiere parámetros adicionales.").pack()

        for i, (label, key) in enumerate(campos.items()):
            ttk.Label(params_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            valor_inicial = self.parametros_existentes.get(key, defaults.get(key, ""))
            var = tk.StringVar(value=valor_inicial)
            entry = ttk.Entry(params_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.parametros_vars[key] = var
            self.param_entries.append(entry)
        
        # --- INICIO CAMBIO 2: Añadir el Checkbox ---
        self.aplicar_regla_var = tk.BooleanVar(value=self.aplicar_regla_inicial)
        chk_regla = ttk.Checkbutton(
            params_frame,
            text="Aplicar regla de adjudicación a un único lote",
            variable=self.aplicar_regla_var
        )
        # Lo colocamos debajo de los otros parámetros
        chk_regla.grid(row=len(campos), column=0, columnspan=2, sticky="w", padx=5, pady=(8, 2))
        # --- FIN CAMBIO 2 ---

        # 2) Controles de modo por lote
        modo_frame = ttk.Frame(master)
        modo_frame.pack(fill="x", padx=10, pady=(0,5))
        chk = ttk.Checkbutton(modo_frame, text="Evaluar técnicamente por LOTE", variable=self.modo_por_lote_var, command=self._refrescar_tabla_por_modo)
        chk.pack(side=tk.LEFT)
        ttk.Label(modo_frame, text="  Lote: ").pack(side=tk.LEFT)
        self.cbx_lote = ttk.Combobox(modo_frame, textvariable=self.lote_sel_var, values=self._lote_ids, state="readonly", width=6)
        self.cbx_lote.pack(side=tk.LEFT)
        self.cbx_lote.bind("<<ComboboxSelected>>", lambda e: self._refrescar_tabla_por_modo())

        # 3) Tabla de puntajes / descalificación
        scores_frame = ttk.LabelFrame(master, text="2. Ingrese Puntajes y Verifique Descalificaciones", padding=10)
        scores_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ('nombre', 'puntaje', 'descalificar')
        self.tree = ttk.Treeview(scores_frame, columns=cols, show="headings")
        self.tree.heading('nombre', text='Participante')
        self.tree.heading('puntaje', text='Puntaje Técnico (Doble Clic)')
        self.tree.heading('descalificar', text='Descalificado (Clic para cambiar)')
        self.tree.column('nombre', width=450)
        self.tree.column('puntaje', width=150, anchor="center")
        self.tree.column('descalificar', width=200, anchor="center")
        tree_scrollbar = ttk.Scrollbar(scores_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._editar_puntaje)
        self.tree.bind("<Button-1>", self._toggle_disqualification)

        self.cbx_lote.configure(state="disabled")
        self._construir_tree_rows_global()
        return self.tree

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=10)

        self.btn_guardar = ttk.Button(box, text="💾 Guardar Parámetros", command=self.ok)
        self.btn_guardar.pack(side=tk.LEFT, padx=5)

        self.btn_editar = ttk.Button(box, text="✏️ Editar", command=lambda: self._toggle_edicion(True))
        self.btn_editar.pack(side=tk.LEFT, padx=5)

        self.btn_calcular = ttk.Button(box, text="📊 Calcular y Ver Resultados", command=self._calcular_y_mostrar)
        self.btn_calcular.pack(side=tk.LEFT, padx=5)

        ttk.Button(box, text="Cerrar", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self._toggle_edicion(not self.parametros_existentes)

    # ------------------------------------------------------------------
    # Helpers de construcción / refresco
    # ------------------------------------------------------------------
    def _filtrar_participantes_por_lote(self, lote_num_str):
        """Participantes que realmente tienen oferta válida en ese lote."""
        res = []
        nombres_empresas_nuestras = {str(e) for e in self.licitacion.empresas_nuestras}

        # Nuestra oferta del lote
        for l in self.licitacion.lotes:
            if str(l.numero) == lote_num_str and l.participamos and l.fase_A_superada and float(l.monto_ofertado or 0) > 0:
                nombre = f"➡️ {l.empresa_nuestra or 'Nuestra Oferta'}"
                res.append({"nombre": nombre, "raw": (l.empresa_nuestra or "Nuestra Oferta")})

        # Competidores con oferta válida en ese lote
        for of in self.licitacion.oferentes_participantes:
            for oferta in getattr(of, "ofertas_por_lote", []):
                if str(oferta.get('lote_numero')) == lote_num_str and oferta.get('paso_fase_A', False):
                    if of.nombre not in nombres_empresas_nuestras:
                        res.append({"nombre": of.nombre, "raw": of.nombre})

        res.sort(key=lambda x: x["nombre"])
        return res

    def _construir_tree_rows_global(self):
        """Filas con participantes globales y variables globales."""
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for p in self.participantes:
            raw = p['raw']
            display = p['display']
            check_char = '☑ Sí' if self.descalificados_vars[raw].get() else '☐ No'
            self.tree.insert('', 'end', iid=raw, values=(display, self.puntajes_tecnicos[raw].get(), check_char))

    def _construir_tree_rows_por_lote(self, lote_num_str):
        """Filas con participantes reales del lote y variables por-lote."""
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        participantes_lote = self._filtrar_participantes_por_lote(lote_num_str)
        pt_lote = self.puntajes_por_lote_exist.get(lote_num_str, {})

        # preparar cache de vars
        self._puntajes_vars_por_lote.setdefault(lote_num_str, {})

        for p in participantes_lote:
            raw = p['raw']
            display = p['nombre']
            valor_inicial = pt_lote.get(raw, self.puntajes_tecnicos.get(raw, tk.StringVar(value="0")).get())
            var = self._puntajes_vars_por_lote[lote_num_str].get(raw)
            if var is None:
                var = tk.StringVar(value=str(valor_inicial))
                self._puntajes_vars_por_lote[lote_num_str][raw] = var

            check_char = '☑ Sí' if self.descalificados_vars.get(raw, tk.BooleanVar(value=False)).get() else '☐ No'
            self.tree.insert('', 'end', iid=raw, values=(display, var.get(), check_char))

    def _refrescar_tabla_por_modo(self):
        """Reconstruye la tabla según el modo (global / por lote)."""
        if self.modo_por_lote_var.get():
            self.cbx_lote.configure(state="readonly")
            lote_num_str = self.lote_sel_var.get()
            self._construir_tree_rows_por_lote(lote_num_str)
        else:
            self.cbx_lote.configure(state="disabled")
            self._construir_tree_rows_global()

    # Obtener la variable correcta (global o por lote) para una fila
    def _get_puntaje_var(self, raw_id):
        if self.modo_por_lote_var.get():
            lote = self.lote_sel_var.get()
            return self._puntajes_vars_por_lote.get(lote, {}).get(raw_id, self.puntajes_tecnicos.get(raw_id))
        return self.puntajes_tecnicos.get(raw_id)

    # ------------------------------------------------------------------
    # Edición / UI actions
    # ------------------------------------------------------------------
    def _toggle_edicion(self, editable=True):
        new_state = "normal" if editable else "readonly"
        for entry in self.param_entries:
            entry.config(state=new_state)
        self.btn_guardar.config(state="normal" if editable else "disabled")
        self.btn_editar.config(state="disabled" if editable else "normal")
        self.btn_calcular.config(state="disabled" if editable else "normal")

    def _editar_puntaje(self, event):
        """Editor en celda; funciona en modo global y por lote."""
        if self.btn_guardar.cget('state') == 'disabled':
            return
        item_id_raw = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not item_id_raw or column_id != "#2":
            return

        x, y, width, height = self.tree.bbox(item_id_raw, column_id)
        puntaje_var = self._get_puntaje_var(item_id_raw)
        if puntaje_var is None:
            return

        entry = ttk.Entry(self.tree, textvariable=puntaje_var, justify='center')
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.selection_range(0, 'end')

        def save_and_close_editor(new_item_to_edit_raw=None):
            display_name = self._display_by_raw.get(item_id_raw, item_id_raw)
            self.tree.item(item_id_raw, values=(display_name, puntaje_var.get(), self.tree.item(item_id_raw, 'values')[2]))
            entry.destroy()
            if new_item_to_edit_raw:
                self.tree.selection_set(new_item_to_edit_raw)
                self.tree.focus(new_item_to_edit_raw)
                self.tree.see(new_item_to_edit_raw)
                self._editar_puntaje_por_id(new_item_to_edit_raw)

        def on_tab_pressed(event=None):
            next_item_raw = self.tree.next(item_id_raw)
            save_and_close_editor(next_item_raw)
            return "break"

        entry.bind("<FocusOut>", lambda e: save_and_close_editor())
        entry.bind("<Return>", lambda e: save_and_close_editor())
        entry.bind("<Tab>", on_tab_pressed)

    def _editar_puntaje_por_id(self, item_id_raw):
        column_id = "#2"
        x, y, width, height = self.tree.bbox(item_id_raw, column_id)
        puntaje_var = self._get_puntaje_var(item_id_raw)
        if puntaje_var is None:
            return

        entry = ttk.Entry(self.tree, textvariable=puntaje_var, justify='center')
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.selection_range(0, 'end')

        def save_and_close_editor(new_item_to_edit_raw=None):
            display_name = self._display_by_raw.get(item_id_raw, item_id_raw)
            self.tree.item(item_id_raw, values=(display_name, puntaje_var.get(), self.tree.item(item_id_raw, 'values')[2]))
            entry.destroy()
            if new_item_to_edit_raw:
                self.tree.selection_set(new_item_to_edit_raw)
                self.tree.focus(new_item_to_edit_raw)
                self.tree.see(new_item_to_edit_raw)
                self._editar_puntaje_por_id(new_item_to_edit_raw)

        def on_tab_pressed(event=None):
            next_item_raw = self.tree.next(item_id_raw)
            save_and_close_editor(next_item_raw)
            return "break"

        entry.bind("<FocusOut>", lambda e: save_and_close_editor())
        entry.bind("<Return>", lambda e: save_and_close_editor())
        entry.bind("<Tab>", on_tab_pressed)

    def _toggle_disqualification(self, event):
        if self.btn_guardar.cget('state') == 'disabled':
            return
        if self.tree.identify_region(event.x, event.y) != "cell" or self.tree.identify_column(event.x) != "#3":
            return

        item_id_raw = self.tree.focus()
        if not item_id_raw:
            return

        var = self.descalificados_vars[item_id_raw]
        var.set(not var.get())

        check_char = '☑ Sí' if var.get() else '☐ No'
        display_name = self._display_by_raw.get(item_id_raw, item_id_raw)
        val_str = (self._get_puntaje_var(item_id_raw).get() if self._get_puntaje_var(item_id_raw) else "0")
        self.tree.item(item_id_raw, values=(display_name, val_str, check_char))

    # ------------------------------------------------------------------
    # Validación / Guardado
    # ------------------------------------------------------------------
    def validate(self):
        try:
            for var in self.parametros_vars.values():
                float(var.get())
            # validar globales
            for var in self.puntajes_tecnicos.values():
                float(var.get())
            # validar por-lote si está activo
            if self.modo_por_lote_var.get():
                for lote_vars in self._puntajes_vars_por_lote.values():
                    for var in lote_vars.values():
                        float(var.get())
            return True
        except ValueError:
            messagebox.showerror("Error de Validación", "Todos los puntajes y parámetros deben ser números válidos.", parent=self)
            return False

    def apply(self):
        # ... (lógica de descalificación sin cambios) ...
        for nombre_raw, var in self.descalificados_vars.items():
            estaba_descalificado = nombre_raw in self.participantes_con_fallas_inicial
            esta_descalificado_ahora = var.get()
            if esta_descalificado_ahora and not estaba_descalificado:
                self.licitacion.fallas_fase_a.append({
                    "participante_nombre": nombre_raw, "documento_id": -1,
                    "comentario": "Descalificado manualmente desde el evaluador.",
                    "es_nuestro": nombre_raw in self._nuestras_empresas_raw
                })
            elif not esta_descalificado_ahora and estaba_descalificado:
                self.licitacion.fallas_fase_a = [
                    f for f in self.licitacion.fallas_fase_a
                    if not (f.get('participante_nombre') == nombre_raw and f.get('documento_id') == -1)
                ]

        # 2) Armar parametros_evaluacion
        pe = {
            "metodo": self.metodo,
            "parametros": {key: float(var.get()) for key, var in self.parametros_vars.items()},
            "puntajes_tecnicos": {key_raw: float(var.get()) for key_raw, var in self.puntajes_tecnicos.items()},
            # --- INICIO CAMBIO 3: Guardar el estado del checkbox ---
            "aplicar_regla_un_lote": self.aplicar_regla_var.get()
            # --- FIN CAMBIO 3 ---
        }

        # ... (lógica de puntajes por lote sin cambios) ...
        if self._puntajes_vars_por_lote:
            ptpl = {}
            for lote_num, vars_por_raw in self._puntajes_vars_por_lote.items():
                ptpl[lote_num] = {raw: float(var.get() or 0) for raw, var in vars_por_raw.items()}
            pe["puntajes_tecnicos_por_lote"] = ptpl
        else:
            if "puntajes_tecnicos_por_lote" in (self.licitacion.parametros_evaluacion or {}):
                pe["puntajes_tecnicos_por_lote"] = (self.licitacion.parametros_evaluacion or {})["puntajes_tecnicos_por_lote"]

        self.licitacion.parametros_evaluacion = pe

        # 3) Guardar en BD
        try:
            self.parent_app.db.save_licitacion(self.licitacion)
            self._toggle_edicion(False)
            messagebox.showinfo("Guardado", "Parámetros y puntajes guardados. Ahora puede calcular los resultados.", parent=self)
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudieron guardar los cambios en la base de datos:\n{e}", parent=self)

    # ------------------------------------------------------------------
    # Acciones extra
    # ------------------------------------------------------------------
    def _calcular_y_mostrar(self):
            """
            Calcula resultados y abre la ventana de resultados.
            - Usa los parámetros que ya están dentro de self.licitacion.parametros_evaluacion
            - Aplica la regla de 1 lote por oferente de forma condicional.
            """
            datos = self.licitacion.parametros_evaluacion or {}
            if not datos:
                messagebox.showwarning("Faltan datos", "Primero guarda los parámetros de evaluación.", parent=self)
                return

            resultados_por_lote = self.parent_ventana_detalles._calcular_resultados_evaluacion(datos)
            if not resultados_por_lote:
                messagebox.showinfo("Sin Datos", "No hay ofertas válidas para evaluar en ningún lote.", parent=self)
                return

            adjudicados = None
            
            # --- INICIO LÓGICA CONDICIONAL ---
            if datos.get("aplicar_regla_un_lote", True): # Si el check está marcado (o no existe, por defecto es True)
                if hasattr(self.parent_ventana_detalles, "_aplicar_regla_un_lote_por_oferente"):
                    try:
                        adjudicados, resultados_por_lote = self.parent_ventana_detalles._aplicar_regla_un_lote_por_oferente(
                            resultados_por_lote,
                            lots_min_excepcion=None,
                            campo_cuantia="monto_base_personal"
                        )
                    except Exception as e:
                        print(f"[REGLA] Error aplicando regla 1-lote-por-oferente: {e}")
            else: # Si el check NO está marcado, adjudicamos al mejor puntaje de cada lote
                resultados_anotados = {}
                for lote_num, lista_resultados in resultados_por_lote.items():
                    ganador = next((r["participante"] for r in lista_resultados if r.get("califica_tecnicamente")), None)
                    anotados = []
                    for res in lista_resultados:
                        res_copia = dict(res)
                        res_copia["es_ganador"] = (ganador is not None and res["participante"] == ganador)
                        anotados.append(res_copia)
                    resultados_anotados[lote_num] = anotados
                resultados_por_lote = resultados_anotados
            # --- FIN LÓGICA CONDICIONAL ---

            VentanaResultadosEvaluacion(self.parent_ventana_detalles, self.licitacion, resultados_por_lote, adjudicados=adjudicados)

    # Editor genérico (aún disponible si lo usabas)
    def _start_editing_cell(self, item_id_raw, column_id):
        x, y, width, height = self.tree.bbox(item_id_raw, column_id)
        puntaje_var = self._get_puntaje_var(item_id_raw)
        if puntaje_var is None:
            return
        entry = ttk.Entry(self.tree, textvariable=puntaje_var, justify='center')
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.selection_range(0, 'end')

        def on_focus_out(event=None):
            display_name = self._display_by_raw.get(item_id_raw, item_id_raw)
            self.tree.item(item_id_raw, values=(display_name, puntaje_var.get(), self.tree.item(item_id_raw, 'values')[2]))
            entry.destroy()

        def on_tab_pressed(event=None):
            on_focus_out()
            next_item_raw = self.tree.next(item_id_raw)
            if next_item_raw:
                self.tree.selection_set(next_item_raw)
                self.tree.focus(next_item_raw)
                self.tree.see(next_item_raw)
                self._start_editing_cell(next_item_raw, column_id)
            return "break"

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", on_focus_out)
        entry.bind("<Tab>", on_tab_pressed)

class DialogoGestionSubsanacion(ThemedDialog):
    """Ventana para marcar documentos a subsanar y definir la fecha límite, con filtros y confirmación."""
    def __init__(self, parent, licitacion, db_manager, callback_guardar):
        self.parent = parent # Guardamos referencia a la ventana padre
        self.licitacion = licitacion
        self.db = db_manager
        self.callback_guardar = callback_guardar
        
        # Ahora solo consideramos candidatos a los documentos que ya tienen un ID en la BD
        self.docs_candidatos = [d for d in self.licitacion.documentos_solicitados if d.id is not None]
        self.seleccion_vars = {doc.id: tk.BooleanVar(value=doc.requiere_subsanacion) for doc in self.docs_candidatos}
        
        self.search_var = tk.StringVar()
        self.categoria_var = tk.StringVar(value="Todas")
        categorias_unicas = sorted(list(set(doc.categoria for doc in self.docs_candidatos if doc.categoria)))
        self.categorias_filtro = ["Todas"] + categorias_unicas

        super().__init__(parent, "Gestionar Subsanación de Documentos")

    def body(self, master):
        self.geometry("800x550")
        fecha_frame = ttk.Frame(master, padding=5)
        fecha_frame.pack(fill=tk.X)
        ttk.Label(fecha_frame, text="Fecha Límite para Entrega:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        datos_evento = self.licitacion.cronograma.get("Entrega de Subsanaciones", {})
        self.fecha_entry = DateEntry(fecha_frame, width=15, locale='es_ES', date_pattern='y-mm-dd')
        if datos_evento.get("fecha_limite"): self.fecha_entry.set_date(datos_evento["fecha_limite"])
        self.fecha_entry.pack(side=tk.LEFT)

        filtros_frame = ttk.Frame(master, padding=(5, 10)); filtros_frame.pack(fill=tk.X)
        filtros_frame.columnconfigure(1, weight=1)
        ttk.Label(filtros_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(filtros_frame, text="Categoría:").grid(row=0, column=2, padx=(10, 5))
        categoria_combo = ttk.Combobox(filtros_frame, textvariable=self.categoria_var, values=self.categorias_filtro, state="readonly", width=20)
        categoria_combo.grid(row=0, column=3)
        self.search_var.trace_add("write", lambda *args: self._filtrar_y_poblar_treeview())
        categoria_combo.bind("<<ComboboxSelected>>", lambda *args: self._filtrar_y_poblar_treeview())

        tree_frame = ttk.LabelFrame(master, text="Marque los documentos que se deben subsanar", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree = ttk.Treeview(tree_frame, columns=('nombre', 'codigo'), show='tree headings')
        self.tree.column("#0", width=40, anchor=tk.CENTER, stretch=False); self.tree.heading("#0", text="Sel.")
        self.tree.heading('nombre', text='Nombre del Documento'); self.tree.heading('codigo', text='Código')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Button-1>", self._toggle_selection)
        self._filtrar_y_poblar_treeview()
        return search_entry
    
    def _filtrar_y_poblar_treeview(self):
        """Filtra los documentos según los controles y actualiza el Treeview."""
        self.tree.delete(*self.tree.get_children())
        
        search_term = self.search_var.get().lower()
        categoria_sel = self.categoria_var.get()

        for doc in self.docs_candidatos:
            # Filtrado por categoría
            if categoria_sel != "Todas" and doc.categoria != categoria_sel:
                continue
            
            # Filtrado por búsqueda de texto
            nombre = doc.nombre or ""
            codigo = doc.codigo or ""
            if search_term and search_term not in nombre.lower() and search_term not in codigo.lower():
                continue

            check_char = '☑' if self.seleccion_vars[doc.id].get() else '☐'
            self.tree.insert('', tk.END, text=check_char, values=(nombre, codigo), iid=doc.id)

    def _toggle_selection(self, event):
        # --- INICIO DE LA CORRECCIÓN DEL ValueError ---
        try:
            row_id_str = self.tree.identify_row(event.y)
            if not row_id_str: return
            if self.tree.identify_column(event.x) != '#0': return
            
            doc_id = int(row_id_str) # Esto ya no fallará porque filtramos docs sin ID
            if doc_id in self.seleccion_vars:
                var = self.seleccion_vars[doc_id]
                var.set(not var.get())
                check_char = '☑' if var.get() else '☐'
                self.tree.item(doc_id, text=check_char)
        except (ValueError, KeyError):
            # Salvaguarda por si ocurre un clic inesperado
            print("Clic en un ítem no válido del Treeview.")
        # --- FIN DE LA CORRECCIÓN ---

# En glicitaciones.py, dentro de la clase DialogoGestionSubsanacion

# En glicitaciones.py, dentro de la clase DialogoGestionSubsanacion

    def apply(self):
        """Muestra una confirmación antes de guardar los cambios."""
        fecha_limite = self.fecha_entry.get()
        # Guardamos los CÓDIGOS de los documentos marcados, ya que el código es un identificador estable.
        codigos_docs_marcados = {doc.codigo for doc in self.docs_candidatos if self.seleccion_vars[doc.id].get()}
        ids_docs_marcados = {doc.id for doc in self.docs_candidatos if self.seleccion_vars[doc.id].get()}

        if not fecha_limite and codigos_docs_marcados:
            messagebox.showwarning("Falta Fecha", "Ha marcado documentos pero no ha establecido una fecha límite.", parent=self)
            self.result = None
            return

        if not codigos_docs_marcados and not fecha_limite:
            # Limpiamos el proceso de subsanación
            self.licitacion.cronograma["Entrega de Subsanaciones"] = {"fecha_limite": None, "estado": "Pendiente"}
            for doc in self.licitacion.documentos_solicitados:
                doc.requiere_subsanacion = False
            self.callback_guardar()
            return
        
        # --- LÓGICA DE CONFIRMACIÓN MEJORADA ---
        msg = "Por favor, confirme los cambios a guardar:\n\n"
        msg += f"FECHA LÍMITE: {fecha_limite or 'Ninguna (se limpiará el proceso)'}\n\n"
        
        # Obtenemos los nombres de los documentos a partir de los códigos
        nombres_docs_marcados = [d.nombre for d in self.docs_candidatos if d.codigo in codigos_docs_marcados]
        msg += f"DOCUMENTOS A MARCAR PARA SUBSANACIÓN ({len(nombres_docs_marcados)}):\n"
        
        if not nombres_docs_marcados:
            msg += "- Ninguno\n"
        else:
            for nombre in nombres_docs_marcados[:10]:
                msg += f"- {nombre}\n"
            if len(nombres_docs_marcados) > 10:
                msg += f"- ... y {len(nombres_docs_marcados) - 10} más."

        if messagebox.askyesno("Confirmar Subsanación", msg, parent=self):
            # --- INICIO DE LA LÓGICA CORREGIDA ---

            # 1. Actualizar el objeto licitacion en memoria PRIMERO.
            if fecha_limite:
                self.licitacion.cronograma["Entrega de Subsanaciones"] = {"fecha_limite": fecha_limite, "estado": "Pendiente"}
            else:
                self.licitacion.cronograma["Entrega de Subsanaciones"] = {"fecha_limite": None, "estado": "Pendiente"}
            
            # Marcamos/desmarcamos los documentos en el objeto en memoria.
            for doc in self.licitacion.documentos_solicitados:
                if doc.id in ids_docs_marcados:
                    doc.requiere_subsanacion = True
                elif doc.id in self.seleccion_vars: # Solo desmarcamos los que estaban en la lista original
                    doc.requiere_subsanacion = False
            
            # 2. Llamar al guardado general. Esto persiste toda la licitación
            #    y asigna un ID a cualquier documento nuevo que se haya agregado.
            self.callback_guardar() 

            # 3. AHORA SÍ, registramos el historial en la BD, porque ya todos los documentos tienen ID.
            eventos_para_registrar = []
            
            # Volvemos a iterar para asegurarnos de que tenemos los IDs actualizados.
            for doc in self.licitacion.documentos_solicitados:
                if doc.requiere_subsanacion and doc.id:
                    # Se registra la solicitud inicial solo si no existe ya una para ese documento.
                    # (Esta es una mejora opcional para no duplicar entradas en el historial)
                    if not self.db.existe_evento_subsanacion_pendiente(self.licitacion.id, doc.id):
                        eventos_para_registrar.append((doc.id, fecha_limite, "Solicitud inicial de subsanación."))

            if eventos_para_registrar:
                self.db.registrar_eventos_subsanacion(self.licitacion.id, eventos_para_registrar)
            
            messagebox.showinfo("Guardado", "Proceso de subsanación actualizado y registrado.", parent=self)
            self.result = True # Indicamos que la operación fue exitosa

            # --- FIN DE LA LÓGICA CORREGIDA ---
        else:
            self.result = None
# Reemplaza la clase completa en glicitaciones.py

class VentanaHistorialSubsanacion(ThemedDialog):
    """Muestra el historial de eventos de subsanación y permite exportarlo."""
    def __init__(self, parent, licitacion):
        self.licitacion = licitacion
        self.parent_app = parent.parent_app
        # Ya NO cargamos el historial aquí, lo haremos en un método separado
        self.historial = [] 
        super().__init__(parent, f"Historial de Subsanaciones - {licitacion.numero_proceso}")

    def body(self, master):
        self.geometry("900x500")
        
        tree_frame = ttk.Frame(master)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ('fecha_sol', 'doc_codigo', 'doc_nombre', 'fecha_lim', 'estado', 'comentario')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        # ... (definición de headings y columns sin cambios) ...
        self.tree.heading('fecha_sol', text='Fecha Solicitud'); self.tree.column('fecha_sol', width=100)
        self.tree.heading('doc_codigo', text='Código Doc.'); self.tree.column('doc_codigo', width=120)
        self.tree.heading('doc_nombre', text='Documento'); self.tree.column('doc_nombre', width=250)
        self.tree.heading('fecha_lim', text='Fecha Límite'); self.tree.column('fecha_lim', width=100)
        self.tree.heading('estado', text='Estado'); self.tree.column('estado', width=100)
        self.tree.heading('comentario', text='Comentario'); self.tree.column('comentario', width=200)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Llamamos al método para cargar los datos por primera vez
        self.refrescar_historial()

    def refrescar_historial(self):
        """
        Limpia la tabla, vuelve a consultar la base de datos para obtener los datos más recientes
        y rellena la tabla de nuevo.
        """
        # Limpiar la vista actual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Volver a cargar los datos FRESCOS desde la BD
        self.historial = self.parent_app.db.obtener_historial_subsanacion(self.licitacion.id)
        
        # Poblar la tabla con los nuevos datos
        for row in self.historial:
            self.tree.insert("", tk.END, values=row)

    def buttonbox(self):
        """Caja de botones con el nuevo botón de Refrescar."""
        box = ttk.Frame(self)
        box.pack(pady=10)
        
        # --- BOTÓN NUEVO ---
        ttk.Button(box, text="🔄 Refrescar", command=self.refrescar_historial).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(box, text="📄 Exportar a PDF", command=self.exportar_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(box, text="Cerrar", command=self.cancel).pack(side=tk.LEFT, padx=5)
    
    # El método exportar_pdf se queda exactamente igual.
    def exportar_pdf(self):
        # ... (código sin cambios) ...
        if not self.historial:
            messagebox.showwarning("Sin Datos", "No hay historial para exportar.", parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            parent=self, title="Exportar Historial",
            initialfile=f"Historial_Subsanacion_{self.licitacion.numero_proceso}.pdf",
            filetypes=[("Archivos PDF", "*.pdf")], defaultextension=".pdf"
        )
        if file_path:
            try:
                self.parent_app.reporter.generate_subsanacion_report(self.licitacion, self.historial, file_path)
                messagebox.showinfo("Éxito", f"Reporte guardado en:\n{file_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}", parent=self)

def main():
    """Función principal para lanzar la aplicación de forma robusta."""
    setup_logging()
    
    db_path = seleccionar_o_crear_db_inicial()
    
    if not db_path:
        print("No se seleccionó ninguna base de datos. Cerrando aplicación.")
        return
        
    app = AppLicitacionesGUI(db_path=db_path)
    app.mainloop()

if __name__ == "__main__":
    main()