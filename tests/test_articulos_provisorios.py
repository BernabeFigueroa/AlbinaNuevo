"""Regresiones de venta y UI; no conecta con Supabase ni imprime comprobantes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QTableWidget, QDialog, QPushButton
from src.core.ventas_manager import VentasManager
from src.core.reportes_manager import ReportesManager
from src.ui.articulo_provisorio_dialog import ArticuloProvisorioDialog
from src.ui.pos_view import POSView, DialogoModificarPrecio
from src.ui.reportes_view import ReportesView


def provisorio(nombre='Bolsa'):
    return dict(producto_id=None, promocion_id=None, nombre=nombre, es_provisorio=True,
                cantidad=2, precio_unitario=120, precio_contado=100, costo_unitario=30)


class VentasProvisoriasTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.rpc.return_value.execute.return_value.data = [
            dict(venta_id=17, subtotal=440, descuento=40, total=400)
        ]
        self.db_patch = patch('src.core.ventas_manager.get_supabase', return_value=self.db)
        self.db_patch.start()
        self.cache_patch = patch('src.core.ventas_manager.DataCache.invalidate_productos')
        self.cache_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.cache_patch.stop)

    def test_venta_mixta_conserva_identidad_costo_y_auditoria_de_precio(self):
        stock = dict(producto_id=5, nombre='Collar', cantidad=1, precio_unitario=200,
                     precio_contado=200, precio_modificado=True, precio_original_efectivo=250)
        resultado = VentasManager.procesar_venta(1, 'EFECTIVO', [stock, provisorio(), provisorio('Caja')])
        args = self.db.rpc.call_args.args[1]
        self.assertEqual([i['descripcion'] for i in args['p_carrito']], ['Collar', 'Bolsa', 'Caja'])
        self.assertEqual([i['es_provisorio'] for i in args['p_carrito']], [False, True, True])
        self.assertEqual(args['p_carrito'][1]['costo_unitario'], 30)
        self.assertIsNone(args['p_carrito'][1]['producto_id'])
        self.assertIn('PRECIO MODIFICADO', args['p_nota_auditoria'])
        self.assertEqual(resultado['venta_id'], 17)
        self.db.rpc.assert_called_once()

    def test_rechaza_datos_invalidos_sin_enviar_venta(self):
        for cambios in ({'nombre': '  '}, {'producto_id': 5}, {'promocion_id': 3},
                        {'cantidad': float('nan')}, {'precio_unitario': float('inf')},
                        {'costo_unitario': -1}, {'cantidad': 0}):
            with self.subTest(cambios=cambios):
                item = provisorio()
                item.update(cambios)
                with self.assertRaises(ValueError):
                    VentasManager.procesar_venta(1, 'EFECTIVO', [item])
        self.db.rpc.assert_not_called()

    def test_backend_sin_migracion_no_procesa_articulo_sin_auditoria(self):
        self.db.table.return_value.select.return_value.limit.return_value.execute.side_effect = RuntimeError('missing column')
        with self.assertRaisesRegex(RuntimeError, 'migración'):
            VentasManager.procesar_venta(1, 'EFECTIVO', [provisorio()])
        self.db.rpc.assert_not_called()

    def test_detalle_recupera_nombre_y_marca_sin_producto(self):
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            dict(descripcion='Bolsa', es_provisorio=True, productos=None,
                 cantidad=2, precio_unitario=100, subtotal=200)
        ]
        detalle = VentasManager.get_detalles_venta(17)['detalles'][0]
        self.assertEqual(detalle['nombre'], 'Bolsa')
        self.assertTrue(detalle['es_provisorio'])

    def test_reporte_conserva_ambas_alertas(self):
        venta = dict(id=17, fecha='2026-09-12T12:00:00', total=200, metodo_pago='EFECTIVO',
                     tiene_provisorios=True, nro_comprobante_afip='PRECIO MODIFICADO: Collar',
                     clientes=None, usuarios=None)
        query = MagicMock()
        for method in ('select', 'neq', 'gte', 'lte', 'order'):
            getattr(query, method).return_value = query
        query.execute.return_value.data = [venta]
        with patch('src.core.reportes_manager.ReportesManager._check_permission'), \
             patch('src.core.reportes_manager.get_supabase') as get_db:
            get_db.return_value.table.return_value = query
            datos = ReportesManager.get_ventas_por_fecha('2026-09-12', '2026-09-12')
        self.assertTrue(datos['ventas'][0]['tiene_provisorios'])
        self.assertTrue(datos['ventas'][0]['precio_modificado'])


class ArticulosUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_cancelar_no_crea_producto_ni_item(self):
        with patch('src.ui.articulo_provisorio_dialog.ProductosManager.crear_producto') as crear:
            dialogo = ArticuloProvisorioDialog()
            dialogo.nombre.setText('Bolsa')
            dialogo.permanente.setChecked(True)
            dialogo.reject()
            self.assertIsNone(dialogo.item)
            crear.assert_not_called()

    def test_provisorio_no_escribe_catalogo_y_conserva_precios(self):
        with patch('src.ui.articulo_provisorio_dialog.ProductosManager.crear_producto') as crear:
            dialogo = ArticuloProvisorioDialog()
            dialogo.nombre.setText(' Bolsa ')
            dialogo.precio_contado.setValue(100)
            dialogo.precio_tarjeta.setValue(120)
            dialogo.agregar()
            self.assertEqual(dialogo.result(), QDialog.DialogCode.Accepted)
            self.assertTrue(dialogo.item['es_provisorio'])
            self.assertEqual(dialogo.item['nombre'], 'Bolsa')
            self.assertEqual(dialogo.item['precio_tarjeta'], 120)
            crear.assert_not_called()

    def test_cantidad_minima_respeta_precision_del_detalle(self):
        dialogo = ArticuloProvisorioDialog()
        dialogo.nombre.setText('Cinta')
        dialogo.cantidad.setValue(0.001)
        dialogo.agregar()
        self.assertEqual(dialogo.item['cantidad'], 0.01)
        self.assertEqual(dialogo.stock.decimals(), 2)

    def test_permanente_guarda_stock_total_y_se_agrega_como_producto(self):
        with patch('src.ui.articulo_provisorio_dialog.ProductosManager.crear_producto', return_value=42) as crear:
            dialogo = ArticuloProvisorioDialog()
            dialogo.nombre.setText('Bolsa')
            dialogo.codigo.setText('B001')
            dialogo.cantidad.setValue(2)
            dialogo.stock.setValue(10)
            dialogo.permanente.setChecked(True)
            dialogo.agregar()
            self.assertEqual(crear.call_args.kwargs['stock_actual'], 10)
            self.assertEqual(dialogo.item['producto_id'], 42)
            self.assertFalse(dialogo.item['es_provisorio'])
            self.assertEqual(dialogo.item['cantidad'], 2)

    def test_stock_inicial_insuficiente_no_crea_producto(self):
        with patch('src.ui.articulo_provisorio_dialog.ProductosManager.crear_producto') as crear, \
             patch('src.ui.articulo_provisorio_dialog.QMessageBox.warning'):
            dialogo = ArticuloProvisorioDialog()
            dialogo.nombre.setText('Bolsa')
            dialogo.codigo.setText('B001')
            dialogo.cantidad.setValue(2)
            dialogo.permanente.setChecked(True)
            dialogo.agregar()
            self.assertIsNone(dialogo.item)
            crear.assert_not_called()

    def test_fallo_al_guardar_no_agrega_provisorio_accidental(self):
        with patch('src.ui.articulo_provisorio_dialog.ProductosManager.crear_producto', side_effect=RuntimeError('duplicate')), \
             patch('src.ui.articulo_provisorio_dialog.QMessageBox.critical'):
            dialogo = ArticuloProvisorioDialog()
            dialogo.nombre.setText('Bolsa')
            dialogo.codigo.setText('B001')
            dialogo.permanente.setChecked(True)
            dialogo.agregar()
            self.assertIsNone(dialogo.item)
            self.assertNotEqual(dialogo.result(), QDialog.DialogCode.Accepted)

    def test_pos_mantiene_lineas_provisorias_separadas_y_cancelacion(self):
        vista = POSView()
        with patch('src.ui.pos_view.ArticuloProvisorioDialog') as dialogo:
            dialogo.return_value.exec.return_value = QDialog.DialogCode.Accepted
            for nombre in ('Bolsa', 'Caja'):
                dialogo.return_value.item = dict(provisorio(nombre), codigo_barras='[PROVISORIO]', precio_tarjeta=120)
                vista.agregar_articulo_provisorio()
            dialogo.return_value.exec.return_value = QDialog.DialogCode.Rejected
            vista.agregar_articulo_provisorio()
        self.assertEqual([i['nombre'] for i in vista.carrito], ['Bolsa', 'Caja'])
        self.assertEqual(vista.tabla_carrito.rowCount(), 2)

    def test_edicion_precio_provisorio_oculta_actualizacion_permanente(self):
        dialogo = DialogoModificarPrecio('Bolsa', 100, 120, permitir_permanente=False)
        boton = next(b for b in dialogo.findChildren(QPushButton) if 'Base de Datos' in b.text())
        self.assertTrue(boton.isHidden())

    def test_edicion_precio_catalogo_conserva_actualizacion(self):
        dialogo = DialogoModificarPrecio('Collar', 100, 120)
        boton = next(b for b in dialogo.findChildren(QPushButton) if 'Base de Datos' in b.text())
        boton.click()
        self.assertEqual(dialogo.respuesta, 'ACTUALIZAR_BD')

    def test_boton_articulo_compacto_con_ayuda(self):
        vista = POSView()
        self.assertEqual(vista.btn_articulo_provisorio.text(), '+ Artículo')
        self.assertEqual(vista.btn_articulo_provisorio.height(), 30)
        self.assertIn('provisorio', vista.btn_articulo_provisorio.toolTip())

    def test_historial_muestra_ambos_avisos_en_columna_existente(self):
        vista = SimpleNamespace(cb_metodo_pago=QComboBox(), lbl_tot_efectivo=QLabel(),
                                lbl_tot_transferencia=QLabel(), lbl_tot_general=QLabel(),
                                tabla_ventas=QTableWidget(0, 7))
        vista.cb_metodo_pago.addItem('TODOS')
        venta = dict(id=17, fecha='2026-09-12T12:00:00', total=200, metodo_pago='EFECTIVO',
                     cliente='Cliente', vendedor='Usuario', precio_modificado=True,
                     tiene_provisorios=True, detalle_modificacion='PRECIO MODIFICADO')
        datos = dict(ventas=[venta], total_efectivo=200, total_transferencia=0, total_general=200)
        with patch('src.ui.reportes_view.ReportesManager.get_ventas_por_fecha', return_value=datos):
            ReportesView.cargar_ventas(vista, '2026-09-12', '2026-09-12')
        self.assertEqual(vista.tabla_ventas.columnCount(), 7)
        aviso = vista.tabla_ventas.item(0, 6)
        self.assertIn('Precio modificado', aviso.text())
        self.assertIn('Provisorio', aviso.text())
        self.assertIn('stock', aviso.toolTip())


if __name__ == '__main__':
    unittest.main()
