import os
import re

ui_dir = os.path.join(os.path.dirname(__file__), 'src', 'ui')

for filename in os.listdir(ui_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(ui_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        
        # 1. Eliminar hojas de estilo en línea para QFrame, QLineEdit, QComboBox, QPushButton
        # Reemplazar setStyleSheet en controles comunes por una cadena vacía
        content = re.sub(
            r'\.setStyleSheet\("QPushButton[^"]*"\)',
            r'',
            content
        )
        content = re.sub(
            r'\.setStyleSheet\("QLineEdit[^"]*"\)',
            r'',
            content
        )
        content = re.sub(
            r'\.setStyleSheet\("QComboBox[^"]*"\)',
            r'',
            content
        )
        content = re.sub(
            r'\.setStyleSheet\("QTableWidget[^"]*"\)',
            r'',
            content
        )
        content = re.sub(
            r'frame\.setStyleSheet\("QFrame[^"]*"\)',
            r'',
            content
        )
        
        # Eliminar cualquier setStyleSheet en línea genérico que contenga colores anteriores
        content = re.sub(
            r'\.setStyleSheet\("background-color:\s*#[0-9A-Fa-f]{6};[^"]*"\)',
            r'',
            content
        )
        
        # 2. Asignar ObjectNames a los botones para poder estilizarlos desde el CSS global
        content = re.sub(
            r'self\.btn_([a-zA-Z_]*(?:grabar|guardar|cobrar|confirmar|nuevo|buscar|actualizar|duplicar|restaurar)[a-zA-Z_]*)\s*=\s*QPushButton\(([^)]*)\)',
            r'self.btn_\1 = QPushButton(\2)\n        self.btn_\1.setObjectName("btn_primary")',
            content
        )
        content = re.sub(
            r'self\.btn_([a-zA-Z_]*eliminar[a-zA-Z_]*)\s*=\s*QPushButton\(([^)]*)\)',
            r'self.btn_\1 = QPushButton(\2)\n        self.btn_\1.setObjectName("btn_danger")',
            content
        )
        content = re.sub(
            r'self\.btn_([a-zA-Z_]*(?:cancelar|anular|salir|ficha|limpiar)[a-zA-Z_]*)\s*=\s*QPushButton\(([^)]*)\)',
            r'self.btn_\1 = QPushButton(\2)\n        self.btn_\1.setObjectName("btn_neutral")',
            content
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Boutique architecture applied to {filename}")
