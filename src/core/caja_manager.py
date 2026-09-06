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
    def cerrar_caja(monto_declarado: float, monto_esperado: float = None, motivo: str = ""):
        CajaManager._check_permission()
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            raise Exception("No hay ninguna caja abierta.")
            
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else sesion.get('usuario_id')

        supabase = get_supabase()
        
        # 1. Si no vino monto_esperado, calcularlo
        if monto_esperado is None:
            resumen = CajaManager.obtener_resumen(sesion['id'])
            monto_esperado = resumen['total_efectivo_esperado']
            
        monto_declarado = float(monto_declarado)
        monto_esperado = float(monto_esperado)
        diferencia = round(monto_declarado - monto_esperado, 2)
        
        # 2. Registrar movimiento de ajuste si hubo faltante o sobrante
        if abs(diferencia) >= 0.01:
            if diferencia < 0:
                tipo_mov = 'EGRESO'
                desc_mov = f"Faltante al Cierre de Turno (-${abs(diferencia):,.2f})"
                if motivo:
                    desc_mov += f" - Motivo: {motivo.strip()}"
                monto_mov = abs(diferencia)
            else:
                tipo_mov = 'INGRESO'
                desc_mov = f"Sobrante al Cierre de Turno (+${abs(diferencia):,.2f})"
                if motivo:
                    desc_mov += f" - Motivo: {motivo.strip()}"
                monto_mov = abs(diferencia)
                
            mov_data = {
                'caja_sesion_id': sesion['id'],
                'tipo': tipo_mov,
                'monto': monto_mov,
                'metodo_pago': 'EFECTIVO',
                'descripcion': desc_mov,
                'usuario_id': usuario_id
            }
            supabase.table('caja_movimientos').insert(mov_data).execute()

        # 3. Actualizar la sesión de caja con el monto declarado y usuario
        data = {
            'monto_cierre': monto_declarado,
            'estado': 'CERRADA',
            'fecha_cierre': datetime.now().isoformat()
        }
        if usuario_id:
            data['usuario_id'] = usuario_id
            
        supabase.table('caja_sesiones').update(data).eq('id', sesion['id']).execute()
        return {
            'monto_declarado': monto_declarado,
            'monto_esperado': monto_esperado,
            'diferencia': diferencia
        }

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
            'monto_cierre': None,
            'diferencia': 0.0,
            'estado': 'ABIERTA',
            'usuario_nombre': 'Desconocido',
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
        
        # 1. Obtener datos de la sesión
        try:
            sesion_res = supabase.table('caja_sesiones').select('*, usuarios(nombre, username)').eq('id', caja_sesion_id).execute()
            if sesion_res.data:
                s_data = sesion_res.data[0]
                resumen['monto_inicial'] = float(s_data.get('monto_inicial') or 0)
                resumen['estado'] = s_data.get('estado', 'ABIERTA')
                if s_data.get('monto_cierre') is not None:
                    resumen['monto_cierre'] = float(s_data['monto_cierre'])
                if s_data.get('usuarios'):
                    resumen['usuario_nombre'] = s_data['usuarios'].get('nombre') or s_data['usuarios'].get('username') or 'Desconocido'
        except Exception as e:
            print(f"Error en obtener_resumen sesion: {e}")
            try:
                sesion_res = supabase.table('caja_sesiones').select('*').eq('id', caja_sesion_id).execute()
                if sesion_res.data:
                    s_data = sesion_res.data[0]
                    resumen['monto_inicial'] = float(s_data.get('monto_inicial') or 0)
                    resumen['estado'] = s_data.get('estado', 'ABIERTA')
                    if s_data.get('monto_cierre') is not None:
                        resumen['monto_cierre'] = float(s_data['monto_cierre'])
            except Exception:
                pass
            
        # 2. Obtener ventas de la sesión
        try:
            ventas_res = supabase.table('ventas').select('id, metodo_pago, total').eq('caja_sesion_id', caja_sesion_id).neq('estado', 'CANCELADA').execute()
            for v in ventas_res.data:
                total_v = float(v['total'] or 0)
                mp = v['metodo_pago'].upper()
                if any(term in mp for term in ['FIADO', 'CTA. CTE', 'CTA CTE', 'CTA_CTE']):
                    resumen['ventas_fiadas'] += total_v
                elif mp == 'MIXTO':
                    resumen['ventas_otros'] += total_v
                elif mp in ['TRANSFERENCIA', 'TARJETA']:
                    resumen['ventas_transferencia'] += total_v
                elif mp == 'EFECTIVO':
                    resumen['ventas_efectivo'] += total_v
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
                desc_upper = desc.upper()
                
                if desc == 'Apertura de Caja':
                    continue
                
                # No sumar faltantes o sobrantes de cierre a ingresos/egresos operativos
                if "FALTANTE AL CIERRE" in desc_upper or "SOBRANTE AL CIERRE" in desc_upper:
                    continue

                # Movimientos generados por cobros de ventas mixtas
                if tipo == 'VENTA' and "(MIXTO)" in desc_upper:
                    if mp == 'EFECTIVO':
                        resumen['ventas_efectivo'] += monto_m
                    elif mp == 'TRANSFERENCIA':
                        resumen['ventas_transferencia'] += monto_m
                    # Descontar de ventas_otros para que no duplique en total_vendido
                    resumen['ventas_otros'] = max(0.0, resumen['ventas_otros'] - monto_m)
                    continue

                if tipo == 'INGRESO':
                    if any(term in desc_upper for term in ["PAGO DE DEUDA", "COBRO DEUDA", "PAGO DE CTAS CTES", "PAGO CTA CTE", "COBRO CTA. CTE", "COBRO CTA CTE"]):
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
        
        if resumen['monto_cierre'] is not None:
            resumen['diferencia'] = round(resumen['monto_cierre'] - resumen['total_efectivo_esperado'], 2)
            
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
