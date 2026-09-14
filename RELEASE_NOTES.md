# Registro de cambios

## 2026-09-14 (v1.1.13)

- **Anulación integral de ventas**:
  - Posibilidad de anular ventas directamente desde la vista de detalle en la sección de Reportes con requerimiento de motivo y autorización.
  - Reintegro automático al stock de los artículos correspondientes a la venta anulada (excluyendo artículos provisorios).
  - Cancelación automática de la deuda generada en cuenta corriente si la venta fue realizada a crédito / fiado.
  - Trazabilidad y ajuste en movimientos de caja, preservando el registro de auditoría con fecha, usuario y motivo.
  - Nuevo filtro por estado en el listado de ventas (Todas, Realizadas, Anuladas) y diferenciación visual inmediata.
- **ReportesManager y métricas de negocio**:
  - Implementación centralizada de `ReportesManager` para la generación eficiente de métricas de ventas, rentabilidad e inventario.
  - Exclusión consistente de ventas anuladas en los cálculos de facturación, costos y ganancias brutas.
  - Incorporación del script de migración SQL para anulación transaccional atómica (`migrations/20260914_anulacion_ventas.sql`).

## 2026-09-12

- Rendimiento, fase 1: las vistas de Productos, Clientes, Proveedores y Categorías ahora solicitan sus listas remotas en segundo plano; la interfaz se abre sin esperar a Supabase.
- Rendimiento, fase 1: al regresar a Productos ya no se fuerza una descarga completa que anulaba el caché local de cinco minutos. Las altas, bajas y modificaciones siguen invalidando/recargando los datos cuando corresponde.
- Rendimiento, fase 2: Caja y las cuentas corrientes de clientes/proveedores obtienen sus lecturas iniciales y cambios de selección en segundo plano, sin bloquear la ventana.
- Rendimiento, fase 2: Reportes carga vendedores en segundo plano y, al generar, consulta sólo la pestaña visible. Las demás se solicitan al abrirlas, evitando las seis consultas consecutivas previas.
- Artículos provisorios: al ingresar o modificar el precio unitario contado, el precio tarjeta/lista se calcula automáticamente con el porcentaje `recargo_tarjeta` configurado en Ajustes (por ejemplo, 40 % transforma $100 en $140).
- El precio tarjeta/lista permanece editable manualmente para contemplar excepciones.
- En el POS, el importe aplicado continúa dependiendo del medio de pago: efectivo usa contado; tarjeta y los demás medios usan lista.

## Cambios anteriores

- Se agregó la opción para incluir artículos provisorios en una venta.
- Corrección de visualización en la tabla de clientes.
