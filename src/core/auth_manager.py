from src.db.database import get_supabase

class AuthManager:
    _current_user = None
    _user_role = None

    @classmethod
    def login(cls, identificador: str, password: str) -> tuple[bool, str]:
        supabase = get_supabase()
        try:
            email = identificador
            if "@" not in identificador:
                # Buscar el email asociado al nombre de usuario
                res = supabase.table('usuarios').select('email').eq('username', identificador).execute()
                if res.data and len(res.data) > 0:
                    email = res.data[0]['email']
                else:
                    return False, f"No existe ningún usuario registrado como '{identificador}'."
            
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
            return True, ""
        except Exception as e:
            msg = str(e)
            if "Invalid login credentials" in msg or "invalid_credentials" in msg:
                err = "El correo/usuario o la contraseña son incorrectos."
            elif "Failed to establish a new connection" in msg or "Max retries exceeded" in msg or "getaddrinfo failed" in msg or "Connection" in msg:
                err = "No se pudo conectar a Internet o al servidor de la base de datos."
            elif "Email not confirmed" in msg:
                err = "El correo no ha sido confirmado aún en el sistema."
            else:
                # Si el mensaje es una estructura JSON de Supabase, extraer el campo 'msg' o 'message'
                try:
                    import json
                    if "{" in msg:
                        json_str = msg[msg.find("{"):msg.rfind("}")+1]
                        data = json.loads(json_str)
                        err = data.get('msg') or data.get('message') or data.get('error_description') or msg
                    else:
                        err = msg
                except Exception:
                    err = "Error de inicio de sesión. Verifique los datos o la conexión."
            return False, err

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
