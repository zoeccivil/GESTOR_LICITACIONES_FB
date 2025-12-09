# models.py
import datetime
import json

class Lote:
    """Representa un lote individual dentro de una licitación."""
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
        return self.__dict__

class Oferente:
    """Representa a un competidor o participante en la licitación."""
    def __init__(self, **kwargs):
        self.nombre = kwargs.get("nombre", "")
        self.comentario = kwargs.get("comentario", "")
        self.ofertas_por_lote = kwargs.get("ofertas_por_lote", [])

    def to_dict(self):
        return self.__dict__

    def get_monto_total_ofertado(self, solo_habilitados=False):
        ofertas_a_sumar = self.ofertas_por_lote
        if solo_habilitados:
            ofertas_a_sumar = [o for o in self.ofertas_por_lote if o.get('paso_fase_A', True)]
        return sum(oferta.get('monto', 0) for oferta in ofertas_a_sumar)

class Documento:
    """Representa un documento solicitado en una licitación."""
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
    """Representa una de nuestras empresas."""
    def __init__(self, nombre):
        self.nombre = nombre
    def to_dict(self):
        return {"nombre": self.nombre}
    def __str__(self):
        return self.nombre

class Riesgo:
    """Representa un riesgo individual asociado a una licitación."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.licitacion_id = kwargs.get('licitacion_id', None)
        self.descripcion = kwargs.get('descripcion', '')
        self.categoria = kwargs.get('categoria', 'Técnico')
        self.impacto = kwargs.get('impacto', 1)
        self.probabilidad = kwargs.get('probabilidad', 1)
        self.mitigacion = kwargs.get('mitigacion', '')

    def to_dict(self):
        return self.__dict__

class Licitacion:
    """La clase principal que agrupa toda la información de una licitación."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.nombre_proceso = kwargs.get("nombre_proceso", "")
        self.numero_proceso = kwargs.get("numero_proceso", "")
        self.institucion = kwargs.get("institucion", "")
        empresas = kwargs.get("empresas_nuestras", [])
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
        self.documentos_solicitados = [Documento(**doc) for doc in kwargs.get("documentos_solicitados", [])]
        self.oferentes_participantes = [Oferente(**data) for data in kwargs.get("oferentes_participantes", [])]
        self.riesgos = [Riesgo(**r) for r in kwargs.get("riesgos", [])]
        self.fallas_fase_a = kwargs.get("fallas_fase_a", [])
        
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
            "fallas_fase_a": self.fallas_fase_a
        }
    
    # ... (El resto de los métodos de la clase Licitacion) ...
    def get_monto_base_total(self, solo_participados: bool = False) -> float:
        total = 0.0
        lotes_a_evaluar = [l for l in self.lotes if l.participamos] if solo_participados else self.lotes
        for lote in lotes_a_evaluar:
            base = lote.monto_base_personal if lote.monto_base_personal > 0 else lote.monto_base
            total += base
        return total

    def get_oferta_total(self, solo_participados: bool = False) -> float:
        lotes_a_evaluar = [l for l in self.lotes if l.participamos] if solo_participados else self.lotes
        return sum(lote.monto_ofertado for lote in lotes_a_evaluar)

    def get_diferencia_porcentual(self, solo_participados=False, usar_base_personal=True):
        base_total = self.get_monto_base_total(solo_participados=solo_participados)
        oferta_total = self.get_oferta_total(solo_participados=solo_participados)
        if base_total == 0:
            return 0.0
        return ((oferta_total - base_total) / base_total) * 100.0

    def get_porcentaje_completado(self):
        total_docs = len(self.documentos_solicitados)
        if total_docs == 0:
            return 100.0 if self.docs_completos_manual else 0.0
        docs_completados = sum(1 for doc in self.documentos_solicitados if doc.presentado)
        return (docs_completados / total_docs) * 100

    def get_dias_restantes(self):
        hoy = datetime.date.today()
        eventos_futuros_pendientes = []
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
                        eventos_futuros_pendientes.append((fecha_limite, nombre_evento))
                        break
                except (ValueError, TypeError):
                    continue
        if eventos_futuros_pendientes:
            proxima_fecha, proximo_evento = eventos_futuros_pendientes[0]
            diferencia = (proxima_fecha - hoy).days
            if diferencia == 0:
                return f"Hoy: {proximo_evento}"
            elif diferencia == 1:
                return f"Mañana: {proximo_evento}"
            else:
                return f"Faltan {diferencia} días para: {proximo_evento}"
        if self.estado == "Adjudicada":
             return "✅ Adjudicada"
        if self.estado in ["Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]:
             return "❌ Finalizada"
        return "Fases cumplidas"