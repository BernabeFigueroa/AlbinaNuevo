from src.db.database import get_supabase
from src.core.auth_manager import AuthManager

class ProductosManager:
    @staticmethod
    def _check_permission():
        if not AuthManager.get_current_user():
            raise PermissionError("Acceso Denegado: Debe iniciar sesión para modificar productos.")

    @staticmethod
    def get_all(incluir_inactivos=False):
        supabase = get_supabase()
        query = supabase.table('productos').select('*, categorias(nombre), proveedores(nombre)')
        if not incluir_inactivos:
            query = query.eq('activo', True)
        res = query.execute()
        
        # Reformatear para que la UI reciba diccionarios planos como sqlite.Row
        productos = []
        for p in res.data:
            prod = p.copy()
            prod['categoria_nombre'] = p['categorias']['nombre'] if p.get('categorias') else None
            prod['proveedor_nombre'] = p['proveedores']['nombre'] if p.get('proveedores') else None
            productos.append(prod)
        return productos

    @staticmethod
    def get_by_codigo(codigo: str):
        supabase = get_supabase()
        res = supabase.table('productos').select('*').eq('codigo_barras', codigo).eq('activo', True).execute()
        if res.data:
            return res.data[0]
            
        if codigo.isdigit():
            res = supabase.table('productos').select('*').eq('id', int(codigo)).eq('activo', True).execute()
            if res.data:
                return res.data[0]
        return None

    @staticmethod
    def get_by_id(producto_id: int):
        supabase = get_supabase()
        try:
            res = supabase.table('productos').select('*, creado_ref:usuarios!creado_por(nombre, username), modificado_ref:usuarios!modificado_por(nombre, username)').eq('id', producto_id).execute()
            return res.data[0] if res.data else None
        except Exception:
            res = supabase.table('productos').select('*').eq('id', producto_id).execute()
            return res.data[0] if res.data else None

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
        return res.data[0]['id']

    @staticmethod
    def actualizar_producto(producto_id, codigo_barras, nombre, costo_lista, flete, utilidad_porcentaje, precio_contado, precio_tarjeta, stock_actual, stock_minimo, stock_maximo=100.0, categoria_id=None, proveedor_id=None, codigo_fabrica="", unidades_bulto=1, ubicacion="", observaciones="", talle=""):
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
            'modificado_por': usuario_id
        }
        supabase.table('productos').update(data).eq('id', producto_id).execute()
        return True

    @staticmethod
    def eliminar_producto(producto_id):
        ProductosManager._check_permission()
        supabase = get_supabase()
        supabase.table('productos').update({'activo': False}).eq('id', producto_id).execute()
        return True

    @staticmethod
    def restaurar_producto(producto_id):
        ProductosManager._check_permission()
        supabase = get_supabase()
        supabase.table('productos').update({'activo': True}).eq('id', producto_id).execute()
        return True

    @staticmethod
    def actualizar_stock(producto_id, cantidad_cambio):
        # Nota: Idealmente se usaría un RPC en Supabase para evitar condiciones de carrera
        supabase = get_supabase()
        res = supabase.table('productos').select('stock_actual').eq('id', producto_id).execute()
        if res.data:
            nuevo_stock = float(res.data[0]['stock_actual']) + cantidad_cambio
            supabase.table('productos').update({'stock_actual': nuevo_stock}).eq('id', producto_id).execute()

    @staticmethod
    def get_historial_producto(producto_id: int):
        supabase = get_supabase()
        try:
            res = supabase.table('ventas_detalle').select(
                'cantidad, precio_unitario, subtotal, ventas!inner(fecha, metodo_pago, estado, clientes(nombre))'
            ).eq('producto_id', producto_id).neq('ventas.estado', 'CANCELADA').order('fecha', foreign_table='ventas', desc=True).execute()
        except Exception as e:
            res = supabase.table('ventas_detalle').select(
                'cantidad, precio_unitario, subtotal, ventas!inner(fecha, metodo_pago, estado, clientes(nombre))'
            ).eq('producto_id', producto_id).neq('ventas.estado', 'CANCELADA').execute()
        
        historial = []
        for d in res.data:
            v = d['ventas']
            c = v.get('clientes')
            historial.append({
                'fecha': v['fecha'],
                'cliente': c['nombre'] if c else 'Consumidor Final',
                'cantidad': d['cantidad'],
                'precio_unitario': d['precio_unitario'],
                'subtotal': d['subtotal'],
                'metodo_pago': v['metodo_pago']
            })
        return historial
