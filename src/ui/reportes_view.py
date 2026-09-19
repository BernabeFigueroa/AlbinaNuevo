from datetime import datetime, timezone, timedelta
from html import escape
try:
    import zoneinfo
    tz_ar = zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")
except Exception:
    tz_ar = timezone(timedelta(hours=-3))

def formatear_fecha_ar(fecha_str):
    if not fecha_str:
        return "-"
    try:
        dt = datetime.fromisoformat(str(fecha_str).replace('Z', '+00:00'))
        dt_local = dt.astimezone(tz_ar)
        return dt_local.strftime("%d/%m/%Y %H:%M hs")
    except Exception:
        # Fallback simple
        return str(fecha_str)[:16].replace("T", " ")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QDateEdit, QTabWidget, QFrame,
    QLineEdit, QMenu
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction

from src.core.reportes_manager import ReportesManager
from src.core.caja_manager import CajaManager
from PyQt6.QtWidgets import QMessageBox, QDialog

class DialogoDetalleModerno(QDialog):
    def __init__(self, titulo, contenido_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
                border: 1px solid #E5DFD5;
                border-radius: 12px;
            }
            QLabel {
                color: #2C2520;
                font-size: 13px;
            }
            QPushButton {
                background-color: #B09886;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 13px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #9C8573;
            }
            QPushButton:pressed {
                background-color: #8C7869;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520; letter-spacing: 0.3px;")
        layout.addWidget(lbl_titulo)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5DFD5;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_contenido = QLabel(contenido_html)
        lbl_contenido.setWordWrap(True)
        lbl_contenido.setTextFormat(Qt.TextFormat.RichText)
        frame_layout.addWidget(lbl_contenido)
        layout.addWidget(frame)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)


class DialogoConfirmarAnulacion(QDialog):
    def __init__(self, venta_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Anular Venta #{venta_id:08d}")
        self.setMinimumWidth(440)
        self.motivo = ""
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
                border: 1px solid #E5DFD5;
                border-radius: 12px;
            }
            QLabel {
                color: #2C2520;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #2C2520;
                border: 1.5px solid #D5CFC7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #B09886;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        
        lbl_tit = QLabel("Confirmar Anulación de Venta")
        lbl_tit.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: #721C24;")
        layout.addWidget(lbl_tit)
        
        lbl_desc = QLabel(
            f"¿Está seguro de que desea anular la <b>Venta #{venta_id:08d}</b>?<br><br>"
            "• Los productos regresarán automáticamente al inventario.<br>"
            "• El importe se descontará de los totales de caja.<br>"
            "• Si fue fiada, se cancelará la deuda del cliente.<br>"
            "• La venta quedará registrada como <b>ANULADA</b> para auditoría."
        )
        lbl_desc.setTextFormat(Qt.TextFormat.RichText)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 12.5px; color: #495057; line-height: 1.4;")
        layout.addWidget(lbl_desc)
        
        lbl_motivo = QLabel("Motivo o descripción de la anulación (obligatorio):")
        lbl_motivo.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        layout.addWidget(lbl_motivo)
        
        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Ej: Cliente cambió de accesorios, error en cobro...")
        layout.addWidget(self.txt_motivo)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E5DFD5;
                color: #2C2520;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #D5CFC7; }
        """)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_anular = QPushButton("Confirmar Anulación")
        btn_anular.setStyleSheet("""
            QPushButton {
                background-color: #C0392B;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #A93226; }
        """)
        btn_anular.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_anular.clicked.connect(self.validar_y_aceptar)
        btn_layout.addWidget(btn_anular)
        
        layout.addLayout(btn_layout)
        
    def validar_y_aceptar(self):
        motivo = self.txt_motivo.text().strip()
        if not motivo:
            QMessageBox.warning(self, "Atención", "Debe ingresar una descripción o motivo para la anulación.")
            self.txt_motivo.setFocus()
            return
        self.motivo = motivo
        self.accept()


class DialogoDetalleVenta(QDialog):
    anulacion_exitosa = pyqtSignal()
    cambio_metodo_exitoso = pyqtSignal(str)

    def __init__(self, venta_id: int, info_venta: dict, contenido_html: str, parent=None):
        super().__init__(parent)
        self.venta_id = venta_id
        self.info_venta = info_venta or {}
        self.setWindowTitle(f"Detalle de Venta #{venta_id:08d}")
        self.setMinimumWidth(520)
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF8F5;
                border: 1px solid #E5DFD5;
                border-radius: 12px;
            }
            QLabel {
                color: #2C2520;
                font-size: 13px;
            }
            QPushButton {
                background-color: #B09886;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 13px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #9C8573;
            }
            QPushButton:pressed {
                background-color: #8C7869;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        
        # Barra de encabezado: Título + Botón de 3 puntitos
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel(f"Detalle de Venta #{venta_id:08d}")
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520; letter-spacing: 0.3px;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        
        # Botón de 3 puntitos discreto y elegante
        import os, sys
        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import QSize
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        icon_path = os.path.join(base_path, "assets", "icons", "more_vert.svg")

        self.btn_opciones = QPushButton()
        if os.path.exists(icon_path):
            self.btn_opciones.setIcon(QIcon(icon_path))
            self.btn_opciones.setIconSize(QSize(20, 20))
        else:
            self.btn_opciones.setText("⋮")
            self.btn_opciones.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.btn_opciones.setFixedSize(36, 36)
        self.btn_opciones.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_opciones.setToolTip("Opciones de venta")
        self.btn_opciones.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #EFE9E0;
                border: 1px solid #D5CFC7;
            }
            QPushButton:pressed {
                background-color: #E2DBD0;
            }
        """)
        self.btn_opciones.clicked.connect(self.mostrar_menu_opciones)
        header_layout.addWidget(self.btn_opciones)
        
        layout.addLayout(header_layout)

        # Tarjeta de Medio de Pago con opción de cambio rápido
        self.card_pago = QFrame()
        self.card_pago.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5DFD5;
            }
        """)
        pago_layout = QHBoxLayout(self.card_pago)
        pago_layout.setContentsMargins(16, 10, 16, 10)
        pago_layout.setSpacing(10)

        lbl_tit_pago = QLabel("Medio de Pago:")
        lbl_tit_pago.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        lbl_tit_pago.setStyleSheet("color: #5A5047;")
        pago_layout.addWidget(lbl_tit_pago)

        self.lbl_metodo_badge = QLabel()
        pago_layout.addWidget(self.lbl_metodo_badge)

        pago_layout.addStretch()

        self.btn_cambiar_metodo = QPushButton()
        self.btn_cambiar_metodo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cambiar_metodo.setStyleSheet("""
            QPushButton {
                background-color: #F4EFE6;
                color: #2C2520;
                border: 1.5px solid #B09886;
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 12px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #B09886;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #9C8573;
                color: #FFFFFF;
            }
        """)
        self.btn_cambiar_metodo.clicked.connect(self.solicitar_cambio_metodo)
        pago_layout.addWidget(self.btn_cambiar_metodo)

        self._actualizar_ui_metodo_pago()
        layout.addWidget(self.card_pago)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5DFD5;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_contenido = QLabel(contenido_html)
        lbl_contenido.setWordWrap(True)
        lbl_contenido.setTextFormat(Qt.TextFormat.RichText)
        frame_layout.addWidget(lbl_contenido)
        layout.addWidget(frame)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _actualizar_ui_metodo_pago(self):
        mp = str(self.info_venta.get('metodo_pago') or '').strip().upper()
        es_anulada = self.info_venta.get('estado') in ('ANULADA', 'CANCELADA')

        if mp == 'EFECTIVO':
            self.lbl_metodo_badge.setText("EFECTIVO")
            self.lbl_metodo_badge.setStyleSheet("""
                background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9;
                border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;
            """)
            self.btn_cambiar_metodo.setText("⇄ Cambiar a Transferencia")
            self.btn_cambiar_metodo.setToolTip("Cambiar el método de pago de esta venta a Transferencia")
            self.btn_cambiar_metodo.setVisible(not es_anulada)
        elif mp == 'TRANSFERENCIA':
            self.lbl_metodo_badge.setText("TRANSFERENCIA")
            self.lbl_metodo_badge.setStyleSheet("""
                background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB;
                border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;
            """)
            self.btn_cambiar_metodo.setText("⇄ Cambiar a Efectivo")
            self.btn_cambiar_metodo.setToolTip("Cambiar el método de pago de esta venta a Efectivo")
            self.btn_cambiar_metodo.setVisible(not es_anulada)
        else:
            self.lbl_metodo_badge.setText(mp)
            self.lbl_metodo_badge.setStyleSheet("""
                background-color: #F5F5F5; color: #616161; border: 1px solid #E0E0E0;
                border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;
            """)
            self.btn_cambiar_metodo.setVisible(False)

    def solicitar_cambio_metodo(self):
        es_anulada = self.info_venta.get('estado') in ('ANULADA', 'CANCELADA')
        if es_anulada:
            QMessageBox.warning(self, "Atención", "No se puede cambiar el método de pago de una venta anulada.")
            return

        metodo_actual = str(self.info_venta.get('metodo_pago') or '').strip().upper()
        if metodo_actual not in ('EFECTIVO', 'TRANSFERENCIA'):
            QMessageBox.warning(
                self, "Atención",
                f"Solo se puede cambiar el método de pago entre Efectivo y Transferencia.\n"
                f"Esta venta posee el método '{metodo_actual}'."
            )
            return

        nuevo_metodo = 'TRANSFERENCIA' if metodo_actual == 'EFECTIVO' else 'EFECTIVO'

        resp = QMessageBox.question(
            self, "Confirmar Cambio de Método de Pago",
            f"¿Desea cambiar el método de pago de la venta #{self.venta_id:08d}?\n\n"
            f"• Actual: {metodo_actual}\n"
            f"• Nuevo: {nuevo_metodo}\n\n"
            "Los reportes y registros de caja se actualizarán automáticamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resp == QMessageBox.StandardButton.Yes:
            try:
                from src.core.ventas_manager import VentasManager
                res = VentasManager.cambiar_metodo_pago(self.venta_id, nuevo_metodo)
                self.info_venta['metodo_pago'] = nuevo_metodo
                self._actualizar_ui_metodo_pago()
                QMessageBox.information(
                    self, "Método Actualizado",
                    f"El método de pago fue cambiado exitosamente a {nuevo_metodo}."
                )
                self.cambio_metodo_exitoso.emit(nuevo_metodo)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cambiar el método de pago:\n{str(e)}")

    def mostrar_menu_opciones(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                color: #2C2520;
            }
            QMenu::item:selected {
                background-color: #F4EFE6;
                color: #2C2520;
            }
            QMenu::item:disabled {
                color: #A09891;
            }
        """)
        
        es_anulada = self.info_venta.get('estado') in ('ANULADA', 'CANCELADA')
        metodo_actual = str(self.info_venta.get('metodo_pago') or '').strip().upper()

        if not es_anulada and metodo_actual in ('EFECTIVO', 'TRANSFERENCIA'):
            nuevo_metodo = 'TRANSFERENCIA' if metodo_actual == 'EFECTIVO' else 'EFECTIVO'
            action_cambiar = QAction(f"Cambiar método a {nuevo_metodo.capitalize()}", self)
            action_cambiar.triggered.connect(self.solicitar_cambio_metodo)
            menu.addAction(action_cambiar)
            menu.addSeparator()

        if es_anulada:
            action_anular = QAction("Venta ya Anulada", self)
            action_anular.setEnabled(False)
            menu.addAction(action_anular)
        else:
            action_anular = QAction("Anular Venta", self)
            action_anular.triggered.connect(self.solicitar_anulacion)
            menu.addAction(action_anular)
            
        menu.exec(self.btn_opciones.mapToGlobal(self.btn_opciones.rect().bottomLeft()))

    def solicitar_anulacion(self):
        dlg = DialogoConfirmarAnulacion(self.venta_id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            motivo = dlg.motivo
            try:
                from src.core.ventas_manager import VentasManager
                VentasManager.anular_venta(self.venta_id, motivo)
                QMessageBox.information(
                    self, "Venta Anulada",
                    f"La venta #{self.venta_id:08d} fue anulada correctamente.\n\n"
                    "• Los productos volvieron al inventario.\n"
                    "• El importe fue descontado de la caja."
                )
                self.anulacion_exitosa.emit()
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo anular la venta:\n{str(e)}")


class ReportesView(QWidget):
    def __init__(self):
        super().__init__()
        self._filtros_reportes = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        
        lbl_titulo = QLabel("REPORTES Y ESTADÍSTICAS")
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520;")
        layout.addWidget(lbl_titulo)

        # --- FILTROS DE FECHA ---
        filtro_frame = QFrame()

        filtro_layout = QHBoxLayout(filtro_frame)
        
        filtro_layout.addWidget(QLabel("Desde:"))
        self.dt_desde = QDateEdit()
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDate(QDate.currentDate())
        self.dt_desde
        filtro_layout.addWidget(self.dt_desde)
        
        filtro_layout.addWidget(QLabel("Hasta:"))
        self.dt_hasta = QDateEdit()
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDate(QDate.currentDate())
        self.dt_hasta
        filtro_layout.addWidget(self.dt_hasta)
        
        self.lbl_pago = QLabel("Pago:")
        filtro_layout.addWidget(self.lbl_pago)
        from PyQt6.QtWidgets import QComboBox
        self.cb_metodo_pago = QComboBox()
        self.cb_metodo_pago.addItems(["TODOS", "EFECTIVO", "TRANSFERENCIA", "TARJETA", "MIXTO", "CUENTA CORRIENTE"])
        filtro_layout.addWidget(self.cb_metodo_pago)

        self.lbl_estado = QLabel("Estado:")
        filtro_layout.addWidget(self.lbl_estado)
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["TODAS", "REALIZADAS", "ANULADAS"])
        filtro_layout.addWidget(self.cb_estado)
        
        self.lbl_vendedor = QLabel("Vendedor:")
        filtro_layout.addWidget(self.lbl_vendedor)
        self.cb_vendedor = QComboBox()
        filtro_layout.addWidget(self.cb_vendedor)
        self.cargar_combo_vendedores()
        
        self.btn_generar = QPushButton("Generar Reportes")
        self.btn_generar.clicked.connect(self.generar_reportes)
        filtro_layout.addWidget(self.btn_generar)
        
        self.btn_exportar_excel = QPushButton("Exportar Excel (Declaración)")
        self.btn_exportar_excel.setStyleSheet("""
            QPushButton {
                background-color: #217346;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e6b41;
            }
        """)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel_declaracion)
        filtro_layout.addWidget(self.btn_exportar_excel)
        
        # Visibilidad según rol
        from src.core.auth_manager import AuthManager
        if not AuthManager.is_admin():
            self.btn_exportar_excel.hide()
        
        filtro_layout.addStretch()
        layout.addWidget(filtro_frame)


        # --- PESTAÑAS (TABS) ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5DFD5;
                border-radius: 6px;
                background-color: transparent;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 8px;
                color: #666666;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                margin-right: 2px;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #E5DFD5;
                border-bottom: 3px solid #B09886;
            }
            QTabBar::tab:hover:!selected {
                background-color: #FFFFFF;
            }
        """)
        self.tabs.currentChanged.connect(self.al_cambiar_pestana)
        
        self.tab_ventas = QWidget()
        self.tab_productos = QWidget()
        self.tab_rubros = QWidget()
        self.tab_caja = QWidget()
        self.tab_alertas = QWidget()
        self.tab_ganancias = QWidget()
        
        self.tabs.addTab(self.tab_ventas, "Historial de Ventas")
        self.tabs.addTab(self.tab_productos, "Productos más Vendidos")
        self.tabs.addTab(self.tab_rubros, "Ventas por Rubro")
        self.tabs.addTab(self.tab_caja, "Cierres de Caja")
        self.tabs.addTab(self.tab_alertas, "Alertas de Reposición")
        self.tabs.addTab(self.tab_ganancias, "Reporte de Ganancias")
        
        layout.addWidget(self.tabs)

        self.setup_tab_ventas()
        self.setup_tab_productos()
        self.setup_tab_rubros()
        self.setup_tab_caja()
        self.setup_tab_alertas()
        self.setup_tab_ganancias()

    def aplicar_estilo_tabla(self, tabla: QTableWidget):
        tabla.setStyleSheet("""
            
            QHeaderView::section {
                background-color: #FFFFFF;
                color: #666666;
                padding: 8px;
                border: none;
                font-weight: bold;
                border-bottom: 2px solid #E5DFD5;
            }
        """)

    def crear_tarjeta_resumen(self, titulo, valor_inicial, color_hex, subtitulo=None):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-top: 4px solid {color_hex};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(2)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #666666; border: none; background: transparent;")
        
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_valor.setStyleSheet(f"color: {color_hex}; border: none; background: transparent;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)

        lbl_sub = None
        if subtitulo is not None:
            lbl_sub = QLabel(subtitulo)
            lbl_sub.setFont(QFont("Segoe UI", 9))
            lbl_sub.setStyleSheet("color: #8C827A; border: none; background: transparent;")
            layout.addWidget(lbl_sub)
            return frame, lbl_valor, lbl_sub

        return frame, lbl_valor

    def setup_tab_ventas(self):
        layout = QVBoxLayout(self.tab_ventas)
        layout.setSpacing(15)
        
        # Resumen
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(15)
        
        self.frame_efectivo, self.lbl_tot_efectivo = self.crear_tarjeta_resumen("EFECTIVO", "$0.00", "#B09886")
        self.frame_transferencia, self.lbl_tot_transferencia = self.crear_tarjeta_resumen("TRANSFERENCIA", "$0.00", "#000000")
        self.frame_tarjeta, self.lbl_tot_tarjeta, self.lbl_tot_tarjeta_bruto = self.crear_tarjeta_resumen(
            "TARJETA (-35%)", "$0.00", "#7A7067", subtitulo="Bruto: $0.00"
        )
        self.frame_general, self.lbl_tot_general = self.crear_tarjeta_resumen("TOTAL GENERAL", "$0.00", "#D99890")
        
        resumen_layout.addWidget(self.frame_efectivo)
        resumen_layout.addWidget(self.frame_transferencia)
        resumen_layout.addWidget(self.frame_tarjeta)
        resumen_layout.addWidget(self.frame_general)
        
        layout.addLayout(resumen_layout)
        
        # Grilla
        self.tabla_ventas = QTableWidget(0, 7)
        self.tabla_ventas.setHorizontalHeaderLabels(["Factura Nº", "Fecha y Hora", "Cliente", "Vendedor", "Medio Pago", "Total", "Avisos"])
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_ventas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_ventas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_ventas.cellDoubleClicked.connect(self.ver_detalle_venta)
        self.tabla_ventas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_ventas.customContextMenuRequested.connect(self.mostrar_menu_contextual_ventas)
        self.aplicar_estilo_tabla(self.tabla_ventas)
        layout.addWidget(self.tabla_ventas)

    def setup_tab_productos(self):
        layout = QVBoxLayout(self.tab_productos)
        
        self.tabla_productos = QTableWidget(0, 4)
        self.tabla_productos.setHorizontalHeaderLabels(["Código", "Producto", "Cant. Vendida", "Recaudación ($)"])
        self.tabla_productos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_productos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_productos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aplicar_estilo_tabla(self.tabla_productos)
        layout.addWidget(self.tabla_productos)

    def setup_tab_rubros(self):
        layout = QVBoxLayout(self.tab_rubros)
        
        self.tabla_rubros = QTableWidget(0, 4)
        self.tabla_rubros.setHorizontalHeaderLabels(["Rubro", "Total Vendido", "Costo Total", "Ganancia Neta"])
        self.tabla_rubros.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla_rubros.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_rubros.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aplicar_estilo_tabla(self.tabla_rubros)
        layout.addWidget(self.tabla_rubros)

    def setup_tab_caja(self):
        layout = QVBoxLayout(self.tab_caja)
        
        self.tabla_caja = QTableWidget(0, 9)
        self.tabla_caja.setHorizontalHeaderLabels([
            "ID Turno", "Usuario", "Estado", "Apertura", "Cierre", 
            "Inicial", "Esperado", "Declarado", "Diferencia"
        ])
        self.tabla_caja.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_caja.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla_caja.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla_caja.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_caja.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_caja.cellDoubleClicked.connect(self.ver_detalle_caja)
        self.aplicar_estilo_tabla(self.tabla_caja)
        layout.addWidget(self.tabla_caja)

    def ver_detalle_caja(self, row, col):
        try:
            caja_id_str = self.tabla_caja.item(row, 0).text()
            if not caja_id_str: return
            caja_id = int(caja_id_str)
            resumen = CajaManager.obtener_resumen(caja_id)
            
            # Formatear diferencia
            monto_cierre = resumen.get('monto_cierre')
            esperado = resumen.get('total_efectivo_esperado', 0.0)
            
            if monto_cierre is not None:
                dif = round(monto_cierre - esperado, 2)
                if abs(dif) < 0.01:
                    dif_html = '<b style="color: #2E7D32;">$ 0.00 (Exacto)</b>'
                elif dif < 0:
                    dif_html = f'<b style="color: #C62828;">-${abs(dif):,.2f} (FALTANTE)</b>'
                else:
                    dif_html = f'<b style="color: #2E7D32;">+${dif:,.2f} (SOBRANTE)</b>'
                cierre_html = f"$ {monto_cierre:,.2f}"
            else:
                cierre_html = "<i>En curso</i>"
                dif_html = "<i>Pendiente</i>"
                
            usuario_txt = resumen.get('usuario_nombre') or "Desconocido"
            
            html = f"""
            <table width="100%" cellspacing="9" cellpadding="0" style="font-family: 'Segoe UI', sans-serif;">
                <tr><td style="color: #7A7067; font-size: 13px;">Usuario Responsable:</td><td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">{usuario_txt}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">Saldo Inicial:</td><td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">$ {resumen['monto_inicial']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Ventas Efectivo:</td><td align="right" style="color: #B09886; font-weight: 600; font-size: 13px;">$ {resumen['ventas_efectivo']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Ventas Transferencia:</td><td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">$ {resumen['ventas_transferencia']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Ventas Tarjeta (-35%):</td><td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">$ {resumen.get('ventas_tarjeta_descontada', 0.0):,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Ventas Fiadas:</td><td align="right" style="color: #7A7067; font-weight: 600; font-size: 13px;">$ {resumen['ventas_fiadas']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Cobros Deuda (Evo):</td><td align="right" style="color: #B09886; font-weight: 600; font-size: 13px;">$ {resumen['pagos_deuda_efectivo']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Cobros Deuda (Trans):</td><td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">$ {resumen['pagos_deuda_transferencia']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">+ Ingresos Manuales:</td><td align="right" style="color: #B09886; font-weight: 600; font-size: 13px;">$ {resumen['ingresos_manuales']:,.2f}</td></tr>
                <tr><td style="color: #7A7067; font-size: 13px;">- Egresos Manuales:</td><td align="right" style="color: #D99890; font-weight: 600; font-size: 13px;">$ {resumen['egresos_manuales']:,.2f}</td></tr>
            </table>
            <br>
            <hr style="background-color: #E5DFD5; border: none; height: 1px;"/>
            <br>
            <table width="100%" cellspacing="6" style="font-family: 'Segoe UI', sans-serif;">
                <tr>
                    <td style="font-size: 13px; color: #2C2520;"><b>EFECTIVO ESPERADO:</b></td>
                    <td align="right"><b style="color: #B09886; font-size: 16px;">$ {esperado:,.2f}</b></td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #2C2520;"><b>EFECTIVO DECLARADO:</b></td>
                    <td align="right"><b style="color: #2C2520; font-size: 16px;">{cierre_html}</b></td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #2C2520;"><b>DIFERENCIA (ARQUEO):</b></td>
                    <td align="right" style="font-size: 15px;">{dif_html}</td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #2C2520;"><b>TOTAL VENDIDO:</b></td>
                    <td align="right"><b style="color: #2C2520; font-size: 17px;">$ {resumen['total_vendido']:,.2f}</b></td>
                </tr>
            </table>
            """
            dialog = DialogoDetalleModerno(f"Detalle Cierre de Caja #{caja_id}", html, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el detalle:\n{str(e)}")

    def setup_tab_alertas(self):
        layout = QVBoxLayout(self.tab_alertas)
        
        lbl_info = QLabel("Productos cuyo stock actual es menor o igual a su stock mínimo.")
        lbl_info.setStyleSheet("color: #D99890; font-style: italic;")
        layout.addWidget(lbl_info)
        
        self.tabla_alertas = QTableWidget(0, 5)
        self.tabla_alertas.setHorizontalHeaderLabels(["Código", "Producto", "Stock Actual", "Mínimo", "Sugerido Pedir"])
        self.tabla_alertas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_alertas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_alertas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aplicar_estilo_tabla(self.tabla_alertas)
        layout.addWidget(self.tabla_alertas)

    def setup_tab_ganancias(self):
        layout = QVBoxLayout(self.tab_ganancias)
        layout.setSpacing(15)
        
        # Resumen
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(15)
        
        self.frame_g_ventas, self.lbl_ganancia_ventas = self.crear_tarjeta_resumen("TOTAL VENDIDO", "$0.00", "#000000")
        self.frame_g_costo, self.lbl_ganancia_costo = self.crear_tarjeta_resumen("COSTO TOTAL", "$0.00", "#D99890")
        self.frame_g_neta, self.lbl_ganancia_neta = self.crear_tarjeta_resumen("GANANCIA NETA", "$0.00", "#B09886")
        self.frame_g_rent, self.lbl_rentabilidad_pct = self.crear_tarjeta_resumen("RENTABILIDAD", "0.00%", "#E5C07B")
        
        resumen_layout.addWidget(self.frame_g_ventas)
        resumen_layout.addWidget(self.frame_g_costo)
        resumen_layout.addWidget(self.frame_g_rent)
        resumen_layout.addWidget(self.frame_g_neta)
        
        layout.addLayout(resumen_layout)
        # Grilla
        self.tabla_ganancias = QTableWidget(0, 4)
        self.tabla_ganancias.setHorizontalHeaderLabels(["Día", "Total Vendido", "Costo Total", "Ganancia Neta"])
        self.tabla_ganancias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_ganancias.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_ganancias.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.aplicar_estilo_tabla(self.tabla_ganancias)
        layout.addWidget(self.tabla_ganancias)

    def cargar_combo_vendedores(self):
        from src.utils.async_worker import run_async
        run_async(ReportesManager.get_vendedores, on_result=self._mostrar_vendedores,
                  on_error=lambda error: print(f"Error cargando vendedores: {error}"))

    def _mostrar_vendedores(self, vendedores):
        try:
            self.cb_vendedor.clear()
            self.cb_vendedor.addItem("TODOS", None)
            for v in vendedores:
                nombre = v.get('nombre') or v.get('username') or 'Sin nombre'
                self.cb_vendedor.addItem(nombre, v['id'])
        except Exception as e:
            print(f"Error al cargar vendedores: {e}")

    def al_cambiar_pestana(self, index):
        if index == 0:
            self.lbl_pago.show()
            self.cb_metodo_pago.show()
            self.lbl_estado.show()
            self.cb_estado.show()
            self.lbl_vendedor.show()
            self.cb_vendedor.show()
        elif index in (3, 5):
            self.lbl_pago.hide()
            self.cb_metodo_pago.hide()
            self.lbl_estado.hide()
            self.cb_estado.hide()
            self.lbl_vendedor.show()
            self.cb_vendedor.show()
        else:
            self.lbl_pago.hide()
            self.cb_metodo_pago.hide()
            self.lbl_estado.hide()
            self.cb_estado.hide()
            self.lbl_vendedor.hide()
            self.cb_vendedor.hide()
        if self._filtros_reportes:
            self.cargar_reporte_actual_async()

    def generar_reportes(self):
        try:
            desde = self.dt_desde.date().toString("yyyy-MM-dd")
            hasta = self.dt_hasta.date().toString("yyyy-MM-dd")
            usuario_id = self.cb_vendedor.currentData()
            
            metodo = self.cb_metodo_pago.currentText()
            self._filtros_reportes = (desde, hasta, usuario_id, metodo)
            self.cargar_reporte_actual_async()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error al generar reportes", f"Ocurrió un error: {str(e)}")

    def cargar_reporte_actual_async(self):
        """Consulta solamente la pestaña visible, fuera del hilo de interfaz."""
        if not self._filtros_reportes:
            return
        from src.utils.async_worker import run_async
        desde, hasta, usuario_id, metodo = self._filtros_reportes
        index = self.tabs.currentIndex()

        def obtener_datos():
            if index == 0:
                return ReportesManager.get_ventas_por_fecha(
                    desde, hasta, None if metodo == "TODOS" else metodo, usuario_id
                )
            if index == 1:
                return ReportesManager.get_productos_mas_vendidos(desde, hasta)
            if index == 2:
                return ReportesManager.get_ventas_por_rubro(desde, hasta)
            if index == 3:
                cierres = ReportesManager.get_cierres_caja(desde, hasta, usuario_id)
                for cierre in cierres:
                    cierre['_esperado'] = CajaManager.obtener_resumen(cierre['id']).get('total_efectivo_esperado', 0.0)
                return cierres
            if index == 4:
                return ReportesManager.get_alertas_reposicion()
            return ReportesManager.get_reporte_ganancias(desde, hasta, usuario_id)

        run_async(obtener_datos,
                  on_result=lambda datos: self._mostrar_reporte(index, datos),
                  on_error=lambda error: print(f"Error cargando reporte: {error}"))

    def _mostrar_reporte(self, index, datos):
        if self.tabs.currentIndex() != index:
            return
        desde, hasta, usuario_id, _metodo = self._filtros_reportes
        if index == 0:
            self.cargar_ventas(desde, hasta, usuario_id, data=datos)
        elif index == 1:
            self.cargar_productos(desde, hasta, data=datos)
        elif index == 2:
            self.cargar_rubros(desde, hasta, data=datos)
        elif index == 3:
            self.cargar_cajas(desde, hasta, usuario_id, data=datos)
        elif index == 4:
            self.cargar_alertas(data=datos)
        else:
            self.cargar_ganancias(desde, hasta, usuario_id, data=datos)

    def exportar_excel_declaracion(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.core.auth_manager import AuthManager
        
        if not AuthManager.is_admin():
            QMessageBox.warning(self, "Acceso Denegado", "Esta función está reservada únicamente para el usuario Administrador.")
            return
            
        desde = self.dt_desde.date().toString("yyyy-MM-dd")
        hasta = self.dt_hasta.date().toString("yyyy-MM-dd")
        
        sugerido = f"Declaracion_Ventas_{desde}_al_{hasta}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Declaración de Ventas para Excel",
            sugerido,
            "Excel Workbook (*.xlsx);;Archivos CSV (*.csv)"
        )
        
        if not filepath:
            return
            
        try:
            ReportesManager.generar_excel_declaracion_ventas(desde, hasta, filepath)
            QMessageBox.information(
                self, 
                "Exportación Exitosa", 
                f"La declaración de ventas fue exportada con éxito en:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar la declaración:\n{str(e)}")


    def cargar_ventas(self, desde, hasta, usuario_id=None, data=None):
        metodo = self.cb_metodo_pago.currentText() if hasattr(self, 'cb_metodo_pago') else "TODOS"
        metodo_filtro = None if metodo == "TODOS" else metodo
        estado_filtro = self.cb_estado.currentText() if hasattr(self, 'cb_estado') else "TODAS"
        if data is None:
            data = ReportesManager.get_ventas_por_fecha(desde, hasta, metodo_filtro, usuario_id)
        
        total_gen = float(data.get('total_general') or 0.0)
        total_efectivo = float(data.get('total_efectivo') or 0.0)
        total_transferencia = float(data.get('total_transferencia') or 0.0)
        total_tarjeta = float(data.get('total_tarjeta') or 0.0)
        tarjeta_descontada = total_tarjeta * 0.65  # Valor de tarjeta con el 35% restado

        self.lbl_tot_efectivo.setText(f"${total_efectivo:.2f}")
        self.lbl_tot_transferencia.setText(f"${total_transferencia:.2f}")

        if hasattr(self, 'lbl_tot_tarjeta'):
            self.lbl_tot_tarjeta.setText(f"${tarjeta_descontada:.2f}")
            self.lbl_tot_tarjeta.setToolTip(
                f"Total tarjeta bruto: ${total_tarjeta:,.2f}\n"
                f"Menos 35%: -${(total_tarjeta * 0.35):,.2f}\n"
                f"Total tarjeta (-35%): ${tarjeta_descontada:,.2f}"
            )
        if hasattr(self, 'lbl_tot_tarjeta_bruto') and self.lbl_tot_tarjeta_bruto is not None:
            self.lbl_tot_tarjeta_bruto.setText(f"Bruto: ${total_tarjeta:,.2f}")

        self.lbl_tot_general.setText(f"${total_gen:.2f}")
        self.lbl_tot_general.setToolTip(f"Total general: ${total_gen:,.2f}")
        
        self.tabla_ventas.setRowCount(0)
        for v in data['ventas']:
            es_anulada = bool(v.get('es_anulada'))
            if estado_filtro == "REALIZADAS" and es_anulada:
                continue
            if estado_filtro == "ANULADAS" and not es_anulada:
                continue

            row = self.tabla_ventas.rowCount()
            self.tabla_ventas.insertRow(row)

            color_texto = QColor("#8C827A") if es_anulada else QColor("#2C2520")
            
            item_id = QTableWidgetItem(f"{v['id']:08d}")
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_id.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 0, item_id)
            
            item_fecha = QTableWidgetItem(formatear_fecha_ar(v['fecha']))
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fecha.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 1, item_fecha)
            
            item_cli = QTableWidgetItem(v['cliente'] or "Consumidor Final")
            item_cli.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 2, item_cli)

            item_vend = QTableWidgetItem(v['vendedor'])
            item_vend.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 3, item_vend)
            
            item_mp = QTableWidgetItem(v['metodo_pago'])
            item_mp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_mp.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 4, item_mp)
            
            item_total = QTableWidgetItem(f"${v['total']:,.2f}")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_total.setForeground(color_texto)
            self.tabla_ventas.setItem(row, 5, item_total)

            if es_anulada:
                u_anul = v.get('usuario_anulacion_nombre') or 'Usuario'
                f_anul = formatear_fecha_ar(v.get('fecha_anulacion'))
                m_anul = v.get('motivo_anulacion') or 'Sin motivo'
                item_alerta = QTableWidgetItem("ANULADA")
                item_alerta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_alerta.setForeground(QColor("#C0392B"))
                item_alerta.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                item_alerta.setToolTip(f"Venta ANULADA por {u_anul} ({f_anul})\nMotivo: {m_anul}")
                self.tabla_ventas.setItem(row, 6, item_alerta)
            else:
                # Compartir la columna de avisos, conservando ambas señales de auditoría.
                avisos, detalles_aviso = [], []
                if v.get('precio_modificado'):
                    avisos.append("Precio modificado")
                    detalles_aviso.append(v.get('detalle_modificacion') or "Precio editado manualmente en la venta")
                if v.get('tiene_provisorios'):
                    avisos.append("Provisorio")
                    detalles_aviso.append("Incluye artículos provisorios que no pertenecen al stock. Abra el detalle para identificarlos.")
                if avisos:
                    item_alerta = QTableWidgetItem("⚠ " + " / ".join(avisos))
                    item_alerta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item_alerta.setForeground(Qt.GlobalColor.red)
                    item_alerta.setToolTip("\n".join(detalles_aviso))
                else:
                    item_alerta = QTableWidgetItem("Normal")
                    item_alerta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item_alerta.setForeground(Qt.GlobalColor.darkGray)
                self.tabla_ventas.setItem(row, 6, item_alerta)

    def cargar_productos(self, desde, hasta, data=None):
        if data is None:
            data = ReportesManager.get_productos_mas_vendidos(desde, hasta)
        self.tabla_productos.setRowCount(0)
        for p in data:
            row = self.tabla_productos.rowCount()
            self.tabla_productos.insertRow(row)
            self.tabla_productos.setItem(row, 0, QTableWidgetItem(p['codigo_barras'] or ""))
            self.tabla_productos.setItem(row, 1, QTableWidgetItem(p['nombre']))
            self.tabla_productos.setItem(row, 2, QTableWidgetItem(str(p['cant_total'])))
            self.tabla_productos.setItem(row, 3, QTableWidgetItem(f"${p['recaudacion']:.2f}"))

    def cargar_rubros(self, desde, hasta, data=None):
        if data is None:
            data = ReportesManager.get_ventas_por_rubro(desde, hasta)
        self.tabla_rubros.setRowCount(0)
        for r in data:
            row = self.tabla_rubros.rowCount()
            self.tabla_rubros.insertRow(row)
            self.tabla_rubros.setItem(row, 0, QTableWidgetItem(r['rubro']))
            
            item_vendido = QTableWidgetItem(f"${r['total_vendido']:.2f}")
            item_vendido.setForeground(Qt.GlobalColor.cyan)
            self.tabla_rubros.setItem(row, 1, item_vendido)
            
            item_costo = QTableWidgetItem(f"${r['costo_total']:.2f}")
            item_costo.setForeground(Qt.GlobalColor.red)
            self.tabla_rubros.setItem(row, 2, item_costo)
            
            item_ganancia = QTableWidgetItem(f"${r['ganancia_neta']:.2f}")
            if r['ganancia_neta'] > 0:
                item_ganancia.setForeground(Qt.GlobalColor.green)
            elif r['ganancia_neta'] < 0:
                item_ganancia.setForeground(Qt.GlobalColor.red)
            self.tabla_rubros.setItem(row, 3, item_ganancia)

    def cargar_cajas(self, desde, hasta, usuario_id=None, data=None):
        if data is None:
            data = ReportesManager.get_cierres_caja(desde, hasta, usuario_id)
        self.tabla_caja.setRowCount(0)
        for c in data:
            row = self.tabla_caja.rowCount()
            self.tabla_caja.insertRow(row)
            
            item_id = QTableWidgetItem(str(c['id']))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_caja.setItem(row, 0, item_id)
            
            usuario = "Desconocido"
            if c.get('usuarios'):
                usuario = c['usuarios'].get('nombre') or c['usuarios'].get('username') or "Desconocido"
            self.tabla_caja.setItem(row, 1, QTableWidgetItem(usuario))
            
            item_estado = QTableWidgetItem(c['estado'])
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_caja.setItem(row, 2, item_estado)
            
            item_apertura = QTableWidgetItem(formatear_fecha_ar(c['fecha_apertura']))
            item_apertura.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_caja.setItem(row, 3, item_apertura)
            
            item_cierre = QTableWidgetItem(formatear_fecha_ar(c['fecha_cierre']) if c.get('fecha_cierre') else "En curso")
            item_cierre.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_caja.setItem(row, 4, item_cierre)
            
            item_ini = QTableWidgetItem(f"${c['monto_inicial']:,.2f}")
            item_ini.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_caja.setItem(row, 5, item_ini)
            
            # Obtener resumen para esperado y diferencia
            if '_esperado' in c:
                esperado = c['_esperado']
            else:
                try:
                    esperado = CajaManager.obtener_resumen(c['id']).get('total_efectivo_esperado', 0.0)
                except Exception:
                    esperado = float(c['monto_inicial'] or 0.0)
                
            item_esp = QTableWidgetItem(f"${esperado:,.2f}")
            item_esp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_caja.setItem(row, 6, item_esp)
            
            if c['monto_cierre'] is not None:
                declarado = float(c['monto_cierre'])
                item_dec = QTableWidgetItem(f"${declarado:,.2f}")
                dif = round(declarado - esperado, 2)
                
                if abs(dif) < 0.01:
                    item_dif = QTableWidgetItem("$ 0.00")
                    item_dif.setForeground(Qt.GlobalColor.green)
                elif dif < 0:
                    item_dif = QTableWidgetItem(f"-${abs(dif):,.2f}")
                    item_dif.setForeground(Qt.GlobalColor.red)
                else:
                    item_dif = QTableWidgetItem(f"+${dif:,.2f}")
                    item_dif.setForeground(Qt.GlobalColor.green)
            else:
                item_dec = QTableWidgetItem("-")
                item_dif = QTableWidgetItem("-")
                
            item_dec.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_dif.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.tabla_caja.setItem(row, 7, item_dec)
            self.tabla_caja.setItem(row, 8, item_dif)

    def cargar_alertas(self, data=None):
        if data is None:
            data = ReportesManager.get_alertas_reposicion()
        self.tabla_alertas.setRowCount(0)
        for a in data:
            row = self.tabla_alertas.rowCount()
            self.tabla_alertas.insertRow(row)
            self.tabla_alertas.setItem(row, 0, QTableWidgetItem(a['codigo_barras'] or ""))
            self.tabla_alertas.setItem(row, 1, QTableWidgetItem(a['nombre']))
            
            # Highlight stock actual
            item_actual = QTableWidgetItem(str(a['stock_actual']))
            item_actual.setForeground(Qt.GlobalColor.red)
            
            self.tabla_alertas.setItem(row, 2, item_actual)
            self.tabla_alertas.setItem(row, 3, QTableWidgetItem(str(a['stock_minimo'])))
            
            # Highlight sugerido
            item_sugerido = QTableWidgetItem(str(a['sugerido_pedir']))
            item_sugerido.setForeground(Qt.GlobalColor.green)
            self.tabla_alertas.setItem(row, 4, item_sugerido)

    def cargar_ganancias(self, desde, hasta, usuario_id=None, data=None):
        if data is None:
            data = ReportesManager.get_reporte_ganancias(desde, hasta, usuario_id)
        totales = data['totales']
        
        ventas = totales['total_vendido']
        costos = totales['costo_total']
        ganancia = totales['ganancia_neta']
        
        rentabilidad = 0.0
        if ventas > 0:
            rentabilidad = (ganancia / ventas) * 100.0
            
        self.lbl_ganancia_ventas.setText(f"${ventas:.2f}")
        self.lbl_ganancia_costo.setText(f"${costos:.2f}")
        self.lbl_ganancia_neta.setText(f"${ganancia:.2f}")
        self.lbl_rentabilidad_pct.setText(f"{rentabilidad:.2f}%")
        
        self.tabla_ganancias.setRowCount(0)
        for g in data['ganancias_por_dia']:
            row = self.tabla_ganancias.rowCount()
            self.tabla_ganancias.insertRow(row)
            self.tabla_ganancias.setItem(row, 0, QTableWidgetItem(g['dia']))
            self.tabla_ganancias.setItem(row, 1, QTableWidgetItem(f"${g['total_vendido']:.2f}"))
            self.tabla_ganancias.setItem(row, 2, QTableWidgetItem(f"${g['costo_total']:.2f}"))
            
            item_ganancia = QTableWidgetItem(f"${g['ganancia_neta']:.2f}")
            if g['ganancia_neta'] > 0:
                item_ganancia.setForeground(Qt.GlobalColor.green)
            elif g['ganancia_neta'] < 0:
                item_ganancia.setForeground(Qt.GlobalColor.red)
            self.tabla_ganancias.setItem(row, 3, item_ganancia)

    def ver_detalle_venta(self, row, column):
        item_id = self.tabla_ventas.item(row, 0)
        if not item_id:
            return
        venta_id = int(item_id.text())
        
        from src.core.ventas_manager import VentasManager
        res_detalles = VentasManager.get_detalles_venta(venta_id)
        
        if isinstance(res_detalles, dict):
            detalles = res_detalles.get('detalles', [])
            info_venta = res_detalles.get('info_venta', {})
        else:
            detalles = res_detalles
            info_venta = {}

        if not detalles:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Detalle", "No hay detalles para esta venta.")
            return

        html_aviso = ""
        nota_comprobante = info_venta.get('nro_comprobante_afip')
        if nota_comprobante and "PRECIO MODIFICADO" in str(nota_comprobante):
            html_aviso = f"""
            <div style="background-color: #FFF3CD; border: 1px solid #FFEBAA; border-radius: 6px; padding: 10px; margin-bottom: 15px; color: #856404; font-size: 12.5px;">
                <b>⚠️ AVISO DE AUDITORÍA:</b> Hubo modificación manual de precio en esta venta.<br>
                <span style="font-size: 11.5px; color: #66512c;">{escape(str(nota_comprobante))}</span>
            </div>
            """

        if info_venta.get('tiene_provisorios') or any(d.get('es_provisorio') for d in detalles):
            html_aviso += '<p style="color: #856404;"><b>⚠ Artículos provisorios:</b> esta venta incluye artículos sin movimiento de stock.</p>'

        es_anulada = info_venta.get('estado') in ('ANULADA', 'CANCELADA')
        html_anulada = ""
        if es_anulada:
            u_anul = escape(str(info_venta.get('usuario_anulacion_nombre') or 'Usuario'))
            f_anul = escape(str(formatear_fecha_ar(info_venta.get('fecha_anulacion'))))
            m_anul = escape(str(info_venta.get('motivo_anulacion') or 'Sin motivo especificado'))
            html_anulada = f"""
            <div style="background-color: #F8D7DA; border: 1.5px solid #F5C6CB; border-radius: 8px; padding: 12px; margin-top: 15px; color: #721C24;">
                <b style="font-size: 13px;">VENTA ANULADA</b><br>
                <div style="margin-top: 6px; font-size: 12px; line-height: 1.5; color: #491217;">
                    <b>Fecha de anulación:</b> {f_anul}<br>
                    <b>Anulada por:</b> {u_anul}<br>
                    <b>Motivo:</b> {m_anul}
                </div>
            </div>
            """

        html = f"""
        {html_aviso}
        <div style="color: #666666; font-weight: bold; margin-bottom: 15px; font-size: 12px; letter-spacing: 1px;">ARTÍCULOS VENDIDOS</div>
        <table width="100%" cellspacing="5">
        """
        total = 0.0
        for d in detalles:
            html += f"""
            <tr>
                <td style="font-size: 14px; padding-bottom: 8px;">{d['cantidad']}x <b style="color: #000000;">{escape(str(d['nombre']))}</b>{' — PROVISORIO (sin stock)' if d.get('es_provisorio') else ''}<br><span style="color: #7f849c; font-size: 12px;">${d['precio_unitario']:.2f} c/u</span></td>
                <td align="right" valign="top" style="color: #000000; font-size: 14px; padding-bottom: 8px;">${d['subtotal']:.2f}</td>
            </tr>
            """
            total += d['subtotal']
            
        html += f"""
        </table>
        <br>
        <hr style="background-color: #E5DFD5; border: none; height: 1px;"/>
        <br>
        <table width="100%">
            <tr>
                <td style="font-size: 14px;"><b>TOTAL DE LA VENTA:</b></td>
                <td align="right"><b style="color: #B09886; font-size: 20px;">${total:.2f}</b></td>
            </tr>
        </table>
        {html_anulada}
        """
        dialog = DialogoDetalleVenta(venta_id, info_venta, html, self)
        dialog.anulacion_exitosa.connect(self.generar_reportes)
        dialog.cambio_metodo_exitoso.connect(self.generar_reportes)
        dialog.exec()

    def mostrar_menu_contextual_ventas(self, pos):
        row = self.tabla_ventas.rowAt(pos.y())
        if row < 0:
            return

        item_id = self.tabla_ventas.item(row, 0)
        item_mp = self.tabla_ventas.item(row, 4)
        if not item_id or not item_mp:
            return

        venta_id = int(item_id.text())
        metodo_actual = item_mp.text().strip().upper()

        item_alerta = self.tabla_ventas.item(row, 6)
        es_anulada = item_alerta is not None and "ANULADA" in item_alerta.text().upper()

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5DFD5;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                color: #2C2520;
            }
            QMenu::item:selected {
                background-color: #F4EFE6;
                color: #2C2520;
            }
            QMenu::item:disabled {
                color: #A09891;
            }
        """)

        act_ver = QAction("👁 Ver Detalle de Venta", self)
        act_ver.triggered.connect(lambda: self.ver_detalle_venta(row, 0))
        menu.addAction(act_ver)

        if not es_anulada and metodo_actual in ('EFECTIVO', 'TRANSFERENCIA'):
            nuevo_metodo = 'TRANSFERENCIA' if metodo_actual == 'EFECTIVO' else 'EFECTIVO'
            texto_accion = f"⇄ Cambiar a {nuevo_metodo.capitalize()}"
            act_cambiar = QAction(texto_accion, self)
            act_cambiar.triggered.connect(lambda: self._cambiar_metodo_desde_tabla(venta_id, metodo_actual, nuevo_metodo))
            menu.addSeparator()
            menu.addAction(act_cambiar)

        menu.exec(self.tabla_ventas.viewport().mapToGlobal(pos))

    def _cambiar_metodo_desde_tabla(self, venta_id: int, metodo_actual: str, nuevo_metodo: str):
        resp = QMessageBox.question(
            self, "Confirmar Cambio de Método de Pago",
            f"¿Desea cambiar el método de pago de la venta #{venta_id:08d}?\n\n"
            f"• Actual: {metodo_actual}\n"
            f"• Nuevo: {nuevo_metodo}\n\n"
            "Los reportes y registros de caja se actualizarán automáticamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resp == QMessageBox.StandardButton.Yes:
            try:
                from src.core.ventas_manager import VentasManager
                VentasManager.cambiar_metodo_pago(venta_id, nuevo_metodo)
                QMessageBox.information(
                    self, "Método Actualizado",
                    f"El método de pago fue cambiado exitosamente a {nuevo_metodo}."
                )
                self.generar_reportes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cambiar el método de pago:\n{str(e)}")
