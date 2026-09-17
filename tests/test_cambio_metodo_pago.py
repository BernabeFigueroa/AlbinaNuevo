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


if __name__ == '__main__':
    unittest.main()
