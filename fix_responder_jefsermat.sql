-- FIX: Corregir función responder_requisicion_jefe_materiales
-- El problema: No valida actlaboralmente y manejo inconsistente de tipos

DROP FUNCTION IF EXISTS requisiciones.responder_requisicion_jefe_materiales(UUID, TEXT, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS requisiciones.responder_requisicion_jefe_materiales(UUID, TEXT, TEXT, TEXT, JSON) CASCADE;

CREATE OR REPLACE FUNCTION requisiciones.responder_requisicion_jefe_materiales(
    p_id_requisicion UUID,
    p_email_jefe TEXT,
    p_estado_aprob TEXT,
    p_comentario TEXT,
    p_productos JSONB DEFAULT '[]'::JSONB
)
RETURNS TEXT AS $$
DECLARE
    v_email_jefe TEXT;
    v_nombre_jefe TEXT;
    v_producto JSONB;
    v_id_producto_uuid UUID;
    v_nueva_cantidad NUMERIC(10,2);
    v_cantidad_original NUMERIC(10,2);
    v_ajustes TEXT := '';
    v_email_solicitante TEXT;
    v_cod_req TEXT;
    v_nom_prod TEXT;
    v_cod_prod TEXT;
BEGIN
    -- Validar estado
    IF UPPER(p_estado_aprob) NOT IN ('APROBADO', 'RECHAZADO') THEN
        RAISE EXCEPTION 'Estado inválido: debe ser APROBADO o RECHAZADO';
    END IF;

    -- Validar comentario obligatorio si rechaza
    IF UPPER(p_estado_aprob) = 'RECHAZADO' AND (p_comentario IS NULL OR TRIM(p_comentario) = '') THEN
        RAISE EXCEPTION 'Comentario es obligatorio al rechazar';
    END IF;

    -- Validar que el usuario es Jefe de Materiales (CON actlaboralmente = true)
    SELECT e.emailinstitucional, e.nombre
    INTO v_email_jefe, v_nombre_jefe
    FROM usuarios.empleados e
    INNER JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
    INNER JOIN acceso.roles r ON r.idrol = er.idrol
    WHERE e.emailinstitucional = p_email_jefe
      AND r.nomrol = 'JefSerMat'
      AND er.actlaboralmente = TRUE
    LIMIT 1;

    IF v_email_jefe IS NULL THEN
        RAISE EXCEPTION 'Usuario no autorizado: no es Jefe de Materiales o no está activo';
    END IF;

    -- Validar que no haya sido respondida ya por este rol
    IF EXISTS (
        SELECT 1 FROM requisiciones.aprobaciones
        WHERE idrequisicion = p_id_requisicion
          AND rol = 'JefSerMat'
    ) THEN
        RAISE EXCEPTION 'Esta requisición ya fue respondida por Jefe de Materiales';
    END IF;

    -- Si aprueba, actualizar cantidades de productos si fueron modificadas
    IF UPPER(p_estado_aprob) = 'APROBADO' THEN
        -- Recorrer productos enviados en JSON
        FOR v_id_producto_uuid, v_nueva_cantidad IN
            SELECT (elem->>'id_producto')::UUID,
                   (elem->>'nueva_cantidad')::NUMERIC
            FROM jsonb_array_elements(p_productos) elem
        LOOP
            -- Obtener cantidad original
            SELECT dr.cantsolicitada
            INTO v_cantidad_original
            FROM requisiciones.detalle_requisicion dr
            WHERE dr.idrequisicion = p_id_requisicion
              AND dr.idproducto = v_id_producto_uuid;

            -- Si la cantidad cambió, actualizar
            IF v_nueva_cantidad IS NOT NULL AND v_nueva_cantidad != v_cantidad_original THEN
                -- Jefe de Materiales puede reducir pero no aumentar
                IF v_nueva_cantidad > v_cantidad_original THEN
                    RAISE EXCEPTION 'No puede aumentar la cantidad solicitada';
                END IF;

                -- Actualizar la cantidad en Detalle_Requisicion
                UPDATE requisiciones.detalle_requisicion
                SET cantsolicitada = v_nueva_cantidad,
                    gastotalproducto = v_nueva_cantidad * gasunitario
                WHERE idrequisicion = p_id_requisicion
                  AND idproducto = v_id_producto_uuid;

                -- Agregar al comentario que hubo modificación
                IF p_comentario IS NULL OR TRIM(p_comentario) = '' THEN
                    p_comentario := FORMAT('Cantidad ajustada de %.2f a %.2f', v_cantidad_original, v_nueva_cantidad);
                ELSE
                    p_comentario := p_comentario || FORMAT(E'\nCantidad ajustada de %.2f a %.2f', v_cantidad_original, v_nueva_cantidad);
                END IF;

                -- Detalle de ajuste
                SELECT p.nomproducto, p.codobjetounico INTO v_nom_prod, v_cod_prod FROM productos.productos p WHERE p.idproducto = v_id_producto_uuid;
                IF v_nom_prod IS NULL THEN v_nom_prod := 'Producto'; END IF;
                IF v_cod_prod IS NULL THEN v_cod_prod := 'N/A'; END IF;
                v_ajustes := v_ajustes || FORMAT(E'\n- %s (%s): %s → %s',
                    v_nom_prod,
                    v_cod_prod,
                    to_char(COALESCE(v_cantidad_original,0),'FM999999990.00'),
                    to_char(COALESCE(v_nueva_cantidad,0),'FM999999990.00')
                );
            END IF;
        END LOOP;

        -- Recalcular total del pedido
        UPDATE requisiciones.requisiciones
        SET gastotaldelpedido = (
                SELECT COALESCE(SUM(gastotalproducto), 0)
                FROM requisiciones.detalle_requisicion
                WHERE idrequisicion = p_id_requisicion
            ),
            -- CRÍTICO: MANTENER EN ESPERA para que pase a Almacén
            estgeneral = 'EN ESPERA',
            actualizadoen = CURRENT_TIMESTAMP,
            actualizadopor = p_email_jefe
        WHERE idrequisicion = p_id_requisicion;

    ELSE
        -- Si rechaza, cambiar estado general a RECHAZADO
        UPDATE requisiciones.requisiciones
        SET estgeneral = 'RECHAZADO',
            motrechazo = p_comentario,
            actualizadoen = CURRENT_TIMESTAMP,
            actualizadopor = p_email_jefe
        WHERE idrequisicion = p_id_requisicion;
    END IF;

    -- Insertar registro de aprobación
    INSERT INTO requisiciones.aprobaciones (
        idaprobacion,
        idrequisicion,
        emailinstitucional,
        rol,
        estadoaprobacion,
        comentario,
        fecaprobacion
    ) VALUES (
        uuid_generate_v4(),
        p_id_requisicion,
        v_email_jefe,
        'JefSerMat',
        UPPER(p_estado_aprob),
        p_comentario,
        CURRENT_DATE
    );

    RETURN FORMAT('✔ Requisición aprobada por Jefe de Materiales (%s) - Estado: %s',
        v_nombre_jefe,
        CASE WHEN UPPER(p_estado_aprob) = 'APROBADO' THEN 'EN ESPERA (pasa a Almacén)' ELSE 'RECHAZADO' END
    );

END;
$$ LANGUAGE plpgsql;
