from src.db.database import get_supabase
from src.core.auth_manager import AuthManager

class ProductosManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.get_current_user():
            raise PermissionError("Acceso Denegado: Debe iniciar sesión para modificar productos.")

    @staticmethod
    def _invalidate_cache():
        try:
            from src.core.cache_manager import DataCache
            DataCache.invalidate_productos()
        except Exception:
            pass

    @staticmethod
    def get_all(incluir_inactivos=False):
        supabase = get_supabase()
        query = supabase.table('productos').select('*, categorias(nombre), proveedores(nombre)')
        if not incluir_inactivos:
            query = query.eq('activo', True)
        res = query.execute()
        
        # Reformatear para que la UI reciba diccionarios planos con compatibilidad total de campos
        productos = []
        for p in res.data:
            prod = p.copy()
            # Mapear precio general a precio_contado / precio_tarjeta si no existen explícitos
            val_precio = float(p.get('precio') if p.get('precio') is not None else p.get('precio_contado') or 0.0)
            prod['precio_contado'] = float(p.get('precio_contado') if p.get('precio_contado') is not None else val_precio)
            prod['precio_tarjeta'] = float(p.get('precio_tarjeta') if p.get('precio_tarjeta') is not None else val_precio)
            
            # Mapear stock a stock_actual
            val_stock = int(p.get('stock') if p.get('stock') is not None else p.get('stock_actual') or 0)
            prod['stock_actual'] = val_stock
            
            prod['categoria_nombre'] = p['categorias']['nombre'] if p.get('categorias') else None
            prod['proveedor_nombre'] = p['proveedores']['nombre'] if p.get('proveedores') else None
            productos.append(prod)
        return productos

    @staticmethod
    def _normalizar_producto(prod: dict):
        if not prod: return prod
        p = prod.copy()
        val_precio = float(p.get('precio') if p.get('precio') is not None else p.get('precio_contado') or 0.0)
        p['precio_contado'] = float(p.get('precio_contado') if p.get('precio_contado') is not None else val_precio)
        p['precio_tarjeta'] = float(p.get('precio_tarjeta') if p.get('precio_tarjeta') is not None else val_precio)
        val_stock = int(p.get('stock') if p.get('stock') is not None else p.get('stock_actual') or 0)
        p['stock_actual'] = val_stock
        return p

    @staticmethod
    def get_by_codigo(codigo: str):
        supabase = get_supabase()
        res = supabase.table('productos').select('*').eq('codigo_barras', codigo).eq('activo', True).execute()
        if res.data:
            return ProductosManager._normalizar_producto(res.data[0])
            
        if codigo.isdigit():
            res = supabase.table('productos').select('*').eq('id', int(codigo)).eq('activo', True).execute()
            if res.data:
                return ProductosManager._normalizar_producto(res.data[0])
        return None

    @staticmethod
    def get_by_id(producto_id: int):
        supabase = get_supabase()
        try:
            res = supabase.table('productos').select('*, creado_ref:usuarios!creado_por(nombre, username), modificado_ref:usuarios!modificado_por(nombre, username)').eq('id', producto_id).execute()
            return ProductosManager._normalizar_producto(res.data[0]) if res.data else None
        except Exception:
            res = supabase.table('productos').select('*').eq('id', producto_id).execute()
            return ProductosManager._normalizar_producto(res.data[0]) if res.data else None

    @staticmethod
    def calcular_precios(costo_lista: float, flete: float, utilidad_porcentaje: float):
        costo_final = costo_lista + flete
        precio_contado = costo_final + (costo_final * (utilidad_porcentaje / 100))
        return costo_final, precio_contado

    @staticmethod
    def crear_producto(codigo_barras, nombre, costo_lista, flete, utilidad_porcentaje, precio_contado, precio_tarjeta, stock_actual, stock_minimo, stock_maximo=100.0, categoria_id=None, proveedor_id=None, codigo_fabrica="", unidades_bulto=1, ubicacion="", observaciones="", talle=""):
        ProductosManager._check_permission()
        costo_final = float(costo_lista) + float(flete)
        codigo_barras = codigo_barras.strip() if codigo_barras and codigo_barras.strip() else None
        
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        data = {
            'codigo_barras': codigo_barras, 'codigo_fabrica': codigo_fabrica, 'nombre': nombre,
            'costo_lista': costo_lista, 'flete': flete, 'costo_final': costo_final,
            'utilidad_porcentaje': utilidad_porcentaje, 'precio_contado': precio_contado,
            'precio_tarjeta': precio_tarjeta, 'stock_actual': stock_actual, 'stock_minimo': stock_minimo,
            'stock_maximo': stock_maximo, 'unidades_bulto': unidades_bulto, 'ubicacion': ubicacion,
            'observaciones': observaciones, 'categoria_id': categoria_id, 'proveedor_id': proveedor_id,
            'talle': talle,
            'creado_por': usuario_id,
            'modificado_por': usuario_id,
            'activo': True
        }
        res = supabase.table('productos').insert(data).execute()
        new_id = res.data[0]['id']
        if not codigo_barras:
            # Asignar automáticamente un código de barras único de 12 dígitos por defecto
            default_barcode = f"200{new_id:09d}"
            supabase.table('productos').update({'codigo_barras': default_barcode}).eq('id', new_id).execute()
        ProductosManager._invalidate_cache()
        return new_id

    @staticmethod
    def actualizar_producto(producto_id, codigo_barras, nombre, costo_lista, flete, utilidad_porcentaje, precio_contado, precio_tarjeta, stock_actual, stock_minimo, stock_maximo=100.0, categoria_id=None, proveedor_id=None, codigo_fabrica="", unidades_bulto=1, ubicacion="", observaciones="", talle=""):
        ProductosManager._check_permission()
        costo_final = float(costo_lista) + float(flete)
        codigo_barras = codigo_barras.strip() if codigo_barras and codigo_barras.strip() else f"200{producto_id:09d}"
        
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        data = {
            'codigo_barras': codigo_barras, 'codigo_fabrica': codigo_fabrica, 'nombre': nombre,
            'costo_lista': costo_lista, 'flete': flete, 'costo_final': costo_final,
            'utilidad_porcentaje': utilidad_porcentaje, 'precio_contado': precio_contado,
            'precio_tarjeta': precio_tarjeta, 'stock_actual': stock_actual, 'stock_minimo': stock_minimo,
            'stock_maximo': stock_maximo, 'unidades_bulto': unidades_bulto, 'ubicacion': ubicacion,
            'observaciones': observaciones, 'categoria_id': categoria_id, 'proveedor_id': proveedor_id,
            'talle': talle,
            'modificado_por': usuario_id
        }
        supabase.table('productos').update(data).eq('id', producto_id).execute()
        ProductosManager._invalidate_cache()
        return True

    @staticmethod
    def actualizar_precios_rapido(producto_id: int, nuevo_precio_contado: float, nuevo_precio_tarjeta: float):
        """Actualiza rápidamente los precios de un producto (contado y tarjeta) desde POS."""
        ProductosManager._check_permission()
        user = AuthManager.get_current_user()
        usuario_id = user.id if user else None

        supabase = get_supabase()
        data = {
            'precio_contado': nuevo_precio_contado,
            'precio_tarjeta': nuevo_precio_tarjeta,
            'modificado_por': usuario_id
        }
        supabase.table('productos').update(data).eq('id', producto_id).execute()
        ProductosManager._invalidate_cache()
        return True

    @staticmethod
    def eliminar_producto(producto_id):
        ProductosManager._check_permission()
        supabase = get_supabase()
        supabase.table('productos').update({'activo': False}).eq('id', producto_id).execute()
        ProductosManager._invalidate_cache()
        return True

    @staticmethod
    def restaurar_producto(producto_id):
        ProductosManager._check_permission()
        supabase = get_supabase()
        supabase.table('productos').update({'activo': True}).eq('id', producto_id).execute()
        ProductosManager._invalidate_cache()
        return True

    @staticmethod
    def actualizar_stock(producto_id, cantidad_cambio):
        # Nota: Idealmente se usaría un RPC en Supabase para evitar condiciones de carrera
        supabase = get_supabase()
        res = supabase.table('productos').select('stock_actual').eq('id', producto_id).execute()
        if res.data:
            nuevo_stock = float(res.data[0]['stock_actual']) + cantidad_cambio
            supabase.table('productos').update({'stock_actual': nuevo_stock}).eq('id', producto_id).execute()
            ProductosManager._invalidate_cache()


    @staticmethod
    def get_historial_producto(producto_id: int):
        supabase = get_supabase()
        try:
            res = supabase.table('ventas_detalle').select(
                'cantidad, precio_unitario, subtotal, ventas!inner(fecha, metodo_pago, estado, clientes(nombre))'
            ).eq('producto_id', producto_id).execute()
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
        
        historial = []
        for d in res.data:
            v = d.get('ventas') or {}
            if v.get('estado') == 'CANCELADA':
                continue
            
            cliente_info = v.get('clientes') or {}
            cliente_nombre = cliente_info.get('nombre') or 'Consumidor Final'
            
            # Formatear fecha
            fecha_str = v.get('fecha')
            try:
                # v['fecha'] suele ser formato ISO: '2026-08-13T05:32:32Z' o similar
                from datetime import datetime
                fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                fecha_str = fecha_dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                pass
                
            historial.append({
                'fecha': fecha_str,
                'cliente': cliente_nombre,
                'cantidad': d.get('cantidad'),
                'precio_unitario': float(d.get('precio_unitario', 0.0)),
                'subtotal': float(d.get('subtotal', 0.0)),
                'metodo_pago': v.get('metodo_pago', '')
            })
        return historial

