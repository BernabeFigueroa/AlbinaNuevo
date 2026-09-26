"""Pruebas unitarias para cambio de método de pago entre Efectivo y Transferencia."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

from src.core.ventas_manager import VentasManager
from src.ui.reportes_view import DialogoDetalleVenta

app = QApplication.instance() or QApplication([])

class CambioMetodoPagoTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db_patch = patch('src.core.ventas_manager.get_supabase', return_value=self.db)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)

    def test_cambiar_metodo_pago_efectivo_a_transferencia_rpc(self):
        # 1. Simular venta encontrada con EFECTIVO
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 100, 'metodo_pago': 'EFECTIVO', 'estado': 'COMPLETADA', 'caja_sesion_id': 1}
        ]
        self.db.rpc.return_value.execute.return_value.data = {'success': True}

        res = VentasManager.cambiar_metodo_pago(100, 'TRANSFERENCIA')
        self.assertTrue(res['success'])
        self.assertEqual(res['metodo_nuevo'], 'TRANSFERENCIA')
        self.db.rpc.assert_called_with('cambiar_metodo_pago_atomico', {
            'p_venta_id': 100,
            'p_nuevo_metodo': 'TRANSFERENCIA'
        })

    def test_cambiar_metodo_pago_auto_toggle(self):
        # Si no se especifica nuevo_metodo, alterna automáticamente
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 101, 'metodo_pago': 'TRANSFERENCIA', 'estado': 'COMPLETADA', 'caja_sesion_id': 1}
        ]
        self.db.rpc.return_value.execute.return_value.data = {'success': True}

        res = VentasManager.cambiar_metodo_pago(101)
        self.assertTrue(res['success'])
        self.assertEqual(res['metodo_nuevo'], 'EFECTIVO')
        self.db.rpc.assert_called_with('cambiar_metodo_pago_atomico', {
            'p_venta_id': 101,
            'p_nuevo_metodo': 'EFECTIVO'
        })

    def test_cambiar_metodo_pago_fallback_actualiza_ventas_y_caja_movimientos(self):
        # Simular fallo en RPC para ejecutar fallback
        self.db.rpc.side_effect = Exception("RPC no encontrada")

        self.db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            # 1. select * from ventas where id = 50
            MagicMock(data=[{
                'id': 50, 'metodo_pago': 'EFECTIVO', 'estado': 'COMPLETADA', 'caja_sesion_id': 2
            }]),
            # 2. select id, descripcion from caja_movimientos where caja_sesion_id = 2
            MagicMock(data=[
                {'id': 301, 'descripcion': 'Venta #50'},
                {'id': 302, 'descripcion': 'Venta #99'}
            ])
        ]

        res = VentasManager.cambiar_metodo_pago(50, 'TRANSFERENCIA')
        self.assertTrue(res['success'])
        self.assertEqual(res['metodo_nuevo'], 'TRANSFERENCIA')

        # Verificar que se actualizó la venta
        self.db.table.return_value.update.assert_any_call({'metodo_pago': 'TRANSFERENCIA'})

    def test_rechaza_venta_inexistente(self):
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        with self.assertRaises(ValueError) as ctx:
            VentasManager.cambiar_metodo_pago(999)
        self.assertIn("no existe", str(ctx.exception))

    def test_rechaza_venta_anulada(self):
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 10, 'metodo_pago': 'EFECTIVO', 'estado': 'ANULADA', 'caja_sesion_id': 1}
        ]
        with self.assertRaises(ValueError) as ctx:
            VentasManager.cambiar_metodo_pago(10)
        self.assertIn("anulada", str(ctx.exception))

    def test_rechaza_metodos_no_permitidos(self):
        # Venta MIXTO
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 20, 'metodo_pago': 'MIXTO', 'estado': 'COMPLETADA', 'caja_sesion_id': 1}
        ]
        with self.assertRaises(ValueError) as ctx:
            VentasManager.cambiar_metodo_pago(20)
        self.assertIn("Solo se puede modificar ventas con método EFECTIVO o TRANSFERENCIA", str(ctx.exception))

        # Venta FIADO / CTA. CTE.
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 21, 'metodo_pago': 'FIADO / CTA. CTE.', 'estado': 'COMPLETADA', 'caja_sesion_id': 1}
        ]
        with self.assertRaises(ValueError) as ctx:
            VentasManager.cambiar_metodo_pago(21)
        self.assertIn("Solo se puede modificar ventas con método EFECTIVO o TRANSFERENCIA", str(ctx.exception))

    def test_rechaza_nuevo_metodo_invalido(self):
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 30, 'metodo_pago': 'EFECTIVO', 'estado': 'COMPLETADA', 'caja_sesion_id': 1}
        ]
        with self.assertRaises(ValueError) as ctx:
            VentasManager.cambiar_metodo_pago(30, 'TARJETA')
        self.assertIn("solo puede cambiarse a EFECTIVO o TRANSFERENCIA", str(ctx.exception))

    def test_dialogo_detalle_venta_ui_metodo_pago(self):
        # Caso 1: Venta en Efectivo
        info_efectivo = {'estado': 'COMPLETADA', 'metodo_pago': 'EFECTIVO', 'total': 1500.0}
        dlg = DialogoDetalleVenta(1, info_efectivo, "<p>Contenido</p>")
        self.assertFalse(dlg.btn_cambiar_metodo.isHidden())
        self.assertEqual(dlg.btn_cambiar_metodo.text(), "⇄ Cambiar a Transferencia")
        self.assertIn("EFECTIVO", dlg.lbl_metodo_badge.text())

        # Caso 2: Venta en Transferencia
        info_transferencia = {'estado': 'COMPLETADA', 'metodo_pago': 'TRANSFERENCIA', 'total': 1500.0}
        dlg2 = DialogoDetalleVenta(2, info_transferencia, "<p>Contenido</p>")
        self.assertFalse(dlg2.btn_cambiar_metodo.isHidden())
        self.assertEqual(dlg2.btn_cambiar_metodo.text(), "⇄ Cambiar a Efectivo")
        self.assertIn("TRANSFERENCIA", dlg2.lbl_metodo_badge.text())

        # Caso 3: Venta Anulada (no debe permitir cambiar)
        info_anulada = {'estado': 'ANULADA', 'metodo_pago': 'EFECTIVO', 'total': 1500.0}
        dlg3 = DialogoDetalleVenta(3, info_anulada, "<p>Contenido</p>")
        self.assertTrue(dlg3.btn_cambiar_metodo.isHidden())

        # Caso 4: Venta con otro método (Mixto)
        info_mixto = {'estado': 'COMPLETADA', 'metodo_pago': 'MIXTO', 'total': 1500.0}
        dlg4 = DialogoDetalleVenta(4, info_mixto, "<p>Contenido</p>")
        self.assertTrue(dlg4.btn_cambiar_metodo.isHidden())

    def test_reportes_manager_totales_tarjeta_y_general(self):
        from src.core.reportes_manager import ReportesManager
        from types import SimpleNamespace

        with patch('src.core.reportes_manager.get_supabase') as mock_sb, \
             patch('src.core.reportes_manager.ReportesManager._check_permission'):
            mock_sb.return_value.table.return_value.select.return_value.neq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value.data = [
                {'id': 1, 'fecha': '2026-09-18T10:00:00Z', 'total': 1000.0, 'metodo_pago': 'EFECTIVO', 'estado': 'COMPLETADA', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None},
                {'id': 2, 'fecha': '2026-09-18T11:00:00Z', 'total': 500.0, 'metodo_pago': 'TRANSFERENCIA', 'estado': 'COMPLETADA', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None},
                {'id': 3, 'fecha': '2026-09-18T12:00:00Z', 'total': 2000.0, 'metodo_pago': 'TARJETA', 'estado': 'COMPLETADA', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None},
                {'id': 4, 'fecha': '2026-09-18T13:00:00Z', 'total': 400.0, 'metodo_pago': 'EFECTIVO', 'estado': 'ANULADA', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None}
            ]

            res = ReportesManager.get_ventas_por_fecha("2026-09-18", "2026-09-18")
            self.assertEqual(res['total_efectivo'], 1000.0)
            self.assertEqual(res['total_transferencia'], 500.0)
            self.assertEqual(res['total_tarjeta'], 2000.0)
            # Total general debe ser la suma de efectivo + transferencia + tarjeta (-35%): 1000 + 500 + 1300 = 2800.0
            self.assertEqual(res['total_general'], 2800.0)

    def test_reportes_view_cargar_ventas_tarjeta_descontada_y_general_completo(self):
        from types import SimpleNamespace
        from PyQt6.QtWidgets import QLabel, QComboBox, QTableWidget
        from src.ui.reportes_view import ReportesView

        vista = SimpleNamespace(
            cb_metodo_pago=QComboBox(),
            cb_estado=QComboBox(),
            lbl_tot_efectivo=QLabel(),
            lbl_tot_transferencia=QLabel(),
            lbl_tot_tarjeta=QLabel(),
            lbl_tot_tarjeta_bruto=QLabel(),
            lbl_tot_general=QLabel(),
            tabla_ventas=QTableWidget(0, 7)
        )
        vista.cb_metodo_pago.addItem('TODOS')
        vista.cb_estado.addItem('TODAS')

        datos = {
            'ventas': [
                {'id': 1, 'fecha': '2026-09-18T10:00:00', 'total': 1000.0, 'metodo_pago': 'EFECTIVO', 'cliente': 'A', 'vendedor': 'B', 'es_anulada': False},
                {'id': 2, 'fecha': '2026-09-18T11:00:00', 'total': 1000.0, 'metodo_pago': 'TARJETA', 'cliente': 'C', 'vendedor': 'D', 'es_anulada': False}
            ],
            'total_efectivo': 1000.0,
            'total_transferencia': 0.0,
            'total_tarjeta': 1000.0,
            'total_tarjeta_descontada': 650.0,
            'total_general': 1650.0
        }

        with patch('src.ui.reportes_view.ReportesManager.get_ventas_por_fecha', return_value=datos):
            ReportesView.cargar_ventas(vista, '2026-09-18', '2026-09-18')

        # Tarjeta debe tener el 35% descontado: 1000 * 0.65 = 650.00
        self.assertEqual(vista.lbl_tot_tarjeta.text(), "$650.00")
        self.assertIn("1,000.00", vista.lbl_tot_tarjeta_bruto.text())

        # Total general debe ser efectivo + transferencia + tarjeta (-35%): 1650.00
        self.assertEqual(vista.lbl_tot_general.text(), "$1650.00")

    def test_caja_manager_resumen_tarjeta_descontada(self):
        from src.core.caja_manager import CajaManager

        with patch('src.core.caja_manager.get_supabase') as mock_sb:
            # 1. Sesión
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'id': 5, 'monto_inicial': 1000.0, 'estado': 'ABIERTA'}
            ]
            # 2. Ventas (select().eq().neq().neq().execute())
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.neq.return_value.neq.return_value.execute.return_value.data = [
                {'id': 1, 'metodo_pago': 'EFECTIVO', 'total': 2000.0},
                {'id': 2, 'metodo_pago': 'TRANSFERENCIA', 'total': 3000.0},
                {'id': 3, 'metodo_pago': 'TARJETA', 'total': 10000.0},
            ]
            # 3. Movimientos (select().eq().execute())
            # usa el mismo mock de eq().execute().data pero como ya se leyó sesión, los movimientos pueden ser []
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
                MagicMock(data=[{'id': 5, 'monto_inicial': 1000.0, 'estado': 'ABIERTA'}]),
                MagicMock(data=[])
            ]

            resumen = CajaManager.obtener_resumen(5)
            self.assertEqual(resumen['ventas_efectivo'], 2000.0)
            self.assertEqual(resumen['ventas_transferencia'], 3000.0)
            self.assertEqual(resumen['ventas_tarjeta'], 10000.0)
            # Tarjeta con 35% de descuento: 10000 * 0.65 = 6500.0
            self.assertEqual(resumen['ventas_tarjeta_descontada'], 6500.0)
            # Total vendido sumando tarjeta descontada (-35%): 2000 + 3000 + 6500 = 11500.0
            self.assertEqual(resumen['total_vendido'], 11500.0)


if __name__ == '__main__':
    unittest.main()


