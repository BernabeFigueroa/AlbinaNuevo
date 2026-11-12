# Albina Accesorios v1.2.0

- **Alta de artículos.** Nuevo modal con nombre, costo, utilidad, precios de efectivo y tarjeta, y stock inicial. El sistema asigna el código de barras automáticamente.
- **Edición de artículos.** Abrí una ficha con doble clic. El formulario muestra el nombre original y el ID, resalta la edición con un borde rojo y pide confirmación si cambia el nombre o el código de barras.
- **Carga del catálogo.** Productos carga en segundo plano y permite reintentar si falla la conexión.
- **Historial y comprobantes.** Una migración de Supabase registra los cambios de los artículos y conserva el nombre del producto en las ventas nuevas.

Para habilitar el historial y la conservación del nombre en Supabase, aplicá la migración `migrations/20261112_historial_productos.sql`. Las ventas anteriores mantienen su comportamiento.
