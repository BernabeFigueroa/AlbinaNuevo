from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QFrame, QSplitter, QInputDialog, QDialog, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.core.clientes_manager import ClientesManager
from src.core.cta_cte_manager import CtaCteManager
from src.core.caja_manager import CajaManager

class DeudoresView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cargar_clientes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_titulo = QLabel("CUENTAS CORRIENTES (DEUDORES)")
        lbl_titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #000000; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)

        # --- Filtro ---
        filtro_frame = QFrame()

        filtro_layout = QHBoxLayout(filtro_frame)
        
        filtro_layout.addWidget(QLabel("Seleccionar Cliente:"))
        self.cb_clientes = QComboBox()

        self.cb_clientes.setMinimumWidth(300)
        self.cb_clientes.currentIndexChanged.connect(self.cargar_datos_cliente)
        filtro_layout.addWidget(self.cb_clientes)
        
        self.btn_recargar = QPushButton("↻ Recargar")
        self.btn_recargar.clicked.connect(self.cargar_clientes)
        filtro_layout.addWidget(self.btn_recargar)
        
        filtro_layout.addStretch()
        layout.addWidget(filtro_frame)

        # --- Resumen ---
        resumen_frame = QFrame()
        resumen_layout = QHBoxLayout(resumen_frame)
        self.lbl_saldo = QLabel("Saldo Pendiente: $0.00")
        self.lbl_saldo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_saldo.setStyleSheet("color: #D99890;")
        resumen_layout.addWidget(self.lbl_saldo)
        
        resumen_layout.addStretch()
        
        self.btn_pagar = QPushButton("REGISTRAR PAGO / A FAVOR")

        self.btn_pagar.clicked.connect(self.registrar_pago)
        resumen_layout.addWidget(self.btn_pagar)
        layout.addWidget(resumen_frame)

        # --- Historial ---
        self.tabla = QTableWidget(0, 5)

        self.tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Detalle", "Registró", "Monto"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.ver_detalle)
        layout.addWidget(self.tabla)

    def ver_detalle(self, row, col):
        item_fecha = self.tabla.item(row, 0)
        if not item_fecha: return
        venta_id = item_fecha.data(Qt.ItemDataRole.UserRole)
        
        if not venta_id:
            return  # No es una venta (probablemente sea un pago o ajuste)
            
        from src.core.ventas_manager import VentasManager
        try:
            detalles = VentasManager.get_detalles_venta(venta_id)
            texto = f"Detalle de la Venta #{venta_id}:\n\n"
            for d in detalles:
                texto += f"- {d['cantidad']} x {d['nombre']} (${d['precio_unitario']:.2f}) = ${d['subtotal']:.2f}\n"
            
            QMessageBox.information(self, f"Detalle de Compra", texto)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{str(e)}")

    def cargar_clientes(self):
        self.cb_clientes.blockSignals(True)
        self.cb_clientes.clear()
        clientes = ClientesManager.get_all()
        for c in clientes:
            if c['id'] != 1: # Ignorar Consumidor Final
                self.cb_clientes.addItem(f"{c['nombre']} (CUIT: {c['cuit']})", c['id'])
        self.cb_clientes.blockSignals(False)
        self.cargar_datos_cliente()

    def cargar_datos_cliente(self):
        cliente_id = self.cb_clientes.currentData()
        if not cliente_id:
            self.lbl_saldo.setText("Saldo Pendiente: $0.00")
            self.tabla.setRowCount(0)
            return
            
        saldo = CtaCteManager.get_saldo(cliente_id)
        if saldo > 0:
            self.lbl_saldo.setText(f"Saldo Pendiente (Deuda): ${saldo:.2f}")
            self.lbl_saldo.setStyleSheet("color: #D99890;")
        elif saldo < 0:
            self.lbl_saldo.setText(f"Saldo A Favor: ${abs(saldo):.2f}")
            self.lbl_saldo.setStyleSheet("color: #B09886;")
        else:
            self.lbl_saldo.setText(f"Saldo: $0.00")
            self.lbl_saldo.setStyleSheet("color: #000000;")
            
        historial = CtaCteManager.get_historial(cliente_id)
        self.tabla.setRowCount(0)
        for h in historial:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            item_fecha = QTableWidgetItem(h['fecha'])
            if 'venta_id' in h and h['venta_id']:
                item_fecha.setData(Qt.ItemDataRole.UserRole, h['venta_id'])
            self.tabla.setItem(row, 0, item_fecha)
            
            tipo_item = QTableWidgetItem(h['tipo'])
            if h['tipo'] == 'DEUDA':
                tipo_item.setForeground(Qt.GlobalColor.red)
            else:
                tipo_item.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(row, 1, tipo_item)
            
            self.tabla.setItem(row, 2, QTableWidgetItem(h['detalle'] or ""))
            
            vendedor = "Sistema"
            if h.get('usuarios'):
                vendedor = h['usuarios'].get('nombre') or h['usuarios'].get('username') or "Desconocido"
            self.tabla.setItem(row, 3, QTableWidgetItem(vendedor))
            
            self.tabla.setItem(row, 4, QTableWidgetItem(f"${h['monto']:.2f}"))

    def registrar_pago(self):
        cliente_id = self.cb_clientes.currentData()
        if not cliente_id:
            QMessageBox.warning(self, "Atención", "Seleccione un cliente primero.")
            return
            
        saldo = CtaCteManager.get_saldo(cliente_id)
            
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            QMessageBox.critical(self, "Caja Cerrada", "Debe abrir la caja diaria para poder cobrar y que el dinero ingrese a la caja.")
            return

        dialog = PagoDialog(saldo, self)
        if dialog.exec():
            monto, metodo = dialog.get_data()
            try:
                CtaCteManager.registrar_pago(cliente_id, monto, sesion['id'], metodo_pago=metodo)
                QMessageBox.information(self, "Éxito", f"Pago de ${monto:.2f} en {metodo} registrado.")
                self.cargar_datos_cliente()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{str(e)}")

class PagoDialog(QDialog):
    def __init__(self, saldo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Pago de Cliente")
        self.setFixedSize(380, 310)
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
                color: #2C2520;
            }
            QLabel {
                color: #2C2520;
                font-size: 13px;
                font-weight: 500;
            }
            QDoubleSpinBox, QComboBox {
                background-color: #FFFFFF;
                color: #2C2520;
                border: 1px solid #ACA096;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 14px;
                min-height: 32px;
            }
            QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #B09886;
            }
            QPushButton {
                min-height: 32px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        # Tarjeta de saldo destacado
        saldo_card = QFrame()
        saldo_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5DFD5;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(saldo_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)
        
        lbl_saldo_sub = QLabel("Saldo Total Pendiente:")
        lbl_saldo_sub.setStyleSheet("font-size: 11px; color: #7A7067; font-weight: normal;")
        
        lbl_saldo = QLabel(f"${saldo:.2f}")
        lbl_saldo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_saldo.setStyleSheet("color: #D99890;") if saldo > 0 else lbl_saldo.setStyleSheet("color: #B09886;")
        
        card_layout.addWidget(lbl_saldo_sub)
        card_layout.addWidget(lbl_saldo)
        layout.addWidget(saldo_card)
        
        # Campo Monto
        layout.addWidget(QLabel("Monto a Abonar / Saldo a Favor:"))
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, 10000000.0)
        self.spin_monto.setValue(saldo if saldo > 0 else 0.0)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("$ ")
        layout.addWidget(self.spin_monto)
        
        # Campo Método
        layout.addWidget(QLabel("Método / Tipo de Cobro:"))
        self.cb_metodo = QComboBox()
        self.cb_metodo.addItems(["EFECTIVO", "TRANSFERENCIA", "CANJE / MERCADERIA"])
        layout.addWidget(self.cb_metodo)
        
        layout.addStretch()
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_neutral")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_aceptar = QPushButton("Registrar Cobro")
        btn_aceptar.setObjectName("btn_primary")
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_aceptar)
        layout.addLayout(btn_layout)

    def get_data(self):
        return self.spin_monto.value(), self.cb_metodo.currentText()
