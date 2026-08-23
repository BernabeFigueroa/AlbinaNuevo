from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QFrame, QInputDialog, QDialog, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime, timezone, timedelta
try:
    import zoneinfo
except ImportError:
    zoneinfo = None

from src.core.proveedores_manager import ProveedoresManager
from src.core.cta_cte_proveedores_manager import CtaCteProveedoresManager
from src.core.caja_manager import CajaManager

def formatear_fecha_ar(fecha_str):
    if not fecha_str:
        return "-"
    try:
        dt = datetime.fromisoformat(str(fecha_str).replace('Z', '+00:00'))
        if zoneinfo:
            try:
                dt = dt.astimezone(zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires"))
            except Exception:
                dt = dt.astimezone(timezone(timedelta(hours=-3)))
        else:
            dt = dt.astimezone(timezone(timedelta(hours=-3)))
        return dt.strftime("%d/%m/%Y %H:%M hs")
    except Exception:
        return str(fecha_str)[:16].replace("T", " ")

class DeudasProveedoresView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cargar_proveedores()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        
        lbl_titulo = QLabel("CUENTAS A PAGAR (PROVEEDORES)")
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520;")
        layout.addWidget(lbl_titulo)

        # --- Filtro ---
        filtro_frame = QFrame()
        filtro_layout = QHBoxLayout(filtro_frame)
        
        filtro_layout.addWidget(QLabel("Seleccionar Proveedor:"))
        self.cb_proveedores = QComboBox()

        self.cb_proveedores.setMinimumWidth(300)
        self.cb_proveedores.currentIndexChanged.connect(self.cargar_datos_proveedor)
        filtro_layout.addWidget(self.cb_proveedores)
        
        self.btn_recargar = QPushButton("↻ Recargar")
        self.btn_recargar.clicked.connect(self.cargar_proveedores)
        filtro_layout.addWidget(self.btn_recargar)
        
        filtro_layout.addStretch()
        layout.addWidget(filtro_frame)

        # --- Resumen ---
        resumen_frame = QFrame()
        resumen_layout = QHBoxLayout(resumen_frame)
        self.lbl_saldo = QLabel("Saldo Deuda: $0.00")
        self.lbl_saldo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_saldo.setStyleSheet("color: #D99890;")
        resumen_layout.addWidget(self.lbl_saldo)
        
        resumen_layout.addStretch()
        
        self.btn_deuda = QPushButton("+ REGISTRAR DEUDA")
        self.btn_deuda.clicked.connect(self.registrar_deuda)
        resumen_layout.addWidget(self.btn_deuda)

        self.btn_pagar = QPushButton("REGISTRAR PAGO")
        self.btn_pagar.clicked.connect(self.registrar_pago)
        resumen_layout.addWidget(self.btn_pagar)
        layout.addWidget(resumen_frame)

        # --- Historial ---
        self.tabla = QTableWidget(0, 4)

        self.tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Detalle", "Monto"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

    def cargar_proveedores(self):
        self.cb_proveedores.blockSignals(True)
        self.cb_proveedores.clear()
        proveedores = ProveedoresManager.get_all()
        for p in proveedores:
            self.cb_proveedores.addItem(f"{p['nombre']}", p['id'])
        self.cb_proveedores.blockSignals(False)
        self.cargar_datos_proveedor()

    def cargar_datos_proveedor(self):
        proveedor_id = self.cb_proveedores.currentData()
        if not proveedor_id:
            self.lbl_saldo.setText("Saldo Deuda: $0.00")
            self.tabla.setRowCount(0)
            return
            
        saldo = CtaCteProveedoresManager.get_saldo(proveedor_id)
        self.lbl_saldo.setText(f"Deuda Pendiente: ${saldo:.2f}")
        if saldo > 0:
            self.lbl_saldo.setStyleSheet("color: #D99890;")
        else:
            self.lbl_saldo.setStyleSheet("color: #B09886;")
            
        historial = CtaCteProveedoresManager.get_historial(proveedor_id)
        self.tabla.setRowCount(0)
        for h in historial:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            item_fecha = QTableWidgetItem(formatear_fecha_ar(h['fecha']))
            self.tabla.setItem(row, 0, item_fecha)
            
            tipo_item = QTableWidgetItem(h['tipo'])
            if h['tipo'] == 'DEUDA':
                tipo_item.setForeground(Qt.GlobalColor.red)
            else:
                tipo_item.setForeground(Qt.GlobalColor.green)
            self.tabla.setItem(row, 1, tipo_item)
            
            self.tabla.setItem(row, 2, QTableWidgetItem(h['detalle'] or ""))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${h['monto']:.2f}"))

    def registrar_deuda(self):
        proveedor_id = self.cb_proveedores.currentData()
        if not proveedor_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proveedor primero.")
            return

        monto, ok = QInputDialog.getDouble(
            self, "Registrar Deuda", 
            "Monto de la deuda / compra (a cuenta):", 
            0.0, 0.01, 10000000.0, 2
        )
        if not ok: return

        detalle, ok2 = QInputDialog.getText(
            self, "Detalle", "Ingrese un detalle (opcional, ej. 'Remito 1234'):"
        )
        if not ok2: return

        try:
            sesion = CajaManager.obtener_sesion_activa()
            caja_id = sesion['id'] if sesion else None
            if not detalle.strip():
                detalle = "Compra de mercadería"
            CtaCteProveedoresManager.registrar_deuda(proveedor_id, monto, caja_id, detalle)
            QMessageBox.information(self, "Éxito", f"Deuda de ${monto:.2f} registrada correctamente.")
            self.cargar_datos_proveedor()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{str(e)}")

    def registrar_pago(self):
        proveedor_id = self.cb_proveedores.currentData()
        if not proveedor_id:
            QMessageBox.warning(self, "Atención", "Seleccione un proveedor primero.")
            return
            
        saldo = CtaCteProveedoresManager.get_saldo(proveedor_id)
        if saldo <= 0:
            QMessageBox.information(self, "Aviso", "No hay deuda pendiente con este proveedor.")
            return
            
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            QMessageBox.critical(self, "Caja Cerrada", "Debe abrir la caja diaria para poder registrar un egreso de dinero.")
            return

        dialog = PagoProveedorDialog(saldo, self)
        if dialog.exec():
            monto, metodo = dialog.get_data()
            try:
                CtaCteProveedoresManager.registrar_pago(proveedor_id, monto, metodo_pago=metodo)
                QMessageBox.information(self, "Éxito", f"Pago de ${monto:.2f} en {metodo} registrado.")
                self.cargar_datos_proveedor()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{str(e)}")

class PagoProveedorDialog(QDialog):
    def __init__(self, saldo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Pago a Proveedor")
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
        
        lbl_saldo_sub = QLabel("Deuda Total Pendiente:")
        lbl_saldo_sub.setStyleSheet("font-size: 11px; color: #7A7067; font-weight: normal;")
        
        lbl_saldo = QLabel(f"${saldo:.2f}")
        lbl_saldo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_saldo.setStyleSheet("color: #D99890;")
        
        card_layout.addWidget(lbl_saldo_sub)
        card_layout.addWidget(lbl_saldo)
        layout.addWidget(saldo_card)
        
        # Campo Monto
        layout.addWidget(QLabel("Monto a Abonar (Egreso de Caja):"))
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, saldo if saldo > 0 else 10000000.0)
        self.spin_monto.setValue(saldo if saldo > 0 else 0.0)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("$ ")
        layout.addWidget(self.spin_monto)
        
        # Campo Método
        layout.addWidget(QLabel("Método de Pago:"))
        self.cb_metodo = QComboBox()
        self.cb_metodo.addItems(["EFECTIVO", "TRANSFERENCIA"])
        layout.addWidget(self.cb_metodo)
        
        layout.addStretch()
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btn_neutral")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_aceptar = QPushButton("Registrar Pago")
        btn_aceptar.setObjectName("btn_primary")
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_aceptar)
        layout.addLayout(btn_layout)

    def get_data(self):
        return self.spin_monto.value(), self.cb_metodo.currentText()
