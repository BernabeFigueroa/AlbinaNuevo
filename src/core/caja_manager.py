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
            res = supabase.table('caja_sesiones').select('*').eq('estado', 'ABIERTA').execute()
            if res.data:
                sesion = res.data[0].copy()
                # La UI de PyQt6 espera que la sesión activa devuelta tenga 'monto_inicial' y 'estado' ('ABIERTA' o 'CERRADA')
                sesion['monto_inicial'] = float(sesion.get('monto_inicial', 0.0))
                sesion['estado'] = 'ABIERTA'
                return sesion
            return None
        except Exception as e:
            print(f"Error en obtener_sesion_activa: {e}")
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
            'monto_inicial': monto_inicial,
            'estado': 'ABIERTA',
            'usuario_id': usuario_id
        }
        res = supabase.table('caja_sesiones').insert(data).execute()
        if not res.data:
            raise Exception("No se pudo crear la sesión de caja.")
        caja_id = res.data[0]['id']
        
        # Registrar movimiento inicial en caja_movimientos
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
        data = {
            'monto_cierre': monto_cierre,
            'estado': 'CERRADA',
            'fecha_cierre': datetime.now().isoformat()
        }
        supabase.table('caja_sesiones').update(data).eq('id', sesion['id']).execute()
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

        tipo_normalizado = 'INGRESO' if tipo.upper() in ['INGRESO', 'IN'] else 'EGRESO'

        metodos_pago_map = {
            'CASH': 'EFECTIVO',
            'EFECTIVO': 'EFECTIVO',
            'CARD': 'TARJETA',
            'TARJETA': 'TARJETA',
            'TRANSFER': 'TRANSFERENCIA',
            'TRANSFERENCIA': 'TRANSFERENCIA'
        }
        db_method = metodos_pago_map.get(metodo_pago.upper() if metodo_pago else '', 'EFECTIVO')

        supabase = get_supabase()
        data = {
            'caja_sesion_id': caja_sesion_id,
            'tipo': tipo_normalizado,
            'monto': monto,
            'metodo_pago': db_method,
            'descripcion': descripcion or '',
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
            
        # 2. Obtener ventas de la sesión
        try:
            ventas_res = supabase.table('ventas').select('id, metodo_pago, total').eq('caja_sesion_id', caja_sesion_id).neq('estado', 'CANCELADA').execute()
            for v in ventas_res.data:
                total_v = float(v['total'] or 0)
                mp = v['metodo_pago'].upper()
                if mp == 'EFECTIVO':
                    resumen['ventas_efectivo'] += total_v
                elif mp in ['TRANSFERENCIA', 'TARJETA']:
                    resumen['ventas_transferencia'] += total_v
                elif mp in ['CTA_CTE', 'CTA CTE', 'FIADO']:
                    resumen['ventas_fiadas'] += total_v
                else:
                    resumen['ventas_otros'] += total_v
        except Exception as e:
            print(f"Error en obtener_resumen ventas: {e}")
            pass
                
        # 3. Obtener movimientos de caja
        try:
            movs_res = supabase.table('caja_movimientos').select('tipo, metodo_pago, monto, descripcion').eq('caja_sesion_id', caja_sesion_id).execute()
            for m in movs_res.data:
                monto_m = float(m['monto'] or 0)
                tipo = m['tipo']
                mp = m['metodo_pago']
                desc = m['descripcion'] or ''
                
                if desc == 'Apertura de Caja':
                    continue
                    
                if tipo == 'INGRESO':
                    if "PAGO DE DEUDA" in desc.upper() or "PAGO DE CTAS CTES" in desc.upper() or "PAGO CTA CTE" in desc.upper():
                        if mp == 'EFECTIVO':
                            resumen['pagos_deuda_efectivo'] += monto_m
                        else:
                            resumen['pagos_deuda_transferencia'] += monto_m
                    else:
                        if mp == 'EFECTIVO':
                            resumen['ingresos_manuales'] += monto_m
                elif tipo == 'EGRESO':
                    if mp == 'EFECTIVO':
                        resumen['egresos_manuales'] += monto_m
        except Exception as e:
            print(f"Error en obtener_resumen movimientos: {e}")
            pass
            
        resumen['total_vendido'] = resumen['ventas_efectivo'] + resumen['ventas_transferencia'] + resumen['ventas_fiadas'] + resumen['ventas_otros']
                    
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
        try:
            res = supabase.table('caja_movimientos').select('*').eq('caja_sesion_id', caja_sesion_id).execute()
            lista = []
            for item in res.data:
                mov = item.copy()
                mov['tipo'] = item.get('tipo')
                mov['monto'] = float(item.get('monto') or 0.0)
                mov['descripcion'] = item.get('descripcion')
                mov['metodo_pago'] = item.get('metodo_pago')
                lista.append(mov)
            return lista
        except Exception as e:
            print(f"Error en obtener_movimientos: {e}")
            return []
