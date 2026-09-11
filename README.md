# AlbinaNuevo

## Despliegue de ventas atómicas

Antes de distribuir una versión que use el flujo transaccional de ventas, ejecutar una única vez [migrations/20260911_procesar_venta_atomica.sql](migrations/20260911_procesar_venta_atomica.sql) desde el SQL Editor del proyecto Supabase.

La función RPC `procesar_venta_atomica` confirma venta, detalle, stock, caja y cuenta corriente en una misma transacción. Si cualquiera de esas operaciones falla, PostgreSQL revierte todas las demás.

## Publicar una nueva versión

La versión del binario se define en `CURRENT_VERSION` dentro de `src/core/updater.py`. Antes de compilar, actualizarla al mismo número que se usará como tag de GitHub, por ejemplo `1.1.10` y `v1.1.10`.

Para publicar la corrección del actualizador actual:

1. Compilar el ejecutable desde este código.
2. Crear la release `v1.1.10` en GitHub.
3. Adjuntar exactamente `AlbinaPOS_SanMartin.exe` como asset de la release.
4. El cliente que muestra `v1.1.8 → v1.1.9` detectará directamente `v1.1.10`, actualizará una vez y guardará su versión instalada en `%LOCALAPPDATA%\AlbinaAccesorios\installed_version.json`.
