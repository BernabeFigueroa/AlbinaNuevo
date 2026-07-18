from src.db.database import get_supabase
from src.core.caja_manager import CajaManager

class CtaCteProveedoresManager:
    @staticmethod
    def get_saldo(proveedor_id: int):
        supabase = get_supabase()
        res = supabase.table('cta_cte_proveedores_movimientos').select('tipo, monto').eq('proveedor_id', proveedor_id).execute()
        
        saldo = 0.0
        for m in res.data:
            if m['tipo'] == 'DEUDA':
                saldo += float(m['monto'])
            elif m['tipo'] == 'PAGO':
                saldo -= float(m['monto'])
        return saldo

    @staticmethod
    def get_historial(proveedor_id: int):
        supabase = get_supabase()
        res = supabase.table('cta_cte_proveedores_movimientos').select('*').eq('proveedor_id', proveedor_id).order('fecha', desc=True).execute()
        return res.data

    @staticmethod
    def registrar_deuda(proveedor_id: int, monto: float, detalle: str = "Ingreso de Mercadería"):
        supabase = get_supabase()
        data = {
            'proveedor_id': proveedor_id,
            'tipo': 'DEUDA',
            'monto': monto,
            'detalle': detalle
        }
        supabase.table('cta_cte_proveedores_movimientos').insert(data).execute()
        return True

    @staticmethod
    def registrar_pago(proveedor_id: int, monto: float, metodo_pago: str, detalle: str = "Pago a Proveedor"):
        sesion_caja = CajaManager.obtener_sesion_activa()
        if not sesion_caja:
            raise Exception("Debe abrir la caja antes de registrar un pago que sale de la caja.")
            
        supabase = get_supabase()
        
        data = {
            'proveedor_id': proveedor_id,
            'caja_sesion_id': sesion_caja['id'],
            'tipo': 'PAGO',
            'monto': monto,
            'detalle': detalle
        }
        supabase.table('cta_cte_proveedores_movimientos').insert(data).execute()
        
        mov_caja = {
            'caja_sesion_id': sesion_caja['id'],
            'tipo': 'EGRESO',
            'monto': monto,
            'metodo_pago': metodo_pago,
            'descripcion': f"Pago a Proveedor #{proveedor_id}"
        }
        supabase.table('caja_movimientos').insert(mov_caja).execute()
        
        return True
