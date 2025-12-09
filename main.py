# ===== BLOQUE DE IMPORTS UNIFICADO (REEMPLAZA TODOS LOS ANTERIORES) =====
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import datetime
import json
import os
import sys
import subprocess
import logging
import shutil
import traceback

# Importaciones de nuestros módulos refactorizados
from logic_licitaciones import DatabaseManager
from clases_modelos import * # Importa todas las clases de datos
from ui_components import * # Importa todas las ventanas y diálogos
# (Opcional) Si decides mover ReportGenerator, también lo importarías aquí
# from report_generator import ReportGenerator 

# ========================================================================


class AppLicitacionesGUI(ThemedTk):

    def __init__(self, db_path):
        super().__init__()
        self.set_theme("arc")

        self.__version__ = "10.0-Stable"
        self.db_path = db_path
        self.api_key = None # Atributo para guardar la clave en memoria
        self._cargar_configuracion() # Nueva función para leer el archivo config.json

        self.title(f"Gestor de Licitaciones v{self.__version__} - [{os.path.basename(db_path)}]")
        self.geometry("1400x750")

        self._conectar_a_db(db_path)
        self._guardar_configuracion(db_path=self.db_path) # Ya no guarda el usuario

        
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
        
        # Estilos
        style = ttk.Style(self)
        style.configure("Urgent.TLabel", background="red", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
        style.configure("Soon.TLabel", background="orange", foreground="black", font=('Helvetica', 10, 'bold'), padding=5)
        style.configure("Safe.TLabel", background="green", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
        style.configure("Done.TLabel", background="grey", foreground="white", font=('Helvetica', 10, 'bold'), padding=5)
        style.configure("Small.TButton", font=("Helvetica", 9), padding=4)
        
        # Creación de la interfaz
        self.crear_widgets()
        self.crear_menu_contextual()
        self._crear_menu_superior()
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)
        
        # Carga de datos
        self.cargar_datos_desde_db()
        self._realizar_backup_automatico()
        self.reporter = ReportGenerator()


# Pega esta NUEVA función DENTRO de la clase AppLicitacionesGUI

    def _cargar_configuracion(self):
        """Lee el archivo config.json y carga la clave API si existe."""
        try:
            with open("config.json", 'r') as f:
                config = json.load(f)
                self.api_key = config.get("api_key", None)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está vacío, no hacemos nada.
            self.api_key = None



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

# En la clase AppLicitacionesGUI, reemplaza este método por completo

    def _crear_menu_superior(self):
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
                # --- AÑADE ESTA LÍNEA TEMPORALMENTE ---
                ("Diagnóstico y Reparación de BD...", self.abrir_ventana_sanity_check),
                ("Ejecutar Pruebas de Integridad...", self.ejecutar_smoke_tests),
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
                        submenu.add_radiobutton(label=option, variable=item["variable"], command=self._guardar_perfil_entorno)

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
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros y Búsqueda", padding="10"); filter_frame.pack(fill=tk.X, pady=(0, 10))
        self.filtro_busqueda_var = tk.StringVar(); self.filtro_busqueda_var.trace_add('write', lambda *a: self.aplicar_filtros())
        self.filtro_lote_var = tk.StringVar(); self.filtro_lote_var.trace_add('write', lambda *a: self.aplicar_filtros())
        self.filtro_estado_var = tk.StringVar(); self.filtro_empresa_var = tk.StringVar()
        ttk.Label(filter_frame, text="🔍 Buscar Proceso:").grid(row=0, column=0, padx=(0,5), sticky="w")
        ttk.Entry(filter_frame, textvariable=self.filtro_busqueda_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(filter_frame, text="📦 Contiene Lote:").grid(row=0, column=2, padx=(10,5), sticky="w")
        ttk.Entry(filter_frame, textvariable=self.filtro_lote_var, width=30).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filter_frame, text="Estado:").grid(row=1, column=0, padx=(0,5), sticky="w")
        self.filtro_estado_combo = ttk.Combobox(filter_frame, textvariable=self.filtro_estado_var, state="readonly", width=28); self.filtro_estado_combo.grid(row=1, column=1, padx=5, pady=5)
        self.filtro_estado_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())
        ttk.Label(filter_frame, text="Empresa:").grid(row=1, column=2, padx=(10,5), sticky="w")
        self.filtro_empresa_combo = ttk.Combobox(filter_frame, textvariable=self.filtro_empresa_var, state="readonly", width=28); self.filtro_empresa_combo.grid(row=1, column=3, padx=5, pady=5)
        self.filtro_empresa_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())
        ttk.Button(filter_frame, text="🧹 Limpiar Filtros", command=self.limpiar_filtros).grid(row=0, column=4, rowspan=2, padx=(20,0), ipady=5)
        ttk.Separator(filter_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=5, sticky="ew", pady=10)
        status_display_frame = ttk.LabelFrame(filter_frame, text="Próximo Vencimiento")
        status_display_frame.grid(row=0, column=5, rowspan=2, padx=(20, 5), pady=5, sticky="nsew")
        self.status_display_label = ttk.Label(status_display_frame, text="-- Selecciona una Fila --", anchor="center", style="Done.TLabel")
        self.status_display_label.pack(fill=tk.BOTH, expand=True)
        filter_frame.columnconfigure(5, weight=1)
        table_frame = ttk.Frame(main_frame); table_frame.pack(fill=tk.BOTH, expand=True)
        cols = ('codigo', 'nombre', 'empresa', 'dias_restantes', 'porcentaje_docs', 'diferencia', 'monto_ofertado', 'estatus')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings')
        # Enlazar selección y doble clic
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind("<Double-1>", self.abrir_vista_detallada_lotes)


        headings = {'codigo':'Código', 'nombre':'Nombre Proceso', 'empresa':'Empresa', 
                    'dias_restantes':'Restan', 'porcentaje_docs':'% Docs', 'diferencia':'% Dif.', 
                    'monto_ofertado':'Monto Ofertado', 'estatus':'Estatus'}
        for col, txt in headings.items():
            self.tree.heading(col, text=txt)


        widths = {'codigo': 140, 'nombre': 450, 'empresa': 150, 'dias_restantes': 120,
                'porcentaje_docs': 75, 'diferencia': 75, 'monto_ofertado': 140, 'estatus': 100}

        for col, width in widths.items():
            anchor = tk.W
            if col not in ['codigo', 'nombre', 'empresa', 'monto_ofertado', 'dias_restantes']:
                anchor = tk.CENTER
            elif col == 'monto_ofertado':
                anchor = tk.E
            self.tree.column(col, width=width, anchor=anchor, stretch=True)

        # 🔽 que el Treeview recalcule anchos al cambiar de tamaño
        self.tree.bind('<Configure>', self._ajustar_ancho_columnas)
        # === COLORES / ESTILOS PARA FILAS ===
        # Ganada: verde suave
        self.tree.tag_configure('ganada', background='#E6F4EA', foreground='#1E7D32')  # verde Google-like
        # Perdida: rojo suave
        self.tree.tag_configure('perdida', background='#FDECEA', foreground='#B71C1C')
        # En proceso (opcional): amarillo suave
        self.tree.tag_configure('proceso', background='#FFF8E1', foreground='#8D6E00')
        # Encabezado de finalizadas (si usas fila de sección)
        self.tree.tag_configure('finalizadas_header', background='#F3F4F6', foreground='#374151', font=('Helvetica', 9, 'bold'))
                # (opcional) Próximo a vencer: solo cambia el texto; el fondo lo pone 'en_proceso'
        self.tree.tag_configure('proximo', foreground='#D35400', font=('Helvetica', 9, 'bold'))

        # (opcional) que la selección no tape el color de fondo
        style = ttk.Style(self)
        style.map('Treeview',
                background=[('selected', '#C7F0D8')],
                foreground=[('selected', '#0B6B32')])

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# Scrollbar vertical
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontal
        hscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=hscroll.set)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
      
# En la función crear_widgets, reemplaza el bloque del status_frame por este:

        status_frame = ttk.Frame(main_frame, relief="sunken", padding=(5,2))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label_total = ttk.Label(status_frame, font=("Helvetica", 9))
        self.status_label_total.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')
        
        self.status_label_activas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="#007bff")
        self.status_label_activas.pack(side=tk.LEFT, padx=5)
        
        self.status_label_ganadas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="green")
        self.status_label_ganadas.pack(side=tk.LEFT, padx=5)
        
        self.status_label_lotes_ganados = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="#2E7D32")
        self.status_label_lotes_ganados.pack(side=tk.LEFT, padx=5)

        self.status_label_perdidas = ttk.Label(status_frame, font=("Helvetica", 9, "bold"), foreground="red")
        self.status_label_perdidas.pack(side=tk.LEFT, padx=5)
        style = ttk.Style(self); style.configure("Accion.TButton", font=("Helvetica", 10, "bold"))
        botones_frame = ttk.Frame(self); botones_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))
        ttk.Button(botones_frame, text="➕ Agregar", style="Accion.TButton", command=self.abrir_ventana_agregar).pack(side=tk.LEFT, padx=5, ipady=4)
        ttk.Button(botones_frame, text="📝 Ver/Editar", style="Accion.TButton", command=self.abrir_ventana_detalles).pack(side=tk.LEFT, padx=5, ipady=4)
        Tooltip(self.tree, text_func=self._get_tooltip_text)


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

# Pega estos dos nuevos métodos DENTRO de la clase AppLicitacionesGUI

# En la clase AppLicitacionesGUI, REEMPLAZA este método:

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
    
# En la clase AppLicitacionesGUI, REEMPLAZA este método:

# En la clase AppLicitacionesGUI, REEMPLAZA este método:

    def _display_empresas_de(self, lic):
        """Devuelve un string amigable para mostrar las empresas de una licitación."""
        # La función _nuestras_empresas_de ahora solo devuelve nombres de empresas reales
        emps = sorted(self._nuestras_empresas_de(lic))
        
        # Si la lista de empresas reales no está vacía, las mostramos.
        # Si está vacía, significa que no hay ninguna asignada, y mostramos "(Sin Asignar)".
        return ", ".join(emps) if emps else "(Sin Asignar)"
    # En la clase AppLicitacionesGUI, REEMPLAZA tu método actual con este:

    def actualizar_tabla_gui(self, lista_a_mostrar=None):
        lista_para_usar = lista_a_mostrar if lista_a_mostrar is not None else self.gestor_licitaciones
        self.tree.delete(*self.tree.get_children())

        estados_finalizados = ["Adjudicada", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]

        licitaciones_activas = [l for l in lista_para_usar if l.estado not in estados_finalizados]
        licitaciones_finalizadas = [l for l in lista_para_usar if l.estado in estados_finalizados]

        def obtener_clave_ordenamiento(licitacion):
            hoy = datetime.date.today()
            fechas = []
            for d in licitacion.cronograma.values():
                if d.get("estado") == "Pendiente" and d.get("fecha_limite"):
                    try:
                        f = datetime.datetime.strptime(d["fecha_limite"], "%Y-%m-%d").date()
                        if f >= hoy:
                            fechas.append(f)
                    except Exception:
                        pass
            return min(fechas) if fechas else datetime.date.max

        activas_ordenadas = sorted(licitaciones_activas, key=obtener_clave_ordenamiento)

        for lic in activas_ordenadas:
            tags = ['proceso']
            dias_restantes_str = lic.get_dias_restantes()
            if "días" in dias_restantes_str:
                try:
                    dias = int(dias_restantes_str.split()[1])
                    if dias <= 7:
                        tags.append('proximo')
                except (ValueError, IndexError):
                    pass

            # --- Lógica de visualización mejorada ---
            monto_ofertado = lic.get_oferta_total(solo_participados=True)
            monto_ofertado_str = f"RD$ {monto_ofertado:,.2f}" if monto_ofertado > 0 else "N/D"
            dif_str = f"{lic.get_diferencia_porcentual(solo_participados=True, usar_base_personal=False):.2f}%" if monto_ofertado > 0 else "N/D"
            # --- Fin de la lógica ---

            values = (
                lic.numero_proceso,
                lic.nombre_proceso,
                self._display_empresas_de(lic),
                dias_restantes_str,
                f"{lic.get_porcentaje_completado():.1f}%",
                dif_str,
                monto_ofertado_str,
                lic.estado
            )
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

# En la clase AppLicitacionesGUI, pega estos nuevos métodos al final

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

            log.append("\n--- PRUEBAS COMPLETADAS ---")
            if any("[FAIL]" in line for line in log):
                log.append("RESULTADO: ❌ FALLO. Se encontraron uno o más errores.")
            else:
                log.append("RESULTADO: ✅ ÉXITO. Todas las pruebas básicas pasaron.")

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

        # Copiamos las listas actuales para no interferir con la lógica de la app
        temp_empresas = list(self.empresas_registradas)
        temp_instituciones = list(self.instituciones_registradas)
        temp_documentos = [d.to_dict() for d in self.documentos_maestros]
        temp_responsables = list(self.responsables_maestros)

        try:
            # 1. CREATE
            temp_competidores = list(self.competidores_maestros)
            temp_competidores.append({'nombre': test_name, 'rnc': '000-0000000-0'})
            self.db.save_master_lists(
                empresas=self.parent_app.empresas_registradas,
                instituciones=self.parent_app.instituciones_registradas,
                documentos_maestros=[d.to_dict() for d in self.parent_app.documentos_maestros],
                competidores_maestros=self.parent_app.competidores_maestros,
                responsables_maestros=self.parent_app.responsables_maestros,
                replace_tables={'competidores_maestros'}  # <- solo esta tabla se reemplaza
            )

            log.append(f"[PASS] CREATE: Se guardó un nuevo competidor maestro '{test_name}'.")
        except Exception as e:
            log.append(f"[FAIL] CREATE: No se pudo guardar el competidor maestro. Error: {e}")
            return

        try:
            # 2. DELETE
            temp_competidores_del = [c for c in temp_competidores if c['nombre'] != test_name]
            self.db.save_master_lists(
                empresas=self.parent_app.empresas_registradas,
                instituciones=self.parent_app.instituciones_registradas,
                documentos_maestros=[d.to_dict() for d in self.parent_app.documentos_maestros],
                competidores_maestros=self.parent_app.competidores_maestros,
                responsables_maestros=self.parent_app.responsables_maestros,
                replace_tables={'competidores_maestros'}  # <- solo esta tabla se reemplaza
            )
            log.append(f"[PASS] DELETE: Se eliminó el competidor maestro de prueba.")
        except Exception as e:
            log.append(f"[FAIL] DELETE: No se pudo eliminar el competidor maestro. Error: {e}")


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