from src.db.database import get_supabase
from src.core.caja_manager import CajaManager
from src.core.auth_manager import AuthManager
from src.core.cache_manager import DataCache
from math import isfinite

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
            if not isfinite(cantidad) or cantidad <= 0:
                raise ValueError("La cantidad de cada artículo debe ser mayor a cero.")
            es_provisorio = item.get('es_provisorio', False)
            descripcion = str(item.get('nombre') or '').strip()
            costo = float(item.get('costo_unitario', 0)) if es_provisorio else 0
            precio = float(item['precio_unitario'])
            contado = float(item.get('precio_contado', precio))
            if any(not isfinite(valor) or valor < 0 for valor in (precio, contado, costo)):
                raise ValueError("Los precios y el costo deben ser números válidos mayores o iguales a cero.")
            if es_provisorio and (not descripcion or item.get('producto_id') is not None or item.get('promocion_id') is not None):
                raise ValueError("El artículo provisorio debe tener descripción y no estar vinculado al stock ni a una promoción.")
            items.append({
                'producto_id': item.get('producto_id'),
                'promocion_id': item.get('promocion_id'),
                'cantidad': cantidad,
                'precio_unitario': precio,
                'precio_contado': contado,
                'es_provisorio': es_provisorio,
                'descripcion': descripcion,
                'costo_unitario': costo,
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
        if any(item['es_provisorio'] for item in items):
            # Un RPC anterior ignora claves JSON desconocidas: impedir ventas sin trazabilidad.
            try:
                supabase.table('ventas').select('tiene_provisorios').limit(1).execute()
            except Exception as exc:
                raise RuntimeError(
                    "No se pudo verificar el soporte de artículos provisorios. "
                    "Verifique la conexión y aplique la migración 20260912_articulos_provisorios.sql antes de venderlos."
                ) from exc
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
        res = supabase.table('ventas_detalle').select('cantidad, precio_unitario, subtotal, descripcion, es_provisorio, productos(nombre)').eq('venta_id', venta_id).execute()
        
        resultado = []
        for d in res.data:
            nombre = d.get('descripcion') or (d['productos']['nombre'] if d.get('productos') else 'Artículo')
            resultado.append({
                'nombre': nombre,
                'es_provisorio': bool(d.get('es_provisorio')),
                'cantidad': d['cantidad'],
                'precio_unitario': d['precio_unitario'],
                'subtotal': d['subtotal']
            })

        # Obtener información adicional de la venta (ej. observaciones, auditoría o anulación)
        info_venta = {}
        try:
            res_v = supabase.table('ventas').select('*').eq('id', venta_id).execute()
            if res_v.data:
                info_venta = res_v.data[0]
                
                # Si está anulada, resolver datos de auditoría
                if info_venta.get('estado') in ('ANULADA', 'CANCELADA'):
                    nota = str(info_venta.get('nro_comprobante_afip') or '')
                    if nota.startswith("ANULADA|"):
                        partes = nota.split("|")
                        if len(partes) >= 4:
                            info_venta['fecha_anulacion'] = partes[1]
                            info_venta['usuario_anulacion_nombre'] = partes[2]
                            info_venta['motivo_anulacion'] = partes[3]
                    elif "ANULADA:" in nota:
                        info_venta['motivo_anulacion'] = nota.split("ANULADA:", 1)[1].strip()
                        if not info_venta.get('usuario_anulacion_nombre'):
                            info_venta['usuario_anulacion_nombre'] = AuthManager.get_current_user_name()
                        if not info_venta.get('fecha_anulacion'):
                            info_venta['fecha_anulacion'] = info_venta.get('fecha')

                    anulada_por = info_venta.get('anulada_por')
                    if anulada_por and not info_venta.get('usuario_anulacion_nombre'):
                        try:
                            u_res = supabase.table('usuarios').select('nombre, username').eq('id', anulada_por).execute()
                            if u_res.data:
                                info_venta['usuario_anulacion_nombre'] = u_res.data[0].get('nombre') or u_res.data[0].get('username')
                        except Exception:
                            pass
                    
                    if not info_venta.get('usuario_anulacion_nombre'):
                        info_venta['usuario_anulacion_nombre'] = AuthManager.get_current_user_name()
                    if not info_venta.get('fecha_anulacion'):
                        info_venta['fecha_anulacion'] = info_venta.get('fecha')
        except Exception:
            pass

        return {
            'detalles': resultado,
            'info_venta': info_venta
        }

    @staticmethod
    def anular_venta(venta_id: int, motivo: str):
        if not motivo or not str(motivo).strip():
            raise ValueError("Debe ingresar un motivo para anular la venta.")
        motivo = str(motivo).strip()

        from datetime import datetime, timezone
        supabase = get_supabase()
        rpc_exitoso = False
        try:
            res_rpc = supabase.rpc('anular_venta_atomica', {
                'p_venta_id': venta_id,
                'p_motivo': motivo
            }).execute()
            if res_rpc.data:
                rpc_exitoso = True
        except Exception:
            rpc_exitoso = False

        if not rpc_exitoso:
            # 1. Obtener la venta
            res_v = supabase.table('ventas').select('*').eq('id', venta_id).execute()
            if not res_v.data:
                raise ValueError(f"La venta #{venta_id} no existe.")
            venta = res_v.data[0]
            if venta.get('estado') in ('ANULADA', 'CANCELADA'):
                raise ValueError(f"La venta #{venta_id} ya se encuentra anulada.")

            usuario = AuthManager.get_current_user()
            usuario_id = str(usuario.id) if usuario else None
            usuario_nombre = AuthManager.get_current_user_name()
            now_iso = datetime.now(timezone.utc).isoformat()

            # 2. Actualizar estado de la venta
            datos_update = {
                'estado': 'ANULADA',
                'anulada_por': usuario_id,
                'fecha_anulacion': now_iso,
                'motivo_anulacion': motivo
            }
            try:
                supabase.table('ventas').update(datos_update).eq('id', venta_id).execute()
            except Exception:
                nota_anul = f"ANULADA|{now_iso}|{usuario_nombre}|{motivo}"
                supabase.table('ventas').update({
                    'estado': 'ANULADA',
                    'nro_comprobante_afip': nota_anul
                }).eq('id', venta_id).execute()

            # 3. Reintegrar stock de los productos vendidos
            detalles_res = supabase.table('ventas_detalle').select('producto_id, cantidad, es_provisorio').eq('venta_id', venta_id).execute()
            for d in (detalles_res.data or []):
                prod_id = d.get('producto_id')
                cant = float(d.get('cantidad') or 0)
                if prod_id and not d.get('es_provisorio') and cant > 0:
                    p_res = supabase.table('productos').select('stock_actual').eq('id', prod_id).execute()
                    if p_res.data:
                        stock_actual = float(p_res.data[0].get('stock_actual') or 0)
                        supabase.table('productos').update({'stock_actual': stock_actual + cant}).eq('id', prod_id).execute()

            # 4. Si fue fiada, eliminar la deuda generada en cuenta corriente
            mp = str(venta.get('metodo_pago') or '').upper()
            if any(term in mp for term in ['FIADO', 'CTA. CTE', 'CTA CTE', 'CUENTA CORRIENTE']):
                try:
                    supabase.table('cta_cte_movimientos').delete().eq('venta_id', venta_id).execute()
                except Exception:
                    pass

            # 5. En caja_movimientos, marcar los movimientos vinculados como ANULADA
            try:
                movs = supabase.table('caja_movimientos').select('id, descripcion').eq('caja_sesion_id', venta.get('caja_sesion_id')).execute()
                for m in (movs.data or []):
                    desc = str(m.get('descripcion') or '')
                    if f"Venta #{venta_id}" in desc:
                        supabase.table('caja_movimientos').update({
                            'tipo': 'ANULADA',
                            'descripcion': f"{desc} [ANULADA: {motivo}]"
                        }).eq('id', m['id']).execute()
            except Exception:
                pass

        # 6. Invalidar caché local de productos para que la grilla refleje el stock actualizado
        DataCache.invalidate_productos()

        return True

    @staticmethod
    def cambiar_metodo_pago(venta_id: int, nuevo_metodo: str = None):
        """
        Modifica el método de pago de una venta exclusivamente entre EFECTIVO y TRANSFERENCIA.
        Si nuevo_metodo es None, alterna automáticamente entre ambos métodos.
        Actualiza tanto la tabla 'ventas' como 'caja_movimientos'.
        """
        supabase = get_supabase()

        # 1. Obtener la venta
        res_v = supabase.table('ventas').select('*').eq('id', venta_id).execute()
        if not res_v.data:
            raise ValueError(f"La venta #{venta_id} no existe.")

        venta = res_v.data[0]
        if venta.get('estado') in ('ANULADA', 'CANCELADA'):
            raise ValueError("No se puede modificar el método de pago de una venta anulada.")

        metodo_actual = str(venta.get('metodo_pago') or '').strip().upper()
        if metodo_actual not in ('EFECTIVO', 'TRANSFERENCIA'):
            raise ValueError(
                f"Solo se puede modificar ventas con método EFECTIVO o TRANSFERENCIA. "
                f"La venta #{venta_id} tiene '{metodo_actual}'."
            )

        # 2. Determinar y validar el nuevo método
        if nuevo_metodo is None:
            nuevo_metodo = 'TRANSFERENCIA' if metodo_actual == 'EFECTIVO' else 'EFECTIVO'
        else:
            nuevo_metodo = str(nuevo_metodo).strip().upper()

        if nuevo_metodo not in ('EFECTIVO', 'TRANSFERENCIA'):
            raise ValueError("El método de pago solo puede cambiarse a EFECTIVO o TRANSFERENCIA.")

        if nuevo_metodo == metodo_actual:
            return {
                'success': True,
                'venta_id': venta_id,
                'metodo_anterior': metodo_actual,
                'metodo_nuevo': nuevo_metodo
            }

        # 3. Intentar RPC atómico
        rpc_exitoso = False
        try:
            res_rpc = supabase.rpc('cambiar_metodo_pago_atomico', {
                'p_venta_id': venta_id,
                'p_nuevo_metodo': nuevo_metodo
            }).execute()
            if res_rpc.data:
                rpc_exitoso = True
        except Exception:
            rpc_exitoso = False

        # 4. Fallback directo en caso de que la RPC no esté desplegada aún
        if not rpc_exitoso:
            supabase.table('ventas').update({
                'metodo_pago': nuevo_metodo
            }).eq('id', venta_id).execute()

            caja_sesion_id = venta.get('caja_sesion_id')
            if caja_sesion_id:
                try:
                    movs = supabase.table('caja_movimientos').select('id, descripcion').eq('caja_sesion_id', caja_sesion_id).execute()
                    for m in (movs.data or []):
                        desc = str(m.get('descripcion') or '')
                        if f"Venta #{venta_id}" in desc:
                            supabase.table('caja_movimientos').update({
                                'metodo_pago': nuevo_metodo
                            }).eq('id', m['id']).execute()
                except Exception as e:
                    print(f"Advertencia al actualizar caja_movimientos: {e}")

        return {
            'success': True,
            'venta_id': venta_id,
            'metodo_anterior': metodo_actual,
            'metodo_nuevo': nuevo_metodo
        }

