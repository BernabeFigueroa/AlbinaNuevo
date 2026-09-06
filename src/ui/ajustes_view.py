from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from src.core.configuracion_manager import ConfiguracionManager

class AjustesView(QWidget):
    """
    Vista de Ajustes y Parámetros del Sistema (Acceso exclusivo Administradora).
    Permite configurar el porcentaje de recargo aplicado sobre el precio en efectivo
    para calcular automáticamente el precio de tarjeta / lista.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 35, 40, 35)
        main_layout.setSpacing(25)

        # Header de la sección
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        
        lbl_titulo = QLabel("Ajustes del Sistema")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #2C2520;")
        
        lbl_subtitulo = QLabel("Configuración comercial y parámetros de precios exclusivos para Administración.")
        lbl_subtitulo.setStyleSheet("font-size: 13px; color: #7A7067;")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addWidget(lbl_subtitulo)
        main_layout.addLayout(header_layout)

        # Separador fino
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #E5DFD5; background-color: #E5DFD5; max-height: 1px;")
        main_layout.addWidget(line)

        # Tarjeta de Configuración de Recargo
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5DFD5;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 28, 30, 28)
        card_layout.setSpacing(20)

        # Título de la tarjeta
        lbl_card_title = QLabel("Porcentaje de Recargo: Tarjeta / Precio de Lista")
        lbl_card_title.setStyleSheet("font-size: 17px; font-weight: bold; color: #2C2520; border: none;")
        card_layout.addWidget(lbl_card_title)

        # Explicación clara
        lbl_explicacion = QLabel(
            "Al crear o modificar productos, el sistema calcula el precio en efectivo a partir del costo y la utilidad.\n"
            "El porcentaje configurado aquí se aplicará automáticamente sobre el precio en efectivo para determinar el Precio de Tarjeta / Lista."
        )
        lbl_explicacion.setWordWrap(True)
        lbl_explicacion.setStyleSheet("font-size: 12.5px; color: #6E6259; line-height: 1.4; border: none;")
        card_layout.addWidget(lbl_explicacion)

        # Input horizontal layout
        input_container = QHBoxLayout()
        input_container.setSpacing(12)

        lbl_campo = QLabel("Porcentaje Tarjeta (%):")
        lbl_campo.setStyleSheet("font-size: 14px; font-weight: 600; color: #2C2520; border: none;")
        input_container.addWidget(lbl_campo)

        self.txt_porcentaje = QLineEdit()
        self.txt_porcentaje.setFixedWidth(130)
        self.txt_porcentaje.setStyleSheet("""
            QLineEdit {
                background-color: #FAF8F5;
                border: 1.5px solid #D4CCC4;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
                color: #2C2520;
            }
            QLineEdit:focus {
                border: 1.5px solid #B09886;
                background-color: #FFFFFF;
            }
        """)
        
        # Cargar valor actual
        val_actual = ConfiguracionManager.get_recargo_tarjeta(force_reload=True)
        self.txt_porcentaje.setText(f"{val_actual:g}")
        input_container.addWidget(self.txt_porcentaje)

        lbl_simbolo = QLabel("%")
        lbl_simbolo.setStyleSheet("font-size: 16px; font-weight: bold; color: #7A7067; border: none;")
        input_container.addWidget(lbl_simbolo)

        input_container.addStretch()
        card_layout.addLayout(input_container)

        # Botón Guardar
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #B09886;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9A8272;
            }
            QPushButton:pressed {
                background-color: #7A7067;
            }
        """)
        self.btn_guardar.clicked.connect(self.guardar_ajustes)
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addStretch()

        card_layout.addLayout(btn_layout)

        main_layout.addWidget(card)
        main_layout.addStretch()

    def guardar_ajustes(self):
        txt = self.txt_porcentaje.text().strip().replace(',', '.')
        try:
            val = float(txt)
            if val < 0:
                QMessageBox.warning(self, "Valor Inválido", "El porcentaje de recargo no puede ser negativo.")
                return
            if val > 500:
                QMessageBox.warning(self, "Valor Excesivo", "Por favor ingresa un porcentaje razonable (menor a 500%).")
                return

            exito = ConfiguracionManager.set_recargo_tarjeta(val)
            if exito:
                QMessageBox.information(
                    self, 
                    "Ajustes Guardados", 
                    f"¡Ajustes actualizados correctamente!\n\nEl recargo para tarjeta/lista ahora es del {val:g}%.\nSe aplicará a las nuevas creaciones y modificaciones de productos."
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Atención", 
                    f"Se guardó el porcentaje ({val:g}%) localmente, pero hubo un error de conexión con la base de datos."
                )
        except ValueError:
            QMessageBox.critical(self, "Error", "Por favor ingresa un número válido (ej: 40 o 35.5).")
