from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from src.core.ventas_manager import VentasManager
from src.core.auth_manager import AuthManager

class VentasView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_ventas()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        toolbar = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar Historial")
        self.btn_actualizar.setStyleSheet("padding: 8px; background-color: #BFB1A6; color: black; font-weight: bold; border-radius: 4px;")
        self.btn_actualizar.clicked.connect(self.cargar_ventas)
        toolbar.addWidget(self.btn_actualizar)
        
        toolbar.addStretch()
        
        if AuthManager.is_admin():
            self.btn_anular = QPushButton("Anular Venta")
            self.btn_anular.setStyleSheet("padding: 8px; background-color: #ff4c4c; color: white; font-weight: bold; border-radius: 4px;")
            self.btn_anular.clicked.connect(self.anular_venta)
            toolbar.addWidget(self.btn_anular)
            
        layout.addLayout(toolbar)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Fecha", "Cliente", "Metodo Pago", "Total", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.tabla)
        
    def cargar_ventas(self):
        try:
            ventas = VentasManager.obtener_ventas_sesion_actual()
            self.tabla.setRowCount(0)
            for i, v in enumerate(ventas):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(v['id'])))
                self.tabla.setItem(i, 1, QTableWidgetItem(str(v['fecha'])[:16].replace('T', ' ')))
                self.tabla.setItem(i, 2, QTableWidgetItem(str(v['cliente_id']))) # Simplificado
                self.tabla.setItem(i, 3, QTableWidgetItem(v['metodo_pago']))
                self.tabla.setItem(i, 4, QTableWidgetItem(f"${v['total']}"))
                self.tabla.setItem(i, 5, QTableWidgetItem(v['estado']))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial: {str(e)}")
            
    def anular_venta(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una venta para anular.")
            return
            
        id_venta = self.tabla.item(fila, 0).text()
        estado = self.tabla.item(fila, 5).text()
        
        if estado == 'ANULADA':
            QMessageBox.warning(self, "Atención", "Esta venta ya está anulada.")
            return
        
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"¿Estás segura de anular la venta #{id_venta}?\nLos productos volverán al inventario.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                VentasManager.anular_venta(int(id_venta))
                QMessageBox.information(self, "Éxito", "Venta anulada correctamente.")
                self.cargar_ventas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo anular: {str(e)}")
