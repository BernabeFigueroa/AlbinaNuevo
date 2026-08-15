from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from src.core.auth_manager import AuthManager
from src.ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Albina Accesorios - Ingreso")
        self.resize(400, 500)
        self.setup_ui()
    def setup_ui(self):
        self.setObjectName("LoginWindow")
        self.setStyleSheet("#LoginWindow { background-color: #FAF8F5; }")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Resolver ruta compatible con PyInstaller (_MEIPASS) o desarrollo local
        import os, sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
        logo_path = os.path.join(base_path, "logo-albina.png")
        icon_path = os.path.join(base_path, "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        elif os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        # Logo
        logo = QLabel()
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(280, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("albina accesorios")
            logo.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        subtitle = QLabel("")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7A7067; margin-bottom: 20px;")
        
        # Campos
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Correo electrónico o Usuario")
        self.email_input.setStyleSheet("border: 2px solid #ddd; border-radius: 8px; padding: 10px; font-size: 14px; background-color: white;")
        self.email_input.setMinimumHeight(40)
        
        pwd_layout = QHBoxLayout()
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(5)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        
        self.toggle_pwd_btn = QPushButton()
        self.toggle_pwd_btn.setIcon(QIcon("assets/icons/visibility.svg"))
        self.toggle_pwd_btn.setMinimumHeight(40)
        self.toggle_pwd_btn.setFixedWidth(40)
        self.toggle_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd_btn.setStyleSheet("background-color: transparent; border: none;")
        self.toggle_pwd_btn.clicked.connect(self.toggle_password)
        
        pwd_layout.addWidget(self.password_input)
        pwd_layout.addWidget(self.toggle_pwd_btn)
        
        # Botón
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        
        # Atajos de teclado (Enter)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Agregar al layout
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addWidget(self.email_input)
        layout.addLayout(pwd_layout)
        layout.addWidget(self.login_btn)
        
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Por favor ingresa correo y contraseña.")
            return
            
        self.login_btn.setText("Conectando...")
        self.login_btn.setEnabled(False)
        
        from src.utils.async_worker import run_async
        
        def on_result(result):
            success, err_msg = result
            if success:
                self.open_main_window()
            else:
                QMessageBox.critical(self, "Error de Ingreso", err_msg)
                self.login_btn.setText("Iniciar Sesión")
                self.login_btn.setEnabled(True)

        def on_error(err):
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado: {err}")
            self.login_btn.setText("Iniciar Sesión")
            self.login_btn.setEnabled(True)

        run_async(AuthManager.login, email, password, on_result=on_result, on_error=on_error)
            
    def toggle_password(self):
        import os, sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            icon_p = os.path.join(base_path, "assets", "icons", "visibility_off.svg")
            self.toggle_pwd_btn.setIcon(QIcon(icon_p))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            icon_p = os.path.join(base_path, "assets", "icons", "visibility.svg")
            self.toggle_pwd_btn.setIcon(QIcon(icon_p))

            
    def open_main_window(self):
        self.main_window = MainWindow()
        self.main_window.showMaximized()
        self.close()
