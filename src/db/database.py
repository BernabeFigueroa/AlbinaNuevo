import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Variable global para mantener el cliente conectado
_supabase_client: Client = None

# Credenciales predeterminadas del proyecto Albina San Martin
DEFAULT_SUPABASE_URL = "https://bvreeibnkivucjqzhgjo.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2cmVlaWJua2l2dWNqcXpoZ2pvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyNDUwMDcsImV4cCI6MjA5OTgyMTAwN30.kHDlhqm3qEyemDzLcOLs4s1szuFn9Yvl4CsrQZm_t4U"

def get_supabase() -> Client:
    """Retorna la instancia del cliente de Supabase (Singleton)"""
    global _supabase_client
    if _supabase_client is None:
        import sys
        # Cargar variables si existe archivo .env local
        if getattr(sys, 'frozen', False):
            exe_env = os.path.join(os.path.dirname(sys.executable), '.env')
            if os.path.exists(exe_env):
                load_dotenv(exe_env, override=True)
        else:
            load_dotenv(override=True)
            
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        # Validar que no sea un placeholder inválido
        if not url or not url.startswith("http") or "tu_url_aqui" in url:
            url = DEFAULT_SUPABASE_URL
            
        if not key or len(key) < 20 or "tu_api_key_aqui" in key:
            key = DEFAULT_SUPABASE_KEY
            
        _supabase_client = create_client(url, key)
    return _supabase_client


