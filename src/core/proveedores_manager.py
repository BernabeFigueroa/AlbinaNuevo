from src.db.database import get_supabase

class ProveedoresManager:
    @staticmethod
    def get_all(incluir_inactivos=False):
        supabase = get_supabase()
        query = supabase.table('proveedores').select('*')
        if not incluir_inactivos:
            query = query.eq('activo', True)
        res = query.execute()
        return res.data



    @staticmethod
    def get_by_id(prov_id: int):
        supabase = get_supabase()
        res = supabase.table('proveedores').select('*').eq('id', prov_id).execute()
        return res.data[0] if res.data else None

    @staticmethod
    def crear(nombre, telefono, direccion):
        supabase = get_supabase()
        data = {'nombre': nombre, 'telefono': telefono, 'direccion': direccion, 'activo': True}
        res = supabase.table('proveedores').insert(data).execute()
        return res.data[0]['id']

    @staticmethod
    def actualizar(prov_id, nombre, telefono, direccion):
        supabase = get_supabase()
        data = {'nombre': nombre, 'telefono': telefono, 'direccion': direccion}
        supabase.table('proveedores').update(data).eq('id', prov_id).execute()
        return True

    @staticmethod
    def eliminar(prov_id):
        supabase = get_supabase()
        supabase.table('proveedores').update({'activo': False}).eq('id', prov_id).execute()
        return True

    @staticmethod
    def restaurar(prov_id):
        supabase = get_supabase()
        supabase.table('proveedores').update({'activo': True}).eq('id', prov_id).execute()
        return True

    # Aliases de compatibilidad con UI
    crear_proveedor = crear
    actualizar_proveedor = actualizar
    eliminar_proveedor = eliminar

