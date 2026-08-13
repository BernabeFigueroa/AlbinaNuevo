import time
from src.core.categorias_manager import CategoriasManager
from src.core.proveedores_manager import ProveedoresManager
from src.core.productos_manager import ProductosManager
from src.core.clientes_manager import ClientesManager

class DataCache:
    _productos = None
    _productos_inactivos = None
    _categorias = None
    _proveedores = None
    _clientes = None

    _last_update_productos = 0
    _last_update_categorias = 0
    _last_update_proveedores = 0
    _last_update_clientes = 0
    
    TTL_SECONDS = 300  # 5 minutos de tiempo de vida

    @classmethod
    def get_categorias(cls, force_reload=False):
        now = time.time()
        if cls._categorias is None or force_reload or (now - cls._last_update_categorias > cls.TTL_SECONDS):
            cls._categorias = CategoriasManager.get_all()
            cls._last_update_categorias = now
        return cls._categorias

    @classmethod
    def get_proveedores(cls, force_reload=False):
        now = time.time()
        if cls._proveedores is None or force_reload or (now - cls._last_update_proveedores > cls.TTL_SECONDS):
            cls._proveedores = ProveedoresManager.get_all()
            cls._last_update_proveedores = now
        return cls._proveedores

    @classmethod
    def get_productos(cls, incluir_inactivos=False, force_reload=False):
        now = time.time()
        if incluir_inactivos:
            if cls._productos_inactivos is None or force_reload or (now - cls._last_update_productos > cls.TTL_SECONDS):
                cls._productos_inactivos = ProductosManager.get_all(incluir_inactivos=True)
                cls._last_update_productos = now
            return cls._productos_inactivos
        else:
            if cls._productos is None or force_reload or (now - cls._last_update_productos > cls.TTL_SECONDS):
                cls._productos = ProductosManager.get_all(incluir_inactivos=False)
                cls._last_update_productos = now
            return cls._productos

    @classmethod
    def get_clientes(cls, force_reload=False):
        now = time.time()
        if cls._clientes is None or force_reload or (now - cls._last_update_clientes > cls.TTL_SECONDS):
            cls._clientes = ClientesManager.get_all()
            cls._last_update_clientes = now
        return cls._clientes

    @classmethod
    def invalidate_productos(cls):
        cls._productos = None
        cls._productos_inactivos = None

    @classmethod
    def invalidate_categorias(cls):
        cls._categorias = None

    @classmethod
    def invalidate_proveedores(cls):
        cls._proveedores = None

    @classmethod
    def invalidate_clientes(cls):
        cls._clientes = None

    @classmethod
    def invalidate_all(cls):
        cls.invalidate_productos()
        cls.invalidate_categorias()
        cls.invalidate_proveedores()
        cls.invalidate_clientes()
