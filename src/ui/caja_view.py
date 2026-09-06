from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QFrame, QGridLayout, QSpacerItem, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime, timezone, timedelta
try:
    import zoneinfo
except ImportError:
    zoneinfo = None

from src.core.caja_manager import CajaManager
from src.core.auth_manager import AuthManager

class DialogoDetalleCierre(QDialog):
    def __init__(self, titulo, contenido_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
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
                padding: 8px 26px;
                font-weight: 600;
                font-size: 13px;
                min-height: 34px;
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
        layout.setSpacing(16)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520;")
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
        frame_layout.setContentsMargins(18, 18, 18, 18)
        
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


class DialogoCerrarTurno(QDialog):
    def __init__(self, esperado: float, usuario_nombre: str, parent=None):
        super().__init__(parent)
        self.esperado = float(esperado)
        self.usuario_nombre = usuario_nombre
        self.declarado = 0.0
        self.diferencia = 0.0
        self.motivo = ""
        
        self.setWindowTitle("Arqueo y Cierre de Turno")
        self.setMinimumWidth(500)
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
                border: 1px solid #D5CFC7;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                min-height: 32px;
            }
            QLineEdit:focus {
                border: 1.5px solid #8C7869;
                background-color: #FCFBF9;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        
        lbl_tit = QLabel("Cierre de Turno y Arqueo de Caja")
        lbl_tit.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: #2C2520;")
        layout.addWidget(lbl_tit)
        
        # Tarjeta resumen informativo
        card_info = QFrame()
        card_info.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 10px; padding: 10px;")
        layout_info = QGridLayout(card_info)
        layout_info.setSpacing(8)
        
        lbl_u_tit = QLabel("Usuario que cierra:")
        lbl_u_tit.setFont(QFont("Segoe UI", 11))
        lbl_u_tit.setStyleSheet("color: #7A7067;")
        self.lbl_u_val = QLabel(self.usuario_nombre)
        self.lbl_u_val.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_u_val.setStyleSheet("color: #2C2520;")
        layout_info.addWidget(lbl_u_tit, 0, 0)
        layout_info.addWidget(self.lbl_u_val, 0, 1)
        
        lbl_esp_tit = QLabel("Efectivo esperado (Sistema):")
        lbl_esp_tit.setFont(QFont("Segoe UI", 12))
        lbl_esp_tit.setStyleSheet("color: #7A7067;")
        self.lbl_esp_val = QLabel(f"$ {self.esperado:,.2f}")
        self.lbl_esp_val.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.lbl_esp_val.setStyleSheet("color: #B09886;")
        self.lbl_esp_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout_info.addWidget(lbl_esp_tit, 1, 0)
        layout_info.addWidget(self.lbl_esp_val, 1, 1)
        
        layout.addWidget(card_info)
        
        # Entrada de dinero contado
        lbl_dec = QLabel("Efectivo real contado en caja: ($)")
        lbl_dec.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_dec.setStyleSheet("color: #2C2520; margin-top: 4px;")
        layout.addWidget(lbl_dec)
        
        self.txt_declarado = QLineEdit(f"{self.esperado:.2f}")
        self.txt_declarado.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.txt_declarado.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_declarado.textChanged.connect(self.recalcular_diferencia)
        layout.addWidget(self.txt_declarado)
        
        # Panel de diferencia / resultado
        self.card_dif = QFrame()
        self.card_dif.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 10px; padding: 10px;")
        layout_dif = QHBoxLayout(self.card_dif)
        
        self.lbl_dif_tit = QLabel("DIFERENCIA:")
        self.lbl_dif_tit.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout_dif.addWidget(self.lbl_dif_tit)
        
        self.lbl_dif_val = QLabel("$ 0.00 (Exacto)")
        self.lbl_dif_val.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_dif_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout_dif.addWidget(self.lbl_dif_val)
        
        layout.addWidget(self.card_dif)
        
        # Campo observaciones
        lbl_mot = QLabel("Observaciones / Motivo (en caso de diferencia):")
        lbl_mot.setFont(QFont("Segoe UI", 10))
        lbl_mot.setStyleSheet("color: #7A7067;")
        layout.addWidget(lbl_mot)
        
        self.txt_motivo = QLineEdit()
        layout.addWidget(self.txt_motivo)
        
        layout.addSpacing(6)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #ACA096;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                min-height: 34px;
            }
            QPushButton:hover { background-color: #918A83; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        
        self.btn_confirmar = QPushButton("CONFIRMAR CIERRE")
        self.btn_confirmar.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #D99890;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                min-height: 34px;
            }
            QPushButton:hover { background-color: #C5847C; }
            QPushButton:pressed { background-color: #A96860; }
        """)
        self.btn_confirmar.clicked.connect(self.validar_y_cerrar)
        btn_layout.addWidget(self.btn_confirmar)
        
        layout.addLayout(btn_layout)
        
        # Inicializar cálculo
        self.recalcular_diferencia()

    def recalcular_diferencia(self):
        txt = self.txt_declarado.text().replace("$", "").replace(" ", "").replace(",", ".").strip()
        try:
            dec = float(txt) if txt else 0.0
        except ValueError:
            self.lbl_dif_val.setText("Monto inválido")
            self.lbl_dif_val.setStyleSheet("color: #D99890;")
            return
            
        dif = round(dec - self.esperado, 2)
        if abs(dif) < 0.01:
            self.lbl_dif_val.setText("$ 0.00 (Cuadrado)")
            self.lbl_dif_val.setStyleSheet("color: #2E7D32;")
        elif dif < 0:
            self.lbl_dif_val.setText(f"-${abs(dif):,.2f} (FALTANTE)")
            self.lbl_dif_val.setStyleSheet("color: #C62828;")
        else:
            self.lbl_dif_val.setText(f"+${dif:,.2f} (SOBRANTE)")
            self.lbl_dif_val.setStyleSheet("color: #2E7D32;")

    def validar_y_cerrar(self):
        txt = self.txt_declarado.text().replace("$", "").replace(" ", "").replace(",", ".").strip()
        try:
            self.declarado = float(txt)
            if self.declarado < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Atención", "Por favor ingrese un monto de efectivo válido (0 o superior).")
            self.txt_declarado.setFocus()
            return
            
        self.diferencia = round(self.declarado - self.esperado, 2)
        self.motivo = self.txt_motivo.text().strip()
        self.accept()

def formatear_fecha_ar(fecha_str):
    if not fecha_str:
        return "-"
    try:
        dt = datetime.fromisoformat(str(fecha_str).replace('Z', '+00:00'))
        if zoneinfo:
            try:
                dt = dt.astimezone(zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires"))
            except Exception:
                dt = dt.astimezone(timezone(timedelta(hours=-3)))
        else:
            dt = dt.astimezone(timezone(timedelta(hours=-3)))
        return dt.strftime("%d/%m/%Y %H:%M hs")
    except Exception:
        # Fallback simple
        return str(fecha_str)[:16].replace("T", " ")

class CajaView(QWidget):
    def __init__(self):
        super().__init__()
        self.sesion_activa = None
        self.init_ui()
        self.actualizar_estado()

    def crear_tarjeta(self, titulo=None):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #E5DFD5; border-radius: 12px; }
            QLabel { border: none; }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        
        if titulo:
            lbl_titulo = QLabel(titulo)
            lbl_titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            lbl_titulo.setStyleSheet("color: #000000;")
            layout.addWidget(lbl_titulo)
            
            linea = QFrame()
            linea.setFrameShape(QFrame.Shape.HLine)
            layout.addWidget(linea)
            
        return frame, layout

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 12, 16, 12)
        layout_principal.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("CAJA DIARIA")
        lbl_titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C2520;")
        header_layout.addWidget(lbl_titulo)
        
        self.lbl_estado_caja = QLabel("Estado: CERRADA")
        self.lbl_estado_caja.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_estado_caja.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.lbl_estado_caja)
        
        layout_principal.addLayout(header_layout)

        # Main Content Layout (Split Left and Right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # --- LEFT PANEL (Apertura y Movimientos) ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # Apertura de Caja
        self.frame_apertura, apertura_layout = self.crear_tarjeta("Apertura de Turno")
        
        form_apertura = QHBoxLayout()
        lbl_monto = QLabel("Monto Inicial en Caja: $")
        lbl_monto.setFont(QFont("Segoe UI", 14))
        lbl_monto.setStyleSheet("color: #7A7067;")
        form_apertura.addWidget(lbl_monto)
        
        self.txt_monto_inicial = QLineEdit("0.00")
        self.txt_monto_inicial.setFont(QFont("Segoe UI", 14))
        self.txt_monto_inicial.setFixedWidth(150)
        self.txt_monto_inicial
        form_apertura.addWidget(self.txt_monto_inicial)
        form_apertura.addStretch()
        apertura_layout.addLayout(form_apertura)
        
        self.btn_abrir_caja = QPushButton("ABRIR CAJA")
        self.btn_abrir_caja.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_abrir_caja.setStyleSheet("""
            QPushButton { background-color: #B09886; color: #000000; border-radius: 6px; padding: 12px; }
            QPushButton:hover { background-color: #A2E8C8; }
        """)
        self.btn_abrir_caja.clicked.connect(self.abrir_caja)
        apertura_layout.addWidget(self.btn_abrir_caja)
        
        left_panel.addWidget(self.frame_apertura)

        # Movimientos Manuales
        self.frame_movimientos, mov_layout = self.crear_tarjeta("Registrar Movimiento")
        
        grid_mov = QGridLayout()
        grid_mov.setSpacing(15)
        
        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("color: #7A7067; font-size: 14px;")
        grid_mov.addWidget(lbl_tipo, 0, 0)
        
        self.cb_tipo_mov = QComboBox()

        self.cb_tipo_mov.addItems(["INGRESO", "EGRESO"])

        grid_mov.addWidget(self.cb_tipo_mov, 0, 1)

        lbl_monto_mov = QLabel("Monto: $")
        lbl_monto_mov.setStyleSheet("color: #7A7067; font-size: 14px;")
        grid_mov.addWidget(lbl_monto_mov, 0, 2)
        
        self.txt_monto_mov = QLineEdit("0.00")
        self.txt_monto_mov
        grid_mov.addWidget(self.txt_monto_mov, 0, 3)

        lbl_desc = QLabel("Descripción:")
        lbl_desc.setStyleSheet("color: #7A7067; font-size: 14px;")
        grid_mov.addWidget(lbl_desc, 1, 0)
        
        self.txt_desc_mov = QLineEdit()
        self.txt_desc_mov
        self.txt_desc_mov.setPlaceholderText("Ej. Pago a proveedor, Retiro...")
        self.txt_desc_mov
        grid_mov.addWidget(self.txt_desc_mov, 1, 1, 1, 3)
        
        mov_layout.addLayout(grid_mov)

        self.btn_registrar_mov = QPushButton("REGISTRAR MOVIMIENTO")
        self.btn_registrar_mov.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_registrar_mov.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_registrar_mov.setStyleSheet("""
            QPushButton {
                background-color: #B09886;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #9C8573;
            }
            QPushButton:pressed {
                background-color: #8C7869;
            }
        """)
        self.btn_registrar_mov.clicked.connect(self.registrar_movimiento)
        mov_layout.addWidget(self.btn_registrar_mov)

        left_panel.addWidget(self.frame_movimientos)
        
        # Tabla de Movimientos de la sesión actual
        self.frame_tabla, tabla_layout = self.crear_tarjeta("Movimientos Registrados")
        self.frame_tabla.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla_movs = QTableWidget(0, 4)
        self.tabla_movs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla_movs.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción", "Monto"])
        self.tabla_movs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_movs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_movs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_movs.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_movs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_movs.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_movs.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_movs.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla_layout.addWidget(self.tabla_movs)
        left_panel.addWidget(self.frame_tabla, 1)

        content_layout.addLayout(left_panel, 1)

        # --- RIGHT PANEL (Resumen) ---
        self.frame_cierre, cierre_layout = self.crear_tarjeta("Resumen de Caja")
        
        self.grid_resumen = QGridLayout()
        self.grid_resumen.setSpacing(10)
        
        # Diccionario para guardar las referencias a los labels de valores
        self.lbl_valores = {}
        
        campos = [
            ("Saldo Inicial", "monto_inicial", "#7A7067"),
            ("Ventas Efectivo", "ventas_efectivo", "#B09886"),
            ("Ventas Transferencia", "ventas_transferencia", "#B09886"),
            ("Ventas Fiadas", "ventas_fiadas", "#7A7067"),
            ("Cobros Deuda (Evo)", "pagos_deuda_efectivo", "#B09886"),
            ("Cobros Deuda (Trans)", "pagos_deuda_transferencia", "#B09886"),
            ("Ingresos Manuales", "ingresos_manuales", "#B09886"),
            ("Egresos Manuales", "egresos_manuales", "#D99890"),
        ]
        
        row = 0
        for titulo, clave, color in campos:
            lbl_tit = QLabel(titulo)
            lbl_tit.setFont(QFont("Segoe UI", 12))
            lbl_tit.setStyleSheet("color: #7A7067;")
            
            lbl_val = QLabel("$ 0.00")
            lbl_val.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl_val.setStyleSheet(f"color: {color};")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.grid_resumen.addWidget(lbl_tit, row, 0)
            self.grid_resumen.addWidget(lbl_val, row, 1)
            self.lbl_valores[clave] = lbl_val
            row += 1
            
        # Linea divisoria
        linea_res = QFrame()
        linea_res.setFrameShape(QFrame.Shape.HLine)
        linea_res
        self.grid_resumen.addWidget(linea_res, row, 0, 1, 2)
        row += 1
        
        # Saldo Efectivo
        lbl_saldo_tit = QLabel("SALDO EFECTIVO CAJA")
        lbl_saldo_tit.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_saldo_tit.setStyleSheet("color: #2C2520;")
        
        self.lbl_saldo_efectivo = QLabel("$ 0.00")
        self.lbl_saldo_efectivo.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.lbl_saldo_efectivo.setStyleSheet("color: #B09886;")
        self.lbl_saldo_efectivo.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.grid_resumen.addWidget(lbl_saldo_tit, row, 0)
        self.grid_resumen.addWidget(self.lbl_saldo_efectivo, row, 1)
        row += 1
        
        # Total Vendido
        lbl_tot_tit = QLabel("TOTAL VENDIDO")
        lbl_tot_tit.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_tot_tit.setStyleSheet("color: #7A7067;")
        
        self.lbl_total_vendido = QLabel("$ 0.00")
        self.lbl_total_vendido.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_total_vendido.setStyleSheet("color: #000000;")
        self.lbl_total_vendido.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.grid_resumen.addWidget(lbl_tot_tit, row, 0)
        self.grid_resumen.addWidget(self.lbl_total_vendido, row, 1)
        
        cierre_layout.addLayout(self.grid_resumen)
        
        cierre_layout.addStretch()
        
        self.btn_cerrar_caja = QPushButton("CERRAR TURNO")
        self.btn_cerrar_caja.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.btn_cerrar_caja.setStyleSheet("""
            QPushButton { background-color: #D99890; color: #000000; border-radius: 8px; padding: 15px; }
            QPushButton:hover { background-color: #E8A2A2; }
            QPushButton:pressed { background-color: #CC7676; }
        """)
        self.btn_cerrar_caja.clicked.connect(self.cerrar_caja)
        cierre_layout.addWidget(self.btn_cerrar_caja)

        content_layout.addWidget(self.frame_cierre, 1)

        layout_principal.addLayout(content_layout)

    def actualizar_estado(self):
        self.sesion_activa = CajaManager.obtener_sesion_activa()
        
        if self.sesion_activa:
            fecha_apertura_limpia = formatear_fecha_ar(self.sesion_activa.get('fecha_apertura'))
            self.lbl_estado_caja.setText(f"● ABIERTA (Inicio: {fecha_apertura_limpia})")
            self.lbl_estado_caja.setStyleSheet("color: #B09886;")
            self.frame_apertura.setVisible(False)
            self.frame_movimientos.setVisible(True)
            self.frame_tabla.setVisible(True)
            self.frame_cierre.setVisible(True)
            self.cargar_resumen()
        else:
            self.lbl_estado_caja.setText("○ CERRADA")
            self.lbl_estado_caja.setStyleSheet("color: #D99890;")
            self.frame_apertura.setVisible(True)
            self.frame_movimientos.setVisible(False)
            self.frame_tabla.setVisible(False)
            self.frame_cierre.setVisible(False)

    def abrir_caja(self):
        try:
            monto = float(self.txt_monto_inicial.text())
            CajaManager.abrir_caja(monto)
            self.actualizar_estado()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la caja:\n{str(e)}")

    def registrar_movimiento(self):
        if not self.sesion_activa:
            return
            
        try:
            tipo = self.cb_tipo_mov.currentText()
            monto = float(self.txt_monto_mov.text())
            desc = self.txt_desc_mov.text().strip()
            
            if monto <= 0:
                QMessageBox.warning(self, "Error", "El monto debe ser mayor a 0.")
                return
            if not desc:
                QMessageBox.warning(self, "Error", "Debe ingresar una descripción.")
                return

            CajaManager.registrar_movimiento(self.sesion_activa['id'], tipo, monto, "EFECTIVO", desc)
            self.txt_monto_mov.setText("0.00")
            self.txt_desc_mov.clear()
            self.cargar_resumen()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al registrar:\n{str(e)}")

    def cargar_resumen(self):
        if not self.sesion_activa:
            return
            
        resumen = CajaManager.obtener_resumen(self.sesion_activa['id'])
        
        for clave, lbl in self.lbl_valores.items():
            valor = resumen.get(clave, 0.0)
            lbl.setText(f"$ {valor:,.2f}")
            
        self.lbl_saldo_efectivo.setText(f"$ {resumen.get('total_efectivo_esperado', 0.0):,.2f}")
        self.lbl_total_vendido.setText(f"$ {resumen.get('total_vendido', 0.0):,.2f}")
        
        # Cargar tabla de movimientos
        self.tabla_movs.setRowCount(0)
        movimientos = CajaManager.obtener_movimientos(self.sesion_activa['id'])
        for m in movimientos:
            row = self.tabla_movs.rowCount()
            self.tabla_movs.insertRow(row)
            
            fecha_str = formatear_fecha_ar(m.get('fecha'))
            item_fecha = QTableWidgetItem(fecha_str)
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_movs.setItem(row, 0, item_fecha)
            
            item_tipo = QTableWidgetItem(m['tipo'])
            item_tipo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if 'INGRESO' in m['tipo'] or 'VENTA' in m['tipo'] or m['tipo'] == 'PAGO_CTA_CTE':
                item_tipo.setForeground(Qt.GlobalColor.green)
            else:
                item_tipo.setForeground(Qt.GlobalColor.red)
            self.tabla_movs.setItem(row, 1, item_tipo)
            
            item_desc = QTableWidgetItem(m['descripcion'])
            item_desc.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_movs.setItem(row, 2, item_desc)
            
            item_monto = QTableWidgetItem(f"$ {m['monto']:,.2f}")
            item_monto.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_movs.setItem(row, 3, item_monto)

    def cerrar_caja(self):
        if not self.sesion_activa:
            return
            
        try:
            resumen = CajaManager.obtener_resumen(self.sesion_activa['id'])
            esperado = resumen['total_efectivo_esperado']
            
            user = AuthManager.get_current_user()
            nombre_usuario = "Admin" if AuthManager.is_admin() else "Empleada"
            if user and hasattr(user, 'email') and user.email:
                nombre_usuario = f"{nombre_usuario} ({user.email})"
            
            dlg = DialogoCerrarTurno(esperado, nombre_usuario, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
                
            declarado = dlg.declarado
            motivo = dlg.motivo
            diferencia = round(declarado - esperado, 2)
            
            resultado = CajaManager.cerrar_caja(declarado, esperado, motivo)
            
            # Modal moderno y estilizado de confirmación con detalle completo
            dif_color = "#2E7D32" if abs(diferencia) < 0.01 else ("#C62828" if diferencia < 0 else "#2E7D32")
            dif_texto = "$ 0.00 (Exacto)" if abs(diferencia) < 0.01 else (f"-${abs(diferencia):,.2f} (FALTANTE)" if diferencia < 0 else f"+${diferencia:,.2f} (SOBRANTE)")
            
            html_exito = f"""
            <table width="100%" cellspacing="8" cellpadding="0" style="font-family: 'Segoe UI', sans-serif;">
                <tr>
                    <td style="color: #7A7067; font-size: 13px;">Usuario responsable:</td>
                    <td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">{nombre_usuario}</td>
                </tr>
                <tr>
                    <td style="color: #7A7067; font-size: 13px;">Efectivo esperado por sistema:</td>
                    <td align="right" style="color: #2C2520; font-weight: 600; font-size: 13px;">$ {esperado:,.2f}</td>
                </tr>
                <tr>
                    <td style="color: #7A7067; font-size: 13px;">Efectivo declarado en caja:</td>
                    <td align="right" style="color: #B09886; font-weight: 700; font-size: 15px;">$ {declarado:,.2f}</td>
                </tr>
                <tr>
                    <td style="color: #7A7067; font-size: 13px;">Diferencia de arqueo:</td>
                    <td align="right" style="color: {dif_color}; font-weight: 700; font-size: 14px;">{dif_texto}</td>
                </tr>
            """
            if motivo:
                html_exito += f"""
                <tr>
                    <td style="color: #7A7067; font-size: 12px; vertical-align: top;">Observaciones:</td>
                    <td align="right" style="color: #7A7067; font-style: italic; font-size: 12px;">{motivo}</td>
                </tr>
                """
            html_exito += "</table>"
            
            dlg_res = DialogoDetalleCierre("Turno Cerrado Correctamente", html_exito, self)
            dlg_res.exec()
            
            self.actualizar_estado()
        except Exception as e:
            QMessageBox.critical(self, "Error al Cerrar Turno", f"Fallo al registrar el cierre de caja:\n{str(e)}")

    def showEvent(self, event):
        super().showEvent(event)
        self.actualizar_estado()
