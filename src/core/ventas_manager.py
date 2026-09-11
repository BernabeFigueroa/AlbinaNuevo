from src.db.database import get_supabase
from src.core.caja_manager import CajaManager
from src.core.auth_manager import AuthManager
from src.core.cache_manager import DataCache

class VentasManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.is_admin():
            raise PermissionError("Acceso Denegado: Solo la dueña puede anular ventas.")

    @staticmethod
    def procesar_venta(cliente_id: int, metodo_pago: str, carrito: list, montos_mixto: dict = None):
        if not carrito:
            raise ValueError("No se puede procesar una venta sin artículos.")

        # La base de datos es la frontera transaccional: venta, detalle, stock,
        # caja y cuenta corriente se confirman juntos o se revierten juntos.
        # Sólo se envían los datos necesarios, nunca referencias de widgets/UI.
        items = []
        for item in carrito:
            cantidad = float(item['cantidad'])
            if cantidad <= 0:
                raise ValueError("La cantidad de cada artículo debe ser mayor a cero.")
            items.append({
                'producto_id': item.get('producto_id'),
                'promocion_id': item.get('promocion_id'),
                'cantidad': cantidad,
                'precio_unitario': float(item['precio_unitario']),
                'precio_contado': float(item.get('precio_contado', item['precio_unitario']))
            })

        # Detectar si en el carrito hubo modificación manual de precios
        items_modificados = [
            f"{it['nombre'][:15]} (${it.get('precio_original_efectivo', 0):.0f}->${it.get('precio_contado', 0):.0f})"
            for it in carrito if it.get('precio_modificado')
        ]
        info_modificado = None
        if items_modificados:
            info_modificado = "PRECIO MODIFICADO: " + ", ".join(items_modificados)
            if len(info_modificado) > 100:
                info_modificado = info_modificado[:97] + "..."

        supabase = get_supabase()
        response = supabase.rpc('procesar_venta_atomica', {
            'p_cliente_id': cliente_id,
            'p_metodo_pago': metodo_pago,
            'p_carrito': items,
            'p_montos_mixto': montos_mixto,
            'p_nota_auditoria': info_modificado
        }).execute()

        if not response.data:
            raise RuntimeError("La base de datos no devolvió el resultado de la venta.")

        resultado = response.data[0]

        # 4. Invalidar caché de productos para que la grilla refleje el stock actualizado
        DataCache.invalidate_productos()

        return {
            "venta_id": resultado['venta_id'],
            "subtotal": float(resultado['subtotal']),
            "descuento": float(resultado['descuento']),
            "total": float(resultado['total'])
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

        # Obtener información adicional de la venta (ej. observaciones o ajuste de precios)
        info_venta = {}
        try:
            res_v = supabase.table('ventas').select('nro_comprobante_afip, metodo_pago, fecha').eq('id', venta_id).execute()
            if res_v.data:
                info_venta = res_v.data[0]
        except Exception:
            pass

        return {
            'detalles': resultado,
            'info_venta': info_venta
        }
