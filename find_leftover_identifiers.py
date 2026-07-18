import os
import re

ui_dir = os.path.join(os.path.dirname(__file__), 'src', 'ui')

for filename in os.listdir(ui_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(ui_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        
        # Eliminar cualquier identificador suelto que termine en guión bajo y esté solo en su línea
        # Ejemplo: "        filtro_"
        content = re.sub(r'^\s*[a-zA-Z_]+_\s*$', '', content, flags=re.MULTILINE)
        
        # También limpiar expresiones del tipo "self.btn_eliminar" o "self.tabla" sueltas en una línea como no-ops
        content = re.sub(r'^\s*self\.btn_[a-zA-Z_]+\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*self\.tabla\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*self\.cb_[a-zA-Z_]+\s*$', '', content, flags=re.MULTILINE)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned leftover no-ops in {filename}")
