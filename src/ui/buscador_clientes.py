from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt
from src.core.clientes_manager import ClientesManager

class BuscadorClientesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscador de Clientes (F3)")
        self.resize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
                color: #2C2520;
            }
            QLabel {
                color: #2C2520;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #2C2520;
                border: 1px solid #ACA096;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #B09886;
            }
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #FDFBF7;
                gridline-color: #E5DFD5;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
                color: #2C2520;
            }
            QTableWidget::item {
                padding: 6px;
                color: #2C2520;
            }
            QTableWidget::item:selected {
                background-color: #B09886;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #F4EFE6;
                color: #2C2520;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #E5DFD5;
            }
        """)

        
        self.cliente_id_seleccionado = None
        self.init_ui()
        self.cargar_grilla()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Buscador
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.txt_buscar = QLineEdit()
        self.txt_buscar
        self.txt_buscar.setPlaceholderText("Escriba nombre, CUIT/DNI o localidad...")
        self.txt_buscar.textChanged.connect(self.filtrar_grilla)
        self.txt_buscar.installEventFilter(self)
        search_layout.addWidget(self.txt_buscar)
        layout.addLayout(search_layout)
        
        # Grilla
        self.tabla = QTableWidget(0, 4)

        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "CUIT/DNI", "Condición IVA"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.seleccionar_cliente)
        self.tabla.installEventFilter(self)
        layout.addWidget(self.tabla)
        
        self.txt_buscar.setFocus()

    def eventFilter(self, source, event):
        if source == self.txt_buscar and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self.tabla.setFocus()
                if self.tabla.rowCount() > 0:
                    self.tabla.selectRow(0)
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.seleccionar_cliente_actual()
                return True
        elif hasattr(self, 'tabla') and source == self.tabla and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.seleccionar_cliente_actual()
                return True
        return super().eventFilter(source, event)

    def cargar_grilla(self, filtro=""):
        self.tabla.setRowCount(0)
        clientes = ClientesManager.get_all()
        for c in clientes:
            coincide_nombre = filtro.lower() in c['nombre'].lower()
            coincide_cuit = bool(c['cuit'] and filtro in c['cuit'])
            coincide_localidad = bool(c['localidad'] and filtro.lower() in c['localidad'].lower())
            coincide_id = filtro == str(c['id'])
            
            if not (coincide_nombre or coincide_cuit or coincide_localidad or coincide_id):
                continue
            
            row_idx = self.tabla.rowCount()
            self.tabla.insertRow(row_idx)
            
            self.tabla.setItem(row_idx, 0, QTableWidgetItem(str(c['id'])))
            self.tabla.setItem(row_idx, 1, QTableWidgetItem(c['nombre']))
            self.tabla.setItem(row_idx, 2, QTableWidgetItem(c['cuit'] or ""))
            self.tabla.setItem(row_idx, 3, QTableWidgetItem(c['condicion_iva'] or ""))

    def filtrar_grilla(self, texto):
        self.cargar_grilla(texto)

    def seleccionar_cliente_actual(self):
        row = self.tabla.currentRow()
        if row >= 0:
            self.cliente_id_seleccionado = self.tabla.item(row, 0).text()
            self.accept()

    def seleccionar_cliente(self, row, col):
        self.cliente_id_seleccionado = self.tabla.item(row, 0).text()
        self.accept()
