import os
import io
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from PyQt6.QtGui import QImage, QPixmap

def generar_barcode_pixmap(codigo: str) -> QPixmap:
    """
    Genera un QPixmap con el gráfico del código de barras a partir del código string dado.
    Utiliza el estándar Code128 que permite cualquier caracter alfanumérico.
    """
    if not codigo or not str(codigo).strip():
        # Retorna un pixmap vacío si no hay código
        return QPixmap()
    
    codigo_str = str(codigo).strip()
    
    try:
        # Usamos Code128 por defecto
        code_class = barcode.get_barcode_class('code128')
        # Configuración del renderizador
        writer = ImageWriter()
        bc = code_class(codigo_str, writer=writer)
        
        buffer = io.BytesIO()
        bc.write(buffer, options={
            'write_text': False,  # No escribir texto del código dentro de la imagen del barcode, lo dibujamos manualmente controlado
            'module_height': 8.0,
            'module_width': 0.25,
            'quiet_zone': 2.0,
            'background': 'white',
            'foreground': 'black'
        })
        
        buffer.seek(0)
        pil_img = Image.open(buffer)
        
        # Convertir PIL Image a QPixmap
        if pil_img.mode != "RGBA":
            pil_img = pil_img.convert("RGBA")
        
        data = pil_img.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        return pixmap
        
    except Exception as e:
        print(f"Error generando código de barras para '{codigo_str}': {e}")
        return QPixmap()
