-- Agregar logging a la función para ver qué está pasando internamente
CREATE OR REPLACE FUNCTION requisiciones.responder_requisicion_jefe_materiales(
    p_id_requisicion UUID,
    p_email_jefe TEXT,
    p_estado_aprob TEXT,
    p_comentario TEXT,
    p_productos JSONB DEFAULT '[]'::jsonb
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_email_jefe TEXT;
    v_nombre_jefe TEXT;
    v_id_producto_uuid UUID;
    v_nueva_cantidad NUMERIC(10,2);
    v_cantidad_original NUMERIC(10,2);
    v_existe_aprobacion BOOLEAN;
    v_count_before INT;
    v_count_after INT;
BEGIN
    RAISE NOTICE '[FUNC] ===== INICIO responder_requisicion_jefe_materiales =====';
    RAISE NOTICE '[FUNC] p_id_requisicion: %, p_email_jefe: %, p_estado_aprob: %', p_id_requisicion, p_email_jefe, p_estado_aprob;

    -- Validar estado
    IF UPPER(p_estado_aprob) NOT IN ('APROBADO', 'RECHAZADO') THEN
        RETURN 'ERROR: Estado inválido: debe ser APROBADO o RECHAZADO';
    END IF;

    -- Validar comentario obligatorio si rechaza
    IF UPPER(p_estado_aprob) = 'RECHAZADO' AND (p_comentario IS NULL OR TRIM(p_comentario) = '') THEN
        RETURN 'ERROR: Comentario es obligatorio al rechazar';
    END IF;

    -- Validar que el usuario es Jefe de Materiales
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
        RETURN 'ERROR: Usuario no autorizado: no es Jefe de Materiales o no está activo';
    END IF;

    RAISE NOTICE '[FUNC] Usuario validado: % (%)', v_email_jefe, v_nombre_jefe;

    -- Contar aprobaciones ANTES
    SELECT COUNT(*) INTO v_count_before
    FROM requisiciones.aprobaciones
    WHERE idrequisicion = p_id_requisicion AND rol = 'JefSerMat';
    
    RAISE NOTICE '[FUNC] Aprobaciones JefSerMat ANTES del INSERT: %', v_count_before;

    -- Verificar si ya existe aprobación
    SELECT EXISTS(
        SELECT 1 FROM requisiciones.aprobaciones
        WHERE idrequisicion = p_id_requisicion
          AND rol = 'JefSerMat'
          AND estadoaprobacion = UPPER(p_estado_aprob)
    ) INTO v_existe_aprobacion;

    RAISE NOTICE '[FUNC] ¿Ya existe aprobación con mismo estado?: %', v_existe_aprobacion;

    -- Si aprueba, actualizar cantidades de productos
    IF UPPER(p_estado_aprob) = 'APROBADO' THEN
        FOR v_id_producto_uuid, v_nueva_cantidad IN
            SELECT (elem->>'id_producto')::UUID,
                   (elem->>'nueva_cantidad')::NUMERIC
            FROM jsonb_array_elements(p_productos) elem
        LOOP
            SELECT dr.cantsolicitada
            INTO v_cantidad_original
            FROM requisiciones.detalle_requisicion dr
            WHERE dr.idrequisicion = p_id_requisicion
              AND dr.idproducto = v_id_producto_uuid;

            IF v_nueva_cantidad IS NOT NULL AND v_nueva_cantidad != v_cantidad_original THEN
                IF v_nueva_cantidad > v_cantidad_original THEN
                    RETURN 'ERROR: No puede aumentar la cantidad solicitada';
                END IF;

                UPDATE requisiciones.detalle_requisicion
                SET cantsolicitada = v_nueva_cantidad,
                    gastotalproducto = v_nueva_cantidad * gasunitario
                WHERE idrequisicion = p_id_requisicion
                  AND idproducto = v_id_producto_uuid;

                IF p_comentario IS NULL OR TRIM(p_comentario) = '' THEN
                    p_comentario := FORMAT('Cantidad ajustada de %.2f a %.2f', v_cantidad_original, v_nueva_cantidad);
                ELSE
                    p_comentario := p_comentario || FORMAT(E'\nCantidad ajustada de %.2f a %.2f', v_cantidad_original, v_nueva_cantidad);
                END IF;
            END IF;
        END LOOP;

        -- Recalcular total del pedido
        UPDATE requisiciones.requisiciones
        SET gastotaldelpedido = (
                SELECT COALESCE(SUM(gastotalproducto), 0)
                FROM requisiciones.detalle_requisicion
                WHERE idrequisicion = p_id_requisicion
            ),
            estgeneral = 'EN ESPERA',
            actualizadoen = CURRENT_TIMESTAMP,
            actualizadopor = p_email_jefe
        WHERE idrequisicion = p_id_requisicion;

        RAISE NOTICE '[FUNC] Estado actualizado a EN ESPERA';

    ELSE
        -- Si rechaza, cambiar estado general a RECHAZADO
        UPDATE requisiciones.requisiciones
        SET estgeneral = 'RECHAZADO',
            motrechazo = p_comentario,
            actualizadoen = CURRENT_TIMESTAMP,
            actualizadopor = p_email_jefe
        WHERE idrequisicion = p_id_requisicion;

        RAISE NOTICE '[FUNC] Estado actualizado a RECHAZADO';
    END IF;

    -- Insertar registro de aprobación (SOLO SI NO EXISTE)
    RAISE NOTICE '[FUNC] ===== INTENTANDO INSERT DE APROBACIÓN =====';
    
    INSERT INTO requisiciones.aprobaciones (
        idaprobacion,
        idrequisicion,
        emailinstitucional,
        rol,
        estadoaprobacion,
        comentario,
        fecaprobacion
    )
    SELECT
        uuid_generate_v4(),
        p_id_requisicion,
        v_email_jefe,
        'JefSerMat',
        UPPER(p_estado_aprob),
        p_comentario,
        CURRENT_DATE
    WHERE NOT EXISTS (
        SELECT 1 FROM requisiciones.aprobaciones
        WHERE idrequisicion = p_id_requisicion
          AND rol = 'JefSerMat'
          AND estadoaprobacion = UPPER(p_estado_aprob)
    );

    -- Verificar si se insertó
    SELECT COUNT(*) INTO v_count_after
    FROM requisiciones.aprobaciones
    WHERE idrequisicion = p_id_requisicion AND rol = 'JefSerMat';

    RAISE NOTICE '[FUNC] Aprobaciones JefSerMat DESPUÉS del INSERT: % (antes: %)', v_count_after, v_count_before;
    
    IF v_count_after > v_count_before THEN
        RAISE NOTICE '[FUNC] ✔ INSERT exitoso: se agregó nueva aprobación';
    ELSE
        RAISE NOTICE '[FUNC] ⚠ INSERT NO ejecutado: condición WHERE NOT EXISTS fue FALSE';
    END IF;

    RAISE NOTICE '[FUNC] ===== FIN responder_requisicion_jefe_materiales =====';

    RETURN FORMAT('✔ Requisición aprobada por Jefe de Materiales (%s) - Estado: %s',
        v_nombre_jefe,
        CASE WHEN UPPER(p_estado_aprob) = 'APROBADO' THEN 'EN ESPERA (pasa a Almacén)' ELSE 'RECHAZADO' END
    );

EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '[FUNC] ❌ EXCEPCIÓN: %', SQLERRM;
    RETURN FORMAT('ERROR: %s', SQLERRM);
END;
$$;
