from src.db.database import get_supabase
from src.core.caja_manager import CajaManager
from src.core.auth_manager import AuthManager

class VentasManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.is_admin():
            raise PermissionError("Acceso Denegado: Solo la dueña puede anular ventas.")

    @staticmethod
    def procesar_venta(cliente_id: int, metodo_pago: str, carrito: list, montos_mixto: dict = None):
        sesion_caja = CajaManager.obtener_sesion_activa()
        if not sesion_caja:
            raise Exception("Debe abrir la caja antes de realizar una venta.")

        subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in carrito)
        pct_descuento = 0.0
        if metodo_pago in ['EFECTIVO', 'TRANSFERENCIA']:
            pct_descuento += 30.0

        supabase = get_supabase()
        
        # Validar si el cliente tiene descuento adicional
        res_cliente = supabase.table('clientes').select('descuento_porcentaje').eq('id', cliente_id).execute()
        if res_cliente.data and res_cliente.data[0].get('descuento_porcentaje', 0) > 0:
            pct_descuento += res_cliente.data[0]['descuento_porcentaje']
            
        descuento_total = subtotal * (pct_descuento / 100.0)
        total = subtotal - descuento_total

        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        # 1. Crear registro de venta
        venta_data = {
            'cliente_id': cliente_id,
            'caja_sesion_id': sesion_caja['id'],
            'usuario_id': usuario_id,
            'subtotal': subtotal,
            'descuento_total': descuento_total,
            'total': total,
            'metodo_pago': metodo_pago,
            'estado': 'COMPLETADA'
        }
        res_venta = supabase.table('ventas').insert(venta_data).execute()
        venta_id = res_venta.data[0]['id']

        # 2. Registrar detalles y descontar stock
        for item in carrito:
            # Obtener costo unitario
            costo_unit = 0.0
            if item.get('producto_id'):
                res_prod = supabase.table('productos').select('costo_final, stock_actual').eq('id', item['producto_id']).execute()
                if res_prod.data:
                    costo_unit = res_prod.data[0].get('costo_final', 0.0)
                    nuevo_stock = res_prod.data[0]['stock_actual'] - item['cantidad']
                    supabase.table('productos').update({'stock_actual': nuevo_stock}).eq('id', item['producto_id']).execute()
                    
            subt_item = item['cantidad'] * item['precio_unitario']
            
            detalle_data = {
                'venta_id': venta_id,
                'producto_id': item.get('producto_id'),
                'cantidad': item['cantidad'],
                'precio_unitario': item['precio_unitario'],
                'costo_unitario': costo_unit,
                'subtotal': subt_item
            }
            supabase.table('ventas_detalle').insert(detalle_data).execute()

        # 3. Registrar en movimientos de caja
        if metodo_pago == 'MIXTO' and montos_mixto:
            for mp, monto in montos_mixto.items():
                if monto > 0:
                    mov_data = {
                        'caja_sesion_id': sesion_caja['id'],
                        'tipo': 'VENTA',
                        'monto': monto,
                        'metodo_pago': mp,
                        'descripcion': f"Venta #{venta_id} (Mixto)"
                    }
                    supabase.table('caja_movimientos').insert(mov_data).execute()
        elif metodo_pago != 'FIADO / CTA. CTE.':
            mov_data = {
                'caja_sesion_id': sesion_caja['id'],
                'tipo': 'VENTA',
                'monto': total,
                'metodo_pago': metodo_pago,
                'descripcion': f"Venta #{venta_id}"
            }
            supabase.table('caja_movimientos').insert(mov_data).execute()
        else:
            # Registrar deuda en Cta Cte
            cta_data = {
                'cliente_id': cliente_id,
                'caja_sesion_id': sesion_caja['id'],
                'venta_id': venta_id,
                'tipo': 'DEUDA',
                'monto': total,
                'detalle': f"Venta Fiada #{venta_id}"
            }
            supabase.table('cta_cte_movimientos').insert(cta_data).execute()

        return {
            "venta_id": venta_id,
            "subtotal": subtotal,
            "descuento": descuento_total,
            "total": total
        }

    @staticmethod
    def get_detalles_venta(venta_id: int):
        supabase = get_supabase()
        res = supabase.table('ventas_detalle').select('cantidad, precio_unitario, subtotal, productos(nombre)').eq('venta_id', venta_id).execute()
        
        resultado = []
        for d in res.data:
            nombre = d['productos']['nombre'] if d.get('productos') else 'Artículo'
            resultado.append({
                'nombre': nombre,
                'cantidad': d['cantidad'],
                'precio_unitario': d['precio_unitario'],
                'subtotal': d['subtotal']
            })
        return resultado
