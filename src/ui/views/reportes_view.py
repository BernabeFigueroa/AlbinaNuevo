from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from src.core.reportes_manager import ReportesManager

class ReportesView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_reporte()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        lbl_titulo = QLabel("Reporte de Ganancias - Sesión Actual")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(lbl_titulo)
        
        # Tarjetas de resumen
        tarjetas_layout = QHBoxLayout()
        
        self.lbl_ventas = self.crear_tarjeta("Ventas Totales", "$0.00", "#e3f2fd", tarjetas_layout)
        self.lbl_costos = self.crear_tarjeta("Costos Totales", "$0.00", "#ffebee", tarjetas_layout)
        self.lbl_ganancia = self.crear_tarjeta("Ganancia Neta", "$0.00", "#e8f5e9", tarjetas_layout)
        
        layout.addLayout(tarjetas_layout)
        
        btn_actualizar = QPushButton("Actualizar Reportes")
        btn_actualizar.setStyleSheet("padding: 10px; background-color: #BFB1A6; font-weight: bold; margin-top: 20px;")
        btn_actualizar.clicked.connect(self.cargar_reporte)
        layout.addWidget(btn_actualizar)
        
        layout.addStretch()
        
    def crear_tarjeta(self, titulo, valor_inicial, color_fondo, layout_padre):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {color_fondo}; border-radius: 10px; padding: 20px;")
        flayout = QVBoxLayout(frame)
        
        ltitulo = QLabel(titulo)
        ltitulo.setStyleSheet("color: #555; font-size: 16px;")
        flayout.addWidget(ltitulo)
        
        lvalor = QLabel(valor_inicial)
        lvalor.setStyleSheet("color: black; font-size: 28px; font-weight: bold;")
        flayout.addWidget(lvalor)
        
        layout_padre.addWidget(frame)
        return lvalor
        
    def cargar_reporte(self):
        try:
            resumen = ReportesManager.obtener_resumen_ganancias()
            if resumen:
                self.lbl_ventas.setText(f"${resumen['total_ventas']:.2f}")
                self.lbl_costos.setText(f"${resumen['costo_total']:.2f}")
                self.lbl_ganancia.setText(f"${resumen['ganancia']:.2f}")
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"No se pudo cargar el reporte: {str(e)}")
