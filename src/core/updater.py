import os
import sys
import json
import urllib.request
import subprocess
from packaging import version
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout, QMessageBox, QApplication

CURRENT_VERSION = "1.0.2"
GITHUB_REPO = "BernabeFigueroa/albina-ecommerce"  # Repositorio oficial de GitHub
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateCheckerThread(QThread):
    update_available = pyqtSignal(dict)  # Emite datos del release si hay actualización
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "AlbinaPOS-AutoUpdater"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    tag_name = data.get("tag_name", "").lstrip("v").strip()
                    
                    if not tag_name:
                        self.no_update.emit()
                        return

                    # Comparar versiones de forma semántica
                    if version.parse(tag_name) > version.parse(CURRENT_VERSION):
                        download_url = None
                        exe_size = 0
                        for asset in data.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                download_url = asset.get("browser_download_url")
                                exe_size = asset.get("size", 0)
                                break
                        
                        if download_url:
                            self.update_available.emit({
                                "version": tag_name,
                                "download_url": download_url,
                                "body": data.get("body", "Mejoras generales y correcciones de errores."),
                                "size": exe_size
                            })
                        else:
                            self.no_update.emit()
                    else:
                        self.no_update.emit()
                else:
                    self.no_update.emit()
        except Exception as e:
            # Si no hay internet o aún no hay release en GitHub, continúa silenciosamente
            self.error_occurred.emit(str(e))


class DownloadWorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, download_url, target_path):
        super().__init__()
        self.download_url = download_url
        self.target_path = target_path

    def run(self):
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "AlbinaPOS-AutoUpdater"}
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                total_size = int(response.headers.get('content-length', 0))
                bytes_downloaded = 0
                block_size = 65536  # 64KB

                with open(self.target_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        bytes_downloaded += len(buffer)
                        f.write(buffer)
                        if total_size > 0:
                            percent = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(percent)

            self.finished.emit(self.target_path)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    def __init__(self, release_info, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.setWindowTitle("Actualización Disponible - Albina Accesorios")
        self.setFixedSize(480, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(f"<b>¡Nueva versión disponible: v{self.release_info['version']}!</b>")
        title.setStyleSheet("font-size: 15px; color: #2C2520;")
        layout.addWidget(title)

        body_text = self.release_info.get('body', '').strip()
        if not body_text:
            body_text = "Se han incluido mejoras de rendimiento y estabilidad."
            
        desc = QLabel(f"Versión actual: v{CURRENT_VERSION}\n\nNovedades:\n{body_text}")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #60564D; font-size: 12px;")
        layout.addWidget(desc)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E5DFD5;
                border-radius: 6px;
                text-align: center;
                height: 22px;
                background-color: #FAF8F5;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #B09886;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #8C7869;")
        self.lbl_status.setVisible(False)
        layout.addWidget(self.lbl_status)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Más tarde")
        self.btn_cancel.setObjectName("btn_neutral")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_update = QPushButton("Actualizar e Instalar")
        self.btn_update.clicked.connect(self.start_download)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_update)
        layout.addLayout(btn_layout)

    def start_download(self):
        self.btn_update.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setVisible(True)
        self.lbl_status.setText("Descargando actualización desde GitHub...")

        current_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath("AlbinaAccesorios.exe")
        target_dir = os.path.dirname(current_exe)
        new_exe_path = os.path.join(target_dir, "AlbinaAccesorios_new.exe")

        self.worker = DownloadWorkerThread(self.release_info["download_url"], new_exe_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_download_error)
        self.worker.start()

    def on_download_finished(self, new_exe_path):
        self.lbl_status.setText("Descarga finalizada. Reiniciando aplicación...")
        apply_update_and_restart(new_exe_path)
        self.accept()

    def on_download_error(self, error_msg):
        self.lbl_status.setText("Error en la descarga.")
        QMessageBox.warning(self, "Error de actualización", f"No se pudo descargar la actualización:\n{error_msg}")
        self.btn_update.setEnabled(True)
        self.btn_cancel.setEnabled(True)


def apply_update_and_restart(new_exe_path):
    """
    Crea un batch script que espera que cierre la app actual,
    reemplaza el .exe viejo por el nuevo y vuelve a abrirlo.
    """
    if not getattr(sys, 'frozen', False):
        QMessageBox.information(None, "Modo Desarrollo", f"Descargado con éxito en:\n{new_exe_path}\n(En modo ejecutable se aplica el reemplazo automático y reinicio)")
        return

    current_exe = sys.executable
    updater_bat = os.path.join(os.path.dirname(current_exe), "update_albina.bat")

    bat_content = f"""@echo off
chcp 65001 > nul
timeout /t 2 /nobreak > nul
:retry
del "{current_exe}" > nul 2>&1
if exist "{current_exe}" (
    timeout /t 1 /nobreak > nul
    goto retry
)
move /y "{new_exe_path}" "{current_exe}" > nul
start "" "{current_exe}"
del "%~f0" > nul 2>&1
exit
"""

    with open(updater_bat, "w", encoding="utf-8") as f:
        f.write(bat_content)

    subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    QApplication.quit()
    sys.exit(0)
