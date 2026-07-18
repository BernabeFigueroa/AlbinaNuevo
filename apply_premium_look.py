import os
import re

ui_dir = os.path.join(os.path.dirname(__file__), 'src', 'ui')

for filename in os.listdir(ui_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(ui_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        
        # 1. Reemplazar estilos de botones para darles un aspecto premium uniforme (con padding, min-height y color correcto)
        # Buscar botones normales y aplicarles estilo boutique con texto blanco
        content = re.sub(
            r'self\.btn_([a-zA-Z_]+)\.setStyleSheet\("background-color:\s*#B09886;[^"]*"\)',
            r'self.btn_\1.setStyleSheet("QPushButton { background-color: #B09886; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px; min-height: 35px; border: none; } QPushButton:hover { background-color: #9C8573; }")',
            content
        )
        
        # Eliminar / peligro
        content = re.sub(
            r'self\.btn_([a-zA-Z_]*eliminar[a-zA-Z_]*)\.setStyleSheet\("background-color:\s*#D99890;[^"]*"\)',
            r'self.btn_\1.setStyleSheet("QPushButton { background-color: #D99890; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px; min-height: 35px; border: none; } QPushButton:hover { background-color: #C5847C; }")',
            content
        )
        
        # Ver ficha / limpiar (neutros)
        content = re.sub(
            r'self\.btn_([a-zA-Z_]*(?:ficha|limpiar)[a-zA-Z_]*)\.setStyleSheet\("background-color:\s*(?:#000000|#ACA096);[^"]*"\)',
            r'self.btn_\1.setStyleSheet("QPushButton { background-color: #ACA096; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px; min-height: 35px; border: none; } QPushButton:hover { background-color: #918A83; }")',
            content
        )

        # 2. Corregir el color de los campos de entrada (QLineEdit y QComboBox) para darles altura
        content = re.sub(
            r'self\.(txt_[a-zA-Z_]+)\s*=\s*QLineEdit\(\)',
            r'self.\1 = QLineEdit()\n        self.\1.setStyleSheet("QLineEdit { background-color: #FFFFFF; border: 1px solid #ACA096; border-radius: 6px; padding: 6px 10px; color: #2C2520; } QLineEdit:focus { border: 1px solid #B09886; }")',
            content
        )
        content = re.sub(
            r'self\.(cb_[a-zA-Z_]+)\s*=\s*QComboBox\(\)',
            r'self.\1 = QComboBox()\n        self.\1.setStyleSheet("QComboBox { background-color: #FFFFFF; border: 1px solid #ACA096; border-radius: 6px; padding: 6px 10px; color: #2C2520; } QComboBox:focus { border: 1px solid #B09886; }")',
            content
        )

        # 3. Corregir el menú lateral de main_window.py
        if filename == 'main_window.py':
            # Cambiar fondo del stacked widget para que las tarjetas resalten
            content = content.replace(
                'self.stacked_widget.setStyleSheet("background-color: #FFFFFF;")',
                'self.stacked_widget.setStyleSheet("background-color: #FAF8F5;")'
            )
            # Cambiar checked button del sidebar para alto contraste
            content = content.replace(
                'QPushButton:checked {\n                background-color: #E5DFD5;\n                color: #FFFFFF;',
                'QPushButton:checked {\n                background-color: #B09886;\n                color: #FFFFFF;'
            )
            content = content.replace(
                'QPushButton:hover {\n                background-color: #E5DFD5;\n                color: #FFFFFF;',
                'QPushButton:hover {\n                background-color: #ACA096;\n                color: #FFFFFF;'
            )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Premium style applied to {filename}")
