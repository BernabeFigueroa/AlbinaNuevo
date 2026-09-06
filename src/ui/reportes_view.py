from datetime import datetime, timezone, timedelta
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
    QTableWidgetItem, QPushButton, QHeaderView, QDateEdit, QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

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
class ReportesView(QWidget):
    def __init__(self):
        super().__init__()
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
        self.cb_metodo_pago.addItems(["TODOS", "EFECTIVO", "TRANSFERENCIA", "MIXTO", "CUENTA CORRIENTE"])
        filtro_layout.addWidget(self.cb_metodo_pago)
        
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

    def crear_tarjeta_resumen(self, titulo, valor_inicial, color_hex):
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
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #666666; border: none; background: transparent;")
        
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_valor.setStyleSheet(f"color: {color_hex}; border: none; background: transparent;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        
        return frame, lbl_valor

    def setup_tab_ventas(self):
        layout = QVBoxLayout(self.tab_ventas)
        layout.setSpacing(15)
        
        # Resumen
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(15)
        
        self.frame_efectivo, self.lbl_tot_efectivo = self.crear_tarjeta_resumen("EFECTIVO", "$0.00", "#B09886")
        self.frame_transferencia, self.lbl_tot_transferencia = self.crear_tarjeta_resumen("TRANSFERENCIA", "$0.00", "#000000")
        self.frame_general, self.lbl_tot_general = self.crear_tarjeta_resumen("TOTAL GENERAL", "$0.00", "#D99890")
        
        resumen_layout.addWidget(self.frame_efectivo)
        resumen_layout.addWidget(self.frame_transferencia)
        resumen_layout.addWidget(self.frame_general)
        
        layout.addLayout(resumen_layout)
        
        # Grilla
        self.tabla_ventas = QTableWidget(0, 7)
        self.tabla_ventas.setHorizontalHeaderLabels(["Factura Nº", "Fecha y Hora", "Cliente", "Vendedor", "Medio Pago", "Total", "Ajuste Precio"])
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_ventas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_ventas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_ventas.cellDoubleClicked.connect(self.ver_detalle_venta)
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
        try:
            self.cb_vendedor.clear()
            self.cb_vendedor.addItem("TODOS", None)
            vendedores = ReportesManager.get_vendedores()
            for v in vendedores:
                nombre = v.get('nombre') or v.get('username') or 'Sin nombre'
                self.cb_vendedor.addItem(nombre, v['id'])
        except Exception as e:
            print(f"Error al cargar vendedores: {e}")

    def al_cambiar_pestana(self, index):
        if index == 0:
            self.lbl_pago.show()
            self.cb_metodo_pago.show()
            self.lbl_vendedor.show()
            self.cb_vendedor.show()
        elif index in (3, 5):
            self.lbl_pago.hide()
            self.cb_metodo_pago.hide()
            self.lbl_vendedor.show()
            self.cb_vendedor.show()
        else:
            self.lbl_pago.hide()
            self.cb_metodo_pago.hide()
            self.lbl_vendedor.hide()
            self.cb_vendedor.hide()

    def generar_reportes(self):
        try:
            desde = self.dt_desde.date().toString("yyyy-MM-dd")
            hasta = self.dt_hasta.date().toString("yyyy-MM-dd")
            usuario_id = self.cb_vendedor.currentData()
            
            self.cargar_ventas(desde, hasta, usuario_id)
            self.cargar_productos(desde, hasta)
            self.cargar_rubros(desde, hasta)
            self.cargar_cajas(desde, hasta, usuario_id)
            self.cargar_alertas()
            self.cargar_ganancias(desde, hasta, usuario_id)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error al generar reportes", f"Ocurrió un error: {str(e)}")

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


    def cargar_ventas(self, desde, hasta, usuario_id=None):
        metodo = self.cb_metodo_pago.currentText()
        metodo_filtro = None if metodo == "TODOS" else metodo
        data = ReportesManager.get_ventas_por_fecha(desde, hasta, metodo_filtro, usuario_id)
        
        self.lbl_tot_efectivo.setText(f"${data['total_efectivo']:.2f}")
        self.lbl_tot_transferencia.setText(f"${data['total_transferencia']:.2f}")
        self.lbl_tot_general.setText(f"${data['total_general']:.2f}")
        
        self.tabla_ventas.setRowCount(0)
        for v in data['ventas']:
            row = self.tabla_ventas.rowCount()
            self.tabla_ventas.insertRow(row)
            
            item_id = QTableWidgetItem(f"{v['id']:08d}")
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_ventas.setItem(row, 0, item_id)
            
            item_fecha = QTableWidgetItem(formatear_fecha_ar(v['fecha']))
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_ventas.setItem(row, 1, item_fecha)
            
            self.tabla_ventas.setItem(row, 2, QTableWidgetItem(v['cliente'] or "Consumidor Final"))
            self.tabla_ventas.setItem(row, 3, QTableWidgetItem(v['vendedor']))
            
            item_mp = QTableWidgetItem(v['metodo_pago'])
            item_mp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_ventas.setItem(row, 4, item_mp)
            
            item_total = QTableWidgetItem(f"${v['total']:,.2f}")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_ventas.setItem(row, 5, item_total)

            # Columna 6: Alerta de Ajuste de Precio
            if v.get('precio_modificado'):
                item_alerta = QTableWidgetItem("⚠️ Modificado")
                item_alerta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_alerta.setForeground(Qt.GlobalColor.red)
                item_alerta.setToolTip(v.get('detalle_modificacion') or "Precio editado manualmente en la venta")
            else:
                item_alerta = QTableWidgetItem("Normal")
                item_alerta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_alerta.setForeground(Qt.GlobalColor.darkGray)
            self.tabla_ventas.setItem(row, 6, item_alerta)

    def cargar_productos(self, desde, hasta):
        data = ReportesManager.get_productos_mas_vendidos(desde, hasta)
        self.tabla_productos.setRowCount(0)
        for p in data:
            row = self.tabla_productos.rowCount()
            self.tabla_productos.insertRow(row)
            self.tabla_productos.setItem(row, 0, QTableWidgetItem(p['codigo_barras'] or ""))
            self.tabla_productos.setItem(row, 1, QTableWidgetItem(p['nombre']))
            self.tabla_productos.setItem(row, 2, QTableWidgetItem(str(p['cant_total'])))
            self.tabla_productos.setItem(row, 3, QTableWidgetItem(f"${p['recaudacion']:.2f}"))

    def cargar_rubros(self, desde, hasta):
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

    def cargar_cajas(self, desde, hasta, usuario_id=None):
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
            try:
                resumen = CajaManager.obtener_resumen(c['id'])
                esperado = resumen.get('total_efectivo_esperado', 0.0)
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

    def cargar_alertas(self):
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

    def cargar_ganancias(self, desde, hasta, usuario_id=None):
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
                <span style="font-size: 11.5px; color: #66512c;">{nota_comprobante}</span>
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
                <td style="font-size: 14px; padding-bottom: 8px;">{d['cantidad']}x <b style="color: #000000;">{d['nombre']}</b><br><span style="color: #7f849c; font-size: 12px;">${d['precio_unitario']:.2f} c/u</span></td>
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
        """
        dialog = DialogoDetalleModerno(f"Detalle de Venta #{venta_id:08d}", html, self)
        dialog.exec()
