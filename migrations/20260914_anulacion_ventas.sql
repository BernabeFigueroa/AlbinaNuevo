-- Migración: Anulación de ventas con reingreso automático de stock y ajuste de caja/cta-cte
-- Fecha: 2026-09-14
-- Descripción: Agrega campos de auditoría a 'ventas' e implementa la función atómica 'anular_venta_atomica'.

BEGIN;

-- 1. Agregar columnas de auditoría a la tabla ventas
ALTER TABLE public.ventas
    ADD COLUMN IF NOT EXISTS anulada_por UUID REFERENCES public.usuarios(id),
    ADD COLUMN IF NOT EXISTS fecha_anulacion TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS motivo_anulacion TEXT;

-- 2. Función RPC para anular venta de manera atómica
CREATE OR REPLACE FUNCTION public.anular_venta_atomica(
    p_venta_id BIGINT,
    p_motivo TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
    v_usuario_id UUID;
    v_venta RECORD;
    v_item RECORD;
BEGIN
    -- 1. Validar usuario autenticado
    v_usuario_id := auth.uid();
    IF v_usuario_id IS NULL THEN
        RAISE EXCEPTION 'Debe iniciar sesión para anular una venta.';
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
        RAISE EXCEPTION 'La venta #% ya se encuentra anulada.', p_venta_id;
    END IF;

    -- 3. Marcar la venta como ANULADA y registrar auditoría
    UPDATE public.ventas
    SET estado = 'ANULADA',
        anulada_por = v_usuario_id,
        fecha_anulacion = NOW(),
        motivo_anulacion = p_motivo
    WHERE id = p_venta_id;

    -- 4. Reintegrar stock de los productos vendidos (excluyendo provisorios)
    FOR v_item IN
        SELECT producto_id, cantidad, es_provisorio
        FROM public.ventas_detalle
        WHERE venta_id = p_venta_id
    LOOP
        IF v_item.producto_id IS NOT NULL AND NOT COALESCE(v_item.es_provisorio, false) THEN
            UPDATE public.productos
            SET stock_actual = stock_actual + v_item.cantidad
            WHERE id = v_item.producto_id;
        END IF;
    END LOOP;

    -- 5. Si la venta fue fiada, eliminar la deuda generada en cta_cte_movimientos
    IF v_venta.metodo_pago IN ('FIADO / CTA. CTE.', 'CUENTA CORRIENTE', 'FIADO') THEN
        DELETE FROM public.cta_cte_movimientos
        WHERE venta_id = p_venta_id;
    END IF;

    -- 6. En caja_movimientos, marcar los movimientos de esta venta como ANULADA
    -- para mantener trazabilidad histórica sin alterar el efectivo esperado
    UPDATE public.caja_movimientos
    SET tipo = 'ANULADA',
        descripcion = descripcion || ' [ANULADA: ' || COALESCE(p_motivo, '') || ']'
    WHERE descripcion LIKE 'Venta #' || p_venta_id || '%'
       OR descripcion LIKE 'Venta #' || p_venta_id;

    RETURN jsonb_build_object(
        'success', true,
        'venta_id', p_venta_id,
        'estado', 'ANULADA'
    );
END;
$$;

COMMIT;
