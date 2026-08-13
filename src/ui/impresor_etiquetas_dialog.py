from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QPushButton, QFrame, QMessageBox, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QRectF, QSizeF
from PyQt6.QtGui import QFont, QPainter, QPixmap, QColor, QPen, QFontMetrics
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from src.core.cache_manager import DataCache
from src.utils.barcode_generator import generar_barcode_pixmap

class EtiquetaPreviewWidget(QFrame):
    """
    Widget de vista previa gráfica premium que simula la etiqueta adhesiva real de 50mm x 25mm.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 160) # Proporción 2:1 simulada
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D1C7BD;
                border-radius: 8px;
            }
        """)
        
        # Efecto de sombra para simular relieve de etiqueta real
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.producto = None
        self.pixmap_barcode = None

    def set_producto(self, producto):
        self.producto = producto
        if producto:
            # Si no hay código de barras, usamos un código único de 6 dígitos por defecto
            codigo_a_generar = producto.get('codigo_barras') or f"1{producto.get('id', 0):05d}"
            self.pixmap_barcode = generar_barcode_pixmap(str(codigo_a_generar))
        else:
            self.pixmap_barcode = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.producto:
            painter = QPainter(self)
            painter.setPen(QColor("#7A7067"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Seleccione un producto")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # 1. Nombre del Producto (Arriba a la izquierda/centro)
        nombre = str(self.producto.get('nombre', 'Sin Nombre')).upper()
        font_nombre = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font_nombre)
        painter.setPen(QColor("#1C1613"))

        rect_nombre = QRectF(15, 12, w - 100, 25)
        metrics = QFontMetrics(font_nombre)
        elided_nombre = metrics.elidedText(nombre, Qt.TextElideMode.ElideRight, int(rect_nombre.width()))
        painter.drawText(rect_nombre, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_nombre)

        # ID Interno Corto (Arriba a la derecha en tamaño pequeño)
        id_corto = str(self.producto.get('id', ''))
        font_id = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font_id)
        painter.setPen(QColor("#7A7067"))
        rect_id = QRectF(w - 85, 12, 70, 25)
        painter.drawText(rect_id, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"ID: {id_corto}")

        # 2. Código de Barras (Centro)
        if self.pixmap_barcode and not self.pixmap_barcode.isNull():
            rect_barcode = QRectF(20, 42, w - 40, 75)
            painter.drawPixmap(rect_barcode.toRect(), self.pixmap_barcode)

        # 3. Código de Barras en Texto (Abajo)
        cod_barras = self.producto.get('codigo_barras') or f"1{self.producto.get('id', 0):05d}"
        font_codigo = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font_codigo)
        painter.setPen(QColor("#1C1613"))

        rect_codigo = QRectF(20, 123, w - 40, 25)
        painter.drawText(rect_codigo, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, str(cod_barras))


class ImpresorEtiquetasDialog(QDialog):
    def __init__(self, producto_inicial_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impresión de Etiquetas")
        self.setFixedSize(460, 520)
        self.producto_actual = None
        self.productos_list = []
        
        # Cargar hojas de estilo elegantes
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
            }
            QLabel {
                color: #2C2520;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #2C2520;
                border: 1px solid #D1C7BD;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                min-height: 32px;
            }
            QComboBox:focus {
                border: 1px solid #B09886;
            }
            QSpinBox {
                background-color: #FFFFFF;
                color: #2C2520;
                border: 1px solid #D1C7BD;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
                min-height: 32px;
            }
            QSpinBox:focus {
                border: 1px solid #B09886;
            }
        """)
        
        self.init_ui()
        self.cargar_productos(producto_inicial_id)

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(24, 24, 24, 24)
        layout_principal.setSpacing(16)
        self.setLayout(layout_principal)

        # Título
        lbl_titulo = QLabel("Impresión de Etiquetas")
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #1C1613; font-weight: bold;")
        layout_principal.addWidget(lbl_titulo)

        # Línea divisoria
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #E5DFD5; background-color: #E5DFD5;")
        layout_principal.addWidget(line)

        # Selección de producto
        layout_prod = QVBoxLayout()
        lbl_prod = QLabel("Seleccionar Producto:")
        lbl_prod.setStyleSheet("font-weight: bold; color: #544941;")
        self.cb_producto = QComboBox()
        self.cb_producto.currentIndexChanged.connect(self.on_producto_changed)
        layout_prod.addWidget(lbl_prod)
        layout_prod.addWidget(self.cb_producto)
        layout_principal.addLayout(layout_prod)

        # Cantidad de etiquetas
        layout_cant = QHBoxLayout()
        layout_cant.addWidget(QLabel("Cantidad a imprimir:"))
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1000)
        self.spn_cantidad.setValue(1)
        self.spn_cantidad.setFixedWidth(100)
        layout_cant.addWidget(self.spn_cantidad)
        layout_cant.addStretch()
        layout_principal.addLayout(layout_cant)

        # Vista Previa
        lbl_preview_title = QLabel("VISTA PREVIA DE ETIQUETA (50x25mm)")
        lbl_preview_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_preview_title.setStyleSheet("color: #ACA096; letter-spacing: 1px;")
        layout_principal.addWidget(lbl_preview_title)

        container_preview = QHBoxLayout()
        self.preview_widget = EtiquetaPreviewWidget()
        container_preview.addStretch()
        container_preview.addWidget(self.preview_widget)
        container_preview.addStretch()
        layout_principal.addLayout(container_preview)

        layout_principal.addStretch()

        # Botonera
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(12)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedHeight(40)
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #E5DFD5; color: #2C2520; border: none; border-radius: 6px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #ACA096; color: #FFFFFF; }
        """)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_imprimir = QPushButton("Imprimir Etiquetas")
        self.btn_imprimir.setFixedHeight(40)
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: #B09886; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #9C8573; }
            QPushButton:pressed { background-color: #8C7869; }
        """)
        self.btn_imprimir.clicked.connect(self.imprimir_etiquetas)

        layout_botones.addWidget(self.btn_cancelar)
        layout_botones.addWidget(self.btn_imprimir)
        layout_principal.addLayout(layout_botones)

    def cargar_productos(self, producto_inicial_id=None):
        self.productos_list = DataCache.get_productos()
        self.cb_producto.blockSignals(True)
        self.cb_producto.clear()

        selected_index = 0
        for idx, p in enumerate(self.productos_list):
            nombre = p.get('nombre', 'Sin nombre')
            self.cb_producto.addItem(nombre, p['id'])
            if producto_inicial_id and p['id'] == producto_inicial_id:
                selected_index = idx

        self.cb_producto.blockSignals(False)

        if self.productos_list:
            self.cb_producto.setCurrentIndex(selected_index)
            self.on_producto_changed(selected_index)

    def on_producto_changed(self, index):
        if 0 <= index < len(self.productos_list):
            self.producto_actual = self.productos_list[index]
            self.preview_widget.set_producto(self.producto_actual)

    def imprimir_etiquetas(self):
        if not self.producto_actual:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un producto para imprimir.")
            return

        cantidad = self.spn_cantidad.value()
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        # Configurar tamaño de página exacto a 50mm x 25mm
        try:
            from PyQt6.QtGui import QPageSize, QPageLayout
            from PyQt6.QtCore import QSizeF
            
            page_size = QPageSize(QSizeF(50.0, 25.0), QPageSize.Unit.Millimeter)
            page_layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, 
                                     QPageLayout.Unit.Millimeter)
            page_layout.setMargins(QPageLayout.Unit.Millimeter, 0.5, 0.5, 0.5, 0.5)
            printer.setPageLayout(page_layout)
        except Exception as e:
            print(f"Nota: Configuración directa de QPageSize: {e}")

        # Mostrar Diálogo Estándar de Impresión de PyQt6
        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("Imprimir Etiquetas de Producto")
        
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            try:
                self.ejecutar_render_impresion(printer, cantidad)
                QMessageBox.information(self, "Éxito", f"Se enviaron {cantidad} etiqueta(s) a la impresora.")
                self.accept()
            except Exception as ex:
                QMessageBox.critical(self, "Error de Impresión", f"No se pudo completar la impresión:\n{str(ex)}")

    def ejecutar_render_impresion(self, printer: QPrinter, cantidad: int):
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Rectángulo de la página en la resolución de la impresora
        rect_page = printer.pageRect(QPrinter.Unit.DevicePixel)
        w = rect_page.width()
        h = rect_page.height()

        codigo_barras = self.producto_actual.get('codigo_barras') or f"1{self.producto_actual.get('id', 0):05d}"
        pixmap_bc = generar_barcode_pixmap(str(codigo_barras))

        nombre = str(self.producto_actual.get('nombre', '')).upper()
        id_corto_txt = str(self.producto_actual.get('id', ''))
        codigo_text = str(codigo_barras)

        for i in range(cantidad):
            if i > 0:
                printer.newPage()

            # 1. Nombre del Producto (Arriba a la izquierda, ~20% alto)
            font_nombre = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font_nombre)
            painter.setPen(QColor("#000000"))

            rect_nombre = QRectF(w * 0.05, h * 0.05, w * 0.65, h * 0.20)
            metrics = QFontMetrics(font_nombre)
            elided_nombre = metrics.elidedText(nombre, Qt.TextElideMode.ElideRight, int(rect_nombre.width()))
            painter.drawText(rect_nombre, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_nombre)

            # ID Interno Corto (Arriba a la derecha, ~20% alto)
            font_id = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(font_id)
            painter.setPen(QColor("#555555"))
            rect_id = QRectF(w * 0.72, h * 0.05, w * 0.23, h * 0.20)
            painter.drawText(rect_id, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"ID: {id_corto_txt}")

            # 2. Código de Barras (Centro, ~48% alto)
            if pixmap_bc and not pixmap_bc.isNull():
                rect_bc = QRectF(w * 0.05, h * 0.28, w * 0.90, h * 0.48)
                painter.drawPixmap(rect_bc.toRect(), pixmap_bc)

            # 3. Código numérico / interno (Abajo, ~18% alto)
            font_cod = QFont("Consolas", 8, QFont.Weight.Bold)
            painter.setFont(font_cod)
            painter.setPen(QColor("#000000"))

            rect_cod = QRectF(w * 0.05, h * 0.78, w * 0.90, h * 0.18)
            painter.drawText(rect_cod, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, codigo_text)

        painter.end()
