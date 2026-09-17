-- Migración: Cambio de método de pago de ventas entre Efectivo y Transferencia
-- Fecha: 2026-09-17
-- Descripción: Permite modificar el método de pago de una venta exclusivamente
--              entre 'EFECTIVO' y 'TRANSFERENCIA', manteniendo sincronizada la tabla
--              'ventas' y 'caja_movimientos'.

BEGIN;

CREATE OR REPLACE FUNCTION public.cambiar_metodo_pago_atomico(
    p_venta_id BIGINT,
    p_nuevo_metodo TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
    v_venta RECORD;
    v_metodo_actual TEXT;
    v_nuevo_metodo TEXT;
BEGIN
    -- 1. Normalizar y validar nuevo método
    v_nuevo_metodo := UPPER(TRIM(p_nuevo_metodo));
    IF v_nuevo_metodo NOT IN ('EFECTIVO', 'TRANSFERENCIA') THEN
        RAISE EXCEPTION 'El método de pago solo puede cambiarse a EFECTIVO o TRANSFERENCIA.';
    END IF;

    -- 2. Obtener la venta
    SELECT * INTO v_venta
    FROM public.ventas
    WHERE id = p_venta_id
    FOR UPDATE;

    IF v_venta.id IS NULL THEN
        RAISE EXCEPTION 'La venta #% no existe.', p_venta_id;
    END IF;

    IF v_venta.estado IN ('ANULADA', 'CANCELADA') THEN
        RAISE EXCEPTION 'No se puede modificar el método de pago de una venta anulada (#%).', p_venta_id;
    END IF;

    v_metodo_actual := UPPER(TRIM(v_venta.metodo_pago));
    IF v_metodo_actual NOT IN ('EFECTIVO', 'TRANSFERENCIA') THEN
        RAISE EXCEPTION 'Solo se permite cambiar el método de pago entre EFECTIVO y TRANSFERENCIA. La venta #% posee %.', p_venta_id, v_metodo_actual;
    END IF;

    IF v_metodo_actual = v_nuevo_metodo THEN
        RETURN jsonb_build_object(
            'success', true,
            'venta_id', p_venta_id,
            'metodo_anterior', v_metodo_actual,
            'metodo_nuevo', v_nuevo_metodo,
            'mensaje', 'El método de pago ya era ' || v_nuevo_metodo
        );
    END IF;

    -- 3. Actualizar venta
    UPDATE public.ventas
    SET metodo_pago = v_nuevo_metodo
    WHERE id = p_venta_id;

    -- 4. Actualizar movimientos de caja asociados
    UPDATE public.caja_movimientos
    SET metodo_pago = v_nuevo_metodo
    WHERE caja_sesion_id = v_venta.caja_sesion_id
      AND (
          descripcion = 'Venta #' || p_venta_id
          OR descripcion LIKE 'Venta #' || p_venta_id || ' %'
          OR descripcion LIKE 'Venta #' || p_venta_id || '(%'
      );

    RETURN jsonb_build_object(
        'success', true,
        'venta_id', p_venta_id,
        'metodo_anterior', v_metodo_actual,
        'metodo_nuevo', v_nuevo_metodo
    );
END;
$$;

COMMIT;
