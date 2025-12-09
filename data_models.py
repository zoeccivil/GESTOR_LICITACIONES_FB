# Contenido de tu nuevo archivo: data_models.py

import datetime
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# --- Función de ayuda (si la mueves aquí) ---
def _as_dict(value, default=None):
    """
    Devuelve un dict a partir de:
    - dict -> igual
    - str  -> intenta json.loads, si falla -> {}
    - None/otros -> {}
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {} if default is None else default
        try:
            return json.loads(s)
        except Exception:
            return {} if default is None else default
    return {} if default is None else default
    
# --- Definiciones de tus clases ---

@dataclass
class Lote:
    # ... (código de la clase Lote) ...

@dataclass
class Oferente:
    # ... (código de la clase Oferente) ...
    
# ... y así con Documento, Empresa y Licitacion ...