from src.db.database import get_supabase
from src.core.caja_manager import CajaManager

class CtaCteManager:
    @staticmethod
    def get_saldo(cliente_id: int):
        supabase = get_supabase()
        res = supabase.table('cta_cte_movimientos').select('tipo, monto').eq('cliente_id', cliente_id).execute()
        
        saldo = 0.0
        for m in res.data:
            if m['tipo'] == 'DEUDA':
                saldo += float(m['monto'])
            elif m['tipo'] == 'PAGO':
                saldo -= float(m['monto'])
        return saldo

    @staticmethod
    def get_historial(cliente_id: int):
        supabase = get_supabase()
        res = supabase.table('cta_cte_movimientos').select('*, usuarios(nombre, username)').eq('cliente_id', cliente_id).order('fecha', desc=True).execute()
        return res.data

    @staticmethod
    def registrar_pago(cliente_id: int, monto: float, metodo_pago: str, detalle: str = "Pago Cta. Cte."):
        sesion_caja = CajaManager.obtener_sesion_activa()
        if not sesion_caja:
            raise Exception("Debe abrir la caja antes de registrar un pago.")
            
        from src.core.auth_manager import AuthManager
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        
        # 1. Registrar movimiento cta cte
        data = {
            'cliente_id': cliente_id,
            'caja_sesion_id': sesion_caja['id'],
            'tipo': 'PAGO',
            'monto': monto,
            'detalle': detalle,
            'usuario_id': usuario_id
        }
        supabase.table('cta_cte_movimientos').insert(data).execute()
        
        # 2. Ingresar plata a la caja
        mov_caja = {
            'caja_sesion_id': sesion_caja['id'],
            'tipo': 'INGRESO',
            'monto': monto,
            'metodo_pago': metodo_pago,
            'descripcion': f"Cobro Cta. Cte. Cliente #{cliente_id}",
            'usuario_id': usuario_id
        }
        supabase.table('caja_movimientos').insert(mov_caja).execute()
        
        return True
