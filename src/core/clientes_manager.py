from src.db.database import get_supabase

class ClientesManager:
    @staticmethod
    def get_all():
        supabase = get_supabase()
        res = supabase.table('clientes').select('*').eq('activo', True).execute()
        return res.data

    @staticmethod
    def get_by_id(cliente_id: int):
        supabase = get_supabase()
        res = supabase.table('clientes').select('*').eq('id', cliente_id).execute()
        return res.data[0] if res.data else None



    @staticmethod
    def _invalidate_cache():
        try:
            from src.core.cache_manager import DataCache
            DataCache.invalidate_clientes()
        except Exception:
            pass

    @staticmethod
    def crear(nombre, cuit, domicilio, localidad, provincia, condicion_iva, telefono, condicion_pago, descuento_porcentaje=0.0):
        supabase = get_supabase()
        data = {
            'nombre': nombre, 'cuit': cuit, 'domicilio': domicilio, 'localidad': localidad,
            'provincia': provincia, 'condicion_iva': condicion_iva, 'telefono': telefono,
            'condicion_pago': condicion_pago, 'descuento_porcentaje': descuento_porcentaje, 'activo': True
        }
        res = supabase.table('clientes').insert(data).execute()
        ClientesManager._invalidate_cache()
        return res.data[0]['id']

    @staticmethod
    def actualizar(cliente_id, nombre, cuit, domicilio, localidad, provincia, condicion_iva, telefono, condicion_pago, descuento_porcentaje=0.0):
        supabase = get_supabase()
        data = {
            'nombre': nombre, 'cuit': cuit, 'domicilio': domicilio, 'localidad': localidad,
            'provincia': provincia, 'condicion_iva': condicion_iva, 'telefono': telefono,
            'condicion_pago': condicion_pago, 'descuento_porcentaje': descuento_porcentaje
        }
        supabase.table('clientes').update(data).eq('id', cliente_id).execute()
        ClientesManager._invalidate_cache()
        return True

    @staticmethod
    def eliminar(cliente_id):
        supabase = get_supabase()
        supabase.table('clientes').update({'activo': False}).eq('id', cliente_id).execute()
        ClientesManager._invalidate_cache()
        return True

    # Aliases de compatibilidad con UI
    crear_cliente = crear
    actualizar_cliente = actualizar
    eliminar_cliente = eliminar

