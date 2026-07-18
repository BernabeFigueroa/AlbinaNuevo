import os
import re

ui_dir = os.path.join(os.path.dirname(__file__), 'src', 'ui')

for filename in os.listdir(ui_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(ui_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        
        # Eliminar la línea duplicada sin cerrar la llamada
        # Patrón: self.tabla = QTableWidget(\n        self.tabla = QTableWidget(
        content = re.sub(
            r'self\.tabla\s*=\s*QTableWidget\(\s*\n\s*self\.tabla\s*=\s*QTableWidget\(',
            'self.tabla = QTableWidget(',
            content
        )
        
        # También para tabla_carrito
        content = re.sub(
            r'self\.tabla_carrito\s*=\s*QTableWidget\(\s*\n\s*self\.tabla_carrito\s*=\s*QTableWidget\(',
            'self.tabla_carrito = QTableWidget(',
            content
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed syntax error in {filename}")
