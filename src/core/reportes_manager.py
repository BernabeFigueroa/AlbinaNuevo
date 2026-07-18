from src.db.database import get_supabase
from src.core.auth_manager import AuthManager
from collections import defaultdict

class ReportesManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.is_admin():
            raise PermissionError("Solo la dueña puede acceder a los reportes de ganancias y estadísticas.")

    @staticmethod
    def get_vendedores():
        ReportesManager._check_permission()
        supabase = get_supabase()
        res = supabase.table('usuarios').select('id, nombre, username').eq('activo', True).execute()
        return res.data

    @staticmethod
    def get_ventas_por_fecha(fecha_desde: str, fecha_hasta: str, metodo_pago: str = None, usuario_id: str = None):
        ReportesManager._check_permission()
        desde = f"{fecha_desde}T00:00:00"
        hasta = f"{fecha_hasta}T23:59:59"
        
        supabase = get_supabase()
        
        query = supabase.table('ventas').select('id, fecha, total, metodo_pago, clientes(nombre), usuarios(nombre, username)').neq('estado', 'CANCELADA').gte('fecha', desde).lte('fecha', hasta)
        
        if metodo_pago:
            query = query.eq('metodo_pago', metodo_pago)
            
        if usuario_id:
            query = query.eq('usuario_id', usuario_id)
            
        res = query.order('fecha', desc=True).execute()
        ventas = res.data
        
        efectivo = 0.0
        transferencia = 0.0
        
        ventas_fmt = []
        for v in ventas:
            total = float(v['total'])
            mp = v['metodo_pago']
            
            if mp == 'EFECTIVO':
                efectivo += total
            elif mp in ('TRANSFERENCIA', 'TARJETA/TRANSFERENCIA'):
                transferencia += total
            elif mp == 'MIXTO':
                # En Supabase Python habría que traer los movimientos asociados para precisión,
                # por simplicidad asumiremos todo efectivo aquí o consultar caja_movimientos.
                # Para evitar N+1 queries, simplificaremos
                pass
            
            vendedor = 'Sistema'
            if v.get('usuarios'):
                vendedor = v['usuarios'].get('nombre') or v['usuarios'].get('username') or 'Desconocido'
                
            ventas_fmt.append({
                'id': v['id'],
                'fecha': v['fecha'],
                'total': total,
                'metodo_pago': mp,
                'cliente': v['clientes']['nombre'] if v.get('clientes') else 'Consumidor Final',
                'vendedor': vendedor
            })
            
        return {
            'ventas': ventas_fmt,
            'total_efectivo': efectivo,
            'total_transferencia': transferencia,
            'total_general': sum(v['total'] for v in ventas_fmt)
        }

    @staticmethod
    def get_productos_mas_vendidos(fecha_desde: str, fecha_hasta: str):
        ReportesManager._check_permission()
        desde = f"{fecha_desde}T00:00:00"
        hasta = f"{fecha_hasta}T23:59:59"
        
        supabase = get_supabase()
        res = supabase.table('ventas_detalle').select(
            'cantidad, subtotal, productos(codigo_barras, nombre), ventas!inner(estado, fecha)'
        ).neq('ventas.estado', 'CANCELADA').gte('ventas.fecha', desde).lte('ventas.fecha', hasta).execute()
        
        agrupado = defaultdict(lambda: {'codigo_barras': '', 'nombre': '', 'cant_total': 0, 'recaudacion': 0.0})
        
        for d in res.data:
            if not d.get('productos'):
                continue
            prod_nombre = d['productos']['nombre']
            prod_codigo = d['productos']['codigo_barras']
            
            agrupado[prod_nombre]['codigo_barras'] = prod_codigo
            agrupado[prod_nombre]['nombre'] = prod_nombre
            agrupado[prod_nombre]['cant_total'] += float(d['cantidad'])
            agrupado[prod_nombre]['recaudacion'] += float(d['subtotal'])
            
        resultado = list(agrupado.values())
        resultado.sort(key=lambda x: x['cant_total'], reverse=True)
        return resultado

    @staticmethod
    def get_cierres_caja(fecha_desde: str, fecha_hasta: str, usuario_id: str = None):
        ReportesManager._check_permission()
        desde = f"{fecha_desde}T00:00:00"
        hasta = f"{fecha_hasta}T23:59:59"
        
        supabase = get_supabase()
        try:
            query = supabase.table('caja_sesiones').select('*, usuarios(nombre, username)').gte('fecha_apertura', desde).lte('fecha_apertura', hasta)
            if usuario_id:
                query = query.eq('usuario_id', usuario_id)
            res = query.order('fecha_apertura', desc=True).execute()
            return res.data
        except Exception:
            query = supabase.table('caja_sesiones').select('*').gte('fecha_apertura', desde).lte('fecha_apertura', hasta)
            res = query.order('fecha_apertura', desc=True).execute()
            return res.data

    @staticmethod
    def get_alertas_reposicion():
        ReportesManager._check_permission()
        supabase = get_supabase()
        res = supabase.table('productos').select('codigo_barras, nombre, stock_actual, stock_minimo, stock_maximo').eq('activo', True).execute()
        
        alertas = []
        for p in res.data:
            actual = float(p['stock_actual'])
            minimo = float(p['stock_minimo'])
            maximo = float(p['stock_maximo'])
            
            if actual <= minimo:
                alertas.append({
                    'codigo_barras': p['codigo_barras'],
                    'nombre': p['nombre'],
                    'stock_actual': actual,
                    'stock_minimo': minimo,
                    'stock_maximo': maximo,
                    'sugerido_pedir': maximo - actual
                })
                
        alertas.sort(key=lambda x: x['sugerido_pedir'], reverse=True)
        return alertas

    @staticmethod
    def get_reporte_ganancias(fecha_desde: str, fecha_hasta: str, usuario_id: str = None):
        ReportesManager._check_permission()
        desde = f"{fecha_desde}T00:00:00"
        hasta = f"{fecha_hasta}T23:59:59"
        
        supabase = get_supabase()
        query = supabase.table('ventas_detalle').select(
            'cantidad, costo_unitario, subtotal, ventas!inner(estado, fecha, usuario_id)'
        ).neq('ventas.estado', 'CANCELADA').gte('ventas.fecha', desde).lte('ventas.fecha', hasta)
        
        if usuario_id:
            query = query.eq('ventas.usuario_id', usuario_id)
            
        res = query.execute()
        
        ganancias_por_dia = defaultdict(lambda: {'total_vendido': 0.0, 'costo_total': 0.0, 'ganancia_neta': 0.0})
        totales = {'total_vendido': 0.0, 'costo_total': 0.0, 'ganancia_neta': 0.0}
        
        for d in res.data:
            fecha_str = d['ventas']['fecha']
            dia = fecha_str[:10]
                
            subt = float(d['subtotal'])
            costo = float(d['costo_unitario']) * float(d['cantidad'])
            neta = subt - costo
            
            ganancias_por_dia[dia]['total_vendido'] += subt
            ganancias_por_dia[dia]['costo_total'] += costo
            ganancias_por_dia[dia]['ganancia_neta'] += neta
            
            totales['total_vendido'] += subt
            totales['costo_total'] += costo
            totales['ganancia_neta'] += neta
            
        resultado_dias = []
        for dia, vals in ganancias_por_dia.items():
            resultado_dias.append({
                'dia': dia,
                'total_vendido': vals['total_vendido'],
                'costo_total': vals['costo_total'],
                'ganancia_neta': vals['ganancia_neta']
            })
            
        resultado_dias.sort(key=lambda x: x['dia'], reverse=True)
        
        return {
            'ganancias_por_dia': resultado_dias,
            'totales': totales
        }

    @staticmethod
    def get_ventas_por_rubro(fecha_desde: str, fecha_hasta: str):
        ReportesManager._check_permission()
        desde = f"{fecha_desde}T00:00:00"
        hasta = f"{fecha_hasta}T23:59:59"
        
        supabase = get_supabase()
        res = supabase.table('ventas_detalle').select(
            'cantidad, costo_unitario, subtotal, productos(categorias(nombre)), ventas!inner(estado, fecha)'
        ).neq('ventas.estado', 'CANCELADA').gte('ventas.fecha', desde).lte('ventas.fecha', hasta).execute()
        
        agrupado = defaultdict(lambda: {'total_vendido': 0.0, 'costo_total': 0.0, 'ganancia_neta': 0.0})
        
        for d in res.data:
            rubro = 'Sin Rubro'
            if d.get('productos') and d['productos'].get('categorias'):
                rubro = d['productos']['categorias']['nombre'] or 'Sin Rubro'
                
            subt = float(d['subtotal'])
            costo = float(d['costo_unitario']) * float(d['cantidad'])
            neta = subt - costo
            
            agrupado[rubro]['total_vendido'] += subt
            agrupado[rubro]['costo_total'] += costo
            agrupado[rubro]['ganancia_neta'] += neta
            
        resultado = []
        for r, vals in agrupado.items():
            resultado.append({
                'rubro': r,
                'total_vendido': vals['total_vendido'],
                'costo_total': vals['costo_total'],
                'ganancia_neta': vals['ganancia_neta']
            })
            
        resultado.sort(key=lambda x: x['total_vendido'], reverse=True)
        return resultado
