from src.db.database import get_supabase
from src.core.auth_manager import AuthManager
from datetime import datetime

class CajaManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.get_current_user():
            raise PermissionError("Acceso Denegado: Debe iniciar sesión para administrar la caja.")

    @staticmethod
    def obtener_sesion_activa():
        supabase = get_supabase()
        try:
            res = supabase.table('cash_register_sessions').select('*').eq('status', 'OPEN').execute()
            if res.data:
                # Mantener compatibilidad con mapeo antiguo
                sesion = res.data[0].copy()
                sesion['monto_inicial'] = float(sesion.get('opening_amount', 0.0))
                sesion['estado'] = 'ABIERTA' if sesion.get('status') == 'OPEN' else 'CERRADA'
                return sesion
            return None
        except Exception:
            return None

    @staticmethod
    def abrir_caja(monto_inicial: float):
        CajaManager._check_permission()
        if CajaManager.obtener_sesion_activa():
            raise Exception("Ya existe una caja abierta.")
            
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        data = {
            'opening_amount': monto_inicial,
            'status': 'OPEN',
            'opened_by': usuario_id
        }
        res = supabase.table('cash_register_sessions').insert(data).execute()
        caja_id = res.data[0]['id']
        
        # Registrar movimiento inicial en cash_movements
        mov_data = {
            'session_id': caja_id,
            'type': 'IN',
            'amount': monto_inicial,
            'method': 'CASH',
            'reason': 'ADJUSTMENT',
            'note': 'Apertura de Caja',
            'created_by': usuario_id
        }
        supabase.table('cash_movements').insert(mov_data).execute()
        return caja_id

    @staticmethod
    def cerrar_caja(monto_cierre: float):
        CajaManager._check_permission()
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            raise Exception("No hay ninguna caja abierta.")
            
        supabase = get_supabase()
        data = {
            'closing_amount': monto_cierre,
            'status': 'CLOSED',
            'closed_at': datetime.now().isoformat(),
            'closed_by': AuthManager.get_current_user().id if AuthManager.get_current_user() else None
        }
        supabase.table('cash_register_sessions').update(data).eq('id', sesion['id']).execute()
        return True

    @staticmethod
    def registrar_movimiento(caja_sesion_id_or_tipo, tipo_or_monto, monto_or_metodo=None, metodo_pago_or_desc=None, descripcion=None):
        if descripcion is not None:
            caja_sesion_id = caja_sesion_id_or_tipo
            tipo = tipo_or_monto
            monto = monto_or_metodo
            metodo_pago = metodo_pago_or_desc
        else:
            sesion = CajaManager.obtener_sesion_activa()
            if not sesion:
                raise Exception("Debe abrir la caja primero.")
            caja_sesion_id = sesion['id']
            tipo = caja_sesion_id_or_tipo
            monto = tipo_or_monto
            metodo_pago = monto_or_metodo
            descripcion = metodo_pago_or_desc

        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        # Mapeo de método de pago
        metodos_pago_map = {
            'EFECTIVO': 'CASH',
            'TARJETA': 'CARD',
            'TRANSFERENCIA': 'TRANSFER'
        }
        db_method = metodos_pago_map.get(metodo_pago, 'CASH')

        supabase = get_supabase()
        data = {
            'session_id': caja_sesion_id,
            'type': 'IN' if tipo.upper() == 'INGRESO' else 'OUT',
            'amount': monto,
            'method': db_method,
            'reason': 'OTHER',
            'note': descripcion or '',
            'created_by': usuario_id
        }
        supabase.table('cash_movements').insert(data).execute()
        return True

    @staticmethod
    def obtener_resumen(caja_sesion_id: int):
        supabase = get_supabase()
        
        resumen = {
            'monto_inicial': 0.0,
            'ventas_efectivo': 0.0,
            'ventas_transferencia': 0.0,
            'ventas_fiadas': 0.0,
            'ventas_otros': 0.0,
            'ingresos_manuales': 0.0,
            'egresos_manuales': 0.0,
            'pagos_deuda_efectivo': 0.0,
            'pagos_deuda_transferencia': 0.0,
            'total_efectivo_esperado': 0.0,
            'total_vendido': 0.0
        }
        
        # 1. Obtener monto inicial
        sesion_res = supabase.table('cash_register_sessions').select('opening_amount').eq('id', caja_sesion_id).execute()
        if sesion_res.data:
            resumen['monto_inicial'] = float(sesion_res.data[0]['opening_amount'] or 0)
            
        # 2. Obtener ventas locales de la sesión en sales
        try:
            ventas_res = supabase.table('sales').select('id, payment_method, total').neq('status', 'CANCELLED').execute()
            for v in ventas_res.data:
                total_v = float(v['total'] or 0)
                mp = v['payment_method']
                if mp == 'CASH':
                    resumen['ventas_efectivo'] += total_v
                elif mp in ['TRANSFER', 'CARD']:
                    resumen['ventas_transferencia'] += total_v
                else:
                    resumen['ventas_otros'] += total_v
        except Exception:
            pass
                
        resumen['total_vendido'] = resumen['ventas_efectivo'] + resumen['ventas_transferencia'] + resumen['ventas_fiadas'] + resumen['ventas_otros']
                
        # 3. Obtener movimientos de caja
        try:
            movs_res = supabase.table('cash_movements').select('type, method, amount, note').eq('session_id', caja_sesion_id).execute()
            for m in movs_res.data:
                monto_m = float(m['amount'] or 0)
                tipo = m['type']
                mp = m['method']
                desc = m['note'] or ''
                
                if desc == 'Apertura de Caja':
                    continue
                    
                if tipo == 'IN' and mp == 'CASH':
                    resumen['ingresos_manuales'] += monto_m
                elif tipo == 'OUT' and mp == 'CASH':
                    resumen['egresos_manuales'] += monto_m
        except Exception:
            pass
                    
        # 4. Calcular total efectivo esperado
        resumen['total_efectivo_esperado'] = (
            resumen['monto_inicial'] + 
            resumen['ventas_efectivo'] + 
            resumen['ingresos_manuales'] - 
            resumen['egresos_manuales']
        )
        
        return resumen

    @staticmethod
    def obtener_movimientos(caja_sesion_id: int):
        supabase = get_supabase()
        try:
            res = supabase.table('cash_movements').select('*').eq('session_id', caja_sesion_id).execute()
            # Mapear para compatibilidad con UI
            lista = []
            for item in res.data:
                mov = item.copy()
                mov['tipo'] = 'INGRESO' if item.get('type') == 'IN' else 'EGRESO'
                mov['monto'] = item.get('amount')
                mov['descripcion'] = item.get('note')
                mov['metodo_pago'] = 'EFECTIVO' if item.get('method') == 'CASH' else 'TRANSFERENCIA'
                lista.append(mov)
            return lista
        except Exception:
            return []

