import os
import sys

def crear_acceso_directo():
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        path = os.path.join(desktop, "Albina POS - San Martin.lnk")
        target = r"C:\Users\CS\OneDrive\Escritorio\¿\AlbinaNuevo\dist\AlbinaPOS_SanMartin.exe"
        icon = r"C:\Users\CS\OneDrive\Escritorio\¿\AlbinaNuevo\logo-albina.ico"

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = icon
        shortcut.save()
        print("Acceso directo creado correctamente")
    except Exception as e:
        print(f"Error al crear acceso directo: {e}")

if __name__ == "__main__":
    crear_acceso_directo()
