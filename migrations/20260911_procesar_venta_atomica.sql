-- Migración: Función RPC transaccional para procesar ventas de forma atómica en PostgreSQL
-- Fecha: 2026-09-11
-- Descripción: Unifica venta, detalles, deducción de stock y movimientos de caja/cta-cte en una sola transacción.

CREATE OR REPLACE FUNCTION public.procesar_venta_atomica(
    p_cliente_id BIGINT,
    p_metodo_pago TEXT,
    p_carrito JSONB,
    p_montos_mixto JSONB DEFAULT NULL,
    p_nota_auditoria TEXT DEFAULT ''
)
RETURNS TABLE (
    venta_id BIGINT,
    subtotal NUMERIC,
    descuento NUMERIC,
    total NUMERIC
)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
    v_usuario_id UUID;
    v_caja_sesion_id BIGINT;
    v_pct_descuento NUMERIC := 0;
    v_subtotal NUMERIC := 0;
    v_total_contado NUMERIC := 0;
    v_total NUMERIC := 0;
    v_descuento_total NUMERIC := 0;
    v_venta_id BIGINT;
    v_item JSONB;
    v_prod_id BIGINT;
    v_cantidad NUMERIC;
    v_p_unit NUMERIC;
    v_p_contado NUMERIC;
    v_costo_unit NUMERIC;
    v_p_unit_efectivo NUMERIC;
    v_subt_item NUMERIC;
    v_mp_key TEXT;
    v_mp_monto NUMERIC;
BEGIN
    -- 1. Validar usuario autenticado
    v_usuario_id := auth.uid();
    IF v_usuario_id IS NULL THEN
        RAISE EXCEPTION 'Debe iniciar sesión para registrar una venta.';
    END IF;

    -- 2. Validar sesión de caja activa
    SELECT id INTO v_caja_sesion_id
    FROM public.caja_sesiones
    WHERE estado = 'ABIERTA'
    ORDER BY id DESC
    LIMIT 1;

    IF v_caja_sesion_id IS NULL THEN
        RAISE EXCEPTION 'Debe abrir la caja antes de realizar una venta.';
    END IF;

    -- 3. Validar carrito no vacío
    IF p_carrito IS NULL OR jsonb_array_length(p_carrito) = 0 THEN
        RAISE EXCEPTION 'No se puede procesar una venta sin artículos.';
    END IF;

    -- 4. Obtener porcentaje de descuento del cliente si aplica
    IF p_cliente_id IS NOT NULL THEN
        SELECT COALESCE(descuento_porcentaje, 0)
        INTO v_pct_descuento
        FROM public.clientes
        WHERE id = p_cliente_id;
    END IF;

    -- 5. Calcular subtotales
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_carrito)
    LOOP
        v_cantidad := (v_item->>'cantidad')::NUMERIC;
        v_p_unit := (v_item->>'precio_unitario')::NUMERIC;
        v_p_contado := COALESCE((v_item->>'precio_contado')::NUMERIC, v_p_unit);

        IF v_cantidad <= 0 THEN
            RAISE EXCEPTION 'La cantidad de cada artículo debe ser mayor a cero.';
        END IF;

        v_subtotal := v_subtotal + (v_cantidad * v_p_unit);
        v_total_contado := v_total_contado + (v_cantidad * v_p_contado);
    END LOOP;

    -- 6. Aplicar reglas de pago y descuento
    IF p_metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA', 'MIXTO') THEN
        IF v_pct_descuento > 0 THEN
            v_total := v_total_contado - (v_total_contado * (v_pct_descuento / 100.0));
        ELSE
            v_total := v_total_contado;
        END IF;
        v_descuento_total := v_subtotal - v_total;
    ELSE
        IF v_pct_descuento > 0 THEN
            v_total := v_subtotal - (v_subtotal * (v_pct_descuento / 100.0));
            v_descuento_total := v_subtotal - v_total;
        ELSE
            v_total := v_subtotal;
            v_descuento_total := 0;
        END IF;
    END IF;

    -- 7. Insertar encabezado de venta
    INSERT INTO public.ventas (
        cliente_id,
        caja_sesion_id,
        usuario_id,
        subtotal,
        descuento_total,
        total,
        metodo_pago,
        nro_comprobante_afip,
        estado
    ) VALUES (
        p_cliente_id,
        v_caja_sesion_id,
        v_usuario_id,
        v_subtotal,
        v_descuento_total,
        v_total,
        p_metodo_pago,
        NULLIF(p_nota_auditoria, ''),
        'COMPLETADA'
    )
    RETURNING id INTO v_venta_id;

    -- 8. Insertar detalles y descontar stock atómicamente
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_carrito)
    LOOP
        v_prod_id := NULLIF(v_item->>'producto_id', '')::BIGINT;
        v_cantidad := (v_item->>'cantidad')::NUMERIC;
        v_p_unit := (v_item->>'precio_unitario')::NUMERIC;
        v_p_contado := COALESCE((v_item->>'precio_contado')::NUMERIC, v_p_unit);
        v_costo_unit := 0.0;

        IF p_metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA', 'MIXTO') THEN
            v_p_unit_efectivo := v_p_contado;
        ELSE
            v_p_unit_efectivo := v_p_unit;
        END IF;

        v_subt_item := v_cantidad * v_p_unit_efectivo;

        IF v_prod_id IS NOT NULL THEN
            SELECT COALESCE(costo_final, 0.0)
            INTO v_costo_unit
            FROM public.productos
            WHERE id = v_prod_id;

            -- Descuento atómico directo en base de datos
            UPDATE public.productos
            SET stock_actual = stock_actual - v_cantidad
            WHERE id = v_prod_id;
        END IF;

        INSERT INTO public.ventas_detalle (
            venta_id,
            producto_id,
            cantidad,
            precio_unitario,
            costo_unitario,
            subtotal
        ) VALUES (
            v_venta_id,
            v_prod_id,
            v_cantidad,
            v_p_unit_efectivo,
            v_costo_unit,
            v_subt_item
        );
    END LOOP;

    -- 9. Registrar movimientos según medio de pago
    IF p_metodo_pago = 'MIXTO' AND p_montos_mixto IS NOT NULL THEN
        FOR v_mp_key, v_mp_monto IN
            SELECT key, value::NUMERIC FROM jsonb_each_text(p_montos_mixto)
        LOOP
            IF v_mp_monto > 0 THEN
                INSERT INTO public.caja_movimientos (
                    caja_sesion_id,
                    tipo,
                    monto,
                    metodo_pago,
                    descripcion
                ) VALUES (
                    v_caja_sesion_id,
                    'VENTA',
                    v_mp_monto,
                    v_mp_key,
                    'Venta #' || v_venta_id || ' (Mixto)'
                );
            END IF;
        END LOOP;
    ELSIF p_metodo_pago != 'FIADO / CTA. CTE.' THEN
        INSERT INTO public.caja_movimientos (
            caja_sesion_id,
            tipo,
            monto,
            metodo_pago,
            descripcion
        ) VALUES (
            v_caja_sesion_id,
            'VENTA',
            v_total,
            p_metodo_pago,
            'Venta #' || v_venta_id
        );
    ELSE
        -- Deuda en cuenta corriente
        INSERT INTO public.cta_cte_movimientos (
            cliente_id,
            caja_sesion_id,
            venta_id,
            tipo,
            monto,
            detalle
        ) VALUES (
            p_cliente_id,
            v_caja_sesion_id,
            v_venta_id,
            'DEUDA',
            v_total,
            'Venta Fiada #' || v_venta_id
        );
    END IF;

    -- 10. Retornar resumen de venta
    RETURN QUERY SELECT v_venta_id, v_subtotal, v_descuento_total, v_total;
END;
$$;
