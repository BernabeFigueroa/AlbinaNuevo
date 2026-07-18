from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLabel, QLineEdit
)
from PyQt6.QtCore import Qt
from src.core.productos_manager import ProductosManager
from src.core.ventas_manager import VentasManager
from src.core.caja_manager import CajaManager

class CajaView(QWidget):
    def __init__(self):
        super().__init__()
        self.carrito = [] # Lista de diccionarios con info del producto
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título y estado de caja
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("Punto de Venta")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_abrir_caja = QPushButton("Abrir Caja Inicial")
        self.btn_abrir_caja.setStyleSheet("background-color: #BFB1A6; padding: 8px; font-weight: bold;")
        self.btn_abrir_caja.clicked.connect(self.abrir_caja)
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_abrir_caja)
        layout.addLayout(header_layout)
        
        # Buscador de productos
        search_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Escanear código de barras o escribir nombre del producto...")
        self.input_buscar.setStyleSheet("padding: 10px; font-size: 16px;")
        self.input_buscar.returnPressed.connect(self.buscar_producto)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("padding: 10px; background-color: #ACA096; color: white; font-weight: bold;")
        btn_buscar.clicked.connect(self.buscar_producto)
        
        search_layout.addWidget(self.input_buscar)
        search_layout.addWidget(btn_buscar)
        layout.addLayout(search_layout)
        
        # Tabla de Carrito
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(5)
        self.tabla_carrito.setHorizontalHeaderLabels(["ID", "Producto", "Precio Un.", "Cant.", "Subtotal"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_carrito.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_carrito)
        
        # Footer con totales y cobrar
        footer_layout = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 28px; font-weight: bold; color: #ff4c4c;")
        
        self.btn_cobrar = QPushButton("Cobrar Venta")
        self.btn_cobrar.setStyleSheet("padding: 15px 30px; font-size: 18px; background-color: #4caf50; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_cobrar.clicked.connect(self.procesar_venta)
        
        footer_layout.addWidget(self.lbl_total)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_cobrar)
        layout.addLayout(footer_layout)
        
    def abrir_caja(self):
        try:
            CajaManager.abrir_caja(0.0) # Monto inicial 0 por defecto para probar
            QMessageBox.information(self, "Caja", "Caja abierta exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            
    def buscar_producto(self):
        termino = self.input_buscar.text().strip()
        if not termino: return
        
        try:
            # Buscar por código exacto o nombre
            productos = ProductosManager.obtener_productos()
            encontrado = None
            
            for p in productos:
                if str(p.get('codigo_barras')) == termino or termino.lower() in p['nombre'].lower():
                    encontrado = p
                    break
                    
            if encontrado:
                self.agregar_al_carrito(encontrado)
                self.input_buscar.clear()
            else:
                QMessageBox.warning(self, "No encontrado", "Producto no encontrado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar: {str(e)}")
            
    def agregar_al_carrito(self, producto):
        # Verificar si ya está en el carrito
        for item in self.carrito:
            if item['producto_id'] == producto['id']:
                item['cantidad'] += 1
                self.actualizar_tabla_carrito()
                return
                
        # Si no está, agregarlo nuevo
        self.carrito.append({
            'producto_id': producto['id'],
            'nombre': producto['nombre'],
            'precio': float(producto['precio_contado']),
            'cantidad': 1
        })
        self.actualizar_tabla_carrito()
        
    def actualizar_tabla_carrito(self):
        self.tabla_carrito.setRowCount(0)
        total = 0.0
        
        for i, item in enumerate(self.carrito):
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            
            self.tabla_carrito.insertRow(i)
            self.tabla_carrito.setItem(i, 0, QTableWidgetItem(str(item['producto_id'])))
            self.tabla_carrito.setItem(i, 1, QTableWidgetItem(item['nombre']))
            self.tabla_carrito.setItem(i, 2, QTableWidgetItem(f"${item['precio']:.2f}"))
            self.tabla_carrito.setItem(i, 3, QTableWidgetItem(str(item['cantidad'])))
            self.tabla_carrito.setItem(i, 4, QTableWidgetItem(f"${subtotal:.2f}"))
            
        self.lbl_total.setText(f"Total: ${total:.2f}")
        
    def procesar_venta(self):
        if not self.carrito:
            QMessageBox.warning(self, "Atención", "El carrito está vacío.")
            return
            
        try:
            # Aquí idealmente se abriría un diálogo para preguntar el método de pago
            VentasManager.crear_venta(
                cliente_id=1, # Consumidor Final
                metodo_pago='Efectivo',
                productos_vendidos=self.carrito
            )
            QMessageBox.information(self, "Éxito", "Venta registrada correctamente.")
            self.carrito.clear()
            self.actualizar_tabla_carrito()
        except Exception as e:
            QMessageBox.critical(self, "Error Venta", f"No se pudo completar la venta:\n{str(e)}\n\n¿Abriste la caja primero?")
