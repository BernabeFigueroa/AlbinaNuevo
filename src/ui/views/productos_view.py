from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from src.core.productos_manager import ProductosManager
from src.core.auth_manager import AuthManager

class ProductosView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_productos()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Barra de herramientas (botones)
        toolbar = QHBoxLayout()
        
        self.btn_actualizar = QPushButton("Actualizar Lista")
        self.btn_actualizar.setStyleSheet("padding: 8px; background-color: #BFB1A6; color: black; font-weight: bold; border-radius: 4px;")
        self.btn_actualizar.clicked.connect(self.cargar_productos)
        toolbar.addWidget(self.btn_actualizar)
        
        toolbar.addStretch()
        
        if AuthManager.is_admin():
            self.btn_nuevo = QPushButton("+ Nuevo Producto")
            self.btn_editar = QPushButton("Editar Seleccionado")
            self.btn_eliminar = QPushButton("Eliminar Seleccionado")
            
            style = "padding: 8px; background-color: #ACA096; color: white; font-weight: bold; border-radius: 4px;"
            self.btn_nuevo.setStyleSheet(style)
            self.btn_editar.setStyleSheet(style)
            self.btn_eliminar.setStyleSheet("padding: 8px; background-color: #ff4c4c; color: white; font-weight: bold; border-radius: 4px;")
            
            toolbar.addWidget(self.btn_nuevo)
            toolbar.addWidget(self.btn_editar)
            toolbar.addWidget(self.btn_eliminar)
            
            self.btn_eliminar.clicked.connect(self.eliminar_producto)
            # btn_nuevo y btn_editar se conectarán a diálogos que haremos luego
            
        layout.addLayout(toolbar)
        
        # Tabla de productos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Código", "Nombre", "Precio", "Stock"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.tabla)
        
    def cargar_productos(self):
        try:
            productos = ProductosManager.obtener_productos()
            self.tabla.setRowCount(0)
            for i, p in enumerate(productos):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(p['id'])))
                self.tabla.setItem(i, 1, QTableWidgetItem(p.get('codigo_barras', '')))
                self.tabla.setItem(i, 2, QTableWidgetItem(p['nombre']))
                self.tabla.setItem(i, 3, QTableWidgetItem(f"${p['precio_contado']}"))
                self.tabla.setItem(i, 4, QTableWidgetItem(str(p['stock_actual'])))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los productos: {str(e)}")
            
    def eliminar_producto(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un producto para eliminar.")
            return
            
        id_prod = self.tabla.item(fila, 0).text()
        nombre = self.tabla.item(fila, 2).text()
        
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"¿Estás segura de eliminar '{nombre}'?\nEsta acción lo marcará como inactivo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                ProductosManager.eliminar_producto(int(id_prod))
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente.")
                self.cargar_productos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {str(e)}")
