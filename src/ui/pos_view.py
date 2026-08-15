from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QFrame, QGridLayout, QInputDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

from src.core.productos_manager import ProductosManager
from src.core.ventas_manager import VentasManager
from src.core.ventas_manager import VentasManager
from src.core.caja_manager import CajaManager
from src.core.promociones_manager import PromocionesManager
from src.core.clientes_manager import ClientesManager
from src.core.cta_cte_manager import CtaCteManager
from src.utils.impresion_ticket import ImpresoraTicket
from src.ui.buscador_productos import BuscadorProductosDialog
from src.ui.buscador_clientes import BuscadorClientesDialog

class POSView(QWidget):
    venta_realizada = pyqtSignal()
    toggle_sidebar = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.carrito = [] 
        self.cliente_id_actual = 1
        self.descuento_actual = 0.0
        self._actualizando_tabla = False
        self.init_ui()

    def verificar_caja(self):
        sesion = CajaManager.obtener_sesion_activa()
        if not sesion:
            QMessageBox.warning(self, "Caja Cerrada", "Debe abrir la caja antes de realizar ventas.")

    def crear_seccion_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 8px;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
            }
            QLabel { border: none; font-weight: 500; }
        """)
        return frame

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)
        self.setLayout(layout_principal)

        # --- 1. CABECERA: FACTURACIÓN Y CLIENTE ---
        header_frame = self.crear_seccion_frame()
        header_layout = QGridLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setVerticalSpacing(10)

        # Fila 0: Info Comprobante y Fecha
        header_layout.addWidget(QLabel("FACTURACIÓN - VENTA"), 0, 0, 1, 2)
        
        # Botón de engranaje para alternar menú
        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import QSize
        import os, sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        icon_path = os.path.join(base_path, "assets", "icons", "settings.svg")
        self.btn_toggle_menu = QPushButton()
        self.btn_toggle_menu.setIcon(QIcon(icon_path))
        self.btn_toggle_menu.setIconSize(QSize(24, 24))
        self.btn_toggle_menu.setFixedSize(40, 40)
        self.btn_toggle_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_menu.setStyleSheet("""
            QPushButton {
                background-color: #F4EFE6;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #E5DFD5;
            }
        """)
        self.btn_toggle_menu.clicked.connect(lambda: self.toggle_sidebar.emit())
        header_layout.addWidget(self.btn_toggle_menu, 0, 6, Qt.AlignmentFlag.AlignRight)

        
        # Panel derecho del comprobante (Factura B, etc)
        comprobante_frame = QFrame()
        comprobante_layout = QHBoxLayout(comprobante_frame)
        comprobante_layout.setContentsMargins(0, 0, 0, 0)
        
        cb_tipo_factura = QComboBox()
        cb_tipo_factura.addItems(["Factura B", "Factura A", "Ticket C"])
        cb_tipo_factura.setFixedWidth(100)
        
        lbl_nro_factura = QLabel("Nº 00000001")
        lbl_nro_factura.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_nro_factura.setStyleSheet("color: #000000;")
        
        comprobante_layout.addWidget(cb_tipo_factura)
        comprobante_layout.addWidget(lbl_nro_factura)
        comprobante_layout.addStretch()
        
        comprobante_frame.setVisible(False)
        header_layout.addWidget(comprobante_frame, 0, 4, 1, 2, Qt.AlignmentFlag.AlignRight)

        # Fila 1: Cliente
        header_layout.addWidget(QLabel("Código Cliente:"), 1, 0)
        
        cliente_input_layout = QHBoxLayout()
        cliente_input_layout.setContentsMargins(0, 0, 0, 0)
        cliente_input_layout.setSpacing(5)
        self.txt_cod_cliente = QLineEdit("1")
        self.txt_cod_cliente.setFixedWidth(80)
        self.txt_cod_cliente.returnPressed.connect(self.buscar_cliente)
        cliente_input_layout.addWidget(self.txt_cod_cliente)
        
        self.btn_buscar_cliente = QPushButton("Buscar (F3)")
        self.btn_buscar_cliente.setObjectName("btn_primary")

        self.btn_buscar_cliente.clicked.connect(self.abrir_buscador_clientes_f3)
        cliente_input_layout.addWidget(self.btn_buscar_cliente)
        
        header_layout.addLayout(cliente_input_layout, 1, 1)

        header_layout.addWidget(QLabel("Nombre:"), 1, 2)
        self.txt_nombre_cliente = QLineEdit("CONSUMIDOR FINAL")
        self.txt_nombre_cliente.setReadOnly(True)
        header_layout.addWidget(self.txt_nombre_cliente, 1, 3, 1, 3)

        # Fila 2: Domicilio, Localidad, Condición
        header_layout.addWidget(QLabel("Domicilio:"), 2, 0)
        self.txt_domicilio = QLineEdit("")
        self.txt_domicilio.setReadOnly(True)
        header_layout.addWidget(self.txt_domicilio, 2, 1, 1, 2)

        header_layout.addWidget(QLabel("Cond. IVA:"), 2, 3)
        self.txt_cond_iva = QLineEdit("Consumidor Final")
        self.txt_cond_iva.setReadOnly(True)
        header_layout.addWidget(self.txt_cond_iva, 2, 4)

        header_layout.addWidget(QLabel("CUIT/DNI:"), 2, 5)
        self.txt_cuit = QLineEdit("00000000000")
        self.txt_cuit.setReadOnly(True)
        header_layout.addWidget(self.txt_cuit, 2, 6)

        layout_principal.addWidget(header_frame)

        # --- 2. INPUT DE PRODUCTO Y TIPO DE CONSUMO ---
        input_layout = QVBoxLayout()
        
        # --- 2. INPUT DE PRODUCTO ---
        input_layout = QVBoxLayout()
        
        # Buscador
        search_bar_layout = QHBoxLayout()
        self.txt_codigo = QLineEdit()
        self.txt_codigo
        self.txt_codigo.setFont(QFont("Segoe UI", 16))
        self.txt_codigo.setPlaceholderText("Ingrese Código de Barras o Artículo y presione Enter (F2 para buscar)...")
        self.txt_codigo.setMinimumHeight(50)
        self.txt_codigo.returnPressed.connect(self.buscar_y_agregar_producto)
        search_bar_layout.addWidget(self.txt_codigo)
        
        input_layout.addLayout(search_bar_layout)
        layout_principal.addLayout(input_layout)

        # --- 3. GRILLA DE PRODUCTOS ---
        self.tabla_carrito = QTableWidget(0, 6)
        self.tabla_carrito.setHorizontalHeaderLabels(["Código", "Descripción", "Talle", "Cantidad", "P. Unitario", "Importe"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_carrito.setFont(QFont("Segoe UI", 12))
        self.tabla_carrito.verticalHeader().setVisible(False)
        self.tabla_carrito.verticalHeader().setDefaultSectionSize(40)
        self.tabla_carrito.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_carrito.itemChanged.connect(self.al_cambiar_celda)
        layout_principal.addWidget(self.tabla_carrito)

        # Panel inferior responsivo
        bottom_frame = self.crear_seccion_frame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(10)

        # Vendedor e Info adicional
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.addWidget(QLabel("Vendedor: 01 - Principal"))
        lbl_shortcuts = QLabel("[F5] Cobrar   |   [F12] Cancelar Venta   |   [Supr] Eliminar Fila")
        lbl_shortcuts.setStyleSheet("color: #666666; font-size: 11px;")
        info_layout.addWidget(lbl_shortcuts)
        bottom_layout.addLayout(info_layout, 2)

        # Botones de Acción
        self.btn_cobrar = QPushButton("COBRAR (F5)")
        self.btn_cobrar.setObjectName("btn_primary")
        self.btn_cobrar.setMinimumSize(120, 50)
        self.btn_cobrar.setStyleSheet("""
            QPushButton { background-color: #B09886; color: #FFFFFF; font-weight: bold; font-size: 15px; border-radius: 8px; border: none;}
            QPushButton:hover { background-color: #9C8573; }
        """)
        self.btn_cobrar.clicked.connect(self.cobrar_venta)

        self.btn_cancelar = QPushButton("CANCELAR (F12)")
        self.btn_cancelar.setObjectName("btn_danger")
        self.btn_cancelar.setMinimumSize(120, 50)
        self.btn_cancelar.setStyleSheet("""
            QPushButton { background-color: #D99890; color: #FFFFFF; font-weight: bold; font-size: 15px; border-radius: 8px; border: none;}
            QPushButton:hover { background-color: #C5847C; }
        """)
        self.btn_cancelar.clicked.connect(self.cancelar_venta)

        bottom_layout.addWidget(self.btn_cobrar)
        bottom_layout.addWidget(self.btn_cancelar)

        # Selector de Medio de Pago
        pago_layout = QVBoxLayout()
        pago_layout.setSpacing(2)
        pago_layout.addWidget(QLabel("Medio de Pago:"))
        self.cb_medio_pago = QComboBox()
        self.cb_medio_pago.addItems(["EFECTIVO", "TRANSFERENCIA", "TARJETA", "MIXTO", "FIADO / CTA. CTE."])
        self.cb_medio_pago.setStyleSheet("font-size: 13px; font-weight: bold; padding: 2px;")
        self.cb_medio_pago.setFixedHeight(36)
        self.cb_medio_pago.setMinimumWidth(140)
        self.cb_medio_pago.currentIndexChanged.connect(self.actualizar_tabla)
        pago_layout.addWidget(self.cb_medio_pago)
        pago_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        bottom_layout.addLayout(pago_layout)

        # Contenedor para el total
        total_layout = QVBoxLayout()
        total_layout.setSpacing(0)
        
        self.lbl_descuento = QLabel("")
        self.lbl_descuento.setFont(QFont("Segoe UI", 10))
        self.lbl_descuento.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.lbl_descuento.setStyleSheet("color: #D99890;")
        
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_total.setStyleSheet("color: #000000; padding: 0px 2px;")
        
        total_layout.addWidget(self.lbl_descuento)
        total_layout.addWidget(self.lbl_total)
        
        bottom_layout.addLayout(total_layout, 3)

        layout_principal.addWidget(bottom_frame)

        # --- Atajos ---
        QShortcut(QKeySequence("F5"), self, self.cobrar_venta)
        QShortcut(QKeySequence("F12"), self, self.cancelar_venta)
        QShortcut(QKeySequence("F2"), self, self.abrir_buscador_f2)
        QShortcut(QKeySequence("F3"), self, self.abrir_buscador_clientes_f3)
        QShortcut(QKeySequence("Delete"), self, self.eliminar_fila)

        self.txt_codigo.setFocus()

    def eliminar_fila(self):
        row = self.tabla_carrito.currentRow()
        if row >= 0:
            del self.carrito[row]
            self.procesar_promociones()
            self.actualizar_tabla()
            self.txt_codigo.setFocus()

    def abrir_buscador_f2(self):
        dialog = BuscadorProductosDialog(self)
        if dialog.exec():
            if dialog.codigo_seleccionado:
                self.txt_codigo.setText(dialog.codigo_seleccionado)
                self.buscar_y_agregar_producto()
        self.txt_codigo.setFocus()

    def abrir_buscador_clientes_f3(self):
        dialog = BuscadorClientesDialog(self)
        if dialog.exec():
            if dialog.cliente_id_seleccionado:
                self.txt_cod_cliente.setText(str(dialog.cliente_id_seleccionado))
                self.buscar_cliente()
        self.txt_codigo.setFocus()

    def buscar_cliente(self):
        try:
            cod_cliente = int(self.txt_cod_cliente.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "El código de cliente debe ser numérico.")
            self.txt_cod_cliente.setText(str(self.cliente_id_actual))
            return

        cliente = ClientesManager.get_by_id(cod_cliente)
        if cliente:
            self.cliente_id_actual = cliente['id']
            self.descuento_actual = cliente.get('descuento_porcentaje', 0.0)
            
            saldo = CtaCteManager.get_saldo(cliente['id'])
            if saldo < 0:
                self.txt_nombre_cliente.setText(f"{cliente['nombre']} (A favor: ${abs(saldo):.2f})")
            else:
                self.txt_nombre_cliente.setText(cliente['nombre'])
                
            self.txt_domicilio.setText(cliente['domicilio'])
            self.txt_cond_iva.setText(cliente['condicion_iva'])
            self.txt_cuit.setText(cliente['cuit'])
            self.txt_codigo.setFocus()
            self.actualizar_tabla()
        else:
            QMessageBox.warning(self, "No Encontrado", f"No se encontró un cliente con el código {cod_cliente}.")
            # Restaurar al último cliente válido
            self.txt_cod_cliente.setText(str(self.cliente_id_actual))
            self.actualizar_tabla()

    def buscar_y_agregar_producto(self):
        codigo = self.txt_codigo.text().strip()
        if not codigo:
            return

        if codigo.startswith("P-"):
            try:
                promo_id = int(codigo.split("-")[1])
                promos = PromocionesManager.get_all()
                promo = next((p for p in promos if p['id'] == promo_id), None)
                if promo:
                    encontrada = False
                    for item in self.carrito:
                        if item.get('es_promo') and item['promocion_id'] == promo['id']:
                            item['cantidad'] += 1
                            encontrada = True
                            break
                    if not encontrada:
                        self.carrito.append({
                            'producto_id': None,
                            'promocion_id': promo['id'],
                            'codigo_barras': promo.get('codigo_barras') or '[COMBO]',
                            'nombre': "PROMO: " + promo['nombre'],
                            'cantidad': 1,
                            'precio_unitario': promo['precio_fijo'],
                            'es_promo': True,
                            'detalles': promo['detalles']
                        })
                    self.procesar_promociones()
                    self.actualizar_tabla()
                    self.txt_codigo.clear()
                    self.txt_codigo.setFocus()
                    return
            except ValueError:
                pass

        # Buscar por código de barras de promo
        promos = PromocionesManager.get_all()
        promo_por_cb = next((p for p in promos if p.get('codigo_barras') == codigo), None)
        if promo_por_cb:
            encontrada = False
            for item in self.carrito:
                if item.get('es_promo') and item['promocion_id'] == promo_por_cb['id']:
                    item['cantidad'] += 1
                    encontrada = True
                    break
            if not encontrada:
                self.carrito.append({
                    'producto_id': None,
                    'promocion_id': promo_por_cb['id'],
                    'codigo_barras': promo_por_cb.get('codigo_barras') or '[COMBO]',
                    'nombre': "PROMO: " + promo_por_cb['nombre'],
                    'cantidad': 1,
                    'precio_unitario': promo_por_cb['precio_fijo'],
                    'es_promo': True,
                    'detalles': promo_por_cb['detalles']
                })
            self.procesar_promociones()
            self.actualizar_tabla()
            self.txt_codigo.clear()
            self.txt_codigo.setFocus()
            return


        from src.core.cache_manager import DataCache
        productos_cache = DataCache.get_productos()
        producto = next((p for p in productos_cache if p.get('codigo_barras') == codigo or str(p['id']) == codigo), None)
        if not producto:
            producto = ProductosManager.get_by_codigo(codigo)
        if not producto:
            QMessageBox.warning(self, "No Encontrado", f"Artículo no encontrado: {codigo}")
            self.txt_codigo.clear()
            return

        # Determinar el precio
        precio_a_cobrar = float(producto['precio_contado'])
        
        # Verificar si ya está en el carrito para sumar cantidad (y chequear que sea el mismo precio)
        encontrado = False
        for item in self.carrito:
            if item['producto_id'] == producto['id'] and item['precio_unitario'] == precio_a_cobrar:
                item['cantidad'] += 1
                encontrado = True
                break
        
        if not encontrado:
            self.carrito.append({
                'producto_id': producto['id'],
                'codigo_barras': producto['codigo_barras'],
                'nombre': producto['nombre'],
                'talle': producto.get('talle') or "",
                'cantidad': 1,
                'precio_unitario': precio_a_cobrar,
                'es_promo': False
            })

        self.procesar_promociones()
        self.actualizar_tabla()
        self.txt_codigo.clear()
        self.txt_codigo.setFocus()

    def actualizar_precios_carrito(self):
        pass

    def procesar_promociones(self):
        promos = PromocionesManager.get_all()
        if not promos:
            return

        cambio = True
        while cambio:
            cambio = False
            for promo in promos:
                # Verificar si tenemos los items requeridos
                cumple_promo = True
                items_a_consumir = []
                
                for det in promo['detalles']:
                    req_id = det['producto_id']
                    req_cant = det['cantidad_requerida']
                    
                    # Buscar en el carrito
                    cant_en_carrito = 0
                    for item in self.carrito:
                        if not item.get('es_promo') and item['producto_id'] == req_id:
                            cant_en_carrito += item['cantidad']
                    
                    if cant_en_carrito < req_cant:
                        cumple_promo = False
                        break
                    else:
                        items_a_consumir.append({'id': req_id, 'cant': req_cant})
                
                if cumple_promo:
                    # Aplicar promo
                    cambio = True
                    # Restar cantidades
                    for cons in items_a_consumir:
                        cant_a_restar = cons['cant']
                        for item in self.carrito:
                            if not item.get('es_promo') and item['producto_id'] == cons['id']:
                                if item['cantidad'] >= cant_a_restar:
                                    item['cantidad'] -= cant_a_restar
                                    cant_a_restar = 0
                                else:
                                    cant_a_restar -= item['cantidad']
                                    item['cantidad'] = 0
                                if cant_a_restar == 0:
                                    break
                    
                    # Limpiar items con cantidad 0
                    self.carrito = [item for item in self.carrito if item['cantidad'] > 0]
                    
                    # Verificar si la promo ya existe para sumar cantidad
                    encontrada = False
                    for item in self.carrito:
                        if item.get('es_promo') and item['nombre'] == "PROMO: " + promo['nombre']:
                            item['cantidad'] += 1
                            encontrada = True
                            break
                            
                    if not encontrada:
                        self.carrito.append({
                            'producto_id': None,
                            'promocion_id': promo['id'],
                            'codigo_barras': promo.get('codigo_barras') or '[COMBO]',
                            'nombre': "PROMO: " + promo['nombre'],
                            'cantidad': 1,
                            'precio_unitario': promo['precio_fijo'],
                            'es_promo': True,
                            'detalles': promo['detalles']
                        })
                    break # Restart loop since cart changed

    def actualizar_tabla(self):
        self._actualizando_tabla = True
        self.tabla_carrito.setRowCount(0)
        total = 0.0
        for item in self.carrito:
            row_idx = self.tabla_carrito.rowCount()
            self.tabla_carrito.insertRow(row_idx)
            
            subtotal = item['cantidad'] * item['precio_unitario']
            total += subtotal

            # Crear items
            item_cod = QTableWidgetItem(item['codigo_barras'])
            item_desc = QTableWidgetItem(item['nombre'])
            item_talle = QTableWidgetItem(item.get('talle') or "")
            item_cant = QTableWidgetItem(f"{item['cantidad']:g}")
            item_pu = QTableWidgetItem(f"{item['precio_unitario']:.2f}")
            item_imp = QTableWidgetItem(f"{subtotal:.2f}")

            # Solo la cantidad (columna 3) es editable, el resto bloqueado
            item_cod.setFlags(item_cod.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_talle.setFlags(item_talle.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.get('es_promo'):
                item_cant.setFlags(item_cant.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_pu.setFlags(item_pu.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_imp.setFlags(item_imp.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.tabla_carrito.setItem(row_idx, 0, item_cod)
            self.tabla_carrito.setItem(row_idx, 1, item_desc)
            self.tabla_carrito.setItem(row_idx, 2, item_talle)
            self.tabla_carrito.setItem(row_idx, 3, item_cant)
            self.tabla_carrito.setItem(row_idx, 4, item_pu)
            self.tabla_carrito.setItem(row_idx, 5, item_imp)

        medio_pago = self.cb_medio_pago.currentText()
        descuento_medio_pago = 30.0 if medio_pago in ["EFECTIVO", "TRANSFERENCIA"] else 0.0
        pct_descuento_total = self.descuento_actual + descuento_medio_pago

        if pct_descuento_total > 0:
            descuento_monto = total * (pct_descuento_total / 100.0)
            total_final = total - descuento_monto
            
            detalles_desc = []
            if descuento_medio_pago > 0:
                detalles_desc.append(f"Desc. {medio_pago} (30%)")
            if self.descuento_actual > 0:
                detalles_desc.append(f"Desc. Cliente ({self.descuento_actual:.0f}%)")
            
            lbl_desc_str = " + ".join(detalles_desc)
            self.lbl_descuento.setText(f"Precio Lista: ${total:.2f} | {lbl_desc_str}: -${descuento_monto:.2f}")
            self.lbl_total.setText(f"${total_final:.2f}")
        else:
            self.lbl_descuento.setText(f"Precio Lista: ${total:.2f}")
            self.lbl_total.setText(f"${total:.2f}")
        self._actualizando_tabla = False

    def al_cambiar_celda(self, item):
        if self._actualizando_tabla:
            return
            
        row = item.row()
        col = item.column()
        
        if col == 3: # Columna Cantidad (antes era 2)
            try:
                texto_cant = item.text().replace(',', '.')
                nueva_cantidad = float(texto_cant)
                if nueva_cantidad <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Error", "La cantidad debe ser un número mayor a 0.")
                self.actualizar_tabla()
                return

            if row < len(self.carrito):
                self.carrito[row]['cantidad'] = nueva_cantidad
                self.procesar_promociones()
                self.actualizar_tabla()

    def resetear_estado_venta(self):
        self.carrito.clear()
        self.txt_cod_cliente.setText("1")
        self.buscar_cliente()
        self.cb_medio_pago.setCurrentText("EFECTIVO")
        self.txt_codigo.clear()
        self.txt_codigo.setFocus()

    def cancelar_venta(self):
        if self.carrito:
            reply = QMessageBox.question(self, "Cancelar Venta", "¿Está seguro de cancelar la venta actual?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.resetear_estado_venta()
        else:
            self.resetear_estado_venta()
        self.txt_codigo.setFocus()

    def cobrar_venta(self):
        if not self.carrito:
            QMessageBox.warning(self, "Vacio", "No hay artículos para cobrar.")
            self.txt_codigo.setFocus()
            return

        try:
            metodo_pago_seleccionado = self.cb_medio_pago.currentText()

            if metodo_pago_seleccionado == "FIADO / CTA. CTE." and self.cliente_id_actual == 1:
                QMessageBox.warning(self, "Error", "No se puede fiar al 'Consumidor Final'. Debe seleccionar o crear un Cliente específico.")
                return

            total_venta = 0.0
            for item in self.carrito:
                total_venta += item['cantidad'] * item['precio_unitario']
                
            descuento_medio_pago = 30.0 if metodo_pago_seleccionado in ["EFECTIVO", "TRANSFERENCIA"] else 0.0
            pct_descuento_total = self.descuento_actual + descuento_medio_pago
            
            descuento_monto = total_venta * (pct_descuento_total / 100.0)
            total_final = total_venta - descuento_monto
            
            if metodo_pago_seleccionado == "EFECTIVO":
                pago, ok = QInputDialog.getDouble(
                    self, 
                    "Cobro en Efectivo", 
                    f"Total a cobrar: ${total_final:.2f}\n\n¿Cuánto efectivo entrega el cliente?", 
                    total_final, 0.0, 10000000.0, 2
                )
                if not ok:
                    return # Canceló el cobro
                if pago < total_final:
                    QMessageBox.warning(self, "Error", f"El monto entregado (${pago:.2f}) es menor al total de la venta (${total_final:.2f}).")
                    return
                vuelto = pago - total_final
                montos_mixto = None

            elif metodo_pago_seleccionado == "MIXTO":
                # Pedimos la parte en Efectivo
                monto_efectivo, ok = QInputDialog.getDouble(
                    self, 
                    "Cobro Mixto", 
                    f"Total a cobrar: ${total_final:.2f}\n\n¿Cuánto entrega en EFECTIVO? (El resto será TRANSFERENCIA)", 
                    0.0, 0.0, total_final, 2
                )
                if not ok:
                    return # Canceló el cobro
                
                monto_transferencia = total_final - monto_efectivo
                montos_mixto = {
                    'EFECTIVO': monto_efectivo,
                    'TRANSFERENCIA': monto_transferencia
                }
                vuelto = 0.0

            else:
                montos_mixto = None
                vuelto = 0.0
                
            resultado = VentasManager.procesar_venta(
                cliente_id=self.cliente_id_actual,
                metodo_pago=metodo_pago_seleccionado,
                carrito=self.carrito,
                montos_mixto=montos_mixto
            )
            
            ImpresoraTicket.imprimir(
                venta_id=resultado["venta_id"],
                carrito=self.carrito,
                subtotal=resultado["subtotal"],
                descuento=resultado["descuento"],
                total=resultado["total"],
                empresa_nombre="Albina Accesorios"
            )
            
            if metodo_pago_seleccionado == "EFECTIVO":
                QMessageBox.information(self, "Venta Exitosa", f"Vuelto a entregar: ${vuelto:.2f}\n\nFactura #{resultado['venta_id']} generada.\nImprimiendo...")
            else:
                QMessageBox.information(self, "Venta Exitosa", f"Factura #{resultado['venta_id']} generada.\nImprimiendo...")
                
            self.resetear_estado_venta()
            self.venta_realizada.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al procesar:\n{str(e)}")
        
        self.txt_codigo.setFocus()
