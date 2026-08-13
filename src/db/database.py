import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Variable global para mantener el cliente conectado
_supabase_client: Client = None

def get_supabase() -> Client:
    """Retorna la instancia del cliente de Supabase (Singleton)"""
    global _supabase_client
    if _supabase_client is None:
        load_dotenv(override=True)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Faltan credenciales de Supabase en el archivo .env")
        _supabase_client = create_client(url, key)
    return _supabase_client


