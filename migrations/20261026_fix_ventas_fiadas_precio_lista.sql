-- Corrección puntual e idempotente de la venta fiada #799 (Daniela Slame).
--
-- La versión anterior de procesar_venta_atomica guardó los artículos provisorios
-- con el precio de tarjeta (+35 %), aunque el POS mostró el precio de contado.
-- Los artículos de catálogo de esta venta ya quedaron registrados correctamente;
-- por eso esta migración no usa precios actuales de productos ni toca otras ventas.

BEGIN;

DO $$
DECLARE
    v_venta RECORD;
    v_deuda RECORD;
BEGIN
    SELECT id, cliente_id, metodo_pago, estado, subtotal, descuento_total, total
    INTO v_venta
    FROM public.ventas
    WHERE id = 799
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe la venta #799.';
    END IF;

    IF v_venta.metodo_pago <> 'FIADO / CTA. CTE.'
       OR v_venta.estado <> 'COMPLETADA' THEN
        RAISE EXCEPTION 'La venta #799 no es una venta fiada completada.';
    END IF;

    -- Permitir volver a ejecutar la migración sin modificar nada.
    IF v_venta.total = 403984.00
       AND v_venta.descuento_total = 36925.00 THEN
        RETURN;
    END IF;

    -- Evitar corregir datos que hayan sido modificados por otro proceso.
    IF v_venta.subtotal <> 440909.00
       OR v_venta.total <> 440909.00
       OR v_venta.descuento_total <> 0.00 THEN
        RAISE EXCEPTION
            'La venta #799 cambió: subtotal %, descuento %, total %. No se aplicó la corrección.',
            v_venta.subtotal, v_venta.descuento_total, v_venta.total;
    END IF;

    -- Valores de contado que estaban visibles en el POS al confirmar la venta.
    UPDATE public.ventas_detalle
    SET precio_unitario = CASE id
            WHEN 1650 THEN 15000.00
            WHEN 1657 THEN  7500.00
            WHEN 1658 THEN  6000.00
            WHEN 1659 THEN  7000.00
            WHEN 1660 THEN 10000.00
            WHEN 1661 THEN 12000.00
        END,
        subtotal = CASE id
            WHEN 1650 THEN 15000.00
            WHEN 1657 THEN  7500.00
            WHEN 1658 THEN 18000.00
            WHEN 1659 THEN 21000.00
            WHEN 1660 THEN 20000.00
            WHEN 1661 THEN 24000.00
        END
    WHERE venta_id = 799
      AND es_provisorio = true
      AND id IN (1650, 1657, 1658, 1659, 1660, 1661);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se encontraron los artículos provisorios de la venta #799.';
    END IF;

    IF (SELECT COUNT(*) FROM public.ventas_detalle
        WHERE venta_id = 799
          AND id IN (1650, 1657, 1658, 1659, 1660, 1661)) <> 6 THEN
        RAISE EXCEPTION 'La venta #799 no contiene los seis detalles esperados.';
    END IF;

    IF (SELECT SUM(subtotal) FROM public.ventas_detalle WHERE venta_id = 799) <> 403984.00 THEN
        RAISE EXCEPTION 'Los detalles de la venta #799 no suman $403.984. Se revierte la corrección.';
    END IF;

    UPDATE public.ventas
    SET descuento_total = 36925.00,
        total = 403984.00
    WHERE id = 799;

    SELECT id, monto
    INTO v_deuda
    FROM public.cta_cte_movimientos
    WHERE venta_id = 799
      AND tipo = 'DEUDA'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se encontró la deuda asociada a la venta #799.';
    END IF;

    IF v_deuda.monto NOT IN (440909.00, 403984.00) THEN
        RAISE EXCEPTION
            'La deuda de la venta #799 cambió a %. No se aplicó la corrección.',
            v_deuda.monto;
    END IF;

    UPDATE public.cta_cte_movimientos
    SET monto = 403984.00
    WHERE id = v_deuda.id;
END;
$$;

COMMIT;
