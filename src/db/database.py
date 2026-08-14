import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Variable global para mantener el cliente conectado
_supabase_client: Client = None

# Credenciales predeterminadas del proyecto Albina
DEFAULT_SUPABASE_URL = "https://lomupnnsjjqytdhsxfoa.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvbXVwbm5zampxeXRkaHN4Zm9hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyNTIzNzAsImV4cCI6MjA3NjgyODM3MH0.lzNoj8bgPAu6DpMQGmsX67bM8hgfdYHC48IEt5AYdU8"

def get_supabase() -> Client:
    """Retorna la instancia del cliente de Supabase (Singleton)"""
    global _supabase_client
    if _supabase_client is None:
        import sys
        if getattr(sys, 'frozen', False):
            env_path = os.path.join(sys._MEIPASS, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
            # También intentar cargar .env junto al ejecutable si existiera
            exe_env = os.path.join(os.path.dirname(sys.executable), '.env')
            if os.path.exists(exe_env):
                load_dotenv(exe_env, override=True)
        else:
            load_dotenv(override=True)
            
        url = os.getenv("SUPABASE_URL") or DEFAULT_SUPABASE_URL
        key = os.getenv("SUPABASE_KEY") or DEFAULT_SUPABASE_KEY
        
        if not url or not key:
            raise ValueError("Faltan credenciales de Supabase en la configuración.")
            
        _supabase_client = create_client(url, key)
    return _supabase_client


