"""Pruebas unitarias para anulación lógica de ventas, reversión de stock y auditoría."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

from src.core.ventas_manager import VentasManager
from src.core.caja_manager import CajaManager
from src.core.reportes_manager import ReportesManager
from src.ui.reportes_view import DialogoConfirmarAnulacion, DialogoDetalleVenta

app = QApplication.instance() or QApplication([])

class AnulacionVentasTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db_patch = patch('src.core.ventas_manager.get_supabase', return_value=self.db)
        self.db_patch.start()
        self.cache_patch = patch('src.core.ventas_manager.DataCache.invalidate_productos')
        self.cache_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.cache_patch.stop)

    def test_anular_venta_exige_motivo(self):
        with self.assertRaises(ValueError):
            VentasManager.anular_venta(10, "")
        with self.assertRaises(ValueError):
            VentasManager.anular_venta(10, "   ")

    def test_anular_venta_rpc_exitoso(self):
        self.db.rpc.return_value.execute.return_value.data = {'success': True}
        res = VentasManager.anular_venta(45, "Cambio de producto")
        self.assertTrue(res)
        self.db.rpc.assert_called_with('anular_venta_atomica', {
            'p_venta_id': 45,
            'p_motivo': 'Cambio de producto'
        })

    def test_anular_venta_fallback_directo_restituye_stock_y_caja(self):
        # Simular fallo en RPC para forzar fallback
        self.db.rpc.side_effect = Exception("RPC no instalada")
        
        # Venta existente completada
        self.db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            # 1. select * from ventas where id = 12
            MagicMock(data=[{
                'id': 12, 'estado': 'COMPLETADA', 'caja_sesion_id': 1,
                'metodo_pago': 'EFECTIVO', 'nro_comprobante_afip': None
            }]),
            # 2. select producto_id, cantidad, es_provisorio from ventas_detalle
            MagicMock(data=[
                {'producto_id': 101, 'cantidad': 3.0, 'es_provisorio': False},
                {'producto_id': None, 'cantidad': 1.0, 'es_provisorio': True}
            ]),
            # 3. select stock_actual from productos where id = 101
            MagicMock(data=[{'stock_actual': 7.0}]),
            # 4. select id, descripcion from caja_movimientos where caja_sesion_id = 1
            MagicMock(data=[{'id': 50, 'descripcion': 'Venta #12'}])
        ]

        with patch('src.core.ventas_manager.AuthManager.get_current_user', return_value=MagicMock(id='user-uuid')):
            res = VentasManager.anular_venta(12, "Clienta devolvió los aros")
            self.assertTrue(res)

    def test_reportes_excluye_anuladas_de_totales(self):
        with patch('src.core.reportes_manager.AuthManager.is_admin', return_value=True), \
             patch('src.core.reportes_manager.get_supabase') as mock_sb:
            
            mock_sb.return_value.table.return_value.select.return_value.neq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value.data = [
                {'id': 1, 'fecha': '2026-09-14T10:00:00Z', 'total': 1000.0, 'metodo_pago': 'EFECTIVO', 'estado': 'COMPLETADA', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None},
                {'id': 2, 'fecha': '2026-09-14T11:00:00Z', 'total': 500.0, 'metodo_pago': 'EFECTIVO', 'estado': 'ANULADA', 'anulada_por': None, 'fecha_anulacion': '2026-09-14T11:30:00Z', 'motivo_anulacion': 'Devolución', 'nro_comprobante_afip': None, 'tiene_provisorios': False, 'clientes': None, 'usuarios': None}
            ]

            res = ReportesManager.get_ventas_por_fecha("2026-09-14", "2026-09-14")
            
            # El listado conserva ambas ventas para trazabilidad
            self.assertEqual(len(res['ventas']), 2)
            # Los totales sólo suman la venta completada ($1000), excluyendo los $500 de la anulada
            self.assertEqual(res['total_efectivo'], 1000.0)
            self.assertEqual(res['total_general'], 1000.0)
            self.assertTrue(res['ventas'][1]['es_anulada'])

    def test_caja_resumen_excluye_ventas_anuladas(self):
        with patch('src.core.caja_manager.get_supabase') as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'id': 1, 'monto_inicial': 5000.0, 'estado': 'ABIERTA'}
            ]
            
            # Mock para ventas donde la venta anulada no se retorna por el filtro .neq('estado', 'ANULADA')
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.neq.return_value.neq.return_value.execute.return_value.data = [
                {'id': 10, 'metodo_pago': 'EFECTIVO', 'total': 3000.0}
            ]
            
            resumen = CajaManager.obtener_resumen(1)
            self.assertEqual(resumen['ventas_efectivo'], 3000.0)
            self.assertEqual(resumen['total_efectivo_esperado'], 8000.0)

    def test_dialogo_confirmar_anulacion_valida_motivo(self):
        dlg = DialogoConfirmarAnulacion(99)
        self.assertEqual(dlg.motivo, "")
        with patch('src.ui.reportes_view.QMessageBox.warning') as mock_warn:
            dlg.txt_motivo.setText("   ")
            dlg.validar_y_aceptar()
            self.assertEqual(dlg.motivo, "") # No aceptado
            mock_warn.assert_called_once()
        
        dlg.txt_motivo.setText("Motivo válido")
        dlg.validar_y_aceptar()
        self.assertEqual(dlg.motivo, "Motivo válido")

if __name__ == '__main__':
    unittest.main()
