-- PROBLEMAS IDENTIFICADOS EN crear_requisicion:
-- 1. Variables no definidas en UPDATE de stock (v_cant_solicitada, v_cant_entregada, v_gas_unitario)
-- 2. Parámetros inexistentes (p_email_almacen, v_id_producto)
-- 3. Lógica de stock incorrecta durante creación

-- FUNCIÓN CORREGIDA:
DROP FUNCTION IF EXISTS requisiciones.crear_requisicion(TEXT, NUMERIC, INTEGER, TEXT, NUMERIC, JSON) CASCADE;

CREATE OR REPLACE FUNCTION requisiciones.crear_requisicion(
    p_email TEXT,
    p_proIntermedio NUMERIC,
    p_proFinal INTEGER,
    p_obsEmpleado TEXT,
    p_gasTotalPedido NUMERIC,
    p_json_productos JSON -- [{ "nombre": "...", "cantidad": ..., "gasUnitario": ..., "gasTotalProducto": ... }, ...]
)
RETURNS UUID
AS $$
DECLARE
    v_idRequisicion UUID;
    v_nombreEmpleado VARCHAR(100);
    v_idDependencia UUID;
    v_codPrograma INTEGER;
    v_idProducto UUID;
    v_producto JSON;
    v_nombre TEXT;
    v_cantidad NUMERIC;
    v_gasUnitario NUMERIC;
    v_gasTotalProducto NUMERIC;
    v_stockActual NUMERIC;
    v_estado_inicial VARCHAR(50) := 'EN ESPERA';
BEGIN
    -- 1. Buscar info del empleado y su dependencia
    SELECT e.IdDependencia, d.CodPrograma, e.Nombre
    INTO v_idDependencia, v_codPrograma, v_nombreEmpleado
    FROM usuarios.Empleados e
    JOIN usuarios.Dependencias d ON e.IdDependencia = d.IdDependencia
    WHERE e.EmailInstitucional = p_email;

    IF v_idDependencia IS NULL OR v_codPrograma IS NULL THEN
        RAISE EXCEPTION 'No se encontró dependencia o programa para el empleado %', p_email;
    END IF;

    -- 2. Insertar en Requisiciones
    INSERT INTO requisiciones.Requisiciones (
        NomEmpleado, IdDependencia, FecSolicitud,
        CodPrograma, ProIntermedio, ProFinal, EstGeneral,
        ObsEmpleado, GasTotalDelPedido,
        CreadoEn, CreadoPor
    )
    VALUES (
        v_nombreEmpleado, v_idDependencia, CURRENT_DATE,
        v_codPrograma, p_proIntermedio, p_proFinal,
        v_estado_inicial,
        p_obsEmpleado, p_gasTotalPedido,
        CURRENT_DATE, p_email
    )
    RETURNING IdRequisicion INTO v_idRequisicion;

    -- 3. Recorrer productos
    FOR v_producto IN SELECT * FROM json_array_elements(p_json_productos)
    LOOP
        v_nombre := v_producto->>'nombre';
        v_cantidad := (v_producto->>'cantidad')::NUMERIC;
        v_gasUnitario := (v_producto->>'gasUnitario')::NUMERIC;
        v_gasTotalProducto := (v_producto->>'gasTotalProducto')::NUMERIC;

        -- Buscar producto y stock
        SELECT IdProducto, CanStock INTO v_idProducto, v_stockActual
        FROM productos.Productos
        WHERE NomProducto = v_nombre;

        IF v_idProducto IS NULL THEN
            RAISE EXCEPTION 'Producto no encontrado: %', v_nombre;
        END IF;

        -- Validar stock
        IF v_stockActual < v_cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para el producto: % (stock disponible: %, solicitado: %)', 
                            v_nombre, v_stockActual, v_cantidad;
        END IF;

        -- CORREGIDO: Actualizar stock restando la cantidad solicitada (NO entregada aún)
        UPDATE productos.Productos
        SET CanStock      = COALESCE(CanStock, 0) - v_cantidad,
            GasTotal      = COALESCE(GasTotal, 0) - (v_cantidad * v_gasUnitario),
            ActualizadoEn = CURRENT_DATE,
            ActualizadoPor = p_email
        WHERE IdProducto  = v_idProducto;

        -- Insertar en Detalle
        INSERT INTO requisiciones.Detalle_Requisicion (
            IdRequisicion, IdProducto, CantSolicitada,
            GasUnitario, GasTotalProducto
        )
        VALUES (
            v_idRequisicion, v_idProducto, v_cantidad,
            v_gasUnitario, v_gasTotalProducto
        );
    END LOOP;

    RETURN v_idRequisicion;

EXCEPTION WHEN OTHERS THEN
    -- rollback automático
    RAISE EXCEPTION 'Error al crear la requisición: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;
