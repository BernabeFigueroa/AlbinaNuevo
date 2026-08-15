from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QFrame, QGridLayout, QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

class NumericLineEdit(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

from src.core.productos_manager import ProductosManager
from src.core.categorias_manager import CategoriasManager
from src.core.proveedores_manager import ProveedoresManager

class ProductosView(QWidget):
    def __init__(self):
        super().__init__()
        self.producto_seleccionado_id = None
        self.init_ui()
        self.cargar_combos()
        self.cargar_grilla()

    def crear_seccion_frame(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 8px;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
            }
            QLabel { border: none; font-weight: 500; font-size: 14px; }
        """)
        return frame

    def cargar_combos(self):
        from src.core.cache_manager import DataCache
        # Guardar selecciones actuales
        cur_cat = self.cb_categoria.currentData() if hasattr(self, 'cb_categoria') else None
        cur_prov = self.cb_proveedor.currentData() if hasattr(self, 'cb_proveedor') else None
        cur_filtro_cat = self.cb_filtro_categoria.currentData() if hasattr(self, 'cb_filtro_categoria') else None
        cur_filtro_prov = self.cb_filtro_proveedor.currentData() if hasattr(self, 'cb_filtro_proveedor') else None

        cats = DataCache.get_categorias()
        provs = DataCache.get_proveedores()

        if hasattr(self, 'cb_categoria'):
            self.cb_categoria.blockSignals(True)
            self.cb_categoria.clear()
            self.cb_categoria.addItem("-- Ninguno --", None)
            for c in cats:
                self.cb_categoria.addItem(c['nombre'], c['id'])
            if cur_cat is not None:
                idx = self.cb_categoria.findData(cur_cat)
                if idx >= 0: self.cb_categoria.setCurrentIndex(idx)
            self.cb_categoria.blockSignals(False)
            
        if hasattr(self, 'cb_proveedor'):
            self.cb_proveedor.blockSignals(True)
            self.cb_proveedor.clear()
            self.cb_proveedor.addItem("-- Ninguno --", None)
            for p in provs:
                self.cb_proveedor.addItem(p['nombre'], p['id'])
            if cur_prov is not None:
                idx = self.cb_proveedor.findData(cur_prov)
                if idx >= 0: self.cb_proveedor.setCurrentIndex(idx)
            self.cb_proveedor.blockSignals(False)

        if hasattr(self, 'cb_filtro_categoria'):
            self.cb_filtro_categoria.blockSignals(True)
            self.cb_filtro_categoria.clear()
            self.cb_filtro_categoria.addItem("Todos", None)
            for c in cats:
                self.cb_filtro_categoria.addItem(c['nombre'], c['id'])
            if cur_filtro_cat is not None:
                idx = self.cb_filtro_categoria.findData(cur_filtro_cat)
                if idx >= 0: self.cb_filtro_categoria.setCurrentIndex(idx)
            self.cb_filtro_categoria.blockSignals(False)
            
        if hasattr(self, 'cb_filtro_proveedor'):
            self.cb_filtro_proveedor.blockSignals(True)
            self.cb_filtro_proveedor.clear()
            self.cb_filtro_proveedor.addItem("Todos", None)
            for p in provs:
                self.cb_filtro_proveedor.addItem(p['nombre'], p['id'])
            if cur_filtro_prov is not None:
                idx = self.cb_filtro_proveedor.findData(cur_filtro_prov)
                if idx >= 0: self.cb_filtro_proveedor.setCurrentIndex(idx)
            self.cb_filtro_proveedor.blockSignals(False)

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(8)
        self.setLayout(layout_principal)

        lbl_titulo = QLabel("MANTENIMIENTO DE ARTÍCULOS")
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #000000;")
        layout_principal.addWidget(lbl_titulo)

        # --- PANEL SUPERIOR: FORMULARIO ---
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0,0,0,0)
        form_layout.setSpacing(8)

        # Un solo contenedor para el formulario
        g_frame = self.crear_seccion_frame()
        g_layout = QGridLayout(g_frame)
        g_layout.setContentsMargins(15, 15, 15, 15)
        g_layout.setVerticalSpacing(12)
        g_layout.setHorizontalSpacing(15)

        # Fila 0
        g_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.txt_descripcion = QLineEdit()
        g_layout.addWidget(self.txt_descripcion, 0, 1, 1, 3)

        g_layout.addWidget(QLabel("Cód. Barras:"), 0, 4)
        self.txt_codigo_barras = QLineEdit()
        g_layout.addWidget(self.txt_codigo_barras, 0, 5)

        # Referencias ocultas para compatibilidad
        self.txt_codigo_interno = QLineEdit("[ Automático ]")
        self.txt_codigo_interno.setVisible(False)
        self.txt_codigo_fabrica = QLineEdit()
        self.txt_codigo_fabrica.setVisible(False)

        # Fila 1
        g_layout.addWidget(QLabel("Categoría:"), 1, 0)
        self.cb_categoria = QComboBox()
        g_layout.addWidget(self.cb_categoria, 1, 1)

        g_layout.addWidget(QLabel("Proveedor:"), 1, 2)
        self.cb_proveedor = QComboBox()
        g_layout.addWidget(self.cb_proveedor, 1, 3)

        g_layout.addWidget(QLabel("Talle:"), 1, 4)
        self.txt_talle = QLineEdit("")
        g_layout.addWidget(self.txt_talle, 1, 5)

        # Fila 2
        g_layout.addWidget(QLabel("Costo:"), 2, 0)
        self.txt_costo_lista = NumericLineEdit("0.00")
        g_layout.addWidget(self.txt_costo_lista, 2, 1)

        g_layout.addWidget(QLabel("Flete:"), 2, 2)
        self.txt_flete = NumericLineEdit("0.00")
        g_layout.addWidget(self.txt_flete, 2, 3)

        g_layout.addWidget(QLabel("Utilidad (%):"), 2, 4)
        self.txt_utilidad = NumericLineEdit("0.00")
        g_layout.addWidget(self.txt_utilidad, 2, 5)

        # Fila 3
        g_layout.addWidget(QLabel("Precio Venta:"), 3, 0)
        self.txt_precio_contado = NumericLineEdit("0.00")
        g_layout.addWidget(self.txt_precio_contado, 3, 1)

        g_layout.addWidget(QLabel("Stock Actual:"), 3, 2)
        self.txt_stock_actual = NumericLineEdit("0")
        g_layout.addWidget(self.txt_stock_actual, 3, 3)

        g_layout.addWidget(QLabel("Stock Mín / Máx:"), 3, 4)
        min_max_layout = QHBoxLayout()
        min_max_layout.setContentsMargins(0, 0, 0, 0)
        min_max_layout.setSpacing(5)
        self.txt_stock_min = NumericLineEdit("5")
        self.txt_stock_max = NumericLineEdit("100")
        min_max_layout.addWidget(self.txt_stock_min)
        min_max_layout.addWidget(self.txt_stock_max)
        g_layout.addLayout(min_max_layout, 3, 5)

        # Fila 4: Trazabilidad (Solo visible para Administradores)
        from src.core.auth_manager import AuthManager
        self.lbl_trazabilidad_titulo = QLabel("Modificado por:")
        self.lbl_trazabilidad_titulo.setStyleSheet("font-weight: bold; color: #7A7067; font-size: 12px;")
        
        self.lbl_modificado_por = QLabel("Sin modificaciones registradas")
        self.lbl_modificado_por.setStyleSheet("color: #2C2520; font-size: 12px; font-weight: 600; font-style: italic;")
        
        es_admin = AuthManager.is_admin()
        self.lbl_trazabilidad_titulo.setVisible(es_admin)
        self.lbl_modificado_por.setVisible(es_admin)

        g_layout.addWidget(self.lbl_trazabilidad_titulo, 4, 0)
        g_layout.addWidget(self.lbl_modificado_por, 4, 1, 1, 5)

        # Ocultos
        self.txt_precio_tarjeta = NumericLineEdit("0.00")
        self.txt_precio_tarjeta.setVisible(False)
        self.txt_ubicacion = QLineEdit("")
        self.txt_ubicacion.setVisible(False)
        self.lbl_creado_por = QLabel("-")
        self.lbl_creado_por.setVisible(False)
        
        from src.core.auth_manager import AuthManager
        self.lbl_modificado_por = QLabel("-")
        if AuthManager.is_admin():
            lbl_mod = QLabel("Modificado por:")
            lbl_mod.setStyleSheet("color: #7A7067; font-size: 11px;")
            self.lbl_modificado_por.setStyleSheet("color: #7A7067; font-size: 11px; font-weight: bold;")
            g_layout.addWidget(lbl_mod, 4, 4, Qt.AlignmentFlag.AlignRight)
            g_layout.addWidget(self.lbl_modificado_por, 4, 5)
        else:
            self.lbl_modificado_por.setVisible(False)

        form_layout.addWidget(g_frame)

        # Conectar señales para cálculos dinámicos
        self.txt_costo_lista.textEdited.connect(self.calcular_precios_desde_costo)
        self.txt_flete.textEdited.connect(self.calcular_precios_desde_costo)
        self.txt_utilidad.textEdited.connect(self.calcular_precios_desde_costo)
        self.txt_precio_contado.textEdited.connect(self.calcular_utilidad_desde_precio)

        # --- BOTONES DE ACCIÓN ---
        btn_layout = QHBoxLayout()
        
        self.btn_limpiar = QPushButton("Limpiar/Nuevo")
        self.btn_limpiar.setObjectName("btn_neutral")

        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("btn_danger")

        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_eliminar.setEnabled(False)

        self.btn_restaurar = QPushButton("Restaurar")
        self.btn_restaurar.setObjectName("btn_primary")

        self.btn_restaurar.clicked.connect(self.restaurar_producto)
        self.btn_restaurar.setVisible(False)

        self.btn_ficha = QPushButton("Ver Ficha")
        self.btn_ficha.setObjectName("btn_neutral")

        self.btn_ficha.clicked.connect(self.ver_ficha_producto)
        self.btn_ficha.setEnabled(False)

        self.btn_imprimir_etiqueta = QPushButton("Imprimir Etiqueta")
        self.btn_imprimir_etiqueta.setObjectName("btn_neutral")
        self.btn_imprimir_etiqueta.clicked.connect(self.abrir_impresor_etiquetas)

        self.btn_grabar = QPushButton("Guardar (F5)")
        self.btn_grabar.setObjectName("btn_primary")

        self.btn_grabar.clicked.connect(self.grabar_producto)
        
        self.shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        self.shortcut_f5.activated.connect(self.grabar_producto)
        self.shortcut_f5.setContext(Qt.ShortcutContext.WindowShortcut)
        
        self.btn_duplicar = QPushButton("Duplicar")
        self.btn_duplicar.setObjectName("btn_primary")

        self.btn_duplicar.clicked.connect(self.duplicar_producto)

        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addWidget(self.btn_restaurar)
        btn_layout.addWidget(self.btn_ficha)
        btn_layout.addWidget(self.btn_imprimir_etiqueta)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_duplicar)
        btn_layout.addWidget(self.btn_grabar)

        form_layout.addLayout(btn_layout)
        
        layout_principal.addWidget(form_widget)

        # --- PANEL INFERIOR: GRILLA ---
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setContentsMargins(0,0,0,0)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Búsqueda:"))
        self.txt_buscar = QLineEdit()
        self.txt_buscar
        self.txt_buscar.setPlaceholderText("Nombre, Código o ID...")
        self.txt_buscar.textChanged.connect(self.filtrar_grilla)
        search_layout.addWidget(self.txt_buscar)
        
        search_layout.addWidget(QLabel("Rubro:"))
        self.cb_filtro_categoria = QComboBox()

        self.cb_filtro_categoria.currentIndexChanged.connect(lambda _: self.filtrar_grilla(self.txt_buscar.text()))
        search_layout.addWidget(self.cb_filtro_categoria)

        search_layout.addWidget(QLabel("Proveedor:"))
        self.cb_filtro_proveedor = QComboBox()

        self.cb_filtro_proveedor.currentIndexChanged.connect(lambda _: self.filtrar_grilla(self.txt_buscar.text()))
        search_layout.addWidget(self.cb_filtro_proveedor)
        
        self.chk_inactivos = QCheckBox("Ver eliminados")
        self.chk_inactivos.setStyleSheet("color: #D99890; font-weight: bold;")
        self.chk_inactivos.stateChanged.connect(lambda _: self.cargar_grilla(self.txt_buscar.text()))
        search_layout.addWidget(self.chk_inactivos)
        
        grid_layout.addLayout(search_layout)

        self.tabla = QTableWidget(0, 5)

        self.tabla.setHorizontalHeaderLabels(["Código", "Descripción", "Talle", "Precio", "Stock"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(True)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.cellDoubleClicked.connect(self.cargar_producto_para_edicion)
        grid_layout.addWidget(self.tabla)

        layout_principal.addWidget(grid_widget, 1)

    def calcular_precios_desde_costo(self, text=""):
        try:
            costo = float(self.txt_costo_lista.text() or 0)
            flete = float(self.txt_flete.text() or 0)
            utilidad = float(self.txt_utilidad.text() or 0)
            
            costo_final = costo + flete
            precio_contado = costo_final * (1 + (utilidad / 100))
            self.txt_precio_contado.blockSignals(True)
            self.txt_precio_contado.setText(f"{precio_contado:.2f}")
            self.txt_precio_contado.blockSignals(False)

            # Ya no obligamos al precio tarjeta (Local) a ser un +51%, 
            # solo lo pre-llenamos con algo razonable si está en 0 para ayudar.
            if not self.txt_precio_tarjeta.text() or float(self.txt_precio_tarjeta.text() or 0) == 0:
                self.txt_precio_tarjeta.setText(f"{precio_contado:.2f}")

        except ValueError:
            pass

    def calcular_utilidad_desde_precio(self, text=""):
        try:
            costo = float(self.txt_costo_lista.text() or 0)
            flete = float(self.txt_flete.text() or 0)
            precio_contado = float(self.txt_precio_contado.text() or 0)
            
            costo_final = costo + flete
            if costo_final > 0:
                utilidad = ((precio_contado / costo_final) - 1) * 100
            else:
                utilidad = 100.0

            self.txt_utilidad.blockSignals(True)
            self.txt_utilidad.setText(f"{utilidad:.2f}")
            self.txt_utilidad.blockSignals(False)

            if not self.txt_precio_tarjeta.text() or float(self.txt_precio_tarjeta.text() or 0) == 0:
                self.txt_precio_tarjeta.setText(f"{precio_contado:.2f}")

        except ValueError:
            pass

    def cargar_grilla(self, filtro=""):
        try:
            from src.core.cache_manager import DataCache
            self.tabla.setUpdatesEnabled(False)
            self.tabla.setRowCount(0)
            incluir_inactivos = hasattr(self, 'chk_inactivos') and self.chk_inactivos.isChecked()
            productos = DataCache.get_productos(incluir_inactivos=incluir_inactivos) or []
            
            cat_filtro = self.cb_filtro_categoria.currentData() if hasattr(self, 'cb_filtro_categoria') else None
            prov_filtro = self.cb_filtro_proveedor.currentData() if hasattr(self, 'cb_filtro_proveedor') else None

            for p in productos:
                if not isinstance(p, dict):
                    continue
                if cat_filtro and p.get('categoria_id') != cat_filtro:
                    continue
                    
                if prov_filtro and p.get('proveedor_id') != prov_filtro:
                    continue
                    
                if filtro:
                    filtro_lower = filtro.lower()
                    nombre_str = str(p.get('nombre') or '').lower()
                    cb_str = str(p.get('codigo_barras') or '').lower()
                    talle_str = str(p.get('talle') or '').lower()
                    id_str = str(p.get('id') or '')
                    
                    if (filtro_lower not in nombre_str and 
                        filtro_lower not in cb_str and 
                        filtro_lower not in talle_str and 
                        filtro_lower != id_str):
                        continue
                
                row_idx = self.tabla.rowCount()
                self.tabla.insertRow(row_idx)
                
                # Mostrar ID interno como el código y centrarlo
                prod_id = p.get('id', 0)
                codigo_mostrar = str(prod_id)
                item_codigo = QTableWidgetItem(codigo_mostrar)
                item_codigo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_codigo.setData(Qt.ItemDataRole.UserRole, prod_id) # ID Oculto
                self.tabla.setItem(row_idx, 0, item_codigo)
                
                nombre_val = str(p.get('nombre') or 'Sin nombre')
                item_nombre = QTableWidgetItem(nombre_val)
                if p.get('activo', 1) == 0:
                    item_nombre.setForeground(Qt.GlobalColor.red)
                    item_nombre.setText(f"{nombre_val} (ELIMINADO)")
                    
                self.tabla.setItem(row_idx, 1, item_nombre)
                self.tabla.setItem(row_idx, 2, QTableWidgetItem(str(p.get('talle') or "")))
                
                # Conversión segura de precio
                try:
                    precio = float(p.get('precio_contado') or 0.0)
                except (ValueError, TypeError):
                    precio = 0.0
                self.tabla.setItem(row_idx, 3, QTableWidgetItem(f"{precio:.2f}"))
                
                # Conversión segura de stock
                stock_val = p.get('stock_actual', 0)
                self.tabla.setItem(row_idx, 4, QTableWidgetItem(str(stock_val if stock_val is not None else 0)))
        except Exception as e:
            print(f"Error cargando grilla de productos: {e}")
        finally:
            self.tabla.setUpdatesEnabled(True)

    def filtrar_grilla(self, texto):
        self.cargar_grilla(texto)

    def cargar_producto_para_edicion(self, row, col):
        item_codigo = self.tabla.item(row, 0)
        if not item_codigo: return
        producto_id = item_codigo.data(Qt.ItemDataRole.UserRole)
        producto = ProductosManager.get_by_id(producto_id)
        if not producto:
            return
            
        self.producto_seleccionado_id = producto['id']
        self.txt_codigo_interno.setText(str(producto['id']))
        self.txt_codigo_barras.setText(producto.get('codigo_barras') or f"1{producto['id']:05d}")
        self.txt_codigo_fabrica.setText(producto.get('codigo_fabrica') or "")
        self.txt_descripcion.setText(producto['nombre'])
        
        idx_cat = self.cb_categoria.findData(producto.get('categoria_id'))
        if idx_cat >= 0:
            self.cb_categoria.setCurrentIndex(idx_cat)
            
        idx_prov = self.cb_proveedor.findData(producto.get('proveedor_id'))
        if idx_prov >= 0:
            self.cb_proveedor.setCurrentIndex(idx_prov)
                 
        self.txt_costo_lista.setText(f"{producto.get('costo_lista', 0.0):.2f}")
        self.txt_flete.setText(f"{producto.get('flete', 0.0):.2f}")
        self.txt_utilidad.setText(f"{producto.get('utilidad_porcentaje', 0.0):.2f}")
        self.txt_precio_contado.setText(f"{producto.get('precio_contado', 0.0):.2f}")
        self.txt_precio_tarjeta.setText(f"{producto.get('precio_tarjeta', 0.0):.2f}")
        
        self.txt_stock_actual.setText(str(producto.get('stock_actual', 0)))


        self.txt_stock_min.setText(str(producto.get('stock_minimo', 5)))
        self.txt_stock_max.setText(str(producto.get('stock_maximo', 100)))
        self.txt_ubicacion.setText(producto.get('ubicacion') or "")
        self.txt_talle.setText(producto.get('talle') or "")
        
        # Información de trazabilidad
        creado = "Desconocido"
        if producto.get('creado_ref'):
            creado = producto['creado_ref'].get('nombre') or producto['creado_ref'].get('username') or "Desconocido"
            
        modificado = producto.get('modificado_por_nombre') or producto.get('modificado_por_username')
        if not modificado and producto.get('modificado_ref'):
            modificado = producto['modificado_ref'].get('nombre') or producto['modificado_ref'].get('username')
            
        if not modificado:
            # Si no hay modificación específica, mostrar fecha de creación
            fecha_creacion = str(producto.get('created_at') or '')[:10]
            modificado = f"Registro inicial ({fecha_creacion})" if fecha_creacion else "Sin modificaciones registradas"
            
        self.lbl_creado_por.setText(creado)
        self.lbl_modificado_por.setText(modificado)
        
        self.btn_ficha.setEnabled(True)
        if producto.get('activo', 1) == 0:
            self.btn_eliminar.setVisible(False)
            self.btn_restaurar.setVisible(True)
            self.btn_grabar.setEnabled(False)
        else:
            self.btn_eliminar.setEnabled(True)
            self.btn_eliminar.setVisible(True)
            self.btn_restaurar.setVisible(False)
            self.btn_grabar.setEnabled(True)
            self.btn_grabar.setText("Actualizar")

    def limpiar_formulario(self):
        self.txt_codigo_interno.setText("[ Automático ]")
        self.txt_codigo_barras.clear()
        self.txt_codigo_fabrica.clear()
        self.txt_descripcion.clear()
        self.txt_costo_lista.setText("0.00")
        self.txt_flete.setText("0.00")
        self.txt_utilidad.setText("0.00")
        self.txt_precio_contado.setText("0.00")
        self.txt_precio_tarjeta.setText("0.00")
        self.txt_stock_actual.setText("0")
        self.txt_stock_min.setText("5")
        self.txt_stock_max.setText("100")
        self.txt_ubicacion.clear()
        self.txt_talle.clear()
        self.lbl_creado_por.setText("-")
        self.lbl_modificado_por.setText("-")
        self.producto_seleccionado_id = None
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setVisible(True)
        self.btn_restaurar.setVisible(False)
        self.btn_ficha.setEnabled(False)
        self.btn_grabar.setEnabled(True)
        self.btn_grabar.setText("Guardar (F5)")
        self.txt_codigo_barras.setFocus()

    def eliminar_producto(self):
        if not self.producto_seleccionado_id:
            return
            
        reply = QMessageBox.question(self, "Confirmar", f"¿Está seguro de eliminar el artículo {self.txt_descripcion.text()}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ProductosManager.eliminar_producto(self.producto_seleccionado_id)
                QMessageBox.information(self, "Eliminado", "Artículo eliminado correctamente.")
                self.limpiar_formulario()
                self.cargar_grilla(self.txt_buscar.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{str(e)}")

    def restaurar_producto(self):
        if not self.producto_seleccionado_id:
            return
            
        reply = QMessageBox.question(self, "Confirmar", f"¿Desea restaurar el artículo {self.txt_descripcion.text()}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ProductosManager.restaurar_producto(self.producto_seleccionado_id)
                QMessageBox.information(self, "Restaurado", "Artículo restaurado correctamente y vuelve a estar activo.")
                self.limpiar_formulario()
                self.cargar_grilla(self.txt_buscar.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo restaurar:\n{str(e)}")

    def abrir_impresor_etiquetas(self):
        from src.ui.impresor_etiquetas_dialog import ImpresorEtiquetasDialog
        dialog = ImpresorEtiquetasDialog(producto_inicial_id=self.producto_seleccionado_id, parent=self)
        dialog.exec()

    def duplicar_producto(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un producto de la grilla para duplicar.")
            return

        codigo_mostrar = self.tabla.item(row, 0).text()
        codigo = codigo_mostrar.replace('[', '').replace(']', '')
        prod = ProductosManager.get_by_codigo(codigo)
        
        if prod:
            self.producto_seleccionado_id = None
            self.txt_codigo_interno.setText("[ Automático ]")
            self.txt_codigo_barras.clear()
            self.txt_codigo_fabrica.clear()
            
            self.txt_descripcion.setText("Copia de " + prod['nombre'])
            self.txt_costo_lista.setText(str(prod['costo_lista']))
            self.txt_flete.setText(str(prod['flete']))
            self.txt_utilidad.setText(str(prod['utilidad_porcentaje']))
            self.txt_precio_contado.setText(str(prod['precio_contado']))
            self.txt_precio_tarjeta.setText(str(prod['precio_tarjeta']))
            
            self.txt_stock_actual.setText(str(prod['stock_actual']))
            self.txt_stock_min.setText(str(prod['stock_minimo']))
            self.txt_talle.setText(prod.get('talle') or "")
            
            self.btn_grabar.setText("Guardar (F5)")
            self.btn_eliminar.setEnabled(False)
            self.btn_ficha.setEnabled(False)
            self.txt_codigo_barras.setFocus()
            QMessageBox.information(self, "Duplicar", "Producto copiado al formulario. Escanee el nuevo código de barras y presione Guardar.")

    def grabar_producto(self):
        try:
            if not self.txt_descripcion.text().strip():
                QMessageBox.warning(self, "Error", "La descripción es obligatoria.")
                return

            cat_data = self.cb_categoria.currentData()
            prov_data = self.cb_proveedor.currentData()
            categoria_id = int(cat_data) if cat_data else None
            proveedor_id = int(prov_data) if prov_data else None

            if self.producto_seleccionado_id:
                # Actualizar
                ProductosManager.actualizar_producto(
                    producto_id=self.producto_seleccionado_id,
                    codigo_barras=self.txt_codigo_barras.text(),
                    codigo_fabrica=self.txt_codigo_fabrica.text(),
                    nombre=self.txt_descripcion.text(),
                    costo_lista=float(self.txt_costo_lista.text()),
                    flete=float(self.txt_flete.text()),
                    utilidad_porcentaje=float(self.txt_utilidad.text()),
                    precio_contado=float(self.txt_precio_contado.text()),
                    precio_tarjeta=float(self.txt_precio_contado.text()),
                    stock_actual=float(self.txt_stock_actual.text()),
                    stock_minimo=float(self.txt_stock_min.text()),
                    stock_maximo=float(self.txt_stock_max.text()),
                    ubicacion=self.txt_ubicacion.text(),
                    categoria_id=categoria_id,
                    proveedor_id=proveedor_id,
                    talle=self.txt_talle.text()
                )
                QMessageBox.information(self, "Éxito", "Artículo actualizado correctamente.")
            else:
                # Crear Nuevo
                ProductosManager.crear_producto(
                    codigo_barras=self.txt_codigo_barras.text(),
                    codigo_fabrica=self.txt_codigo_fabrica.text(),
                    nombre=self.txt_descripcion.text(),
                    costo_lista=float(self.txt_costo_lista.text()),
                    flete=float(self.txt_flete.text()),
                    utilidad_porcentaje=float(self.txt_utilidad.text()),
                    precio_contado=float(self.txt_precio_contado.text()),
                    precio_tarjeta=float(self.txt_precio_contado.text()),
                    stock_actual=float(self.txt_stock_actual.text()),
                    stock_minimo=float(self.txt_stock_min.text()),
                    stock_maximo=float(self.txt_stock_max.text()),
                    ubicacion=self.txt_ubicacion.text(),
                    categoria_id=categoria_id,
                    proveedor_id=proveedor_id,
                    talle=self.txt_talle.text()
                )
                QMessageBox.information(self, "Éxito", "Artículo guardado correctamente.")
                
            self.limpiar_formulario()
            self.cargar_grilla()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_combos()

    def ver_ficha_producto(self):
        if not self.producto_seleccionado_id:
            return
            
        historial = ProductosManager.get_historial_producto(self.producto_seleccionado_id)
        
        from PyQt6.QtWidgets import QDialog
        
        class FichaDialog(QDialog):
            def __init__(self, parent=None, producto_nombre="", historial_data=None):
                super().__init__(parent)
                self.setWindowTitle(f"Ficha / Historial: {producto_nombre}")
                self.setMinimumSize(750, 450)
                self.setStyleSheet("""
                    QDialog {
                        background-color: #FAF8F5;
                    }
                    QLabel {
                        color: #2C2520;
                        font-size: 14px;
                    }
                    QTableWidget {
                        background-color: #FFFFFF;
                        alternate-background-color: #FDFBF7;
                        gridline-color: #E5DFD5;
                        border: 1px solid #E5DFD5;
                        border-radius: 8px;
                        color: #2C2520;
                    }
                    QHeaderView::section {
                        background-color: #F4EFE6;
                        color: #2C2520;
                        padding: 8px;
                        border: none;
                        font-weight: bold;
                        border-bottom: 2px solid #E5DFD5;
                    }
                    QPushButton {
                        background-color: #B09886;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 20px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #9C8573;
                    }
                    QPushButton:pressed {
                        background-color: #8C7869;
                    }
                """)
                
                layout = QVBoxLayout(self)
                layout.setContentsMargins(20, 20, 20, 20)
                layout.setSpacing(15)
                
                lbl_titulo = QLabel(f"Movimientos de: {producto_nombre}")
                lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
                lbl_titulo.setStyleSheet("color: #2C2520;")
                layout.addWidget(lbl_titulo)
                
                tabla = QTableWidget(0, 6)
                tabla.setHorizontalHeaderLabels(["Fecha", "Cliente", "Método Pago", "Cant.", "Precio Unit.", "Subtotal"])
                tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
                tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
                
                tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                tabla.setAlternatingRowColors(True)
                
                for mov in historial_data:
                    row = tabla.rowCount()
                    tabla.insertRow(row)
                    
                    # Fecha (Centrada)
                    item_fecha = QTableWidgetItem(mov['fecha'])
                    item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tabla.setItem(row, 0, item_fecha)
                    
                    # Cliente (Alineado izquierda)
                    item_cliente = QTableWidgetItem(mov['cliente'])
                    item_cliente.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    tabla.setItem(row, 1, item_cliente)
                    
                    # Método Pago (Centrado)
                    item_mp = QTableWidgetItem(mov['metodo_pago'])
                    item_mp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tabla.setItem(row, 2, item_mp)
                    
                    # Cantidad (Centrado, sin decimales si es entero)
                    cant = mov['cantidad']
                    cant_str = str(int(cant)) if float(cant).is_integer() else f"{cant:.2f}"
                    item_cant = QTableWidgetItem(cant_str)
                    item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tabla.setItem(row, 3, item_cant)
                    
                    # Precio Unitario (Derecha con espacio y coma)
                    precio = float(mov['precio_unitario'])
                    item_precio = QTableWidgetItem(f"$ {precio:,.2f}")
                    item_precio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    tabla.setItem(row, 4, item_precio)
                    
                    # Subtotal (Derecha con espacio y coma)
                    subtotal = float(mov['subtotal'])
                    item_subtotal = QTableWidgetItem(f"$ {subtotal:,.2f}")
                    item_subtotal.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    tabla.setItem(row, 5, item_subtotal)
                
                layout.addWidget(tabla)
                
                btn_cerrar = QPushButton("Cerrar")
                btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_cerrar.clicked.connect(self.accept)
                btn_layout = QHBoxLayout()
                btn_layout.addStretch()
                btn_layout.addWidget(btn_cerrar)
                layout.addLayout(btn_layout)
                
        dialog = FichaDialog(self, self.txt_descripcion.text(), historial)
        dialog.exec()
