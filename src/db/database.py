import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Variable global para mantener el cliente conectado
_supabase_client: Client = None

def get_supabase() -> Client:
    """Retorna la instancia del cliente de Supabase (Singleton)"""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Faltan credenciales de Supabase en el archivo .env")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client
