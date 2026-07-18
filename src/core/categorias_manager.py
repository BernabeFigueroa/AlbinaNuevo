from src.db.database import get_supabase

class CategoriasManager:
    @staticmethod
    def get_all():
        supabase = get_supabase()
        res = supabase.table('categorias').select('*').execute()
        return res.data

    @staticmethod
    def crear(nombre: str):
        supabase = get_supabase()
        res = supabase.table('categorias').insert({'nombre': nombre}).execute()
        return res.data[0]['id']

    @staticmethod
    def actualizar(cat_id: int, nombre: str):
        supabase = get_supabase()
        supabase.table('categorias').update({'nombre': nombre}).eq('id', cat_id).execute()
        return True

    @staticmethod
    def eliminar(cat_id: int):
        # NOTA: Supabase manejará las FK constraints si hay productos asociados.
        supabase = get_supabase()
        supabase.table('categorias').delete().eq('id', cat_id).execute()
        return True
