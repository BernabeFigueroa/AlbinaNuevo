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
        res = supabase.table('caja_sesiones').select('*').eq('estado', 'ABIERTA').execute()
        return res.data[0] if res.data else None

    @staticmethod
    def abrir_caja(monto_inicial: float):
        CajaManager._check_permission()
        if CajaManager.obtener_sesion_activa():
            raise Exception("Ya existe una caja abierta.")
            
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        data = {
            'monto_inicial': monto_inicial,
            'estado': 'ABIERTA',
            'usuario_id': usuario_id
        }
        res = supabase.table('caja_sesiones').insert(data).execute()
        
        # Registrar movimiento inicial
        caja_id = res.data[0]['id']
        mov_data = {
            'caja_sesion_id': caja_id,
            'tipo': 'INGRESO',
            'monto': monto_inicial,
            'metodo_pago': 'EFECTIVO',
            'descripcion': 'Apertura de Caja',
            'usuario_id': usuario_id
        }
        supabase.table('caja_movimientos').insert(mov_data).execute()
        return caja_id

    @staticmethod
    def cerrar_caja(monto_cierre: float):
        CajaManager._check_permission()
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            raise Exception("No hay ninguna caja abierta.")
            
        supabase = get_supabase()
        data = {'monto_cierre': monto_cierre, 'estado': 'CERRADA', 'fecha_cierre': datetime.now().isoformat()}
        supabase.table('caja_sesiones').update(data).eq('id', sesion['id']).execute()
        return True

    @staticmethod
    def registrar_movimiento(caja_sesion_id_or_tipo, tipo_or_monto, monto_or_metodo=None, metodo_pago_or_desc=None, descripcion=None):
        if descripcion is not None:
            # Se llamó como (caja_sesion_id, tipo, monto, metodo_pago, descripcion)
            caja_sesion_id = caja_sesion_id_or_tipo
            tipo = tipo_or_monto
            monto = monto_or_metodo
            metodo_pago = metodo_pago_or_desc
        else:
            # Se llamó como (tipo, monto, metodo_pago, descripcion)
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

        supabase = get_supabase()
        data = {
            'caja_sesion_id': caja_sesion_id,
            'tipo': tipo.upper(),
            'monto': monto,
            'metodo_pago': metodo_pago,
            'descripcion': descripcion,
            'usuario_id': usuario_id
        }
        supabase.table('caja_movimientos').insert(data).execute()
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
        sesion_res = supabase.table('caja_sesiones').select('monto_inicial').eq('id', caja_sesion_id).execute()
        if sesion_res.data:
            resumen['monto_inicial'] = float(sesion_res.data[0]['monto_inicial'] or 0)
            
        # 2. Obtener ventas
        ventas_res = supabase.table('ventas').select('id, metodo_pago, total').eq('caja_sesion_id', caja_sesion_id).neq('estado', 'CANCELADA').execute()
        for v in ventas_res.data:
            total_v = float(v['total'] or 0)
            mp = v['metodo_pago']
            if mp == 'EFECTIVO':
                resumen['ventas_efectivo'] += total_v
            elif mp in ['TRANSFERENCIA', 'TARJETA', 'TARJETA/TRANSFERENCIA']:
                resumen['ventas_transferencia'] += total_v
            elif mp == 'FIADO / CTA. CTE.':
                resumen['ventas_fiadas'] += total_v
            elif mp == 'MIXTO':
                desc_mixto = f"Venta #{v['id']} (Mixto)"
                movs_res = supabase.table('caja_movimientos').select('metodo_pago, monto').eq('caja_sesion_id', caja_sesion_id).eq('descripcion', desc_mixto).execute()
                for m in movs_res.data:
                    monto_m = float(m['monto'] or 0)
                    if m['metodo_pago'] == 'EFECTIVO':
                        resumen['ventas_efectivo'] += monto_m
                    elif m['metodo_pago'] in ['TRANSFERENCIA', 'TARJETA/TRANSFERENCIA']:
                        resumen['ventas_transferencia'] += monto_m
                    else:
                        resumen['ventas_otros'] += monto_m
            else:
                resumen['ventas_otros'] += total_v
                
        resumen['total_vendido'] = resumen['ventas_efectivo'] + resumen['ventas_transferencia'] + resumen['ventas_fiadas'] + resumen['ventas_otros']
                
        # 3. Obtener movimientos
        movs_res = supabase.table('caja_movimientos').select('tipo, metodo_pago, monto, descripcion').eq('caja_sesion_id', caja_sesion_id).execute()
        for m in movs_res.data:
            monto_m = float(m['monto'] or 0)
            tipo = m['tipo'].upper()
            mp = m['metodo_pago']
            desc = m['descripcion'] or ''
            
            # Ignorar el movimiento de apertura de caja para ingresos manuales
            if desc == 'Apertura de Caja':
                continue
            # Ignorar desgloses de ventas mixtas
            if "Mixto" in desc:
                continue
                
            if tipo == 'INGRESO' and mp == 'EFECTIVO':
                resumen['ingresos_manuales'] += monto_m
            elif tipo == 'EGRESO' and mp == 'EFECTIVO':
                resumen['egresos_manuales'] += monto_m
            elif tipo == 'PAGO_CTA_CTE':
                if mp == 'EFECTIVO':
                    resumen['pagos_deuda_efectivo'] += monto_m
                elif mp in ['TRANSFERENCIA', 'TARJETA', 'TARJETA/TRANSFERENCIA']:
                    resumen['pagos_deuda_transferencia'] += monto_m
                    
        # 4. Calcular total efectivo esperado
        resumen['total_efectivo_esperado'] = (
            resumen['monto_inicial'] + 
            resumen['ventas_efectivo'] + 
            resumen['ingresos_manuales'] +
            resumen['pagos_deuda_efectivo'] - 
            resumen['egresos_manuales']
        )
        
        return resumen

    @staticmethod
    def obtener_movimientos(caja_sesion_id: int):
        supabase = get_supabase()
        res = supabase.table('caja_movimientos').select('*').eq('caja_sesion_id', caja_sesion_id).order('fecha', desc=True).execute()
        return res.data
