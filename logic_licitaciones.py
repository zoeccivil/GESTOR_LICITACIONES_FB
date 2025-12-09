import sqlite3
import json
import logging
import datetime

class ConcurrencyException(Exception):
    """Excepción personalizada para errores de concurrencia."""
    pass

class DatabaseManager:
    """
    Gestiona todas las interacciones con la base de datos SQLite
    utilizando una estructura relacional de múltiples tablas.
    """
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.conn.cursor()
        self._actualizar_schema()
        self.create_tables()
        self.setup_fts()  # Inicializa/asegura los índices FTS
        self.cursor.execute("PRAGMA foreign_keys = ON")  # recomendado
        self._ensure_ganadores_schema()                  # <- ¡IMPRESCINDIBLE!


        

    def _ensure_ganadores_schema(self):
    # Crea la tabla/índices si no existen
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS licitacion_ganadores_lote (
                licitacion_id   INTEGER NOT NULL,
                lote_numero     TEXT    NOT NULL,
                ganador_nombre  TEXT    NOT NULL,
                empresa_nuestra TEXT, -- NUEVA columna
                PRIMARY KEY (licitacion_id, lote_numero, ganador_nombre),
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (empresa_nuestra) REFERENCES empresas_maestras(nombre)
            )
        ''')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ganadores_licitacion ON licitacion_ganadores_lote(licitacion_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ganadores_nombre ON licitacion_ganadores_lote(ganador_nombre)")
        self.conn.commit()


    def _actualizar_schema(self):
            """
            Añade columnas y repara tablas de forma robusta, guardando
            después de cada cambio estructural importante.
            """
            cursor = self.conn.cursor()

            def ejecutar_cambio(descripcion, sql_alter):
                try:
                    print(f"Verificando schema: {descripcion}...")
                    cursor.execute(sql_alter)
                    self.conn.commit()
                    print(f" -> OK: {descripcion} aplicado.")
                except sqlite3.OperationalError as e:
                    # Ignoramos el error si la columna ya existe, que es lo esperado
                    if "duplicate column name" not in str(e):
                        raise e # Si es otro error, sí lo reportamos
                    else:
                        print(f" -> OK: {descripcion} ya existía.")
                except Exception as e:
                    print(f"Error aplicando '{descripcion}': {e}")
                    self.conn.rollback()
                    raise e

            # --- 1. Cambios en 'licitaciones' ---
            cursor.execute("PRAGMA table_info(licitaciones)")
            columnas_lic = {info[1] for info in cursor.fetchall()}
            if 'bnb_score' not in columnas_lic:
                ejecutar_cambio("Añadir bnb_score a licitaciones", 'ALTER TABLE licitaciones ADD COLUMN bnb_score REAL DEFAULT -1.0')
            if 'last_modified' not in columnas_lic:
                ejecutar_cambio("Añadir last_modified a licitaciones", "ALTER TABLE licitaciones ADD COLUMN last_modified TEXT")

            # --- 2. Cambios en 'documentos' ---
            cursor.execute("PRAGMA table_info(documentos)")
            if 'obligatorio' not in {info[1] for info in cursor.fetchall()}:
                ejecutar_cambio("Añadir obligatorio a documentos", 'ALTER TABLE documentos ADD COLUMN obligatorio BOOLEAN DEFAULT 0')

            # --- 3. Cambios en 'ofertas_lote_oferentes' ---
            cursor.execute("PRAGMA table_info(ofertas_lote_oferentes)")
            columnas_ofertas = {info[1] for info in cursor.fetchall()}
            if 'plazo_entrega' not in columnas_ofertas:
                ejecutar_cambio("Añadir plazo_entrega a ofertas", 'ALTER TABLE ofertas_lote_oferentes ADD COLUMN plazo_entrega INTEGER DEFAULT 0')
            if 'garantia_meses' not in columnas_ofertas:
                ejecutar_cambio("Añadir garantia_meses a ofertas", 'ALTER TABLE ofertas_lote_oferentes ADD COLUMN garantia_meses INTEGER DEFAULT 0')

            # --- 4. Cambios en 'competidores_maestros' (NUEVO Y CORREGIDO) ---
            cursor.execute("PRAGMA table_info(competidores_maestros)")
            columnas_comp = {info[1] for info in cursor.fetchall()}
            if 'rpe' not in columnas_comp:
                ejecutar_cambio("Añadir rpe a competidores", 'ALTER TABLE competidores_maestros ADD COLUMN rpe TEXT')
            if 'representante' not in columnas_comp:
                ejecutar_cambio("Añadir representante a competidores", 'ALTER TABLE competidores_maestros ADD COLUMN representante TEXT')

            # --- 5. Reparación de la tabla 'kit_items' (se mantiene como antes) ---
            try:
                cursor.execute("PRAGMA table_info(kit_items)")
                columnas_kit_items = cursor.fetchall()
                if columnas_kit_items and not any(col[5] for col in columnas_kit_items):
                    print("Reparando la tabla 'kit_items' para añadir Primary Key y eliminar duplicados...")
                    self.conn.execute('BEGIN TRANSACTION')
                    cursor.execute("ALTER TABLE kit_items RENAME TO kit_items_old")
                    cursor.execute('''
                        CREATE TABLE kit_items (
                            kit_id INTEGER, documento_maestro_id INTEGER,
                            PRIMARY KEY (kit_id, documento_maestro_id),
                            FOREIGN KEY (kit_id) REFERENCES kits_de_requisitos (id) ON DELETE CASCADE,
                            FOREIGN KEY (documento_maestro_id) REFERENCES documentos_maestros (id) ON DELETE CASCADE
                        )
                    ''')
                    cursor.execute("INSERT OR IGNORE INTO kit_items (kit_id, documento_maestro_id) SELECT DISTINCT kit_id, documento_maestro_id FROM kit_items_old")
                    cursor.execute("DROP TABLE kit_items_old")
                    self.conn.commit()
            except sqlite3.OperationalError as e:
                if "no such table" not in str(e):
                    self.conn.rollback()
                    raise e
            except Exception as e:
                print(f"Error reparando 'kit_items': {e}")
                self.conn.rollback()
                raise e
        
                        # --- MIGRACIÓN: columna de orden persistente para documentos ---
            # Agrega 'orden_pliego' si no existe
            try:
                self.cursor.execute("PRAGMA table_info(documentos)")
                cols = [r[1] for r in self.cursor.fetchall()]
                if "orden_pliego" not in cols:
                    self.cursor.execute("ALTER TABLE documentos ADD COLUMN orden_pliego INTEGER")
                    self.conn.commit()
            except Exception as e:
                print("[WARN] No se pudo asegurar columna 'orden_pliego' en documentos:", e)



    def create_tables(self):
        """Crea/migra todas las tablas necesarias de forma segura (idempotente)."""

        # === BASE ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS licitaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_proceso TEXT NOT NULL,
                numero_proceso TEXT UNIQUE NOT NULL,
                institucion TEXT,
                empresa_nuestra TEXT,
                estado TEXT,
                fase_A_superada BOOLEAN,
                fase_B_superada BOOLEAN,
                adjudicada BOOLEAN,
                adjudicada_a TEXT,
                motivo_descalificacion TEXT,
                fecha_creacion TEXT,
                cronograma TEXT,
                docs_completos_manual BOOLEAN DEFAULT 0,
                bnb_score REAL DEFAULT -1.0,
                last_modified TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS licitacion_empresas_nuestras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER NOT NULL,
                empresa_nombre TEXT NOT NULL,
                UNIQUE(licitacion_id, empresa_nombre),
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones(id) ON DELETE CASCADE,
                FOREIGN KEY (empresa_nombre) REFERENCES empresas_maestras(nombre) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER,
                numero TEXT,
                nombre TEXT,
                monto_base REAL,
                monto_base_personal REAL,
                monto_ofertado REAL,
                participamos BOOLEAN,
                fase_A_superada BOOLEAN,
                empresa_nuestra TEXT,             -- puede faltar en BDs antiguas; se migra abajo
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER,
                codigo TEXT,
                nombre TEXT,
                categoria TEXT,
                comentario TEXT,
                presentado BOOLEAN,
                subsanable TEXT,
                ruta_archivo TEXT,
                responsable TEXT,
                revisado BOOLEAN DEFAULT 0,
                obligatorio BOOLEAN DEFAULT 0,
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS oferentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER,
                nombre TEXT,
                comentario TEXT,
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ofertas_lote_oferentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oferente_id INTEGER,
                lote_numero TEXT,
                monto REAL,
                paso_fase_A BOOLEAN,
                plazo_entrega INTEGER DEFAULT 0,
                garantia_meses INTEGER DEFAULT 0,
                FOREIGN KEY (oferente_id) REFERENCES oferentes(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('CREATE TABLE IF NOT EXISTS empresas_maestras (nombre TEXT PRIMARY KEY, rnc TEXT, telefono TEXT, correo TEXT, direccion TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS instituciones_maestras (nombre TEXT PRIMARY KEY, rnc TEXT, telefono TEXT, correo TEXT, direccion TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS competidores_maestros (nombre TEXT PRIMARY KEY, rnc TEXT, rpe TEXT, representante TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS responsables_maestros (nombre TEXT PRIMARY KEY)')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos_maestros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL,
                nombre TEXT,
                categoria TEXT,
                comentario TEXT,
                empresa_nombre TEXT,
                ruta_archivo TEXT,
                UNIQUE(codigo, empresa_nombre)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS criterios_bnb (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                peso REAL NOT NULL CHECK (peso > 0 AND peso <= 1),
                activo BOOLEAN DEFAULT 1
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bnb_evaluaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER,
                criterio_id INTEGER,
                puntaje INTEGER NOT NULL CHECK (puntaje >= 0 AND puntaje <= 10),
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (criterio_id) REFERENCES criterios_bnb (id) ON DELETE CASCADE,
                UNIQUE(licitacion_id, criterio_id)
            )
        ''')

        # === KITS ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kits_de_requisitos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_kit TEXT NOT NULL,
                institucion_nombre TEXT NOT NULL,
                UNIQUE(nombre_kit, institucion_nombre),
                FOREIGN KEY (institucion_nombre) REFERENCES instituciones_maestras (nombre) ON DELETE CASCADE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kit_items (
                kit_id INTEGER,
                documento_maestro_id INTEGER,
                PRIMARY KEY (kit_id, documento_maestro_id),
                FOREIGN KEY (kit_id) REFERENCES kits_de_requisitos (id) ON DELETE CASCADE,
                FOREIGN KEY (documento_maestro_id) REFERENCES documentos_maestros (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS riesgos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                categoria TEXT,
                impacto INTEGER DEFAULT 1,
                probabilidad INTEGER DEFAULT 1,
                mitigacion TEXT,
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                comentario TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_app (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')

        # === EXPEDIENTES ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expedientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                licitacion_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                creado_en TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f','now')),
                creado_por TEXT,
                FOREIGN KEY (licitacion_id) REFERENCES licitaciones(id) ON DELETE CASCADE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expediente_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expediente_id INTEGER NOT NULL,
                orden INTEGER NOT NULL,
                doc_version_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                FOREIGN KEY (expediente_id) REFERENCES expedientes(id) ON DELETE CASCADE,
                FOREIGN KEY (doc_version_id) REFERENCES documentos(id) ON DELETE CASCADE
            )
        ''')

        # === GANADORES POR LOTE ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS licitacion_ganadores_lote (
                licitacion_id   INTEGER NOT NULL,
                lote_numero     TEXT    NOT NULL,
                ganador_nombre  TEXT    NOT NULL,
                empresa_nuestra TEXT,   -- nombre de nuestra empresa si aplica (SIN FK)
                PRIMARY KEY (licitacion_id, lote_numero)
                -- OJO: NO declaramos FK sobre empresa_nuestra para evitar errores al guardar
                --      si el nombre aún no está en empresas_maestras.
                --      La pertenencia "es_nuestro" se calcula al leer.
            )
        ''')

        # Índices útiles
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ganadores_licitacion ON licitacion_ganadores_lote(licitacion_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ganadores_nombre ON licitacion_ganadores_lote(ganador_nombre)")

        # MIGRACIÓN: si traes datos antiguos, limpiamos duplicados y garantizamos 1 ganador por (licitación,lote)
        self.cursor.execute("""
            DELETE FROM licitacion_ganadores_lote
            WHERE rowid NOT IN (
                SELECT MAX(rowid)
                FROM licitacion_ganadores_lote
                GROUP BY licitacion_id, lote_numero
            )
        """)
        self.cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_ganador_por_lote
            ON licitacion_ganadores_lote(licitacion_id, lote_numero)
        """)

        # Asegurar columna empresa_nuestra en LOTES (por si faltara)
        self.cursor.execute("PRAGMA table_info(lotes)")
        _l_cols = [r[1] for r in self.cursor.fetchall()]
        if 'empresa_nuestra' not in _l_cols:
            self.cursor.execute("ALTER TABLE lotes ADD COLUMN empresa_nuestra TEXT")

        self.conn.commit()

        


    def update_lote_empresa(self, licitacion_id: int, lote_numero: str, empresa_nuestra: str | None):
        self.cursor.execute("""
            UPDATE lotes
            SET empresa_nuestra = ?
            WHERE licitacion_id = ? AND CAST(numero AS TEXT) = CAST(? AS TEXT)
        """, (empresa_nuestra or None, licitacion_id, str(lote_numero)))
        self.conn.commit()

    def update_lote_flags(self, licitacion_id: int, lote_numero: str, participamos: bool, fase_a_ok: bool, monto_ofertado: float | None):
        self.cursor.execute("""
            UPDATE lotes
            SET participamos = ?, fase_A_superada = ?, monto_ofertado = ?
            WHERE licitacion_id = ? AND CAST(numero AS TEXT) = CAST(? AS TEXT)
        """, (1 if participamos else 0, 1 if fase_a_ok else 0, float(monto_ofertado or 0.0), licitacion_id, str(lote_numero)))
        self.conn.commit()


    def obtener_todas_las_fallas(self):
        """Obtiene todos los fallos de la base de datos para el dashboard global, incluyendo el ID del documento."""
        self.cursor.execute("""
            SELECT l.institucion, dfa.participante_nombre, d.nombre, dfa.es_nuestro, d.id
            FROM descalificaciones_fase_a dfa
            JOIN documentos d ON dfa.documento_id = d.id
            JOIN licitaciones l ON dfa.licitacion_id = l.id
        """)
        return self.cursor.fetchall()

    def _update_or_insert_documentos(self, licitacion_id, documentos_en_memoria):
        """
        Actualiza, inserta o elimina documentos de forma inteligente para no romper
        las claves foráneas que dependen de ellos.
        """
        # Obtenemos los IDs de los documentos que existen en la BD para esta licitación
        self.cursor.execute("SELECT id FROM documentos WHERE licitacion_id = ?", (licitacion_id,))
        ids_en_db = {row[0] for row in self.cursor.fetchall()}
        
        ids_en_memoria = {doc.id for doc in documentos_en_memoria if doc.id is not None}

        # 1. Documentos para BORRAR: están en la BD pero ya no en la memoria.
        ids_para_borrar = ids_en_db - ids_en_memoria
        if ids_para_borrar:
            placeholders = ",".join("?" * len(ids_para_borrar))
            # Importante: Borramos primero las fallas dependientes para evitar errores.
            self.cursor.execute(f"DELETE FROM descalificaciones_fase_a WHERE documento_id IN ({placeholders})", list(ids_para_borrar))
            self.cursor.execute(f"DELETE FROM documentos WHERE id IN ({placeholders})", list(ids_para_borrar))

        # 2. Documentos para ACTUALIZAR o INSERTAR
        cols = ['codigo', 'nombre', 'categoria', 'comentario', 'presentado', 'subsanable', 
                'ruta_archivo', 'responsable', 'revisado', 'obligatorio', 'orden_pliego']
        
        for doc in documentos_en_memoria:
            if doc.id in ids_en_db:
                # Si el ID ya existe, es un UPDATE
                update_sql = f"UPDATE documentos SET {', '.join(f'{c}=?' for c in cols)} WHERE id=?"
                values = [getattr(doc, c, None) for c in cols] + [doc.id]
                self.cursor.execute(update_sql, values)
            else:
                # Si el ID es nuevo o no existe, es un INSERT
                insert_cols = ['licitacion_id'] + cols
                placeholders = ",".join("?" * len(insert_cols))
                insert_sql = f"INSERT INTO documentos ({', '.join(insert_cols)}) VALUES ({placeholders})"
                values = [licitacion_id] + [getattr(doc, c, None) for c in cols]
                self.cursor.execute(insert_sql, values)
                # Actualizamos el objeto en memoria con el nuevo ID generado por la BD.
                doc.id = self.cursor.lastrowid


    def get_empresas_maestras(self):
        """
        Devuelve empresas maestras como lista de dicts:
        [{'nombre': ..., 'rnc': ..., 'telefono': ..., 'correo': ..., 'direccion': ...}, ...]
        """
        try:
            self.cursor.execute("""
                SELECT nombre, rnc, telefono, correo, direccion
                FROM empresas_maestras
                ORDER BY nombre COLLATE NOCASE
            """)
            filas = self.cursor.fetchall()
            return [
                {
                    "nombre":     (f[0] or "").strip(),
                    "rnc":        (f[1] or "").strip() if len(f) > 1 and f[1] else "",
                    "telefono":   (f[2] or "").strip() if len(f) > 2 and f[2] else "",
                    "correo":     (f[3] or "").strip() if len(f) > 3 and f[3] else "",
                    "direccion":  (f[4] or "").strip() if len(f) > 4 and f[4] else "",
                }
                for f in filas
            ]
        except Exception as e:
            print("[WARN] get_empresas_maestras falló:", e)
            return []



    # ================= GANADORES POR LOTE =================

    def save_ganadores_por_lote(self, licitacion_id: int, mapping: list[tuple]):
        """
        mapping: lista de tuplas (lote_numero, ganador_nombre, es_nuestro_bool)
        Si es_nuestro_bool is True => empresa_nuestra = ganador_nombre.
        """
        try:
            if not mapping:
                return True  # nada que hacer

            # 0) asegurar catálogo para las empresas nuestras
            for _, ganador_nombre, es_nuestro in mapping:
                if es_nuestro and ganador_nombre:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO empresas_maestras (nombre) VALUES (?)",
                        (ganador_nombre.strip(),)
                    )

            # 1) reemplazo completo de filas de esta licitación
            self.cursor.execute(
                "DELETE FROM licitacion_ganadores_lote WHERE licitacion_id = ?",
                (licitacion_id,)
            )

            rows = []
            for lote_num, ganador_nombre, es_nuestro in mapping:
                empresa_nuestra = ganador_nombre if es_nuestro else None
                rows.append((licitacion_id, str(lote_num), str(ganador_nombre), empresa_nuestra))

            self.cursor.executemany(
                """INSERT INTO licitacion_ganadores_lote (licitacion_id, lote_numero, ganador_nombre, empresa_nuestra)
                VALUES (?,?,?,?)
                ON CONFLICT(licitacion_id, lote_numero) DO UPDATE SET
                    ganador_nombre=excluded.ganador_nombre,
                    empresa_nuestra=excluded.empresa_nuestra""",
                rows
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"[DB] save_ganadores_por_lote falló: {e}")
            return False

        
    def _ensure_ganadores_empresa_col(self):
        """Asegura que la tabla licitacion_ganadores_lote tenga la columna empresa_nuestra."""
        try:
            self.cursor.execute("PRAGMA table_info(licitacion_ganadores_lote)")
            cols = [r[1] for r in self.cursor.fetchall()]
            if "empresa_nuestra" not in cols:
                # Migración mínima: agregar la columna
                self.cursor.execute("ALTER TABLE licitacion_ganadores_lote ADD COLUMN empresa_nuestra TEXT")
                # (Opcional) si quieres inicializar algo, haz UPDATE aquí.
                self.conn.commit()
        except Exception as e:
            # No interrumpas el arranque por la migración; solo infórmalo en consola
            print(f"[WARN] No se pudo asegurar columna empresa_nuestra en licitacion_ganadores_lote: {e}")


    def marcar_ganador_lote(self, licitacion_id, lote_numero, ganador_nombre, empresa_nuestra=None):
        """
        Guarda/actualiza el ganador de un lote.
        Garantiza 1 ganador por (licitacion_id, lote_numero).
        """
        # si es nuestra empresa, primero asegúrala en el catálogo
        if empresa_nuestra:
            self.cursor.execute(
                "INSERT OR IGNORE INTO empresas_maestras (nombre) VALUES (?)",
                (empresa_nuestra.strip(),)
            )

        self.cursor.execute("""
            INSERT INTO licitacion_ganadores_lote(licitacion_id, lote_numero, ganador_nombre, empresa_nuestra)
            VALUES(?,?,?,?)
            ON CONFLICT(licitacion_id, lote_numero) DO UPDATE SET
                ganador_nombre  = excluded.ganador_nombre,
                empresa_nuestra = excluded.empresa_nuestra
        """, (licitacion_id, str(lote_numero), (ganador_nombre or ""), (empresa_nuestra or None)))
        self.conn.commit()
        return True


    def borrar_ganador_lote(self, licitacion_id, lote_numero):
        """Elimina el registro de ganador para ese lote (deja 'sin ganador')."""
        self.cursor.execute(
            "DELETE FROM licitacion_ganadores_lote WHERE licitacion_id=? AND lote_numero=?",
            (licitacion_id, str(lote_numero))
        )
        self.conn.commit()
        return True



    def save_empresas_nuestras(self, licitacion_id: int, empresas: list[str]):
        """
        Vincula empresas con la licitación.
        FIX: antes de insertar en la tabla relacional, nos aseguramos
        de que cada empresa exista en el catálogo 'empresas_maestras'
        para no violar la FK.
        """
        # 1) normalizamos nombres
        empresas_norm = [(e or "").strip() for e in empresas if (e or "").strip()]

        # 2) aseguramos catálogo
        for nombre in empresas_norm:
            self.cursor.execute(
                "INSERT OR IGNORE INTO empresas_maestras (nombre) VALUES (?)",
                (nombre,)
            )

        # 3) borramos vínculos anteriores y creamos los nuevos
        self.cursor.execute(
            "DELETE FROM licitacion_empresas_nuestras WHERE licitacion_id = ?",
            (licitacion_id,)
        )
        for nombre in empresas_norm:
            self.cursor.execute(
                "INSERT OR IGNORE INTO licitacion_empresas_nuestras (licitacion_id, empresa_nombre) VALUES (?, ?)",
                (licitacion_id, nombre)
            )
        self.conn.commit()


    def agregar_empresa_maestra(self, nombre: str):
        """Inserta una empresa en el catálogo de empresas maestras."""
        if not nombre:
            return False
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO empresas_maestras (nombre) VALUES (?)",
                (nombre.strip(),)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print("Error al agregar empresa:", e)
            return False


# En la clase DatabaseManager, REEMPLAZA este método por completo:

# En la clase DatabaseManager

    def get_all_data(self):
        """
        Recupera todas las licitaciones y sus entidades relacionadas.
        - Incluye compatibilidad con datos antiguos donde la empresa estaba en la tabla principal.
        """
        # === LICITACIONES ===
        self.cursor.execute("SELECT * FROM licitaciones")
        lic_cols = [d[0] for d in self.cursor.description]
        licitaciones_dict = {}

        for row in self.cursor.fetchall():
            lic = dict(zip(lic_cols, row)) 
            lic_id = lic.get("id")

            legacy_company_name = None
            if isinstance(lic.get("empresa_nuestra"), str) and lic["empresa_nuestra"]:
                legacy_company_name = lic["empresa_nuestra"]

            lic["empresa_nuestra"] = None 

            if isinstance(lic.get("cronograma"), str):
                try: lic["cronograma"] = json.loads(lic["cronograma"] or "{}")
                except Exception: lic["cronograma"] = {}
            else:
                lic["cronograma"] = lic.get("cronograma") or {}

            # ▼▼▼ AÑADE "fallas_fase_a" AL DICCIONARIO ▼▼▼
            lic.update({
                "lotes": [], "documentos_solicitados": [], "oferentes_participantes": [],
                "bnb_evaluacion": [], "riesgos": [], "empresas_nuestras": [], "fallas_fase_a": [],
                "_legacy_company": legacy_company_name 
            })
            # ▲▲▲ FIN DEL CAMBIO ▲▲▲
            licitaciones_dict[lic_id] = lic

        if not licitaciones_dict:
            return [], [], [], [], [], []

        # === EMPRESAS NUESTRAS (Tabla nueva) ===
        self.cursor.execute("SELECT licitacion_id, empresa_nombre FROM licitacion_empresas_nuestras")
        emp_por_lic = {}
        for lic_id, nombre in self.cursor.fetchall():
            if nombre:
                emp_por_lic.setdefault(lic_id, set()).add(nombre.strip())

        # === ASIGNACIÓN FINAL DE EMPRESAS ===
        for lic_id, lic in licitaciones_dict.items():
            nombres_empresas = emp_por_lic.get(lic_id, set())
            if not nombres_empresas and lic.get("_legacy_company"):
                nombres_empresas.add(lic["_legacy_company"])
            lic["empresas_nuestras"] = [{"nombre": nombre} for nombre in sorted(list(nombres_empresas))]
            if "_legacy_company" in lic:
                del lic["_legacy_company"]
        
        # LOTES, DOCUMENTOS, etc. (sin cambios)
        cols_lotes = {r[1] for r in self.cursor.execute("PRAGMA table_info(lotes)").fetchall()}
        tiene_emp_lote = "empresa_nuestra" in cols_lotes
        self.cursor.execute(f"SELECT id, licitacion_id, numero, nombre, monto_base, monto_base_personal, monto_ofertado, participamos, fase_A_superada{', empresa_nuestra' if tiene_emp_lote else ''} FROM lotes ORDER BY CASE WHEN numero GLOB '*[0-9]*' THEN CAST(numero AS INTEGER) ELSE NULL END, numero")
        lot_cols = [d[0] for d in self.cursor.description]
        for row in self.cursor.fetchall():
            l = dict(zip(lot_cols, row)); lic_id = l.get("licitacion_id")
            if lic_id not in licitaciones_dict: continue
            l["monto_base"] = float(l.get("monto_base") or 0.0); l["monto_base_personal"] = float(l.get("monto_base_personal") or 0.0); l["monto_ofertado"] = float(l.get("monto_ofertado") or 0.0)
            l["participamos"] = bool(l.get("participamos")); l["fase_A_superada"] = bool(l.get("fase_A_superada"))
            if tiene_emp_lote: l["empresa_nuestra"] = (l.get("empresa_nuestra") or "").strip() or None
            else: l["empresa_nuestra"] = None
            l.setdefault("ganador_nombre", ""); l.setdefault("ganado_por_nosotros", False)
            licitaciones_dict[lic_id]["lotes"].append(l)

        self.cursor.execute("SELECT * FROM documentos"); doc_cols = [d[0] for d in self.cursor.description]
        for row in self.cursor.fetchall():
            d = dict(zip(doc_cols, row)); lic_id = d.get("licitacion_id")
            if lic_id in licitaciones_dict: licitaciones_dict[lic_id]["documentos_solicitados"].append(d)

        self.cursor.execute("SELECT * FROM bnb_evaluaciones"); bnb_cols = [d[0] for d in self.cursor.description]
        for row in self.cursor.fetchall():
            b = dict(zip(bnb_cols, row)); lic_id = b.get("licitacion_id")
            if lic_id in licitaciones_dict: licitaciones_dict[lic_id]["bnb_evaluacion"].append(b)

        self.cursor.execute("SELECT * FROM riesgos"); r_cols = [d[0] for d in self.cursor.description]
        for row in self.cursor.fetchall():
            r = dict(zip(r_cols, row)); lic_id = r.get("licitacion_id")
            if lic_id in licitaciones_dict: licitaciones_dict[lic_id]["riesgos"].append(r)

        # ▼▼▼ INICIO DEL BLOQUE NUEVO PARA CARGAR FALLAS ▼▼▼
        # === FALLAS FASE A ===
        try:
            self.cursor.execute("SELECT licitacion_id, participante_nombre, documento_id, comentario, es_nuestro FROM descalificaciones_fase_a")
            dfa_cols = ['licitacion_id', 'participante_nombre', 'documento_id', 'comentario', 'es_nuestro']
            for row in self.cursor.fetchall():
                dfa = dict(zip(dfa_cols, row))
                lic_id = dfa.get("licitacion_id")
                if lic_id in licitaciones_dict:
                    licitaciones_dict[lic_id]["fallas_fase_a"].append(dfa)
        except sqlite3.OperationalError:
            # La tabla podría no existir en una base de datos muy antigua, no es un error crítico.
            pass
        # ▲▲▲ FIN DEL BLOQUE NUEVO ▲▲▲

        # OFERENTES, GANADORES, etc. (sin cambios)
        self.cursor.execute("SELECT o.id, o.licitacion_id, o.nombre, o.comentario, ol.lote_numero, ol.monto, ol.paso_fase_A FROM oferentes o LEFT JOIN ofertas_lote_oferentes ol ON o.id = ol.oferente_id")
        oferentes_temp = {}
        for oferente_id, lic_id, nombre, comentario, lote_num, monto, paso_a in self.cursor.fetchall():
            if lic_id not in licitaciones_dict: continue
            if oferente_id not in oferentes_temp: oferentes_temp[oferente_id] = {"licitacion_id": lic_id, "nombre": nombre, "comentario": comentario, "ofertas_por_lote": []}
            if lote_num is not None: oferentes_temp[oferente_id]["ofertas_por_lote"].append({"lote_numero": lote_num, "monto": float(monto or 0.0), "paso_fase_A": bool(paso_a), "ganador": False})
        for ofr in oferentes_temp.values():
            lic_id = ofr["licitacion_id"]
            if lic_id in licitaciones_dict: licitaciones_dict[lic_id]["oferentes_participantes"].append(ofr)
        try:
            cols_g = {r[1] for r in self.cursor.execute("PRAGMA table_info(licitacion_ganadores_lote)").fetchall()}
            if "empresa_nuestra" in cols_g: self.cursor.execute("SELECT licitacion_id, lote_numero, ganador_nombre, empresa_nuestra FROM licitacion_ganadores_lote"); ganador_rows = self.cursor.fetchall(); esquema = "nuevo"
            else: self.cursor.execute("SELECT licitacion_id, lote_numero, ganador_nombre, es_nuestro FROM licitacion_ganadores_lote"); ganador_rows = self.cursor.fetchall(); esquema = "viejo"
        except Exception: ganador_rows = []; esquema = "ninguno"
        gan_por_lic = {}
        if esquema == "nuevo":
            for lic_id, lote_num, ganador_nombre, empresa_nuestra in ganador_rows:
                gan_por_lic.setdefault(lic_id, []).append({
                    "lote_numero": lote_num,
                    "ganador_nombre": (ganador_nombre or "").strip(),
                    "empresa_nuestra": (empresa_nuestra or "").strip()
                })
        # ...
        for lic_id, lic in licitaciones_dict.items():
            if lic_id not in gan_por_lic: continue
            for g in gan_por_lic[lic_id]:
                loteno  = str(g.get("lote_numero"))
                ganador = (g.get("ganador_nombre") or "").strip()
                for L in lic["lotes"]:
                    if str(L.get("numero")) != loteno: continue
                    L["ganador_nombre"] = ganador
                    if esquema == "nuevo":
                        emp_n_row = (g.get("empresa_nuestra") or "").strip()
                        emp_lote  = (L.get("empresa_nuestra") or "").strip()
                        L["ganado_por_nosotros"] = bool(emp_n_row) or (emp_lote and ganador and ganador == emp_lote)
                    else:
                        # soporte legado con 'es_nuestro'
                        es_nuestro = bool(g.get("es_nuestro"))
                        if es_nuestro:
                            L["ganado_por_nosotros"] = True
                        else:
                            emp_lote = (L.get("empresa_nuestra") or "").strip()
                            L["ganado_por_nosotros"] = bool(emp_lote and ganador and ganador == emp_lote)
                    break

            for g in gan_por_lic[lic_id]:
                loteno = str(g.get("lote_numero")); ganador = (g.get("ganador_nombre") or "").strip()
                for comp in lic["oferentes_participantes"]:
                    if comp.get("nombre") == ganador:
                        for o in comp.get("ofertas_por_lote", []):
                            if str(o.get("lote_numero")) == loteno: o["ganador"] = True
                    else:
                        for o in comp.get("ofertas_por_lote", []): o.setdefault("ganador", False)
        
        master_tables = ["empresas_maestras", "instituciones_maestras", "documentos_maestros", "competidores_maestros", "responsables_maestros"]
        master_data = [self._get_master_table(tbl) for tbl in master_tables]
        return list(licitaciones_dict.values()), *master_data

    def _get_master_table(self, table_name):
        self.cursor.execute(f'SELECT * FROM {table_name}')
        cols = [d[0] for d in self.cursor.description]
        return [dict(zip(cols, row)) for row in self.cursor.fetchall()]

    def save_licitacion(self, licitacion):
        """
        Guarda una licitación y todos sus datos relacionados, con control
        de concurrencia 'suave' (un reintento si el timestamp cambió).
        """
        is_new = not hasattr(licitacion, 'id') or not licitacion.id
        manage_transaction = not self.conn.in_transaction

        def _do_update():
            new_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%f')
            empresas_str = ", ".join(sorted([str(e) for e in licitacion.empresas_nuestras]))
            lic_data = {
                'nombre_proceso': licitacion.nombre_proceso,
                'numero_proceso': licitacion.numero_proceso,
                'institucion': licitacion.institucion,
                'empresa_nuestra': empresas_str,
                'estado': licitacion.estado,
                'fase_A_superada': licitacion.fase_A_superada,
                'fase_B_superada': licitacion.fase_B_superada,
                'adjudicada': licitacion.adjudicada,
                'adjudicada_a': licitacion.adjudicada_a,
                'motivo_descalificacion': licitacion.motivo_descalificacion,
                'fecha_creacion': licitacion.fecha_creacion.strftime('%Y-%m-%d'),
                'cronograma': json.dumps(licitacion.cronograma),
                'docs_completos_manual': licitacion.docs_completos_manual,
                'bnb_score': getattr(licitacion, 'bnb_score', -1.0),
                'last_modified': new_timestamp
            }

            if not is_new:
                licitacion_id = licitacion.id
                columns_to_update = ', '.join(f'{k}=?' for k in lic_data)
                self.cursor.execute(
                    f"UPDATE licitaciones SET {columns_to_update} WHERE id=?",
                    list(lic_data.values()) + [licitacion_id]
                )
            else:
                insert_query = f"INSERT INTO licitaciones ({', '.join(lic_data.keys())}) VALUES ({','.join('?'*len(lic_data))})"
                self.cursor.execute(insert_query, list(lic_data.values()))
                licitacion.id = self.cursor.lastrowid

            licitacion.last_modified = new_timestamp

        try:
            if manage_transaction:
                self.cursor.execute('BEGIN IMMEDIATE TRANSACTION')

            if not is_new:
                # 1) Comprobación de duplicado de código
                self.cursor.execute(
                    'SELECT 1 FROM licitaciones WHERE numero_proceso = ? AND id <> ?',
                    (licitacion.numero_proceso, licitacion.id)
                )
                if self.cursor.fetchone():
                    if manage_transaction: self.conn.rollback()
                    raise ValueError("Ya existe otra licitación con el mismo código.")

                # 2) Control de concurrencia SUAVE
                self.cursor.execute('SELECT last_modified FROM licitaciones WHERE id = ?', (licitacion.id,))
                row = self.cursor.fetchone()
                db_ts = row[0] if row else None

                # Si ambos son None o iguales, seguimos normal; si difieren, hacemos UN reintento:
                if db_ts is not None and licitacion.last_modified is not None and db_ts != licitacion.last_modified:
                    # Recargo el timestamp y continúo
                    licitacion.last_modified = db_ts

            # === Escritura principal ===
            _do_update()

            # ==== RELACIONADOS ====
            self.save_empresas_nuestras(licitacion.id, [str(e) for e in licitacion.empresas_nuestras])

            # Lotes y riesgos por método clásico
            self._save_related_data('lotes', licitacion.id, licitacion.lotes,
                                    ['licitacion_id','numero','nombre','monto_base','monto_base_personal',
                                    'monto_ofertado','participamos','fase_A_superada','empresa_nuestra'])
            self._save_related_data('riesgos', licitacion.id, [r.to_dict() for r in licitacion.riesgos],
                                    ['licitacion_id','descripcion','categoria','impacto','probabilidad','mitigacion'])

            # Documentos (inteligente) y Fallas
            self._update_or_insert_documentos(licitacion.id, licitacion.documentos_solicitados)
            self._save_related_data('descalificaciones_fase_a', licitacion.id, getattr(licitacion, 'fallas_fase_a', []),
                                    ['licitacion_id','participante_nombre','documento_id','comentario','es_nuestro'])

            # Oferentes y ofertas por lote
            self.cursor.execute('DELETE FROM oferentes WHERE licitacion_id = ?', (licitacion.id,))
            if licitacion.oferentes_participantes:
                for oferente in licitacion.oferentes_participantes:
                    self.cursor.execute(
                        'INSERT INTO oferentes (licitacion_id, nombre, comentario) VALUES (?,?,?)',
                        (licitacion.id, oferente.nombre, oferente.comentario)
                    )
                    oferente_id = self.cursor.lastrowid
                    if getattr(oferente, 'ofertas_por_lote', None):
                        ofertas_to_save = [
                            (oferente_id, o['lote_numero'], o['monto'], o.get('paso_fase_A', True),
                            o.get('plazo_entrega', 0), o.get('garantia_meses', 0))
                            for o in oferente.ofertas_por_lote
                        ]
                        self.cursor.executemany(
                            'INSERT INTO ofertas_lote_oferentes (oferente_id, lote_numero, monto, paso_fase_A, plazo_entrega, garantia_meses) VALUES (?,?,?,?,?,?)',
                            ofertas_to_save
                        )

            if manage_transaction:
                self.conn.commit()

            return True

        except Exception as e:
            if manage_transaction:
                self.conn.rollback()
            raise e


    def get_last_modified(self, licitacion_id: int):
        self.cursor.execute('SELECT last_modified FROM licitaciones WHERE id=?', (licitacion_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None


    def save_single_institucion(self, institucion_data):
        """Guarda o actualiza una sola institución en la tabla maestra."""
        try:
            sql = """
                INSERT INTO instituciones_maestras (nombre, rnc, telefono, correo, direccion)
                VALUES (:nombre, :rnc, :telefono, :correo, :direccion)
                ON CONFLICT(nombre) DO UPDATE SET
                    rnc=excluded.rnc,
                    telefono=excluded.telefono,
                    correo=excluded.correo,
                    direccion=excluded.direccion
            """
            self.cursor.execute(sql, institucion_data)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar institución individual: {e}")
            self.conn.rollback()
            return False


    # ===== Helpers para ganadores por lote =====
    def get_ganadores_por_lote(self, licitacion_id: int):
        self.cursor.execute("""
            SELECT lote_numero, ganador_nombre, es_nuestro
            FROM licitacion_ganadores_lote
            WHERE licitacion_id = ?
            ORDER BY CAST(lote_numero AS INTEGER)
        """, (licitacion_id,))
        rows = self.cursor.fetchall()
        return [
            {"lote_numero": r[0], "ganador_nombre": r[1], "es_nuestro": int(r[2]) if r[2] is not None else 0}
            for r in rows
        ]

    def ganador_de_competidor_en_licitacion(self, licitacion_id: int, competidor_nombre: str) -> bool:
        self.cursor.execute("""
            SELECT 1
            FROM licitacion_ganadores_lote
            WHERE licitacion_id = ? AND ganador_nombre = ?
            LIMIT 1
        """, (licitacion_id, competidor_nombre))
        return self.cursor.fetchone() is not None

    def cantidad_lotes_ganados_por_competidor(self, licitacion_id: int, competidor_nombre: str) -> int:
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM licitacion_ganadores_lote
            WHERE licitacion_id = ? AND ganador_nombre = ?
        """, (licitacion_id, competidor_nombre))
        row = self.cursor.fetchone()
        return int(row[0]) if row else 0






    def _save_related_data(self, table_name, licitacion_id, data_list, columns):
        """Borra e inserta datos en tablas relacionadas."""
        self.cursor.execute(f'DELETE FROM {table_name} WHERE licitacion_id = ?', (licitacion_id,))
        if data_list:
            to_save = [
                tuple(item.get(col) if isinstance(item, dict) else getattr(item, col) for col in columns[1:])
                for item in data_list
            ]
            to_save_with_id = [(licitacion_id,) + row for row in to_save]
            placeholders = ','.join('?' * len(columns))
            self.cursor.executemany(
                f'INSERT INTO {table_name} ({",".join(columns)}) VALUES ({placeholders})',
                to_save_with_id
            )

    def _save_master_table(self, table_name, data_list, columns, unique_cols, replace=False):
        """
        Guarda una lista maestra de forma segura.
        - Por defecto hace UPSERT (NO destructivo).
        - Si replace=True, borra todo antes de insertar.
        - columns: columnas a escribir en INSERT.
        - unique_cols: columnas que definen la clave única para ON CONFLICT.
        """
        if replace:
            self.cursor.execute(f"DELETE FROM {table_name}")

        if not data_list:
            return  # nada que insertar

        filas = []
        for item in data_list:
            if not isinstance(item, dict):
                try:
                    item = item.to_dict()
                except Exception:
                    item = getattr(item, "__dict__", {})
            filas.append(tuple(item.get(c) for c in columns))

        placeholders = ",".join("?" * len(columns))
        cols_joined = ",".join(columns)
        conflict_target = ",".join(unique_cols)

        update_cols = [c for c in columns if c not in unique_cols]
        if update_cols:
            set_clause = ", ".join([f"{c}=excluded.{c}" for c in update_cols])
            sql = f"""
                INSERT INTO {table_name} ({cols_joined})
                VALUES ({placeholders})
                ON CONFLICT({conflict_target}) DO UPDATE SET
                {set_clause}
            """
        else:
            sql = f"""
                INSERT INTO {table_name} ({cols_joined})
                VALUES ({placeholders})
                ON CONFLICT({conflict_target}) DO NOTHING
            """

        self.cursor.executemany(sql, filas)


    def save_master_lists(self, empresas, instituciones, documentos_maestros,
                            competidores_maestros, responsables_maestros, replace_tables=None):
            """
            Guarda todas las listas maestras.
            - UPSERT por defecto (no borra).
            - Usa replace_tables={'tabla1','tabla2',...} solo si necesitas reemplazo total.
            Tablas válidas: 'empresas_maestras','instituciones_maestras','documentos_maestros',
                            'competidores_maestros','responsables_maestros'
            """
            try:
                # --- CORRECCIÓN ---
                # Se elimina la línea "docs_to_save = [d.to_dict() for d in documentos_maestros]"
                # que era redundante y causaba el error. Pasaremos 'documentos_maestros' directamente.
                
                replace_tables = set(replace_tables or [])

                def safe_replace(flag, data_list, tabla):
                    # Evita un borrado total si la lista llega vacía por error
                    if flag and not data_list:
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{ts}] [SAFEGUARD] Ignorando replace en {tabla}: lista vacía.")
                        return False
                    return flag

                # EMPRESAS
                self._save_master_table(
                    table_name='empresas_maestras',
                    data_list=empresas,
                    columns=['nombre', 'rnc', 'telefono', 'correo', 'direccion'],
                    unique_cols=['nombre'],
                    replace=safe_replace('empresas_maestras' in replace_tables, empresas, 'empresas_maestras')
                )

                # INSTITUCIONES
                self._save_master_table(
                    table_name='instituciones_maestras',
                    data_list=instituciones,
                    columns=['nombre', 'rnc', 'telefono', 'correo', 'direccion'],
                    unique_cols=['nombre'],
                    replace=safe_replace('instituciones_maestras' in replace_tables, instituciones, 'instituciones_maestras')
                )

                # DOCUMENTOS
                # Normalizamos 'empresa_nombre' a un string vacío si es None
                docs_to_save = []
                for d in documentos_maestros:
                    # Aseguramos que trabajamos con diccionarios
                    d_dict = d.to_dict() if hasattr(d, 'to_dict') else dict(d)
                    if d_dict.get('empresa_nombre') is None:
                        d_dict['empresa_nombre'] = ''
                    docs_to_save.append(d_dict)

                self._save_master_table(
                    table_name='documentos_maestros',
                    data_list=docs_to_save, # Usamos la lista normalizada
                    columns=['codigo', 'nombre', 'categoria', 'comentario', 'empresa_nombre', 'ruta_archivo'],
                    unique_cols=['codigo', 'empresa_nombre'],
                    replace=safe_replace('documentos_maestros' in replace_tables, docs_to_save, 'documentos_maestros')
                )

                # COMPETIDORES
                self._save_master_table(
                    table_name='competidores_maestros',
                    data_list=competidores_maestros,
                    columns=['nombre', 'rnc', 'rpe', 'representante'],
                    unique_cols=['nombre'],
                    replace=safe_replace('competidores_maestros' in replace_tables, competidores_maestros, 'competidores_maestros')
                )

                # RESPONSABLES
                self._save_master_table(
                    table_name='responsables_maestros',
                    data_list=responsables_maestros,
                    columns=['nombre'],
                    unique_cols=['nombre'],
                    replace=safe_replace('responsables_maestros' in replace_tables, responsables_maestros, 'responsables_maestros')
                )

                self.conn.commit()

            except Exception as e:
                import logging
                logging.error(f"Error al guardar listas maestras: {e}")
                self.conn.rollback()
                raise

    # ================= EXPEDIENTES (DB) =================
    def crear_expediente(self, licitacion_id, titulo, creado_por):
        self.cursor.execute(
            "INSERT INTO expedientes (licitacion_id, titulo, creado_por) VALUES (?,?,?)",
            (licitacion_id, titulo, creado_por)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def agregar_items_expediente(self, expediente_id, items):
        """
        items: lista de dicts o tuplas con:
            - orden (int)
            - doc_version_id (int -> documentos.id)
            - titulo (str)
        """
        rows = []
        for it in items:
            if isinstance(it, dict):
                rows.append((expediente_id, it['orden'], it['doc_version_id'], it['titulo']))
            else:
                # tupla (orden, doc_id, titulo)
                rows.append((expediente_id, it[0], it[1], it[2]))
        self.cursor.executemany(
            "INSERT INTO expediente_items (expediente_id, orden, doc_version_id, titulo) VALUES (?,?,?,?)",
            rows
        )
        self.conn.commit()

    def obtener_documentos_de_licitacion(self, licitacion_id):
        """Devuelve documentos (dicts) incluyendo 'orden_pliego'."""
        self.cursor.execute("""
            SELECT id, codigo, nombre, categoria, comentario, presentado,
                   subsanable, ruta_archivo, responsable, revisado, obligatorio,
                   orden_pliego
            FROM documentos
            WHERE licitacion_id = ?
            ORDER BY COALESCE(orden_pliego, 999999), categoria, codigo
        """, (licitacion_id,))
        cols = [d[0] for d in self.cursor.description]
        return [dict(zip(cols, row)) for row in self.cursor.fetchall()]
    
    def guardar_orden_documentos(self, licitacion_id, pares_docid_orden):
        """
        Persiste el orden elegido por el usuario.
        pares_docid_orden: lista de (doc_id:int, orden_pliego:int) en el orden final (1..N)
        """
        try:
            self.cursor.executemany(
                "UPDATE documentos SET orden_pliego=? WHERE id=? AND licitacion_id=?",
                [(orden, doc_id, licitacion_id) for (doc_id, orden) in pares_docid_orden]
            )
            self.conn.commit()
            return True
        except Exception as e:
            print("[ERROR] guardar_orden_documentos:", e)
            return False


    def obtener_expediente(self, expediente_id):
        """Devuelve cabecera + items (ya ordenados)."""
        self.cursor.execute("SELECT * FROM expedientes WHERE id=?", (expediente_id,))
        exp_cols = [d[0] for d in self.cursor.description]
        exp = dict(zip(exp_cols, self.cursor.fetchone()))
        self.cursor.execute("""
            SELECT ei.id, ei.orden, ei.doc_version_id, ei.titulo, d.ruta_archivo
            FROM expediente_items ei
            JOIN documentos d ON d.id = ei.doc_version_id
            WHERE ei.expediente_id = ?
            ORDER BY ei.orden ASC
        """, (expediente_id,))
        cols = [d[0] for d in self.cursor.description]
        exp['items'] = [dict(zip(cols, row)) for row in self.cursor.fetchall()]
        return exp







    def delete_licitacion(self, numero_proceso):
        try:
            self.cursor.execute('DELETE FROM licitaciones WHERE numero_proceso = ?', (numero_proceso,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al eliminar la licitación {numero_proceso}: {e}")
            self.conn.rollback()
            return False

    def run_sanity_checks(self):
        """Ejecuta chequeos de integridad en la base de datos."""
        issues = {'orphans': {}, 'missing_indexes': []}
        # 1. Huérfanos
        orphan_checks = {
            'lotes': ('id', 'licitacion_id', 'licitaciones'),
            'documentos': ('id', 'licitacion_id', 'licitaciones'),
            'oferentes': ('id', 'licitacion_id', 'licitaciones'),
            'riesgos': ('id', 'licitacion_id', 'licitaciones'),
            'ofertas_lote_oferentes': ('id', 'oferente_id', 'oferentes'),
            # Caso especial para tablas sin columna 'id'
            'kit_items': (['kit_id', 'documento_maestro_id'], 'kit_id', 'kits_de_requisitos')
        }
        for table, config in orphan_checks.items():
            pk_column, fk_column, parent_table = config
            select_col = "id" if isinstance(pk_column, str) else fk_column
            query = f"""
                SELECT t1.{select_col} FROM {table} AS t1
                LEFT JOIN {parent_table} AS t2 ON t1.{fk_column} = t2.id
                WHERE t2.id IS NULL
            """
            self.cursor.execute(query)
            orphans = [row[0] for row in self.cursor.fetchall()]
            if orphans:
                issues['orphans'][table] = orphans

        # 2. Índices faltantes
        expected_indexes = {
            'idx_lotes_licitacion_id': ('lotes', 'licitacion_id'),
            'idx_documentos_licitacion_id': ('documentos', 'licitacion_id'),
            'idx_oferentes_licitacion_id': ('oferentes', 'licitacion_id'),
            'idx_riesgos_licitacion_id': ('riesgos', 'licitacion_id'),
            'idx_ofertas_oferente_id': ('ofertas_lote_oferentes', 'oferente_id'),
        }
        for index_name, (table, column) in expected_indexes.items():
            self.cursor.execute(f"PRAGMA index_list('{table}')")
            if not any(index_name in idx for idx in self.cursor.fetchall()):
                issues['missing_indexes'].append({'name': index_name, 'table': table, 'column': column})
        return issues

    def begin_transaction(self):
        """Inicia una transacción explícita."""
        try:
            self.cursor.execute('BEGIN IMMEDIATE TRANSACTION')
        except sqlite3.OperationalError as e:
            print(f"Advertencia al iniciar transacción: {e}")

    def rollback_transaction(self):
        """Revierte la transacción actual."""
        self.conn.rollback()

    def auto_repair(self, issues):
        """Intenta reparar los problemas encontrados por run_sanity_checks."""
        report = []
        try:
            # 1. Reparar huérfanos
            if issues.get('orphans'):
                for table, ids in issues['orphans'].items():
                    delete_column = 'kit_id' if table == 'kit_items' else 'id'
                    placeholders = ','.join('?' for _ in ids)
                    self.cursor.execute(f"DELETE FROM {table} WHERE {delete_column} IN ({placeholders})", ids)
                    report.append(f"  - Se eliminaron {len(ids)} registros huérfanos de la tabla '{table}'.")
            # 2. Crear índices faltantes
            if issues.get('missing_indexes'):
                for index_info in issues['missing_indexes']:
                    name, table, column = index_info['name'], index_info['table'], index_info['column']
                    self.cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table}({column})")
                    report.append(f"  - Se creó el índice faltante '{name}' en la tabla '{table}'.")
            self.conn.commit()
            return True, "Reparación completada con éxito:\n" + "\n".join(report)
        except Exception as e:
            self.conn.rollback()
            return False, f"La reparación falló: {e}"

    def get_setting(self, clave, default=None):
        """Obtiene un valor de la tabla de configuración."""
        self.cursor.execute("SELECT valor FROM config_app WHERE clave = ?", (clave,))
        result = self.cursor.fetchone()
        return result[0] if result else default

    def set_setting(self, clave, valor):
        """Guarda o actualiza un valor en la tabla de configuración."""
        self.cursor.execute("INSERT OR REPLACE INTO config_app (clave, valor) VALUES (?, ?)", (clave, valor))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    # ======================== FTS ========================
    def setup_fts(self):
        # 1) Limpia triggers antiguos
        for trigger_name in [
            'licitaciones_after_insert', 'licitaciones_after_delete', 'licitaciones_after_update',
            'documentos_after_insert', 'documentos_after_delete', 'documentos_after_update'
        ]:
            self.cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name};")

        # 2) Asegura el esquema correcto del FTS
        self.cursor.execute("DROP TABLE IF EXISTS fts_licitaciones;")
        self.cursor.execute("DROP TABLE IF EXISTS fts_documentos;")

        # 3) FTS licitaciones (usa rowid = id)
        self.cursor.execute('''
            CREATE VIRTUAL TABLE fts_licitaciones USING fts5(
                numero_proceso,
                nombre_proceso,
                institucion,
                motivo_descalificacion,
                content='licitaciones',
                content_rowid='id'
            );
        ''')

        # Triggers licitaciones
        self.cursor.execute('''
            CREATE TRIGGER licitaciones_after_insert AFTER INSERT ON licitaciones BEGIN
                INSERT OR IGNORE INTO fts_licitaciones(rowid, numero_proceso, nombre_proceso, institucion, motivo_descalificacion)
                VALUES (new.id, new.numero_proceso, new.nombre_proceso, new.institucion, new.motivo_descalificacion);
            END;
        ''')
        self.cursor.execute('''
            CREATE TRIGGER licitaciones_after_update AFTER UPDATE ON licitaciones BEGIN
                INSERT OR REPLACE INTO fts_licitaciones(rowid, numero_proceso, nombre_proceso, institucion, motivo_descalificacion)
                VALUES (new.id, new.numero_proceso, new.nombre_proceso, new.institucion, new.motivo_descalificacion);
            END;
        ''')
        self.cursor.execute('''
            CREATE TRIGGER licitaciones_after_delete AFTER DELETE ON licitaciones BEGIN
                DELETE FROM fts_licitaciones WHERE rowid = old.id;
            END;
        ''')

        # 4) FTS documentos (sin columnas inexistentes; usaremos JOIN para IDs)
        self.cursor.execute('''
            CREATE VIRTUAL TABLE fts_documentos USING fts5(
                codigo,
                nombre,
                comentario,
                content='documentos',
                content_rowid='id'
            );
        ''')

        # Triggers documentos
        self.cursor.execute('''
            CREATE TRIGGER documentos_after_insert AFTER INSERT ON documentos BEGIN
                INSERT OR IGNORE INTO fts_documentos(rowid, codigo, nombre, comentario)
                VALUES (new.id, new.codigo, new.nombre, COALESCE(new.comentario, ''));
            END;
        ''')
        self.cursor.execute('''
            CREATE TRIGGER documentos_after_update AFTER UPDATE ON documentos BEGIN
                INSERT OR REPLACE INTO fts_documentos(rowid, codigo, nombre, comentario)
                VALUES (new.id, new.codigo, new.nombre, COALESCE(new.comentario, ''));
            END;
        ''')
        self.cursor.execute('''
            CREATE TRIGGER documentos_after_delete AFTER DELETE ON documentos BEGIN
                DELETE FROM fts_documentos WHERE rowid = old.id;
            END;
        ''')
        self.conn.commit()


    def set_busy_timeout(self, seconds: int):
        """Ajusta PRAGMA busy_timeout (ms)."""
        try:
            ms = int(seconds * 1000)
            self.conn.execute(f"PRAGMA busy_timeout = {ms}")
        except Exception as e:
            import logging
            logging.warning(f"[DB] No se pudo ajustar busy_timeout: {e}")

    def search_global(self, search_term):
        """Busca en FTS y devuelve resultados unificados con IDs reales."""
        if not search_term:
            return []
        query_term = f'"{search_term}"*'

        # Licitaciones desde FTS
        query_lic = """
            SELECT
                'Licitación' AS tipo,
                snippet(fts_licitaciones, 1, '➡️', '⬅️', '...', 15) AS contexto,
                fts_licitaciones.nombre_proceso AS referencia,
                fts_licitaciones.rowid AS licitacion_id,
                NULL AS documento_id,
                bm25(fts_licitaciones) AS rank
            FROM fts_licitaciones
            WHERE fts_licitaciones MATCH ?
        """

        # Documentos desde FTS (JOIN para mapear a licitacion_id y documento_id reales)
        query_doc = """
            SELECT
                'Documento' AS tipo,
                snippet(fts_documentos, 1, '➡️', '⬅️', '...', 15) AS contexto,
                d.nombre AS referencia,
                d.licitacion_id AS licitacion_id,
                d.id AS documento_id,
                bm25(fts_documentos) AS rank
            FROM fts_documentos
            JOIN documentos d ON d.id = fts_documentos.rowid
            WHERE fts_documentos MATCH ?
        """

        final_query = f"""
            {query_lic}
            UNION ALL
            {query_doc}
            ORDER BY rank
        """

        self.cursor.execute(final_query, (query_term, query_term))
        cols = ['tipo', 'contexto', 'referencia', 'licitacion_id', 'documento_id']
        return [dict(zip(cols, row)) for row in self.cursor.fetchall()]


    def integrity_check(self):
        """Ejecuta PRAGMA integrity_check y devuelve (ok: bool, mensaje: str)."""
        try:
            self.cursor.execute("PRAGMA integrity_check;")
            res = self.cursor.fetchone()
            msg = res[0] if res else "sin respuesta"
            return (msg == "ok"), msg
        except Exception as e:
            return False, f"Error en integrity_check: {e}"

    def rebuild_fts_index(self):
        """Reconstruye FTS evitando tocar estructuras dañadas."""
        try:
            # Transacción
            self.cursor.execute("BEGIN IMMEDIATE TRANSACTION;")

            # Elimina por completo las tablas FTS y recrea todo el esquema/trigger
            self.cursor.execute("DROP TABLE IF EXISTS fts_licitaciones;")
            self.cursor.execute("DROP TABLE IF EXISTS fts_documentos;")
            self.setup_fts()

            # Relleno vía comando especial 'rebuild' (si falla, fallback manual)
            try:
                self.cursor.execute("INSERT INTO fts_licitaciones(fts_licitaciones) VALUES('rebuild');")
                self.cursor.execute("INSERT INTO fts_documentos(fts_documentos) VALUES('rebuild');")
            except Exception:
                self.cursor.execute('''
                    INSERT INTO fts_licitaciones(rowid, numero_proceso, nombre_proceso, institucion, motivo_descalificacion)
                    SELECT id, numero_proceso, nombre_proceso, institucion, COALESCE(motivo_descalificacion,'')
                    FROM licitaciones;
                ''')
                self.cursor.execute('''
                    INSERT INTO fts_documentos(rowid, codigo, nombre, comentario)
                    SELECT id, COALESCE(codigo,''), COALESCE(nombre,''), COALESCE(comentario,'')
                    FROM documentos;
                ''')

            self.conn.commit()
            # Conteo
            self.cursor.execute("SELECT count(*) FROM fts_licitaciones;")
            c1 = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT count(*) FROM fts_documentos;")
            c2 = self.cursor.fetchone()[0]
            return True, c1 + c2
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

