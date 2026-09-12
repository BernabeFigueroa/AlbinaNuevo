from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget,
)

from src.core.productos_manager import ProductosManager


class ArticuloProvisorioDialog(QDialog):
    """Alta puntual; el catálogo sólo se escribe al elegir explícitamente permanente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar artículo a la venta")
        self.setMinimumWidth(440)
        self.item = None
        layout = QVBoxLayout(self)
        aviso = QLabel("El artículo se agrega sólo a esta venta, sin modificar el stock.")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)
        form = QFormLayout()
        self.nombre = QLineEdit()
        self.nombre.setMaxLength(200)
        self.cantidad = self._numero(0.01, 999999, 2, 1)
        self.precio_contado = self._numero(0, 99999999, 2)
        self.precio_tarjeta = self._numero(0, 99999999, 2)
        self.costo = self._numero(0, 99999999, 2)
        form.addRow("Descripción:", self.nombre)
        form.addRow("Cantidad a vender:", self.cantidad)
        form.addRow("Precio unitario contado:", self.precio_contado)
        form.addRow("Precio unitario tarjeta / lista:", self.precio_tarjeta)
        form.addRow("Costo unitario (0 si no tiene):", self.costo)
        # Al comenzar se ofrece el mismo precio en ambos medios; luego son editables.
        self.precio_contado.valueChanged.connect(self.precio_tarjeta.setValue)
        layout.addLayout(form)
        self.permanente = QCheckBox("Guardar también como producto permanente")
        layout.addWidget(self.permanente)
        self.datos_stock = QWidget()
        stock_form = QFormLayout(self.datos_stock)
        self.codigo = QLineEdit()
        self.codigo.setMaxLength(100)
        self.stock = self._numero(0, 999999, 2, 1)
        stock_form.addRow("Código de barras (obligatorio):", self.codigo)
        stock_form.addRow("Stock inicial total:", self.stock)
        nota = QLabel(
            "El stock inicial incluye las unidades de esta venta. Se descuentan al cobrar. "
            "El producto se guarda al agregarlo y permanece en el catálogo aunque cancele la venta."
        )
        nota.setWordWrap(True)
        stock_form.addRow(nota)
        self.datos_stock.setVisible(False)
        self.permanente.toggled.connect(self.datos_stock.setVisible)
        layout.addWidget(self.datos_stock)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Agregar a la venta")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.agregar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    @staticmethod
    def _numero(minimo, maximo, decimales, valor=0):
        campo = QDoubleSpinBox()
        campo.setDecimals(decimales)
        campo.setRange(minimo, maximo)
        campo.setValue(valor)
        return campo

    def agregar(self):
        nombre = self.nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Artículo", "La descripción es obligatoria.")
            return
        producto_id = None
        codigo = self.codigo.text().strip()
        if self.permanente.isChecked():
            if not codigo:
                QMessageBox.warning(self, "Artículo", "Ingrese un código de barras para el producto permanente.")
                return
            if self.stock.value() < self.cantidad.value():
                QMessageBox.warning(self, "Stock", "El stock inicial debe incluir todas las unidades que va a vender.")
                return
            try:
                producto_id = ProductosManager.crear_producto(
                    codigo_barras=codigo, nombre=nombre, costo_lista=self.costo.value(),
                    flete=0, utilidad_porcentaje=0,
                    precio_contado=self.precio_contado.value(), precio_tarjeta=self.precio_tarjeta.value(),
                    stock_actual=self.stock.value(), stock_minimo=0,
                    stock_maximo=max(100, self.stock.value()),
                )
            except Exception as exc:
                QMessageBox.critical(self, "Artículo", f"No se pudo guardar el producto:\n{exc}")
                return
        self.item = {
            'producto_id': producto_id, 'promocion_id': None,
            'codigo_barras': codigo if producto_id is not None else '[PROVISORIO]',
            'nombre': nombre, 'cantidad': self.cantidad.value(),
            'precio_unitario': self.precio_tarjeta.value(),
            'precio_contado': self.precio_contado.value(),
            'precio_tarjeta': self.precio_tarjeta.value(),
            'costo_unitario': self.costo.value(), 'es_promo': False,
            'es_provisorio': producto_id is None,
        }
        self.accept()
