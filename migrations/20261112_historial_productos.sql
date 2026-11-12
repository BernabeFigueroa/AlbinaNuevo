BEGIN;

CREATE TABLE public.productos_historial (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    producto_id BIGINT NOT NULL,
    operacion TEXT NOT NULL CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    fecha TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    usuario_id UUID,
    rol_conexion NAME NOT NULL,
    anterior JSONB,
    posterior JSONB
);

CREATE INDEX productos_historial_producto_fecha_idx
    ON public.productos_historial (producto_id, fecha DESC);

ALTER TABLE public.productos_historial ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.productos_historial FROM PUBLIC, anon, authenticated;

CREATE FUNCTION public.registrar_historial_producto()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND to_jsonb(OLD) = to_jsonb(NEW) THEN
        RETURN NULL;
    END IF;

    INSERT INTO public.productos_historial
        (producto_id, operacion, usuario_id, rol_conexion, anterior, posterior)
    VALUES (
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        TG_OP,
        auth.uid(),
        session_user,
        CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END
    );

    RETURN NULL;
END;
$$;

REVOKE ALL ON FUNCTION public.registrar_historial_producto() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER registrar_historial_producto
AFTER INSERT OR UPDATE OR DELETE ON public.productos
FOR EACH ROW EXECUTE FUNCTION public.registrar_historial_producto();

CREATE FUNCTION public.guardar_nombre_producto_vendido()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NEW.producto_id IS NOT NULL AND NULLIF(btrim(NEW.descripcion), '') IS NULL THEN
        SELECT nombre INTO NEW.descripcion
        FROM public.productos WHERE id = NEW.producto_id;
    END IF;

    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.guardar_nombre_producto_vendido() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER guardar_nombre_producto_vendido
BEFORE INSERT ON public.ventas_detalle
FOR EACH ROW EXECUTE FUNCTION public.guardar_nombre_producto_vendido();

COMMIT;
