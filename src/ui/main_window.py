from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel
from PyQt6.QtCore import Qt
from src.ui.pos_view import POSView
from src.ui.productos_view import ProductosView
from src.ui.caja_view import CajaView
from src.ui.reportes_view import ReportesView
from src.ui.clientes_view import ClientesView
from src.ui.proveedores_view import ProveedoresView
from src.ui.categorias_view import CategoriasView
from src.ui.deudores_view import DeudoresView
from src.ui.deudas_proveedores_view import DeudasProveedoresView
from src.core.auth_manager import AuthManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Albina Accesorios - Sistema de Gestión")
        self.setMinimumSize(1000, 580)
        self.resize(1200, 720)
        
        # Set Window Icon
        import os, sys
        from PyQt6.QtGui import QIcon
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.setWindowIcon(QIcon(os.path.join(base_path, "logo-albina.png")))
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Menú Lateral (Colores Albina) ---
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(235)
        self.sidebar.setStyleSheet("background-color: #FFFFFF; border-right: 1px solid #E5DFD5;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(4)

        # Título del menú (Logo)
        lbl_brand = QLabel()
        from PyQt6.QtGui import QPixmap
        import os, sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logo_path = os.path.join(base_path, "logo-albina.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            lbl_brand.setPixmap(pixmap.scaled(180, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_brand.setMinimumHeight(55)
            lbl_brand.setStyleSheet("margin-bottom: 6px; border: none; background-color: transparent;")
        else:
            lbl_brand.setText("ALBINA ACCESORIOS")
            lbl_brand.setStyleSheet("font-size: 16px; font-weight: 800; color: #2C2520; margin-bottom: 6px; border: none;")
        
        sidebar_layout.addWidget(lbl_brand)

        # Botones del menú
        self.btn_pos = self.crear_boton_menu("Punto de Venta")
        self.btn_productos = self.crear_boton_menu("Productos")
        self.btn_categorias = self.crear_boton_menu("Categorías/Rubros")
        self.btn_proveedores = self.crear_boton_menu("Proveedores")
        self.btn_deudas_proveedores = self.crear_boton_menu("Cuentas a Pagar (Prov.)")
        self.btn_clientes = self.crear_boton_menu("Clientes")
        self.btn_deudores = self.crear_boton_menu("Cuentas Ctes. (Fiado)")
        self.btn_caja = self.crear_boton_menu("Caja Diaria")
        self.btn_reportes = self.crear_boton_menu("Reportes")

        sidebar_layout.addWidget(self.btn_pos)
        sidebar_layout.addWidget(self.btn_productos)
        sidebar_layout.addWidget(self.btn_categorias)
        sidebar_layout.addWidget(self.btn_proveedores)
        sidebar_layout.addWidget(self.btn_deudas_proveedores)
        sidebar_layout.addWidget(self.btn_clientes)
        sidebar_layout.addWidget(self.btn_deudores)
        sidebar_layout.addWidget(self.btn_caja)
        
        # Ocultar botones según rol
        if AuthManager.is_admin():
            sidebar_layout.addWidget(self.btn_reportes)
        else:
            self.btn_reportes.hide()
            self.btn_categorias.hide()
            self.btn_proveedores.hide()
            self.btn_deudas_proveedores.hide()
            self.btn_clientes.hide()
            
        sidebar_layout.addStretch()
        
        # Info usuario y Cerrar Sesión
        rol = "Admin" if AuthManager.is_admin() else "Empleada"
        lbl_user = QLabel(f"Usuario: {rol}")
        lbl_user.setStyleSheet("color: #000000; font-weight: bold; border: none; font-size: 11px;")
        sidebar_layout.addWidget(lbl_user)
        
        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #7A7067;
                color: #FFFFFF;
                border: none;
                padding: 6px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #000000; }
        """)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)

        # --- Área Central (Stack de Vistas) ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget
        
        # Inicializar vistas (Ojo: Deberán ser adaptadas a Supabase)
        # Solo instanciamos POSView al inicio por defecto
        self.pos_view = POSView()
        self.productos_view = None
        self.categorias_view = None
        self.proveedores_view = None
        self.deudas_proveedores_view = None
        self.clientes_view = None
        self.deudores_view = None
        self.caja_view = None
        self.reportes_view = None
        
        # Agregar vistas al stack
        self.stacked_widget.addWidget(self.pos_view)

        # Conectar botones a las vistas
        self.btn_pos.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.pos_view))
        
        def show_productos():
            if self.productos_view is None:
                self.productos_view = ProductosView()
                self.stacked_widget.addWidget(self.productos_view)
            else:
                self.productos_view.cargar_grilla(force_reload=True)
            self.stacked_widget.setCurrentWidget(self.productos_view)
            
        def show_categorias():
            if self.categorias_view is None:
                self.categorias_view = CategoriasView()
                self.stacked_widget.addWidget(self.categorias_view)
            self.stacked_widget.setCurrentWidget(self.categorias_view)

        def show_proveedores():
            if self.proveedores_view is None:
                self.proveedores_view = ProveedoresView()
                self.stacked_widget.addWidget(self.proveedores_view)
            self.stacked_widget.setCurrentWidget(self.proveedores_view)

        def show_deudas_proveedores():
            if self.deudas_proveedores_view is None:
                self.deudas_proveedores_view = DeudasProveedoresView()
                self.stacked_widget.addWidget(self.deudas_proveedores_view)
            self.stacked_widget.setCurrentWidget(self.deudas_proveedores_view)

        def show_clientes():
            if self.clientes_view is None:
                self.clientes_view = ClientesView()
                self.stacked_widget.addWidget(self.clientes_view)
            self.stacked_widget.setCurrentWidget(self.clientes_view)

        def show_deudores():
            if self.deudores_view is None:
                self.deudores_view = DeudoresView()
                self.stacked_widget.addWidget(self.deudores_view)
            self.stacked_widget.setCurrentWidget(self.deudores_view)

        def show_caja():
            if self.caja_view is None:
                self.caja_view = CajaView()
                self.stacked_widget.addWidget(self.caja_view)
            self.stacked_widget.setCurrentWidget(self.caja_view)

        def show_reportes():
            if self.reportes_view is None:
                self.reportes_view = ReportesView()
                self.stacked_widget.addWidget(self.reportes_view)
            self.stacked_widget.setCurrentWidget(self.reportes_view)

        self.btn_productos.clicked.connect(show_productos)
        self.btn_categorias.clicked.connect(show_categorias)
        self.btn_proveedores.clicked.connect(show_proveedores)
        self.btn_deudas_proveedores.clicked.connect(show_deudas_proveedores)
        self.btn_clientes.clicked.connect(show_clientes)
        self.btn_deudores.clicked.connect(show_deudores)
        self.btn_caja.clicked.connect(show_caja)
        self.btn_reportes.clicked.connect(show_reportes)

        # Conectar señal para ocultar/mostrar menú
        self.pos_view.toggle_sidebar.connect(self.toggle_sidebar_visibility)

        # Agregar todo al layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)

        # Establecer padding 0
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.btn_pos.setChecked(True)
        self.stacked_widget.setCurrentWidget(self.pos_view)

        # Ocultar menú lateral por defecto si es empleada
        if not AuthManager.is_admin():
            self.sidebar.setVisible(False)

    def toggle_sidebar_visibility(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def crear_boton_menu(self, texto):
        btn = QPushButton(texto)
        btn.setFixedHeight(38)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #000000;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
                padding-left: 14px;
            }
            QPushButton:hover {
                background-color: #ACA096;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #7A7067;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #B09886;
                color: #FFFFFF;
                border-left: 4px solid #FFFFFF;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
            }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn
        
    def logout(self):
        AuthManager.logout()
        from src.ui.login_window import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()
