import os
import sys
import json
from src.db.database import get_supabase

DEFAULT_RECARGO_TARJETA = 35.0

class ConfiguracionManager:
    _cached_recargo = None

    @staticmethod
    def _get_local_config_path():
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, "config_app.json")

    @classmethod
    def get_recargo_tarjeta(cls, force_reload=False) -> float:
        """Obtiene el porcentaje de recargo para tarjeta/lista."""
        if cls._cached_recargo is not None and not force_reload:
            return cls._cached_recargo

        # 1. Intentar consultar en Supabase (si existe la tabla 'configuracion')
        try:
            supabase = get_supabase()
            res = supabase.table('configuracion').select('valor').eq('clave', 'recargo_tarjeta').execute()
            if res.data and len(res.data) > 0:
                val = float(res.data[0]['valor'])
                cls._cached_recargo = val
                return val
        except Exception:
            pass

        # 2. Fallback a archivo JSON persistente local
        try:
            cfg_path = cls._get_local_config_path()
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    val = float(data.get('recargo_tarjeta', DEFAULT_RECARGO_TARJETA))
                    cls._cached_recargo = val
                    return val
        except Exception:
            pass

        cls._cached_recargo = DEFAULT_RECARGO_TARJETA
        return DEFAULT_RECARGO_TARJETA

    @classmethod
    def set_recargo_tarjeta(cls, nuevo_porcentaje: float) -> bool:
        """Guarda el porcentaje de recargo en Supabase y/o archivo local."""
        val = float(nuevo_porcentaje)
        cls._cached_recargo = val

        # 1. Guardar en archivo local
        try:
            cfg_path = cls._get_local_config_path()
            data = {}
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data['recargo_tarjeta'] = val
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando config local: {e}")

        # 2. Intentar guardar en Supabase si la tabla existe
        try:
            supabase = get_supabase()
            # Upsert en Supabase
            supabase.table('configuracion').upsert({
                'clave': 'recargo_tarjeta',
                'valor': str(val)
            }).execute()
        except Exception:
            pass

        return True
