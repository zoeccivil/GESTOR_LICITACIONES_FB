# clases_modelos.py
import datetime

class Lote:
    def __init__(self, **kwargs):
        self.numero = kwargs.get("numero", "")
        self.nombre = kwargs.get("nombre", "")
        self.monto_base = float(kwargs.get("monto_base", 0.0) or 0.0)
        self.monto_base_personal = float(kwargs.get("monto_base_personal", 0.0) or 0.0)
        self.monto_ofertado = float(kwargs.get("monto_ofertado", 0.0) or 0.0)
        self.participamos = kwargs.get("participamos", True)
        self.fase_A_superada = kwargs.get("fase_A_superada", True)
        self.ganador_nombre = kwargs.get("ganador_nombre", "")
        self.ganado_por_nosotros = kwargs.get("ganado_por_nosotros", False)
        self.empresa_nuestra = kwargs.get("empresa_nuestra", None)

    def to_dict(self):
        return {
            "numero": self.numero, "nombre": self.nombre, "monto_base": self.monto_base,
            "monto_base_personal": self.monto_base_personal, "monto_ofertado": self.monto_ofertado,
            "participamos": self.participamos, "fase_A_superada": self.fase_A_superada,
            "empresa_nuestra": self.empresa_nuestra
        }

class Oferente:
    def __init__(self, **kwargs):
        self.nombre = kwargs.get("nombre", "")
        self.comentario = kwargs.get("comentario", "")
        self.ofertas_por_lote = kwargs.get("ofertas_por_lote", [])

    def to_dict(self):
        return {"nombre": self.nombre, "comentario": self.comentario, "ofertas_por_lote": self.ofertas_por_lote}

    def get_monto_total_ofertado(self, solo_habilitados=False):
        ofertas_a_sumar = self.ofertas_por_lote
        if solo_habilitados:
            ofertas_a_sumar = [o for o in self.ofertas_por_lote if o.get('paso_fase_A', True)]
        return sum(oferta.get('monto', 0) for oferta in ofertas_a_sumar)

class Documento:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.codigo = kwargs.get("codigo")
        self.nombre = kwargs.get("nombre")
        self.categoria = kwargs.get("categoria")
        self.comentario = kwargs.get("comentario", "")
        self.presentado = kwargs.get("presentado", False)
        self.subsanable = kwargs.get("subsanable", "Subsanable")
        self.ruta_archivo = kwargs.get("ruta_archivo", "")
        self.empresa_nombre = kwargs.get("empresa_nombre", None)
        self.responsable = kwargs.get("responsable", "Sin Asignar")
        self.revisado = kwargs.get("revisado", False)
        self.obligatorio = kwargs.get("obligatorio", False)
        self.orden_pliego = kwargs.get("orden_pliego", None)
        
    def to_dict(self):
        return self.__dict__

    def __str__(self):
        estado = "✅" if self.presentado else "❌"
        adjunto = "📎" if self.ruta_archivo else ""
        revisado_str = "👁️" if self.revisado else ""
        comentario_str = f"({self.comentario})" if self.comentario else ""
        sub_str = {'Subsanable': '(S)', 'No Subsanable': '(NS)'}.get(self.subsanable, '')
        return f"{estado} {revisado_str} {adjunto} [{self.codigo}] {self.nombre} {sub_str} {comentario_str}".strip()

class Empresa:
    def __init__(self, nombre):
        self.nombre = nombre
    def to_dict(self):
        return {"nombre": self.nombre}
    def __str__(self):
        return self.nombre


class Licitacion:

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.nombre_proceso = kwargs.get("nombre_proceso", "")
        self.numero_proceso = kwargs.get("numero_proceso", "")
        self.institucion = kwargs.get("institucion", "")
        empresas = kwargs.get("empresas_nuestras", [])
        print(f"DEBUG: Cargando licitación '{self.numero_proceso}'. Datos de 'empresas_nuestras': {empresas}")
        self.empresas_nuestras = [Empresa(e["nombre"]) for e in empresas]
        self.estado = kwargs.get("estado", "Iniciada")
        self.fase_A_superada = kwargs.get("fase_A_superada", False)
        self.fase_B_superada = kwargs.get("fase_B_superada", False)
        self.adjudicada = kwargs.get("adjudicada", False)
        self.adjudicada_a = kwargs.get("adjudicada_a", "")
        self.motivo_descalificacion = kwargs.get("motivo_descalificacion", "")
        self.docs_completos_manual = kwargs.get("docs_completos_manual", False)
        self.last_modified = kwargs.get("last_modified")

        try:
            self.fecha_creacion = datetime.datetime.strptime(
                kwargs.get("fecha_creacion", str(datetime.date.today())), 
                '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            self.fecha_creacion = datetime.date.today()

        self.lotes = [Lote(**data) for data in kwargs.get("lotes", [])]
        self.oferentes_participantes = [Oferente(**data) for data in kwargs.get("oferentes_participantes", [])]
        
        documentos_data = kwargs.get("documentos_solicitados", [])
        for doc_data in documentos_data:
            if doc_data.get("categoria") == "Tecnica":
                doc_data["categoria"] = "Técnica"
        self.documentos_solicitados = [Documento(**doc) for doc in documentos_data]

        # ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼
        self.fallas_fase_a = kwargs.get("fallas_fase_a", [])
        # ▲▲▲ FIN DE LA LÍNEA ▲▲▲

        cronograma_cargado = kwargs.get('cronograma', {})
        self.cronograma = {}
        eventos_posibles = [
            "Presentacion de Ofertas", "Apertura de Ofertas", "Informe de Evaluacion Tecnica",
            "Notificaciones de Subsanables", "Notificacion de Habilitacion Sobre B",
            "Apertura de Oferta Economica", "Adjudicacion"
        ]
        for evento in eventos_posibles:
            datos_evento = cronograma_cargado.get(evento)
            if isinstance(datos_evento, dict):
                self.cronograma[evento] = datos_evento
            elif isinstance(datos_evento, str):
                self.cronograma[evento] = {"fecha_limite": datos_evento, "estado": "Pendiente"}
            else:
                self.cronograma[evento] = {"fecha_limite": None, "estado": "Pendiente"}
    
    def to_dict(self):
        return {
            "id": self.id,
            "nombre_proceso": self.nombre_proceso,
            "numero_proceso": self.numero_proceso,
            "institucion": self.institucion,
            "empresas_nuestras": [e.to_dict() for e in self.empresas_nuestras],
            "estado": self.estado,
            "fase_A_superada": self.fase_A_superada,
            "fase_B_superada": self.fase_B_superada,
            "adjudicada": self.adjudicada,
            "adjudicada_a": self.adjudicada_a,
            "motivo_descalificacion": self.motivo_descalificacion,
            "docs_completos_manual": self.docs_completos_manual,
            "last_modified": self.last_modified,
            "fecha_creacion": str(self.fecha_creacion),
            "lotes": [l.to_dict() for l in self.lotes],
            "oferentes_participantes": [o.to_dict() for o in self.oferentes_participantes],
            "documentos_solicitados": [d.to_dict() for d in self.documentos_solicitados],
            "cronograma": self.cronograma,
            "riesgos": [r.to_dict() for r in self.riesgos],
            # ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼
            "fallas_fase_a": self.fallas_fase_a
            # ▲▲▲ FIN DE LA LÍNEA ▲▲▲
        }

    def get_monto_base_personal_total(self):
        """Calcula la suma de los montos base personales de los lotes en los que participamos."""
        return sum(lote.monto_base_personal for lote in self.lotes if lote.participamos)

    def get_diferencia_bases_porcentual(self):
        """
        Calcula la diferencia porcentual entre el presupuesto base personal total
        y el presupuesto base de la licitación total.
        Un resultado negativo significa que tu presupuesto es menor que el de la licitación.
        """
        monto_base_licitacion = self.get_monto_base_total()
        monto_base_personal = self.get_monto_base_personal_total()

        if monto_base_licitacion > 0:
            return ((monto_base_personal - monto_base_licitacion) / monto_base_licitacion) * 100
        return 0.0


    def to_summary_dict(self):
        """Devuelve un diccionario con un resumen de la licitación, para el log."""
        return {
            "numero_proceso": self.numero_proceso,
            "nombre_proceso": self.nombre_proceso,
            "institucion": self.institucion,
            "empresa_nuestra": str(", ".join(str(e) for e in self.empresas_nuestras)
),
            "estado": self.estado,
            "monto_ofertado_total": self.get_oferta_total(),
            "cantidad_lotes": len(self.lotes),
            "cantidad_documentos": len(self.documentos_solicitados)
        }

    def get_matriz_ofertas(self):
        """
        Crea una matriz (diccionario) con todas las ofertas válidas (Fase A superada)
        organizadas por Lote y luego por Oferente.
        
        Devuelve: {lote_numero: {oferente_nombre: {'monto': X, 'plazo': Y}, ...}, ...}
        """
        matriz = {str(lote.numero): {} for lote in self.lotes}
        
        for oferente in self.oferentes_participantes:
            for oferta in oferente.ofertas_por_lote:
                # Solo consideramos ofertas que pasaron la Fase A
                if oferta.get('paso_fase_A', False):
                    lote_num_str = str(oferta.get('lote_numero'))
                    if lote_num_str in matriz:
                        matriz[lote_num_str][oferente.nombre] = {
                            'monto': oferta.get('monto', 0),
                            'plazo': oferta.get('plazo_entrega', 0)
                        }
        return matriz
    def get_riesgo_total_score(self):
        """Calcula la puntuación total de riesgo sumando (impacto * probabilidad) de cada riesgo."""
        if not self.riesgos:
            return 0
        return sum(r.impacto * r.probabilidad for r in self.riesgos)

    def calcular_mejor_paquete_individual(self):
        """
        Calcula el costo total si se adjudicara cada lote al oferente más barato
        para ese lote en específico.

        Devuelve: {'monto_total': X, 'detalle': {lote_numero: oferente_nombre, ...}}
        """
        matriz = self.get_matriz_ofertas()
        monto_total = 0.0
        detalle_adjudicacion = {}

        for lote_num, ofertas_lote in matriz.items():
            if not ofertas_lote:  # Si no hay ofertas para este lote, se ignora
                continue

            # Encontrar el oferente con el monto más bajo para este lote
            mejor_oferente = min(ofertas_lote, key=lambda oferente: ofertas_lote[oferente]['monto'])
            monto_minimo = ofertas_lote[mejor_oferente]['monto']
            
            monto_total += monto_minimo
            detalle_adjudicacion[lote_num] = mejor_oferente
            
        return {'monto_total': monto_total, 'detalle': detalle_adjudicacion}

    def calcular_mejor_paquete_por_oferente(self):
        """
        Calcula el costo total por cada oferente que participa en todos los lotes
        requeridos y devuelve el mejor paquete de un único oferente.

        Devuelve: {'monto_total': X, 'oferente': oferente_nombre} o None si nadie ofertó a todo.
        """
        paquetes_completos = {}
        # Obtenemos solo los lotes en los que nosotros participamos
        lotes_participantes = {str(l.numero) for l in self.lotes if l.participamos}
        
        if not lotes_participantes:
            return None

        for oferente in self.oferentes_participantes:
            ofertas_validas = [o for o in oferente.ofertas_por_lote if o.get('paso_fase_A', False)]
            lotes_ofertados_por_competidor = {str(o['lote_numero']) for o in ofertas_validas}

            # Verificamos si el oferente ha ofertado en TODOS los lotes en los que participamos
            if lotes_participantes.issubset(lotes_ofertados_por_competidor):
                # Sumamos solo los montos de los lotes relevantes
                monto_paquete = sum(o['monto'] for o in ofertas_validas if str(o['lote_numero']) in lotes_participantes)
                paquetes_completos[oferente.nombre] = monto_paquete
        
        if not paquetes_completos:
            return None # Ningún oferente ofertó a todos los lotes necesarios

        mejor_oferente = min(paquetes_completos, key=paquetes_completos.get)
        monto_mas_bajo = paquetes_completos[mejor_oferente]

        return {'monto_total': monto_mas_bajo, 'oferente': mejor_oferente}


    def get_monto_base_total(self, solo_participados: bool = False) -> float:
        """
        Suma de montos base. Prioriza el presupuesto personal si es > 0.
        - si solo_participados=True: solo lotes elegibles.
        """
        total = 0.0
        lotes_a_evaluar = self._lotes_elegibles_para_porcentaje() if solo_participados else getattr(self, "lotes", [])
        
        for lote in lotes_a_evaluar:
            # Prioridad 1: Monto Base Personal, pero solo si es un valor positivo.
            base = float(getattr(lote, "monto_base_personal", 0.0) or 0.0)
            
            # Prioridad 2: Si el personal es 0, usar el Monto Base de la licitación.
            if base <= 0:
                base = float(getattr(lote, "monto_base", 0.0) or 0.0)
            
            total += base
        return total    

    def get_oferta_total(self, solo_participados: bool = False) -> float:
        """
        Suma de ofertas.
        - si solo_participados=True: solo lotes elegibles (participamos o con oferta > 0)
        """
        total = 0.0
        lotes = self._lotes_elegibles_para_porcentaje() if solo_participados else getattr(self, "lotes", [])
        for lote in lotes:
            total += float(getattr(lote, "monto_ofertado", 0) or 0.0)
        return total


    def get_diferencia_porcentual(self, solo_participados=False, usar_base_personal=True):
        """
        Calcula la diferencia porcentual entre la oferta y el monto base.
        - solo_participados: Si es True, solo considera lotes en los que participamos o que tienen oferta.
        - usar_base_personal: Si es True, prioriza el monto base personal. Si es False, usa solo el de la licitación.
        """
        lotes_a_considerar = self.lotes
        if solo_participados:
            lotes_a_considerar = [
                l for l in self.lotes
                if bool(getattr(l, 'participamos', False)) or (float(getattr(l, 'monto_ofertado', 0) or 0) > 0)
            ]

        base_total = 0.0
        oferta_total = 0.0

        for lote in lotes_a_considerar:
            oferta = float(getattr(lote, 'monto_ofertado', 0) or 0)
            
            # --- LÓGICA MODIFICADA ---
            if usar_base_personal:
                base = float(getattr(lote, 'monto_base_personal', 0.0) or 0.0)
                if base <= 0:
                    base = float(getattr(lote, 'monto_base', 0.0) or 0.0)
            else:
                base = float(getattr(lote, 'monto_base', 0.0) or 0.0)
            
            base_total += base
            
            # --- CORRECCIÓN CLAVE ---
            # Si el lote está en la lista de 'lotes_a_considerar',
            # su oferta siempre debe ser sumada, sin doble verificación.
            oferta_total += oferta
            # --- FIN DE LA CORRECCIÓN ---

        if base_total == 0:
            return 0.0

        return ((oferta_total - base_total) / base_total) * 100.0

    
    def get_porcentaje_completado(self):
        total_docs = len(self.documentos_solicitados)
        if total_docs == 0:
            return 100.0 if self.docs_completos_manual else 0.0
        docs_completados = sum(1 for doc in self.documentos_solicitados if doc.presentado)
        return (docs_completados / total_docs) * 100
    
    def _lotes_elegibles_para_porcentaje(self):
        """Lotes que cuentan para %Dif: participamos o ya tienen oferta (>0)."""
        elegibles = []
        for lote in getattr(self, "lotes", []):
            participa = bool(getattr(lote, "participamos", False))
            oferta = float(getattr(lote, "monto_ofertado", 0) or 0.0)
            if participa or oferta > 0:
                elegibles.append(lote)
        return elegibles

# En la clase Licitacion, reemplaza este método:
    def get_dias_restantes(self):
        hoy = datetime.date.today()
        eventos_futuros_pendientes = []
        
        # Define un orden de prioridad para los eventos
        hitos_prioridad = [
            "Presentacion de Ofertas", "Apertura de Ofertas", "Informe de Evaluacion Tecnica",
            "Notificaciones de Subsanables", "Notificacion de Habilitacion Sobre B",
            "Apertura de Oferta Economica", "Adjudicacion"
        ]

        for nombre_evento in hitos_prioridad:
            datos_evento = self.cronograma.get(nombre_evento)
            if datos_evento and datos_evento.get("estado") == "Pendiente" and datos_evento.get("fecha_limite"):
                try:
                    fecha_limite = datetime.datetime.strptime(datos_evento["fecha_limite"], '%Y-%m-%d').date()
                    if fecha_limite >= hoy:
                        # Al encontrar el primer evento futuro y pendiente según la prioridad, lo usamos y salimos del bucle.
                        eventos_futuros_pendientes.append((fecha_limite, nombre_evento))
                        break
                except (ValueError, TypeError):
                    continue

        if eventos_futuros_pendientes:
            proxima_fecha, proximo_evento = eventos_futuros_pendientes[0]
            diferencia = (proxima_fecha - hoy).days
            
            # --- LÓGICA CORREGIDA ---
            # Ahora, todos los casos incluyen el nombre del evento.
            if diferencia == 0:
                return f"Hoy: {proximo_evento}"
            elif diferencia == 1:
                return f"Mañana: {proximo_evento}"
            else:
                return f"Faltan {diferencia} días para: {proximo_evento}"
        
        # El resto de la lógica para estados finalizados permanece igual.
        if self.estado == "Adjudicada (Ganada)": return "✅ Adjudicada"
        if self.estado in ["Adjudicada (Perdida)", "Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]: return "❌ Finalizada"
        
        return "Fases cumplidas"
    
    def clone(self):
        return Licitacion(**self.to_dict())
