from src.db.database import get_supabase

class AuthManager:
    _current_user = None
    _user_role = None

    @classmethod
    def login(cls, identificador: str, password: str) -> bool:
        supabase = get_supabase()
        try:
            email = identificador
            if "@" not in identificador:
                # Buscar el email asociado al nombre de usuario
                res = supabase.table('usuarios').select('email').eq('username', identificador).execute()
                if res.data:
                    email = res.data[0]['email']
                else:
                    return False
            
            # 1. Autenticar con Supabase Auth
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            cls._current_user = response.user
            
            # 2. Obtener el rol del usuario desde la tabla 'usuarios'
            if cls._current_user:
                res_rol = supabase.table('usuarios').select('rol').eq('id', cls._current_user.id).execute()
                if res_rol.data and len(res_rol.data) > 0:
                    cls._user_role = res_rol.data[0]['rol']
                else:
                    cls._user_role = 'empleada' # Fallback seguro
            return True
        except Exception as e:
            import traceback
            print(f"\n--- ERROR DETALLADO DE LOGIN ---")
            print(f"Excepción: {type(e).__name__}")
            print(f"Mensaje: {e}")
            print(f"--------------------------------\n")
            return False

    @classmethod
    def logout(cls):
        supabase = get_supabase()
        supabase.auth.sign_out()
        cls._current_user = None
        cls._user_role = None

    @classmethod
    def is_admin(cls) -> bool:
        return cls._user_role == 'admin'

    @classmethod
    def get_current_user(cls):
        return cls._current_user
