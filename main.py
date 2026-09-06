import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import Qt

# Configurar soporte para pantallas High-DPI (escalado 125%, 150%, laptops)
if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

from src.ui.login_window import LoginWindow

def main():
    app = QApplication(sys.argv)
    
    # Cargar tipografía Poppins
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-Bold.ttf")
    app.setFont(QFont("Poppins", 10))
    
    # Estilo moderno Boutique para Albina Accesorios
    # Resuelve de raíz los problemas de visualización e inconsistencias de botones y flechas
    albina_style = """
    /* Fondo General de Ventas */
    QMainWindow, QDialog, QStackedWidget, QMessageBox {
        background-color: #FAF8F5;
        color: #2C2520;
    }

    /* Diálogos y Modales (QMessageBox, QDialog, QInputDialog) */
    QMessageBox {
        background-color: #FAF8F5;
        color: #2C2520;
        min-width: 420px;
    }
    QMessageBox QLabel {
        color: #2C2520;
        font-size: 13px;
        font-weight: 500;
        background-color: transparent;
        min-height: 48px;
        padding: 6px;
    }
    QMessageBox QPushButton {
        min-width: 85px;
        min-height: 32px;
        padding: 6px 16px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 6px;
        background-color: #B09886;
        color: #FFFFFF;
        border: none;
    }
    QMessageBox QPushButton:hover {
        background-color: #9C8573;
    }
    QMessageBox QPushButton:pressed {
        background-color: #8C7869;
    }
    QDialog QLabel {
        color: #2C2520;
    }
    
    /* Separador invisible para que no dibuje una barra negra gruesa */
    QSplitter::handle {
        background-color: transparent;
        height: 10px;
        width: 10px;
    }
    
    /* Paneles / Tarjetas Flotantes */
    .QFrame {
        background-color: #FFFFFF;
        border: 1px solid #E5DFD5;
        border-radius: 12px;
    }
    
    /* Forzar que las etiquetas dentro de QFrame no tengan borde */
    .QFrame QLabel {
        border: none;
        background-color: transparent;
        color: #2C2520;
    }
    
    /* Campos de Entrada (QLineEdit, QComboBox, QDateEdit) */
    QLineEdit, QComboBox, QDateEdit {
        background-color: #FFFFFF;
        color: #2C2520;
        border: 1px solid #D5CFC7;
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 13px;
        min-height: 30px;
    }
    
    QLineEdit:hover, QComboBox:hover, QDateEdit:hover {
        border: 1px solid #B09886;
    }
    
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
        border: 1.5px solid #8C7869;
        background-color: #FCFBF9;
    }
    
    /* Personalización Delicada y Elegante de Desplegables (QComboBox y QDateEdit) */
    QComboBox, QDateEdit {
        padding-right: 30px;
    }
    
    QComboBox::drop-down, QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: none;
        background-color: transparent;
    }
    
    QComboBox::down-arrow, QDateEdit::down-arrow {
        image: url("assets/icons/chevron_down.svg");
        width: 10px;
        height: 10px;
        margin-right: 4px;
    }
    
    QComboBox::down-arrow:hover, QDateEdit::down-arrow:hover {
        opacity: 0.8;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #2C2520;
        selection-background-color: #F4EFE6;
        selection-color: #2C2520;
        border: 1px solid #E5DFD5;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }

    QComboBox QAbstractItemView::item {
        color: #2C2520;
        background-color: #FFFFFF;
        min-height: 28px;
        padding: 4px 10px;
        border-radius: 4px;
    }

    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:selected {
        background-color: #F4EFE6;
        color: #1A1715;
    }
    
    /* Botones - Regla General (Primary) */
    QPushButton {
        background-color: #B09886; /* Beige Boutique */
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 13px;
        padding: 8px 16px;
        min-height: 35px;
    }
    
    QPushButton:hover {
        background-color: #9C8573;
    }
    
    QPushButton:pressed {
        background-color: #8C7869;
    }
    
    /* Botones Danger (Eliminar, etc.) */
    QPushButton#btn_danger {
        background-color: #D99890; /* Rosa Pastel Apagado */
        color: #FFFFFF;
    }
    QPushButton#btn_danger:hover {
        background-color: #C5847C;
    }
    
    /* Botones Neutrales/Warning (Limpiar, Ver Ficha, Cancelar) */
    QPushButton#btn_neutral {
        background-color: #ACA096; /* Gris Crema */
        color: #FFFFFF;
    }
    QPushButton#btn_neutral:hover {
        background-color: #918A83;
    }
    
    /* Estilo de Grillas / Tablas */
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
    """
    
    app.setStyleSheet(albina_style)
    
    # Iniciar con la ventana de Login
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
